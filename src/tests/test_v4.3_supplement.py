# -*- coding: utf-8 -*-
"""
V4.3 单元测试补充
为V4.1新增模块补充测试用例

版本：V4.3
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import os
import tempfile
from datetime import datetime

from src.content.content_parser_service import (
    ParsedContent,
    ContentParserService,
    TextParser,
    MSGParserWrapper,
    ImageParser,
    WeChatParser,
    ProgressParser,
    get_parser_service,
)
from src.content.image_ocr_processor import (
    ImageOCRProcessor,
    OCRResult,
    OCRContactInfo,
    get_ocr_processor,
)
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


# =============================================================================
# ImageParser 测试补充
# =============================================================================

class TestImageParserV43:
    """V4.3 ImageParser测试补充"""

    def setup_method(self):
        """设置"""
        self.parser = ImageParser()

    def test_parser_type(self):
        """测试解析器类型"""
        assert self.parser.parser_type == "image"

    def test_is_available_when_library_missing(self):
        """测试库未安装时可用性"""
        with patch('builtins.__import__') as mock_import:
            mock_import.side_effect = ImportError("No module named 'pytesseract'")
            parser = ImageParser()
            assert parser.is_available() is False

    def test_parse_library_not_available(self):
        """测试OCR库不可用时的错误处理"""
        with patch.object(ImageParser, 'is_available', return_value=False):
            result = self.parser.parse("/path/to/image.png")
            assert result.error == "OCR库未安装"
            assert "pip install pytesseract" in result.error_details

    def test_parse_nonexistent_file(self):
        """测试解析不存在的图片文件"""
        with patch.object(ImageParser, 'is_available', return_value=True):
            result = self.parser.parse("/nonexistent/image.png")
            assert result.error == "图片文件不存在"

    def test_parse_empty_path(self):
        """测试解析空路径"""
        with patch.object(ImageParser, 'is_available', return_value=True):
            result = self.parser.parse("")
            assert result.error == "图片文件不存在"


class TestWeChatParserV43:
    """V4.3 WeChatParser测试补充"""

    def setup_method(self):
        """设置"""
        self.parser = WeChatParser()

    def test_parser_type(self):
        """测试解析器类型"""
        assert self.parser.parser_type == "wechat"

    def test_is_available(self):
        """测试解析器可用性"""
        assert self.parser.is_available() is True

    def test_parse_returns_placeholder(self):
        """测试解析返回占位数据"""
        result = self.parser.parse("测试内容")
        assert result.source_type == "wechat"
        assert result.task_content == "测试内容"
        assert "待实现" in result.error


# =============================================================================
# DataPager 测试补充
# =============================================================================

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
        config = PageConfig(page_size=100, cache_size=200)
        assert config.page_size == 100
        assert config.cache_size == 200


class TestPageInfo:
    """测试分页信息"""

    def test_default_values(self):
        """测试默认值"""
        info = PageInfo()
        assert info.current_page == 1
        assert info.page_size == 50
        assert info.total_items == 0
        assert info.total_pages == 0

    def test_is_first(self):
        """测试首页判断"""
        info = PageInfo(current_page=1)
        assert info.is_first is True

        info = PageInfo(current_page=2)
        assert info.is_first is False

    def test_is_last(self):
        """测试末页判断"""
        info = PageInfo(current_page=1, total_pages=5)
        assert info.is_last is False

        info = PageInfo(current_page=5, total_pages=5)
        assert info.is_last is True


class TestPagedResult:
    """测试分页结果"""

    def test_is_empty_with_items(self):
        """测试有数据时非空"""
        result = PagedResult(items=['a', 'b', 'c'], page_info=PageInfo())
        assert result.is_empty() is False

    def test_is_empty_without_items(self):
        """测试无数据时为空"""
        result = PagedResult(items=[], page_info=PageInfo())
        assert result.is_empty() is True

    def test_first_or_none_with_items(self):
        """测试获取第一个元素"""
        result = PagedResult(items=['a', 'b', 'c'], page_info=PageInfo())
        assert result.first_or_none() == 'a'

    def test_first_or_none_without_items(self):
        """测试空数据时返回None"""
        result = PagedResult(items=[], page_info=PageInfo())
        assert result.first_or_none() is None


class TestDataLoader:
    """测试数据加载器基类"""

    def setup_method(self):
        """设置"""
        self.loader = DataLoader()

    def test_cache_disabled(self):
        """测试禁用缓存"""
        config = PageConfig(enable_cache=False)
        loader = DataLoader(config)
        assert loader.config.enable_cache is False


class TestLazyIterator:
    """测试懒加载迭代器"""

    def test_iteration_with_mock_loader(self):
        """测试迭代功能"""
        mock_loader = Mock()
        mock_loader.get_page.return_value = ['item1', 'item2']

        iterator = LazyIterator(mock_loader, page_size=10)

        items = list(iterator)
        assert len(items) == 2
        assert items[0] == 'item1'
        assert items[1] == 'item2'

    def test_reset(self):
        """测试重置功能"""
        mock_loader = Mock()
        mock_loader.get_page.return_value = ['item1']

        iterator = LazyIterator(mock_loader, page_size=10)
        list(iterator)  # 消耗迭代器

        iterator.reset()
        assert iterator.current_page == 1
        assert iterator.current_index == 0


class TestBatchProcessor:
    """测试批量处理器"""

    def test_process_sequential(self):
        """测试顺序处理"""
        processor = BatchProcessor(batch_size=10, max_workers=1)

        items = [1, 2, 3, 4, 5]
        results = processor.process(items, lambda x: x * 2)

        assert results == [2, 4, 6, 8, 10]

    def test_process_with_progress_callback(self):
        """测试带进度回调"""
        processor = BatchProcessor(batch_size=2)
        progress_calls = []

        def callback(current, total):
            progress_calls.append((current, total))

        items = [1, 2, 3, 4]
        processor.process(items, lambda x: x, progress_callback=callback)

        assert len(progress_calls) > 0

    def test_process_batch_parallel(self):
        """测试批量并行处理"""
        processor = BatchProcessor(batch_size=2, max_workers=2)

        items = [1, 2, 3, 4]
        results = processor.process(items, lambda x: x * 2)

        assert results == [2, 4, 6, 8]


class TestVirtualScrollState:
    """测试虚拟滚动状态"""

    def test_initial_state(self):
        """测试初始状态"""
        state = VirtualScrollState()
        assert state.visible_start == 0
        assert state.visible_end == 50
        assert state.total_height == 0
        assert state.item_height == 30

    def test_get_visible_range(self):
        """测试获取可见范围"""
        state = VirtualScrollState(visible_start=10, visible_end=30)
        start, end = state.get_visible_range()
        assert start == 10
        assert end == 30

    def test_update_scroll(self):
        """测试更新滚动"""
        state = VirtualScrollState(total_height=1000, item_height=30)
        state.update_scroll(scroll_top=100, viewport_height=300)

        assert state.scroll_top == 100
        assert state.visible_start >= 0


class TestHelperFunctions:
    """测试辅助函数"""

    def test_create_paged_result(self):
        """测试创建分页结果"""
        items = ['a', 'b', 'c']
        result = create_paged_result(items, page=1, page_size=10, total=100)

        assert result.items == items
        assert result.page_info.current_page == 1
        assert result.page_info.total_items == 100

    def test_normalize_page(self):
        """测试规范化页码"""
        assert normalize_page(1, 10, 100) == 1
        assert normalize_page(0, 10, 100) == 1
        assert normalize_page(-1, 10, 100) == 1
        assert normalize_page(15, 10, 100) == 10  # 超过最大页

    def test_calculate_offset(self):
        """测试计算偏移量"""
        assert calculate_offset(1, 10) == 0
        assert calculate_offset(2, 10) == 10
        assert calculate_offset(3, 10) == 20


# =============================================================================
# ContentParserService 集成测试
# =============================================================================

class TestContentParserServiceIntegration:
    """测试内容解析服务集成"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        service1 = get_parser_service()
        service2 = get_parser_service()
        assert service1 is service2

    def test_parse_unknown_type(self):
        """测试未知类型解析"""
        service = ContentParserService()
        result = service.parse("test content", "unknown_type")
        assert result.error is not None
        assert "不支持" in result.error

    def test_auto_detect_with_invalid_path(self):
        """测试自动检测无效路径"""
        service = ContentParserService()
        result = service.parse("/invalid/path/file.unknown")
        # 应该回退到text类型
        assert result.source_type == "text"


