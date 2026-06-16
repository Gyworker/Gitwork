"""
性能优化模块
提供数据库优化、缓存管理、性能监控等功能
"""

import time
import functools
import threading
from typing import Callable, Any, Optional, Dict, List
from collections import OrderedDict
from dataclasses import dataclass
import tracemalloc
import psutil
import os

from src.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    name: str
    duration: float
    memory_delta: int
    timestamp: float
    
    @property
    def memory_mb(self) -> float:
        return self.memory_delta / 1024 / 1024


class PerformanceMonitor:
    """性能监控器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._metrics: List[PerformanceMetrics] = []
        self._current = None
        self._start_memory = 0
    
    def start(self, name: str = "operation"):
        """开始监控"""
        self._current = name
        self._start_memory = tracemalloc.get_traced_memory()[0]
        self._start_time = time.perf_counter()
    
    def stop(self) -> PerformanceMetrics:
        """停止监控"""
        if self._current is None:
            raise ValueError("Performance monitor not started")
        
        end_time = time.perf_counter()
        end_memory = tracemalloc.get_traced_memory()[0]
        
        metrics = PerformanceMetrics(
            name=self._current,
            duration=end_time - self._start_time,
            memory_delta=end_memory - self._start_memory,
            timestamp=time.time(),
        )
        
        self._metrics.append(metrics)
        self._current = None
        
        return metrics
    
    def get_metrics(self, name: Optional[str] = None) -> List[PerformanceMetrics]:
        """获取性能指标"""
        if name:
            return [m for m in self._metrics if m.name == name]
        return self._metrics
    
    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self._metrics:
            return {}
        
        by_name: Dict[str, List[PerformanceMetrics]] = {}
        for m in self._metrics:
            if m.name not in by_name:
                by_name[m.name] = []
            by_name[m.name].append(m)
        
        summary = {}
        for name, metrics in by_name.items():
            durations = [m.duration for m in metrics]
            memories = [m.memory_delta for m in metrics]
            
            summary[name] = {
                "count": len(metrics),
                "avg_duration": sum(durations) / len(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "avg_memory_mb": sum(memories) / len(memories) / 1024 / 1024,
                "total_memory_mb": sum(memories) / 1024 / 1024,
            }
        
        return summary
    
    def clear(self):
        """清除指标"""
        self._metrics.clear()


def monitor(name: Optional[str] = None) -> Callable:
    """
    性能监控装饰器
    
    Args:
        name: 监控名称，默认使用函数名
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            monitor_instance = PerformanceMonitor()
            monitor_name = name or f"{func.__module__}.{func.__qualname__}"
            
            monitor_instance.start(monitor_name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                metrics = monitor_instance.stop()
                logger.debug(
                    f"Performance: {metrics.name} - "
                    f"Duration: {metrics.duration*1000:.2f}ms, "
                    f"Memory: {metrics.memory_mb:.2f}MB"
                )
        
        return wrapper
    return decorator


class LRUCache:
    """LRU缓存"""
    
    def __init__(self, max_size: int = 100):
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            if key in self._cache:
                # 移到末尾（最新）
                self._cache.move_to_end(key)
                return self._cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """设置缓存"""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self._max_size:
                    # 移除最旧的
                    self._cache.popitem(last=False)
            self._cache[key] = value
    
    def clear(self):
        """清除缓存"""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        with self._lock:
            return len(self._cache)


class DatabaseOptimizer:
    """数据库优化器"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    @monitor("database.optimize")
    def analyze(self):
        """分析数据库"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # 分析任务表
        cursor.execute("ANALYZE tasks")
        
        # 分析联系人表
        cursor.execute("ANALYZE contacts")
        
        # 分析推荐库表
        cursor.execute("ANALYZE recommendations")
        
        conn.commit()
        logger.info("Database analysis completed")
    
    @monitor("database.vacuum")
    def vacuum(self):
        """清理数据库"""
        conn = self.db.get_connection()
        conn.execute("VACUUM")
        logger.info("Database vacuum completed")
    
    def get_table_info(self) -> List[Dict[str, Any]]:
        """获取表信息"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        tables = []
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        
        for (table_name,) in cursor.fetchall():
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = len(cursor.fetchall())
            
            tables.append({
                "name": table_name,
                "rows": count,
                "columns": columns,
            })
        
        return tables
    
    def get_index_info(self) -> List[Dict[str, Any]]:
        """获取索引信息"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, tbl_name, sql 
            FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
        """)
        
        indexes = []
        for name, tbl_name, sql in cursor.fetchall():
            indexes.append({
                "name": name,
                "table": tbl_name,
                "sql": sql,
            })
        
        return indexes


class SystemMonitor:
    """系统资源监控"""
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """获取内存使用情况"""
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        
        return {
            "rss_mb": mem_info.rss / 1024 / 1024,
            "vms_mb": mem_info.vms / 1024 / 1024,
            "percent": process.memory_percent(),
        }
    
    @staticmethod
    def get_cpu_usage() -> float:
        """获取CPU使用率"""
        process = psutil.Process(os.getpid())
        return process.cpu_percent(interval=0.1)
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """获取系统信息"""
        return {
            "cpu_count": psutil.cpu_count(),
            "total_memory_mb": psutil.virtual_memory().total / 1024 / 1024,
            "available_memory_mb": psutil.virtual_memory().available / 1024 / 1024,
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
        }


class QueryOptimizer:
    """查询优化器"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    @monitor("query.optimize")
    def optimize_query(self, query: str, params: tuple = ()) -> List:
        """
        优化查询
        
        Args:
            query: SQL查询
            params: 查询参数
            
        Returns:
            查询结果
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # 使用 EXPLAIN QUERY PLAN 分析查询
        cursor.execute(f"EXPLAIN QUERY PLAN {query}", params)
        plan = cursor.fetchall()
        
        # 检查是否需要优化
        for row in plan:
            if b"SCAN" in str(row).encode() or b"FULL" in str(row).encode():
                logger.warning(f"Query may need optimization: {query}")
        
        # 执行查询
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def get_slow_queries(self, threshold_ms: float = 100) -> List[Dict]:
        """获取慢查询"""
        # SQLite没有内置的慢查询日志，这里提供建议
        suggestions = [
            {
                "suggestion": "Use indexes for frequently queried columns",
                "examples": [
                    "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
                    "CREATE INDEX IF NOT EXISTS idx_tasks_importance ON tasks(importance)",
                ]
            },
            {
                "suggestion": "Use LIMIT for large result sets",
                "examples": ["SELECT * FROM tasks LIMIT 100"]
            },
            {
                "suggestion": "Avoid SELECT *", 
                "examples": ["SELECT id, title, status FROM tasks"]
            },
        ]
        return suggestions


# 全局缓存实例
_global_cache = LRUCache(max_size=1000)


def cached(key_prefix: str = "", max_age: Optional[int] = None):
    """
    缓存装饰器
    
    Args:
        key_prefix: 缓存键前缀
        max_age: 缓存最大生存时间（秒）
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            cached_value = _global_cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            _global_cache.set(cache_key, result)
            
            return result
        
        return wrapper
    return decorator


# 性能分析上下文管理器
class PerformanceContext:
    """性能分析上下文"""
    
    def __init__(self, name: str):
        self.name = name
        self.metrics = None
    
    def __enter__(self):
        self.metrics = PerformanceMonitor()
        self.metrics.start(self.name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.metrics = self.metrics.stop()
        logger.info(
            f"Operation '{self.metrics.name}' completed in "
            f"{self.metrics.duration*1000:.2f}ms"
        )
