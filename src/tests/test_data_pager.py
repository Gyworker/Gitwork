# -*- coding: utf-8 -*-
"""
数据分页模块单元测试

版本：V4.1
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import time

from src.core.data_pager import (
    PageConfig,
    PageInfo,
    PagedResult,
    DataLoader,
    TaskDataLoader,
    LazyIterator,
    BatchProcessor,
    VirtualScrollState,
    create_paged_result,
    normalize_page,
    calculate_offset,
)


class TestPageConfig:
    """测试分页配置"""
    
    def test_default_values(self):
        """测试默认值"""
        config = PageConfig()
        assert config.page_size == 50
        assert config.max_page_size == 200
        assert config.prefetch_pages == 2
        assert config.enable_cache is True
        assert config.cache_size == 100
    
    def test_custom_values(self):
        """测试自定义值"""
        config = PageConfig(
            page_size=100,
            max_page_size=500,
            enable_cache=False
        )
        assert config.page_size == 100
        assert config.max_page_size == 500
        assert config.enable_cache is False


class TestPageInfo:
    """测试分页信息"""
    
    def test_first_page(self):
        """测试首页"""
        info = PageInfo(
            current_page=1,
            page_size=50,
            total_items=100,
            total_pages=2,
            has_next=True,
            has_prev=False
        )
        assert info.is_first is True
        assert info.is_last is False
    
    def test_last_page(self):
        """测试末页"""
        info = PageInfo(
            current_page=2,
            page_size=50,
            total_items=100,
            total_pages=2,
            has_next=False,
            has_prev=True
        )
        assert info.is_first is False
        assert info.is_last is True
    
    def test_middle_page(self):
        """测试中间页"""
        info = PageInfo(
            current_page=2,
            page_size=50,
            total_items=200,
            total_pages=4,
            has_next=True,
            has_prev=True
        )
        assert info.is_first is False
        assert info.is_last is False


class TestPagedResult:
    """测试分页结果"""
    
    def test_with_items(self):
        """测试有数据的结果"""
        page_info = PageInfo(
            current_page=1,
            page_size=50,
            total_items=100,
            total_pages=2,
            has_next=True,
            has_prev=False
        )
        result = PagedResult(
            items=[{'id': 1}, {'id': 2}],
            page_info=page_info,
            fetch_time_ms=10.5
        )
        assert result.is_empty() is False
        assert result.first_or_none() == {'id': 1}
    
    def test_empty_result(self):
        """测试空结果"""
        page_info = PageInfo(
            current_page=1,
            page_size=50,
            total_items=0,
            total_pages=1,
            has_next=False,
            has_prev=False
        )
        result = PagedResult(items=[], page_info=page_info)
        assert result.is_empty() is True
        assert result.first_or_none() is None


class MockDataLoader(DataLoader):
    """模拟数据加载器"""
    
    def __init__(self, data, config=None):
        super().__init__(config)
        self.data = data
        self.load_count = 0
    
    def _load_page(self, page: int) -> list:
        self.load_count += 1
        page_size = self.config.page_size
        start = (page - 1) * page_size
        end = start + page_size
        return self.data[start:end]


class TestDataLoader:
    """测试数据加载器"""
    
    def test_get_page_with_cache(self):
        """测试获取页面（启用缓存）"""
        data = list(range(100))
        loader = MockDataLoader(data, PageConfig(enable_cache=True, cache_size=10))
        
        # 第一次加载
        page1 = loader.get_page(1)
        assert len(page1) == 50
        assert loader.load_count == 1
        
        # 第二次从缓存获取
        page1_again = loader.get_page(1)
        assert loader.load_count == 1  # 没有新的加载
    
    def test_get_page_without_cache(self):
        """测试获取页面（禁用缓存）"""
        data = list(range(100))
        loader = MockDataLoader(data, PageConfig(enable_cache=False))
        
        page1 = loader.get_page(1)
        assert loader.load_count == 1
        
        page1_again = loader.get_page(1)
        assert loader.load_count == 2  # 重新加载
    
    def test_invalidate_cache(self):
        """测试清除缓存"""
        data = list(range(100))
        loader = MockDataLoader(data, PageConfig(enable_cache=True))
        
        # 第一次加载
        loader.get_page(1)
        assert loader.load_count == 1
        
        # 清除缓存
        loader.invalidate_cache()
        
        # 重新加载
        loader.get_page(1)
        assert loader.load_count == 2
    
    def test_invalidate_specific_page(self):
        """测试清除指定页面缓存"""
        data = list(range(200))
        loader = MockDataLoader(data, PageConfig(enable_cache=True))
        
        loader.get_page(1)
        loader.get_page(2)
        assert loader.load_count == 2
        
        # 清除页面1的缓存
        loader.invalidate_cache(1)
        
        # 页面1重新加载，页面2从缓存
        loader.get_page(1)
        loader.get_page(2)
        assert loader.load_count == 3


class TestTaskDataLoader:
    """测试任务数据加载器"""
    
    def test_get_paged_with_mock_db(self):
        """测试分页查询"""
        mock_db = Mock()
        mock_db.count.return_value = 100
        mock_db.fetchall.return_value = [{'id': 1}, {'id': 2}]
        
        loader = TaskDataLoader(mock_db, PageConfig(page_size=10))
        result = loader.get_paged(page=1)
        
        assert result.page_info.current_page == 1
        assert result.page_info.total_items == 100
        assert result.page_info.total_pages == 10
        assert result.page_info.has_next is True
        assert result.page_info.has_prev is False
    
    def test_page_boundary(self):
        """测试页码边界"""
        mock_db = Mock()
        mock_db.count.return_value = 25
        
        loader = TaskDataLoader(mock_db, PageConfig(page_size=10))
        
        # 请求超出范围的页面
        result = loader.get_paged(page=10)
        assert result.page_info.current_page == 3  # 应该限制在最后一页
    
    def test_search(self):
        """测试搜索"""
        mock_db = Mock()
        mock_db.count.return_value = 5
        mock_db.fetchall.return_value = [{'keyword': 'test'}]
        
        loader = TaskDataLoader(mock_db)
        result = loader.search("test", page=1)
        
        assert result.is_empty() is False


class TestLazyIterator:
    """测试懒加载迭代器"""
    
    def test_iteration(self):
        """测试迭代"""
        data = list(range(100))
        loader = MockDataLoader(data, PageConfig(page_size=20))
        iterator = LazyIterator(loader)
        
        values = []
        for item in iterator:
            values.append(item)
            if len(values) >= 50:  # 只取前50个
                break
        
        assert len(values) == 50
        assert values[0] == 0
        assert values[49] == 49
    
    def test_reset(self):
        """测试重置"""
        data = list(range(100))
        loader = MockDataLoader(data, PageConfig(page_size=20))
        iterator = LazyIterator(loader)
        
        # 迭代部分数据
        values1 = []
        for i, item in enumerate(iterator):
            values1.append(item)
            if i >= 9:
                break
        
        # 重置
        iterator.reset()
        
        # 重新迭代
        values2 = []
        for i, item in enumerate(iterator):
            values2.append(item)
            if i >= 9:
                break
        
        assert values1 == values2


class TestBatchProcessor:
    """测试批量处理器"""
    
    def test_sequential_processing(self):
        """测试顺序处理"""
        def process_func(x):
            return x * 2
        
        processor = BatchProcessor(batch_size=10, max_workers=1)
        results = processor.process([1, 2, 3, 4, 5], process_func)
        
        assert results == [2, 4, 6, 8, 10]
    
    def test_parallel_processing(self):
        """测试并行处理"""
        def process_func(x):
            time.sleep(0.01)  # 模拟耗时操作
            return x * 2
        
        start = time.time()
        processor = BatchProcessor(batch_size=5, max_workers=4)
        results = processor.process([1, 2, 3, 4, 5], process_func)
        elapsed = time.time() - start
        
        assert results == [2, 4, 6, 8, 10]
        # 并行处理应该比顺序快
        assert elapsed < 0.1
    
    def test_progress_callback(self):
        """测试进度回调"""
        progress_calls = []
        
        def callback(current, total):
            progress_calls.append((current, total))
        
        processor = BatchProcessor(batch_size=2, progress_callback=callback)
        results = processor.process([1, 2, 3, 4, 5], lambda x: x)
        
        assert len(progress_calls) > 0
        assert progress_calls[-1] == (5, 5)


class TestVirtualScrollState:
    """测试虚拟滚动状态"""
    
    def test_initial_state(self):
        """测试初始状态"""
        state = VirtualScrollState()
        assert state.visible_start == 0
        assert state.visible_end == 50
    
    def test_update_scroll(self):
        """测试更新滚动"""
        state = VirtualScrollState(total_height=1000, item_height=30)
        state.update_scroll(scroll_top=300, viewport_height=300)
        
        assert state.visible_start == 5  # 300/30 - 5
        assert state.visible_end == 15   # 300/30 + 10


class TestHelperFunctions:
    """测试辅助函数"""
    
    def test_create_paged_result(self):
        """测试创建分页结果"""
        result = create_paged_result(
            items=[{'id': 1}],
            page=2,
            page_size=10,
            total=50
        )
        
        assert result.page_info.current_page == 2
        assert result.page_info.total_pages == 5
        assert result.page_info.has_next is True
        assert result.page_info.has_prev is True
    
    def test_normalize_page(self):
        """测试规范化页码"""
        assert normalize_page(None, 10, 100) == 1
        assert normalize_page(0, 10, 100) == 1
        assert normalize_page(-1, 10, 100) == 1
        assert normalize_page(5, 10, 100) == 5
        assert normalize_page(20, 10, 100) == 10  # 超出范围
    
    def test_calculate_offset(self):
        """测试计算偏移"""
        assert calculate_offset(1, 50) == 0
        assert calculate_offset(2, 50) == 50
        assert calculate_offset(3, 50) == 100
        assert calculate_offset(1, 100) == 0
        assert calculate_offset(2, 100) == 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
