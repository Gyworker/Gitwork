# -*- coding: utf-8 -*-
"""
遗留问题修复测试
Issue Fixes Test

测试数据库加密、审计日志、权限控制等修复功能
"""

import os
import sys
import time
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict
import unittest

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.security import (
    EncryptionManager,
    DatabaseEncryption,
    AuditLogger,
    AuditAction,
    AuditLevel,
    PermissionManager,
    Permission,
    Role,
    User,
    get_audit_logger,
    get_permission_manager,
    get_encryption_manager,
)

from src.core.cache_optimizer import (
    EnhancedLRUCache,
    CachePolicy,
    StatisticsCache,
    smart_cache,
    get_statistics_cache,
    get_global_cache,
)


class TestEncryptionManager(unittest.TestCase):
    """加密管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.encryption_manager = EncryptionManager()
        self.test_data = b"Hello, World! This is a test message."
    
    def test_encrypt_decrypt_data(self):
        """测试数据加密解密"""
        # 加密
        encrypted = self.encryption_manager.encrypt_data(self.test_data)
        self.assertIsNotNone(encrypted)
        self.assertNotEqual(encrypted, self.test_data)
        self.assertGreater(len(encrypted), len(self.test_data))
        
        # 解密
        decrypted = self.encryption_manager.decrypt_data(encrypted)
        self.assertEqual(decrypted, self.test_data)
    
    def test_hash_password(self):
        """测试密码哈希"""
        password = "TestPassword123!"
        hashed = self.encryption_manager.hash_password(password)
        
        # 哈希后的密码应该更长
        self.assertGreater(len(hashed), len(password))
        
        # 相同密码应该生成不同的哈希（因为有随机盐）
        hashed2 = self.encryption_manager.hash_password(password)
        self.assertNotEqual(hashed, hashed2)
    
    def test_verify_password(self):
        """测试密码验证"""
        password = "TestPassword123!"
        hashed = self.encryption_manager.hash_password(password)
        
        # 正确密码验证
        self.assertTrue(self.encryption_manager.verify_password(password, hashed))
        
        # 错误密码验证
        self.assertFalse(self.encryption_manager.verify_password("WrongPassword", hashed))
    
    def test_encrypt_decrypt_file(self):
        """测试文件加密解密"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False) as f:
            input_path = f.name
            f.write(self.test_data)
        
        encrypted_path = input_path + ".enc"
        decrypted_path = input_path + ".dec"
        
        try:
            # 加密
            success = self.encryption_manager.encrypt_file(input_path, encrypted_path)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(encrypted_path))
            
            # 解密
            success = self.encryption_manager.decrypt_file(encrypted_path, decrypted_path)
            self.assertTrue(success)
            
            # 验证
            with open(decrypted_path, 'rb') as f:
                decrypted = f.read()
            self.assertEqual(decrypted, self.test_data)
            
        finally:
            # 清理
            for path in [input_path, encrypted_path, decrypted_path]:
                if os.path.exists(path):
                    os.unlink(path)


