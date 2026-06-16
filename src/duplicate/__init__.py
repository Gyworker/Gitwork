# -*- coding: utf-8 -*-
"""
重复任务检测模块
提供任务重复检测和合并功能
"""

from .duplicate_detector import DuplicateDetector, DuplicateGroup
from .lightweight_detector import LightweightDetector
from .merge_handler import MergeHandler

__all__ = [
    'DuplicateDetector',
    'DuplicateGroup',
    'LightweightDetector',
    'MergeHandler',
]
