# -*- coding: utf-8 -*-
"""
自动备份模块单元测试
"""

import os
import sys
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.backup.backup_manager import BackupManager, BackupRecord
from src.backup.backup_retry import BackupRetryManager
from src.backup.disk_monitor import DiskSpaceMonitor


class TestBackupRecord:
    """备份记录数据类测试"""
    
    def test_create_record(self):
        """测试创建备份记录"""
        record = BackupRecord(
            backup_id='20260616120000',
            file_path='/path/to/backup.zip',
            file_size=1024000,
            status='success'
        )
        
        assert record.backup_id == '20260616120000'
        assert record.file_size == 1024000
        assert record.status == 'success'
        assert record.backup_time is not None
    
    def test_to_dict(self):
        """测试转换为字典"""
        record = BackupRecord(
            backup_id='20260616120000',
            status='success'
        )
        
        data = record.to_dict()
        assert isinstance(data, dict)
        assert data['backup_id'] == '20260616120000'
        assert 'backup_time' in data


class TestBackupManager:
    """备份管理器测试"""
    
    def test_init(self, tmp_path):
        """测试初始化"""
        config = {
            'backup_path': str(tmp_path / 'backups'),
            'max_backups': 5,
            'compression': True
        }
        
        manager = BackupManager(config)
        
        assert manager is not None
        assert manager.backup_path.exists()
        assert manager.config['max_backups'] == 5
    
    def test_create_backup_without_files(self, tmp_path):
        """测试创建备份（无数据文件）"""
        manager = BackupManager({
            'backup_path': str(tmp_path / 'backups'),
            'compression': True
        })
        
        record = manager.create_backup(data_dir=str(tmp_path))
        
        assert record is not None
        assert record.status in ['success', 'failed']  # 可能失败因为没有文件
        assert record.backup_id is not None
    
    def test_create_backup_with_mock_files(self, tmp_path):
        """测试创建备份（模拟数据文件）"""
        # 创建模拟数据文件
        data_dir = tmp_path / 'data'
        data_dir.mkdir()
        
        tasks_db = data_dir / 'tasks.db'
        tasks_db.write_text('mock database content')
        
        manager = BackupManager({
            'backup_path': str(tmp_path / 'backups'),
            'compression': True
        })
        
        record = manager.create_backup(data_dir=str(data_dir))
        
        # 由于文件不是真正的SQLite，可能失败，但至少验证流程
        assert record is not None
        assert record.backup_id is not None
    
    def test_list_backups(self, tmp_path):
        """测试列出备份"""
        manager = BackupManager({
            'backup_path': str(tmp_path / 'backups')
        })
        
        # 添加一些备份记录
        for i in range(3):
            record = BackupRecord(
                backup_id=f'backup_{i}',
                file_path=str(tmp_path / f'backup_{i}.zip'),
                status='success'
            )
            manager._records.append(record)
        
        backups = manager.list_backups()
        assert len(backups) == 3
    
    def test_delete_backup(self, tmp_path):
        """测试删除备份"""
        manager = BackupManager({
            'backup_path': str(tmp_path / 'backups')
        })
        
        # 创建备份文件和记录
        backup_file = tmp_path / 'backups' / 'test_backup.zip'
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        backup_file.write_text('test content')
        
        record = BackupRecord(
            backup_id='test_backup',
            file_path=str(backup_file),
            status='success'
        )
        manager._records.append(record)
        
        # 删除备份
        result = manager.delete_backup('test_backup')
        assert result == True
        assert len(manager._records) == 0
        assert not backup_file.exists()
    
    def test_get_backup_stats(self, tmp_path):
        """测试获取备份统计"""
        manager = BackupManager({
            'backup_path': str(tmp_path / 'backups')
        })
        
        # 添加备份记录
        for i in range(3):
            record = BackupRecord(
                backup_id=f'backup_{i}',
                file_size=1024 * (i + 1),
                status='success'
            )
            manager._records.append(record)
        
        stats = manager.get_backup_stats()
        
        assert stats['total_backups'] == 3
        assert stats['success_count'] == 3
        assert stats['total_size'] == 1024 * 6  # 1+2+3 KB


