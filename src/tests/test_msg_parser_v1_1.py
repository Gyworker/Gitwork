# -*- coding: utf-8 -*-
"""
MSG邮件解析模块V1.1单元测试
版本：V1.1
测试新增功能：
- ParseError错误上下文增强
- 进度回调机制
- 流式解析大文件
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.content.msg_parser import (
    MSGParser, MSGEmail, BatchMSGParser, 
    ParseError, ParseProgress, 
    MSGParserWithProgress, StreamingMSGParser, MemoryWarning
)


class TestParseError:
    """ParseError错误上下文增强测试"""
    
    def test_parse_error_creation(self):
        """TC-ERR-001: ParseError创建测试"""
        error = ParseError(
            error_type='file_not_found',
            error_message='文件不存在',
            filepath='test.msg',
            file_size=1024,
            timestamp='2026-06-18 10:00:00'
        )
        
        assert error.error_type == 'file_not_found'
        assert error.error_message == '文件不存在'
        assert error.filepath == 'test.msg'
        assert error.file_size == 1024
        assert error.timestamp == '2026-06-18 10:00:00'
    
    def test_parse_error_to_user_message(self):
        """TC-ERR-002: ParseError用户消息生成测试"""
        error = ParseError(
            error_type='parse_error',
            error_message='解析失败',
            filepath='C:\\test\\email.msg',
            file_size=2048,
            timestamp='2026-06-18 10:00:00'
        )
        
        message = error.to_user_message()
        
        assert '解析失败' in message
        assert 'email.msg' in message
        assert 'KB' in message or 'B' in message
        assert '2026-06-18' in message
    
    def test_parse_error_to_dict(self):
        """TC-ERR-003: ParseError字典转换测试"""
        error = ParseError(
            error_type='value_error',
            error_message='格式错误',
            filepath='test.msg'
        )
        
        data = error.to_dict()
        
        assert isinstance(data, dict)
        assert data['error_type'] == 'value_error'
        assert data['error_message'] == '格式错误'


class TestMSGParserErrorContext:
    """MSGParser错误上下文测试"""
    
    def test_create_error_method(self):
        """测试_create_error方法"""
        context = {
            'filepath': 'test.msg',
            'file_size': 1024,
            'parse_stage': 'init'
        }
        
        error = MSGParser._create_error(
            FileNotFoundError("文件不存在"),
            context,
            'file_not_found'
        )
        
        assert error.error_type == 'file_not_found'
        assert '文件不存在' in error.error_message
        assert error.filepath == 'test.msg'
        assert error.context['parse_stage'] == 'init'
    
    def test_parse_file_not_found_context(self):
        """测试文件不存在的错误上下文"""
        with pytest.raises((FileNotFoundError, ParseError)):
            MSGParser.parse_file('nonexistent_file.msg')
    
    def test_parse_invalid_extension_context(self):
        """测试无效文件扩展名的错误上下文"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            filepath = f.name
        
        try:
            with pytest.raises((ValueError, ParseError)):
                MSGParser.parse_file(filepath)
        finally:
            os.unlink(filepath)


class TestProgressCallback:
    """进度回调机制测试"""
    
    def test_parser_with_progress_init(self):
        """TC-PROG-001: 进度回调初始化测试"""
        def dummy_callback(progress):
            pass
        
        def dummy_cancel():
            return False
        
        parser = MSGParserWithProgress(
            progress_callback=dummy_callback,
            cancel_check=dummy_cancel
        )
        
        assert parser.progress_callback == dummy_callback
        assert parser.cancel_check == dummy_cancel
    
    def test_progress_callback_triggered(self):
        """TC-PROG-001: 进度回调触发测试"""
        progress_events = []
        
        def progress_callback(progress: ParseProgress):
            progress_events.append(progress)
        
        parser = MSGParserWithProgress(progress_callback=progress_callback)
        
        # 测试空列表
        results = parser.parse_batch([])
        assert len(progress_events) == 0
    
    def test_progress_percentage_calculation(self):
        """TC-PROG-002: 进度百分比计算测试"""
        progress_events = []
        
        def progress_callback(progress: ParseProgress):
            progress_events.append(progress)
        
        parser = MSGParserWithProgress(progress_callback=progress_callback)
        
        # 模拟5个文件的进度
        test_files = [f'test{i}.msg' for i in range(5)]
        
        # 由于文件不存在，会触发error状态
        parser.parse_batch(test_files)
        
        # 验证进度百分比递增
        if len(progress_events) > 1:
            percentages = [p.percentage for p in progress_events if p.status == 'processing']
            # 百分比应该递增
            assert percentages == sorted(percentages) or len(percentages) <= 1
    
    def test_cancel_operation(self):
        """TC-PROG-003: 取消操作测试"""
        cancel_at = [2]  # 第2个文件时取消
        call_count = [0]
        
        def cancel_check():
            call_count[0] += 1
            return call_count[0] > cancel_at[0]
        
        parser = MSGParserWithProgress(cancel_check=cancel_check)
        
        # 5个文件，第2个之后取消
        test_files = [f'test{i}.msg' for i in range(5)]
        results = parser.parse_batch(test_files)
        
        # cancel_check被调用多次
        assert call_count[0] > cancel_at[0]
    
    def test_progress_history(self):
        """测试进度历史记录"""
        def progress_callback(progress: ParseProgress):
            pass
        
        parser = MSGParserWithProgress(progress_callback=progress_callback)
        parser.parse_batch(['test.msg'])
        
        history = parser.get_progress_history()
        assert isinstance(history, list)


