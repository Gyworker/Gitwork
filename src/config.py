# -*- coding: utf-8 -*-
"""
配置管理模块
Configuration Management Module

负责应用程序的配置管理，包括数据库配置、UI配置、系统配置等
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class Config:
    """配置管理类"""

    _instance: Optional["Config"] = None
    _config: Dict[str, Any] = {}

    def __new__(cls) -> "Config":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初始化配置"""
        if not self._config:
            self.load_config()

    @classmethod
    def get_instance(cls) -> "Config":
        """获取配置单例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_config(self, config_path: Optional[str] = None) -> None:
        """
        加载配置文件

        Args:
            config_path: 配置文件路径，默认为config.yaml
        """
        if config_path is None:
            # 获取项目根目录
            root_dir = Path(__file__).parent.parent
            config_path = root_dir / "config.yaml"

        if not Path(config_path).exists():
            # 使用默认配置
            self._config = self._get_default_config()
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self._config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "app": {
                "name": "市场咨询任务跟踪工具",
                "version": "1.0.0",
                "debug": False,
            },
            "database": {
                "type": "sqlite",
                "path": "data/market_task_tracker.db",
                "backup_enabled": True,
                "backup_interval": 86400,  # 24小时
            },
            "ui": {
                "theme": "default",
                "language": "zh_CN",
                "window": {
                    "width": 1280,
                    "height": 720,
                    "min_width": 1024,
                    "min_height": 600,
                },
            },
            "task": {
                "default_urgency": "中",
                "default_reply_hours": 24,
                "auto_save": True,
                "auto_save_interval": 300,  # 5分钟
            },
            "notification": {
                "enabled": True,
                "check_interval": 60,  # 1分钟
                "sound_enabled": True,
            },
            "recommendation": {
                "enabled": True,
                "similarity_threshold": 0.6,
                "max_results": 10,
            },
            "import_export": {
                "excel_encoding": "utf-8",
                "max_import_rows": 10000,
            },
            "log": {
                "level": "INFO",
                "file": "logs/app.log",
                "max_size": 10485760,  # 10MB
                "backup_count": 5,
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点号分隔的路径，如"database.path"
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

            if value is None:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值

        Args:
            key: 配置键，支持点号分隔的路径
            value: 配置值
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save_config(self, config_path: Optional[str] = None) -> bool:
        """
        保存配置到文件

        Args:
            config_path: 配置文件路径

        Returns:
            是否保存成功
        """
        if config_path is None:
            root_dir = Path(__file__).parent.parent
            config_path = root_dir / "config.yaml"

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    self._config, f, allow_unicode=True, default_flow_style=False
                )
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

    @property
    def app_name(self) -> str:
        """获取应用名称"""
        return self.get("app.name", "市场咨询任务跟踪工具")

    @property
    def app_version(self) -> str:
        """获取应用版本"""
        return self.get("app.version", "1.0.0")

    @property
    def debug(self) -> bool:
        """是否调试模式"""
        return self.get("app.debug", False)

    @property
    def database_path(self) -> str:
        """获取数据库路径"""
        return self.get("database.path", "data/market_task_tracker.db")

    @property
    def log_level(self) -> str:
        """获取日志级别"""
        return self.get("log.level", "INFO")

    @property
    def log_file(self) -> str:
        """获取日志文件路径"""
        return self.get("log.file", "logs/app.log")


# 全局配置实例
config = Config.get_instance()


def get_config() -> Config:
    """获取配置实例"""
    return config
