"""
核心模块测试
测试工具函数、配置管理等核心功能
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.core.utils import (
    generate_id,
    format_datetime,
    parse_datetime,
    validate_email,
    validate_phone,
    truncate_text,
    safe_dict_get,
)
from src.core.config import ConfigManager, load_config, save_config
from src.core.logger import get_logger, setup_logging


class TestUtils:
    """工具函数测试"""
    
    def test_generate_id(self):
        """测试ID生成"""
        id1 = generate_id()
        id2 = generate_id()
        
        assert id1 is not None
        assert id2 is not None
        assert id1 != id2
        assert isinstance(id1, int)
    
    def test_format_datetime(self):
        """测试日期时间格式化"""
        dt = datetime(2026, 6, 16, 12, 30, 45)
        
        # 默认格式
        result = format_datetime(dt)
        assert "2026" in result
        
        # 自定义格式
        result = format_datetime(dt, "%Y-%m-%d")
        assert result == "2026-06-16"
    
    def test_parse_datetime(self):
        """测试日期时间解析"""
        # 标准格式
        dt = parse_datetime("2026-06-16 12:30:45")
        assert dt.year == 2026
        assert dt.month == 6
        assert dt.day == 16
        
        # 另一种格式
        dt = parse_datetime("2026/06/16")
        assert dt.year == 2026
    
    def test_validate_email(self):
        """测试邮箱验证"""
        # 有效邮箱
        assert validate_email("test@example.com") == True
        assert validate_email("user.name@domain.co.uk") == True
        
        # 无效邮箱
        assert validate_email("invalid") == False
        assert validate_email("@example.com") == False
        assert validate_email("test@") == False
    
    def test_validate_phone(self):
        """测试电话验证"""
        # 有效电话
        assert validate_phone("13800138000") == True
        assert validate_phone("010-12345678") == True
        
        # 无效电话
        assert validate_phone("123") == False
        assert validate_phone("abcdefghijk") == False
    
    def test_truncate_text(self):
        """测试文本截断"""
        text = "这是一段很长的文本，需要被截断"
        
        result = truncate_text(text, max_length=10)
        assert len(result) <= 13  # 10 + 省略号
        assert "..." in result
    
    def test_safe_dict_get(self):
        """测试安全字典获取"""
        data = {"a": {"b": {"c": "value"}}}
        
        # 正常获取
        assert safe_dict_get(data, "a.b.c") == "value"
        
        # 获取不存在的键
        assert safe_dict_get(data, "a.b.d") is None
        assert safe_dict_get(data, "a.b.d", default="default") == "default"


class TestConfig:
    """配置管理测试"""
    
    @pytest.fixture
    def temp_config(self):
        """临时配置文件"""
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)
    
    def test_config_creation(self, temp_config):
        """测试配置创建"""
        config = ConfigManager(temp_config)
        assert config is not None
    
    def test_config_load(self, temp_config):
        """测试配置加载"""
        # 写入配置
        data = {"key": "value", "number": 42}
        with open(temp_config, 'w') as f:
            json.dump(data, f)
        
        # 加载配置
        config = ConfigManager(temp_config)
        assert config.get("key") == "value"
        assert config.get("number") == 42
    
    def test_config_save(self, temp_config):
        """测试配置保存"""
        config = ConfigManager(temp_config)
        config.set("test_key", "test_value")
        config.save()
        
        # 重新加载
        config2 = ConfigManager(temp_config)
        assert config2.get("test_key") == "test_value"
    
    def test_config_get_set(self, temp_config):
        """测试配置获取设置"""
        config = ConfigManager(temp_config)
        
        config.set("string_val", "hello")
        config.set("int_val", 123)
        config.set("bool_val", True)
        
        assert config.get("string_val") == "hello"
        assert config.get("int_val") == 123
        assert config.get("bool_val") == True
    
    def test_config_nested(self, temp_config):
        """测试嵌套配置"""
        config = ConfigManager(temp_config)
        
        config.set("database.host", "localhost")
        config.set("database.port", 3306)
        
        assert config.get("database.host") == "localhost"
        assert config.get("database.port") == 3306
    
    def test_load_save_functions(self, temp_config):
        """测试便捷函数"""
        data = {"test": "value"}
        save_config(temp_config, data)
        
        loaded = load_config(temp_config)
        assert loaded["test"] == "value"


class TestLogger:
    """日志测试"""
    
    @pytest.fixture
    def log_file(self):
        """日志文件"""
        fd, path = tempfile.mkstemp(suffix=".log")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)
    
    def test_logger_creation(self):
        """测试日志器创建"""
        logger = get_logger("test")
        assert logger is not None
    
    def test_logger_output(self, log_file):
        """测试日志输出"""
        setup_logging(log_file)
        logger = get_logger("test_output")
        
        logger.info("Test message")
        
        # 验证日志写入
        with open(log_file, 'r') as f:
            content = f.read()
            assert "Test message" in content
    
    def test_log_levels(self, log_file):
        """测试日志级别"""
        setup_logging(log_file, level="DEBUG")
        logger = get_logger("test_levels")
        
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        with open(log_file, 'r') as f:
            content = f.read()
            assert "Debug message" in content
            assert "Info message" in content
            assert "Warning message" in content
            assert "Error message" in content


class TestDataExport:
    """数据导出测试"""
    
    @pytest.fixture
    def temp_export_dir(self):
        """临时导出目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_csv_export(self, temp_export_dir, temp_db):
        """测试CSV导出"""
        from src.core.data_export import DataExporter
        
        exporter = DataExporter(temp_db)
        output_path = os.path.join(temp_export_dir, "export.csv")
        
        result = exporter.export_tasks_csv(output_path)
        assert result is True
        assert os.path.exists(output_path)


class TestStatistics:
    """统计分析测试"""
    
    @pytest.fixture
    def stats_data(self, temp_db):
        """统计数据"""
        from src.database.connection import DatabaseManager
        
        db = DatabaseManager(temp_db)
        
        # 创建测试任务
        for i in range(10):
            db.tasks.create(
                title=f"统计测试任务{i}",
                status=["pending", "in_progress", "completed"][i % 3],
                importance=["low", "medium", "high"][i % 3],
            )
        
        return db
    
    def test_status_distribution(self, stats_data):
        """测试状态分布统计"""
        from src.core.statistics import Statistics
        
        stats = Statistics(stats_data)
        distribution = stats.get_status_distribution()
        
        assert "pending" in distribution
        assert "in_progress" in distribution
        assert "completed" in distribution
    
    def test_importance_distribution(self, stats_data):
        """测试重要性分布统计"""
        from src.core.statistics import Statistics
        
        stats = Statistics(stats_data)
        distribution = stats.get_importance_distribution()
        
        assert "low" in distribution
        assert "medium" in distribution
        assert "high" in distribution


class TestPerformance:
    """性能测试"""
    
    @pytest.mark.slow
    @pytest.mark.performance
    def test_large_data_performance(self, temp_db):
        """测试大数据量性能"""
        import time
        from src.database.connection import DatabaseManager
        
        db = DatabaseManager(temp_db)
        
        # 插入1000条记录
        start = time.time()
        for i in range(1000):
            db.tasks.create(
                title=f"性能测试任务{i}",
                status="pending",
            )
        duration = time.time() - start
        
        # 验证性能
        assert duration < 30  # 30秒内完成
        
        # 查询性能
        start = time.time()
        tasks = db.tasks.list_all()
        query_duration = time.time() - start
        
        assert query_duration < 2  # 2秒内完成查询


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
