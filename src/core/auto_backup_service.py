# -*- coding: utf-8 -*-
"""
自动备份服务模块
Auto Backup Service Module

提供自动备份功能，包括定时备份、备份策略管理、备份提醒等
"""

import os
import sys
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from pathlib import Path
from enum import Enum

from ..database.connection import get_db_connection
from ..utils.logger import get_logger

logger = get_logger(__name__)


class BackupFrequency(Enum):
    """备份频率枚举"""
    EVERY_HOUR = "hourly"        # 每小时
    EVERY_4_HOURS = "4hours"    # 每4小时
    EVERY_8_HOURS = "8hours"    # 每8小时
    DAILY = "daily"              # 每天
    WEEKLY = "weekly"            # 每周
    MONTHLY = "monthly"          # 每月
    MANUAL = "manual"           # 手动


class AutoBackupConfig:
    """自动备份配置类"""

    # 默认配置
    DEFAULT_CONFIG = {
        "enabled": False,                    # 是否启用自动备份
        "frequency": BackupFrequency.DAILY.value,  # 备份频率
        "backup_time": "02:00",              # 备份时间（每日备份时有效）
        "keep_count": 7,                      # 保留的备份数量
        "max_backup_size_mb": 100,           # 最大单个备份大小(MB)
        "backup_on_startup": True,            # 启动时备份
        "backup_on_shutdown": True,           # 关闭时备份
        "notify_on_backup": True,              # 备份完成通知
        "include_logs": False,                # 是否包含日志文件
        "compression_level": 6,               # 压缩级别 (0-9)
        "last_backup_time": None,             # 上次备份时间
        "last_backup_path": None,             # 上次备份路径
        "auto_backup_count": 0,               # 自动备份次数统计
    }

    def __init__(self):
        """初始化自动备份配置"""
        self.db = get_db_connection()
        self._init_config_table()
        self._load_config()

    def _init_config_table(self) -> None:
        """初始化自动备份配置表"""
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS auto_backup_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                config_data TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            commit=True
        )

        # 如果表为空，插入默认配置
        count = self.db.fetchone("SELECT COUNT(*) FROM auto_backup_config")
        if count and count[0] == 0:
            self.db.execute(
                "INSERT INTO auto_backup_config (id, config_data) VALUES (1, ?)",
                (json.dumps(self.DEFAULT_CONFIG, ensure_ascii=False),),
                commit=True
            )
            logger.info("自动备份配置表初始化完成")

    def _load_config(self) -> None:
        """加载配置"""
        try:
            row = self.db.fetchone("SELECT config_data FROM auto_backup_config WHERE id = 1")
            if row and row[0]:
                self.config = json.loads(row[0])
                # 确保所有默认键都存在
                for key, value in self.DEFAULT_CONFIG.items():
                    if key not in self.config:
                        self.config[key] = value
            else:
                self.config = self.DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"加载自动备份配置失败: {e}")
            self.config = self.DEFAULT_CONFIG.copy()

    def get(self, key: str, default: any = None) -> any:
        """获取配置值"""
        return self.config.get(key, default)

    def set(self, key: str, value: any) -> None:
        """设置配置值"""
        self.config[key] = value

    def save(self) -> bool:
        """保存配置"""
        try:
            self.db.execute(
                """
                UPDATE auto_backup_config SET
                    config_data = ?,
                    updated_at = ?
                WHERE id = 1
                """,
                (json.dumps(self.config, ensure_ascii=False), datetime.now()),
                commit=True
            )
            logger.info("自动备份配置已保存")
            return True
        except Exception as e:
            logger.error(f"保存自动备份配置失败: {e}")
            return False

    @property
    def frequency_seconds(self) -> int:
        """获取备份频率对应的秒数"""
        frequency_map = {
            BackupFrequency.EVERY_HOUR.value: 3600,
            BackupFrequency.EVERY_4_HOURS.value: 14400,
            BackupFrequency.EVERY_8_HOURS.value: 28800,
            BackupFrequency.DAILY.value: 86400,
            BackupFrequency.WEEKLY.value: 604800,
            BackupFrequency.MONTHLY.value: 2592000,
        }
        return frequency_map.get(self.config.get("frequency", BackupFrequency.DAILY.value), 86400)

    def should_backup_now(self) -> bool:
        """检查是否应该立即备份"""
        if not self.config.get("enabled", False):
            return False

        frequency = self.config.get("frequency", BackupFrequency.DAILY.value)
        last_backup = self.config.get("last_backup_time")

        if not last_backup:
            return True

        # 解析上次备份时间
        try:
            last_time = datetime.fromisoformat(last_backup)
            next_backup = last_time + timedelta(seconds=self.frequency_seconds)
            return datetime.now() >= next_backup
        except Exception:
            return True

    def get_next_backup_time(self) -> Optional[datetime]:
        """获取下次备份时间"""
        if not self.config.get("enabled", False):
            return None

        last_backup = self.config.get("last_backup_time")
        if not last_backup:
            return datetime.now()

        try:
            last_time = datetime.fromisoformat(last_backup)
            return last_time + timedelta(seconds=self.frequency_seconds)
        except Exception:
            return None

    def to_dict(self) -> Dict:
        """转换为字典"""
        return self.config.copy()


