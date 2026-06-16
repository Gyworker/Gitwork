# -*- coding: utf-8 -*-
"""
操作历史记录器
记录用户在系统中的所有操作行为
"""

import json
import re
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any


@dataclass
class HistoryRecord:
    """历史记录数据类"""
    id: Optional[int] = None
    timestamp: datetime = None
    user: str = 'local_user'
    module: str = ''
    action: str = ''
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    target_name: Optional[str] = None
    before_value: Optional[str] = None
    after_value: Optional[str] = None
    ip_address: str = '127.0.0.1'
    device_info: str = 'Windows Desktop'
    session_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.before_value and not isinstance(self.before_value, str):
            self.before_value = json.dumps(self.before_value, ensure_ascii=False)
        if self.after_value and not isinstance(self.after_value, str):
            self.after_value = json.dumps(self.after_value, ensure_ascii=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat() if self.timestamp else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoryRecord':
        """从字典创建"""
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class OperationHistory:
    """
    操作历史记录器
    
    功能：
    - 记录用户操作
    - 查询历史记录
    - 导出历史记录
    - 清理过期记录
    """
    
    # 操作类型定义
    ACTION_CREATE = 'CREATE'
    ACTION_UPDATE = 'UPDATE'
    ACTION_DELETE = 'DELETE'
    ACTION_IMPORT = 'IMPORT'
    ACTION_EXPORT = 'EXPORT'
    ACTION_LOGIN = 'LOGIN'
    ACTION_LOGOUT = 'LOGOUT'
    ACTION_MERGE = 'MERGE'
    ACTION_BACKUP = 'BACKUP'
    
    # 模块定义
    MODULE_TASK = 'task'
    MODULE_CONTACT = 'contact'
    MODULE_RECOMMENDATION = 'recommendation'
    MODULE_SYSTEM = 'system'
    
    def __init__(self, db_connection=None):
        """
        初始化操作历史记录器
        
        Args:
            db_connection: 数据库连接对象
        """
        self.db = db_connection
        self._records = []  # 内存存储（无数据库时使用）
    
    def log_operation(
        self,
        module: str,
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        target_name: Optional[str] = None,
        before_value: Any = None,
        after_value: Any = None,
        user: str = 'local_user'
    ) -> HistoryRecord:
        """
        记录操作
        
        Args:
            module: 模块名称
            action: 操作类型
            target_type: 目标类型
            target_id: 目标ID
            target_name: 目标名称
            before_value: 操作前值
            after_value: 操作后值
            user: 用户名
            
        Returns:
            HistoryRecord: 历史记录对象
        """
        record = HistoryRecord(
            module=module,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            before_value=before_value,
            after_value=after_value,
            user=user,
            timestamp=datetime.now()
        )
        
        # 如果有数据库连接，保存到数据库
        if self.db:
            self._save_to_db(record)
        else:
            # 保存到内存
            record.id = len(self._records) + 1
            self._records.append(record)
        
        return record
    
    def _save_to_db(self, record: HistoryRecord) -> None:
        """保存记录到数据库"""
        try:
            query = """
                INSERT INTO operation_history 
                (timestamp, user, module, action, target_type, target_id, 
                 target_name, before_value, after_value, ip_address, device_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                record.timestamp.isoformat(),
                record.user,
                record.module,
                record.action,
                record.target_type,
                record.target_id,
                record.target_name,
                record.before_value,
                record.after_value,
                record.ip_address,
                record.device_info
            )
            self.db.execute(query, params)
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    def query_history(
        self,
        module: Optional[str] = None,
        action: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        查询历史记录
        
        Args:
            module: 模块筛选
            action: 操作类型筛选
            start_time: 开始时间
            end_time: 结束时间
            keyword: 关键词搜索
            page: 页码
            page_size: 每页数量
            
        Returns:
            Dict: 查询结果
        """
        if self.db:
            return self._query_from_db(
                module, action, start_time, end_time, 
                keyword, page, page_size
            )
        else:
            return self._query_from_memory(
                module, action, start_time, end_time,
                keyword, page, page_size
            )
    
    def _query_from_db(
        self, module, action, start_time, end_time,
        keyword, page, page_size
    ) -> Dict[str, Any]:
        """从数据库查询"""
        conditions = []
        params = []
        
        if module:
            conditions.append("module = ?")
            params.append(module)
        if action:
            conditions.append("action = ?")
            params.append(action)
        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())
        if keyword:
            conditions.append("(target_name LIKE ? OR module LIKE ?)")
            params.extend([f'%{keyword}%', f'%{keyword}%'])
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 计算总数
        count_query = f"SELECT COUNT(*) FROM operation_history WHERE {where_clause}"
        cursor = self.db.execute(count_query, params)
        total = cursor.fetchone()[0] if cursor else 0
        
        # 分页查询
        offset = (page - 1) * page_size
        query = f"""
            SELECT * FROM operation_history 
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, offset])
        
        cursor = self.db.execute(query, params)
        rows = cursor.fetchall() if cursor else []
        
        records = []
        for row in rows:
            records.append(HistoryRecord(
                id=row[0],
                timestamp=datetime.fromisoformat(row[1]) if row[1] else None,
                user=row[2],
                module=row[3],
                action=row[4],
                target_type=row[5],
                target_id=row[6],
                target_name=row[7],
                before_value=row[8],
                after_value=row[9],
                ip_address=row[10] if len(row) > 10 else '127.0.0.1',
                device_info=row[11] if len(row) > 11 else 'Windows Desktop'
            ))
        
        return {
            'data': records,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
    
    def _query_from_memory(
        self, module, action, start_time, end_time,
        keyword, page, page_size
    ) -> Dict[str, Any]:
        """从内存查询"""
        filtered = self._records.copy()
        
        if module:
            filtered = [r for r in filtered if r.module == module]
        if action:
            filtered = [r for r in filtered if r.action == action]
        if start_time:
            filtered = [r for r in filtered if r.timestamp >= start_time]
        if end_time:
            filtered = [r for r in filtered if r.timestamp <= end_time]
        if keyword:
            filtered = [r for r in filtered 
                       if keyword.lower() in (r.target_name or '').lower()
                       or keyword.lower() in r.module.lower()]
        
        # 排序
        filtered.sort(key=lambda x: x.timestamp, reverse=True)
        
        total = len(filtered)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_records = filtered[start_idx:end_idx]
        
        return {
            'data': page_records,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
    
    def get_target_history(
        self, 
        target_type: str, 
        target_id: int
    ) -> List[HistoryRecord]:
        """获取指定目标的所有历史"""
        result = self.query_history(
            target_type=target_type,
            page=1,
            page_size=1000
        )
        
        return [r for r in result['data'] 
                if r.target_id == target_id]
    
    def export_history(
        self, 
        format: str = 'json',
        path: str = None,
        filters: Dict = None
    ) -> str:
        """
        导出历史记录
        
        Args:
            format: 导出格式 (json/csv)
            path: 保存路径
            filters: 筛选条件
            
        Returns:
            str: 导出文件路径
        """
        if filters is None:
            filters = {}
        
        result = self.query_history(**filters, page=1, page_size=100000)
        records = result['data']
        
        if format == 'json':
            return self._export_json(records, path)
        elif format == 'csv':
            return self._export_csv(records, path)
        else:
            raise ValueError(f"不支持的导出格式: {format}")
    
    def _export_json(self, records: List[HistoryRecord], path: str) -> str:
        """导出为JSON"""
        if path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            path = f'operation_history_{timestamp}.json'
        
        data = [r.to_dict() for r in records]
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return path
    
    def _export_csv(self, records: List[HistoryRecord], path: str) -> str:
        """导出为CSV"""
        if path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            path = f'operation_history_{timestamp}.csv'
        
        import csv
        
        with open(path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            # 写入表头
            writer.writerow([
                'ID', '时间', '用户', '模块', '操作', 
                '目标类型', '目标ID', '目标名称'
            ])
            # 写入数据
            for r in records:
                writer.writerow([
                    r.id, 
                    r.timestamp.strftime('%Y-%m-%d %H:%M:%S') if r.timestamp else '',
                    r.user, r.module, r.action,
                    r.target_type or '', r.target_id or '', r.target_name or ''
                ])
        
        return path
    
    def cleanup_old_records(self, days: int = 90) -> int:
        """
        清理过期记录
        
        Args:
            days: 保留天数
            
        Returns:
            int: 删除的记录数
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        if self.db:
            query = """
                DELETE FROM operation_history 
                WHERE timestamp < ?
            """
            try:
                cursor = self.db.execute(query, (cutoff_date.isoformat(),))
                deleted_count = cursor.rowcount if hasattr(cursor, 'rowcount') else 0
            except Exception as e:
                print(f"清理历史记录失败: {e}")
        else:
            old_count = len(self._records)
            self._records = [r for r in self._records if r.timestamp >= cutoff_date]
            deleted_count = old_count - len(self._records)
        
        return deleted_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计数据"""
        if self.db:
            return self._get_db_statistics()
        else:
            return self._get_memory_statistics()
    
    def _get_db_statistics(self) -> Dict[str, Any]:
        """从数据库获取统计"""
        stats = {
            'total_count': 0,
            'by_module': {},
            'by_action': {},
            'recent_days': {}
        }
        
        try:
            # 总数
            cursor = self.db.execute("SELECT COUNT(*) FROM operation_history")
            stats['total_count'] = cursor.fetchone()[0] if cursor else 0
            
            # 按模块统计
            cursor = self.db.execute("""
                SELECT module, COUNT(*) FROM operation_history 
                GROUP BY module
            """)
            for row in cursor.fetchall() if cursor else []:
                stats['by_module'][row[0]] = row[1]
            
            # 按操作统计
            cursor = self.db.execute("""
                SELECT action, COUNT(*) FROM operation_history 
                GROUP BY action
            """)
            for row in cursor.fetchall() if cursor else []:
                stats['by_action'][row[0]] = row[1]
                
        except Exception as e:
            print(f"获取统计数据失败: {e}")
        
        return stats
    
    def _get_memory_statistics(self) -> Dict[str, Any]:
        """从内存获取统计"""
        stats = {
            'total_count': len(self._records),
            'by_module': {},
            'by_action': {},
            'recent_days': {}
        }
        
        for r in self._records:
            # 按模块统计
            stats['by_module'][r.module] = stats['by_module'].get(r.module, 0) + 1
            # 按操作统计
            stats['by_action'][r.action] = stats['by_action'].get(r.action, 0) + 1
        
        return stats