# =============================================================================
# 错误处理测试
# =============================================================================

class TestParsedContentErrorHandling:
    """测试ParsedContent错误处理"""

    def test_error_with_details(self):
        """测试带详情的错误"""
        content = ParsedContent()
        content.error = "测试错误"
        content.error_details = "详细错误信息"

        assert content.error == "测试错误"
        assert content.error_details == "详细错误信息"
        assert content.is_success is False

    def test_preview_with_error(self):
        """测试错误预览"""
        content = ParsedContent()
        content.error = "解析失败"
        preview = content.preview
        assert "解析失败" in preview


# =============================================================================
# ImageOCRProcessor 测试
# =============================================================================

class TestImageOCRProcessor:
    """测试ImageOCRProcessor"""

    def test_default_initialization(self):
        """测试默认初始化"""
        processor = ImageOCRProcessor()
        # 不检查is_available，因为它依赖外部库

    def test_supported_formats(self):
        """测试支持的格式"""
        from src.content.image_ocr_processor import SUPPORTED_IMAGE_FORMATS
        assert '.png' in SUPPORTED_IMAGE_FORMATS
        assert '.jpg' in SUPPORTED_IMAGE_FORMATS
        assert '.jpeg' in SUPPORTED_IMAGE_FORMATS


class TestOCRContactInfo:
    """测试OCR联系人信息"""

    def test_to_dict(self):
        """测试转换为字典"""
        info = OCRContactInfo(
            name="张三",
            phone="13800138000",
            email="zhangsan@example.com",
            confidence=0.85
        )
        result = info.to_dict()
        assert result['name'] == "张三"
        assert result['phone'] == "13800138000"
        assert result['email'] == "zhangsan@example.com"
        assert result['confidence'] == 0.85