class AutoBackupService:
    """自动备份服务类"""

    _instance: Optional["AutoBackupService"] = None

    def __new__(cls) -> "AutoBackupService":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化自动备份服务"""
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.db = get_db_connection()
        self.config = AutoBackupConfig()
        self.backup_service = None  # 延迟加载
        self._timer: Optional[threading.Timer] = None
        self._running = False
        self._startup_backup_done = False
        self._shutdown_backup_done = False

        # 连接数据库时自动检查
        self._check_startup_backup()

    def _get_backup_service(self):
        """获取备份服务实例"""
        if self.backup_service is None:
            from .backup_service import BackupService
            self.backup_service = BackupService()
        return self.backup_service

    def _check_startup_backup(self) -> None:
        """检查启动时备份"""
        if not self._startup_backup_done and self.config.get("backup_on_startup", True):
            if self.config.should_backup_now():
                logger.info("执行启动时自动备份...")
                self._startup_backup_done = True
                # 在后台线程执行备份
                threading.Thread(target=self._do_auto_backup, args=("启动备份",), daemon=True).start()

    def _do_auto_backup(self, reason: str = "定时备份") -> bool:
        """执行自动备份"""
        try:
            backup_path = self._get_backup_service().create_backup(backup_type="自动")

            if backup_path:
                # 更新配置
                self.config.set("last_backup_time", datetime.now().isoformat())
                self.config.set("last_backup_path", backup_path)
                self.config.set("auto_backup_count",
                               self.config.get("auto_backup_count", 0) + 1)
                self.config.save()

                # 清理旧备份
                self._clean_old_backups()

                logger.info(f"自动备份成功: {backup_path}")
                return True
            else:
                logger.error("自动备份失败")
                return False

        except Exception as e:
            logger.error(f"自动备份执行失败: {e}")
            return False

    def _clean_old_backups(self) -> int:
        """清理旧备份"""
        keep_count = self.config.get("keep_count", 7)
        return self._get_backup_service().clean_old_backups(keep_count)

    def start(self) -> None:
        """启动自动备份定时器"""
        if self._running:
            return

        if not self.config.get("enabled", False):
            logger.info("自动备份未启用")
            return

        self._running = True
        self._schedule_next_backup()
        logger.info("自动备份服务已启动")

    def stop(self) -> None:
        """停止自动备份定时器"""
        self._running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None
        logger.info("自动备份服务已停止")

    def _schedule_next_backup(self) -> None:
        """安排下次备份"""
        if not self._running or not self.config.get("enabled", False):
            return

        next_time = self.config.get_next_backup_time()
        if not next_time:
            return

        # 计算等待秒数
        wait_seconds = (next_time - datetime.now()).total_seconds()
        if wait_seconds <= 0:
            wait_seconds = self.config.frequency_seconds

        # 设置定时器
        self._timer = threading.Timer(wait_seconds, self._on_timer)
        self._timer.daemon = True
        self._timer.start()

    def _on_timer(self) -> None:
        """定时器回调"""
        if not self._running:
            return

        # 执行备份
        self._do_auto_backup("定时备份")

        # 安排下次备份
        self._schedule_next_backup()

    def trigger_backup(self, reason: str = "手动触发") -> bool:
        """手动触发备份"""
        return self._do_auto_backup(reason)

    def get_status(self) -> Dict:
        """获取自动备份状态"""
        next_backup = self.config.get_next_backup_time()
        return {
            "enabled": self.config.get("enabled", False),
            "running": self._running,
            "frequency": self.config.get("frequency", BackupFrequency.DAILY.value),
            "keep_count": self.config.get("keep_count", 7),
            "last_backup_time": self.config.get("last_backup_time"),
            "last_backup_path": self.config.get("last_backup_path"),
            "next_backup_time": next_backup.isoformat() if next_backup else None,
            "auto_backup_count": self.config.get("auto_backup_count", 0),
        }

    def update_config(self, config_dict: Dict) -> bool:
        """更新配置"""
        try:
            for key, value in config_dict.items():
                self.config.set(key, value)
            self.config.save()

            # 如果启用状态改变，更新服务状态
            if "enabled" in config_dict:
                if config_dict["enabled"]:
                    self.start()
                else:
                    self.stop()

            return True
        except Exception as e:
            logger.error(f"更新自动备份配置失败: {e}")
            return False


# 全局服务实例
_auto_backup_service: Optional[AutoBackupService] = None


def get_auto_backup_service() -> AutoBackupService:
    """获取自动备份服务实例"""
    global _auto_backup_service
    if _auto_backup_service is None:
        _auto_backup_service = AutoBackupService()
    return _auto_backup_service