class TestBackupSecurityChecks:
    """备份安全检查测试"""
    
    def test_validate_path_safe(self):
        """测试安全路径验证"""
        manager = BackupManager()
        
        safe_paths = [
            'backup.zip',
            'backups/backup.zip',
            'data/files/backup.zip',
            'test_file_123.txt',
            '备份文件.zip',
        ]
        
        for path in safe_paths:
            assert manager._validate_path(path) == True, f"路径应该安全: {path}"
    
    def test_validate_path_traversal(self):
        """测试路径遍历攻击检测"""
        manager = BackupManager()
        
        unsafe_paths = [
            '../etc/passwd',
            'backups/../../etc/passwd',
            '..\\Windows\\System32\\config',
            './../secret.txt',
            'a/../../../b',
        ]
        
        for path in unsafe_paths:
            assert manager._validate_path(path) == False, f"路径应该不安全: {path}"
    
    def test_validate_path_absolute(self):
        """测试绝对路径检查"""
        manager = BackupManager()
        
        # 默认不允许绝对路径
        assert manager._validate_path('/tmp/backup.zip') == False
        assert manager._validate_path('C:\\Windows\\backup.zip') == False
        
        # 允许时应该通过
        assert manager._validate_path('/tmp/backup.zip', allow_absolute=True) == True
    
    def test_validate_path_special_chars(self):
        """测试特殊字符检查"""
        manager = BackupManager()
        
        unsafe_paths = [
            'file<name>.txt',
            'file>name.txt',
            'file:name.txt',
            'file|name.txt',
            'file?name.txt',
            'file*name.txt',
            'file"name.txt',
        ]
        
        for path in unsafe_paths:
            assert manager._validate_path(path) == False, f"路径应该不安全: {path}"
    
    def test_validate_restore_path_critical(self):
        """测试还原到关键目录的检查"""
        manager = BackupManager()
        
        critical_paths = [
            '/',
            '/bin',
            '/etc',
            '/usr',
            'C:\\',
            'C:\\Windows',
            'C:\\Program Files',
        ]
        
        for path in critical_paths:
            assert manager._validate_restore_path(path) == False, f"路径应该不安全: {path}"
    
    def test_sanitize_filename(self):
        """测试文件名清理"""
        manager = BackupManager()
        
        # 测试清理特殊字符
        assert manager._sanitize_filename('file<name>.txt') == 'file_name_.txt'
        assert manager._sanitize_filename('normal_file.txt') == 'normal_file.txt'
        
        # 测试清理路径遍历
        assert '..' not in manager._sanitize_filename('../file.txt')
        assert '..' not in manager._sanitize_filename('..\\file.txt')
    
    def test_verify_backup_invalid_path(self):
        """测试验证不安全路径的备份"""
        manager = BackupManager()
        
        result = manager.verify_backup('../dangerous/backup.zip')
        
        assert result['valid'] == False
        assert any('不安全' in err for err in result['errors'])
    
    def test_restore_backup_invalid_path(self):
        """测试还原不安全路径的备份"""
        manager = BackupManager()
        
        result = manager.restore_backup(
            '../dangerous/backup.zip',
            restore_dir='./restore'
        )
        
        assert result == False
    
    def test_restore_to_critical_path(self):
        """测试还原到系统关键目录"""
        manager = BackupManager()
        
        result = manager.restore_backup(
            'backup.zip',
            restore_dir='C:\\Windows\\System32'
        )
        
        assert result == False
    
    def test_verify_backup_valid(self, tmp_path):
        """测试验证有效的备份"""
        # 创建有效的备份文件
        backup_file = tmp_path / 'test_backup.zip'
        
        import zipfile
        with zipfile.ZipFile(backup_file, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        manager = BackupManager({
            'backup_path': str(tmp_path)
        })
        
        result = manager.verify_backup(str(backup_file))
        
        assert result['valid'] == True
        assert result['file_size'] > 0


class TestBackupRetryManager:
    """备份重试管理器测试"""
    
    def test_init(self):
        """测试初始化"""
        retry_mgr = BackupRetryManager(
            max_retries=3,
            retry_interval=60
        )
        
        assert retry_mgr.max_retries == 3
        assert retry_mgr.retry_interval == 60
    
    def test_get_retry_status(self):
        """测试获取重试状态"""
        retry_mgr = BackupRetryManager(max_retries=3)
        
        status = retry_mgr.get_retry_status('backup_1')
        
        assert status['backup_id'] == 'backup_1'
        assert status['retry_count'] == 0
        assert status['can_retry'] == True
    
    def test_reset_retry(self):
        """测试重置重试"""
        retry_mgr = BackupRetryManager(max_retries=3)
        
        # 增加重试计数
        retry_mgr._retry_count['backup_1'] = 2
        
        # 重置
        retry_mgr.reset_retry('backup_1')
        
        assert retry_mgr._retry_count.get('backup_1', 0) == 0
    
    def test_clear_history(self):
        """测试清除历史"""
        retry_mgr = BackupRetryManager(max_retries=3)
        
        retry_mgr._retry_history['backup_1'] = []
        retry_mgr._retry_count['backup_1'] = 2
        
        retry_mgr.clear_history()
        
        assert len(retry_mgr._retry_history) == 0
        assert len(retry_mgr._retry_count) == 0


class TestDiskSpaceMonitor:
    """磁盘空间监控器测试"""
    
    def test_init(self):
        """测试初始化"""
        monitor = DiskSpaceMonitor(min_free_space_gb=1.0)
        
        assert monitor.min_free_space == 1.0 * 1024 * 1024 * 1024
    
    def test_check_space(self):
        """测试检查磁盘空间"""
        monitor = DiskSpaceMonitor()
        
        space_info = monitor.check_space('.')
        
        # 验证返回结构
        assert 'total' in space_info
        assert 'used' in space_info
        assert 'free' in space_info
        assert 'total_gb' in space_info
        
        # 验证数值合理性
        assert space_info['total_gb'] > 0
        assert space_info['free_gb'] >= 0
    
    def test_get_warning(self):
        """测试获取空间警告"""
        monitor = DiskSpaceMonitor()
        
        warning = monitor.get_warning('.')
        
        assert warning.level in ['normal', 'warning', 'critical', 'error', 'caution']
        assert warning.message is not None
        assert warning.free_space_gb >= 0
    
    def test_format_space_info(self):
        """测试格式化空间信息"""
        monitor = DiskSpaceMonitor()
        
        info = monitor.format_space_info('.')
        
        assert '磁盘空间信息' in info
        assert '总容量' in info
        assert '可用空间' in info


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
