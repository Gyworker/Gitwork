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
    
    # 允许的文件名正则（只允许字母、数字、下划线、连字符、点和中文）
    SAFE_PATH_PATTERN = r'^[\w\-\.]+$'
    
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
    
    # ==================== 路径安全检查 ====================
    
    def _validate_path(self, path: str, allow_absolute: bool = False) -> bool:
        """
        验证路径安全性，防止路径遍历攻击
        
        Args:
            path: 要验证的路径
            allow_absolute: 是否允许绝对路径
            
        Returns:
            bool: 路径是否安全
        """
        if not path:
            return False
        
        path_obj = Path(path)
        
        # 检查是否包含路径遍历攻击的特征
        # .. 或绝对路径
        if '..' in path_obj.parts:
            return False
        
        # 不允许以斜杠开头（除非明确允许）
        if path.startswith('/') or path.startswith('\\'):
            if not allow_absolute:
                return False
        
        # 检查文件名是否安全
        if path_obj.name:
            # 禁止特殊字符
            unsafe_chars = ['<', '>', ':', '"', '|', '?', '*']
            if any(char in path_obj.name for char in unsafe_chars):
                return False
        
        # 禁止隐藏文件（以.开头）
        if path_obj.name.startswith('.') and path_obj.name not in ['.']:
            # 允许配置文件等隐藏文件
            pass
        
        return True
    
    def _validate_restore_path(self, restore_path: str) -> bool:
        """
        验证还原路径的安全性
        
        Args:
            restore_path: 还原目标路径
            
        Returns:
            bool: 路径是否安全
        """
        if not self._validate_path(restore_path, allow_absolute=True):
            return False
        
        restore_obj = Path(restore_path).resolve()
        
        # 禁止还原到系统关键目录
        critical_paths = [
            Path('/'),
            Path('/bin'),
            Path('/etc'),
            Path('/usr'),
            Path('/var'),
            Path('C:\\'),
            Path('C:\\Windows'),
            Path('C:\\Program Files'),
            Path('C:\\Program Files (x86)'),
            Path(os.environ.get('SYSTEMROOT', 'C:\\Windows')),
            Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')),
        ]
        
        for critical in critical_paths:
            try:
                if restore_obj == critical.resolve() or restore_obj.is_relative_to(critical):
                    return False
            except (ValueError, OSError):
                continue
        
        return True
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，只保留安全字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 清理后的安全文件名
        """
        # 只保留字母、数字、中文、下划线、连字符、点
        import re
        sanitized = re.sub(r'[^\w\-\.\u4e00-\u9fff]', '_', filename)
        # 移除连续的下划线
        sanitized = re.sub(r'_+', '_', sanitized)
        # 限制长度
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:255 - len(ext)] + ext
        return sanitized
    
    # ==================== 备份操作 ====================
    
    def create_backup(
        self,
        data_dir: str = './data',
        include_ocr: bool = False,
        progress_callback: Callable[[int, str], None] = None
    ) -> BackupRecord:
        """创建备份"""
        # 验证数据目录安全性
        if not self._validate_path(data_dir):
            raise ValueError(f"数据目录路径不安全: {data_dir}")
        
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
            # 验证文件路径安全性
            if file_path.exists() and self._validate_path(str(file_path)):
                files.append({
                    'path': file_path,
                    'name': self._sanitize_filename(filename),
                    'size': file_path.stat().st_size
                })
        
        if include_ocr:
            ocr_dir = data_path / 'imports' / 'ocr_results'
            if ocr_dir.exists() and self._validate_path(str(ocr_dir)):
                one_week_ago = datetime.now().timestamp() - 7 * 24 * 3600
                for file_path in ocr_dir.glob('*.xlsx'):
                    if file_path.stat().st_mtime >= one_week_ago:
                        # 验证文件名安全性
                        safe_name = self._sanitize_filename(f'ocr_results/{file_path.name}')
                        files.append({
                            'path': file_path,
                            'name': safe_name,
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
    
    # ==================== 还原操作 ====================
    
    def restore_backup(
        self,
        backup_file: str,
        restore_dir: str = './data',
        progress_callback: Callable[[int, str], None] = None
    ) -> bool:
        """还原备份"""
        try:
            # 验证备份文件路径
            if not self._validate_path(backup_file):
                raise ValueError(f"备份文件路径不安全: {backup_file}")
            
            # 验证还原目录
            if not self._validate_restore_path(restore_dir):
                raise ValueError(f"还原目标路径不安全: {restore_dir}")
            
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
                    # 验证压缩包内的文件名安全性
                    self._validate_zip_filenames(zf)
                    zf.extractall(restore_path)
            else:
                for src_file in backup_path.rglob('*'):
                    if src_file.is_file():
                        rel_path = src_file.relative_to(backup_path)
                        # 验证相对路径安全性
                        if not self._validate_path(str(rel_path)):
                            continue
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
    
    def _validate_zip_filenames(self, zf: zipfile.ZipFile) -> None:
        """
        验证ZIP压缩包内的文件名安全性
        
        Args:
            zf: ZIP文件对象
            
        Raises:
            ValueError: 如果发现不安全的文件名
        """
        for name in zf.namelist():
            # 禁止绝对路径
            if name.startswith('/') or name.startswith('\\'):
                raise ValueError(f"ZIP文件包含不安全的绝对路径: {name}")
            
            # 禁止路径遍历
            if '..' in name:
                raise ValueError(f"ZIP文件包含路径遍历攻击: {name}")
            
            # 检查每个路径部分
            path_obj = Path(name)
            for part in path_obj.parts:
                if not self._validate_path(part):
                    raise ValueError(f"ZIP文件包含不安全的文件名: {name}")
    
    # ==================== 验证操作 ====================
    
    def verify_backup(self, backup_file: str) -> Dict[str, Any]:
        """验证备份完整性"""
        # 验证路径安全性
        if not self._validate_path(backup_file):
            return {
                'valid': False,
                'file_path': backup_file,
                'errors': ['备份文件路径不安全']
            }
        
        backup_path = Path(backup_file)
        return self._verify_backup_internal(backup_path)
    
    def _verify_backup_internal(self, backup_path: Path) -> Dict[str, Any]:
        """
        内部验证方法
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            Dict: 验证结果
        """
        result = self._init_verify_result(backup_path)
        
        try:
            # 检查文件存在性
            if not self._check_file_exists(backup_path, result):
                return result
            
            # 检查文件大小和校验和
            self._check_file_checksum(backup_path, result)
            
            # 验证校验和匹配记录
            self._verify_checksum_match(backup_path, result)
            
            # 验证ZIP完整性
            if backup_path.suffix == '.zip':
                self._verify_zip_integrity(backup_path, result)
            
            # 设置最终验证状态
            if not result['errors']:
                result['valid'] = True
                
        except Exception as e:
            result['errors'].append(str(e))
        
        return result
    
    def _init_verify_result(self, backup_path: Path) -> Dict[str, Any]:
        """初始化验证结果字典"""
        return {
            'valid': False,
            'file_path': str(backup_path),
            'file_size': 0,
            'checksum': '',
            'file_count': 0,
            'errors': []
        }
    
    def _check_file_exists(self, backup_path: Path, result: Dict) -> bool:
        """检查备份文件是否存在"""
        if not backup_path.exists():
            result['errors'].append('备份文件不存在')
            return False
        return True
    
    def _check_file_checksum(self, backup_path: Path, result: Dict) -> None:
        """检查文件校验和"""
        result['file_size'] = backup_path.stat().st_size
        result['checksum'] = self._calculate_checksum(backup_path)
    
    def _verify_checksum_match(self, backup_path: Path, result: Dict) -> None:
        """验证校验和是否与记录匹配"""
        for record in self._records:
            if record.file_path == str(backup_path):
                if record.checksum != result['checksum']:
                    result['errors'].append('校验和不匹配')
                break
    
    def _verify_zip_integrity(self, backup_path: Path, result: Dict) -> None:
        """验证ZIP文件完整性"""
        try:
            with zipfile.ZipFile(backup_path, 'r') as zf:
                corrupt_files = zf.testzip()
                if corrupt_files:
                    result['errors'].append(f'损坏的文件: {corrupt_files}')
                else:
                    result['file_count'] = len(zf.namelist())
                    result['valid'] = True
        except zipfile.BadZipFile as e:
            result['errors'].append(f'无效的ZIP文件: {str(e)}')
    
    # ==================== 列表和删除操作 ====================
    
    def list_backups(self) -> List[BackupRecord]:
        """列出所有备份"""
        return sorted(self._records, key=lambda x: x.backup_time, reverse=True)
    
    def delete_backup(self, backup_id: str) -> bool:
        """删除备份"""
        for i, record in enumerate(self._records):
            if record.backup_id == backup_id:
                backup_path = Path(record.file_path)
                # 验证路径安全性后再删除
                if self._validate_path(str(backup_path)):
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
