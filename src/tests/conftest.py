"""
测试配置和夹具
提供测试所需的通用配置和夹具函数
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

import pytest


def pytest_configure(config):
    """Pytest配置钩子"""
    # 添加自定义标记
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "ui: marks tests as UI tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )


@pytest.fixture(scope="session")
def test_data_dir():
    """测试数据目录"""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def temp_db():
    """临时数据库夹具"""
    # 创建临时数据库
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    
    # 初始化测试数据库
    from src.database.connection import DatabaseManager
    from src.database.models import init_database
    
    db = DatabaseManager(db_path)
    init_database(db.get_connection())
    
    yield db_path
    
    # 清理
    db.close()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_task_data():
    """示例任务数据"""
    return {
        "title": "测试任务",
        "description": "这是一个测试任务",
        "task_type": "咨询",
        "status": "pending",
        "importance": "high",
        "requester": "张三",
        "requester_dept": "市场部",
        "consultant": "李四",
        "consultant_dept": "技术部",
        "responder": "王五",
        "deadline": "2026-06-30",
        "key_module": "数据分析",
        "industry": "金融",
        "estimated_hours": 8,
    }


@pytest.fixture
def sample_contact_data():
    """示例联系人数据"""
    return {
        "name": "测试联系人",
        "department": "测试部门",
        "position": "测试工程师",
        "phone": "13800138000",
        "email": "test@example.com",
        "tags": "测试,样例",
    }


@pytest.fixture
def sample_recommendation_data():
    """示例推荐数据"""
    return {
        "keyword": "数据分析",
        "task_title": "数据分析咨询",
        "task_id": None,
        "description": "数据分析相关任务推荐",
        "source": "manual",
    }


@pytest.fixture
def mock_qt_app():
    """Mock Qt应用夹具"""
    # 在CI环境中跳过需要Qt的测试
    pytest.skip("UI tests require display", allow_module_level=True)
