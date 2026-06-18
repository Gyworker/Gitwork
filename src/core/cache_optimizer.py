# -*- coding: utf-8 -*-
"""
性能优化模块 - 增强版
Performance Optimization Module - Enhanced

提供缓存策略优化、性能监控等功能
"""

import time
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import json

from src.utils.logger import get_logger

logger = get_logger(__name__)


# ==================== 增强缓存策略 ====================

@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    max_age: Optional[int] = None  # 秒
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.max_age is None:
            return False
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.max_age
    
    def touch(self):
        """更新访问时间"""
        self.last_accessed = datetime.now()
        self.access_count += 1


class CachePolicy(Enum):
    """缓存策略"""
    LRU = "lru"           # 最近最少使用
    LFU = "lfu"           # 最不经常使用
    FIFO = "fifo"         # 先进先出
    TTL = "ttl"           # 基于时间过期
    WEIGHTED = "weighted"  # 加权策略


class EnhancedLRUCache:
    """
    增强型LRU缓存
    支持多种缓存策略和过期机制
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        policy: CachePolicy = CachePolicy.LRU,
        default_ttl: int = 3600,
        enable_stats: bool = True
    ):
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存条目数
            policy: 缓存策略
            default_ttl: 默认过期时间（秒）
            enable_stats: 启用统计
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._policy = policy
        self._default_ttl = default_ttl
        self._enable_stats = enable_stats
        
        self._lock = threading.RLock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0,
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存
        
        Args:
            key: 缓存键
            default: 默认值
            
        Returns:
            缓存值或默认值
        """
        with self._lock:
            if key not in self._cache:
                self._record_miss()
                return default
            
            entry = self._cache[key]
            
            # 检查过期
            if entry.is_expired():
                self._remove(key)
                self._record_expiration()
                return default
            
            # 更新访问
            entry.touch()
            self._cache.move_to_end(key)
            
            self._record_hit()
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        with self._lock:
            # 如果存在，先移除
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                # 检查容量
                if len(self._cache) >= self._max_size:
                    self._evict()
            
            # 创建新条目
            now = datetime.now()
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                last_accessed=now,
                max_age=ttl or self._default_ttl
            )
            
            self._cache[key] = entry
            logger.debug(f"缓存设置: {key}")
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        with self._lock:
            if key in self._cache:
                self._remove(key)
                return True
            return False
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            logger.info("缓存已清空")
    
    def _remove(self, key: str):
        """移除缓存条目"""
        if key in self._cache:
            del self._cache[key]
    
    def _evict(self) -> Optional[str]:
        """根据策略淘汰条目"""
        if not self._cache:
            return None
        
        evicted_key = None
        
        if self._policy == CachePolicy.LRU:
            # 淘汰最旧的
            evicted_key, _ = self._cache.popitem(last=False)
        elif self._policy == CachePolicy.LFU:
            # 淘汰访问次数最少的
            evicted_key = min(
                self._cache.keys(),
                key=lambda k: self._cache[k].access_count
            )
            del self._cache[evicted_key]
        elif self._policy == CachePolicy.FIFO:
            # 淘汰最早的
            evicted_key, _ = self._cache.popitem(last=False)
        elif self._policy == CachePolicy.TTL:
            # 淘汰过期或最旧的
            for key, entry in self._cache.items():
                if entry.is_expired():
                    del self._cache[key]
                    evicted_key = key
                    break
            else:
                evicted_key, _ = self._cache.popitem(last=False)
        
        if evicted_key:
            self._stats["evictions"] += 1
            logger.debug(f"缓存淘汰: {evicted_key}")
        
        return evicted_key
    
    def _record_hit(self):
        """记录命中"""
        if self._enable_stats:
            self._stats["hits"] += 1
    
    def _record_miss(self):
        """记录未命中"""
        if self._enable_stats:
            self._stats["misses"] += 1
    
    def _record_expiration(self):
        """记录过期"""
        if self._enable_stats:
            self._stats["expirations"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = (
                self._stats["hits"] / total * 100 if total > 0 else 0
            )
            
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "policy": self._policy.value,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate": round(hit_rate, 2),
                "evictions": self._stats["evictions"],
                "expirations": self._stats["expirations"],
            }
    
    def cleanup_expired(self) -> int:
        """
        清理过期条目
        
        Returns:
            清理的条目数
        """
        with self._lock:
            count = 0
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
                count += 1
            
            if count > 0:
                logger.info(f"清理过期缓存: {count}条")
            
            return count


