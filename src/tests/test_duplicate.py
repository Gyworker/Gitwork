# -*- coding: utf-8 -*-
"""
重复任务检测模块单元测试
"""

import os
import sys
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.duplicate.duplicate_detector import DuplicateDetector, DuplicateGroup
from src.duplicate.lightweight_detector import LightweightDetector
from src.duplicate.merge_handler import MergeHandler, MergeRecord


class TestLightweightDetector:
    """轻量级检测器测试"""
    
    def test_init(self):
        """测试初始化"""
        detector = LightweightDetector(threshold=0.8)
        assert detector.threshold == 0.8
    
    def test_calculate_name_similarity_exact(self):
        """测试完全相同的名称"""
        detector = LightweightDetector()
        
        sim = detector.calculate_name_similarity('产品报价咨询', '产品报价咨询')
        assert sim == 1.0
    
    def test_calculate_name_similarity_contains(self):
        """测试包含关系"""
        detector = LightweightDetector()
        
        sim = detector.calculate_name_similarity('产品报价咨询', '产品报价咨询-紧急')
        assert sim > 0.8  # 应该高于包含关系的基准分
    
    def test_calculate_name_similarity_different(self):
        """测试完全不同的名称"""
        detector = LightweightDetector()
        
        sim = detector.calculate_name_similarity('产品报价', '技术支持')
        assert sim < 0.5
    
    def test_calculate_name_similarity_empty(self):
        """测试空名称"""
        detector = LightweightDetector()
        
        assert detector.calculate_name_similarity('', '测试') == 0.0
        assert detector.calculate_name_similarity('测试', '') == 0.0
        assert detector.calculate_name_similarity('', '') == 0.0
    
    def test_detect_duplicates(self):
        """测试重复检测"""
        detector = LightweightDetector(threshold=0.7)
        
        tasks = [
            {'id': 1, 'name': '产品报价咨询', 'consultant_name': '张三'},
            {'id': 2, 'name': '产品报价咨询', 'consultant_name': '张三'},
            {'id': 3, 'name': '技术支持', 'consultant_name': '李四'},
        ]
        
        duplicates = detector.detect_duplicates(tasks)
        
        # 任务1和任务2应该被识别为重复
        assert len(duplicates) >= 1
        
        # 检查是否有任务1和2的重复
        dup_pair = None
        for t1_id, t2_id, sim in duplicates:
            if (t1_id == 1 and t2_id == 2) or (t1_id == 2 and t2_id == 1):
                dup_pair = (t1_id, t2_id, sim)
                break
        
        assert dup_pair is not None
        assert dup_pair[2] > 0.7


class TestDuplicateDetector:
    """重复任务检测器测试"""
    
    def test_init_default(self):
        """测试默认初始化"""
        detector = DuplicateDetector()
        
        assert detector.threshold == 0.75
        assert detector.auto_merge_threshold == 0.95
        assert detector.manual_confirm_threshold == 0.85
    
    def test_init_custom(self):
        """测试自定义初始化"""
        detector = DuplicateDetector(
            threshold=0.8,
            auto_merge_threshold=0.9,
            manual_confirm_threshold=0.85
        )
        
        assert detector.threshold == 0.8
        assert detector.auto_merge_threshold == 0.9
        assert detector.manual_confirm_threshold == 0.85
    
    def test_detect_duplicates(self):
        """测试重复检测"""
        detector = DuplicateDetector(threshold=0.7)
        
        tasks = [
            {'id': 1, 'name': '产品报价咨询', 'consultant_name': '张三'},
            {'id': 2, 'name': '产品报价咨询', 'consultant_name': '张三'},
            {'id': 3, 'name': '技术支持', 'consultant_name': '李四'},
        ]
        
        groups = detector.detect_duplicates(tasks)
        
        assert len(groups) >= 1
        assert isinstance(groups[0], DuplicateGroup)


