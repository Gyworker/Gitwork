# -*- coding: utf-8 -*-
"""
配置模块单元测试
Configuration Module Unit Tests
"""

import pytest
from pathlib import Path
import tempfile
import os

# 设置项目根目录
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import Config, get_config


class TestConfig:
    """配置测试类"""

    def setup_method(self):
        """测试前设置"""
        # 重置单例
        Config._instance = None
        Config._config = {}

    def teardown_method(self):
        """测试后清理"""
        Config._instance = None
        Config._config = {}

    def test_singleton_pattern(self):
        """测试单例模式"""
        config1 = Config()
        config2 = Config()
        assert config1 is config2

    def test_get_instance(self):
        """测试获取实例方法"""
        instance1 = Config.get_instance()
        instance2 = Config.get_instance()
        assert instance1 is instance2

    def test_get_default_values(self):
        """测试获取默认值"""
        config = Config()
        assert config.app_name == "市场咨询任务跟踪工具"
        assert config.app_version == "1.0.0"
        assert config.debug is False
        assert config.database_path == "data/market_task_tracker.db"
        assert config.log_level == "INFO"

    def test_get_nested_value(self):
        """测试获取嵌套配置值"""
        config = Config()
        assert config.get("app.name") == "市场咨询任务跟踪工具"
        assert config.get("app.version") == "1.0.0"
        assert config.get("database.type") == "sqlite"

    def test_get_with_default(self):
        """测试获取不存在的配置值"""
        config = Config()
        assert config.get("nonexistent.key", "default") == "default"
        assert config.get("app.nonexistent", "fallback") == "fallback"

    def test_set_value(self):
        """测试设置配置值"""
        config = Config()
        config.set("test.key", "test_value")
        assert config.get("test.key") == "test_value"

    def test_set_nested_value(self):
        """测试设置嵌套配置值"""
        config = Config()
        config.set("new.nested.key", "nested_value")
        assert config.get("new.nested.key") == "nested_value"

    def test_properties(self):
        """测试配置属性"""
        config = Config()

        # 测试属性访问
        assert isinstance(config.app_name, str)
        assert isinstance(config.app_version, str)
        assert isinstance(config.debug, bool)
        assert isinstance(config.database_path, str)
        assert isinstance(config.log_level, str)


class TestGetConfig:
    """get_config函数测试"""

    def setup_method(self):
        """测试前设置"""
        Config._instance = None
        Config._config = {}

    def teardown_method(self):
        """测试后清理"""
        Config._instance = None
        Config._config = {}

    def test_get_config_returns_config_instance(self):
        """测试get_config返回Config实例"""
        config = get_config()
        assert isinstance(config, Config)

    def test_get_config_returns_same_instance(self):
        """测试get_config返回同一实例"""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
