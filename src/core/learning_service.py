# -*- coding: utf-8 -*-
"""
学习积累服务模块
Learning Accumulation Service Module:

从任务数据中自动学习并积累咨询者和答复人的相关信息，
自动丰富通讯录和推荐库数据。
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict

from ..database.connection import get_db_connection
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LearningConfig:
    """学习配置类"""

    # 停用词列表
    STOP_WORDS = {
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个",
        "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
        "自己", "这", "那", "里", "后", "前", "从", "为", "与", "或", "但", "把", "被",
        "给", "让", "请", "对", "以", "能", "可以", "可能", "需要", "应该", "必须"
    }

    # 关键模块最小匹配长度
    MIN_MODULE_LENGTH = 2

    # 最大关键模块数量
    MAX_MODULES_PER_TASK = 10

    # 行业关键词
    INDUSTRY_KEYWORDS = {
        "网络": ["网络", "路由", "交换", "TCP", "IP", "OSPF", "BGP", "VLAN", "ACL"],
        "安全": ["安全", "防火墙", "VPN", "加密", "认证", "入侵", "病毒", "漏洞"],
        "存储": ["存储", "SAN", "NAS", "RAID", "磁盘", "备份", "容灾"],
        "服务器": ["服务器", "CPU", "内存", "硬盘", "虚拟化", "VMware", "Hyper-V"],
        "无线": ["无线", "WiFi", "AP", "AC", "漫游", "信号"],
        "语音": ["语音", "IP电话", "VoIP", "会议", "录音"],
        "数据中心": ["数据中心", "IDC", "机房", "空调", "UPS", "动力"],
        "监控": ["监控", "视频", "摄像头", "NVR", "门禁"],
    }


class ContactLearningService:
    """通讯录学习服务"""

    def __init__(self):
        """初始化通讯录学习服务"""
        self.db = get_db_connection()
        self.config = LearningConfig()
        self._init_contact_tables()

    def _init_contact_tables(self) -> None:
        """初始化联系人学习记录表"""
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS contact_learning_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_name TEXT NOT NULL,
                employee_id TEXT,                -- 工号（用于区分重名）
                learning_source TEXT,             -- 学习来源：inquirer/respondent
                company TEXT,
                industry TEXT,
                task_count INTEGER DEFAULT 1,
                last_task_id TEXT,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_from_recommendation INTEGER DEFAULT 0,
                UNIQUE(contact_name, employee_id, learning_source)
            )
            """,
            commit=True
        )

        # 修改表结构：添加工号字段
        self._migrate_add_employee_id()

        # 创建索引
        self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_learned_contacts_name ON learned_contacts(name)",
            commit=True
        )
        self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_learned_contacts_employee_id ON learned_contacts(employee_id)",
            commit=True
        )
        self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_learned_contacts_industry ON learned_contacts(industry)",
            commit=True
        )
        self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_learned_contacts_name_empid ON learned_contacts(name, employee_id)",
            commit=True
        )

        logger.info("通讯录学习表初始化完成")

    def _migrate_add_employee_id(self) -> None:
        """迁移添加工号字段"""
        # 检查是否已有 employee_id 列
        rows = self.db.fetchall("PRAGMA table_info(learned_contacts)")
        columns = [row[1] for row in rows]

        if "employee_id" not in columns:
            self.db.execute(
                "ALTER TABLE learned_contacts ADD COLUMN employee_id TEXT",
                commit=True
            )
            logger.info("已添加 employee_id 字段")

        # 修改唯一约束
        try:
            self.db.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_learned_contacts_unique
                ON learned_contacts(
                    CASE WHEN employee_id IS NULL OR employee_id = '' THEN name ELSE name || ':' || employee_id END
                )
                """,
                commit=True
            )
        except Exception as e:
            logger.debug(f"索引可能已存在: {e}")  # 索引可能已存在，静默处理

    def learn_from_task(self, task_data: Dict[str, Any]) -> bool:
        """
        从任务数据中学习咨询者信息

        Args:
            task_data: 任务数据字典

        Returns:
            是否学习成功
        """
        try:
            # 学习咨询者信息（支持工号）
            if task_data.get("inquirer"):
                self._learn_contact(
                    name=task_data.get("inquirer", ""),
                    source_type="inquirer",
                    department=task_data.get("inquirer_dept", ""),
                    company=task_data.get("inquirer_company", ""),
                    industry=task_data.get("industry", ""),
                    phone=task_data.get("inquirer_phone", ""),
                    email=task_data.get("inquirer_email", ""),
                    task_id=task_data.get("task_id", ""),
                    employee_id=task_data.get("inquirer_employee_id", "")  # 新增：工号
                )

            # 学习答复人信息（支持工号）
            if task_data.get("respondent"):
                self._learn_contact(
                    name=task_data.get("respondent", ""),
                    source_type="respondent",
                    department=task_data.get("respondent_dept", ""),
                    company="",
                    industry=task_data.get("industry", ""),
                    phone=task_data.get("respondent_phone", ""),
                    email=task_data.get("respondent_email", ""),
                    task_id=task_data.get("task_id", ""),
                    employee_id=task_data.get("respondent_employee_id", "")  # 新增：工号
                )

            return True

        except Exception as e:
            logger.error(f"从任务学习失败: {e}")
            return False

    def _learn_contact(self,
                      name: str,
                      source_type: str,
                      department: str = "",
                      company: str = "",
                      industry: str = "",
                      phone: str = "",
                      email: str = "",
                      task_id: str = "",
                      employee_id: str = "") -> bool:
        """学习单个联系人

        Args:
            name: 姓名
            source_type: 来源类型 (inquirer/respondent)
            department: 部门
            company: 公司
            industry: 行业
            phone: 电话
            email: 邮箱
            task_id: 任务ID
            employee_id: 工号（用于区分重名）
        """
        try:
            if not name:
                return False

            now = datetime.now()

            # 更新或插入联系人学习记录（用工号区分重名）
            self.db.execute(
                """
                INSERT INTO contact_learning_records
                (contact_name, employee_id, learning_source, company, industry, task_count, last_task_id, last_seen)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                ON CONFLICT(contact_name, employee_id, learning_source) DO UPDATE SET
                    task_count = task_count + 1,
                    company = COALESCE(NULLIF(?, ''), company),   -- 新数据覆盖旧数据
                    industry = COALESCE(NULLIF(?, ''), industry), -- 新数据覆盖旧数据
                    department = COALESCE(NULLIF(?, ''), department), -- 新数据覆盖旧数据
                    phone = COALESCE(NULLIF(?, ''), phone),        -- 新数据覆盖旧数据
                    email = COALESCE(NULLIF(?, ''), email),        -- 新数据覆盖旧数据
                    last_task_id = ?,
                    last_seen = ?
                """,
                (name, employee_id, source_type, company, industry, task_id, now,
                 company, industry, department, phone, email, task_id, now),
                commit=True
            )

            # 更新综合联系人表
            self._update_learned_contact(
                name=name,
                employee_id=employee_id,
                source_type=source_type,
                department=department,
                company=company,
                industry=industry,
                phone=phone,
                email=email
            )

            logger.info(f"已学习联系人: {name} (工号:{employee_id or '无'}, 来源:{source_type})")
            return True

        except Exception as e:
            logger.error(f"学习联系人失败: {e}")
            return False

    def _update_learned_contact(self,
                                name: str,
                                employee_id: str = "",
                                source_type: str = "",
                                department: str = "",
                                company: str = "",
                                industry: str = "",
                                phone: str = "",
                                email: str = "") -> bool:
        """更新综合联系人表（支持工号区分重名）"""
        try:
            now = datetime.now()

            # 构建查询条件：优先用工号匹配，其次用姓名
            if employee_id:
                # 有工号：精确匹配姓名+工号
                existing = self.db.fetchone(
                    """SELECT id, source_type, task_count, department, company, industry, phone, email
                       FROM learned_contacts WHERE name = ? AND employee_id = ?""",
                    (name, employee_id)
                )
                check_sql = "SELECT id FROM learned_contacts WHERE name = ? AND employee_id = ?"
                check_params = (name, employee_id)
            else:
                # 无工号：精确匹配姓名+空工号
                existing = self.db.fetchone(
                    """SELECT id, source_type, task_count, department, company, industry, phone, email
                       FROM learned_contacts WHERE name = ? AND (employee_id IS NULL OR employee_id = '')""",
                    (name,)
                )
                check_sql = "SELECT id FROM learned_contacts WHERE name = ? AND (employee_id IS NULL OR employee_id = '')"
                check_params = (name,)

            if existing:
                # 更新现有记录（刷新数据：用新数据覆盖旧数据）
                old_source = existing[1] or ""
                old_count = existing[2] or 0

                # 合并来源类型
                if source_type and source_type not in old_source:
                    new_source = f"{old_source},{source_type}"
                else:
                    new_source = old_source

                self.db.execute(
                    """
                    UPDATE learned_contacts SET
                        source_type = ?,
                        employee_id = COALESCE(NULLIF(?, ''), COALESCE(employee_id, '')),
                        department = ?,
                        company = ?,
                        industry = ?,
                        phone = ?,
                        email = ?,
                        task_count = ?,
                        updated_at = ?
                    WHERE name = ? AND employee_id = ?
                    """,
                    (new_source, employee_id,
                     department or existing[3], company or existing[4],
                     industry or existing[5], phone or existing[6], email or existing[7],
                     old_count + 1, now, name, employee_id or None),
                    commit=True
                )
            else:
                # 新增记录
                self.db.execute(
                    """
                    INSERT INTO learned_contacts
                    (name, employee_id, source_type, department, company, industry, phone, email, task_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    (name, employee_id or None, source_type, department, company, industry, phone, email),
                    commit=True
                )

            return True

        except Exception as e:
            logger.error(f"更新综合联系人失败: {e}")
            return False

    def find_duplicates(self, name: str) -> List[Dict[str, Any]]:
        """查找重名联系人

        Args:
            name: 姓名

        Returns:
            重名联系人列表
        """
        try:
            rows = self.db.fetchall(
                """SELECT id, name, employee_id, company, department, phone, email, task_count
                   FROM learned_contacts WHERE name = ?""",
                (name,)
            )

            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "employee_id": row[2],
                    "company": row[3],
                    "department": row[4],
                    "phone": row[5],
                    "email": row[6],
                    "task_count": row[7]
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"查找重名联系人失败: {e}")
            return []

    def merge_contacts(self, contact_ids: List[int], keep_id: int) -> bool:
        """合并重名联系人

        Args:
            contact_ids: 要合并的联系人ID列表
            keep_id: 保留的联系人ID

        Returns:
            是否合并成功
        """
        try:
            # 获取保留联系人的信息
            keep_contact = self.db.fetchone(
                "SELECT name, employee_id FROM learned_contacts WHERE id = ?",
                (keep_id,)
            )
            if not keep_contact:
                return False

            # 合并其他联系人的任务数
            self.db.execute(
                """
                UPDATE learned_contacts SET
                    task_count = (
                        SELECT COALESCE(SUM(c2.task_count), 0)
                        FROM learned_contacts c2
                        WHERE c2.name = learned_contacts.name
                    ),
                    updated_at = ?
                WHERE id = ?
                """,
                (datetime.now(), keep_id),
                commit=True
            )

            # 删除被合并的联系人
            for cid in contact_ids:
                if cid != keep_id:
                    self.db.execute(
                        "DELETE FROM learned_contacts WHERE id = ?",
                        (cid,),
                        commit=True
                    )

            logger.info(f"已合并重名联系人: {keep_contact[0]}")
            return True

        except Exception as e:
            logger.error(f"合并重名联系人失败: {e}")
            return False

    def get_learned_contacts(self,
                             source_type: Optional[str] = None,
                             keyword: str = "",
                             limit: int = 100) -> List[Dict[str, Any]]:
        """获取学习到的联系人"""
        try:
            conditions = ["1=1"]
            params = []

            if source_type:
                conditions.append("source_type LIKE ?")
                params.append(f"%{source_type}%")

            if keyword:
                conditions.append("(name LIKE ? OR company LIKE ? OR industry LIKE ?)")
                params.extend([f"%{keyword}%"] * 3)

            where_clause = " AND ".join(conditions)

            sql = f"""
                SELECT id, name, source_type, department, company, industry,
                       phone, email, task_count, usage_count, confidence, last_used
                FROM learned_contacts
                WHERE {where_clause}
                ORDER BY task_count DESC, usage_count DESC
                LIMIT ?
            """
            params.append(limit)

            rows = self.db.fetchall(sql, tuple(params))

            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "source_type": row[2],
                    "department": row[3],
                    "company": row[4],
                    "industry": row[5],
                    "phone": row[6],
                    "email": row[7],
                    "task_count": row[8],
                    "usage_count": row[9],
                    "confidence": row[10],
                    "last_used": row[11]
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"获取学习联系人失败: {e}")
            return []

    def export_to_contacts(self, contact_names: List[str]) -> int:
        """导出学习到的联系人到正式通讯录"""
        try:
            count = 0
            for name in contact_names:
                # 从学习记录中获取信息
                rows = self.db.fetchall(
                    """
                    SELECT DISTINCT department, company, industry, phone, email
                    FROM learned_contacts
                    WHERE name = ?
                    LIMIT 1
                    """,
                    (name,)
                )

                if rows:
                    row = rows[0]
                    from ..utils.helpers import generate_id
                    contact_id = generate_id()

                    self.db.execute(
                        """
                        INSERT OR IGNORE INTO contacts
                        (id, name, department, phone, email)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (contact_id, name, row[0] or "", row[3] or "", row[4] or ""),
                        commit=True
                    )
                    count += 1

            logger.info(f"导出{count}个联系人到通讯录")
            return count

        except Exception as e:
            logger.error(f"导出联系人失败: {e}")
            return 0


class RecommendationLearningService:
    """推荐库学习服务"""

    def __init__(self):
        """初始化推荐库学习服务"""
        self.db = get_db_connection()
        self.config = LearningConfig()
        self._init_recommendation_tables()

    def _init_recommendation_tables(self) -> None:
        """初始化推荐库学习表"""
        # 修改表结构：添加工号字段
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendation_learning (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                respondent_name TEXT NOT NULL,
                employee_id TEXT,                   -- 工号（用于区分重名）
                department TEXT,
                key_module TEXT NOT NULL,
                all_modules TEXT,                   -- 该人员所有关键模块（汇总）
                related_modules TEXT,                -- 相关模块（逗号分隔）
                industry TEXT,
                task_count INTEGER DEFAULT 1,
                reply_count INTEGER DEFAULT 0,       -- 答复次数
                avg_response_time REAL,              -- 平均响应时间（小时）
                success_rate REAL DEFAULT 0.0,      -- 成功率
                last_task_id TEXT,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                confidence REAL DEFAULT 0.5,         -- 置信度
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(respondent_name, employee_id, key_module)
            )
            """,
            commit=True
        )

        # 模块关联表
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS module_correlation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_a TEXT NOT NULL,
                module_b TEXT NOT NULL,
                correlation_count INTEGER DEFAULT 1,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(module_a, module_b)
            )
            """,
            commit=True
        )

        # 行业-模块映射表
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS industry_module_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                industry TEXT NOT NULL,
                module TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(industry, module)
            )
            """,
            commit=True
        )

        # 创建索引
        self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_recommendation_learning_respondent ON recommendation_learning(respondent_name)",
            commit=True
        )
        self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_recommendation_learning_employee_id ON recommendation_learning(employee_id)",
            commit=True
        )
        self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_recommendation_learning_module ON recommendation_learning(key_module)",
            commit=True
        )
        self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_recommendation_learning_all_modules ON recommendation_learning(all_modules)",
            commit=True
        )
        self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_industry_module_mapping_industry ON industry_module_mapping(industry)",
            commit=True
        )

        logger.info("推荐库学习表初始化完成")

    def learn_from_task(self, task_data: Dict[str, Any]) -> bool:
        """
        从任务数据中学习推荐信息

        Args:
            task_data: 任务数据字典

        Returns:
            是否学习成功
        """
        try:
            if not task_data.get("respondent") or not task_data.get("key_module"):
                return False

            # 提取关键模块
            key_modules = self._extract_key_modules(
                task_data.get("key_module", ""),
                task_data.get("task_content", "")
            )

            if not key_modules:
                return False

            # 获取工号
            employee_id = task_data.get("respondent_employee_id", "")

            # 学习每个关键模块
            for module in key_modules:
                self._learn_recommendation(
                    respondent_name=task_data.get("respondent", ""),
                    department=task_data.get("respondent_dept", ""),
                    key_module=module,
                    related_modules=key_modules,
                    industry=task_data.get("industry", ""),
                    task_id=task_data.get("task_id", ""),
                    status=task_data.get("status", ""),
                    employee_id=employee_id
                )

            # 更新模块关联
            self._update_module_correlation(key_modules)

            # 更新行业-模块映射
            if task_data.get("industry"):
                self._update_industry_module_mapping(
                    industry=task_data.get("industry", ""),
                    modules=key_modules
                )

            return True

        except Exception as e:
            logger.error(f"从任务学习推荐信息失败: {e}")
            return False

    def _extract_key_modules(self, key_module: str, task_content: str) -> List[str]:
        """提取关键模块列表"""
        modules = set()

        # 从关键模块字段提取
        if key_module:
            # 支持多种分隔符
            for sep in ["、", "/", ",", "，"]:
                if sep in key_module:
                    parts = key_module.split(sep)
                    modules.update([p.strip() for p in parts if p.strip()])
                    break
            else:
                modules.add(key_module.strip())

        # 从任务内容中提取
        if task_content:
            # 匹配常见模块关键词
            module_patterns = [
                r"(?:OSPF|RIP|BGP|ISIS)",          # 路由协议
                r"(?:VLAN|STP|RSTP|MSTP)",         # 二层协议
                r"(?:ACL|NAT|PAT|PFW)",             # 安全策略
                r"(?:VPN|IPSec|SSL)",              # VPN
                r"(?:堆叠|集群|IRF|VSF)",          # 堆叠技术
                r"(?:无线|WiFi|AP|AC|漫游)",        # 无线
                r"(?:防火墙|WAF|IPS|IDS)",         # 安全设备
                r"(?:负载均衡|SLB|AS)",             # 负载均衡
                r"(?:SDN|VXLAN|Overlay)",           # 新技术
            ]

            for pattern in module_patterns:
                matches = re.findall(pattern, task_content)
                modules.update(matches)

        # 过滤并限制数量
        result = [
            m for m in modules
            if len(m) >= self.config.MIN_MODULE_LENGTH
            and m not in self.config.STOP_WORDS
        ]

        return result[:self.config.MAX_MODULES_PER_TASK]

    def _learn_recommendation(self,
                              respondent_name: str,
                              department: str,
                              key_module: str,
                              related_modules: List[str],
                              industry: str,
                              task_id: str,
                              status: str,
                              employee_id: str = "") -> bool:
        """学习推荐信息（支持工号区分重名，all_modules累加）

        Args:
            respondent_name: 答复人姓名
            department: 部门
            key_module: 关键模块
            related_modules: 相关模块列表
            industry: 行业
            task_id: 任务ID
            status: 任务状态
            employee_id: 工号（用于区分重名）
        """
        try:
            now = datetime.now()

            # 计算相关模块
            other_modules = [m for m in related_modules if m != key_module]
            related_str = ",".join(other_modules[:5])  # 最多保留5个

            # 判断是否成功答复
            is_replied = status in ["已答复", "完成"]

            # 查询现有记录的all_modules
            if employee_id:
                existing = self.db.fetchone(
                    """SELECT all_modules, task_count FROM recommendation_learning
                       WHERE respondent_name = ? AND employee_id = ? AND key_module = ?""",
                    (respondent_name, employee_id, key_module)
                )
            else:
                existing = self.db.fetchone(
                    """SELECT all_modules, task_count FROM recommendation_learning
                       WHERE respondent_name = ? AND (employee_id IS NULL OR employee_id = '') AND key_module = ?""",
                    (respondent_name, key_module)
                )

            # 计算累加的all_modules（汇总该人所有关键模块）
            if existing and existing[0]:
                existing_modules = set(existing[0].split(",")) if existing[0] else set()
                # 将当前任务的模块加入汇总
                existing_modules.update(related_modules)
                all_modules_str = ",".join(sorted(existing_modules))
            else:
                all_modules_str = ",".join(related_modules)

            # 插入或更新记录
            if employee_id:
                self.db.execute(
                    """
                    INSERT INTO recommendation_learning
                    (respondent_name, employee_id, department, key_module, all_modules, related_modules, industry,
                     task_count, reply_count, last_task_id, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                    ON CONFLICT(respondent_name, employee_id, key_module) DO UPDATE SET
                        department = COALESCE(NULLIF(?, ''), department),
                        all_modules = ?,
                        related_modules = ?,
                        industry = COALESCE(NULLIF(?, ''), industry),
                        task_count = task_count + 1,
                        reply_count = reply_count + ?,
                        last_task_id = ?,
                        last_seen = ?,
                        success_rate = CAST(reply_count + ? AS REAL) / (task_count + 1),
                        confidence = MIN(1.0, 0.5 + (task_count + 1) * 0.05),
                        updated_at = ?
                    """,
                    (
                        respondent_name, employee_id, department, key_module, all_modules_str, related_str, industry,
                        1 if is_replied else 0, task_id, now,
                        department, all_modules_str, related_str, industry,
                        1 if is_replied else 0, task_id, now,
                        1 if is_replied else 0, now
                    ),
                    commit=True
                )
            else:
                self.db.execute(
                    """
                    INSERT INTO recommendation_learning
                    (respondent_name, employee_id, department, key_module, all_modules, related_modules, industry,
                     task_count, reply_count, last_task_id, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                    ON CONFLICT(respondent_name, employee_id, key_module) DO UPDATE SET
                        department = COALESCE(NULLIF(?, ''), department),
                        all_modules = ?,
                        related_modules = ?,
                        industry = COALESCE(NULLIF(?, ''), industry),
                        task_count = task_count + 1,
                        reply_count = reply_count + ?,
                        last_task_id = ?,
                        last_seen = ?,
                        success_rate = CAST(reply_count + ? AS REAL) / (task_count + 1),
                        confidence = MIN(1.0, 0.5 + (task_count + 1) * 0.05),
                        updated_at = ?
                    """,
                    (
                        respondent_name, None, department, key_module, all_modules_str, related_str, industry,
                        1 if is_replied else 0, task_id, now,
                        department, all_modules_str, related_str, industry,
                        1 if is_replied else 0, task_id, now,
                        1 if is_replied else 0, now
                    ),
                    commit=True
                )

            logger.info(f"已学习推荐信息: {respondent_name} (工号:{employee_id or '无'}) - {key_module}")
            return True

        except Exception as e:
            logger.error(f"学习推荐信息失败: {e}")
            return False

    def _update_module_correlation(self, modules: List[str]) -> bool:
        """更新模块关联"""
        try:
            now = datetime.now()

            # 更新两两关联
            for i, mod_a in enumerate(modules):
                for mod_b in modules[i + 1:]:
                    # 确保顺序一致
                    if mod_a > mod_b:
                        mod_a, mod_b = mod_b, mod_a

                    self.db.execute(
                        """
                        INSERT INTO module_correlation
                        (module_a, module_b, correlation_count, last_seen)
                        VALUES (?, ?, 1, ?)
                        ON CONFLICT(module_a, module_b) DO UPDATE SET
                            correlation_count = correlation_count + 1,
                            last_seen = ?
                        """,
                        (mod_a, mod_b, now, now),
                        commit=True
                    )

            return True

        except Exception as e:
            logger.error(f"更新模块关联失败: {e}")
            return False

    def _update_industry_module_mapping(self, industry: str, modules: List[str]) -> bool:
        """更新行业-模块映射"""
        try:
            now = datetime.now()

            for module in modules:
                self.db.execute(
                    """
                    INSERT INTO industry_module_mapping
                    (industry, module, frequency, last_seen)
                    VALUES (?, ?, 1, ?)
                    ON CONFLICT(industry, module) DO UPDATE SET
                        frequency = frequency + 1,
                        last_seen = ?
                    """,
                    (industry, module, now, now),
                    commit=True
                )

            return True

        except Exception as e:
            logger.error(f"更新行业模块映射失败: {e}")
            return False

    def get_recommendations(self, key_module: str = "",
                            industry: str = "",
                            limit: int = 20) -> List[Dict[str, Any]]:
        """获取推荐（支持all_modules汇总匹配）

        匹配逻辑：
        1. 精确匹配 key_module
        2. 在 related_modules 中匹配
        3. 在 all_modules（汇总所有模块）中匹配

        Args:
            key_module: 关键模块
            industry: 行业
            limit: 返回数量限制

        Returns:
            推荐列表
        """
        try:
            conditions = ["1=1"]
            params = []

            if key_module:
                # 三层匹配：key_module, related_modules, all_modules
                conditions.append(
                    "(key_module LIKE ? OR related_modules LIKE ? OR all_modules LIKE ?)"
                )
                params.extend([f"%{key_module}%"] * 3)

            if industry:
                conditions.append("industry LIKE ?")
                params.append(f"%{industry}%")

            where_clause = " AND ".join(conditions)

            sql = f"""
                SELECT respondent_name, employee_id, department, key_module, all_modules,
                       related_modules, industry, task_count, reply_count, success_rate, confidence
                FROM recommendation_learning
                WHERE {where_clause}
                ORDER BY confidence DESC, task_count DESC, success_rate DESC
                LIMIT ?
            """
            params.append(limit)

            rows = self.db.fetchall(sql, tuple(params))

            return [
                {
                    "respondent_name": row[0],
                    "employee_id": row[1],
                    "department": row[2],
                    "key_module": row[3],
                    "all_modules": row[4],  # 该人所有关键模块汇总
                    "related_modules": row[5],
                    "industry": row[6],
                    "task_count": row[7],
                    "reply_count": row[8],
                    "success_rate": row[9],
                    "confidence": row[10]
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"获取推荐失败: {e}")
            return []

    def get_aggregated_recommendations(self,
                                       key_module: str = "",
                                       industry: str = "",
                                       limit: int = 20) -> List[Dict[str, Any]]:
        """获取汇总视图推荐（按人员聚合，显示所有关键模块）

        例如：赵六有 MAC认证 和 802.1x认证 两个记录，
        汇总后显示为：赵六 - MAC认证、802.1x认证

        Args:
            key_module: 关键模块
            industry: 行业
            limit: 返回数量限制

        Returns:
            汇总后的推荐列表
        """
        try:
            conditions = ["1=1"]
            params = []

            # 如果指定了模块，需要在聚合结果中匹配
            if key_module:
                # 匹配 key_module 或 all_modules 中包含该模块的人员
                conditions.append(
                    "(key_module LIKE ? OR all_modules LIKE ?)"
                )
                params.extend([f"%{key_module}%"] * 2)

            if industry:
                conditions.append("industry LIKE ?")
                params.append(f"%{industry}%")

            where_clause = " AND ".join(conditions)

            # 按人员聚合，合并所有关键模块
            sql = f"""
                SELECT
                    respondent_name,
                    employee_id,
                    department,
                    GROUP_CONCAT(DISTINCT key_module) as all_modules,
                    MAX(related_modules) as related_modules,
                    industry,
                    SUM(task_count) as total_task_count,
                    SUM(reply_count) as total_reply_count,
                    AVG(success_rate) as avg_success_rate,
                    MAX(confidence) as max_confidence,
                    COUNT(*) as module_count
                FROM recommendation_learning
                WHERE {where_clause}
                GROUP BY respondent_name, employee_id
                ORDER BY max_confidence DESC, total_task_count DESC, avg_success_rate DESC
                LIMIT ?
            """
            params.append(limit)

            rows = self.db.fetchall(sql, tuple(params))

            return [
                {
                    "respondent_name": row[0],
                    "employee_id": row[1],
                    "department": row[2],
                    "all_modules": row[3],  # 逗号分隔的所有模块
                    "module_list": row[3].split(",") if row[3] else [],  # 数组形式
                    "related_modules": row[4],
                    "industry": row[5],
                    "total_task_count": row[6],
                    "total_reply_count": row[7],
                    "avg_success_rate": round(row[8], 2) if row[8] else 0,
                    "max_confidence": row[9],
                    "module_count": row[10]  # 该人擅长的模块数量
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"获取汇总推荐失败: {e}")
            return []

    def find_expert_by_module(self, key_module: str) -> List[Dict[str, Any]]:
        """根据模块查找专家（返回汇总信息）

        Args:
            key_module: 关键模块

        Returns:
            擅长该模块的人员列表
        """
        return self.get_aggregated_recommendations(key_module=key_module, limit=10)

    def get_related_modules(self, key_module: str, limit: int = 5) -> List[str]:
        """获取相关模块"""
        try:
            # 从module_correlation获取
            rows = self.db.fetchall(
                """
                SELECT module_b, correlation_count
                FROM module_correlation
                WHERE module_a = ?
                ORDER BY correlation_count DESC
                LIMIT ?
                """,
                (key_module, limit)
            )

            # 也从recommendation_learning获取
            rows2 = self.db.fetchall(
                """
                SELECT key_module, SUM(task_count)
                FROM recommendation_learning
                WHERE related_modules LIKE ?
                GROUP BY key_module
                ORDER BY SUM(task_count) DESC
                LIMIT ?
                """,
                (f"%{key_module}%", limit)
            )

            # 合并结果
            modules = []
            seen = set()
            seen.add(key_module)

            for row in rows:
                if row[0] not in seen:
                    modules.append(row[0])
                    seen.add(row[0])

            for row in rows2:
                if row[0] not in seen:
                    modules.append(row[0])
                    seen.add(row[0])

            return modules[:limit]

        except Exception as e:
            logger.error(f"获取相关模块失败: {e}")
            return []

    def get_industry_modules(self, industry: str) -> List[Dict[str, Any]]:
        """获取行业常用模块"""
        try:
            rows = self.db.fetchall(
                """
                SELECT module, frequency
                FROM industry_module_mapping
                WHERE industry = ?
                ORDER BY frequency DESC
                """,
                (industry,)
            )

            return [
                {"module": row[0], "frequency": row[1]}
                for row in rows
            ]

        except Exception as e:
            logger.error(f"获取行业模块失败: {e}")
            return []

    def update_usage_count(self, respondent_name: str, key_module: str) -> bool:
        """更新使用次数"""
        try:
            self.db.execute(
                """
                UPDATE recommendation_learning
                SET confidence = MIN(1.0, confidence + 0.1),
                    updated_at = ?
                WHERE respondent_name = ? AND key_module = ?
                """,
                (datetime.now(), respondent_name, key_module),
                commit=True
            )
            return True

        except Exception as e:
            logger.error(f"更新使用次数失败: {e}")
            return False


class LearningService:
    """综合学习服务"""

    def __init__(self):
        """初始化综合学习服务"""
        self.contact_service = ContactLearningService()
        self.recommendation_service = RecommendationLearningService()
        self.db = get_db_connection()

    def learn_from_all_tasks(self, progress_callback=None) -> Dict[str, Any]:
        """
        从所有任务中学习

        Args:
            progress_callback: 进度回调函数

        Returns:
            学习结果统计
        """
        try:
            if progress_callback:
                progress_callback(0, 100, "正在加载所有任务...")

            # 获取所有任务
            rows = self.db.fetchall("SELECT * FROM tasks ORDER BY created_at")

            total = len(rows)
            contact_count = 0
            rec_count = 0

            for i, row in enumerate(rows):
                task_data = self._row_to_dict(row)

                # 学习通讯录
                if self.contact_service.learn_from_task(task_data):
                    contact_count += 1

                # 学习推荐库
                if self.recommendation_service.learn_from_task(task_data):
                    rec_count += 1

                if progress_callback:
                    progress = int((i + 1) / total * 100)
                    progress_callback(progress, 100, f"正在学习... {i + 1}/{total}")

            result = {
                "total_tasks": total,
                "contacts_learned": contact_count,
                "recommendations_learned": rec_count,
                "success": True
            }

            logger.info(f"批量学习完成: 学习了{contact_count}个联系人, {rec_count}条推荐")
            return result

        except Exception as e:
            logger.error(f"批量学习失败: {e}")
            return {"success": False, "error": str(e)}

    def learn_from_task(self, task_data: Dict[str, Any]) -> bool:
        """
        从单个任务中学习

        Args:
            task_data: 任务数据

        Returns:
            是否学习成功
        """
        try:
            # 学习通讯录
            self.contact_service.learn_from_task(task_data)

            # 学习推荐库
            self.recommendation_service.learn_from_task(task_data)

            return True

        except Exception as e:
            logger.error(f"学习任务失败: {e}")
            return False

    def _row_to_dict(self, row: tuple) -> Dict[str, Any]:
        """将数据库行转换为字典"""
        columns = [
            "task_id", "task_name", "inquirer", "inquirer_dept", "inquirer_company",
            "inquirer_phone", "inquirer_email", "inquirer_employee_id",  # 新增
            "respondent", "respondent_dept", "respondent_employee_id",    # 新增
            "industry", "key_module", "task_content", "urgency", "status",
            "expected_reply_time", "actual_reply_time", "reply_status", "reply_content",
            "created_at", "updated_at", "created_by", "remark",
        ]
        return dict(zip(columns, row))

    def get_statistics(self) -> Dict[str, Any]:
        """获取学习统计"""
        try:
            # 通讯录学习统计
            contact_stats = self.db.fetchone(
                "SELECT COUNT(*), SUM(task_count) FROM learned_contacts"
            )

            # 推荐库学习统计
            rec_stats = self.db.fetchone(
                "SELECT COUNT(*), SUM(task_count) FROM recommendation_learning"
            )

            # 模块统计
            module_count = self.db.fetchone(
                "SELECT COUNT(DISTINCT key_module) FROM recommendation_learning"
            )

            # 行业统计
            industry_count = self.db.fetchone(
                "SELECT COUNT(DISTINCT industry) FROM recommendation_learning WHERE industry IS NOT NULL AND industry != ''"
            )

            return {
                "total_learned_contacts": contact_stats[0] if contact_stats else 0,
                "total_contact_tasks": contact_stats[1] if contact_stats else 0,
                "total_recommendations": rec_stats[0] if rec_stats else 0,
                "total_recommendation_tasks": rec_stats[1] if rec_stats else 0,
                "unique_modules": module_count[0] if module_count else 0,
                "unique_industries": industry_count[0] if industry_count else 0,
            }

        except Exception as e:
            logger.error(f"获取学习统计失败: {e}")
            return {}


# 全局服务实例
_learning_service: Optional[LearningService] = None


def get_learning_service() -> LearningService:
    """获取学习服务实例"""
    global _learning_service
    if _learning_service is None:
        _learning_service = LearningService()
    return _learning_service


def get_contact_learning_service() -> ContactLearningService:
    """获取通讯录学习服务实例"""
    return get_learning_service().contact_service


def get_recommendation_learning_service() -> RecommendationLearningService:
    """获取推荐库学习服务实例"""
    return get_learning_service().recommendation_service
