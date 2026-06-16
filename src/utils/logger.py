# -*- coding: utf-8 -*-
"""
日志管理模块
Logger Module

负责应用程序的日志记录和管理
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

try:
    import colorlog

    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False

from ..config import get_config


class Logger:
    """日志管理类"""

    _loggers = {}

    def __init__(self, name: str = "market_task_tracker") -> None:
        """
        初始化日志记录器

        Args:
            name: 日志记录器名称
        """
        self.name = name
        self.logger: Optional[logging.Logger] = None
        self._setup_logger()

    def _setup_logger(self) -> None:
        """设置日志记录器"""
        if self.name in self._loggers:
            self.logger = self._loggers[self.name]
            return

        config = get_config()
        self.logger = logging.getLogger(self.name)

        # 设置日志级别
        log_level = getattr(logging, config.log_level.upper(), logging.INFO)
        self.logger.setLevel(log_level)

        # 避免重复添加处理器
        if self.logger.handlers:
            self._loggers[self.name] = self.logger
            return

        # 创建日志格式
        formatter = self._create_formatter()

        # 控制台处理器
        console_handler = self._create_console_handler(formatter)
        self.logger.addHandler(console_handler)

        # 文件处理器
        file_handler = self._create_file_handler(formatter)
        if file_handler:
            self.logger.addHandler(file_handler)

        self._loggers[self.name] = self.logger

    def _create_formatter(self) -> logging.Formatter:
        """创建日志格式化器"""
        config = get_config()

        if config.debug and COLORLOG_AVAILABLE:
            # 使用彩色日志格式
            formatter = colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white",
                },
            )
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        return formatter

    def _create_console_handler(
        self, formatter: logging.Formatter
    ) -> logging.StreamHandler:
        """
        创建控制台处理器

        Args:
            formatter: 日志格式化器

        Returns:
            控制台处理器
        """
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        return console_handler

    def _create_file_handler(
        self, formatter: logging.Formatter
    ) -> Optional[RotatingFileHandler]:
        """
        创建文件处理器

        Args:
            formatter: 日志格式化器

        Returns:
            文件处理器，如果失败返回None
        """
        config = get_config()
        log_file = config.log_file

        try:
            # 确保日志目录存在
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # 创建滚动文件处理器
            max_bytes = config.get("log.max_size", 10485760)  # 默认10MB
            backup_count = config.get("log.backup_count", 5)

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            return file_handler
        except Exception as e:
            print(f"创建日志文件处理器失败: {e}")
            return None

    def debug(self, message: str, *args, **kwargs) -> None:
        """记录调试日志"""
        if self.logger:
            self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        """记录信息日志"""
        if self.logger:
            self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        """记录警告日志"""
        if self.logger:
            self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        """记录错误日志"""
        if self.logger:
            self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        """记录严重错误日志"""
        if self.logger:
            self.logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs) -> None:
        """记录异常日志"""
        if self.logger:
            self.logger.exception(message, *args, **kwargs)


# 全局日志实例
_default_logger: Optional[Logger] = None


def get_logger(name: str = "market_task_tracker") -> Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器实例
    """
    return Logger(name)


def get_default_logger() -> Logger:
    """获取默认日志记录器"""
    global _default_logger
    if _default_logger is None:
        _default_logger = Logger()
    return _default_logger
