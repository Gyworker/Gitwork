# -*- coding: utf-8 -*-
"""
磁盘空间监控器
监控磁盘空间，防止备份因空间不足失败
"""

import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SpaceWarning:
    """空间警告信息"""
    level: str  # 'normal', 'warning', 'critical'
    message: str
    action: Optional[str]
    free_space_gb: float
    total_space_gb: float
    used_percent: float


class DiskSpaceMonitor:
    """
    磁盘空间监控器
    
    功能：
    - 检查磁盘空间
    - 空间不足预警
    - 备份前空间检查
    """
    
    def __init__(self, min_free_space_gb: float = 1.0):
        """
        初始化监控器
        
        Args:
            min_free_space_gb: 最小可用空间（GB）
        """
        self.min_free_space = min_free_space_gb * 1024 * 1024 * 1024  # 转换为字节
    
    def check_space(self, path: str = '.') -> Dict[str, Any]:
        """
        检查指定路径的磁盘空间
        
        Args:
            path: 路径
            
        Returns:
            Dict: 空间信息
        """
        try:
            stat = shutil.disk_usage(path)
            
            total_gb = stat.total / (1024 ** 3)
            used_gb = stat.used / (1024 ** 3)
            free_gb = stat.free / (1024 ** 3)
            used_percent = (stat.used / stat.total) * 100 if stat.total > 0 else 0
            
            return {
                'total': stat.total,
                'used': stat.used,
                'free': stat.free,
                'total_gb': total_gb,
                'used_gb': used_gb,
                'free_gb': free_gb,
                'used_percent': used_percent
            }
        except Exception as e:
            logger.error(f"检查磁盘空间失败: {e}")
            return {
                'error': str(e)
            }
    
    def is_space_sufficient(self, path: str, required_size: int = None) -> bool:
        """
        检查空间是否充足
        
        Args:
            path: 路径
            required_size: 所需空间（字节），如果不指定则使用最小空间
            
        Returns:
            bool: 是否充足
        """
        required = required_size or self.min_free_space
        space_info = self.check_space(path)
        
        if 'error' in space_info:
            return False
        
        return space_info['free'] >= required
    
    def get_warning(self, path: str = '.') -> SpaceWarning:
        """
        获取空间警告信息
        
        Args:
            path: 路径
            
        Returns:
            SpaceWarning: 警告信息
        """
        space_info = self.check_space(path)
        
        if 'error' in space_info:
            return SpaceWarning(
                level='error',
                message=f"无法检查磁盘空间: {space_info['error']}",
                action=None,
                free_space_gb=0,
                total_space_gb=0,
                used_percent=0
            )
        
        free_gb = space_info['free_gb']
        used_percent = space_info['used_percent']
        
        if free_gb < 0.5:
            return SpaceWarning(
                level='critical',
                message=f'磁盘空间严重不足！剩余 {free_gb:.2f} GB',
                action='立即清理备份或联系管理员',
                free_space_gb=free_gb,
                total_space_gb=space_info['total_gb'],
                used_percent=used_percent
            )
        elif free_gb < 1.0:
            return SpaceWarning(
                level='warning',
                message=f'磁盘空间不足，剩余 {free_gb:.2f} GB',
                action='建议清理旧备份',
                free_space_gb=free_gb,
                total_space_gb=space_info['total_gb'],
                used_percent=used_percent
            )
        elif free_gb < 2.0:
            return SpaceWarning(
                level='caution',
                message=f'磁盘空间偏低，剩余 {free_gb:.2f} GB',
                action='可关注备份清理策略',
                free_space_gb=free_gb,
                total_space_gb=space_info['total_gb'],
                used_percent=used_percent
            )
        else:
            return SpaceWarning(
                level='normal',
                message=f'磁盘空间充足，剩余 {free_gb:.2f} GB',
                action=None,
                free_space_gb=free_gb,
                total_space_gb=space_info['total_gb'],
                used_percent=used_percent
            )
    
    def pre_backup_check(self, backup_path: str, estimated_size: int = None) -> SpaceWarning:
        """
        备份前空间检查
        
        Args:
            backup_path: 备份路径
            estimated_size: 预估备份大小（字节）
            
        Returns:
            SpaceWarning: 检查结果
        """
        warning = self.get_warning(backup_path)
        
        # 检查是否有足够空间进行备份
        required = estimated_size or (500 * 1024 * 1024)  # 默认500MB
        
        if warning.free_space_gb * 1024 * 1024 * 1024 < required:
            return SpaceWarning(
                level='critical',
                message=f'空间不足，无法创建备份。预估需要 {required / (1024**3):.2f} GB',
                action='清理磁盘空间后重试',
                free_space_gb=warning.free_space_gb,
                total_space_gb=warning.total_space_gb,
                used_percent=warning.used_percent
            )
        
        return warning
    
    def format_space_info(self, path: str = '.') -> str:
        """
        格式化磁盘空间信息
        
        Args:
            path: 路径
            
        Returns:
            str: 格式化字符串
        """
        space = self.check_space(path)
        
        if 'error' in space:
            return f"无法获取磁盘空间信息: {space['error']}"
        
        return (
            f"磁盘空间信息:\n"
            f"  总容量: {space['total_gb']:.2f} GB\n"
            f"  已使用: {space['used_gb']:.2f} GB ({space['used_percent']:.1f}%)\n"
            f"  可用空间: {space['free_gb']:.2f} GB"
        )
