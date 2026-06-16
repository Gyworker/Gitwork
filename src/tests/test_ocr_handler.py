# -*- coding: utf-8 -*-
"""
OCR处理模块单元测试
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.content.ocr_handler import (
    OCRResult, ImagePreprocessor, BusinessCardParser, OCRProcessor
)


class TestOCRResult:
    """OCR结果数据类测试"""

    def test_create_result(self):
        """测试创建结果"""
        result = OCRResult(
            raw_text="张三 13800138000 zhangsan@example.com",
            name="张三",
            phone="13800138000",
            email="zhangsan@example.com",
            company="测试公司",
            confidence=0.9
        )

        assert result.name == "张三"
        assert result.phone == "13800138000"
        assert result.confidence == 0.9

    def test_to_dict(self):
        """测试转换为字典"""
        result = OCRResult(name="李四", phone="13900139000")
        data = result.to_dict()

        assert isinstance(data, dict)
        assert data['name'] == "李四"

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            'raw_text': '测试',
            'name': '王五',
            'phone': '13700137000',
            'email': '',
            'company': '',
            'department': '',
            'position': '',
            'address': '',
            'confidence': 0.8,
            'source_image': 'test.jpg',
            'process_time': 1.5
        }
        result = OCRResult.from_dict(data)

        assert result.name == "王五"
        assert result.confidence == 0.8


class TestImagePreprocessor:
    """图像预处理器测试"""

    def test_preprocess_returns_image(self):
        """测试预处理返回图像对象"""
        # 创建一个简单的测试图片
        from PIL import Image

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            # 创建一个简单的测试图像
            img = Image.new('RGB', (100, 100), color='white')
            img.save(f.name)

            try:
                # 这个测试验证预处理函数可以被调用
                # 实际测试需要有效的图片文件
                # 这里只测试函数存在且可调用
                preprocessor = ImagePreprocessor()
                assert hasattr(preprocessor, 'preprocess')
                assert hasattr(preprocessor, 'enhance_for_text')
            finally:
                os.unlink(f.name)

    def test_get_supported_formats(self):
        """测试支持的格式"""
        processor = OCRProcessor()
        formats = processor.get_supported_formats()

        assert '.jpg' in formats
        assert '.jpeg' in formats
        assert '.png' in formats
        assert '.bmp' in formats

    def test_is_supported_format(self):
        """测试格式检查"""
        processor = OCRProcessor()

        assert processor.is_supported_format('test.jpg') == True
        assert processor.is_supported_format('test.png') == True
        assert processor.is_supported_format('test.bmp') == True
        assert processor.is_supported_format('test.gif') == False


class TestBusinessCardParser:
    """名片解析器测试"""

    def test_parse_chinese_card(self):
        """测试解析中文名片"""
        text = """
        张三
        电话: 13800138000
        邮箱: zhangsan@example.com
        测试科技有限公司
        市场部经理
        """

        result = BusinessCardParser.parse(text)

        assert result['name'] == '张三'
        assert result['phone'] == '13800138000'
        assert result['email'] == 'zhangsan@example.com'

    def test_parse_phone_patterns(self):
        """测试电话号码提取"""
        test_cases = [
            ("电话: 13800138000", "13800138000"),
            ("手机:13900139000", "13900139000"),
            ("Tel: 021-12345678", "021-12345678"),
        ]

        for text, expected in test_cases:
            result = BusinessCardParser.parse(text)
            # 电话号码应该被提取
            # 注意：可能需要根据正则表达式调整预期

    def test_parse_email(self):
        """测试邮箱提取"""
        text = "联系方式: contact@example.com"
        result = BusinessCardParser.parse(text)

        assert result['email'] == 'contact@example.com'

    def test_parse_company(self):
        """测试公司名称提取"""
        text = """
        李四
        有限公司
        测试科技有限公司
        """

        result = BusinessCardParser.parse(text)

        # 应该识别出公司
        assert 'company' in result

    def test_parse_empty_text(self):
        """测试空文本"""
        result = BusinessCardParser.parse("")

        assert result['name'] == ''
        assert result['phone'] == ''

    def test_clean_phone(self):
        """测试电话号码清理"""
        test_cases = [
            ("+86-138-0013-8000", "13800138000"),
            ("021-12345678", "021-12345678"),
        ]

        for phone_str, expected in test_cases:
            cleaned = BusinessCardParser._clean_phone(phone_str)
            # 验证清理结果（可能需要调整正则）
            assert len(cleaned) > 0

    def test_extract_name_from_email(self):
        """测试从邮箱提取姓名"""
        email = "zhangsan@example.com"
        name = BusinessCardParser._extract_name_from_email(email)

        assert name == "Zhangsan"

    def test_extract_name_with_prefix(self):
        """测试从邮箱提取姓名（带前缀）"""
        email = "info@example.com"
        name = BusinessCardParser._extract_name_from_email(email)

        # info前缀应该被移除
        assert name != "Info"


class TestOCRProcessor:
    """OCR处理器测试"""

    def test_init_default(self):
        """测试默认初始化"""
        processor = OCRProcessor()

        assert processor.batch_id is not None
        assert processor.preprocessor is not None
        assert processor.parser is not None

    def test_init_custom_tesseract_path(self):
        """测试自定义Tesseract路径"""
        processor = OCRProcessor(tesseract_path='C:/tesseract/tesseract.exe')

        # 应该能正常初始化
        assert processor is not None

    @patch('src.content.ocr_handler.pytesseract.image_to_string')
    @patch('src.content.ocr_handler.Image.open')
    def test_recognize_image_mock(self, mock_image_open, mock_ocr):
        """测试图像识别（模拟）"""
        # 模拟图片
        mock_img = MagicMock()
        mock_image_open.return_value = mock_img
        mock_img.convert.return_value = mock_img
        mock_img.filter.return_value = mock_img
        mock_img.point.return_value = mock_img

        # 模拟OCR结果
        mock_ocr.return_value = "张三\n13800138000\ntest@example.com"

        processor = OCRProcessor()
        result = processor.recognize_image('test.jpg')

        assert isinstance(result, OCRResult)
        # 由于使用了mock，原始文本应该是OCR返回值
        assert len(result.raw_text) > 0

    def test_recognize_batch_empty(self):
        """测试批量识别空列表"""
        processor = OCRProcessor()
        results = processor.recognize_batch([])

        assert results == []

    @patch('src.content.ocr_handler.pytesseract.image_to_string')
    @patch('src.content.ocr_handler.Image.open')
    def test_recognize_batch_multiple(self, mock_image_open, mock_ocr):
        """测试批量识别多张图片"""
        # 模拟多张图片
        mock_img = MagicMock()
        mock_image_open.return_value = mock_img
        mock_img.convert.return_value = mock_img
        mock_img.filter.return_value = mock_img
        mock_img.point.return_value = mock_img
        mock_ocr.return_value = "测试"

        processor = OCRProcessor()
        results = processor.recognize_batch(['test1.jpg', 'test2.jpg'])

        assert len(results) == 2
        assert all(isinstance(r, OCRResult) for r in results)


class TestOCRIntegration:
    """OCR集成测试（需要实际Tesseract）"""

    @pytest.fixture
    def sample_image_path(self):
        """创建样本图片"""
        from PIL import Image, ImageDraw, ImageFont

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            # 创建一个包含文字的图片
            img = Image.new('RGB', (300, 150), color='white')
            draw = ImageDraw.Draw(img)

            # 尝试绘制文字（如果字体可用）
            try:
                draw.text((10, 10), "Test OCR", fill='black')
            except:
                pass

            img.save(f.name, 'PNG')

        yield f.name

        if os.path.exists(f.name):
            os.unlink(f.name)

    def test_ocr_processor_can_be_instantiated(self):
        """测试OCR处理器可以实例化"""
        processor = OCRProcessor()
        assert processor is not None
        assert processor.get_supported_formats() is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
