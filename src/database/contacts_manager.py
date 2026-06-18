"""
通讯录数据管理器

V4.5增强功能:
1. 支持姓名+工号唯一标识，区分同名联系人
2. 支持导入时按新信息刷新本地记录
3. 支持批量导入、导出

版本：V4.5
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


class ContactsManager:
    """
    通讯录数据管理器

    功能：
    1. 联系人CRUD操作（基于姓名+工号唯一标识）
    2. 批量导入（支持刷新模式）
    3. 同名联系人区分
    """

    def __init__(self, db_connection):
        self.db = db_connection

    @staticmethod
    def make_unique_key(name: str, employee_id: Optional[str] = None) -> str:
        """
        生成唯一标识键（姓名+工号）

        规则：
        - 姓名相同时，用工号区分
        - 无工号时使用空字符串
        - 工号相同时，使用姓名区分

        Args:
            name: 姓名
            employee_id: 工号（可选）

        Returns:
            唯一标识键，格式：name|employee_id

        示例：
            赵六|EMP001 → 赵六|EMP001
            赵六| → 赵六|
            王五|EMP002 → 王五|EMP002
        """
        name = name.strip() if name else ""
        emp_id = employee_id.strip() if employee_id else ""
        return f"{name}|{emp_id}"

    @staticmethod
    def parse_unique_key(unique_key: str) -> Tuple[str, str]:
        """
        解析唯一标识键

        Args:
            unique_key: 唯一标识键

        Returns:
            (name, employee_id) 元组
        """
        parts = unique_key.rsplit("|", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return unique_key, ""

    def find_by_unique_key(
        self,
        name: str,
        employee_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        根据姓名+工号查找联系人

        Args:
            name: 姓名
            employee_id: 工号

        Returns:
            联系人信息，未找到返回None
        """
        unique_key = self.make_unique_key(name, employee_id)

        sql = """
        SELECT * FROM contacts
        WHERE name = ? AND (employee_id = ? OR (employee_id IS NULL AND ? = ''))
        LIMIT 1
        """

        try:
            result = self.db.execute_query(sql, (name, employee_id or '', employee_id or ''))
            return result[0] if result else None
        except Exception:
            return None

    def find_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        根据姓名查找所有匹配的联系人（考虑同名情况）

        Args:
            name: 姓名

        Returns:
            联系人列表
        """
        sql = """
        SELECT * FROM contacts
        WHERE name = ?
        ORDER BY employee_id, created_at
        """

        try:
            return self.db.execute_query(sql, (name,))
        except Exception:
            return []

    def add_contact(
        self,
        data: Dict[str, Any],
        refresh_if_exists: bool = True
    ) -> Tuple[bool, str, Optional[int]]:
        """
        添加联系人（支持刷新模式）

        Args:
            data: 联系人数据，包含 name, employee_id 等字段
            refresh_if_exists: 如果联系人已存在，是否用新数据刷新

        Returns:
            (success, message, contact_id) 元组
                - success: 是否成功
                - message: 结果消息
                - contact_id: 联系人ID（新增时返回新ID，更新时返回原ID）
        """
        name = data.get('name', '').strip()
        if not name:
            return False, "姓名不能为空", None

        employee_id = data.get('employee_id')

        # 检查是否已存在
        existing = self.find_by_unique_key(name, employee_id)

        if existing:
            if refresh_if_exists:
                # 用新数据刷新本地记录
                contact_id = existing.get('id')
                success = self.update_contact(contact_id, data)
                if success:
                    return True, f"已刷新联系人「{name}」的信息", contact_id
                else:
                    return False, f"刷新联系人「{name}」失败", contact_id
            else:
                return False, f"联系人「{name}」已存在", existing.get('id')

        # 新增联系人
        sql = """
        INSERT INTO contacts
        (name, employee_id, phone, email, department, position, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        try:
            now = datetime.now()
            cursor = self.db.execute(sql, (
                name,
                employee_id or '',
                data.get('phone', ''),
                data.get('email', ''),
                data.get('department', ''),
                data.get('position', ''),
                now,
                now
            ))
            self.db.commit()

            contact_id = cursor.lastrowid if cursor else None
            return True, f"已添加联系人「{name}」", contact_id

        except Exception as e:
            return False, f"添加联系人失败: {str(e)}", None

    def update_contact(
        self,
        contact_id: int,
        data: Dict[str, Any]
    ) -> bool:
        """
        更新联系人信息

        Args:
            contact_id: 联系人ID
            data: 更新的数据

        Returns:
            是否成功
        """
        sql = """
        UPDATE contacts SET
            name = ?,
            employee_id = ?,
            phone = ?,
            email = ?,
            department = ?,
            position = ?,
            updated_at = ?
        WHERE id = ?
        """

        try:
            now = datetime.now()
            self.db.execute(sql, (
                data.get('name', '').strip(),
                data.get('employee_id', ''),
                data.get('phone', ''),
                data.get('email', ''),
                data.get('department', ''),
                data.get('position', ''),
                now,
                contact_id
            ))
            self.db.commit()
            return True
        except Exception:
            return False

    def delete_contact(self, contact_id: int) -> bool:
        """
        删除联系人

        Args:
            contact_id: 联系人ID

        Returns:
            是否成功
        """
        sql = "DELETE FROM contacts WHERE id = ?"

        try:
            self.db.execute(sql, (contact_id,))
            self.db.commit()
            return True
        except Exception:
            return False

    def import_contacts(
        self,
        contacts: List[Dict[str, Any]],
        refresh_mode: bool = True,
        batch_size: int = 100
    ) -> Dict[str, int]:
        """
        批量导入通讯录

        规则：
        1. 姓名+工号相同 → 视为同一联系人
        2. 姓名相同但工号不同 → 视为不同联系人（保留）
        3. refresh_mode=True 时：用导入数据刷新本地记录

        Args:
            contacts: 联系人列表
            refresh_mode: 是否刷新已存在的记录
            batch_size: 每批处理数量

        Returns:
            导入统计 {'added': N, 'updated': N, 'skipped': N, 'errors': N}
        """
        stats = {'added': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

        for contact in contacts:
            name = contact.get('name', '').strip()
            if not name:
                stats['errors'] += 1
                continue

            success, message, _ = self.add_contact(contact, refresh_mode)

            if success:
                if '已添加' in message:
                    stats['added'] += 1
                elif '已刷新' in message:
                    stats['updated'] += 1
                else:
                    stats['skipped'] += 1
            else:
                stats['errors'] += 1

        return stats

    def export_contacts(self) -> List[Dict[str, Any]]:
        """
        导出所有通讯录

        Returns:
            联系人列表
        """
        sql = """
        SELECT * FROM contacts
        ORDER BY name, employee_id
        """

        try:
            return self.db.execute_query(sql)
        except Exception:
            return []

    def get_duplicate_names(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取同名联系人列表（姓名相同但工号不同）

        Returns:
            {姓名: [联系人列表]}，只包含同名联系人
        """
        sql = """
        SELECT name, COUNT(*) as count
        FROM contacts
        WHERE name IS NOT NULL AND name != ''
        GROUP BY name
        HAVING count > 1
        """

        try:
            duplicates = self.db.execute_query(sql)

            result = {}
            for dup in duplicates:
                name = dup[0]
                contacts = self.find_by_name(name)
                if contacts:
                    result[name] = contacts

            return result
        except Exception:
            return {}

    def sync_with_external(
        self,
        external_contacts: List[Dict[str, Any]],
        strategy: str = 'refresh'  # 'refresh': 刷新, 'add_new': 仅新增, 'full_replace': 完全替换
    ) -> Dict[str, int]:
        """
        与外部数据源同步通讯录

        Args:
            external_contacts: 外部联系人列表
            strategy: 同步策略
                - 'refresh': 外部数据刷新本地
                - 'add_new': 仅添加本地不存在的新联系人
                - 'full_replace': 完全替换（删除本地不在外部列表中的记录）

        Returns:
            同步统计
        """
        stats = {'added': 0, 'updated': 0, 'deleted': 0, 'unchanged': 0}

        if strategy == 'full_replace':
            # 完全替换模式
            existing = self.export_contacts()
            existing_keys = {
                self.make_unique_key(c.get('name', ''), c.get('employee_id', '')): c
                for c in existing
            }

            external_keys = {
                self.make_unique_key(c.get('name', ''), c.get('employee_id', '')): c
                for c in external_contacts
            }

            # 删除不在外部列表中的记录
            for key, contact in existing_keys.items():
                if key not in external_keys:
                    contact_id = contact.get('id')
                    if contact_id and self.delete_contact(contact_id):
                        stats['deleted'] += 1

            # 添加或更新外部列表中的记录
            for key, contact in external_keys.items():
                success, _, _ = self.add_contact(contact, refresh_if_exists=True)
                if success:
                    if key in existing_keys:
                        stats['updated'] += 1
                    else:
                        stats['added'] += 1

        else:
            # 刷新或仅新增模式
            for contact in external_contacts:
                success, message, _ = self.add_contact(
                    contact,
                    refresh_if_exists=(strategy == 'refresh')
                )

                if success:
                    if '已添加' in message:
                        stats['added'] += 1
                    elif '已刷新' in message:
                        stats['updated'] += 1
                    else:
                        stats['unchanged'] += 1

        return stats
