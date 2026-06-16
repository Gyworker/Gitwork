# -*- coding: utf-8 -*-
"""
操作历史模块单元测试
"""

import os
import sys
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.history.operation_history import OperationHistory, HistoryRecord
from src.history.sensitive_masker import SensitiveDataMasker
from src.history.batch_recorder import BatchOperationRecorder


class TestHistoryRecord:
    """历史记录数据类测试"""
    
    def test_create_record(self):
        """测试创建历史记录"""
        record = HistoryRecord(
            module='task',
            action='CREATE',
            target_type='task',
            target_id=1,
            target_name='测试任务'
        )
        
        assert record.module == 'task'
        assert record.action == 'CREATE'
        assert record.target_id == 1
        assert record.timestamp is not None
    
    def test_to_dict(self):
        """测试转换为字典"""
        record = HistoryRecord(
            module='contact',
            action='IMPORT',
            target_name='导入25条记录'
        )
        
        data = record.to_dict()
        assert isinstance(data, dict)
        assert data['module'] == 'contact'
        assert data['action'] == 'IMPORT'
        assert 'timestamp' in data
    
    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            'id': 1,
            'module': 'task',
            'action': 'UPDATE',
            'target_id': 100,
            'timestamp': '2026-06-16T10:00:00'
        }
        
        record = HistoryRecord.from_dict(data)
        assert record.id == 1
        assert record.module == 'task'
        assert record.target_id == 100


class TestOperationHistory:
    """操作历史记录器测试"""
    
    def test_init(self):
        """测试初始化"""
        history = OperationHistory()
        assert history is not None
        assert history._records == []
    
    def test_log_operation(self):
        """测试记录操作"""
        history = OperationHistory()
        
        record = history.log_operation(
            module='task',
            action='CREATE',
            target_type='task',
            target_id=1,
            target_name='测试任务'
        )
        
        assert record is not None
        assert record.module == 'task'
        assert record.action == 'CREATE'
        assert len(history._records) == 1
    
    def test_query_history(self):
        """测试查询历史"""
        history = OperationHistory()
        
        # 添加测试记录
        for i in range(5):
            history.log_operation(
                module='task' if i < 3 else 'contact',
                action='CREATE' if i % 2 == 0 else 'UPDATE',
                target_name=f'任务{i}'
            )
        
        # 查询全部
        result = history.query_history()
        assert result['total'] == 5
        assert len(result['data']) == 5
        
        # 按模块筛选
        result = history.query_history(module='task')
        assert result['total'] == 3
        assert len(result['data']) == 3
    
    def test_query_with_pagination(self):
        """测试分页查询"""
        history = OperationHistory()
        
        # 添加10条记录
        for i in range(10):
            history.log_operation(
                module='task',
                action='CREATE',
                target_name=f'任务{i}'
            )
        
        # 第一页
        result = history.query_history(page=1, page_size=3)
        assert len(result['data']) == 3
        assert result['page'] == 1
        assert result['total_pages'] == 4
        
        # 第二页
        result = history.query_history(page=2, page_size=3)
        assert len(result['data']) == 3
        assert result['page'] == 2
    
    def test_cleanup_old_records(self):
        """测试清理过期记录"""
        history = OperationHistory()
        
        # 添加记录
        for i in range(5):
            record = HistoryRecord(
                module='task',
                action='CREATE',
                target_name=f'任务{i}'
            )
            # 手动设置时间（最后一条设为100天前）
            if i == 4:
                record.timestamp = datetime.now() - timedelta(days=100)
            history._records.append(record)
        
        # 清理90天前的记录
        deleted = history.cleanup_old_records(days=90)
        assert deleted == 1
        assert len(history._records) == 4
    
    def test_export_history(self, tmp_path):
        """测试导出历史"""
        history = OperationHistory()
        
        # 添加记录
        history.log_operation(
            module='task',
            action='CREATE',
            target_name='测试任务'
        )
        
        # 导出为JSON
        export_path = tmp_path / 'history.json'
        result_path = history.export_history(
            format='json',
            path=str(export_path)
        )
        
        assert export_path.exists()
        
        # 验证内容
        import json
        with open(export_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]['module'] == 'task'


class TestSensitiveDataMasker:
    """敏感数据脱敏测试"""
    
    def test_mask_phone(self):
        """测试手机号脱敏"""
        assert SensitiveDataMasker.mask_phone('13800138000') == '138****8000'
        assert SensitiveDataMasker.mask_phone('+8613800138000') == '138****8000'
        assert SensitiveDataMasker.mask_phone('') == ''
        assert SensitiveDataMasker.mask_phone(None) is None
    
    def test_mask_email(self):
        """测试邮箱脱敏"""
        assert SensitiveDataMasker.mask_email('zhangsan@example.com') == 'zha***@example.com'
        assert SensitiveDataMasker.mask_email('ab@example.com') == '***@example.com'
        assert SensitiveDataMasker.mask_email('') == ''
        assert SensitiveDataMasker.mask_email(None) is None
    
    def test_mask_id_card(self):
        """测试身份证脱敏"""
        assert SensitiveDataMasker.mask_id_card('110101199001011234') == '11******34'
        assert SensitiveDataMasker.mask_id_card('') == ''
    
    def test_mask_bank_card(self):
        """测试银行卡脱敏"""
        assert SensitiveDataMasker.mask_bank_card('6222021234567890123') == '****0123'
        assert SensitiveDataMasker.mask_bank_card('') == ''
    
    def test_mask_name(self):
        """测试姓名脱敏"""
        assert SensitiveDataMasker.mask_name('张三') == '张*'
        assert SensitiveDataMasker.mask_name('李四王') == '李*王'
        assert SensitiveDataMasker.mask_name('') == ''
    
    def test_mask_dict(self):
        """测试字典脱敏"""
        data = {
            'name': '张三',
            'phone': '13800138000',
            'email': 'zhangsan@example.com'
        }
        
        masked = SensitiveDataMasker.mask_dict(data)
        
        assert masked['name'] == '张*'
        assert masked['phone'] == '138****8000'
        assert masked['email'] == 'zha***@example.com'


class TestBatchOperationRecorder:
    """批量操作记录器测试"""
    
    def test_record_batch_import(self):
        """测试批量导入记录"""
        history = OperationHistory()
        recorder = BatchOperationRecorder(history)
        
        # 小批量：记录详细信息
        records = [{'name': f'联系人{i}', 'id': i} for i in range(5)]
        record = recorder.record_batch_import(
            module='contact',
            count=5,
            source='Excel导入',
            records=records
        )
        
        assert record is not None
        assert record.action == 'IMPORT'
        assert '批量导入 5 条' in record.target_name
    
    def test_record_batch_delete(self):
        """测试批量删除记录"""
        history = OperationHistory()
        recorder = BatchOperationRecorder(history)
        
        target_ids = [1, 2, 3, 4, 5]
        record = recorder.record_batch_delete(
            module='task',
            count=5,
            target_ids=target_ids
        )
        
        assert record is not None
        assert record.action == 'DELETE'
        assert '批量删除' in record.target_name
        assert record.before_value is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
