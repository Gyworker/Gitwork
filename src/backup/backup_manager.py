# -*- coding: utf-8 -*-
"""
备份管理器
提供数据备份、还原、调度功能
"""

import os
import json
import zipfile
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Callable


@dataclass
class BackupRecord:
    """备份记录数据类"""
    id: Optional[int] = None
    backup_id: str = ''
    backup_time: datetime = None
    file_path: str = ''
    file_size: int = 0
    checksum: str = ''
    status: str = 'pending'
    error_message: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.backup_time is None:
            self.backup_time = datetime.now()
        if self.created_at is None:
            self.created_at = datetime.now()
        if not self.backup_id:
            self.backup_id = self.backup_time.strftime('%Y%m%d%H%M%S')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['backup_time'] = self.backup_time.isoformat() if self.backup_time else None
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        return data


class BackupManager:
    """
    备份管理器
    
    功能：
    - 创建备份（支持压缩）
    - 还原备份
    - 备份调度
    - 备份验证
    - 备份清理
    """
    
    # 备份文件包含的内容
    DEFAULT_INCLUDES = [
        'tasks.db',
        'contacts.db',
        'recommendations.db',
        'config.yaml',
        'mapping_rules.xlsx',
    ]
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化备份管理器"""
        self.config = config or self._default_config()
        self.backup_path = Path(self.config.get('backup_path', './backups'))
        self.backup_path.mkdir(parents=True, exist_ok=True)
        self._records: List[BackupRecord] = []
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            'enabled': True,
            'auto_backup': True,
            'backup_interval': 4,
            'max_backups': 10,
            'backup_path': './backups',
            'compression': True,
            'retry': {
                'enabled': True,
                'max_retries': 3,
                'retry_interval': 300,
            },
            'disk_space': {
                'min_free_space_gb': 1.0,
                'auto_cleanup': True,
            }
        }
    
    def create_backup(
        self,
        data_dir: str = './data',
        include_ocr: bool = False,
        progress_callback: Callable[[int, str], None] = None
    ) -> BackupRecord:
        """创建备份"""
        backup_time = datetime.now()
        backup_id = backup_time.strftime('%Y%m%d%H%M%S')
        
        record = BackupRecord(
            backup_id=backup_id,
            backup_time=backup_time,
            status='in_progress'
        )
        
        try:
            if progress_callback:
                progress_callback(0, '开始创建备份...')
            
            files_to_backup = self._collect_files(data_dir, include_ocr)
            
            if progress_callback:
                progress_callback(70, '正在压缩文件...')
            
            backup_file = self._create_archive(backup_id, files_to_backup)
            checksum = self._calculate_checksum(backup_file)
            
            record.file_path = str(backup_file)
            record.file_size = backup_file.stat().st_size
            record.checksum = checksum
            record.status = 'success'
            
            if progress_callback:
                progress_callback(100, f'备份完成: {backup_file.name}')
            
            if self.config.get('disk_space', {}).get('auto_cleanup', True):
                self._cleanup_old_backups()
            
        except Exception as e:
            record.status = 'failed'
            record.error_message = str(e)
            if progress_callback:
                progress_callback(-1, f'备份失败: {e}')
        
        self._records.append(record)
        return record
    
    def _collect_files(self, data_dir: str, include_ocr: bool) -> List[Dict[str, Any]]:
        """收集要备份的文件"""
        files = []
        data_path = Path(data_dir)
        
        if not data_path.exists():
            data_path = Path('.')
        
        for filename in self.DEFAULT_INCLUDES:
            file_path = data_path / filename
            if file_path.exists():
                files.append({
                    'path': file_path,
                    'name': filename,
                    'size': file_path.stat().st_size
                })
        
        if include_ocr:
            ocr_dir = data_path / 'imports' / 'ocr_results'
            if ocr_dir.exists():
                one_week_ago = datetime.now().timestamp() - 7 * 24 * 3600
                for file_path in ocr_dir.glob('*.xlsx'):
                    if file_path.stat().st_mtime >= one_week_ago:
                        files.append({
                            'path': file_path,
                            'name': f'ocr_results/{file_path.name}',
                            'size': file_path.stat().st_size
                        })
        
        return files
    
    def _create_archive(self, backup_id: str, files: List[Dict[str, Any]]) -> Path:
        """创建备份压缩包"""
        if self.config.get('compression', True):
            backup_file = self.backup_path / f"Gitwork_backup_{backup_id}.zip"
            
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_info in files:
                    zf.write(file_info['path'], file_info['name'])
        else:
            backup_dir = self.backup_path / f"Gitwork_backup_{backup_id}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            for file_info in files:
                dest = backup_dir / file_info['name']
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_info['path'], dest)
            
            backup_file = backup_dir
        
        return backup_file
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """计算文件校验和"""
        md5 = hashlib.md5()
        
        if file_path.suffix == '.zip':
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    md5.update(chunk)
        else:
            for src_file in file_path.rglob('*'):
                if src_file.is_file():
                    with open(src_file, 'rb') as f:
                        md5.update(f.read())
        
        return md5.hexdigest()
    
    def restore_backup(
        self,
        backup_file: str,
        restore_dir: str = './data',
        progress_callback: Callable[[int, str], None] = None
    ) -> bool:
        """还原备份"""
        try:
            backup_path = Path(backup_file)
            restore_path = Path(restore_dir)
            
            if not backup_path.exists():
                raise FileNotFoundError(f"备份文件不存在: {backup_file}")
            
            if progress_callback:
                progress_callback(0, '开始还原...')
            
            if backup_path.suffix == '.zip':
                with zipfile.ZipFile(backup_path, 'r') as zf:
                    if progress_callback:
                        progress_callback(50, '正在解压...')
                    zf.extractall(restore_path)
            else:
                for src_file in backup_path.rglob('*'):
                    if src_file.is_file():
                        rel_path = src_file.relative_to(backup_path)
                        dest_file = restore_path / rel_path
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, dest_file)
            
            if progress_callback:
                progress_callback(100, '还原完成')
            
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(-1, f'还原失败: {e}')
            return False
    
    def verify_backup(self, backup_file: str) -> Dict[str, Any]:
        """验证备份完整性"""
        backup_path = Path(backup_file)
        
        result = {
            'valid': False,
            'file_path': str(backup_path),
            'file_size': 0,
            'checksum': '',
            'file_count': 0,
            'errors': []
        }
        
        try:
            if not backup_path.exists():
                result['errors'].append('备份文件不存在')
                return result
            
            result['file_size'] = backup_path.stat().st_size
            current_checksum = self._calculate_checksum(backup_path)
            result['checksum'] = current_checksum
            
            for record in self._records:
                if record.file_path == str(backup_path):
                    if record.checksum == current_checksum:
                        result['valid'] = True
                    else:
                        result['errors'].append(f'校验和不匹配')
                    break
            
            if backup_path.suffix == '.zip':
                with zipfile.ZipFile(backup_path, 'r') as zf:
                    corrupt_files = zf.testzip()
                    if corrupt_files:
                        result['errors'].append(f'损坏的文件: {corrupt_files}')
                    else:
                        result['file_count'] = len(zf.namelist())
                        result['valid'] = True
            
            if not result['errors']:
                result['valid'] = True
                
        except Exception as e:
            result['errors'].append(str(e))
        
        return result
    
    def list_backups(self) -> List[BackupRecord]:
        """列出所有备份"""
        return sorted(self._records, key=lambda x: x.backup_time, reverse=True)
    
    def delete_backup(self, backup_id: str) -> bool:
        """删除备份"""
        for i, record in enumerate(self._records):
            if record.backup_id == backup_id:
                backup_path = Path(record.file_path)
                if backup_path.exists():
                    if backup_path.is_dir():
                        shutil.rmtree(backup_path)
                    else:
                        backup_path.unlink()
                self._records.pop(i)
                return True
        return False
    
    def _cleanup_old_backups(self) -> int:
        """清理旧备份"""
        max_backups = self.config.get('max_backups', 10)
        
        if len(self._records) <= max_backups:
            return 0
        
        sorted_records = sorted(self._records, key=lambda x: x.backup_time, reverse=True)
        deleted_count = 0
        
        for record in sorted_records[max_backups:]:
            if self.delete_backup(record.backup_id):
                deleted_count += 1
        
        return deleted_count
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """获取备份统计信息"""
        total_size = sum(r.file_size for r in self._records)
        success_count = sum(1 for r in self._records if r.status == 'success')
        
        return {
            'total_backups': len(self._records),
            'success_count': success_count,
            'total_size': total_size,
            'total_size_mb': total_size / (1024 * 1024)
        }