class TestDuplicateGroup:
    """重复任务组测试"""
    
    def test_create_group(self):
        """测试创建重复组"""
        group = DuplicateGroup(
            group_id='dup_1_2_1000',
            task1_id=1,
            task2_id=2,
            similarity=0.85,
            factors={'name': 1.0, 'consultant': 0.7}
        )
        
        assert group.group_id == 'dup_1_2_1000'
        assert group.task1_id == 1
        assert group.task2_id == 2
        assert group.similarity == 0.85
        assert group.status == 'pending'
    
    def test_to_dict(self):
        """测试转换为字典"""
        group = DuplicateGroup(
            group_id='dup_1_2_1000',
            task1_id=1,
            task2_id=2,
            similarity=0.85
        )
        
        data = group.to_dict()
        
        assert isinstance(data, dict)
        assert data['group_id'] == 'dup_1_2_1000'
        assert data['similarity'] == 0.85
        assert 'detected_at' in data


class TestMergeHandler:
    """合并处理器测试"""
    
    def test_init(self):
        """测试初始化"""
        handler = MergeHandler()
        
        assert handler is not None
        assert handler._merge_records == []
    
    def test_merge_tasks(self):
        """测试合并任务"""
        handler = MergeHandler()
        
        record = handler.merge_tasks(
            primary_task_id=1,
            merged_task_ids=[2, 3],
            merged_by='test'
        )
        
        assert record is not None
        assert record.primary_task_id == 1
        assert record.merged_task_ids == [2, 3]
        assert record.merged_by == 'test'
        assert record.status == 'confirmed'
        assert len(handler._merge_records) == 1
    
    def test_undo_merge(self):
        """测试撤销合并"""
        handler = MergeHandler()
        
        # 合并任务
        record = handler.merge_tasks(
            primary_task_id=1,
            merged_task_ids=[2]
        )
        
        # 撤销
        result = handler.undo_merge(record.merge_id)
        
        assert result == True
        assert record.status == 'undone'
        assert record.undo_available == False
    
    def test_cannot_undo_twice(self):
        """测试不能重复撤销"""
        handler = MergeHandler()
        
        record = handler.merge_tasks(
            primary_task_id=1,
            merged_task_ids=[2]
        )
        
        # 第一次撤销
        handler.undo_merge(record.merge_id)
        
        # 第二次撤销应该失败
        result = handler.undo_merge(record.merge_id)
        assert result == False
    
    def test_get_merge_history(self):
        """测试获取合并历史"""
        handler = MergeHandler()
        
        # 添加合并记录
        handler.merge_tasks(primary_task_id=1, merged_task_ids=[2])
        handler.merge_tasks(primary_task_id=3, merged_task_ids=[4])
        
        history = handler.get_merge_history()
        
        assert len(history) == 2
    
    def test_get_merge_history_by_task(self):
        """测试按任务筛选合并历史"""
        handler = MergeHandler()
        
        handler.merge_tasks(primary_task_id=1, merged_task_ids=[2])
        handler.merge_tasks(primary_task_id=3, merged_task_ids=[4])
        
        history = handler.get_merge_history(task_id=1)
        
        assert len(history) == 1
        assert history[0].primary_task_id == 1
    
    def test_get_merge_stats(self):
        """测试获取合并统计"""
        handler = MergeHandler()
        
        handler.merge_tasks(primary_task_id=1, merged_task_ids=[2])
        handler.merge_tasks(primary_task_id=3, merged_task_ids=[4])
        
        stats = handler.get_merge_stats()
        
        assert stats['total_merges'] == 2
        assert stats['undoable_count'] == 2
        assert 'by_status' in stats
    
    def test_can_undo(self):
        """测试检查是否可以撤销"""
        handler = MergeHandler()
        
        record = handler.merge_tasks(
            primary_task_id=1,
            merged_task_ids=[2]
        )
        
        assert handler.can_undo(record.merge_id) == True
        
        handler.undo_merge(record.merge_id)
        
        assert handler.can_undo(record.merge_id) == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
