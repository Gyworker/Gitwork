# -*- coding: utf-8 -*-
"""
重复任务检测器
检测重复任务并支持合并
"""

import re
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod


@dataclass
class DuplicateGroup:
    """重复任务组"""
    group_id: str
    task1_id: int
    task2_id: int
    similarity: float
    factors: Dict[str, float] = field(default_factory=dict)
    status: str = 'pending'  # pending, auto_merged, confirmed, ignored
    detected_at: datetime = None
    merged_at: Optional[datetime] = None
    merged_into: Optional[int] = None
    
    def __post_init__(self):
        if self.detected_at is None:
            self.detected_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'group_id': self.group_id,
            'task1_id': self.task1_id,
            'task2_id': self.task2_id,
            'similarity': self.similarity,
            'factors': self.factors,
            'status': self.status,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'merged_at': self.merged_at.isoformat() if self.merged_at else None,
            'merged_into': self.merged_into
        }


class DuplicateDetectionAlgorithm(ABC):
    """重复检测算法基类"""
    
    @abstractmethod
    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """计算名称相似度"""
        pass
    
    @abstractmethod
    def detect_duplicates(self, tasks: List[Dict]) -> List[Tuple[int, int, float]]:
        """检测重复任务对"""
        pass


class DuplicateDetector:
    """
    重复任务检测器
    
    功能：
    - 检测重复任务
    - 支持多种检测算法
    - 计算相似度
    """
    
    # 相似度阈值
    DEFAULT_THRESHOLD = 0.75
    AUTO_MERGE_THRESHOLD = 0.95
    MANUAL_CONFIRM_THRESHOLD = 0.85
    
    def __init__(
        self,
        threshold: float = None,
        auto_merge_threshold: float = None,
        manual_confirm_threshold: float = None,
        algorithm: str = 'lightweight'
    ):
        """
        初始化检测器
        
        Args:
            threshold: 相似度阈值
            auto_merge_threshold: 自动合并阈值
            manual_confirm_threshold: 手动确认阈值
            algorithm: 检测算法 ('lightweight' 或 'tfidf')
        """
        self.threshold = threshold or self.DEFAULT_THRESHOLD
        self.auto_merge_threshold = auto_merge_threshold or self.AUTO_MERGE_THRESHOLD
        self.manual_confirm_threshold = manual_confirm_threshold or self.MANUAL_CONFIRM_THRESHOLD
        
        # 使用轻量级算法
        self._detector = self._create_detector(algorithm)
    
    def _create_detector(self, algorithm: str) -> DuplicateDetectionAlgorithm:
        """创建检测算法实例"""
        if algorithm == 'tfidf':
            # TF-IDF算法（需要sklearn）
            try:
                from .tfidf_detector import TFIDFDetector
                return TFIDFDetector(self.threshold)
            except ImportError:
                pass
        
        # 默认使用轻量级算法
        from .lightweight_detector import LightweightDetector
        return LightweightDetector(self.threshold)
    
    def detect_duplicates(
        self,
        tasks: List[Dict],
        include_auto_merge: bool = True
    ) -> List[DuplicateGroup]:
        """
        检测重复任务
        
        Args:
            tasks: 任务列表
            include_auto_merge: 是否包含自动合并
            
        Returns:
            List[DuplicateGroup]: 重复组列表
        """
        duplicates = []
        duplicate_pairs = self._detector.detect_duplicates(tasks)
        
        for task1_id, task2_id, similarity in duplicate_pairs:
            # 获取任务信息
            task1 = self._find_task(tasks, task1_id)
            task2 = self._find_task(tasks, task2_id)
            
            if not task1 or not task2:
                continue
            
            # 计算各项相似度
            factors = self._calculate_factors(task1, task2)
            
            # 创建重复组
            group = DuplicateGroup(
                group_id=f"dup_{task1_id}_{task2_id}_{int(datetime.now().timestamp())}",
                task1_id=task1_id,
                task2_id=task2_id,
                similarity=similarity,
                factors=factors,
                status=self._get_initial_status(similarity)
            )
            
            duplicates.append(group)
        
        # 按相似度排序
        duplicates.sort(key=lambda x: x.similarity, reverse=True)
        
        return duplicates
    
    def _find_task(self, tasks: List[Dict], task_id: int) -> Optional[Dict]:
        """查找任务"""
        for task in tasks:
            if task.get('id') == task_id:
                return task
        return None
    
    def _calculate_factors(self, task1: Dict, task2: Dict) -> Dict[str, float]:
        """计算各项相似度因素"""
        factors = {}
        
        # 名称相似度
        name1 = task1.get('name', '')
        name2 = task2.get('name', '')
        factors['name'] = self._detector.calculate_name_similarity(name1, name2)
        
        # 咨询者相似度
        consultant1 = task1.get('consultant_name', '')
        consultant2 = task2.get('consultant_name', '')
        factors['consultant'] = self._detector.calculate_name_similarity(consultant1, consultant2)
        
        # 电话相似度
        phone1 = self._normalize_phone(task1.get('consultant_phone', ''))
        phone2 = self._normalize_phone(task2.get('consultant_phone', ''))
        factors['phone'] = 1.0 if phone1 and phone2 and phone1 == phone2 else 0.0
        
        # 时间接近度
        time1 = task1.get('created_at')
        time2 = task2.get('created_at')
        factors['time'] = self._calculate_time_proximity(time1, time2)
        
        return factors
    
    def _calculate_time_proximity(self, time1: Any, time2: Any) -> float:
        """计算时间接近度"""
        if not time1 or not time2:
            return 0.0
        
        # 转换为datetime
        if isinstance(time1, str):
            try:
                time1 = datetime.fromisoformat(time1)
            except:
                return 0.0
        if isinstance(time2, str):
            try:
                time2 = datetime.fromisoformat(time2)
            except:
                return 0.0
        
        # 计算时间差（天）
        time_diff = abs((time1 - time2).total_seconds()) / (24 * 3600)
        
        # 7天内为高接近度，7-30天为中等，30天以上为低
        if time_diff <= 7:
            return 1.0
        elif time_diff <= 30:
            return 0.5
        else:
            return 0.0
    
    def _normalize_phone(self, phone: str) -> str:
        """标准化电话号码"""
        if not phone:
            return ''
        return re.sub(r'[^\d]', '', phone)
    
    def _get_initial_status(self, similarity: float) -> str:
        """根据相似度确定初始状态"""
        if similarity >= self.auto_merge_threshold:
            return 'auto_merge_pending'
        elif similarity >= self.manual_confirm_threshold:
            return 'pending'
        else:
            return 'need_review'
    
    def get_merge_recommendation(self, group: DuplicateGroup) -> Dict[str, Any]:
        """
        获取合并建议
        
        Args:
            group: 重复组
            
        Returns:
            Dict: 合并建议
        """
        task1_data = {
            'id': group.task1_id,
            'importance': 'high',  # 需要从实际数据获取
            'created_at': datetime.now(),
            'reminder_count': 0
        }
        
        task2_data = {
            'id': group.task2_id,
            'importance': 'medium',
            'created_at': datetime.now() - timedelta(days=1),
            'reminder_count': 5
        }
        
        # 决定保留哪个任务
        primary_id, merged_id = self._decide_primary_task(group)
        
        return {
            'primary_task_id': primary_id,
            'merged_task_id': merged_id,
            'merge_action': 'auto' if group.similarity >= self.auto_merge_threshold else 'manual',
            'similarity': group.similarity,
            'factors': group.factors
        }
    
    def _decide_primary_task(
        self,
        group: DuplicateGroup
    ) -> Tuple[int, int]:
        """
        决定保留哪个任务
        
        规则：
        1. 保留重要程度高的
        2. 保留创建时间早的
        3. 保留ID较小的
        """
        # 这里应该从数据库获取实际任务信息
        # 简化处理：task1_id < task2_id 时保留task1
        if group.task1_id < group.task2_id:
            return group.task1_id, group.task2_id
        else:
            return group.task2_id, group.task1_id
    
    def calculate_overall_similarity(self, factors: Dict[str, float]) -> float:
        """
        计算总体相似度
        
        Args:
            factors: 各项相似度因素
            
        Returns:
            float: 总体相似度
        """
        weights = {
            'name': 0.4,
            'consultant': 0.2,
            'phone': 0.1,
            'time': 0.2,
            'content': 0.1
        }
        
        total = 0.0
        for key, weight in weights.items():
            value = factors.get(key, 0.0)
            total += value * weight
        
        return total
