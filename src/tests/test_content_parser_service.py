# -*- coding: utf-8 -*-
"""
内容解析服务单元测试

版本：V4.1
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.content.content_parser_service import (
    ParsedContent,
    ContentParser,
    ContentParserService,
    TextParser,
    MSGParserWrapper,
    ImageParser,
    WeChatParser,
    ProgressParser,
    get_parser_service,
)


class TestParsedContent:
    """测试ParsedContent数据结构"""
    
    def test_default_values(self):
        """测试默认值"""
        content = ParsedContent()
        assert content.task_name == ""
        assert content.task_content == ""
        assert content.source == "unknown"
        assert content.error is None
    
    def test_to_dict(self):
        """测试转换为字典"""
        content = ParsedContent()
        content.task_name = "测试任务"
        content.task_content = "测试内容"
        content.source = "text"
        content.consultant_name = "张三"
        
        result = content.to_dict()
        assert result['task_name'] == "测试任务"
        assert result['task_content'] == "测试内容"
        assert result['consultant_name'] == "张三"
    
    def test_is_success_with_content(self):
        """测试成功判断（有内容）"""
        content = ParsedContent()
        content.task_content = "有内容"
        content.error = None
        assert content.is_success is True
    
    def test_is_success_with_error(self):
        """测试成功判断（有错误）"""
        content = ParsedContent()
        content.task_content = ""
        content.error = "解析失败"
        assert content.is_success is False
    
    def test_preview_with_error(self):
        """测试预览（错误情况）"""
        content = ParsedContent()
        content.error = "文件不存在"
        assert "解析失败" in content.preview
    
    def test_preview_with_content(self):
        """测试预览（有内容）"""
        content = ParsedContent()
        content.task_name = "测试主题"
        content.task_content = "这是测试内容"
        content.sender = "发件人"
        content.sender_email = "test@example.com"
        
        preview = content.preview
        assert "测试主题" in preview
        assert "发件人" in preview
        assert "test@example.com" in preview


class TestTextParser:
    """测试文本解析器"""
    
    def setup_method(self):
        """设置"""
        self.parser = TextParser()
    
    def test_parser_type(self):
        """测试解析器类型"""
        assert self.parser.parser_type == "text"
    
    def test_is_available(self):
        """测试解析器可用性"""
        assert self.parser.is_available() is True
    
    def test_parse_empty_content(self):
        """测试解析空内容"""
        result = self.parser.parse("")
        assert result.error == "内容为空"
    
    def test_parse_whitespace_content(self):
        """测试解析空白内容"""
        result = self.parser.parse("   ")
        assert result.error == "内容为空"
    
    def test_parse_normal_content(self):
        """测试解析普通内容"""
        content = "这是一个测试任务内容"
        result = self.parser.parse(content)
        
        assert result.is_success is True
        assert result.task_content == content
        assert result.source_type == "text"
    
    def test_parse_long_content(self):
        """测试解析长内容（任务名称截断）"""
        content = "A" * 100  # 超过50个字符
        result = self.parser.parse(content)
        
        assert result.is_success is True
        assert len(result.task_name) == 50  # 应该截断为50字符


class TestMSGParserWrapper:
    """测试MSG解析器包装器"""
    
    def setup_method(self):
        """设置"""
        self.parser = MSGParserWrapper()
    
    def test_parser_type(self):
        """测试解析器类型"""
        assert self.parser.parser_type == "msg"
    
    def test_is_available_when_library_missing(self):
        """测试库未安装时可用性"""
        with patch('src.content.msg_parser.MSGParser.is_available', return_value=False):
            parser = MSGParserWrapper()
            assert parser.is_available() is False
    
    def test_is_available_when_library_exists(self):
        """测试库已安装时可用性"""
        with patch('src.content.msg_parser.MSGParser.is_available', return_value=True):
            parser = MSGParserWrapper()
            assert parser.is_available() is True
    
    def test_parse_empty_path(self):
        """测试解析空路径"""
        result = self.parser.parse("")
        assert result.error == "文件路径为空"
    
    def test_parse_invalid_extension(self):
        """测试解析无效扩展名"""
        result = self.parser.parse("/path/to/file.txt")
        assert result.error == "文件格式不正确"
    
    def test_parse_nonexistent_file(self):
        """测试解析不存在的文件"""
        result = self.parser.parse("/nonexistent/path/test.msg")
        assert result.error == "文件不存在"
    
    def test_parse_library_not_available(self):
        """测试解析时库不可用"""
        with patch('src.content.msg_parser.MSGParser.is_available', return_value=False):
            parser = MSGParserWrapper()
            result = parser.parse("/path/to/test.msg")
            assert result.error == "MSG解析库未安装"
    
    def test_get_info(self):
        """测试获取解析器信息"""
        info = self.parser.get_info()
        assert 'type' in info
        assert info['type'] == 'msg'


class TestContentParserService:
    """测试内容解析服务"""
    
    def setup_method(self):
        """设置"""
        self.service = ContentParserService()
    
    def test_supported_types(self):
        """测试支持的类型"""
        assert 'text' in self.service.SUPPORTED_TYPES
        assert 'msg' in self.service.SUPPORTED_TYPES
        assert 'image' in self.service.SUPPORTED_TYPES
        assert 'wechat' in self.service.SUPPORTED_TYPES
    
    def test_get_parser(self):
        """测试获取解析器"""
        text_parser = self.service.get_parser('text')
        assert text_parser is not None
        assert isinstance(text_parser, TextParser)
        
        msg_parser = self.service.get_parser('msg')
        assert msg_parser is not None
        assert isinstance(msg_parser, MSGParserWrapper)
    
    def test_get_parser_invalid_type(self):
        """测试获取无效类型的解析器"""
        parser = self.service.get_parser('invalid')
        assert parser is None
    
    def test_parse_with_explicit_type(self):
        """测试指定类型解析"""
        result = self.service.parse("测试内容", "text")
        assert result.is_success is True
    
    def test_parse_auto_detect_text(self):
        """测试自动检测文本类型"""
        result = self.service.parse("测试内容")
        assert result.source_type == "text"
    
    def test_parse_auto_detect_msg(self):
        """测试自动检测MSG类型"""
        with patch('os.path.exists', return_value=True):
            with patch.object(MSGParserWrapper, 'is_available', return_value=True):
                with patch.object(MSGParserWrapper, 'parse') as mock_parse:
                    mock_result = ParsedContent()
                    mock_result.source_type = "msg"
                    mock_parse.return_value = mock_result
                    
                    result = self.service.parse("/path/to/test.msg")
                    assert result.source_type == "msg"
    
    def test_get_available_parsers(self):
        """测试获取可用解析器列表"""
        parsers = self.service.get_available_parsers()
        assert len(parsers) == 4
        assert all('type' in p for p in parsers)
        assert all('available' in p for p in parsers)
    
    def test_check_dependencies(self):
        """测试检查依赖"""
        deps = self.service.check_dependencies()
        assert 'text' in deps
        assert 'msg' in deps
        assert 'image' in deps
        assert 'wechat' in deps


class TestProgressParser:
    """测试进度解析器"""
    
    def test_init(self):
        """测试初始化"""
        parser = ProgressParser(source_type='msg')
        assert parser.source_type == 'msg'
        assert parser.parser is not None
    
    def test_parse_files_with_callback(self):
        """测试批量解析带回调"""
        progress_calls = []
        
        def callback(current, total, status):
            progress_calls.append((current, total, status))
        
        with patch.object(MSGParserWrapper, 'is_available', return_value=True):
            with patch.object(MSGParserWrapper, 'parse') as mock_parse:
                mock_result = ParsedContent()
                mock_result.source_type = "msg"
                mock_parse.return_value = mock_result
                
                with patch('os.path.exists', return_value=True):
                    parser = ProgressParser(source_type='msg')
                    parser.parser = mock_parse
                    
                    results = parser.parse_files(
                        ['/path/file1.msg', '/path/file2.msg'],
                        progress_callback=callback
                    )
                    
                    assert len(results) == 2
                    assert len(progress_calls) == 3  # 2个文件 + 1个完成
    
    def test_parse_with_retry_success(self):
        """测试重试成功"""
        with patch.object(MSGParserWrapper, 'is_available', return_value=True):
            with patch.object(MSGParserWrapper, 'parse') as mock_parse:
                mock_result = ParsedContent()
                mock_result.error = None
                mock_result.task_content = "success"
                mock_parse.return_value = mock_result
                
                parser = ProgressParser(source_type='msg')
                parser.parser = mock_parse
                
                result = parser.parse_with_retry("/path/test.msg", max_retries=3)
                assert result.is_success is True


class TestSingleton:
    """测试单例"""
    
    def test_get_parser_service_returns_same_instance(self):
        """测试获取解析服务返回同一实例"""
        service1 = get_parser_service()
        service2 = get_parser_service()
        assert service1 is service2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