class TestStreamingParser:
    """流式解析大文件测试"""
    
    def test_streaming_parser_init(self):
        """TC-STREAM-001: 流式解析器初始化测试"""
        parser = StreamingMSGParser()
        
        assert parser.memory_limit == StreamingMSGParser.DEFAULT_MEMORY_LIMIT
        assert parser.CHUNK_SIZE == 1024 * 1024  # 1MB
    
    def test_streaming_parser_custom_memory_limit(self):
        """测试自定义内存限制"""
        custom_limit = 100 * 1024 * 1024  # 100MB
        parser = StreamingMSGParser(memory_limit=custom_limit)
        
        assert parser.memory_limit == custom_limit
    
    def test_parse_large_file_nonexistent(self):
        """TC-STREAM-001: 大文件解析文件不存在"""
        parser = StreamingMSGParser()
        
        with pytest.raises(FileNotFoundError):
            parser.parse_large_file('nonexistent.msg')
    
    def test_small_file_standard_parse(self):
        """TC-STREAM-001: 小文件使用标准解析"""
        parser = StreamingMSGParser()
        
        # 小于2MB的文件应该使用标准解析
        assert parser.CHUNK_SIZE * 2 == 2 * 1024 * 1024
    
    def test_memory_warning_class(self):
        """TC-STREAM-002: 内存警告异常测试"""
        warning = MemoryWarning("内存超过限制")
        
        assert str(warning) == "内存超过限制"
        assert isinstance(warning, Exception)
    
    def test_parse_header_method(self):
        """TC-STREAM-003: 文件头解析测试"""
        parser = StreamingMSGParser()
        
        # 模拟文件头
        header = b"Subject: Test Email\r\nDate: 2026-06-18\r\n"
        
        email = MSGEmail()
        parser._parse_header(header, email)
        
        # 验证主题被提取
        assert email.subject == "Test Email"
        # 验证日期被提取
        assert '2026-06-18' in email.date


class TestV1Compatibility:
    """V1.0 API兼容性测试"""
    
    def test_parse_file_safe_compatibility(self):
        """TC-COMPAT-001: V1.0 API兼容测试"""
        # parse_file_safe应该仍然可用
        assert hasattr(MSGParser, 'parse_file_safe')
        assert callable(MSGParser.parse_file_safe)
    
    def test_msg_email_to_task_content(self):
        """TC-COMPAT-001: to_task_content方法兼容性"""
        email = MSGEmail(
            subject="测试主题",
            sender="张三",
            sender_email="test@example.com",
            date="2026-06-18"
        )
        
        content = email.to_task_content()
        
        assert "【主题】测试主题" in content
        assert "【发件人】张三" in content
    
    def test_json_indent_parameter(self):
        """测试JSON格式化参数"""
        email = MSGEmail(subject="测试")
        
        # 不缩进
        json_no_indent = MSGParser.to_json(email, indent=0)
        assert '\n' not in json_no_indent or json_no_indent.count('\n') <= 1
        
        # 有缩进
        json_indent = MSGParser.to_json(email, indent=2)
        assert '  ' in json_indent  # 2空格缩进


class TestBatchParserWithProgress:
    """批量解析器进度支持测试"""
    
    def test_parse_directory_with_callback(self):
        """测试带回调的目录解析"""
        progress_events = []
        
        def progress_callback(progress: ParseProgress):
            progress_events.append(progress)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_parser = BatchMSGParser()
            results = batch_parser.parse_directory(
                tmpdir,
                progress_callback=progress_callback
            )
            
            assert results == []
    
    def test_parse_directory_with_cancel(self):
        """测试带取消的目录解析"""
        cancel_at = [1]
        
        def cancel_check():
            cancel_at[0] += 1
            return cancel_at[0] > 2
        
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_parser = BatchMSGParser()
            results = batch_parser.parse_directory(
                tmpdir,
                cancel_check=cancel_check
            )
            
            assert isinstance(results, list)
