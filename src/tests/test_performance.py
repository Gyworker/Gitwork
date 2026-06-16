"""
性能测试
测试系统各模块的性能指标
"""

import pytest
import time
import tracemalloc
import psutil
import os
import gc
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


class TestPerformance:
    """性能测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self, temp_db):
        """设置测试环境"""
        self.db_path = temp_db
        yield
    
    @pytest.mark.performance
    def test_database_insert_performance(self):
        """测试数据库插入性能"""
        from src.database.connection import DatabaseManager
        
        db = DatabaseManager(self.db_path)
        
        tracemalloc.start()
        start_time = time.perf_counter()
        
        # 批量插入测试
        for i in range(100):
            db.tasks.create(
                title=f"性能测试任务{i}",
                description=f"这是第{i}个测试任务",
                status="pending",
                importance="medium",
            )
        
        duration = time.perf_counter() - start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # 验证性能指标
        assert duration < 5.0  # 100条记录应在5秒内完成
        print(f"\n插入100条记录耗时: {duration:.3f}秒")
        print(f"峰值内存: {peak / 1024 / 1024:.2f}MB")
    
    @pytest.mark.performance
    def test_database_query_performance(self):
        """测试数据库查询性能"""
        from src.database.connection import DatabaseManager
        
        db = DatabaseManager(self.db_path)
        
        # 创建测试数据
        for i in range(100):
            db.tasks.create(
                title=f"查询测试任务{i}",
                status=["pending", "in_progress", "completed"][i % 3],
                importance=["low", "medium", "high"][i % 3],
            )
        
        # 测试查询性能
        tracemalloc.start()
        start_time = time.perf_counter()
        
        for _ in range(50):
            tasks = db.tasks.list_all()
            db.tasks.filter(status="pending")
        
        duration = time.perf_counter() - start_time
        tracemalloc.stop()
        
        assert duration < 2.0  # 50次查询应在2秒内完成
        print(f"\n50次查询耗时: {duration:.3f}秒")
    
    @pytest.mark.performance
    def test_large_data_handling(self):
        """测试大数据量处理"""
        from src.database.connection import DatabaseManager
        
        db = DatabaseManager(self.db_path)
        
        # 创建1000条记录
        tracemalloc.start()
        start_time = time.perf_counter()
        
        for i in range(1000):
            db.tasks.create(
                title=f"大数据测试任务{i}",
                description="测试描述" * 10,
                status="pending",
                importance="high",
            )
        
        create_duration = time.perf_counter() - start_time
        
        # 测试大数据查询
        start_time = time.perf_counter()
        tasks = db.tasks.list_all()
        query_duration = time.perf_counter() - start_time
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        assert len(tasks) >= 1000
        assert create_duration < 30  # 创建1000条记录应在30秒内
        assert query_duration < 2  # 查询应在2秒内
        assert peak < 100 * 1024 * 1024  # 内存峰值应小于100MB
        
        print(f"\n创建1000条记录: {create_duration:.2f}秒")
        print(f"查询1000条记录: {query_duration:.3f}秒")
        print(f"峰值内存: {peak / 1024 / 1024:.2f}MB")
    
    @pytest.mark.performance
    def test_concurrent_access(self):
        """测试并发访问性能"""
        from src.database.connection import DatabaseManager
        
        def worker(worker_id: int):
            db = DatabaseManager(self.db_path)
            results = []
            for i in range(10):
                task_id = db.tasks.create(
                    title=f"并发测试-{worker_id}-{i}",
                    status="pending",
                )
                task = db.tasks.get_by_id(task_id)
                results.append(task is not None)
            db.close()
            return all(results)
        
        # 并发执行
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker, i) for i in range(5)]
            results = [f.result() for f in futures]
        
        duration = time.perf_counter() - start_time
        
        assert all(results)
        assert duration < 15  # 并发处理应在15秒内完成
        print(f"\n5个线程并发执行(各10次操作): {duration:.2f}秒")
    
    @pytest.mark.performance
    def test_memory_usage(self):
        """测试内存使用"""
        from src.database.connection import DatabaseManager
        
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024
        
        # 创建大量数据
        db = DatabaseManager(self.db_path)
        for i in range(500):
            db.tasks.create(
                title=f"内存测试任务{i}",
                description="测试描述" * 50,
                status="pending",
            )
        
        # 触发垃圾回收
        gc.collect()
        
        mem_after = process.memory_info().rss / 1024 / 1024
        mem_delta = mem_after - mem_before
        
        assert mem_delta < 100  # 内存增长应小于100MB
        print(f"\n内存使用: {mem_before:.1f}MB -> {mem_after:.1f}MB (+{mem_delta:.1f}MB)")
    
    @pytest.mark.slow
    @pytest.mark.performance
    def test_sustained_load(self):
        """测试持续负载"""
        from src.database.connection import DatabaseManager
        
        db = DatabaseManager(self.db_path)
        
        durations = []
        
        # 模拟持续负载
        for round_num in range(10):
            start_time = time.perf_counter()
            
            for i in range(50):
                db.tasks.create(
                    title=f"负载测试-{round_num}-{i}",
                    status="pending",
                )
            
            duration = time.perf_counter() - start_time
            durations.append(duration)
            
            # 清理部分数据
            tasks = db.tasks.list_all(page_size=25)
            for task in tasks[:10]:
                db.tasks.delete(task.id)
        
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        
        assert max_duration < 3  # 最大单轮耗时应小于3秒
        print(f"\n持续负载测试(10轮):")
        print(f"  平均耗时: {avg_duration:.3f}秒")
        print(f"  最大耗时: {max_duration:.3f}秒")
    
    @pytest.mark.performance
    def test_cache_performance(self):
        """测试缓存性能"""
        from src.core.performance import LRUCache
        
        cache = LRUCache(max_size=100)
        
        # 测试缓存写入
        start_time = time.perf_counter()
        for i in range(1000):
            cache.set(f"key_{i}", f"value_{i}")
        write_duration = time.perf_counter() - start_time
        
        # 测试缓存读取
        start_time = time.perf_counter()
        for i in range(1000):
            cache.get(f"key_{i}")
        read_duration = time.perf_counter() - start_time
        
        assert write_duration < 0.1
        assert read_duration < 0.1
        print(f"\n缓存性能:")
        print(f"  1000次写入: {write_duration*1000:.2f}ms")
        print(f"  1000次读取: {read_duration*1000:.2f}ms")


class TestSystemPerformance:
    """系统性能测试"""
    
    @pytest.mark.performance
    def test_startup_time(self):
        """测试启动时间"""
        pytest.skip("需要单独测试启动时间")
    
    @pytest.mark.performance
    def test_response_time(self):
        """测试响应时间"""
        from src.database.connection import DatabaseManager
        import tempfile
        
        # 创建临时数据库
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        
        try:
            db = DatabaseManager(path)
            
            # 创建测试数据
            for i in range(100):
                db.tasks.create(
                    title=f"响应时间测试{i}",
                    status="pending",
                )
            
            # 测试响应时间
            times = []
            for _ in range(20):
                start = time.perf_counter()
                db.tasks.list_all()
                times.append(time.perf_counter() - start)
            
            avg_time = sum(times) / len(times)
            max_time = max(times)
            
            assert avg_time < 0.1  # 平均响应时间应小于100ms
            print(f"\n响应时间: 平均={avg_time*1000:.1f}ms, 最大={max_time*1000:.1f}ms")
            
            db.close()
        finally:
            if os.path.exists(path):
                os.remove(path)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
