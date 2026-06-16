"""
数据库模块测试
测试数据库连接、CRUD操作、事务处理等
"""

import pytest
import sqlite3
import threading
import time
from pathlib import Path
from contextlib import contextmanager

from src.database.connection import DatabaseManager
from src.database.models import Task, Contact, Recommendation


class TestDatabase:
    """数据库测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self, temp_db):
        """设置测试环境"""
        self.db_path = temp_db
        self.db = DatabaseManager(self.db_path)
        self.conn = self.db.get_connection()
        yield
        self.db.close()
    
    def test_connection(self):
        """测试数据库连接"""
        assert self.conn is not None
        assert isinstance(self.conn, sqlite3.Connection)
        
        # 测试连接是否正常
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1
    
    def test_task_crud(self, sample_task_data):
        """测试任务CRUD操作"""
        # Create - 创建任务
        task_id = self.db.tasks.create(**sample_task_data)
        assert task_id is not None
        assert task_id > 0
        
        # Read - 读取任务
        task = self.db.tasks.get_by_id(task_id)
        assert task is not None
        assert task.title == sample_task_data["title"]
        assert task.description == sample_task_data["description"]
        
        # Update - 更新任务
        new_title = "更新后的任务"
        self.db.tasks.update(task_id, title=new_title)
        updated_task = self.db.tasks.get_by_id(task_id)
        assert updated_task.title == new_title
        
        # Delete - 删除任务
        self.db.tasks.delete(task_id)
        deleted_task = self.db.tasks.get_by_id(task_id)
        assert deleted_task is None
    
    def test_task_list(self, sample_task_data):
        """测试任务列表"""
        # 创建多个任务
        for i in range(5):
            data = sample_task_data.copy()
            data["title"] = f"任务{i}"
            self.db.tasks.create(**data)
        
        # 获取列表
        tasks = self.db.tasks.list_all()
        assert len(tasks) >= 5
        
        # 测试分页
        tasks_page = self.db.tasks.list_all(page=1, page_size=2)
        assert len(tasks_page) <= 2
    
    def test_task_filter(self, sample_task_data):
        """测试任务筛选"""
        # 创建不同状态的任务
        statuses = ["pending", "in_progress", "completed"]
        for status in statuses:
            data = sample_task_data.copy()
            data["status"] = status
            self.db.tasks.create(**data)
        
        # 按状态筛选
        pending_tasks = self.db.tasks.filter(status="pending")
        assert all(t.status == "pending" for t in pending_tasks)
        
        # 按重要性筛选
        high_tasks = self.db.tasks.filter(importance="high")
        assert all(t.importance == "high" for t in high_tasks)
    
    def test_contact_crud(self, sample_contact_data):
        """测试联系人CRUD操作"""
        # Create
        contact_id = self.db.contacts.create(**sample_contact_data)
        assert contact_id is not None
        
        # Read
        contact = self.db.contacts.get_by_id(contact_id)
        assert contact.name == sample_contact_data["name"]
        
        # Update
        self.db.contacts.update(contact_id, name="新姓名")
        updated = self.db.contacts.get_by_id(contact_id)
        assert updated.name == "新姓名"
        
        # Delete
        self.db.contacts.delete(contact_id)
        deleted = self.db.contacts.get_by_id(contact_id)
        assert deleted is None
    
    def test_contact_search(self, sample_contact_data):
        """测试联系人搜索"""
        # 创建联系人
        self.db.contacts.create(**sample_contact_data)
        
        # 按姓名搜索
        results = self.db.contacts.search("测试")
        assert len(results) >= 1
    
    def test_recommendation_crud(self, sample_recommendation_data):
        """测试推荐库CRUD操作"""
        # Create
        rec_id = self.db.recommendations.create(**sample_recommendation_data)
        assert rec_id is not None
        
        # Read
        rec = self.db.recommendations.get_by_id(rec_id)
        assert rec.keyword == sample_recommendation_data["keyword"]
        
        # Update
        self.db.recommendations.update(rec_id, keyword="新关键词")
        updated = self.db.recommendations.get_by_id(rec_id)
        assert updated.keyword == "新关键词"
        
        # Delete
        self.db.recommendations.delete(rec_id)
        deleted = self.db.recommendations.get_by_id(rec_id)
        assert deleted is None
    
    def test_recommendation_match(self, sample_recommendation_data):
        """测试推荐匹配"""
        # 创建推荐
        self.db.recommendations.create(**sample_recommendation_data)
        
        # 匹配关键词
        matches = self.db.recommendations.match("数据分析")
        assert len(matches) >= 1
    
    def test_transaction(self, sample_task_data):
        """测试事务处理"""
        # 开始事务
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("BEGIN TRANSACTION")
            
            # 创建任务
            task_id = self.db.tasks.create(**sample_task_data)
            
            # 人为制造错误
            raise ValueError("Test error")
            
            cursor.execute("COMMIT")
        except ValueError:
            cursor.execute("ROLLBACK")
        
        # 验证回滚
        task = self.db.tasks.get_by_id(task_id)
        assert task is None
    
    def test_concurrent_access(self, sample_task_data):
        """测试并发访问"""
        errors = []
        
        def worker():
            try:
                db = DatabaseManager(self.db_path)
                task_id = db.tasks.create(**sample_task_data)
                task = db.tasks.get_by_id(task_id)
                assert task is not None
                db.close()
            except Exception as e:
                errors.append(str(e))
        
        # 创建多个线程
        threads = []
        for _ in range(5):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        # 验证没有错误
        assert len(errors) == 0
    
    def test_performance_bulk_insert(self, sample_task_data):
        """测试批量插入性能"""
        import time
        
        start_time = time.time()
        
        # 批量插入
        for i in range(100):
            data = sample_task_data.copy()
            data["title"] = f"批量任务{i}"
            self.db.tasks.create(**data)
        
        duration = time.time() - start_time
        
        # 验证性能 - 100条记录应在合理时间内完成
        assert duration < 5.0  # 5秒内完成
    
    def test_task_relationships(self, sample_task_data):
        """测试任务关联"""
        # 创建任务
        task_id = self.db.tasks.create(**sample_task_data)
        
        # 添加跟踪记录
        track_data = {
            "task_id": task_id,
            "content": "测试跟踪记录",
            "operator": "测试员",
        }
        self.db.tracks.create(**track_data)
        
        # 添加提醒
        reminder_data = {
            "task_id": task_id,
            "remind_time": "2026-06-20 10:00:00",
            "message": "测试提醒",
        }
        self.db.reminders.create(**reminder_data)
        
        # 验证关联
        tracks = self.db.tracks.filter(task_id=task_id)
        assert len(tracks) >= 1
        
        reminders = self.db.reminders.filter(task_id=task_id)
        assert len(reminders) >= 1


class TestDatabasePerformance:
    """数据库性能测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self, temp_db):
        self.db_path = temp_db
        self.db = DatabaseManager(self.db_path)
        yield
        self.db.close()
    
    @pytest.mark.slow
    def test_large_data_query(self, sample_task_data):
        """测试大数据量查询"""
        # 插入1000条记录
        for i in range(1000):
            data = sample_task_data.copy()
            data["title"] = f"性能测试任务{i}"
            self.db.tasks.create(**data)
        
        # 测试查询性能
        import time
        start = time.time()
        tasks = self.db.tasks.list_all()
        duration = time.time() - start
        
        assert len(tasks) >= 1000
        assert duration < 2.0  # 查询应在2秒内完成
    
    @pytest.mark.slow
    def test_index_performance(self):
        """测试索引性能"""
        import time
        
        # 创建测试数据
        for i in range(100):
            self.db.tasks.create(
                title=f"索引测试{i}",
                status="pending",
                importance="high"
            )
        
        # 测试带索引的查询
        start = time.time()
        results = self.db.tasks.filter(status="pending")
        duration = time.time() - start
        
        assert duration < 0.5  # 索引查询应很快


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
