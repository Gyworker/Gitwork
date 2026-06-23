# -*- coding: utf-8 -*-
"""
数据库访问层
Database Access Layer

提供数据库操作的封装
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from database.connection import get_db_connection
from utils.logger import get_logger

logger = get_logger(__name__)


class TaskDAO:
    """任务数据访问对象"""

    def __init__(self) -> None:
        """初始化DAO"""
        self._db = get_db_connection()

    def create(self, data: Dict[str, Any]) -> Optional[str]:
        """
        创建任务

        Args:
            data: 任务数据

        Returns:
            任务ID，失败返回None
        """
        try:
            from ..utils.helpers import generate_id

            task_id = data.get("task_id") or generate_id()
            data["task_id"] = task_id

            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            sql = f"INSERT INTO tasks ({columns}) VALUES ({placeholders})"

            self._db.execute(sql, tuple(data.values()), commit=True)
            logger.info(f"任务创建成功: {task_id}")
            return task_id
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            return None

    def get_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取任务

        Args:
            task_id: 任务ID

        Returns:
            任务数据字典
        """
        try:
            sql = "SELECT * FROM tasks WHERE task_id = ?"
            row = self._db.fetchone(sql, (task_id,))
            if row:
                return self._row_to_dict(row)
            return None
        except Exception as e:
            logger.error(f"获取任务失败: {e}")
            return None

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        获取所有任务

        Args:
            filters: 过滤条件

        Returns:
            任务列表
        """
        try:
            sql = "SELECT * FROM tasks"
            params = []

            if filters:
                conditions = []
                for key, value in filters.items():
                    if value is not None:
                        conditions.append(f"{key} = ?")
                        params.append(value)

                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)

            sql += " ORDER BY created_at DESC"
            rows = self._db.fetchall(sql, tuple(params) if params else None)
            return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return []

    def update(self, task_id: str, data: Dict[str, Any]) -> bool:
        """
        更新任务

        Args:
            task_id: 任务ID
            data: 更新数据

        Returns:
            是否成功
        """
        try:
            data["updated_at"] = datetime.now()

            set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
            sql = f"UPDATE tasks SET {set_clause} WHERE task_id = ?"

            params = list(data.values()) + [task_id]
            self._db.execute(sql, tuple(params), commit=True)
            logger.info(f"任务更新成功: {task_id}")
            return True
        except Exception as e:
            logger.error(f"更新任务失败: {e}")
            return False

    def delete(self, task_id: str) -> bool:
        """
        删除任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        try:
            self._db.delete("tasks", "task_id = ?", (task_id,))
            logger.info(f"任务删除成功: {task_id}")
            return True
        except Exception as e:
            logger.error(f"删除任务失败: {e}")
            return False

    def search(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索任务

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的任务列表
        """
        try:
            pattern = f"%{keyword}%"
            sql = """
                SELECT * FROM tasks
                WHERE task_name LIKE ?
                   OR task_content LIKE ?
                   OR inquirer LIKE ?
                   OR respondent LIKE ?
                   OR key_module LIKE ?
                ORDER BY created_at DESC
            """
            rows = self._db.fetchall(sql, (pattern,) * 5)
            return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(f"搜索任务失败: {e}")
            return []

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        统计任务数量

        Args:
            filters: 过滤条件

        Returns:
            任务数量
        """
        try:
            sql = "SELECT COUNT(*) FROM tasks"
            params = []

            if filters:
                conditions = []
                for key, value in filters.items():
                    if value is not None:
                        conditions.append(f"{k} = ?")
                        params.append(value)

                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)

            result = self._db.fetchone(sql, tuple(params) if params else None)
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"统计任务数量失败: {e}")
            return 0

    def _row_to_dict(self, row: Tuple) -> Dict[str, Any]:
        """将数据库行转换为字典"""
        columns = [
            "task_id", "task_name", "inquirer", "inquirer_dept", "inquirer_company",
            "inquirer_phone", "inquirer_email", "respondent", "respondent_dept",
            "industry", "key_module", "task_content", "urgency", "status",
            "expected_reply_time", "actual_reply_time", "reply_status", "reply_content",
            "created_at", "updated_at", "created_by", "remark",
        ]
        return dict(zip(columns, row))


class TaskTrackDAO:
    """任务跟踪记录数据访问对象"""

    def __init__(self) -> None:
        """初始化DAO"""
        self._db = get_db_connection()

    def create(self, data: Dict[str, Any]) -> Optional[str]:
        """创建跟踪记录"""
        try:
            from ..utils.helpers import generate_id

            record_id = data.get("record_id") or generate_id()
            data["record_id"] = record_id

            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            sql = f"INSERT INTO task_track_records ({columns}) VALUES ({placeholders})"

            self._db.execute(sql, tuple(data.values()), commit=True)
            logger.info(f"跟踪记录创建成功: {record_id}")
            return record_id
        except Exception as e:
            logger.error(f"创建跟踪记录失败: {e}")
            return None

    def get_by_task_id(self, task_id: str) -> List[Dict[str, Any]]:
        """获取任务的跟踪记录"""
        try:
            sql = """
                SELECT * FROM task_track_records
                WHERE task_id = ?
                ORDER BY track_time DESC
            """
            rows = self._db.fetchall(sql, (task_id,))

            columns = ["record_id", "task_id", "track_content", "track_status", "track_time", "created_at"]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"获取跟踪记录失败: {e}")
            return []

    def delete_by_task_id(self, task_id: str) -> bool:
        """删除任务的所有跟踪记录"""
        try:
            self._db.delete("task_track_records", "task_id = ?", (task_id,))
            return True
        except Exception as e:
            logger.error(f"删除跟踪记录失败: {e}")
            return False


