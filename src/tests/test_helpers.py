# -*- coding: utf-8 -*-
"""
工具函数模块单元测试
Helper Functions Unit Tests
"""

import pytest
from datetime import datetime, timedelta

# 设置项目根目录
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.helpers import (
    generate_id,
    generate_short_id,
    md5_hash,
    get_current_timestamp,
    get_current_timestamp_ms,
    timestamp_to_datetime,
    datetime_to_timestamp,
    format_datetime,
    parse_datetime,
    get_date_range,
    is_valid_email,
    is_valid_phone,
    sanitize_filename,
    truncate_string,
    safe_divide,
    chunk_list,
    flatten_dict,
    merge_dicts,
    filter_dict,
    remove_none_values,
    calculate_percentage,
    format_file_size,
)


class TestIdGeneration:
    """ID生成测试类"""

    def test_generate_id(self):
        """测试生成唯一ID"""
        id1 = generate_id()
        id2 = generate_id()
        assert id1 != id2
        assert len(id1) == 36  # UUID格式

    def test_generate_short_id(self):
        """测试生成短ID"""
        short_id = generate_short_id()
        assert len(short_id) == 8


class TestHashFunctions:
    """哈希函数测试类"""

    def test_md5_hash(self):
        """测试MD5哈希"""
        text = "hello world"
        hash1 = md5_hash(text)
        hash2 = md5_hash(text)
        assert hash1 == hash2
        assert len(hash1) == 32


class TestTimestampFunctions:
    """时间戳函数测试类"""

    def test_get_current_timestamp(self):
        """测试获取当前时间戳"""
        timestamp = get_current_timestamp()
        assert isinstance(timestamp, int)
        assert timestamp > 0

    def test_get_current_timestamp_ms(self):
        """测试获取毫秒时间戳"""
        timestamp = get_current_timestamp_ms()
        assert isinstance(timestamp, int)
        assert timestamp > 0

    def test_timestamp_conversion(self):
        """测试时间戳转换"""
        now = datetime.now()
        timestamp = datetime_to_timestamp(now)
        dt = timestamp_to_datetime(timestamp)
        assert abs((now - dt).total_seconds()) < 1


class TestDatetimeFunctions:
    """日期时间函数测试类"""

    def test_format_datetime(self):
        """测试格式化日期时间"""
        dt = datetime(2026, 6, 15, 12, 30, 45)
        result = format_datetime(dt, "%Y-%m-%d")
        assert result == "2026-06-15"

    def test_format_datetime_with_now(self):
        """测试格式化当前时间"""
        result = format_datetime()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_parse_datetime(self):
        """测试解析日期时间字符串"""
        date_str = "2026-06-15 12:30:45"
        dt = parse_datetime(date_str)
        assert dt.year == 2026
        assert dt.month == 6
        assert dt.day == 15

    def test_get_date_range(self):
        """测试获取日期范围"""
        start, end = get_date_range(days=7)
        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        assert (end - start).days == 7


class TestValidationFunctions:
    """验证函数测试类"""

    def test_is_valid_email(self):
        """测试邮箱验证"""
        assert is_valid_email("test@example.com") is True
        assert is_valid_email("user.name@domain.co.uk") is True
        assert is_valid_email("invalid.email") is False
        assert is_valid_email("@domain.com") is False

    def test_is_valid_phone(self):
        """测试手机号验证"""
        assert is_valid_phone("13812345678") is True
        assert is_valid_phone("15912345678") is True
        assert is_valid_phone("12345678901") is False
        assert is_valid_phone("1381234567") is False


class TestStringFunctions:
    """字符串函数测试类"""

    def test_sanitize_filename(self):
        """测试清理文件名"""
        result = sanitize_filename("test<>file?.txt")
        assert "<" not in result
        assert ">" not in result
        assert "?" not in result

    def test_truncate_string(self):
        """测试截断字符串"""
        text = "This is a long string"
        result = truncate_string(text, 10)
        assert len(result) <= 13  # 10 + len("...")
        assert result.endswith("...")


class TestMathFunctions:
    """数学函数测试类"""

    def test_safe_divide(self):
        """测试安全除法"""
        assert safe_divide(10, 2) == 5
        assert safe_divide(10, 0) == 0.0
        assert safe_divide(10, 0, 1.0) == 1.0

    def test_calculate_percentage(self):
        """测试百分比计算"""
        assert calculate_percentage(25, 100) == 25.0
        assert calculate_percentage(1, 3) == 33.33
        assert calculate_percentage(0, 100) == 0.0
        assert calculate_percentage(50, 0) == 0.0


class TestListFunctions:
    """列表函数测试类"""

    def test_chunk_list(self):
        """测试列表分块"""
        lst = [1, 2, 3, 4, 5, 6, 7]
        chunks = chunk_list(lst, 3)
        assert len(chunks) == 3
        assert chunks[0] == [1, 2, 3]
        assert chunks[2] == [7]


class TestDictFunctions:
    """字典函数测试类"""

    def test_flatten_dict(self):
        """测试字典扁平化"""
        d = {"a": {"b": 1, "c": 2}, "d": 3}
        result = flatten_dict(d)
        assert "a.b" in result
        assert "a.c" in result
        assert result["a.b"] == 1

    def test_merge_dicts(self):
        """测试字典合并"""
        d1 = {"a": 1, "b": 2}
        d2 = {"b": 3, "c": 4}
        result = merge_dicts(d1, d2)
        assert result["a"] == 1
        assert result["b"] == 3
        assert result["c"] == 4

    def test_filter_dict(self):
        """测试字典过滤"""
        d = {"a": 1, "b": 2, "c": 3}
        result = filter_dict(d, ["a", "c"])
        assert "a" in result
        assert "b" not in result
        assert "c" in result

    def test_remove_none_values(self):
        """测试移除None值"""
        d = {"a": 1, "b": None, "c": 3}
        result = remove_none_values(d)
        assert "a" in result
        assert "b" not in result
        assert "c" in result


class TestFileSizeFormatting:
    """文件大小格式化测试类"""

    def test_format_file_size(self):
        """测试格式化文件大小"""
        assert "B" in format_file_size(100)
        assert "KB" in format_file_size(1024)
        assert "MB" in format_file_size(1024 * 1024)
        assert "GB" in format_file_size(1024 * 1024 * 1024)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
