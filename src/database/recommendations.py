"""
推荐库管理模块
管理答复人推荐信息，支持智能匹配

V4.5增强功能:
1. 支持姓名+工号唯一标识，区分同名联系人
2. 支持多个关键模块合并（同姓名多条记录自动合并）
3. 智能推荐支持任一关键模块匹配

版本：V4.5
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from collections import defaultdict


class RecommendationModel:
    """推荐库数据模型"""
    
    TABLE_NAME = "recommendations"
    
    def __init__(self, db_connection):
        self.db = db_connection
        
    def create_table(self) -> bool:
        """创建推荐库表"""
        sql = """
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL,
            employee_id VARCHAR(20),
            phone VARCHAR(20),
            email VARCHAR(100),
            department VARCHAR(50),
            position VARCHAR(50),
            key_module VARCHAR(200),
            expertise VARCHAR(200),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        try:
            self.db.execute(sql)
            self.db.commit()
            return True
        except Exception:
            return False
            
    def add_recommendation(self, data: Dict[str, Any]) -> Optional[int]:
        """添加推荐记录"""
        sql = """
        INSERT INTO recommendations 
        (name, employee_id, phone, email, department, position, key_module, expertise)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            cursor = self.db.execute(sql, (
                data.get('name'),
                data.get('employee_id'),
                data.get('phone'),
                data.get('email'),
                data.get('department'),
                data.get('position'),
                data.get('key_module'),
                data.get('expertise')
            ))
            self.db.commit()
            return cursor.lastrowid
        except Exception:
            return None
            
    def get_recommendation(self, rec_id: int) -> Optional[Dict[str, Any]]:
        """获取推荐记录"""
        sql = "SELECT * FROM recommendations WHERE id = ?"
        try:
            result = self.db.execute_query(sql, (rec_id,))
            if result:
                return result[0]
            return None
        except Exception:
            return None
            
    def get_all_recommendations(self) -> List[Dict[str, Any]]:
        """获取所有推荐记录"""
        sql = "SELECT * FROM recommendations ORDER BY updated_at DESC"
        try:
            return self.db.execute_query(sql)
        except Exception:
            return []
            
    def search_by_key_module(self, keyword: str) -> List[Dict[str, Any]]:
        """根据关键模块搜索"""
        sql = """
        SELECT * FROM recommendations 
        WHERE key_module LIKE ? 
        ORDER BY updated_at DESC
        """
        try:
            return self.db.execute_query(sql, (f"%{keyword}%",))
        except Exception:
            return []
            
    def update_recommendation(self, rec_id: int, data: Dict[str, Any]) -> bool:
        """更新推荐记录"""
        sql = """
        UPDATE recommendations SET
            name = ?,
            employee_id = ?,
            phone = ?,
            email = ?,
            department = ?,
            position = ?,
            key_module = ?,
            expertise = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
        try:
            self.db.execute(sql, (
                data.get('name'),
                data.get('employee_id'),
                data.get('phone'),
                data.get('email'),
                data.get('department'),
                data.get('position'),
                data.get('key_module'),
                data.get('expertise'),
                rec_id
            ))
            self.db.commit()
            return True
        except Exception:
            return False
            
    def delete_recommendation(self, rec_id: int) -> bool:
        """删除推荐记录"""
        sql = "DELETE FROM recommendations WHERE id = ?"
        try:
            self.db.execute(sql, (rec_id,))
            self.db.commit()
            return True
        except Exception:
            return False
            
    def import_batch(self, records: List[Dict[str, Any]]) -> int:
        """批量导入推荐记录"""
        count = 0
        for record in records:
            if self.add_recommendation(record):
                count += 1
        return count
        
    def export_all(self) -> List[Dict[str, Any]]:
        """导出所有推荐记录"""
        return self.get_all_recommendations()