# ==================== 统计缓存优化 ====================

class StatisticsCache:
    """
    统计分析缓存
    针对统计数据优化的高性能缓存
    """
    
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
        
        # 按数据类型使用不同缓存
        self._counts_cache = EnhancedLRUCache(
            max_size=100,
            policy=CachePolicy.LRU,
            default_ttl=300  # 5分钟
        )
        self._distribution_cache = EnhancedLRUCache(
            max_size=50,
            policy=CachePolicy.TTL,
            default_ttl=600  # 10分钟
        )
        self._trend_cache = EnhancedLRUCache(
            max_size=30,
            policy=CachePolicy.TTL,
            default_ttl=900  # 15分钟
        )
        
        # 缓存键前缀
        self._prefix = {
            "counts": "stat:counts:",
            "distribution": "stat:dist:",
            "trend": "stat:trend:",
        }
    
    def _make_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """生成缓存键"""
        param_str = json.dumps(params, sort_keys=True, default=str)
        return f"{prefix}{hashlib.md5(param_str.encode()).hexdigest()}"
    
    def get_counts(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """获取计数缓存"""
        key = self._make_key(
            self._prefix["counts"],
            {"table": table, "filters": filters or {}}
        )
        return self._counts_cache.get(key)
    
    def set_counts(
        self,
        table: str,
        count: int,
        filters: Optional[Dict[str, Any]] = None
    ):
        """设置计数缓存"""
        key = self._make_key(
            self._prefix["counts"],
            {"table": table, "filters": filters or {}}
        )
        self._counts_cache.set(key, count, ttl=300)
    
    def get_distribution(
        self,
        table: str,
        group_by: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, int]]:
        """获取分布缓存"""
        key = self._make_key(
            self._prefix["distribution"],
            {"table": table, "group_by": group_by, "filters": filters or {}}
        )
        return self._distribution_cache.get(key)
    
    def set_distribution(
        self,
        table: str,
        group_by: str,
        distribution: Dict[str, int],
        filters: Optional[Dict[str, Any]] = None
    ):
        """设置分布缓存"""
        key = self._make_key(
            self._prefix["distribution"],
            {"table": table, "group_by": group_by, "filters": filters or {}}
        )
        self._distribution_cache.set(key, distribution, ttl=600)
    
    def get_trend(
        self,
        table: str,
        date_field: str,
        interval: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """获取趋势缓存"""
        key = self._make_key(
            self._prefix["trend"],
            {"table": table, "date_field": date_field, 
             "interval": interval, "filters": filters or {}}
        )
        return self._trend_cache.get(key)
    
    def set_trend(
        self,
        table: str,
        date_field: str,
        interval: str,
        trend: List[Dict[str, Any]],
        filters: Optional[Dict[str, Any]] = None
    ):
        """设置趋势缓存"""
        key = self._make_key(
            self._prefix["trend"],
            {"table": table, "date_field": date_field,
             "interval": interval, "filters": filters or {}}
        )
        self._trend_cache.set(key, trend, ttl=900)
    
    def invalidate(self, table: str = None):
        """使缓存失效"""
        if table:
            # 只清理特定表的缓存
            self._counts_cache.clear()
            self._distribution_cache.clear()
            self._trend_cache.clear()
        else:
            # 清理所有缓存
            self._counts_cache.clear()
            self._distribution_cache.clear()
            self._trend_cache.clear()
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """获取所有缓存统计"""
        return {
            "counts": self._counts_cache.get_stats(),
            "distribution": self._distribution_cache.get_stats(),
            "trend": self._trend_cache.get_stats(),
        }


# ==================== 批量操作优化 ====================

class BatchOperation:
    """批量操作优化"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self._lock = threading.Lock()
        self._batch_buffer: Dict[str, List[Tuple]] = {}
        self._batch_size = 100
        self._flush_interval = 5  # 秒
    
    def set_batch_size(self, size: int):
        """设置批量大小"""
        self._batch_size = size
    
    def add_to_batch(
        self,
        table: str,
        operation: str,
        data: Tuple
    ):
        """
        添加到批量操作
        
        Args:
            table: 表名
            operation: 操作类型 (insert, update, delete)
            data: 数据元组
        """
        with self._lock:
            key = f"{table}:{operation}"
            if key not in self._batch_buffer:
                self._batch_buffer[key] = []
            
            self._batch_buffer[key].append(data)
            
            # 检查是否需要自动刷新
            if len(self._batch_buffer[key]) >= self._batch_size:
                self._flush_key(key)
    
    def _flush_key(self, key: str):
        """刷新指定键的批量操作"""
        if key not in self._batch_buffer or not self._batch_buffer[key]:
            return
        
        table, operation = key.split(":")
        data_list = self._batch_buffer[key]
        
        try:
            if operation == "insert":
                columns = data_list[0][0]
                values = data_list[0][1]
                placeholders = ", ".join(["?" for _ in values])
                sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
                self.db.executemany(sql, [d[1] for d in data_list], commit=True)
            
            elif operation == "update":
                sql = data_list[0][0]
                params_list = [d[1] for d in data_list]
                self.db.executemany(sql, params_list, commit=True)
            
            elif operation == "delete":
                sql = data_list[0][0]
                params_list = [d[1] for d in data_list]
                self.db.executemany(sql, params_list, commit=True)
            
            logger.info(f"批量{operation}完成: {table}, {len(data_list)}条")
            
        except Exception as e:
            logger.error(f"批量操作失败: {e}")
            raise
        
        finally:
            self._batch_buffer[key] = []
    
    def flush_all(self):
        """刷新所有批量操作"""
        with self._lock:
            keys = list(self._batch_buffer.keys())
            for key in keys:
                self._flush_key(key)
    
    def get_pending_count(self) -> int:
        """获取待处理数量"""
        with self._lock:
            return sum(len(v) for v in self._batch_buffer.values())


# ==================== 性能优化装饰器 ====================

def smart_cache(
    prefix: str = "",
    ttl: int = 300,
    cache_instance: EnhancedLRUCache = None
):
    """
    智能缓存装饰器
    
    Args:
        prefix: 缓存键前缀
        ttl: 过期时间（秒）
        cache_instance: 缓存实例
    """
    _cache = cache_instance or EnhancedLRUCache(max_size=1000)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            result = _cache.get(cache_key)
            if result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            _cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        # 添加缓存实例引用
        wrapper._cache = _cache
        return wrapper
    return decorator


def rate_limit(max_calls: int, period: float):
    """
    速率限制装饰器
    
    Args:
        max_calls: 最大调用次数
        period: 时间周期（秒）
    """
    _calls: Dict[str, List[float]] = {}
    _lock = threading.Lock()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__module__}.{func.__qualname__}"
            
            with _lock:
                now = time.time()
                
                if key not in _calls:
                    _calls[key] = []
                
                # 清理过期的调用记录
                _calls[key] = [
                    t for t in _calls[key]
                    if now - t < period
                ]
                
                # 检查是否超过限制
                if len(_calls[key]) >= max_calls:
                    raise RuntimeError(
                        f"速率限制: 超过{max_calls}次/{period}秒"
                    )
                
                _calls[key].append(now)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# 全局缓存实例
_statistics_cache = StatisticsCache()
_global_cache = EnhancedLRUCache(max_size=1000)


def get_statistics_cache() -> StatisticsCache:
    """获取统计缓存"""
    return _statistics_cache


def get_global_cache() -> EnhancedLRUCache:
    """获取全局缓存"""
    return _global_cache


from enum import Enum
