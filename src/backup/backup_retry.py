# -*- coding: utf-8 -*-
"""
备份重试管理器
提供备份失败自动重试功能
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RetryRecord:
    """重试记录"""
    attempt: int = 0
    timestamp: datetime = None
    error: str = ''
    next_retry_at: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class BackupRetryManager:
    """
    备份重试管理器
    
    功能：
    - 备份失败自动重试
    - 记录重试历史
    - 支持自定义重试间隔
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_interval: int = 300,
        on_retry_callback: Callable[[int, str], None] = None
    ):
        """
        初始化重试管理器
        
        Args:
            max_retries: 最大重试次数
            retry_interval: 重试间隔（秒）
            on_retry_callback: 重试回调函数
        """
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        self.on_retry_callback = on_retry_callback
        
        # 重试记录
        self._retry_history: Dict[str, list] = {}
        self._retry_count: Dict[str, int] = {}
    
    def execute_with_retry(
        self,
        backup_id: str,
        backup_func: Callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行带重试的备份
        
        Args:
            backup_id: 备份ID
            backup_func: 备份函数
            *args, **kwargs: 传递给备份函数的参数
            
        Returns:
            Dict: 执行结果
        """
        # 初始化重试计数
        if backup_id not in self._retry_count:
            self._retry_count[backup_id] = 0
        
        # 检查是否在冷却期
        if backup_id in self._retry_history:
            last_retry = self._retry_history[backup_id][-1]
            if last_retry.next_retry_at:
                if datetime.now() < last_retry.next_retry_at:
                    remaining = (last_retry.next_retry_at - datetime.now()).seconds
                    return {
                        'success': False,
                        'error': 'in_cool_down',
                        'message': f'重试冷却中，还需等待 {remaining} 秒',
                        'next_retry_at': last_retry.next_retry_at.isoformat()
                    }
        
        # 执行备份
        while self._retry_count[backup_id] < self.max_retries:
            try:
                result = backup_func(*args, **kwargs)
                
                # 成功：重置计数并返回
                self._retry_count[backup_id] = 0
                return {
                    'success': True,
                    'result': result,
                    'attempts': self._retry_count[backup_id] + 1
                }
                
            except Exception as e:
                self._retry_count[backup_id] += 1
                error_msg = str(e)
                
                # 记录重试
                retry_record = RetryRecord(
                    attempt=self._retry_count[backup_id],
                    error=error_msg,
                    next_retry_at=datetime.now() + timedelta(seconds=self.retry_interval)
                )
                
                if backup_id not in self._retry_history:
                    self._retry_history[backup_id] = []
                self._retry_history[backup_id].append(retry_record)
                
                # 回调
                if self.on_retry_callback:
                    self.on_retry_callback(
                        self._retry_count[backup_id],
                        error_msg
                    )
                
                # 还有重试机会，等待后重试
                if self._retry_count[backup_id] < self.max_retries:
                    logger.warning(
                        f"备份 {backup_id} 失败 (尝试 {self._retry_count[backup_id]}/{self.max_retries}): "
                        f"{error_msg}，{self.retry_interval}秒后重试..."
                    )
                    time.sleep(self.retry_interval)
                else:
                    logger.error(
                        f"备份 {backup_id} 失败，已达到最大重试次数 "
                        f"({self.max_retries}/{self.max_retries})"
                    )
        
        # 所有重试都失败
        return {
            'success': False,
            'error': 'max_retries_exceeded',
            'message': f'备份失败，已重试 {self.max_retries} 次',
            'attempts': self.max_retries,
            'last_error': self._retry_history[backup_id][-1].error if self._retry_history.get(backup_id) else ''
        }
    
    def get_retry_status(self, backup_id: str) -> Dict[str, Any]:
        """
        获取备份重试状态
        
        Args:
            backup_id: 备份ID
            
        Returns:
            Dict: 重试状态
        """
        return {
            'backup_id': backup_id,
            'retry_count': self._retry_count.get(backup_id, 0),
            'max_retries': self.max_retries,
            'retry_history': [
                {
                    'attempt': r.attempt,
                    'timestamp': r.timestamp.isoformat(),
                    'error': r.error,
                    'next_retry_at': r.next_retry_at.isoformat() if r.next_retry_at else None
                }
                for r in self._retry_history.get(backup_id, [])
            ],
            'can_retry': self._retry_count.get(backup_id, 0) < self.max_retries
        }
    
    def reset_retry(self, backup_id: str) -> None:
        """
        重置重试计数
        
        Args:
            backup_id: 备份ID
        """
        self._retry_count[backup_id] = 0
        if backup_id in self._retry_history:
            self._retry_history[backup_id].clear()
    
    def clear_history(self) -> None:
        """清除所有重试历史"""
        self._retry_history.clear()
        self._retry_count.clear()
