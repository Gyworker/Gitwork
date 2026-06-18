# -*- coding: utf-8 -*-
"""
数据分页和懒加载模块
为大数据量场景提供高效的数据访问接口

版本：V4.1
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Iterator, Generic, TypeVar
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.core.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


# =============================================================================
# 分页配置
# =============================================================================

@dataclass
class PageConfig:
    """分页配置"""
    page_size: int = 50          # 每页大小
    max_page_size: int = 200     # 最大每页大小
    prefetch_pages: int = 2       # 预加载页数
    enable_cache: bool = True     # 启用缓存
    cache_size: int = 100         # 缓存大小


@dataclass
class PageInfo:
    """分页信息"""
    current_page: int = 1
    page_size: int = 50
    total_items: int = 0
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False
    
    @property
    def is_first(self) -> bool:
        return self.current_page == 1
    
    @property
    def is_last(self) -> bool:
        return self.current_page >= self.total_pages


# =============================================================================
# 分页结果
# =============================================================================

@dataclass
class PagedResult(Generic[T]):
    """分页查询结果"""
    items: List[T]
    page_info: PageInfo
    fetch_time_ms: float = 0.0
    
    def is_empty(self) -> bool:
        """判断结果是否为空"""
        return len(self.items) == 0
    
    def first_or_none(self) -> Optional[T]:
        """获取第一个元素"""
        return self.items[0] if self.items else None


# =============================================================================
# 数据加载器基类
# =============================================================================

class DataLoader(Generic[T]):
    """
    数据加载器基类
    支持分页、缓存、懒加载
    """
    
    def __init__(self, config: Optional[PageConfig] = None):
        self.config = config or PageConfig()
        self._cache: Dict[int, List[T]] = {}
        self._cache_order: List[int] = []
        self._lock = threading.Lock()
        self._loaded_count: Dict[int, int] = {}  # page -> item_count
    
    def get_page(self, page: int) -> List[T]:
        """
        获取指定页的数据
        
        Args:
            page: 页码（从1开始）
            
        Returns:
            该页的数据列表
        """
        # 检查缓存
        if self.config.enable_cache:
            cached = self._get_from_cache(page)
            if cached is not None:
                return cached
        
        # 加载数据
        items = self._load_page(page)
        
        # 更新缓存
        if self.config.enable_cache:
            self._add_to_cache(page, items)
        
        return items
    
    def _get_from_cache(self, page: int) -> Optional[List[T]]:
        """从缓存获取"""
        with self._lock:
            return self._cache.get(page)
    
    def _add_to_cache(self, page: int, items: List[T]):
        """添加到缓存"""
        with self._lock:
            # 清理过期缓存
            if len(self._cache) >= self.config.cache_size:
                self._evict_oldest()
            
            self._cache[page] = items
            self._cache_order.append(page)
            self._loaded_count[page] = len(items)
    
    def _evict_oldest(self):
        """清除最旧的缓存"""
        if self._cache_order:
            oldest = self._cache_order.pop(0)
            self._cache.pop(oldest, None)
            self._loaded_count.pop(oldest, None)
    
    def _load_page(self, page: int) -> List[T]:
        """
        加载指定页的数据（子类实现）
        
        Args:
            page: 页码
            
        Returns:
            数据列表
        """
        raise NotImplementedError("子类必须实现_load_page方法")
    
    def invalidate_cache(self, page: Optional[int] = None):
        """清除缓存"""
        with self._lock:
            if page is None:
                self._cache.clear()
                self._cache_order.clear()
                self._loaded_count.clear()
            else:
                self._cache.pop(page, None)
                self._cache_order = [p for p in self._cache_order if p != page]
                self._loaded_count.pop(page, None)


# =============================================================================
# 任务数据加载器
# =============================================================================

class TaskDataLoader(DataLoader[Dict[str, Any]]):
    """
    任务数据加载器
    支持分页加载、搜索筛选
    """
    
    def __init__(self, db_manager, config: Optional[PageConfig] = None):
        """
        初始化任务数据加载器
        
        Args:
            db_manager: 数据库管理器
            config: 分页配置
        """
        super().__init__(config)
        self.db = db_manager
    
    def get_paged(self,
                  page: int = 1,
                  filters: Optional[Dict[str, Any]] = None,
                  sort_by: str = "created_at",
                  sort_order: str = "DESC") -> PagedResult[Dict[str, Any]]:
        """
        获取分页数据
        
        Args:
            page: 页码
            filters: 筛选条件
            sort_by: 排序字段
            sort_order: 排序方向
            
        Returns:
            PagedResult
        """
        import time
        start_time = time.perf_counter()
        
        filters = filters or {}
        
        # 获取总数
        total = self._count_items(filters)
        
        # 计算分页信息
        total_pages = max(1, (total + self.config.page_size - 1) // self.config.page_size)
        page = max(1, min(page, total_pages))
        
        page_info = PageInfo(
            current_page=page,
            page_size=self.config.page_size,
            total_items=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
        # 获取数据
        offset = (page - 1) * self.config.page_size
        items = self._load_items(offset, filters, sort_by, sort_order)
        
        fetch_time = (time.perf_counter() - start_time) * 1000
        
        return PagedResult(
            items=items,
            page_info=page_info,
            fetch_time_ms=fetch_time
        )
    
    def _count_items(self, filters: Dict[str, Any]) -> int:
        """统计符合条件的数量"""
        try:
            # 简化实现，实际应该查询数据库
            return self.db.count("tasks", filters) if hasattr(self.db, 'count') else 0
        except Exception as e:
            logger.error(f"统计数量失败: {e}")
            return 0
    
    def _load_page(self, page: int) -> List[Dict[str, Any]]:
        """加载指定页"""
        offset = (page - 1) * self.config.page_size
        return self._load_items(offset, {}, "created_at", "DESC")
    
    def _load_items(self,
                   offset: int,
                   filters: Dict[str, Any],
                   sort_by: str,
                   sort_order: str) -> List[Dict[str, Any]]:
        """加载数据项"""
        try:
            # 使用数据库的limit/offset查询
            if hasattr(self.db, 'fetchall'):
                # 构建查询
                where = " AND ".join([f"{k} = ?" for k in filters.keys()]) if filters else "1=1"
                sql = f"SELECT * FROM tasks WHERE {where} ORDER BY {sort_by} {sort_order} LIMIT ? OFFSET ?"
                params = list(filters.values()) + [self.config.page_size, offset]
                return self.db.fetchall(sql, tuple(params))
            return []
        except Exception as e:
            logger.error(f"加载数据失败: {e}")
            return []
    
    def search(self,
               keyword: str,
               page: int = 1) -> PagedResult[Dict[str, Any]]:
        """
        搜索任务
        
        Args:
            keyword: 搜索关键词
            page: 页码
            
        Returns:
            搜索结果
        """
        filters = {
            'keyword': keyword
        }
        return self.get_paged(page, filters)


# =============================================================================
# 懒加载迭代器
# =============================================================================

class LazyIterator(Generic[T]):
    """
    懒加载迭代器
    按需加载数据，避免一次性加载全部数据
    """
    
    def __init__(self,
                 data_loader: DataLoader,
                 page_size: int = 50):
        """
        初始化懒加载迭代器
        
        Args:
            data_loader: 数据加载器
            page_size: 每页大小
        """
        self.loader = data_loader
        self.page_size = page_size
        self.current_page = 1
        self.current_index = 0
        self.current_page_items: List[T] = []
        self._exhausted = False
    
    def __iter__(self) -> Iterator[T]:
        return self
    
    def __next__(self) -> T:
        """获取下一个元素"""
        if self._exhausted:
            raise StopIteration
        
        # 如果当前页已加载完，加载下一页
        while self.current_index >= len(self.current_page_items):
            self._load_next_page()
            if self._exhausted:
                raise StopIteration
        
        item = self.current_page_items[self.current_index]
        self.current_index += 1
        return item
    
    def _load_next_page(self):
        """加载下一页"""
        items = self.loader.get_page(self.current_page)
        
        if not items:
            self._exhausted = True
            return
        
        self.current_page_items = items
        self.current_index = 0
        self.current_page += 1
    
    def reset(self):
        """重置迭代器"""
        self.current_page = 1
        self.current_index = 0
        self.current_page_items = []
        self._exhausted = False


# =============================================================================
# 批量处理
# =============================================================================

class BatchProcessor(Generic[T]):
    """
    批量处理器
    支持并发处理和进度回调
    """
    
    def __init__(self,
                 batch_size: int = 100,
                 max_workers: int = 4,
                 progress_callback: Optional[Callable[[int, int], None]] = None):
        """
        初始化批量处理器
        
        Args:
            batch_size: 批处理大小
            max_workers: 最大并发数
            progress_callback: 进度回调 (current, total)
        """
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.progress_callback = progress_callback
    
    def process(self,
               items: List[T],
               process_func: Callable[[T], Any]) -> List[Any]:
        """
        批量处理
        
        Args:
            items: 数据列表
            process_func: 处理函数
            
        Returns:
            处理结果列表
        """
        results = []
        total = len(items)
        
        # 分批处理
        for batch_start in range(0, total, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total)
            batch = items[batch_start:batch_end]
            
            # 并发处理当前批次
            batch_results = self._process_batch(batch, process_func)
            results.extend(batch_results)
            
            # 报告进度
            if self.progress_callback:
                self.progress_callback(len(results), total)
        
        return results
    
    def _process_batch(self,
                      batch: List[T],
                      process_func: Callable[[T], Any]) -> List[Any]:
        """处理单个批次"""
        if self.max_workers <= 1:
            return [process_func(item) for item in batch]
        
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(process_func, item): i for i, item in enumerate(batch)}
            
            # 按顺序收集结果
            result_map = {}
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    result_map[idx] = future.result()
                except Exception as e:
                    logger.error(f"处理失败: {e}")
                    result_map[idx] = None
            
            # 按原始顺序返回
            for i in range(len(batch)):
                results.append(result_map.get(i))
        
        return results


# =============================================================================
# 虚拟滚动支持
# =============================================================================

@dataclass
class VirtualScrollState:
    """虚拟滚动状态"""
    visible_start: int = 0      # 可见起始索引
    visible_end: int = 50        # 可见结束索引
    total_height: int = 0       # 总高度
    item_height: int = 30       # 单项高度
    scroll_top: int = 0          # 滚动位置
    
    def get_visible_range(self) -> tuple:
        """获取可见范围"""
        return (self.visible_start, self.visible_end)
    
    def update_scroll(self, scroll_top: int, viewport_height: int):
        """更新滚动状态"""
        self.scroll_top = scroll_top
        start = max(0, scroll_top // self.item_height - 5)  # 额外缓冲
        end = min(self.total_height, start + viewport_height // self.item_height + 10)
        self.visible_start = start
        self.visible_end = end


# =============================================================================
# 分页辅助函数
# =============================================================================

def create_paged_result(items: List[T],
                        page: int,
                        page_size: int,
                        total: int) -> PagedResult[T]:
    """
    创建分页结果
    
    Args:
        items: 数据列表
        page: 当前页
        page_size: 每页大小
        total: 总数
        
    Returns:
        PagedResult
    """
    total_pages = max(1, (total + page_size - 1) // page_size)
    
    page_info = PageInfo(
        current_page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )
    
    return PagedResult(items=items, page_info=page_info)


def normalize_page(page: Optional[int], 
                   page_size: int, 
                   total: int) -> int:
    """
    规范化页码
    
    Args:
        page: 请求的页码
        page_size: 每页大小
        total: 总数
        
    Returns:
        规范化后的页码
    """
    if page is None or page < 1:
        return 1
    
    total_pages = max(1, (total + page_size - 1) // page_size)
    return min(page, total_pages)


def calculate_offset(page: int, page_size: int) -> int:
    """
    计算偏移量
    
    Args:
        page: 页码
        page_size: 每页大小
        
    Returns:
        偏移量
    """
    return max(0, (page - 1) * page_size)
