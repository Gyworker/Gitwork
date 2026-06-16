# -*- coding: utf-8 -*-
"""
批量操作记录器
对批量导入、导出、删除等操作进行优化记录
"""

import json
from datetime import datetime
from typing import Any, List, Dict, Optional
from .operation_history import OperationHistory, HistoryRecord


class BatchOperationRecorder:
    """
    批量操作记录器
    
    功能：
    - 批量导入记录（摘要形式）
    - 批量导出记录
    - 批量删除记录
    """
    
    # 批量操作阈值，超过此数量使用摘要记录
    DEFAULT_BATCH_THRESHOLD = 10
    
    def __init__(
        self, 
        history: OperationHistory,
        batch_threshold: int = None
    ):
        """
        初始化批量操作记录器
        
        Args:
            history: 操作历史记录器实例
            batch_threshold: 批量操作阈值
        """
        self.history = history
        self.batch_threshold = batch_threshold or self.DEFAULT_BATCH_THRESHOLD
    
    def record_batch_import(
        self,
        module: str,
        count: int,
        source: str,
        details: Dict[str, Any] = None,
        records: List[Dict] = None
    ) -> HistoryRecord:
        """
        记录批量导入操作
        
        Args:
            module: 模块名称
            count: 导入数量
            source: 数据来源
            details: 详细统计
            records: 详细记录（可选，用于小批量）
            
        Returns:
            HistoryRecord: 历史记录
        """
        if count <= self.batch_threshold and records:
            # 小批量：记录详细信息
            return self._record_detailed_import(
                module, count, source, records
            )
        else:
            # 大批量：记录摘要
            return self._record_summary_import(
                module, count, source, details
            )
    
    def _record_detailed_import(
        self,
        module: str,
        count: int,
        source: str,
        records: List[Dict]
    ) -> HistoryRecord:
        """记录详细导入信息"""
        summary = f"批量导入 {count} 条{self._get_module_name(module)}记录"
        
        after_value = {
            'count': count,
            'source': source,
            'records': [
                {'name': r.get('name', ''), 'id': r.get('id')}
                for r in records[:self.batch_threshold]
            ],
            'total_count': count
        }
        
        return self.history.log_operation(
            module=module,
            action=OperationHistory.ACTION_IMPORT,
            target_type=module,
            target_name=summary,
            after_value=after_value
        )
    
    def _record_summary_import(
        self,
        module: str,
        count: int,
        source: str,
        details: Dict[str, Any] = None
    ) -> HistoryRecord:
        """记录导入摘要"""
        module_name = self._get_module_name(module)
        summary = f"批量导入 {count} 条{module_name}记录"
        
        after_value = {
            'count': count,
            'source': source,
            'operation_type': 'BATCH',
            'status': 'success',
            'summary': summary
        }
        
        if details:
            after_value['details'] = details
        
        return self.history.log_operation(
            module=module,
            action=OperationHistory.ACTION_IMPORT,
            target_type=module,
            target_name=summary,
            after_value=after_value
        )
    
    def record_batch_delete(
        self,
        module: str,
        count: int,
        target_ids: List[int],
        target_names: List[str] = None
    ) -> HistoryRecord:
        """
        记录批量删除操作
        
        Args:
            module: 模块名称
            count: 删除数量
            target_ids: 被删除的目标ID列表
            target_names: 被删除的目标名称列表
            
        Returns:
            HistoryRecord: 历史记录
        """
        module_name = self._get_module_name(module)
        summary = f"批量删除 {count} 条{module_name}记录"
        
        # 只记录前N个ID，节省存储空间
        display_ids = target_ids[:self.batch_threshold]
        
        before_value = {
            'count': count,
            'operation_type': 'BATCH',
            'deleted_ids': display_ids,
            'total_count': count
        }
        
        if target_names:
            before_value['deleted_names'] = target_names[:self.batch_threshold]
        
        return self.history.log_operation(
            module=module,
            action=OperationHistory.ACTION_DELETE,
            target_type=module,
            target_name=summary,
            before_value=before_value
        )
    
    def record_batch_update(
        self,
        module: str,
        count: int,
        update_type: str,
        changes: Dict[str, Any] = None
    ) -> HistoryRecord:
        """
        记录批量更新操作
        
        Args:
            module: 模块名称
            count: 更新数量
            update_type: 更新类型（如：批量修改状态）
            changes: 变更内容
            
        Returns:
            HistoryRecord: 历史记录
        """
        module_name = self._get_module_name(module)
        summary = f"批量更新 {count} 条{module_name}记录：{update_type}"
        
        after_value = {
            'count': count,
            'operation_type': 'BATCH',
            'update_type': update_type,
            'changes': changes or {}
        }
        
        return self.history.log_operation(
            module=module,
            action=OperationHistory.ACTION_UPDATE,
            target_type=module,
            target_name=summary,
            after_value=after_value
        )
    
    def record_batch_export(
        self,
        module: str,
        count: int,
        export_path: str,
        export_format: str = 'excel'
    ) -> HistoryRecord:
        """
        记录批量导出操作
        
        Args:
            module: 模块名称
            count: 导出数量
            export_path: 导出文件路径
            export_format: 导出格式
            
        Returns:
            HistoryRecord: 历史记录
        """
        module_name = self._get_module_name(module)
        summary = f"导出 {count} 条{module_name}记录"
        
        after_value = {
            'count': count,
            'operation_type': 'BATCH',
            'export_format': export_format,
            'export_path': export_path
        }
        
        return self.history.log_operation(
            module=module,
            action=OperationHistory.ACTION_EXPORT,
            target_type=module,
            target_name=summary,
            after_value=after_value
        )
    
    def record_merge_operation(
        self,
        module: str,
        primary_id: int,
        merged_ids: List[int],
        merge_type: str = 'duplicate_merge'
    ) -> HistoryRecord:
        """
        记录合并操作
        
        Args:
            module: 模块名称
            primary_id: 合并后的主记录ID
            merged_ids: 被合并的记录ID列表
            merge_type: 合并类型
            
        Returns:
            HistoryRecord: 历史记录
        """
        module_name = self._get_module_name(module)
        summary = f"合并 {len(merged_ids)} 条{module_name}记录"
        
        before_value = {
            'merged_ids': merged_ids,
            'merge_type': merge_type
        }
        
        after_value = {
            'primary_id': primary_id,
            'merged_count': len(merged_ids),
            'merge_type': merge_type
        }
        
        return self.history.log_operation(
            module=module,
            action=OperationHistory.ACTION_MERGE,
            target_type=module,
            target_id=primary_id,
            target_name=summary,
            before_value=before_value,
            after_value=after_value
        )
    
    def _get_module_name(self, module: str) -> str:
        """获取模块显示名称"""
        module_names = {
            OperationHistory.MODULE_TASK: '任务',
            OperationHistory.MODULE_CONTACT: '联系人',
            OperationHistory.MODULE_RECOMMENDATION: '推荐库',
            OperationHistory.MODULE_SYSTEM: '系统',
            'task': '任务',
            'contact': '联系人',
            'contacts': '联系人',
            'recommendation': '推荐库',
            'recommendations': '推荐库',
        }
        return module_names.get(module, module)