class RecommendationService:
    """
    推荐服务

    V4.5增强功能:
    1. recommend_responder: 支持姓名+工号唯一标识，区分同名联系人
    2. merge_recommendations: 同姓名多条记录自动合并关键模块
    3. 智能推荐：无论关键模块是MAC认证还是802.1x认证，都能关联到赵六
    """

    def __init__(self, db_connection):
        self.model = RecommendationModel(db_connection)

    @staticmethod
    def make_unique_key(name: str, employee_id: Optional[str] = None) -> str:
        """
        生成唯一标识键（姓名+工号）

        Args:
            name: 姓名
            employee_id: 工号（可选）

        Returns:
            唯一标识键，格式：name|employee_id 或 name|（空）
            同姓名无工号时使用空字符串区分
        """
        emp_id = employee_id.strip() if employee_id else ""
        return f"{name.strip()}|{emp_id}"

    @staticmethod
    def parse_unique_key(unique_key: str) -> tuple:
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

    def merge_recommendations(
        self,
        records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        合并同姓名多条推荐记录

        规则：
        1. 姓名相同 + 工号相同 → 合并关键模块
        2. 姓名相同 + 工号不同 → 视为不同联系人，不合并

        示例：
            赵六，MAC认证 + 赵六，802.1x认证 → 赵六，MAC认证、802.1x认证

        Args:
            records: 推荐记录列表

        Returns:
            合并后的记录列表
        """
        if not records:
            return []

        # 按唯一键分组
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for record in records:
            name = record.get('name', '').strip()
            employee_id = record.get('employee_id', '') or ''
            unique_key = self.make_unique_key(name, employee_id)
            grouped[unique_key].append(record)

        # 合并每组的记录
        merged: List[Dict[str, Any]] = []
        for unique_key, group in grouped.items():
            if len(group) == 1:
                # 单条记录直接添加
                merged.append(group[0])
            else:
                # 多条记录合并关键模块
                merged_record = self._merge_records(unique_key, group)
                merged.append(merged_record)

        return merged

    def _merge_records(
        self,
        unique_key: str,
        records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        合并多条同名记录

        Args:
            unique_key: 唯一标识键
            records: 同组的记录列表

        Returns:
            合并后的记录
        """
        name, employee_id = self.parse_unique_key(unique_key)

        # 使用第一条记录作为基础
        base = records[0].copy()

        # 合并关键模块（去重）
        all_modules: Set[str] = set()
        for record in records:
            key_module = record.get('key_module', '')
            if key_module:
                # 按逗号或斜杠分割
                modules = [m.strip() for m in key_module.replace('/', ',').split(',')]
                all_modules.update(modules)

        base['key_module'] = '、'.join(sorted(all_modules))  # 使用中文顿号分隔

        # 合并专业领域（去重）
        all_expertise: Set[str] = set()
        for record in records:
            expertise = record.get('expertise', '')
            if expertise:
                expertise_list = [e.strip() for e in expertise.replace('/', ',').split(',')]
                all_expertise.update(expertise_list)

        if all_expertise:
            base['expertise'] = '、'.join(sorted(all_expertise))

        # 优先使用非空字段（手机号、邮箱等）
        for field in ['phone', 'email', 'department', 'position']:
            for record in records:
                value = record.get(field)
                if value and not base.get(field):
                    base[field] = value

        base['merged_from'] = len(records)  # 标记合并来源数量
        base['is_merged'] = True

        return base

    def recommend_responder(
        self,
        key_module: str,
        exact_match: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        根据关键模块推荐答复人

        匹配规则：
        1. key_module包含搜索关键字
        2. 支持姓名+工号唯一标识（区分同名联系人）
        3. 自动合并同姓名多条记录的关键模块

        Args:
            key_module: 关键模块名称
            exact_match: 是否精确匹配（True时完全相等，False时包含即可）

        Returns:
            推荐的答复人信息

        示例：
            导入：
                赵六，MAC认证
                赵六，802.1x认证

            搜索"MAC认证" → 返回 赵六，关键模块：MAC认证、802.1x认证
            搜索"802.1x认证" → 返回 赵六，关键模块：MAC认证、802.1x认证
        """
        if not key_module:
            return None

        # 分割多个关键字
        keywords = [k.strip() for k in key_module.replace('/', ',').split(',') if k.strip()]

        all_matched: List[Dict[str, Any]] = []

        for keyword in keywords:
            if not keyword:
                continue

            # 搜索匹配记录
            results = self.model.search_by_key_module(keyword)

            if results:
                # 合并匹配结果
                all_matched.extend(results)

        if not all_matched:
            return None

        # 合并同名记录的关键模块
        merged_results = self.merge_recommendations(all_matched)

        # 返回第一条匹配记录（优先级最高）
        record = merged_results[0]

        # 设置首选联系方式
        contact = record.get('phone') or record.get('email', '')
        record['preferred_contact'] = contact

        # 添加匹配信息
        record['matched_keywords'] = [k for k in keywords if k]

        return record

    def recommend_all(
        self,
        key_module: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        根据关键模块推荐所有匹配的答复人

        Args:
            key_module: 关键模块名称
            limit: 返回数量限制

        Returns:
            匹配的答复人列表（按相关度排序）
        """
        if not key_module:
            return []

        # 分割关键字
        keywords = [k.strip() for k in key_module.replace('/', ',').split(',') if k.strip()]

        all_matched: Dict[str, Dict[str, Any]] = {}

        for keyword in keywords:
            if not keyword:
                continue

            results = self.model.search_by_key_module(keyword)

            for record in results:
                # 使用唯一键去重
                unique_key = self.make_unique_key(
                    record.get('name', ''),
                    record.get('employee_id', '')
                )

                if unique_key not in all_matched:
                    all_matched[unique_key] = record

        if not all_matched:
            return []

        # 合并并返回
        merged_results = self.merge_recommendations(list(all_matched.values()))

        # 设置联系方式和匹配关键字
        for record in merged_results:
            contact = record.get('phone') or record.get('email', '')
            record['preferred_contact'] = contact
            record['matched_keywords'] = keywords

        return merged_results[:limit]

    def get_recommendation_source(self, key_module: str) -> str:
        """获取推荐来源说明"""
        keywords = [k.strip() for k in key_module.replace('/', ',').split(',') if k.strip()]

        for keyword in keywords:
            if keyword:
                results = self.model.search_by_key_module(keyword)
                if results:
                    return f"推荐库（智能匹配关键模块：{keyword}）"

        return "无匹配推荐"

    def import_with_merge(
        self,
        records: List[Dict[str, Any]],
        mode: str = 'merge'  # 'merge': 合并, 'replace': 替换, 'skip': 跳过
    ) -> Dict[str, int]:
        """
        导入推荐记录（支持合并模式）

        Args:
            records: 要导入的记录列表
            mode: 导入模式
                - 'merge': 合并同名记录的关键模块
                - 'replace': 替换同名记录
                - 'skip': 跳过已存在的记录

        Returns:
            导入统计 {'added': N, 'updated': N, 'skipped': N}
        """
        stats = {'added': 0, 'updated': 0, 'skipped': 0}

        existing = {rec['name']: rec for rec in self.model.get_all_recommendations()}

        for record in records:
            name = record.get('name', '').strip()
            if not name:
                continue

            if name in existing:
                if mode == 'skip':
                    stats['skipped'] += 1
                elif mode == 'replace':
                    # 替换整个记录
                    existing_id = existing[name].get('id')
                    if existing_id:
                        self.model.update_recommendation(existing_id, record)
                        stats['updated'] += 1
                elif mode == 'merge':
                    # 合并关键模块
                    existing_rec = existing[name]
                    existing_modules = existing_rec.get('key_module', '')
                    new_modules = record.get('key_module', '')

                    # 合并并去重
                    all_modules = set()
                    if existing_modules:
                        all_modules.update(m.strip() for m in existing_modules.replace('/', ',').split(','))
                    if new_modules:
                        all_modules.update(m.strip() for m in new_modules.replace('/', ',').split(','))

                    merged_record = record.copy()
                    merged_record['key_module'] = '、'.join(sorted(all_modules))

                    existing_id = existing[name].get('id')
                    if existing_id:
                        self.model.update_recommendation(existing_id, merged_record)
                        stats['updated'] += 1
            else:
                # 新增记录
                if self.model.add_recommendation(record):
                    stats['added'] += 1

        return stats
