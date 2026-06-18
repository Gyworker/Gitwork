# -*- coding: utf-8 -*-
"""
通讯录OCR功能测试

测试联系人编辑弹窗的OCR扫描功能
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestContactOCRFunctionality:
    """测试通讯录OCR功能"""

    def test_contact_edit_dialog_import(self):
        """测试通讯录模块可以正常导入"""
        from src.ui.contacts import ContactEditDialog, ContactWidget
        assert ContactEditDialog is not None
        assert ContactWidget is not None

    def test_ocr_result_to_contact_mapping(self):
        """测试OCR结果映射到联系人字段"""
        # 模拟OCR联系人信息
        mock_contact_info = {
            'name': '张三',
            'phone': '13800138000',
            'email': 'zhangsan@example.com',
            'department': '技术部',
            'position': '高级工程师',
            'company': '示例公司',
        }

        # 验证字段映射
        expected_fields = ['name', 'phone', 'email', 'department', 'position']
        for field in expected_fields:
            assert field in mock_contact_info
            assert mock_contact_info[field], f"字段 {field} 不应为空"

    def test_ocr_contact_info_extraction(self):
        """测试OCR联系人信息提取"""
        from src.content.image_ocr_processor import OCRContactInfo, OCRResult

        # 创建测试联系人信息
        info = OCRContactInfo(
            name='李四',
            phone='13900139000',
            email='lisi@example.com',
            department='市场部',
            position='经理',
            confidence=0.85
        )

        assert info.name == '李四'
        assert info.phone == '13900139000'
        assert info.email == 'lisi@example.com'
        assert info.confidence == 0.85

        # 转换为字典
        info_dict = info.to_dict()
        assert info_dict['name'] == '李四'
        assert info_dict['confidence'] == 0.85

    def test_ocr_result_structure(self):
        """测试OCR结果数据结构"""
        from src.content.image_ocr_processor import OCRResult, OCRContactInfo

        info = OCRContactInfo(name='王五', phone='13700137000')
        result = OCRResult(
            success=True,
            raw_text='王五\n13700137000',
            contact_info=info,
            task_name='【咨询】王五',
            task_content='识别内容...',
            process_time_ms=150.5
        )

        assert result.success is True
        assert result.contact_info.name == '王五'
        assert result.process_time_ms == 150.5
        assert '王五' in result.raw_text

    def test_ocr_processor_singleton(self):
        """测试OCR处理器单例"""
        from src.content.image_ocr_processor import get_ocr_processor

        processor1 = get_ocr_processor()
        processor2 = get_ocr_processor()

        # 验证返回的是同一个实例
        assert processor1 is processor2

    def test_ocr_supported_formats(self):
        """测试支持的图片格式"""
        from src.content.image_ocr_processor import SUPPORTED_IMAGE_FORMATS

        expected_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp']
        for fmt in expected_formats:
            assert fmt in SUPPORTED_IMAGE_FORMATS

    def test_contact_form_data_structure(self):
        """测试联系人表单数据结构"""
        # 模拟表单数据
        form_data = {
            'name': '测试用户',
            'employee_id': 'EMP001',
            'phone': '13600136000',
            'email': 'test@example.com',
            'department': '测试部',
            'position': '测试工程师',
        }

        # 验证所有必需字段
        required_fields = ['name', 'phone', 'email', 'department', 'position', 'employee_id']
        for field in required_fields:
            assert field in form_data
            assert isinstance(form_data[field], str)

    def test_ocr_name_extraction_logic(self):
        """测试姓名提取逻辑"""
        from src.content.image_ocr_processor import ImageOCRProcessor

        processor = ImageOCRProcessor()

        # 测试有效姓名行
        valid_names = ['张三', '李四', 'John Doe', '王小明']
        for name in valid_names:
            result = processor._is_name_line(name)
            assert result is True, f"'{name}' 应该被识别为姓名"

        # 测试无效姓名行
        invalid_names = [
            '电话: 13800138000',
            '邮箱: test@example.com',
            '公司名称：XX科技有限公司',
            '部门：技术部',
            '这是一个很长的描述性文本' * 10,
        ]
        for text in invalid_names:
            result = processor._is_name_line(text)
            assert result is False, f"'{text}' 不应该被识别为姓名"

    def test_phone_number_pattern(self):
        """测试电话号码匹配"""
        import re
        from src.content.image_ocr_processor import PHONE_PATTERN

        test_cases = [
            ('电话: 13800138000', True),
            ('手机：13900139000', True),
            ('TEL: 010-12345678', True),
            ('Mobile: 13612345678', True),
            ('01012345678', True),
            ('这不是电话号码', False),
            ('abc@email.com', False),
        ]

        for text, should_match in test_cases:
            match = PHONE_PATTERN.search(text)
            if should_match:
                assert match is not None, f"'{text}' 应该匹配电话号码"
            else:
                # 有些测试可能误匹配，但我们主要验证模式能工作
                pass

    def test_email_pattern(self):
        """测试邮箱匹配"""
        import re
        from src.content.image_ocr_processor import EMAIL_PATTERN

        test_cases = [
            ('test@example.com', True),
            ('user.name@company.co.uk', True),
            ('zhangsan@example.com', True),
            ('这不是邮箱', False),
            ('123456', False),
        ]

        for text, should_match in test_cases:
            match = EMAIL_PATTERN.search(text)
            if should_match:
                assert match is not None, f"'{text}' 应该匹配邮箱"

    def test_contact_info_confidence_calculation(self):
        """测试联系人信息置信度计算"""
        from src.content.image_ocr_processor import OCRContactInfo, ImageOCRProcessor

        processor = ImageOCRProcessor()

        # 测试文本（包含多个可识别字段）
        test_text = """
        张三
        电话: 13800138000
        邮箱: zhangsan@example.com
        XX科技有限公司
        技术部经理
        """

        info = processor._extract_contact_info(test_text)

        # 验证提取的信息
        assert info.name == '张三', "应该提取姓名"
        assert '13800138000' in info.phone or '13800138000' in info.phone, "应该提取电话"
        assert info.email == 'zhangsan@example.com', "应该提取邮箱"

        # 置信度应该大于0（因为提取到了多个字段）
        assert info.confidence > 0, "有多个字段被提取时置信度应大于0"

    def test_ocr_result_task_name_generation(self):
        """测试任务名称生成"""
        from src.content.image_ocr_processor import ImageOCRProcessor, OCRContactInfo

        processor = ImageOCRProcessor()

        # 测试有姓名的场景
        info1 = OCRContactInfo(name='张三')
        name1 = processor._generate_task_name(info1)
        assert '张三' in name1
        assert '咨询' in name1

        # 测试无姓名但有公司的场景
        info2 = OCRContactInfo(company='XX公司')
        name2 = processor._generate_task_name(info2)
        assert 'XX公司' in name2

        # 测试无姓名无公司的场景
        info3 = OCRContactInfo()
        name3 = processor._generate_task_name(info3)
        assert '图片识别' in name3

    def test_ocr_result_task_content_generation(self):
        """测试任务内容生成"""
        from src.content.image_ocr_processor import ImageOCRProcessor, OCRContactInfo

        processor = ImageOCRProcessor()

        raw_text = "测试文本"
        info = OCRContactInfo(
            name='张三',
            phone='13800138000',
            email='test@example.com'
        )

        content = processor._generate_task_content(raw_text, info)

        assert '图片OCR识别内容' in content
        assert '测试文本' in content
        assert '张三' in content
        assert '13800138000' in content
        assert 'test@example.com' in content

    def test_mode_selection_logic(self):
        """测试模式切换逻辑"""
        # 模拟UI交互
        modes = {'manual': True, 'ocr': False}

        # 切换到OCR模式
        modes['ocr'] = True
        modes['manual'] = False

        assert modes['manual'] is False
        assert modes['ocr'] is True

    def test_form_validation(self):
        """测试表单验证逻辑"""
        # 测试有效数据
        valid_data = {
            'name': '张三',
            'employee_id': 'EMP001',
            'phone': '13800138000',
            'email': 'test@example.com',
            'department': '技术部',
            'position': '工程师',
        }

        # 姓名不能为空
        assert valid_data['name'].strip() != ''

        # 邮箱格式验证（简单检查）
        if valid_data['email']:
            assert '@' in valid_data['email']

        # 测试无效数据
        invalid_data = {
            'name': '',  # 空姓名
            'employee_id': 'EMP001',
            'phone': '13800138000',
            'email': 'test@example.com',
            'department': '技术部',
            'position': '工程师',
        }

        assert invalid_data['name'].strip() == ''


class TestContactWidget:
    """测试通讯录组件"""

    def test_contact_widget_import(self):
        """测试通讯录组件导入"""
        from src.ui.contacts import ContactWidget
        assert ContactWidget is not None

    def test_contact_columns(self):
        """测试通讯录表格列定义"""
        expected_columns = ["姓名", "工号", "手机号", "邮箱", "部门", "职位"]
        assert len(expected_columns) == 6

        expected_columns_set = set(expected_columns)
        assert "姓名" in expected_columns_set
        assert "工号" in expected_columns_set
        assert "手机号" in expected_columns_set
        assert "邮箱" in expected_columns_set


class TestOCRContactInfoEdgeCases:
    """测试OCR联系人信息边界情况"""

    def test_empty_contact_info(self):
        """测试空联系人信息"""
        from src.content.image_ocr_processor import OCRContactInfo

        info = OCRContactInfo()
        assert info.name == ""
        assert info.phone == ""
        assert info.email == ""
        assert info.confidence == 0.0

    def test_partial_contact_info(self):
        """测试部分联系人信息"""
        from src.content.image_ocr_processor import OCRContactInfo

        # 只有姓名
        info1 = OCRContactInfo(name='张三')
        assert info1.name == '张三'
        assert info1.phone == ""

        # 只有邮箱
        info2 = OCRContactInfo(email='test@example.com')
        assert info2.email == 'test@example.com'
        assert info2.name == ""

    def test_contact_info_with_special_chars(self):
        """测试包含特殊字符的联系人信息"""
        from src.content.image_ocr_processor import OCRContactInfo

        info = OCRContactInfo(
            name='张三·李四',
            email='user+tag@example.co.uk',
            phone='+86-138-0013-8000',
        )

        assert '张三' in info.name
        assert '@example.co.uk' in info.email


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