class TestAuditLogger(unittest.TestCase):
    """审计日志测试"""
    
    def setUp(self):
        """测试前准备"""
        self.audit_logger = get_audit_logger()
        self.audit_logger._entries.clear()
    
    def test_log_entry_creation(self):
        """测试审计日志条目创建"""
        entry = self.audit_logger.log(
            action=AuditAction.TASK_CREATE,
            resource_type="task",
            resource_id="T001",
            details={"title": "测试任务"},
            user="test_user"
        )
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.action, "TASK_CREATE")
        self.assertEqual(entry.user, "test_user")
        self.assertEqual(entry.resource_type, "task")
        self.assertEqual(entry.resource_id, "T001")
        self.assertIn("title", entry.details)
    
    def test_get_entries_by_user(self):
        """测试按用户获取日志"""
        # 记录多个用户的操作
        self.audit_logger.log(AuditAction.TASK_CREATE, user="user1")
        self.audit_logger.log(AuditAction.TASK_UPDATE, user="user1")
        self.audit_logger.log(AuditAction.TASK_CREATE, user="user2")
        
        # 获取user1的日志
        entries = self.audit_logger.get_entries(user="user1")
        self.assertEqual(len(entries), 2)
        
        # 获取user2的日志
        entries = self.audit_logger.get_entries(user="user2")
        self.assertEqual(len(entries), 1)
    
    def test_get_entries_by_action(self):
        """测试按操作类型获取日志"""
        self.audit_logger.log(AuditAction.TASK_CREATE)
        self.audit_logger.log(AuditAction.TASK_UPDATE)
        self.audit_logger.log(AuditAction.TASK_CREATE)
        
        entries = self.audit_logger.get_entries(action=AuditAction.TASK_CREATE)
        self.assertEqual(len(entries), 2)
    
    def test_get_entries_by_time_range(self):
        """测试按时间范围获取日志"""
        self.audit_logger.log(AuditAction.TASK_CREATE)
        
        # 获取最近1小时的日志
        one_hour_ago = datetime.now() - timedelta(hours=1)
        entries = self.audit_logger.get_entries(start_time=one_hour_ago)
        self.assertGreaterEqual(len(entries), 1)
    
    def test_user_activity_stats(self):
        """测试用户活动统计"""
        self.audit_logger.log(AuditAction.TASK_CREATE, user="test_user")
        self.audit_logger.log(AuditAction.TASK_UPDATE, user="test_user")
        self.audit_logger.log(AuditAction.TASK_DELETE, user="test_user")
        
        stats = self.audit_logger.get_user_activity("test_user")
        
        self.assertEqual(stats.get("TASK_CREATE", 0), 1)
        self.assertEqual(stats.get("TASK_UPDATE", 0), 1)
        self.assertEqual(stats.get("TASK_DELETE", 0), 1)
    
    def test_export_to_json(self):
        """测试导出为JSON"""
        self.audit_logger.log(AuditAction.TASK_CREATE, user="test_user")
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            output_path = f.name
        
        try:
            success = self.audit_logger.export_to_file(output_path, format="json")
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
            
            # 验证内容
            with open(output_path, 'r') as f:
                content = f.read()
                self.assertIn("TASK_CREATE", content)
                self.assertIn("test_user", content)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestPermissionManager(unittest.TestCase):
    """权限管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.permission_manager = get_permission_manager()
        self.test_user = User(
            user_id="U001",
            username="testuser",
            role=Role.USER
        )
    
    def test_add_user(self):
        """测试添加用户"""
        success = self.permission_manager.add_user(self.test_user)
        self.assertTrue(success)
        
        # 验证用户已添加
        user = self.permission_manager.get_user("U001")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
    
    def test_remove_user(self):
        """测试删除用户"""
        self.permission_manager.add_user(self.test_user)
        success = self.permission_manager.remove_user("U001")
        self.assertTrue(success)
        
        # 验证用户已删除
        user = self.permission_manager.get_user("U001")
        self.assertIsNone(user)
    
    def test_update_user_role(self):
        """测试更新用户角色"""
        self.permission_manager.add_user(self.test_user)
        
        # 更新为管理员
        success = self.permission_manager.update_user_role("U001", Role.ADMIN)
        self.assertTrue(success)
        
        user = self.permission_manager.get_user("U001")
        self.assertEqual(user.role, Role.ADMIN)
    
    def test_has_permission_admin(self):
        """测试管理员权限"""
        admin_user = User(user_id="A001", username="admin", role=Role.ADMIN)
        self.permission_manager.add_user(admin_user)
        
        # 管理员应该有所有权限
        self.assertTrue(
            self.permission_manager.has_permission("A001", Permission.TASK_VIEW)
        )
        self.assertTrue(
            self.permission_manager.has_permission("A001", Permission.SYSTEM_CONFIG)
        )
        self.assertTrue(
            self.permission_manager.has_permission("A001", Permission.SYSTEM_AUDIT)
        )
    
    def test_has_permission_user(self):
        """测试普通用户权限"""
        self.permission_manager.add_user(self.test_user)
        
        # 普通用户有任务权限
        self.assertTrue(
            self.permission_manager.has_permission("U001", Permission.TASK_VIEW)
        )
        self.assertTrue(
            self.permission_manager.has_permission("U001", Permission.TASK_CREATE)
        )
        
        # 普通用户无系统权限
        self.assertFalse(
            self.permission_manager.has_permission("U001", Permission.SYSTEM_CONFIG)
        )
        self.assertFalse(
            self.permission_manager.has_permission("U001", Permission.SYSTEM_AUDIT)
        )
    
    def test_has_permission_guest(self):
        """测试访客权限"""
        guest_user = User(user_id="G001", username="guest", role=Role.GUEST)
        self.permission_manager.add_user(guest_user)
        
        # 访客只有查看权限
        self.assertTrue(
            self.permission_manager.has_permission("G001", Permission.TASK_VIEW)
        )
        self.assertFalse(
            self.permission_manager.has_permission("G001", Permission.TASK_CREATE)
        )
    
    def test_grant_permission(self):
        """测试授予权限"""
        self.permission_manager.add_user(self.test_user)
        
        # 授予额外权限
        success = self.permission_manager.grant_permission(
            "U001", Permission.SYSTEM_BACKUP
        )
        self.assertTrue(success)
        
        # 验证权限已授予
        self.assertTrue(
            self.permission_manager.has_permission("U001", Permission.SYSTEM_BACKUP)
        )
    
    def test_revoke_permission(self):
        """测试撤销权限"""
        admin_user = User(user_id="A001", username="admin", role=Role.ADMIN)
        self.permission_manager.add_user(admin_user)
        
        # 撤销权限
        success = self.permission_manager.revoke_permission(
            "A001", Permission.SYSTEM_AUDIT
        )
        self.assertTrue(success)
        
        # 验证权限已撤销
        self.assertFalse(
            self.permission_manager.has_permission("A001", Permission.SYSTEM_AUDIT)
        )
    
    def test_get_user_permissions(self):
        """测试获取用户权限列表"""
        self.permission_manager.add_user(self.test_user)
        
        permissions = self.permission_manager.get_user_permissions("U001")
        self.assertIsInstance(permissions, list)
        self.assertIn(Permission.TASK_VIEW, permissions)
        self.assertIn(Permission.TASK_CREATE, permissions)


class TestEnhancedLRUCache(unittest.TestCase):
    """增强型LRU缓存测试"""
    
    def setUp(self):
        """测试前准备"""
        self.cache = EnhancedLRUCache(max_size=3, default_ttl=60)
    
    def test_basic_get_set(self):
        """测试基本存取"""
        self.cache.set("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")
        
        # 不存在的键
        self.assertIsNone(self.cache.get("nonexistent"))
        self.assertEqual(self.cache.get("nonexistent", "default"), "default")
    
    def test_lru_eviction(self):
        """测试LRU淘汰"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")
        
        # 触发key1访问，使其成为最近使用的
        self.cache.get("key1")
        
        # 添加新键，key2应该被淘汰
        self.cache.set("key4", "value4")
        
        self.assertEqual(self.cache.get("key1"), "value1")
        self.assertEqual(self.cache.get("key4"), "value4")
        self.assertIsNone(self.cache.get("key2"))
    
    def test_ttl_expiration(self):
        """测试TTL过期"""
        # 创建TTL很短的缓存
        cache = EnhancedLRUCache(max_size=10, default_ttl=1)
        
        cache.set("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")
        
        # 等待过期
        time.sleep(1.1)
        
        # 应该已过期
        self.assertIsNone(cache.get("key1"))
    
    def test_delete(self):
        """测试删除"""
        self.cache.set("key1", "value1")
        self.assertTrue(self.cache.delete("key1"))
        self.assertFalse(self.cache.delete("nonexistent"))
        self.assertIsNone(self.cache.get("key1"))
    
    def test_clear(self):
        """测试清空"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.clear()
        
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))
    
    def test_cache_stats(self):
        """测试缓存统计"""
        self.cache.set("key1", "value1")
        self.cache.get("key1")  # 命中
        self.cache.get("key2")  # 未命中
        
        stats = self.cache.get_stats()
        
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hit_rate"], 50.0)


class TestStatisticsCache(unittest.TestCase):
    """统计缓存测试"""
    
    def setUp(self):
        """测试前准备"""
        self.stats_cache = get_statistics_cache()
        self.stats_cache.invalidate()
    
    def test_counts_cache(self):
        """测试计数缓存"""
        self.stats_cache.set_counts("tasks", 100)
        count = self.stats_cache.get_counts("tasks")
        self.assertEqual(count, 100)
    
    def test_distribution_cache(self):
        """测试分布缓存"""
        dist = {"高": 10, "中": 50, "低": 40}
        self.stats_cache.set_distribution("tasks", "urgency", dist)
        
        result = self.stats_cache.get_distribution("tasks", "urgency")
        self.assertEqual(result, dist)
    
    def test_trend_cache(self):
        """测试趋势缓存"""
        trend = [
            {"date": "2024-01-01", "count": 10},
            {"date": "2024-01-02", "count": 15},
        ]
        self.stats_cache.set_trend("tasks", "created_at", "daily", trend)
        
        result = self.stats_cache.get_trend("tasks", "created_at", "daily")
        self.assertEqual(result, trend)
    
    def test_invalidate(self):
        """测试缓存失效"""
        self.stats_cache.set_counts("tasks", 100)
        self.stats_cache.invalidate("tasks")
        
        count = self.stats_cache.get_counts("tasks")
        self.assertIsNone(count)


class TestSmartCache(unittest.TestCase):
    """智能缓存装饰器测试"""
    
    def test_smart_cache_decorator(self):
        """测试智能缓存装饰器"""
        call_count = 0
        
        @smart_cache(prefix="test", ttl=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # 第一次调用
        result1 = expensive_function(5)
        self.assertEqual(result1, 10)
        self.assertEqual(call_count, 1)
        
        # 第二次调用（应该使用缓存）
        result2 = expensive_function(5)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count, 1)  # 没有增加


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_security_workflow(self):
        """测试安全功能工作流"""
        # 1. 创建用户
        permission_manager = get_permission_manager()
        user = User(user_id="U001", username="testuser", role=Role.USER)
        permission_manager.add_user(user)
        
        # 2. 记录审计日志
        audit_logger = get_audit_logger()
        audit_logger.set_current_user("testuser")
        audit_logger.log(
            AuditAction.TASK_CREATE,
            resource_type="task",
            resource_id="T001",
            details={"title": "测试任务"}
        )
        
        # 3. 验证权限
        self.assertTrue(
            permission_manager.has_permission("U001", Permission.TASK_VIEW)
        )
        
        # 4. 获取审计日志
        entries = audit_logger.get_entries(user="testuser")
        self.assertGreaterEqual(len(entries), 1)
    
    def test_cache_performance(self):
        """测试缓存性能"""
        stats_cache = get_statistics_cache()
        stats_cache.invalidate()
        
        # 设置缓存
        stats_cache.set_counts("tasks", 1000)
        
        # 多次读取（应使用缓存）
        for _ in range(100):
            count = stats_cache.get_counts("tasks")
            self.assertEqual(count, 1000)
        
        # 检查缓存命中率
        stats = stats_cache.get_all_stats()
        self.assertGreater(stats["counts"]["hits"], 0)


if __name__ == "__main__":
    unittest.main()
