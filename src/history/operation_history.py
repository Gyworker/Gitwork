# -*- coding: utf-8 -*-
"""
操作历史记录器
记录用户在系统中的所有操作行为
"""

import json
import os
import re
import gzip
from datetime import datetime
from pathlib import Path
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
    
    def get_size(self) -> int:
        """获取记录大小（字节）"""
        return len(json.dumps(self.to_dict(), ensure_ascii=False))
    
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
    - 内存限制保护（自动保存到本地文件）
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
    
    # 内存限制配置
    DEFAULT_MEMORY_LIMIT = 10 * 1024  # 默认10KB
    DEFAULT_ARCHIVE_DIR = './data/history_archive'
    
    def __init__(
        self,
        db_connection=None,
        memory_limit_kb: int = None,
        archive_dir: str = None
    ):
        """
        初始化操作历史记录器
        
        Args:
            db_connection: 数据库连接对象
            memory_limit_kb: 内存限制（KB），超过此限制自动保存到文件
            archive_dir: 历史归档目录路径
        """
        self.db = db_connection
        self._records = []  # 内存存储（无数据库时使用）
        
        # 内存限制配置
        self._memory_limit = (memory_limit_kb or self.DEFAULT_MEMORY_LIMIT) * 1024
        self._archive_dir = archive_dir or self.DEFAULT_ARCHIVE_DIR
        
        # 初始化归档目录
        Path(self._archive_dir).mkdir(parents=True, exist_ok=True)
        
        # 当前内存使用量
        self._current_memory_size = 0
        
        # 归档文件列表
        self._archive_files: List[str] = []
    
    def _get_record_size(self, record: HistoryRecord) -> int:
        """计算单条记录大小"""
        return record.get_size()
    
    def _get_memory_usage(self) -> int:
        """计算当前内存使用量"""
        total_size = self._current_memory_size
        # 加上_records列表中所有记录的大小
        for record in self._records:
            total_size += self._get_record_size(record)
        return total_size
    
    def _save_to_archive_file(self, records: List[HistoryRecord]) -> str:
        """
        将记录保存到归档文件
        
        Args:
            records: 要保存的记录列表
            
        Returns:
            str: 归档文件路径
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_file = Path(self._archive_dir) / f'history_archive_{timestamp}.json.gz'
        
        data = [r.to_dict() for r in records]
        
        # 使用gzip压缩保存
        with gzip.open(archive_file, 'wt', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 更新归档文件列表
        self._archive_files.append(str(archive_file))
        
        # 清理超过30天的归档文件
        self._cleanup_archive_files()
        
        return str(archive_file)
    
    def _cleanup_archive_files(self, days: int = 30) -> int:
        """清理过期的归档文件"""
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        for archive_file in self._archive_files[:]:
            try:
                file_path = Path(archive_file)
                if file_path.exists():
                    # 获取文件修改时间
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff_time:
                        file_path.unlink()
                        self._archive_files.remove(archive_file)
                        deleted_count += 1
            except Exception:
                pass
        
        return deleted_count
    
    def _load_from_archive_file(self, archive_file: str) -> List[HistoryRecord]:
        """
        从归档文件加载记录
        
        Args:
            archive_file: 归档文件路径
            
        Returns:
            List[HistoryRecord]: 记录列表
        """
        try:
            with gzip.open(archive_file, 'rt', encoding='utf-8') as f:
                data = json.load(f)
                return [HistoryRecord.from_dict(item) for item in data]
        except Exception as e:
            print(f"加载归档文件失败: {e}")
            return []
    
    def _check_and_archive_if_needed(self) -> Optional[str]:
        """
        检查内存使用量，超过限制则保存到归档文件
        
        Returns:
            str: 归档文件路径，如果没有触发归档则返回None
        """
        current_usage = self._get_memory_usage()
        
        if current_usage >= self._memory_limit and self._records:
            # 保存当前内存中的所有记录到归档文件
            archive_file = self._save_to_archive_file(self._records)
            
            # 清空内存记录
            self._records.clear()
            self._current_memory_size = 0
            
            print(f"历史记录已自动归档到: {archive_file}")
            print(f"归档记录数: {len(self._records) if not archive_file else '已清空'}")
            
            return archive_file
        
        return None
    
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
            
            # 更新内存使用量
            self._current_memory_size += self._get_record_size(record)
            self._records.append(record)
            
            # 检查是否需要归档
            self._check_and_archive_if_needed()
        
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
    
    def get_all_records(self) -> List[HistoryRecord]:
        """获取所有记录（包含归档文件）"""
        all_records = self._records.copy()
        
        # 从归档文件加载记录
        for archive_file in self._archive_files:
            if Path(archive_file).exists():
                archived_records = self._load_from_archive_file(archive_file)
                all_records.extend(archived_records)
        
        # 按时间排序
        all_records.sort(key=lambda x: x.timestamp, reverse=True)
        return all_records
    
    def get_memory_status(self) -> Dict[str, Any]:
        """获取内存使用状态"""
        memory_usage = self._get_memory_usage()
        
        return {
            'current_records': len(self._records),
            'memory_usage_bytes': memory_usage,
            'memory_usage_kb': memory_usage / 1024,
            'memory_limit_bytes': self._memory_limit,
            'memory_limit_kb': self._memory_limit / 1024,
            'usage_percent': (memory_usage / self._memory_limit) * 100 if self._memory_limit > 0 else 0,
            'archive_files': len(self._archive_files),
            'archive_dir': self._archive_dir
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
            
            # 清理归档文件
            deleted_count += self._cleanup_archive_files(days)
        
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
            'recent_days': {},
            'memory_status': self.get_memory_status()
        }
        
        for r in self._records:
            # 按模块统计
            stats['by_module'][r.module] = stats['by_module'].get(r.module, 0) + 1
            # 按操作统计
            stats['by_action'][r.action] = stats['by_action'].get(r.action, 0) + 1
        
        return stats
