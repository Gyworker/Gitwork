# -*- coding: utf-8 -*-
"""
任务合并处理器
处理任务合并和撤销操作
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class MergeStatus(Enum):
    """合并状态"""
    PENDING = 'pending'
    AUTO_MERGED = 'auto_merged'
    CONFIRMED = 'confirmed'
    IGNORED = 'ignored'
    UNDONE = 'undone'


@dataclass
class MergeRecord:
    """合并记录"""
    merge_id: str
    primary_task_id: int
    merged_task_ids: List[int]
    merged_at: datetime
    merged_by: str = 'system'
    status: str = MergeStatus.CONFIRMED.value
    undo_available: bool = True
    original_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'merge_id': self.merge_id,
            'primary_task_id': self.primary_task_id,
            'merged_task_ids': self.merged_task_ids,
            'merged_at': self.merged_at.isoformat(),
            'merged_by': self.merged_by,
            'status': self.status,
            'undo_available': self.undo_available,
            'original_data': self.original_data
        }


class MergeHandler:
    """
    任务合并处理器
    
    功能：
    - 执行任务合并
    - 撤销合并操作
    - 记录合并历史
    """
    
    def __init__(self, db_connection=None):
        """
        初始化合并处理器
        
        Args:
            db_connection: 数据库连接
        """
        self.db = db_connection
        self._merge_records: List[MergeRecord] = []
    
    def merge_tasks(
        self,
        primary_task_id: int,
        merged_task_ids: List[int],
        merged_by: str = 'system',
        task_data: Dict[int, Dict] = None
    ) -> MergeRecord:
        """
        合并任务
        
        Args:
            primary_task_id: 主任务ID（保留）
            merged_task_ids: 被合并的任务ID列表
            merged_by: 合并操作者
            task_data: 任务数据（用于撤销）
            
        Returns:
            MergeRecord: 合并记录
        """
        # 保存原始数据（用于撤销）
        original_data = {}
        if task_data:
            for task_id in merged_task_ids:
                if task_id in task_data:
                    original_data[task_id] = task_data[task_id].copy()
        
        # 创建合并记录
        merge_record = MergeRecord(
            merge_id=f"merge_{primary_task_id}_{int(datetime.now().timestamp())}",
            primary_task_id=primary_task_id,
            merged_task_ids=merged_task_ids,
            merged_at=datetime.now(),
            merged_by=merged_by,
            original_data=original_data
        )
        
        # 执行合并逻辑
        self._execute_merge(merge_record)
        
        # 保存记录
        self._merge_records.append(merge_record)
        
        # 保存到数据库
        if self.db:
            self._save_to_db(merge_record)
        
        return merge_record
    
    def _execute_merge(self, record: MergeRecord) -> None:
        """执行合并"""
        # 这里应该执行实际的数据库合并操作
        # 1. 更新主任务（合并内容）
        # 2. 标记被合并任务为归档状态
        # 3. 记录操作历史
        pass
    
    def undo_merge(self, merge_id: str) -> bool:
        """
        撤销合并
        
        Args:
            merge_id: 合并ID
            
        Returns:
            bool: 是否成功
        """
        # 查找合并记录
        record = None
        for r in self._merge_records:
            if r.merge_id == merge_id:
                record = r
                break
        
        if not record:
            return False
        
        if not record.undo_available:
            return False
        
        # 恢复原始数据
        if record.original_data:
            self._restore_tasks(record.original_data)
        
        # 更新记录状态
        record.status = MergeStatus.UNDONE.value
        record.undo_available = False
        
        # 更新数据库
        if self.db:
            self._update_db_record(record)
        
        return True
    
    def _restore_tasks(self, original_data: Dict[int, Dict]) -> None:
        """恢复任务数据"""
        # 恢复被合并的任务
        for task_id, task_data in original_data.items():
            # 将归档状态的任务恢复为正常状态
            # 更新任务数据
            pass
    
    def get_merge_history(
        self,
        task_id: int = None,
        status: str = None
    ) -> List[MergeRecord]:
        """
        获取合并历史
        
        Args:
            task_id: 任务ID（筛选）
            status: 状态（筛选）
            
        Returns:
            List[MergeRecord]: 合并记录列表
        """
        results = self._merge_records.copy()
        
        if task_id:
            results = [
                r for r in results
                if r.primary_task_id == task_id or task_id in r.merged_task_ids
            ]
        
        if status:
            results = [r for r in results if r.status == status]
        
        # 按时间倒序
        results.sort(key=lambda x: x.merged_at, reverse=True)
        
        return results
    
    def _save_to_db(self, record: MergeRecord) -> None:
        """保存合并记录到数据库"""
        try:
            query = """
                INSERT INTO merge_records
                (merge_id, primary_task_id, merged_task_ids, merged_at, merged_by, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (
                record.merge_id,
                record.primary_task_id,
                json.dumps(record.merged_task_ids),
                record.merged_at.isoformat(),
                record.merged_by,
                record.status
            )
            self.db.execute(query, params)
        except Exception as e:
            print(f"保存合并记录失败: {e}")
    
    def _update_db_record(self, record: MergeRecord) -> None:
        """更新数据库中的合并记录"""
        try:
            query = """
                UPDATE merge_records
                SET status = ?, undo_available = ?
                WHERE merge_id = ?
            """
            params = (record.status, 1 if record.undo_available else 0, record.merge_id)
            self.db.execute(query, params)
        except Exception as e:
            print(f"更新合并记录失败: {e}")
    
    def get_merge_stats(self) -> Dict[str, Any]:
        """获取合并统计"""
        total = len(self._merge_records)
        by_status = {}
        
        for record in self._merge_records:
            status = record.status
            by_status[status] = by_status.get(status, 0) + 1
        
        undoable = sum(1 for r in self._merge_records if r.undo_available)
        
        return {
            'total_merges': total,
            'by_status': by_status,
            'undoable_count': undoable,
            'undone_count': by_status.get(MergeStatus.UNDONE.value, 0)
        }
    
    def can_undo(self, merge_id: str) -> bool:
        """检查是否可以撤销"""
        for record in self._merge_records:
            if record.merge_id == merge_id:
                return record.undo_available
        return False