class ReminderDAO:
    """提醒数据访问对象"""

    def __init__(self) -> None:
        """初始化DAO"""
        self._db = get_db_connection()

    def create(self, data: Dict[str, Any]) -> Optional[str]:
        """创建提醒"""
        try:
            from ..utils.helpers import generate_id

            reminder_id = data.get("reminder_id") or generate_id()
            data["reminder_id"] = reminder_id

            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            sql = f"INSERT INTO reminders ({columns}) VALUES ({placeholders})"

            self._db.execute(sql, tuple(data.values()), commit=True)
            logger.info(f"提醒创建成功: {reminder_id}")
            return reminder_id
        except Exception as e:
            logger.error(f"创建提醒失败: {e}")
            return None

    def get_pending(self) -> List[Dict[str, Any]]:
        """获取待触发的提醒"""
        try:
            sql = """
                SELECT * FROM reminders
                WHERE is_triggered = 0
                  AND reminder_time <= ?
                ORDER BY reminder_time ASC
            """
            rows = self._db.fetchall(sql, (datetime.now(),))

            columns = ["reminder_id", "task_id", "reminder_time", "reminder_type", "is_triggered", "triggered_at", "created_at"]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"获取待触发提醒失败: {e}")
            return []

    def trigger(self, reminder_id: str) -> bool:
        """触发提醒"""
        try:
            sql = """
                UPDATE reminders
                SET is_triggered = 1, triggered_at = ?
                WHERE reminder_id = ?
            """
            self._db.execute(sql, (datetime.now(), reminder_id), commit=True)
            logger.info(f"提醒已触发: {reminder_id}")
            return True
        except Exception as e:
            logger.error(f"触发提醒失败: {e}")
            return False

    def delete_by_task_id(self, task_id: str) -> bool:
        """删除任务的所有提醒"""
        try:
            self._db.delete("reminders", "task_id = ?", (task_id,))
            return True
        except Exception as e:
            logger.error(f"删除提醒失败: {e}")
            return False


class RecommendationLibraryDAO:
    """推荐库数据访问对象"""

    def __init__(self) -> None:
        """初始化DAO"""
        self._db = get_db_connection()

    def create(self, data: Dict[str, Any]) -> Optional[str]:
        """创建推荐库条目"""
        try:
            from ..utils.helpers import generate_id

            lib_id = data.get("lib_id") or generate_id()
            data["lib_id"] = lib_id

            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            sql = f"INSERT INTO recommendation_library ({columns}) VALUES ({placeholders})"

            self._db.execute(sql, tuple(data.values()), commit=True)
            logger.info(f"推荐库条目创建成功: {lib_id}")
            return lib_id
        except Exception as e:
            logger.error(f"创建推荐库条目失败: {e}")
            return None

    def get_all(self) -> List[Dict[str, Any]]:
        """获取所有推荐库条目"""
        try:
            sql = "SELECT * FROM recommendation_library ORDER BY usage_count DESC"
            rows = self._db.fetchall(sql)

            columns = ["lib_id", "keywords", "related_module", "related_content", "usage_count", "created_at", "updated_at"]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"获取推荐库失败: {e}")
            return []

    def search(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索推荐库"""
        try:
            pattern = f"%{keyword}%"
            sql = """
                SELECT * FROM recommendation_library
                WHERE keywords LIKE ?
                   OR related_module LIKE ?
                   OR related_content LIKE ?
                ORDER BY usage_count DESC
            """
            rows = self._db.fetchall(sql, (pattern,) * 3)

            columns = ["lib_id", "keywords", "related_module", "related_content", "usage_count", "created_at", "updated_at"]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"搜索推荐库失败: {e}")
            return []

    def update_usage(self, lib_id: str) -> bool:
        """更新使用次数"""
        try:
            sql = """
                UPDATE recommendation_library
                SET usage_count = usage_count + 1, updated_at = ?
                WHERE lib_id = ?
            """
            self._db.execute(sql, (datetime.now(), lib_id), commit=True)
            return True
        except Exception as e:
            logger.error(f"更新使用次数失败: {e}")
            return False

    def delete(self, lib_id: str) -> bool:
        """删除推荐库条目"""
        try:
            self._db.delete("recommendation_library", "lib_id = ?", (lib_id,))
            return True
        except Exception as e:
            logger.error(f"删除推荐库条目失败: {e}")
            return False