class TestOCRResult:
    """测试OCR结果"""

    def test_successful_result(self):
        """测试成功结果"""
        result = OCRResult(
            success=True,
            raw_text="张三\n13800138000\ntest@example.com",
            task_name="【咨询】张三",
            task_content="【图片OCR识别内容】..."
        )
        assert result.success is True
        assert "张三" in result.raw_text

    def test_failed_result(self):
        """测试失败结果"""
        result = OCRResult(
            success=False,
            error="OCR库不可用",
            error_details="请安装pytesseract"
        )
        assert result.success is False
        assert result.error == "OCR库不可用"

    def test_to_dict(self):
        """测试转换为字典"""
        info = OCRContactInfo(name="测试", confidence=0.9)
        result = OCRResult(
            success=True,
            raw_text="测试文本",
            contact_info=info,
            task_name="测试任务",
            task_content="测试内容"
        )
        result_dict = result.to_dict()
        assert result_dict['success'] is True
        assert 'contact_info' in result_dict


class TestImageParserOCRIntegration:
    """测试ImageParser与OCR集成"""

    def test_parse_with_mock_processor(self):
        """测试使用模拟OCR处理器的解析"""
        parser = ImageParser()

        # 模拟OCR处理器不可用的情况
        with patch('src.content.content_parser_service.get_ocr_processor') as mock_get:
            mock_processor = Mock()
            mock_processor.is_available = False
            mock_get.return_value = mock_processor

            result = parser.parse("/path/to/image.png")

            assert result.source_type == "image"
            # OCR不可用时应该返回错误信息
            assert result.error is not None or "未启用" in result.task_content
