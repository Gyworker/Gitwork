# -*- coding: utf-8 -*-
"""
统一异常处理模块
Exception Handler Module:

提供分类异常处理和统一日志记录功能
"""

import traceback
from typing import Optional, Callable, Any, Type, Tuple
from functools import wraps

from .logger import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    """应用基础异常类"""
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def __str__(self):
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class DatabaseException(AppException):
    """数据库操作异常"""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, code="DB_ERROR", details=details)


class ValidationException(AppException):
    """数据验证异常"""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class FileOperationException(AppException):
    """文件操作异常"""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, code="FILE_ERROR", details=details)


class NetworkException(AppException):
    """网络请求异常"""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, code="NETWORK_ERROR", details=details)


class ServiceException(AppException):
    """服务层异常"""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, code="SERVICE_ERROR", details=details)


def safe_execute(
    default_return: Any = None,
    log_errors: bool = True,
    reraise: bool = False,
    error_message: Optional[str] = None
) -> Callable:
    """
    安全执行装饰器

    Args:
        default_return: 异常时返回的默认值
        log_errors: 是否记录错误日志
        reraise: 是否重新抛出异常
        error_message: 自定义错误消息前缀

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except AppException as e:
                # 已知应用异常
                if log_errors:
                    logger.warning(f"{error_message or '业务异常'}: {e}")
                if reraise:
                    raise
                return default_return
            except (DatabaseException, ValidationException,
                    FileOperationException, NetworkException, ServiceException) as e:
                # 特定类型异常
                if log_errors:
                    logger.warning(f"{error_message or '业务异常'}: {e}")
                if reraise:
                    raise
                return default_return
            except Exception as e:
                # 未知异常
                if log_errors:
                    logger.error(
                        f"{error_message or '执行失败'}: {func.__name__} - {str(e)}",
                        exc_info=True
                    )
                if reraise:
                    raise
                return default_return
        return wrapper
    return decorator


def handle_database_error(func: Callable) -> Callable:
    """
    数据库错误处理装饰器

    专门处理数据库相关异常
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"数据库操作失败: {func.__name__} - {str(e)}", exc_info=True)
            return None
    return wrapper


def handle_file_error(
    func: Callable = None,
    default_return: Any = None
) -> Callable:
    """
    文件操作错误处理装饰器

    专门处理文件读写相关异常
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return f(*args, **kwargs)
            except FileNotFoundError:
                logger.error(f"文件不存在: {f.__name__}")
                return default_return
            except PermissionError:
                logger.error(f"文件权限不足: {f.__name__}")
                return default_return
            except OSError as e:
                logger.error(f"文件操作失败: {f.__name__} - {str(e)}")
                return default_return
            except Exception as e:
                logger.error(f"文件操作异常: {f.__name__} - {str(e)}", exc_info=True)
                return default_return
        return wrapper

    if func is None:
        return decorator
    return decorator(func)


def handle_network_error(
    func: Callable = None,
    default_return: Any = None,
    retry_count: int = 0
) -> Callable:
    """
    网络请求错误处理装饰器

    专门处理网络请求相关异常
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs) -> Any:
            import requests

            last_error = None
            for attempt in range(retry_count + 1):
                try:
                    return f(*args, **kwargs)
                except requests.exceptions.Timeout:
                    last_error = "请求超时"
                    logger.warning(f"网络请求超时 (尝试 {attempt + 1}/{retry_count + 1}): {f.__name__}")
                except requests.exceptions.ConnectionError:
                    last_error = "连接失败"
                    logger.warning(f"网络连接失败 (尝试 {attempt + 1}/{retry_count + 1}): {f.__name__}")
                except requests.exceptions.HTTPError as e:
                    last_error = f"HTTP错误: {e.response.status_code}"
                    logger.warning(f"HTTP错误 (尝试 {attempt + 1}/{retry_count + 1}): {f.__name__}")
                except requests.exceptions.RequestException as e:
                    last_error = str(e)
                    logger.warning(f"请求异常 (尝试 {attempt + 1}/{retry_count + 1}): {f.__name__}")
                except Exception as e:
                    last_error = str(e)
                    logger.error(f"网络操作异常: {f.__name__} - {str(e)}", exc_info=True)
                    break

            return default_return
        return wrapper

    if func is None:
        return decorator
    return decorator(func)


class ErrorHandler:
    """错误处理器类"""

    @staticmethod
    def log_exception(
        error: Exception,
        context: str = "",
        level: str = "error"
    ) -> None:
        """
        记录异常日志

        Args:
            error: 异常对象
            context: 上下文信息
            level: 日志级别 (error, warning, info)
        """
        error_type = type(error).__name__
        error_msg = str(error)
        context_msg = f" [{context}]" if context else ""

        log_func = getattr(logger, level, logger.error)
        log_func(
            f"异常: {error_type}{context_msg} - {error_msg}",
            exc_info=True
        )

    @staticmethod
    def format_error_info(
        error: Exception,
        include_traceback: bool = False
    ) -> str:
        """
        格式化错误信息

        Args:
            error: 异常对象
            include_traceback: 是否包含堆栈信息

        Returns:
            格式化后的错误字符串
        """
        error_type = type(error).__name__
        error_msg = str(error)

        result = f"{error_type}: {error_msg}"

        if include_traceback:
            result += f"\n\n堆栈信息:\n{traceback.format_exc()}"

        return result

    @staticmethod
    def categorize_error(error: Exception) -> str:
        """
        分类错误类型

        Args:
            error: 异常对象

        Returns:
            错误类型字符串
        """
        error_type = type(error).__name__

        categories = {
            "database": ["sqlite3.Error", "OperationalError",
                         "ProgrammingError", "IntegrityError"],
            "file": ["FileNotFoundError", "PermissionError",
                    "IsADirectoryError", "OSError"],
            "network": ["requests.exceptions.Timeout",
                       "requests.exceptions.ConnectionError",
                       "requests.exceptions.HTTPError",
                       "requests.exceptions.RequestException"],
            "validation": ["ValueError", "TypeError", "KeyError", "IndexError"],
        }

        for category, types in categories.items():
            if error_type in types:
                return category

        return "unknown"


def try_except(
    default_return: Any = None,
    error_types: Optional[Tuple[Type[Exception], ...]] = None,
    on_error: Optional[Callable[[Exception], None]] = None
) -> Callable:
    """
    try-except简化装饰器

    Args:
        default_return: 默认返回值
        error_types: 要捕获的异常类型元组
        on_error: 错误回调函数

    Example:
        @try_except(default_return=False)
        def my_function():
            # 可能抛出异常的操作
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if error_types and not isinstance(e, error_types):
                    raise
                if on_error:
                    on_error(e)
                else:
                    logger.debug(f"{func.__name__} 异常: {str(e)}")
                return default_return
        return wrapper
    return decorator
