# -*- coding: utf-8 -*-
"""
数据备份与恢复服务模块
Backup and Restore Service Module:

提供数据备份、恢复、导出等数据管理功能
"""

import os
import shutil
import zipfile
import json
import sys
from datetime import datetime
from typing import List, Dict, Optional, Callable
from pathlib import Path

from ..database.connection import get_db_connection
from ..utils.logger import get_logger

logger = get_logger(__name__)


class BackupService:
    """备份服务类"""

    def __init__(self):
        """初始化备份服务"""
        self.db = get_db_connection()
        self.backup_dir = self._get_backup_dir()
        self._init_backup_table()

    def _get_backup_dir(self) -> Path:
        """获取备份目录"""
        # 获取应用数据目录
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包后
            app_dir = Path(sys._MEIPASS)
        else:
            app_dir = Path(__file__).parent.parent.parent

        backup_dir = app_dir / "backup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir

    def _init_backup_table(self) -> None:
        """初始化备份记录表"""
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS backup_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_type VARCHAR(20) NOT NULL,
                backup_file TEXT NOT NULL,
                backup_size INTEGER,
                task_count INTEGER,
                contact_count INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            commit=True
        )

    def get_backup_records(self, limit: int = 10) -> List[Dict]:
        """获取备份记录列表"""
        try:
            rows = self.db.fetchall(
                """
                SELECT id, backup_type, backup_file, backup_size, 
                       task_count, contact_count, created_at
                FROM backup_records
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,)
            )

            result = []
            for row in rows:
                result.append({
                    "id": row[0],
                    "backup_type": row[1],
                    "backup_file": row[2],
                    "backup_size": row[3],
                    "task_count": row[4],
                    "contact_count": row[5],
                    "created_at": row[6]
                })

            return result

        except Exception as e:
            logger.error(f"获取备份记录失败: {e}")
            return []

    def _get_record_counts(self) -> Dict[str, int]:
        """获取各表记录数量"""
        try:
            task_count = self.db.fetchone("SELECT COUNT(*) FROM tasks")
            contact_count = self.db.fetchone("SELECT COUNT(*) FROM contacts")

            return {
                "task_count": task_count[0] if task_count else 0,
                "contact_count": contact_count[0] if contact_count else 0
            }
        except Exception as e:
            logger.error(f"获取记录数量失败: {e}")
            return {"task_count": 0, "contact_count": 0}

    def create_backup(self, backup_type: str = "手动") -> Optional[str]:
        """
        创建数据备份

        Args:
            backup_type: 备份类型（自动/手动）

        Returns:
            备份文件路径，失败返回None
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}.zip"
            backup_path = self.backup_dir / backup_filename

            # 获取数据库文件路径
            db_path = self._get_db_path()
            if not db_path:
                logger.error("无法获取数据库文件路径")
                return None

            # 创建ZIP压缩包
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 添加数据库文件
                zipf.write(db_path, "database.db")

                # 添加元数据
                metadata = {
                    "backup_type": backup_type,
                    "backup_time": timestamp,
                    "app_version": "1.2.1",
                    **self._get_record_counts()
                }
                zipf.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))

            # 记录备份信息
            backup_size = backup_path.stat().st_size
            counts = self._get_record_counts()

            self.db.execute(
                """
                INSERT INTO backup_records 
                (backup_type, backup_file, backup_size, task_count, contact_count)
                VALUES (?, ?, ?, ?, ?)
                """,
                (backup_type, str(backup_path), backup_size, counts["task_count"], counts["contact_count"]),
                commit=True
            )

            logger.info(f"数据备份成功: {backup_path}")
            return str(backup_path)

        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            return None

    def restore_backup(self, backup_path: str, 
                       progress_callback: Optional[Callable] = None) -> bool:
        """
        从备份恢复数据

        Args:
            backup_path: 备份文件路径
            progress_callback: 进度回调函数

        Returns:
            是否恢复成功
        """
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                logger.error(f"备份文件不存在: {backup_path}")
                return False

            if progress_callback:
                progress_callback(10, 100, "正在验证备份文件...")

            # 验证ZIP文件
            if not zipfile.is_zipfile(backup_file):
                logger.error("备份文件格式不正确")
                return False

            # 获取当前数据库路径
            current_db_path = self._get_db_path()
            if not current_db_path:
                logger.error("无法获取当前数据库文件路径")
                return False

            if progress_callback:
                progress_callback(20, 100, "正在备份当前数据...")

            # 先备份当前数据库
            current_backup = self.backup_dir / f"before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(current_db_path, current_backup)

            if progress_callback:
                progress_callback(30, 100, "正在解压备份文件...")

            # 解压备份文件到临时目录
            temp_dir = self.backup_dir / f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            temp_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(temp_dir)

            if progress_callback:
                progress_callback(50, 100, "正在验证数据完整性...")

            # 验证解压后的文件
            extracted_db = temp_dir / "database.db"
            if not extracted_db.exists():
                logger.error("备份文件中缺少数据库文件")
                shutil.rmtree(temp_dir)
                return False

            # 验证元数据
            metadata_file = temp_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    logger.info(f"备份元数据: {metadata}")

            if progress_callback:
                progress_callback(70, 100, "正在恢复数据库...")

            # 关闭当前数据库连接
            self.db.close()

            # 替换数据库文件
            shutil.copy2(extracted_db, current_db_path)

            if progress_callback:
                progress_callback(90, 100, "正在清理临时文件...")

            # 清理临时目录
            shutil.rmtree(temp_dir)

            # 重新初始化数据库连接
            from ..database.connection import DatabaseConnection
            DatabaseConnection._instance = None

            if progress_callback:
                progress_callback(100, 100, "恢复完成！")

            logger.info(f"数据恢复成功: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"恢复备份失败: {e}")
            return False

    def _get_db_path(self) -> Optional[str]:
        """获取数据库文件路径"""
        try:
            from ..database.connection import DatabaseConnection
            db = DatabaseConnection()
            return db.db_path
        except Exception as e:
            logger.error(f"获取数据库路径失败: {e}")
            return None

    def delete_backup(self, backup_id: int) -> bool:
        """删除备份记录"""
        try:
            # 获取备份文件路径
            result = self.db.fetchone(
                "SELECT backup_file FROM backup_records WHERE id = ?",
                (backup_id,)
            )

            if result and result[0]:
                backup_file = Path(result[0])
                if backup_file.exists():
                    backup_file.unlink()

            # 删除记录
            self.db.execute(
                "DELETE FROM backup_records WHERE id = ?",
                (backup_id,),
                commit=True
            )

            logger.info(f"备份记录已删除: {backup_id}")
            return True

        except Exception as e:
            logger.error(f"删除备份记录失败: {e}")
            return False

    def clean_old_backups(self, keep_count: int = 6) -> int:
        """
        清理旧备份文件

        Args:
            keep_count: 保留的备份数量

        Returns:
            删除的备份数量
        """
        try:
            # 获取所有备份记录（按时间倒序）
            records = self.db.fetchall(
                """
                SELECT id, backup_file FROM backup_records 
                ORDER BY created_at DESC
                """
            )

            if not records or len(records) <= keep_count:
                return 0

            # 删除多余的备份
            deleted_count = 0
            for i, record in enumerate(records):
                if i >= keep_count:
                    backup_id = record[0]
                    backup_file = record[1]

                    # 删除文件
                    if backup_file:
                        try:
                            Path(backup_file).unlink()
                        except (FileNotFoundError, OSError):
                            pass

                    # 删除记录
                    self.db.execute(
                        "DELETE FROM backup_records WHERE id = ?",
                        (backup_id,),
                        commit=True
                    )
                    deleted_count += 1

            logger.info(f"清理旧备份完成，删除了 {deleted_count} 个备份")
            return deleted_count

        except Exception as e:
            logger.error(f"清理旧备份失败: {e}")
            return 0

    def get_backup_size(self) -> Dict[str, int]:
        """获取备份统计信息"""
        try:
            total_size = 0
            backup_count = 0

            for record in self.get_backup_records(100):
                total_size += record.get("backup_size", 0)
                backup_count += 1

            return {
                "total_size": total_size,
                "backup_count": backup_count,
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            }

        except Exception as e:
            logger.error(f"获取备份统计失败: {e}")
            return {"total_size": 0, "backup_count": 0, "total_size_mb": 0}


class StatisticsService:
    """统计服务类"""

    def __init__(self):
        """初始化统计服务"""
        self.db = get_db_connection()

    def get_task_statistics(self) -> Dict:
        """获取任务统计信息"""
        try:
            # 总任务数
            total = self.db.fetchone("SELECT COUNT(*) FROM tasks")
            total_tasks = total[0] if total else 0

            # 按状态统计
            status_stats = self.db.fetchall(
                """
                SELECT status, COUNT(*) as count 
                FROM tasks 
                GROUP BY status
                """
            )

            # 按重要程度统计
            urgency_stats = self.db.fetchall(
                """
                SELECT urgency, COUNT(*) as count 
                FROM tasks 
                GROUP BY urgency
                """
            )

            # 本月新增任务
            month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
            monthly_new = self.db.fetchone(
                "SELECT COUNT(*) FROM tasks WHERE DATE(created_at) >= ?",
                (month_start,)
            )

            # 待处理任务
            pending = self.db.fetchone(
                "SELECT COUNT(*) FROM tasks WHERE status IN ('进行中', '挂起')"
            )

            return {
                "total_tasks": total_tasks,
                "status_distribution": {row[0]: row[1] for row in status_stats},
                "urgency_distribution": {row[0]: row[1] for row in urgency_stats},
                "monthly_new": monthly_new[0] if monthly_new else 0,
                "pending_tasks": pending[0] if pending else 0
            }

        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            return {}

    def get_contact_statistics(self) -> Dict:
        """获取通讯录统计信息"""
        try:
            total = self.db.fetchone("SELECT COUNT(*) FROM contacts")
            by_dept = self.db.fetchall(
                """
                SELECT department, COUNT(*) as count 
                FROM contacts 
                WHERE department IS NOT NULL AND department != ''
                GROUP BY department
                """
            )

            return {
                "total_contacts": total[0] if total else 0,
                "department_distribution": {row[0]: row[1] for row in by_dept}
            }

        except Exception as e:
            logger.error(f"获取通讯录统计失败: {e}")
            return {}

    def get_reminder_statistics(self) -> Dict:
        """获取提醒统计信息"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")

            # 今日提醒数
            today_reminders = self.db.fetchone(
                "SELECT COUNT(*) FROM reminder_history WHERE DATE(reminder_time) = ?",
                (today,)
            )

            # 待处理提醒
            pending_reminders = self.db.fetchone(
                "SELECT COUNT(*) FROM reminder_history WHERE is_processed = 0"
            )

            # 按类型统计
            type_stats = self.db.fetchall(
                """
                SELECT reminder_type, COUNT(*) as count 
                FROM reminder_history 
                GROUP BY reminder_type
                """
            )

            return {
                "today_reminders": today_reminders[0] if today_reminders else 0,
                "pending_reminders": pending_reminders[0] if pending_reminders else 0,
                "type_distribution": {row[0]: row[1] for row in type_stats}
            }

        except Exception as e:
            logger.error(f"获取提醒统计失败: {e}")
            return {}


# 全局服务实例
_backup_service: Optional[BackupService] = None
_statistics_service: Optional[StatisticsService] = None


def get_backup_service() -> BackupService:
    """获取备份服务实例"""
    global _backup_service
    if _backup_service is None:
        _backup_service = BackupService()
    return _backup_service


def get_statistics_service() -> StatisticsService:
    """获取统计服务实例"""
    global _statistics_service
    if _statistics_service is None:
        _statistics_service = StatisticsService()
    return _statistics_service
