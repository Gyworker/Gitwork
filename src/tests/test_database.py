# -*- coding: utf-8 -*-
"""
数据库模块单元测试
Database Module Unit Tests
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime

# 设置项目根目录
# 方法1：使用相对路径（推荐用于包内导入）
import sys
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 方法2：直接导入src包（需要src目录下有__init__.py）
# 这确保了无论从哪个目录运行测试，都能正确导入模块
os.chdir(project_root)  # 切换到项目根目录

from src.database.connection import DatabaseConnection
from src.database.models import Task, init_database


class TestDatabaseConnection:
    """数据库连接测试类"""

    def setup_method(self):
        """测试前设置"""
        # 创建临时数据库
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = os.path.join(self.temp_dir, "test.db")

        # 创建一个独立的数据库连接实例进行测试
        self.db = DatabaseConnection()
        # 使用临时数据库
        self.db._connection = None
        self.db._config._config["database"]["path"] = self.temp_db

    def teardown_method(self):
        """测试后清理"""
        if self.db._connection:
            self.db.disconnect()
        # 清理临时文件
        if os.path.exists(self.temp_db):
            os.remove(self.temp_db)
        os.rmdir(self.temp_dir)

    def test_singleton_pattern(self):
        """测试单例模式"""
        db1 = DatabaseConnection()
        db2 = DatabaseConnection()
        assert db1 is db2

    def test_connect(self):
        """测试数据库连接"""
        conn = self.db.connect()
        assert conn is not None

    def test_execute_query(self):
        """测试执行查询"""
        self.db.connect()
        cursor = self.db.execute("SELECT 1 as test")
        result = cursor.fetchone()
        assert result[0] == 1

    def test_insert_and_fetch(self):
        """测试插入和查询"""
        self.db.connect()
        self.db.execute(
            "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)",
            commit=True,
        )

        # 插入数据
        self.db.execute(
            "INSERT INTO test_table (name) VALUES (?)",
            ("test_name",),
            commit=True,
        )

        # 查询数据
        result = self.db.fetchone("SELECT * FROM test_table WHERE name = ?", ("test_name",))
        assert result is not None
        assert result[1] == "test_name"

    def test_fetchall(self):
        """测试查询所有"""
        self.db.connect()
        self.db.execute(
            "CREATE TABLE test_table2 (id INTEGER PRIMARY KEY, value INTEGER)",
            commit=True,
        )

        # 插入多条数据
        for i in range(5):
            self.db.execute(
                "INSERT INTO test_table2 (value) VALUES (?)",
                (i,),
                commit=True,
            )

        results = self.db.fetchall("SELECT * FROM test_table2")
        assert len(results) == 5

    def test_table_exists(self):
        """测试表是否存在"""
        self.db.connect()
        self.db.execute(
            "CREATE TABLE existing_table (id INTEGER PRIMARY KEY)",
            commit=True,
        )

        assert self.db.table_exists("existing_table") is True
        assert self.db.table_exists("nonexistent_table") is False

    def test_get_tables(self):
        """测试获取所有表"""
        self.db.connect()
        self.db.execute(
            "CREATE TABLE table1 (id INTEGER PRIMARY KEY)",
            commit=True,
        )
        self.db.execute(
            "CREATE TABLE table2 (id INTEGER PRIMARY KEY)",
            commit=True,
        )

        tables = self.db.get_tables()
        assert "table1" in tables
        assert "table2" in tables


class TestTaskModel:
    """任务模型测试类"""

    def setup_method(self):
        """测试前设置"""
        # 创建临时数据库
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = os.path.join(self.temp_dir, "test.db")

        # 重置数据库连接
        DatabaseConnection._instance = None
        self.db = DatabaseConnection()
        self.db._connection = None
        self.db._config._config["database"]["path"] = self.temp_db

        # 初始化数据库
        init_database()

    def teardown_method(self):
        """测试后清理"""
        if self.db._connection:
            self.db.disconnect()
        # 清理临时文件
        if os.path.exists(self.temp_db):
            os.remove(self.temp_db)
        os.rmdir(self.temp_dir)

    def test_task_creation(self):
        """测试任务创建"""
        task = Task(
            task_name="测试任务",
            inquirer="张三",
            task_content="测试内容",
        )
        assert task.task_id is not None
        assert task.task_name == "测试任务"
        assert task.status == "进行中"
        assert task.urgency == "中"

    def test_task_save(self):
        """测试任务保存"""
        task = Task(
            task_name="测试任务",
            inquirer="张三",
            task_content="测试内容",
        )
        assert task.save() is True

    def test_task_get_by_id(self):
        """测试根据ID获取任务"""
        task = Task(
            task_name="测试任务",
            inquirer="张三",
            task_content="测试内容",
        )
        task.save()

        retrieved_task = Task.get_by_id(task.task_id)
        assert retrieved_task is not None
        assert retrieved_task.task_name == "测试任务"
        assert retrieved_task.inquirer == "张三"

    def test_task_update(self):
        """测试任务更新"""
        task = Task(
            task_name="测试任务",
            inquirer="张三",
        )
        task.save()

        task.task_name = "更新后的任务"
        task.save()

        updated_task = Task.get_by_id(task.task_id)
        assert updated_task.task_name == "更新后的任务"

    def test_task_delete(self):
        """测试任务删除"""
        task = Task(
            task_name="测试任务",
            inquirer="张三",
        )
        task.save()

        assert task.delete() is True

        deleted_task = Task.get_by_id(task.task_id)
        assert deleted_task is None

    def test_task_search(self):
        """测试任务搜索"""
        task1 = Task(task_name="市场咨询任务", inquirer="张三")
        task2 = Task(task_name="技术支持任务", inquirer="李四")
        task1.save()
        task2.save()

        results = Task.search("市场")
        assert len(results) >= 1
        assert any(t.task_name == "市场咨询任务" for t in results)

    def test_task_to_dict(self):
        """测试任务转字典"""
        task = Task(
            task_name="测试任务",
            inquirer="张三",
        )
        data = task.to_dict()

        assert "task_id" in data
        assert "task_name" in data
        assert "inquirer" in data
        assert data["task_name"] == "测试任务"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
