# -*- coding: utf-8 -*-
"""
MSG邮件解析模块单元测试
版本：V1.0
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.content.msg_parser import MSGParser, MSGEmail, BatchMSGParser


class TestMSGEmail:
    """MSGEmail数据类测试"""
    
    def test_email_creation(self):
        """测试邮件对象创建"""
        email = MSGEmail(
            subject="测试邮件",
            sender="张三",
            sender_email="zhangsan@example.com",
            body="这是一封测试邮件",
            date="2026-06-17"
        )
        
        assert email.subject == "测试邮件"
        assert email.sender == "张三"
        assert email.sender_email == "zhangsan@example.com"
        assert email.body == "这是一封测试邮件"
    
    def test_email_to_dict(self):
        """测试转换为字典"""
        email = MSGEmail(subject="测试")
        data = email.to_dict()
        
        assert isinstance(data, dict)
        assert data['subject'] == "测试"
        assert 'attachments' in data
    
    def test_to_task_content(self):
        """测试转换为任务内容"""
        email = MSGEmail(
            subject="产品报价咨询",
            sender="李四",
            sender_email="lisi@example.com",
            date="2026-06-17 10:00",
            body="请尽快提供报价清单",
            importance="高"
        )
        
        content = email.to_task_content()
        
        assert "【主题】产品报价咨询" in content
        assert "【发件人】李四" in content
        assert "【邮箱】lisi@example.com" in content
        assert "【时间】2026-06-17 10:00" in content
        assert "【重要程度】高" in content
        assert "请尽快提供报价清单" in content


class TestMSGParser:
    """MSG解析器测试"""
    
    def test_library_status(self):
        """测试库状态检查"""
        info = MSGParser.get_library_info()
        
        assert 'available' in info
        assert 'library' in info
        assert info['library'] == 'extract-msg'
    
    def test_is_available(self):
        """测试库可用性检查"""
        result = MSGParser.is_available()
        assert isinstance(result, bool)
    
    def test_supported_extensions(self):
        """测试支持的文件扩展名"""
        assert '.msg' in MSGParser.SUPPORTED_EXTENSIONS
    
    def test_clean_text(self):
        """测试文本清理"""
        # 测试多余空白清理
        text = "测试\n\n\n文本\n\n"
        cleaned = MSGParser._clean_text(text)
        assert cleaned.count('\n') <= 2
        
        # 测试空字符串
        assert MSGParser._clean_text("") == ""
        assert MSGParser._clean_text(None) == ""
    
    def test_extract_name(self):
        """测试姓名提取"""
        # "姓名 <邮箱>" 格式
        assert MSGParser._extract_name("张三 <zhangsan@example.com>") == "张三"
        
        # 普通文本
        assert MSGParser._extract_name("李四") == "李四"
        
        # 空字符串
        assert MSGParser._extract_name("") == ""
    
    def test_extract_email(self):
        """测试邮箱提取"""
        assert MSGParser._extract_email("张三 <zhangsan@example.com>") == "zhangsan@example.com"
        assert MSGParser._extract_email("联系: wangwu@example.com") == "wangwu@example.com"
        assert MSGParser._extract_email("无邮箱") == ""
    
    def test_format_date(self):
        """测试日期格式化"""
        # 标准格式
        assert MSGParser._format_date("2026-06-17 10:30:00") == "2026-06-17 10:30"
        
        # 空字符串
        assert MSGParser._format_date("") == ""
        
        # 其他格式
        result = MSGParser._format_date("invalid date")
        assert isinstance(result, str)
    
    def test_map_importance(self):
        """测试重要程度映射"""
        assert MSGParser._map_importance(0) == "低"
        assert MSGParser._map_importance(1) == "普通"
        assert MSGParser._map_importance(2) == "高"
        assert MSGParser._map_importance(99) == "普通"  # 未知值
    
    def test_parse_nonexistent_file(self):
        """测试解析不存在的文件"""
        with pytest.raises(FileNotFoundError):
            MSGParser.parse_file("/nonexistent/file.msg")
    
    def test_parse_invalid_extension(self):
        """测试无效文件扩展名"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            filepath = f.name
        
        try:
            with pytest.raises(ValueError):
                MSGParser.parse_file(filepath)
        finally:
            os.unlink(filepath)


class TestExtractContacts:
    """联系人提取测试"""
    
    def test_extract_sender_contact(self):
        """测试提取发件人联系人"""
        email = MSGEmail(
            sender="张三",
            sender_email="zhangsan@example.com",
            body="请联系我: 13800138000"
        )
        
        contacts = MSGParser.extract_contacts(email)
        
        assert len(contacts) >= 1
        assert any(c['email'] == 'zhangsan@example.com' for c in contacts)
    
    def test_extract_body_contacts(self):
        """测试从正文提取联系人"""
        email = MSGEmail(
            sender="李四",
            sender_email="lisi@example.com",
            body="请联系王五: wangwu@example.com\n赵六: zhaoliu@example.com"
        )
        
        contacts = MSGParser.extract_contacts(email)
        
        # 应该包含发件人和正文中的联系人
        assert len(contacts) >= 3


class TestBatchParser:
    """批量解析测试"""
    
    def test_batch_parser_init(self):
        """测试批量解析器初始化"""
        parser = BatchMSGParser()
        assert parser.results == []
        assert parser.errors == []
    
    def test_batch_parser_summary(self):
        """测试批量解析摘要"""
        parser = BatchMSGParser()
        summary = parser.get_summary()
        
        assert 'total_files' in summary
        assert 'success_count' in summary
        assert 'error_count' in summary
    
    def test_parse_empty_directory(self):
        """测试解析空目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            parser = BatchMSGParser()
            results = parser.parse_directory(tmpdir)
            
            assert results == []


class TestJSONSerialization:
    """JSON序列化测试"""
    
    def test_to_json(self):
        """测试导出为JSON"""
        email = MSGEmail(
            subject="测试",
            sender="张三"
        )
        
        json_str = MSGParser.to_json(email)
        
        assert isinstance(json_str, str)
        assert "测试" in json_str
        assert "张三" in json_str
    
    def test_to_json_with_file(self):
        """测试导出到文件"""
        email = MSGEmail(subject="测试邮件")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            json_str = MSGParser.to_json(email, filepath)
            
            # 验证文件已创建
            assert os.path.exists(filepath)
            
            # 验证文件内容
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "测试邮件" in content
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
    
    def test_from_json(self):
        """测试从JSON导入"""
        json_str = '{"subject": "测试", "sender": "李四"}'
        
        email = MSGParser.from_json(json_str=json_str)
        
        assert email.subject == "测试"
        assert email.sender == "李四"
    
    def test_from_json_file(self):
        """测试从JSON文件导入"""
        json_str = '{"subject": "文件测试"}'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(json_str)
            filepath = f.name
        
        try:
            email = MSGParser.from_json(filepath=filepath)
            assert email.subject == "文件测试"
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
