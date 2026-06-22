# -*- coding: utf-8 -*-
"""
提醒服务核心模块
Reminder Service Core Module:

提供提醒功能的业务逻辑，包括首次提醒、周期提醒、额外时间点提醒等
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import json
import threading

from ..database.connection import get_db_connection
from ..utils.logger import get_logger
from ..utils.exception_handler import (
    safe_execute,
    handle_database_error,
    DatabaseException,
    ServiceException
)

logger = get_logger(__name__)


class ReminderConfig:
    """提醒配置类"""

    # 默认提醒配置
    DEFAULT_CONFIG = {
        "高": {
            "reminder_interval": 3,  # 3小时
            "daily_max_reminders": 6,  # 每天最多6次
            "extra_reminder_times": ["08:30", "11:00", "13:50", "17:30"],  # 额外提醒时间点
            "enabled": True
        },
        "中": {
            "reminder_interval": 4,  # 4小时
            "daily_max_reminders": 4,  # 每天最多4次
            "extra_reminder_times": ["08:30", "13:55", "17:35"],  # 额外提醒时间点
            "enabled": True
        },
        "低": {
            "reminder_interval": 6,  # 6小时
            "daily_max_reminders": 2,  # 每天最多2次
            "extra_reminder_times": ["08:30", "17:40"],  # 额外提醒时间点
            "enabled": True
        }
    }

    def __init__(self):
        """初始化提醒配置"""
        self.db = get_db_connection()
        self._init_config_table()
        self._load_config()

    def _init_config_table(self) -> None:
        """初始化提醒配置表"""
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS reminder_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                urgency VARCHAR(10) NOT NULL UNIQUE,
                reminder_interval INTEGER NOT NULL,
                daily_max_reminders INTEGER NOT NULL,
                extra_reminder_times TEXT,
                enabled INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            commit=True
        )

        # 如果表为空，插入默认配置
        count = self.db.fetchone("SELECT COUNT(*) FROM reminder_config")
        if count and count[0] == 0:
            for urgency, config in self.DEFAULT_CONFIG.items():
                self.db.execute(
                    """
                    INSERT INTO reminder_config 
                    (urgency, reminder_interval, daily_max_reminders, extra_reminder_times, enabled)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        urgency,
                        config["reminder_interval"],
                        config["daily_max_reminders"],
                        json.dumps(config["extra_reminder_times"]),
                        1 if config["enabled"] else 0
                    ),
                    commit=True
                )
            logger.info("提醒配置表初始化完成")

    def _load_config(self) -> None:
        """加载提醒配置"""
        rows = self.db.fetchall("SELECT * FROM reminder_config")
        self.config = {}
        for row in rows:
            urgency, interval, max_reminders, extra_times, enabled = row[1:6]
            self.config[urgency] = {
                "reminder_interval": interval,
                "daily_max_reminders": max_reminders,
                "extra_reminder_times": json.loads(extra_times) if extra_times else [],
                "enabled": bool(enabled)
            }

    def get_config(self, urgency: str) -> Dict:
        """获取指定重要程度的提醒配置"""
        if urgency not in self.config:
            return self.DEFAULT_CONFIG.get(urgency, {})
        return self.config[urgency]

    def get_all_config(self) -> Dict[str, Dict]:
        """获取所有提醒配置"""
        return self.config

    def update_config(self, urgency: str, config: Dict) -> bool:
        """更新提醒配置"""
        try:
            self.db.execute(
                """
                UPDATE reminder_config
                SET reminder_interval = ?,
                    daily_max_reminders = ?,
                    extra_reminder_times = ?,
                    enabled = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE urgency = ?
                """,
                (
                    config.get("reminder_interval", 3),
                    config.get("daily_max_reminders", 6),
                    json.dumps(config.get("extra_reminder_times", [])),
                    1 if config.get("enabled", True) else 0,
                    urgency
                ),
                commit=True
            )
            self._load_config()
            logger.info(f"提醒配置更新成功: {urgency}")
            return True
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return False
        except Exception as e:
            logger.error(f"更新提醒配置失败: {e}")
            return False

    def reset_to_default(self, urgency: Optional[str] = None) -> bool:
        """恢复默认配置"""
        try:
            if urgency:
                # 恢复单个配置
                default = self.DEFAULT_CONFIG.get(urgency, {})
                if default:
                    self.update_config(urgency, default)
            else:
                # 恢复所有配置
                for urgency_level, default in self.DEFAULT_CONFIG.items():
                    self.update_config(urgency_level, default)
            logger.info(f"提醒配置已恢复默认值")
            return True
        except Exception as e:
            logger.error(f"恢复默认配置失败: {e}")
            return False


