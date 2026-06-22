# -*- coding: utf-8 -*-
"""
异常处理模块单元测试
Exception Handler Unit Tests:

测试统一异常处理模块的功能
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.exception_handler import (
    AppException,
    DatabaseException,
    ValidationException,
    FileOperationException,
    NetworkException,
    ServiceException,
    safe_execute,
    handle_database_error,
    handle_file_error,
    handle_network_error,
    ErrorHandler,
    try_except
)


class TestCustomExceptions:
    """测试自定义异常类"""

    def test_app_exception_basic(self):
        """测试基础异常"""
        exc = AppException("测试错误")
        assert str(exc) == "测试错误"
        assert exc.message == "测试错误"
        assert exc.code is None

    def test_app_exception_with_code(self):
        """测试带代码的异常"""
        exc = AppException("测试错误", code="TEST_ERROR")
        assert str(exc) == "[TEST_ERROR] 测试错误"
        assert exc.code == "TEST_ERROR"

    def test_app_exception_with_details(self):
        """测试带详情的异常"""
        details = {"field": "username", "value": ""}
        exc = AppException("字段不能为空", code="VALIDATION", details=details)
        assert exc.details == details
        assert exc.details["field"] == "username"

    def test_database_exception(self):
        """测试数据库异常"""
        exc = DatabaseException("连接失败")
        assert exc.code == "DB_ERROR"
        assert isinstance(exc, AppException)

    def test_validation_exception(self):
        """测试验证异常"""
        exc = ValidationException("格式错误")
        assert exc.code == "VALIDATION_ERROR"

    def test_file_operation_exception(self):
        """测试文件操作异常"""
        exc = FileOperationException("文件不存在")
        assert exc.code == "FILE_ERROR"

    def test_network_exception(self):
        """测试网络异常"""
        exc = NetworkException("连接超时")
        assert exc.code == "NETWORK_ERROR"

    def test_service_exception(self):
        """测试服务异常"""
        exc = ServiceException("服务不可用")
        assert exc.code == "SERVICE_ERROR"


class TestSafeExecuteDecorator:
    """测试safe_execute装饰器"""

    def test_normal_function(self):
        """测试正常函数执行"""
        @safe_execute(default_return=False)
        def add(a, b):
            return a + b

        assert add(1, 2) == 3

    def test_exception_returns_default(self):
        """测试异常返回默认值"""
        @safe_execute(default_return=False)
        def raise_error():
            raise ValueError("测试错误")

        result = raise_error()
        assert result is False

    def test_exception_with_custom_message(self):
        """测试带自定义消息的异常处理"""
        @safe_execute(default_return=False, error_message="自定义错误")
        def raise_error():
            raise ValueError("测试错误")

        result = raise_error()
        assert result is False

    def test_app_exception_reraise(self):
        """测试已知异常重新抛出"""
        @safe_execute(reraise=True)
        def raise_app_exception():
            raise AppException("测试")

        with pytest.raises(AppException):
            raise_app_exception()

    def test_decorator_preserves_function_name(self):
        """测试装饰器保留函数名"""
        @safe_execute(default_return=False)
        def my_function():
            return True

        assert my_function.__name__ == "my_function"


class TestDatabaseErrorHandler:
    """测试数据库错误处理装饰器"""

    def test_normal_execution(self):
        """测试正常执行"""
        @handle_database_error
        def query():
            return [{"id": 1}]

        result = query()
        assert result == [{"id": 1}]

    def test_exception_returns_none(self):
        """测试异常返回None"""
        @handle_database_error
        def query_with_error():
            raise Exception("DB Error")

        result = query_with_error()
        assert result is None


class TestFileErrorHandler:
    """测试文件错误处理装饰器"""

    def test_file_not_found(self):
        """测试文件不存在"""
        @handle_file_error(default_return=None)
        def read_file():
            with open("nonexistent.txt", "r") as f:
                return f.read()

        result = read_file()
        assert result is None

    def test_normal_file_operation(self):
        """测试正常文件操作"""
        import tempfile

        @handle_file_error(default_return=None)
        def write_and_read():
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write("test content")
                path = f.name
            with open(path, 'r') as f:
                return f.read()

        result = write_and_read()
        assert result == "test content"


class TestNetworkErrorHandler:
    """测试网络错误处理装饰器"""

    def test_normal_request(self):
        """测试正常请求"""
        @handle_network_error(default_return=None)
        def fetch_data():
            return {"data": "test"}

        result = fetch_data()
        assert result == {"data": "test"}


class TestErrorHandler:
    """测试ErrorHandler工具类"""

    def test_categorize_database_error(self):
        """测试数据库错误分类"""
        import sqlite3
        error = sqlite3.Error("test")
        category = ErrorHandler.categorize_error(error)
        assert category == "database"

    def test_categorize_file_error(self):
        """测试文件错误分类"""
        error = FileNotFoundError("test")
        category = ErrorHandler.categorize_error(error)
        assert category == "file"

    def test_categorize_validation_error(self):
        """测试验证错误分类"""
        error = ValueError("test")
        category = ErrorHandler.categorize_error(error)
        assert category == "validation"

    def test_format_error_info(self):
        """测试格式化错误信息"""
        error = ValueError("测试错误")
        info = ErrorHandler.format_error_info(error)
        assert "ValueError" in info
        assert "测试错误" in info

    def test_format_error_info_with_traceback(self):
        """测试格式化错误信息(包含堆栈)"""
        error = ValueError("测试错误")
        info = ErrorHandler.format_error_info(error, include_traceback=True)
        assert "ValueError" in info
        assert "Traceback" in info


class TestTryExceptDecorator:
    """测试try_except装饰器"""

    def test_normal_execution(self):
        """测试正常执行"""
        @try_except(default_return=False)
        def get_value():
            return 42

        assert get_value() == 42

    def test_catch_specific_exception(self):
        """测试捕获特定异常"""
        @try_except(default_return=-1, error_types=(ValueError,))
        def convert_value():
            raise ValueError("invalid")

        assert convert_value() == -1

    def test_reraise_non_catchable(self):
        """测试非捕获异常重新抛出"""
        @try_except(error_types=(ValueError,))
        def raise_type_error():
            raise TypeError("not catchable")

        with pytest.raises(TypeError):
            raise_type_error()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
