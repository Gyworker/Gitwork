# -*- coding: utf-8 -*-
"""
轻量级重复检测算法
不依赖sklearn，使用简单字符串匹配
"""

import re
from typing import List, Tuple


class LightweightDetector:
    """
    轻量级重复检测器
    
    使用Jaccard相似度和包含关系检测
    适用于数据量较小（<10000条）的场景
    
    优点：
    - 无外部依赖
    - 运行速度快
    - 内存占用低
    """
    
    def __init__(self, threshold: float = 0.75):
        """
        初始化检测器
        
        Args:
            threshold: 相似度阈值
        """
        self.threshold = threshold
    
    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        计算两个文本的相似度
        
        使用Jaccard相似度和包含关系
        
        Args:
            name1: 文本1
            name2: 文本2
            
        Returns:
            float: 相似度 (0-1)
        """
        if not name1 or not name2:
            return 0.0
        
        # 转换为小写
        t1 = name1.lower().strip()
        t2 = name2.lower().strip()
        
        # 完全相同
        if t1 == t2:
            return 1.0
        
        # 包含关系检测（高权重）
        if t1 in t2 or t2 in t1:
            shorter_len = min(len(t1), len(t2))
            longer_len = max(len(t1), len(t2))
            return 0.8 + 0.2 * (shorter_len / longer_len)
        
        # Jaccard相似度（基于字符）
        set1 = set(t1)
        set2 = set(t2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        jaccard = intersection / union if union > 0 else 0.0
        
        # 分词后Jaccard
        words1 = set(self._tokenize(t1))
        words2 = set(self._tokenize(t2))
        word_intersection = len(words1 & words2)
        word_union = len(words1 | words2)
        word_jaccard = word_intersection / word_union if word_union > 0 else 0.0
        
        # 综合相似度
        return max(jaccard, word_jaccard * 0.9)
    
    def _tokenize(self, text: str) -> List[str]:
        """
        分词
        
        Args:
            text: 文本
            
        Returns:
            List[str]: 词语列表
        """
        # 中文分词（简单实现）
        # 移除非中文英文数字字符
        cleaned = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', ' ', text)
        
        # 按空格分割
        words = [w.strip() for w in cleaned.split() if w.strip()]
        
        # 英文按字符分割
        english_words = []
        for w in words:
            if w.isascii():
                english_words.extend(list(w.lower()))
            else:
                english_words.append(w)
        
        return english_words
    
    def detect_duplicates(self, tasks: List[dict]) -> List[Tuple[int, int, float]]:
        """
        检测重复任务
        
        Args:
            tasks: 任务列表
            
        Returns:
            List[Tuple[int, int, float]]: [(task1_id, task2_id, similarity), ...]
        """
        duplicates = []
        
        # 构建任务索引
        task_dict = {}
        for task in tasks:
            task_id = task.get('id')
            if task_id:
                task_dict[task_id] = task
        
        # 两两比较
        task_ids = list(task_dict.keys())
        n = len(task_ids)
        
        for i in range(n):
            for j in range(i + 1, n):
                task1_id = task_ids[i]
                task2_id = task_ids[j]
                task1 = task_dict[task1_id]
                task2 = task_dict[task2_id]
                
                # 计算名称相似度
                name1 = task1.get('name', '')
                name2 = task2.get('name', '')
                name_sim = self.calculate_name_similarity(name1, name2)
                
                # 计算咨询者相似度
                consultant1 = task1.get('consultant_name', '')
                consultant2 = task2.get('consultant_name', '')
                consultant_sim = self.calculate_name_similarity(consultant1, consultant2)
                
                # 计算电话相似度
                phone1 = self._normalize_phone(task1.get('consultant_phone', ''))
                phone2 = self._normalize_phone(task2.get('consultant_phone', ''))
                phone_sim = 1.0 if phone1 and phone2 and phone1 == phone2 else 0.0
                
                # 综合相似度
                overall_sim = (
                    0.5 * name_sim +
                    0.3 * consultant_sim +
                    0.2 * phone_sim
                )
                
                if overall_sim >= self.threshold:
                    duplicates.append((task1_id, task2_id, overall_sim))
        
        return duplicates
    
    def _normalize_phone(self, phone: str) -> str:
        """标准化电话号码"""
        if not phone:
            return ''
        return re.sub(r'[^\d]', '', phone)
    
    def calculate_contact_similarity(self, task1: dict, task2: dict) -> float:
        """
        计算咨询者相似度
        
        Args:
            task1: 任务1
            task2: 任务2
            
        Returns:
            float: 相似度
        """
        name_sim = self.calculate_name_similarity(
            task1.get('consultant_name', ''),
            task2.get('consultant_name', '')
        )
        
        phone_sim = 1.0 if (
            self._normalize_phone(task1.get('consultant_phone', '')) ==
            self._normalize_phone(task2.get('consultant_phone', ''))
        ) else 0.0
        
        return max(name_sim, phone_sim * 0.9)
