# -*- coding: utf-8 -*-
"""
数据模型模块
Data Models Module

定义数据库表结构和数据模型
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# 延迟导入避免循环依赖
_logger = None

def _get_logger():
    global _logger
    if _logger is None:
        from ..utils.logger import get_logger
        _logger = get_logger(__name__)
    return _logger


class TaskStatus(Enum):
    """任务状态枚举"""

    IN_PROGRESS = "进行中"
    PENDING = "挂起"
    REPLIED = "已答复"
    COMPLETED = "完成"


class TaskUrgency(Enum):
    """任务重要程度枚举"""

    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"


class ReplyStatus(Enum):
    """答复状态枚举"""

    WAITING = "等待答复"
    REPLIED = "已答复"
    NO_REPLY = "无需答复"


class BaseModel:
    """基础模型类"""

    def __init__(self) -> None:
        """初始化基础模型"""
        self._db = get_db_connection()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseModel":
        """从字典创建实例"""
        instance = cls()
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        return instance


class Task(BaseModel):
    """任务模型"""

    def __init__(
        self,
        task_id: Optional[str] = None,
        task_name: str = "",
        inquirer: str = "",
        inquirer_dept: str = "",
        inquirer_company: str = "",
        inquirer_phone: str = "",
        inquirer_email: str = "",
        respondent: str = "",
        respondent_dept: str = "",
        industry: str = "",
        key_module: str = "",
        task_content: str = "",
        urgency: str = "中",
        status: str = "进行中",
        expected_reply_time: Optional[datetime] = None,
        actual_reply_time: Optional[datetime] = None,
        reply_status: str = "等待答复",
        reply_content: str = "",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        created_by: str = "",
        remark: str = "",
    ) -> None:
        """
        初始化任务

        Args:
            task_id: 任务ID
            task_name: 任务名称
            inquirer: 咨询者姓名
            inquirer_dept: 咨询者部门
            inquirer_company: 咨询者公司
            inquirer_phone: 咨询者电话
            inquirer_email: 咨询者邮箱
            respondent: 答复人姓名
            respondent_dept: 答复人部门
            industry: 所属行业
            key_module: 关键模块
            task_content: 任务内容
            urgency: 重要程度
            status: 任务状态
            expected_reply_time: 预期答复时间
            actual_reply_time: 实际答复时间
            reply_status: 答复状态
            reply_content: 答复内容
            created_at: 创建时间
            updated_at: 更新时间
            created_by: 创建人
            remark: 备注
        """
        super().__init__()
        self.task_id = task_id or generate_id()
        self.task_name = task_name
        self.inquirer = inquirer
        self.inquirer_dept = inquirer_dept
        self.inquirer_company = inquirer_company
        self.inquirer_phone = inquirer_phone
        self.inquirer_email = inquirer_email
        self.respondent = respondent
        self.respondent_dept = respondent_dept
        self.industry = industry
        self.key_module = key_module
        self.task_content = task_content
        self.urgency = urgency
        self.status = status
        self.expected_reply_time = expected_reply_time
        self.actual_reply_time = actual_reply_time
        self.reply_status = reply_status
        self.reply_content = reply_content
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.created_by = created_by
        self.remark = remark

    def save(self) -> bool:
        """
        保存任务到数据库

        Returns:
            是否保存成功
        """
        try:
            self.updated_at = datetime.now()
            data = self.to_dict()

            # 检查任务是否已存在
            existing = self._db.fetchone(
                "SELECT task_id FROM tasks WHERE task_id = ?", (self.task_id,)
            )

            if existing:
                # 更新
                update_fields = [k for k in data.keys() if k != "task_id"]
                set_clause = ", ".join([f"{k} = ?" for k in update_fields])
                values = [data[k] for k in update_fields]
                values.append(self.task_id)
                sql = f"UPDATE tasks SET {set_clause} WHERE task_id = ?"
                self._db.execute(sql, tuple(values), commit=True)
                _get_logger().info(f"任务更新成功: {self.task_id}")
            else:
                # 新增
                columns = ", ".join(data.keys())
                placeholders = ", ".join(["?" for _ in data])
                sql = f"INSERT INTO tasks ({columns}) VALUES ({placeholders})"
                self._db.execute(sql, tuple(data.values()), commit=True)
                _get_logger().info(f"任务创建成功: {self.task_id}")

            return True
        except Exception as e:
            _get_logger().error(f"保存任务失败: {e}")
            return False

    def delete(self) -> bool:
        """
        删除任务

        Returns:
            是否删除成功
        """
        try:
            self._db.delete("tasks", "task_id = ?", (self.task_id,))
            _get_logger().info(f"任务删除成功: {self.task_id}")
            return True
        except Exception as e:
            _get_logger().error(f"删除任务失败: {e}")
            return False

    @classmethod
    def get_by_id(cls, task_id: str) -> Optional["Task"]:
        """
        根据ID获取任务

        Args:
            task_id: 任务ID

        Returns:
            任务对象，如果不存在返回None
        """
        db = get_db_connection()
        row = db.fetchone("SELECT * FROM tasks WHERE task_id = ?", (task_id,))

        if row:
            columns = [
                "task_id",
                "task_name",
                "inquirer",
                "inquirer_dept",
                "inquirer_company",
                "inquirer_phone",
                "inquirer_email",
                "respondent",
                "respondent_dept",
                "industry",
                "key_module",
                "task_content",
                "urgency",
                "status",
                "expected_reply_time",
                "actual_reply_time",
                "reply_status",
                "reply_content",
                "created_at",
                "updated_at",
                "created_by",
                "remark",
            ]
            data = dict(zip(columns, row))
            return cls.from_dict(data)

        return None

    @classmethod
    def get_all(cls) -> List["Task"]:
        """
        获取所有任务

        Returns:
            任务列表
        """
        db = get_db_connection()
        rows = db.fetchall("SELECT * FROM tasks ORDER BY created_at DESC")

        tasks = []
        columns = [
            "task_id",
            "task_name",
            "inquirer",
            "inquirer_dept",
            "inquirer_company",
            "inquirer_phone",
            "inquirer_email",
            "respondent",
            "respondent_dept",
            "industry",
            "key_module",
            "task_content",
            "urgency",
            "status",
            "expected_reply_time",
            "actual_reply_time",
            "reply_status",
            "reply_content",
            "created_at",
            "updated_at",
            "created_by",
            "remark",
        ]

        for row in rows:
            data = dict(zip(columns, row))
            tasks.append(cls.from_dict(data))

        return tasks

    @classmethod
    def search(cls, keyword: str) -> List["Task"]:
        """
        搜索任务

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的任务列表
        """
        db = get_db_connection()
        sql = """
            SELECT * FROM tasks
            WHERE task_name LIKE ?
               OR task_content LIKE ?
               OR inquirer LIKE ?
               OR respondent LIKE ?
               OR key_module LIKE ?
            ORDER BY created_at DESC
        """
        pattern = f"%{keyword}%"
        rows = db.fetchall(sql, (pattern,) * 5)

        tasks = []
        columns = [
            "task_id",
            "task_name",
            "inquirer",
            "inquirer_dept",
            "inquirer_company",
            "inquirer_phone",
            "inquirer_email",
            "respondent",
            "respondent_dept",
            "industry",
            "key_module",
            "task_content",
            "urgency",
            "status",
            "expected_reply_time",
            "actual_reply_time",
            "reply_status",
            "reply_content",
            "created_at",
            "updated_at",
            "created_by",
            "remark",
        ]

        for row in rows:
            data = dict(zip(columns, row))
            tasks.append(cls.from_dict(data))

        return tasks


class TaskTrackRecord(BaseModel):
    """任务跟踪记录模型"""

    def __init__(
        self,
        record_id: Optional[str] = None,
        task_id: str = "",
        track_content: str = "",
        track_status: str = "",
        track_time: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
    ) -> None:
        """
        初始化跟踪记录

        Args:
            record_id: 记录ID
            task_id: 任务ID
            track_content: 跟踪内容
            track_status: 跟踪状态
            track_time: 跟踪时间
            created_at: 创建时间
        """
        super().__init__()
        self.record_id = record_id or generate_id()
        self.task_id = task_id
        self.track_content = track_content
        self.track_status = track_status
        self.track_time = track_time or datetime.now()
        self.created_at = created_at or datetime.now()

    def save(self) -> bool:
        """保存跟踪记录"""
        try:
            data = self.to_dict()
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            sql = f"INSERT INTO task_track_records ({columns}) VALUES ({placeholders})"
            self._db.execute(sql, tuple(data.values()), commit=True)
            _get_logger().info(f"跟踪记录创建成功: {self.record_id}")
            return True
        except Exception as e:
            _get_logger().error(f"保存跟踪记录失败: {e}")
            return False

    @classmethod
    def get_by_task_id(cls, task_id: str) -> List["TaskTrackRecord"]:
        """根据任务ID获取跟踪记录"""
        db = get_db_connection()
        rows = db.fetchall(
            "SELECT * FROM task_track_records WHERE task_id = ? ORDER BY track_time DESC",
            (task_id,),
        )

        records = []
        columns = ["record_id", "task_id", "track_content", "track_status", "track_time", "created_at"]

        for row in rows:
            data = dict(zip(columns, row))
            records.append(cls.from_dict(data))

        return records


class Recommendation(BaseModel):
    """智能推荐模型"""

    def __init__(
        self,
        rec_id: Optional[str] = None,
        source_task_id: str = "",
        target_task_id: str = "",
        similarity: float = 0.0,
        recommendation_type: str = "",
        feedback: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> None:
        """
        初始化推荐记录

        Args:
            rec_id: 推荐ID
            source_task_id: 源任务ID
            target_task_id: 目标任务ID
            similarity: 相似度
            recommendation_type: 推荐类型
            feedback: 反馈
            created_at: 创建时间
        """
        super().__init__()
        self.rec_id = rec_id or generate_id()
        self.source_task_id = source_task_id
        self.target_task_id = target_task_id
        self.similarity = similarity
        self.recommendation_type = recommendation_type
        self.feedback = feedback
        self.created_at = created_at or datetime.now()

    def save(self) -> bool:
        """保存推荐记录"""
        try:
            data = self.to_dict()
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            sql = f"INSERT INTO recommendations ({columns}) VALUES ({placeholders})"
            self._db.execute(sql, tuple(data.values()), commit=True)
            _get_logger().info(f"推荐记录创建成功: {self.rec_id}")
            return True
        except Exception as e:
            _get_logger().error(f"保存推荐记录失败: {e}")
            return False


class Reminder(BaseModel):
    """提醒记录模型"""

    def __init__(
        self,
        reminder_id: Optional[str] = None,
        task_id: str = "",
        reminder_time: Optional[datetime] = None,
        reminder_type: str = "",
        is_triggered: bool = False,
        triggered_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
    ) -> None:
        """
        初始化提醒记录

        Args:
            reminder_id: 提醒ID
            task_id: 任务ID
            reminder_time: 提醒时间
            reminder_type: 提醒类型
            is_triggered: 是否已触发
            triggered_at: 触发时间
            created_at: 创建时间
        """
        super().__init__()
        self.reminder_id = reminder_id or generate_id()
        self.task_id = task_id
        self.reminder_time = reminder_time or datetime.now()
        self.reminder_type = reminder_type
        self.is_triggered = is_triggered
        self.triggered_at = triggered_at
        self.created_at = created_at or datetime.now()

    def save(self) -> bool:
        """保存提醒记录"""
        try:
            data = self.to_dict()
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            sql = f"INSERT INTO reminders ({columns}) VALUES ({placeholders})"
            self._db.execute(sql, tuple(data.values()), commit=True)
            _get_logger().info(f"提醒记录创建成功: {self.reminder_id}")
            return True
        except Exception as e:
            _get_logger().error(f"保存提醒记录失败: {e}")
            return False

    def trigger(self) -> bool:
        """触发提醒"""
        try:
            self.is_triggered = True
            self.triggered_at = datetime.now()
            data = self.to_dict()

            update_fields = ["is_triggered", "triggered_at"]
            set_clause = ", ".join([f"{k} = ?" for k in update_fields])
            values = [data[k] for k in update_fields]
            values.append(self.reminder_id)

            sql = f"UPDATE reminders SET {set_clause} WHERE reminder_id = ?"
            self._db.execute(sql, tuple(values), commit=True)
            _get_logger().info(f"提醒已触发: {self.reminder_id}")
            return True
        except Exception as e:
            _get_logger().error(f"触发提醒失败: {e}")
            return False


def init_database() -> bool:
    """
    初始化数据库表结构

    Returns:
        是否初始化成功
    """
    db = get_db_connection()

    # 创建任务表
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            task_name TEXT,
            inquirer TEXT,
            inquirer_dept TEXT,
            inquirer_company TEXT,
            inquirer_phone TEXT,
            inquirer_email TEXT,
            respondent TEXT,
            respondent_dept TEXT,
            industry TEXT,
            key_module TEXT,
            task_content TEXT,
            urgency TEXT DEFAULT '中',
            status TEXT DEFAULT '进行中',
            expected_reply_time DATETIME,
            actual_reply_time DATETIME,
            reply_status TEXT DEFAULT '等待答复',
            reply_content TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT,
            remark TEXT
        )
    """,
        commit=True,
    )

    # 创建跟踪记录表
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS task_track_records (
            record_id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            track_content TEXT,
            track_status TEXT,
            track_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
        )
    """,
        commit=True,
    )

    # 创建推荐表
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS recommendations (
            rec_id TEXT PRIMARY KEY,
            source_task_id TEXT NOT NULL,
            target_task_id TEXT NOT NULL,
            similarity REAL DEFAULT 0.0,
            recommendation_type TEXT,
            feedback TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
            FOREIGN KEY (target_task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
        )
    """,
        commit=True,
    )

    # 创建提醒表
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS reminders (
            reminder_id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            reminder_time DATETIME NOT NULL,
            reminder_type TEXT,
            is_triggered INTEGER DEFAULT 0,
            triggered_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
        )
    """,
        commit=True,
    )

    # 创建推荐库表
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS recommendation_library (
            lib_id TEXT PRIMARY KEY,
            keywords TEXT,
            related_module TEXT,
            related_content TEXT,
            usage_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """,
        commit=True,
    )

    # 创建索引
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
        commit=True,
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)",
        commit=True,
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_track_records_task_id ON task_track_records(task_id)",
        commit=True,
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_reminders_task_id ON reminders(task_id)",
        commit=True,
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_reminders_time ON reminders(reminder_time)",
        commit=True,
    )

    _get_logger().info("数据库表结构初始化完成")
    return True