class ReminderService:
    """提醒服务类"""

    def __init__(self):
        """初始化提醒服务"""
        self.db = get_db_connection()
        self.config = ReminderConfig()
        self._init_reminder_tables()
        self._callbacks: List[Callable] = []
        self._is_running = False
        self._check_thread: Optional[threading.Thread] = None

    def _init_reminder_tables(self) -> None:
        """初始化提醒相关表"""
        # 提醒历史表
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS reminder_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                task_name TEXT,
                urgency TEXT,
                reminder_time DATETIME NOT NULL,
                reminder_type VARCHAR(20),
                is_processed INTEGER DEFAULT 0,
                processed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
            )
            """,
            commit=True
        )

        # 任务提醒计数表
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS task_reminder_counts (
                task_id TEXT PRIMARY KEY,
                today_reminder_count INTEGER DEFAULT 0,
                total_reminder_count INTEGER DEFAULT 0,
                last_reminder_date DATE,
                last_reminder_time DATETIME,
                FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
            )
            """,
            commit=True
        )

        # 创建索引
        self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_reminder_history_task_id ON reminder_history(task_id)",
            commit=True
        )
        self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_reminder_history_reminder_time ON reminder_history(reminder_time)",
            commit=True
        )

        logger.info("提醒相关表初始化完成")

    def register_callback(self, callback: Callable) -> None:
        """注册提醒回调函数"""
        if callback not in self._callbacks:
            self._callbacks.append(callback)
            logger.info(f"提醒回调函数已注册: {callback.__name__}")

    def unregister_callback(self, callback: Callable) -> None:
        """取消注册提醒回调函数"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            logger.info(f"提醒回调函数已取消注册: {callback.__name__}")

    def _notify_callbacks(self, task_data: Dict) -> None:
        """通知所有回调函数"""
        for callback in self._callbacks:
            try:
                callback(task_data)
            except (TypeError, ValueError) as e:
                logger.warning(f"回调参数错误: {callback.__name__} - {e}")
            except Exception as e:
                logger.error(f"提醒回调函数执行失败: {callback.__name__} - {e}")

    def check_and_trigger_reminders(self) -> List[Dict]:
        """检查并触发提醒"""
        triggered_reminders = []
        current_time = datetime.now()
        current_time_str = current_time.strftime("%H:%M")
        current_date_str = current_time.strftime("%Y-%m-%d")

        try:
            # 获取所有未完成的任务
            tasks = self.db.fetchall(
                """
                SELECT task_id, task_name, urgency, status,
                       reminder_count, reminder_limit, last_reminder_time
                FROM tasks 
                WHERE status IN ('进行中', '挂起')
                ORDER BY 
                    CASE urgency 
                        WHEN '高' THEN 1 
                        WHEN '中' THEN 2 
                        WHEN '低' THEN 3 
                    END,
                    created_at ASC
                """
            )

            for task in tasks:
                task_id, task_name, urgency, status = task[0:4]
                reminder_count = task[4] if task[4] else 0
                reminder_limit = task[5] if task[5] else 6
                last_reminder_time = task[6]

                # 获取该任务的提醒配置
                config = self.config.get_config(urgency)
                if not config.get("enabled", True):
                    continue

                # 检查是否达到提醒上限
                if reminder_count >= reminder_limit:
                    continue

                # 检查今天是否已达到最大提醒次数
                today_count = self._get_today_reminder_count(task_id)
                if today_count >= config.get("daily_max_reminders", 6):
                    continue

                # 检查是否需要提醒
                should_remind = False
                reminder_type = ""

                # 首次提醒（08:30）
                if current_time_str == "08:30" and self._should_send_first_reminder(task_id):
                    should_remind = True
                    reminder_type = "首次提醒"
                # 额外时间点提醒
                elif current_time_str in config.get("extra_reminder_times", []):
                    if self._should_send_extra_reminder(task_id, current_time_str):
                        should_remind = True
                        reminder_type = "额外提醒"
                # 周期提醒
                elif self._should_send_periodic_reminder(task_id, config.get("reminder_interval", 3)):
                    should_remind = True
                    reminder_type = "周期提醒"

                if should_remind:
                    # 触发提醒
                    task_data = {
                        "task_id": task_id,
                        "task_name": task_name,
                        "urgency": urgency,
                        "reminder_type": reminder_type,
                        "reminder_count": reminder_count + 1,
                        "reminder_limit": reminder_limit,
                        "current_time": current_time
                    }

                    # 记录提醒历史
                    self._record_reminder(task_data)

                    # 更新任务提醒计数
                    self._update_reminder_count(task_id)

                    # 通知回调
                    self._notify_callbacks(task_data)

                    triggered_reminders.append(task_data)
                    logger.info(f"提醒已触发: {task_name} ({reminder_type})")

            return triggered_reminders

        except Exception as e:
            logger.error(f"检查并触发提醒失败: {e}")
            return []

    def _should_send_first_reminder(self, task_id: str) -> bool:
        """判断是否应该发送首次提醒"""
        # 检查今天是否已发送首次提醒
        today = datetime.now().strftime("%Y-%m-%d")
        result = self.db.fetchone(
            """
            SELECT COUNT(*) FROM reminder_history 
            WHERE task_id = ? AND DATE(reminder_time) = ? AND reminder_type = '首次提醒'
            """,
            (task_id, today)
        )
        return result and result[0] == 0

    def _should_send_extra_reminder(self, task_id: str, time_str: str) -> bool:
        """判断是否应该发送额外时间点提醒"""
        today = datetime.now().strftime("%Y-%m-%d")
        # 检查这个时间点是否已发送过提醒
        result = self.db.fetchone(
            """
            SELECT COUNT(*) FROM reminder_history 
            WHERE task_id = ? 
              AND DATE(reminder_time) = ? 
              AND reminder_type = '额外提醒'
              AND TIME(reminder_time) LIKE ?
            """,
            (task_id, today, f"{time_str}%")
        )
        return result and result[0] == 0

    def _should_send_periodic_reminder(self, task_id: str, interval_hours: int) -> bool:
        """判断是否应该发送周期提醒"""
        today = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now()

        # 获取最后提醒时间
        result = self.db.fetchone(
            """
            SELECT reminder_time FROM reminder_history 
            WHERE task_id = ? AND DATE(reminder_time) = ?
            ORDER BY reminder_time DESC LIMIT 1
            """,
            (task_id, today)
        )

        if not result or not result[0]:
            return False

        last_reminder_time = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
        time_diff = (current_time - last_reminder_time).total_seconds() / 3600

        # 如果距离上次提醒超过间隔时间，且不是首次提醒或额外提醒刚发过
        if time_diff >= interval_hours:
            # 检查最近是否有其他类型的提醒
            recent_result = self.db.fetchone(
                """
                SELECT reminder_type FROM reminder_history 
                WHERE task_id = ? AND DATE(reminder_time) = ?
                ORDER BY reminder_time DESC LIMIT 1
                """,
                (task_id, today)
            )
            if recent_result and recent_result[0] in ["首次提醒", "额外提醒"]:
                return time_diff >= interval_hours * 1.5  # 额外提醒后需要更长时间才发周期提醒
            return True

        return False

    def _get_today_reminder_count(self, task_id: str) -> int:
        """获取今天已提醒次数"""
        today = datetime.now().strftime("%Y-%m-%d")
        result = self.db.fetchone(
            """
            SELECT COUNT(*) FROM reminder_history 
            WHERE task_id = ? AND DATE(reminder_time) = ?
            """,
            (task_id, today)
        )
        return result[0] if result else 0

    def _record_reminder(self, task_data: Dict) -> None:
        """记录提醒历史"""
        try:
            self.db.execute(
                """
                INSERT INTO reminder_history 
                (task_id, task_name, urgency, reminder_time, reminder_type)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    task_data["task_id"],
                    task_data["task_name"],
                    task_data["urgency"],
                    task_data["current_time"].strftime("%Y-%m-%d %H:%M:%S"),
                    task_data["reminder_type"]
                ),
                commit=True
            )
        except Exception as e:
            logger.error(f"记录提醒历史失败: {e}")

    def _update_reminder_count(self, task_id: str) -> None:
        """更新任务提醒计数"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            current_time = datetime.now()

            # 更新任务表的提醒计数
            self.db.execute(
                """
                UPDATE tasks 
                SET reminder_count = reminder_count + 1,
                    last_reminder_time = ?
                WHERE task_id = ?
                """,
                (current_time.strftime("%Y-%m-%d %H:%M:%S"), task_id),
                commit=True
            )

            # 更新提醒计数表
            self.db.execute(
                """
                INSERT INTO task_reminder_counts 
                (task_id, today_reminder_count, total_reminder_count, last_reminder_date, last_reminder_time)
                VALUES (?, 1, 1, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    today_reminder_count = CASE 
                        WHEN last_reminder_date = ? THEN today_reminder_count + 1 
                        ELSE 1 
                    END,
                    total_reminder_count = total_reminder_count + 1,
                    last_reminder_date = ?,
                    last_reminder_time = ?
                """,
                (
                    task_id, today, current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    today, today, current_time.strftime("%Y-%m-%d %H:%M:%S")
                ),
                commit=True
            )
        except Exception as e:
            logger.error(f"更新提醒计数失败: {e}")

    def get_pending_tasks(self) -> List[Dict]:
        """获取待提醒任务列表"""
        try:
            tasks = self.db.fetchall(
                """
                SELECT t.task_id, t.task_name, t.urgency, t.status,
                       t.reminder_count, t.reminder_limit,
                       rc.today_reminder_count
                FROM tasks t
                LEFT JOIN task_reminder_counts rc ON t.task_id = rc.task_id
                WHERE t.status IN ('进行中', '挂起')
                ORDER BY 
                    CASE t.urgency 
                        WHEN '高' THEN 1 
                        WHEN '中' THEN 2 
                        WHEN '低' THEN 3 
                    END,
                    t.created_at ASC
                """
            )

            result = []
            for task in tasks:
                task_id, task_name, urgency, status = task[0:4]
                reminder_count = task[4] if task[4] else 0
                reminder_limit = task[5] if task[5] else 6
                today_count = task[6] if task[6] else 0

                config = self.config.get_config(urgency)

                result.append({
                    "task_id": task_id,
                    "task_name": task_name,
                    "urgency": urgency,
                    "status": status,
                    "reminder_count": reminder_count,
                    "reminder_limit": reminder_limit,
                    "today_count": today_count,
                    "daily_max": config.get("daily_max_reminders", 6),
                    "can_remind": today_count < config.get("daily_max_reminders", 6) and reminder_count < reminder_limit
                })

            return result

        except Exception as e:
            logger.error(f"获取待提醒任务列表失败: {e}")
            return []

    def get_reminder_history(self, task_id: Optional[str] = None, 
                            limit: int = 100) -> List[Dict]:
        """获取提醒历史"""
        try:
            if task_id:
                rows = self.db.fetchall(
                    """
                    SELECT id, task_id, task_name, urgency, reminder_time, 
                           reminder_type, is_processed, processed_at
                    FROM reminder_history 
                    WHERE task_id = ?
                    ORDER BY reminder_time DESC
                    LIMIT ?
                    """,
                    (task_id, limit)
                )
            else:
                rows = self.db.fetchall(
                    """
                    SELECT id, task_id, task_name, urgency, reminder_time, 
                           reminder_type, is_processed, processed_at
                    FROM reminder_history 
                    ORDER BY reminder_time DESC
                    LIMIT ?
                    """,
                    (limit,)
                )

            result = []
            for row in rows:
                result.append({
                    "id": row[0],
                    "task_id": row[1],
                    "task_name": row[2],
                    "urgency": row[3],
                    "reminder_time": row[4],
                    "reminder_type": row[5],
                    "is_processed": bool(row[6]),
                    "processed_at": row[7]
                })

            return result

        except Exception as e:
            logger.error(f"获取提醒历史失败: {e}")
            return []

    def mark_as_processed(self, task_id: str, 
                          reminder_time: Optional[str] = None) -> bool:
        """标记任务已处理"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if reminder_time:
                self.db.execute(
                    """
                    UPDATE reminder_history 
                    SET is_processed = 1, processed_at = ?
                    WHERE task_id = ? AND reminder_time = ?
                    """,
                    (current_time, task_id, reminder_time),
                    commit=True
                )
            else:
                self.db.execute(
                    """
                    UPDATE reminder_history 
                    SET is_processed = 1, processed_at = ?
                    WHERE task_id = ? AND is_processed = 0
                    """,
                    (current_time, task_id),
                    commit=True
                )

            logger.info(f"任务已标记为已处理: {task_id}")
            return True

        except Exception as e:
            logger.error(f"标记任务已处理失败: {e}")
            return False

    def snooze_reminder(self, task_id: str, minutes: int = 30) -> bool:
        """延迟提醒"""
        try:
            # 计算新的提醒时间
            new_reminder_time = datetime.now() + timedelta(minutes=minutes)

            # 添加一条新的提醒记录
            task = self.db.fetchone(
                "SELECT task_name, urgency FROM tasks WHERE task_id = ?",
                (task_id,)
            )

            if task:
                self.db.execute(
                    """
                    INSERT INTO reminder_history 
                    (task_id, task_name, urgency, reminder_time, reminder_type)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        task_id,
                        task[0],
                        task[1],
                        new_reminder_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "稍后提醒"
                    ),
                    commit=True
                )

            logger.info(f"提醒已延迟{minutes}分钟: {task_id}")
            return True

        except Exception as e:
            logger.error(f"延迟提醒失败: {e}")
            return False

    def start_scheduler(self) -> None:
        """启动提醒调度器"""
        if self._is_running:
            logger.warning("提醒调度器已在运行")
            return

        self._is_running = True
        self._check_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._check_thread.start()
        logger.info("提醒调度器已启动")

    def stop_scheduler(self) -> None:
        """停止提醒调度器"""
        self._is_running = False
        if self._check_thread:
            self._check_thread.join(timeout=5)
        logger.info("提醒调度器已停止")

    def _scheduler_loop(self) -> None:
        """调度器循环"""
        import time

        while self._is_running:
            try:
                # 每分钟检查一次
                self.check_and_trigger_reminders()
            except Exception as e:
                logger.error(f"调度器执行失败: {e}")

            # 休眠直到下一分钟
            time.sleep(60 - datetime.now().second)


# 全局提醒服务实例
_reminder_service: Optional[ReminderService] = None


def get_reminder_service() -> ReminderService:
    """获取提醒服务实例"""
    global _reminder_service
    if _reminder_service is None:
        _reminder_service = ReminderService()
    return _reminder_service


def get_reminder_config() -> ReminderConfig:
    """获取提醒配置实例"""
    service = get_reminder_service()
    return service.config
