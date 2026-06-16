# -*- coding: utf-8 -*-
"""
异常处理模块
Exception Handling Module

提供统一的异常处理机制
"""

import traceback
from typing import Optional, Callable, Any
from functools import wraps

from .logger import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    """应用程序异常基类"""

    def __init__(self, message: str, code: Optional[str] = None, details: Optional[dict] = None) -> None:
        """
        初始化异常

        Args:
            message: 错误消息
            code: 错误代码
            details: 详细信息
        """
        super().__init__(message)
        self.message = message
        self.code = code or "APP_ERROR"
        self.details = details or {}

    def __str__(self) -> str:
        """返回异常字符串表示"""
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class ValidationException(AppException):
    """数据验证异常"""

    def __init__(self, message: str, field: Optional[str] = None) -> None:
        super().__init__(message, code="VALIDATION_ERROR", details={"field": field})


class DatabaseException(AppException):
    """数据库操作异常"""

    def __init__(self, message: str, sql: Optional[str] = None) -> None:
        super().__init__(message, code="DATABASE_ERROR", details={"sql": sql})


class ConfigException(AppException):
    """配置异常"""

    def __init__(self, message: str, key: Optional[str] = None) -> None:
        super().__init__(message, code="CONFIG_ERROR", details={"key": key})


class TaskNotFoundException(AppException):
    """任务未找到异常"""

    def __init__(self, task_id: str) -> None:
        super().__init__(
            f"任务未找到: {task_id}",
            code="TASK_NOT_FOUND",
            details={"task_id": task_id}
        )


class InvalidStatusTransitionException(AppException):
    """无效状态转换异常"""

    def __init__(self, from_status: str, to_status: str) -> None:
        super().__init__(
            f"无效的状态转换: {from_status} -> {to_status}",
            code="INVALID_STATUS_TRANSITION",
            details={"from_status": from_status, "to_status": to_status}
        )


def handle_exception(
    func: Optional[Callable] = None,
    default_return: Any = None,
    log_traceback: bool = True,
) -> Callable:
    """
    异常处理装饰器

    Args:
        func: 被装饰的函数
        default_return: 异常时的默认返回值
        log_traceback: 是否记录堆栈跟踪

    Returns:
        装饰后的函数
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except AppException as e:
                logger.error(f"应用异常: {e}")
                if log_traceback:
                    logger.exception(e)
                return default_return
            except Exception as e:
                logger.error(f"未知异常: {e}")
                if log_traceback:
                    logger.exception(e)
                return default_return

        return wrapper

    if func:
        return decorator(func)
    return decorator


def safe_execute(func: Callable, *args, **kwargs) -> tuple:
    """
    安全执行函数

    Args:
        func: 要执行的函数
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        (成功标志, 结果/错误消息)
    """
    try:
        result = func(*args, **kwargs)
        return True, result
    except AppException as e:
        logger.error(f"应用异常: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"执行函数失败: {e}")
        logger.exception(e)
        return False, str(e)


class ErrorHandler:
    """全局错误处理器"""

    _instance: Optional["ErrorHandler"] = None

    def __new__(cls) -> "ErrorHandler":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self._error_callbacks = []
        self._logger = get_logger(__name__)

    def register_callback(self, callback: Callable[[Exception], None]) -> None:
        """
        注册错误回调

        Args:
            callback: 回调函数
        """
        self._error_callbacks.append(callback)

    def handle(self, error: Exception, context: Optional[dict] = None) -> None:
        """
        处理错误

        Args:
            error: 异常对象
            context: 上下文信息
        """
        # 记录日志
        self._logger.error(f"错误处理: {error}")
        if context:
            self._logger.error(f"上下文: {context}")
        self._logger.exception(error)

        # 调用回调
        for callback in self._error_callbacks:
            try:
                callback(error)
            except Exception as e:
                self._logger.error(f"错误回调失败: {e}")

    def get_error_info(self, error: Exception) -> dict:
        """
        获取错误信息

        Args:
            error: 异常对象

        Returns:
            错误信息字典
        """
        return {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }


# 全局错误处理器实例
error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """获取错误处理器"""
    return error_handler
