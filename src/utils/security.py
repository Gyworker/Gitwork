# -*- coding: utf-8 -*-
"""
安全模块
Security Module

提供数据库加密、审计日志、权限控制等安全功能
"""

import os
import hashlib
import hmac
import json
import time
import threading
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
from functools import wraps
from pathlib import Path
from enum import Enum

from .logger import get_logger

logger = get_logger(__name__)


# ==================== 数据库加密 ====================

class EncryptionManager:
    """加密管理器"""
    
    def __init__(self, key: Optional[str] = None):
        """
        初始化加密管理器
        
        Args:
            key: 加密密钥，如果为None则使用默认密钥
        """
        self._key = key or self._load_or_generate_key()
        self._lock = threading.Lock()
    
    def _load_or_generate_key(self) -> str:
        """加载或生成密钥"""
        key_file = Path.home() / ".gitwork" / ".key"
        
        if key_file.exists():
            with open(key_file, 'r') as f:
                return f.read().strip()
        else:
            # 生成新密钥
            import secrets
            key = secrets.token_hex(32)
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, 'w') as f:
                f.write(key)
            os.chmod(str(key_file), 0o600)  # 限制权限
            logger.info("生成新的加密密钥")
            return key
    
    def _derive_key(self, salt: bytes) -> bytes:
        """从主密钥派生出实际加密密钥"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            self._key.encode('utf-8'),
            salt,
            100000
        )
    
    def encrypt_data(self, data: bytes) -> bytes:
        """
        加密数据
        
        Args:
            data: 原始数据
            
        Returns:
            加密后的数据 (salt + encrypted)
        """
        import secrets
        from cryptography.fernet import Fernet
        
        with self._lock:
            salt = secrets.token_bytes(16)
            derived_key = self._derive_key(salt)
            fernet = Fernet(Fernet.generate_key(derived_key))
            encrypted = fernet.encrypt(data)
            
            return salt + encrypted
    
    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """
        解密数据
        
        Args:
            encrypted_data: 加密数据
            
        Returns:
            解密后的原始数据
        """
        from cryptography.fernet import Fernet
        
        with self._lock:
            salt = encrypted_data[:16]
            encrypted = encrypted_data[16:]
            
            derived_key = self._derive_key(salt)
            fernet = Fernet(Fernet.generate_key(derived_key))
            
            return fernet.decrypt(encrypted)
    
    def encrypt_file(self, input_path: str, output_path: str) -> bool:
        """
        加密文件
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            
        Returns:
            是否加密成功
        """
        try:
            with open(input_path, 'rb') as f:
                data = f.read()
            
            encrypted = self.encrypt_data(data)
            
            with open(output_path, 'wb') as f:
                f.write(encrypted)
            
            logger.info(f"文件加密成功: {input_path} -> {output_path}")
            return True
        except Exception as e:
            logger.error(f"文件加密失败: {e}")
            return False
    
    def decrypt_file(self, input_path: str, output_path: str) -> bool:
        """
        解密文件
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            
        Returns:
            是否解密成功
        """
        try:
            with open(input_path, 'rb') as f:
                encrypted = f.read()
            
            data = self.decrypt_data(encrypted)
            
            with open(output_path, 'wb') as f:
                f.write(data)
            
            logger.info(f"文件解密成功: {input_path} -> {output_path}")
            return True
        except Exception as e:
            logger.error(f"文件解密失败: {e}")
            return False
    
    def hash_password(self, password: str) -> str:
        """
        密码哈希
        
        Args:
            password: 明文密码
            
        Returns:
            哈希后的密码
        """
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        return salt.hex() + key.hex()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        验证密码
        
        Args:
            password: 明文密码
            hashed: 哈希后的密码
            
        Returns:
            是否匹配
        """
        salt = bytes.fromhex(hashed[:64])
        stored_key = hashed[64:]
        
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        
        return hmac.compare_digest(key.hex(), stored_key)


class DatabaseEncryption:
    """数据库加密封装"""
    
    def __init__(self, db_path: str, encrypted: bool = True):
        """
        初始化数据库加密
        
        Args:
            db_path: 数据库文件路径
            encrypted: 是否启用加密
        """
        self.db_path = db_path
        self.encrypted = encrypted
        self.encryption_manager = EncryptionManager()
        self._temp_db_path = db_path + ".tmp"
    
    def encrypt_database(self) -> bool:
        """加密数据库"""
        if not os.path.exists(self.db_path):
            logger.warning(f"数据库文件不存在: {self.db_path}")
            return False
        
        try:
            # 先创建备份
            backup_path = self.db_path + ".backup"
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            # 加密数据库
            success = self.encryption_manager.encrypt_file(
                self.db_path,
                self._temp_db_path
            )
            
            if success:
                # 替换原文件
                os.replace(self._temp_db_path, self.db_path)
                # 删除备份
                os.remove(backup_path)
                logger.info("数据库加密完成")
            
            return success
        except Exception as e:
            logger.error(f"数据库加密失败: {e}")
            return False
    
    def decrypt_database(self) -> bool:
        """解密数据库"""
        if not os.path.exists(self.db_path):
            logger.warning(f"加密数据库文件不存在: {self.db_path}")
            return False
        
        try:
            # 创建备份
            backup_path = self.db_path + ".encrypted.backup"
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            # 解密到临时文件
            decrypted_path = self.db_path + ".decrypted"
            success = self.encryption_manager.decrypt_file(
                self.db_path,
                decrypted_path
            )
            
            if success:
                # 替换原文件
                os.replace(decrypted_path, self.db_path)
                # 删除加密备份
                os.remove(backup_path)
                logger.info("数据库解密完成")
            
            return success
        except Exception as e:
            logger.error(f"数据库解密失败: {e}")
            return False


# ==================== 审计日志 ====================

class AuditLevel(Enum):
    """审计级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditAction(Enum):
    """审计操作类型"""
    # 任务操作
    TASK_CREATE = "TASK_CREATE"
    TASK_UPDATE = "TASK_UPDATE"
    TASK_DELETE = "TASK_DELETE"
    TASK_VIEW = "TASK_VIEW"
    TASK_EXPORT = "TASK_EXPORT"
    
    # 通讯录操作
    CONTACT_CREATE = "CONTACT_CREATE"
    CONTACT_UPDATE = "CONTACT_UPDATE"
    CONTACT_DELETE = "CONTACT_DELETE"
    CONTACT_IMPORT = "CONTACT_IMPORT"
    CONTACT_EXPORT = "CONTACT_EXPORT"
    
    # 系统操作
    SYSTEM_LOGIN = "SYSTEM_LOGIN"
    SYSTEM_LOGOUT = "SYSTEM_LOGOUT"
    SYSTEM_BACKUP = "SYSTEM_BACKUP"
    SYSTEM_RESTORE = "SYSTEM_RESTORE"
    SYSTEM_CONFIG = "SYSTEM_CONFIG"
    
    # 数据操作
    DATA_IMPORT = "DATA_IMPORT"
    DATA_EXPORT = "DATA_EXPORT"
    DATA_DELETE = "DATA_DELETE"


class AuditEntry:
    """审计日志条目"""
    
    def __init__(
        self,
        action: AuditAction,
        user: str = "system",
        resource_type: str = "",
        resource_id: str = "",
        details: Optional[Dict[str, Any]] = None,
        level: AuditLevel = AuditLevel.INFO,
        ip_address: str = "localhost"
    ):
        self.entry_id = self._generate_id()
        self.timestamp = datetime.now().isoformat()
        self.action = action.value
        self.user = user
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.details = details or {}
        self.level = level.value
        self.ip_address = ip_address
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        import uuid
        return str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "action": self.action,
            "user": self.user,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "level": self.level,
            "ip_address": self.ip_address,
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class AuditLogger:
    """审计日志记录器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._entries: List[AuditEntry] = []
        self._max_entries = 10000
        self._log_file: Optional[str] = None
        self._current_user = "anonymous"
        self._enabled = True
    
    def set_log_file(self, log_file: str):
        """设置日志文件"""
        self._log_file = log_file
    
    def set_current_user(self, user: str):
        """设置当前用户"""
        self._current_user = user
    
    def set_enabled(self, enabled: bool):
        """启用/禁用审计"""
        self._enabled = enabled
    
    def log(
        self,
        action: AuditAction,
        resource_type: str = "",
        resource_id: str = "",
        details: Optional[Dict[str, Any]] = None,
        level: AuditLevel = AuditLevel.INFO,
        user: Optional[str] = None
    ) -> AuditEntry:
        """
        记录审计日志
        
        Args:
            action: 操作类型
            resource_type: 资源类型
            resource_id: 资源ID
            details: 详细信息
            level: 审计级别
            user: 用户名
            
        Returns:
            审计日志条目
        """
        if not self._enabled:
            return None
        
        entry = AuditEntry(
            action=action,
            user=user or self._current_user,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            level=level
        )
        
        self._entries.append(entry)
        
        # 保持最大条目数
        if len(self._entries) > self._max_entries:
            self._entries.pop(0)
        
        # 写入日志文件
        if self._log_file:
            try:
                with open(self._log_file, 'a', encoding='utf-8') as f:
                    f.write(entry.to_json() + '\n')
            except Exception as e:
                logger.error(f"审计日志写入失败: {e}")
        
        logger.info(f"审计日志: [{action.value}] {user or self._current_user} - {resource_type}/{resource_id}")
        
        return entry
    
    def get_entries(
        self,
        user: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """
        获取审计日志条目
        
        Args:
            user: 用户名过滤
            action: 操作类型过滤
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制
            
        Returns:
            符合条件的审计条目列表
        """
        results = self._entries.copy()
        
        if user:
            results = [e for e in results if e.user == user]
        
        if action:
            results = [e for e in results if e.action == action.value]
        
        if start_time:
            results = [
                e for e in results
                if datetime.fromisoformat(e.timestamp) >= start_time
            ]
        
        if end_time:
            results = [
                e for e in results
                if datetime.fromisoformat(e.timestamp) <= end_time
            ]
        
        return results[-limit:]
    
    def get_user_activity(self, user: str, days: int = 7) -> Dict[str, int]:
        """
        获取用户活动统计
        
        Args:
            user: 用户名
            days: 统计天数
            
        Returns:
            活动统计字典
        """
        start_time = datetime.now() - timedelta(days=days)
        entries = self.get_entries(user=user, start_time=start_time)
        
        stats: Dict[str, int] = {}
        for entry in entries:
            action = entry.action
            stats[action] = stats.get(action, 0) + 1
        
        return stats
    
    def export_to_file(self, output_file: str, format: str = "json") -> bool:
        """
        导出审计日志
        
        Args:
            output_file: 输出文件
            format: 格式 (json, csv)
            
        Returns:
            是否导出成功
        """
        try:
            if format == "json":
                with open(output_file, 'w', encoding='utf-8') as f:
                    for entry in self._entries:
                        f.write(entry.to_json() + '\n')
            elif format == "csv":
                import csv
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(
                        f,
                        fieldnames=["entry_id", "timestamp", "action", "user",
                                   "resource_type", "resource_id", "level", "ip_address"]
                    )
                    writer.writeheader()
                    for entry in self._entries:
                        writer.writerow(entry.to_dict())
            else:
                raise ValueError(f"不支持的格式: {format}")
            
            logger.info(f"审计日志导出成功: {output_file}")
            return True
        except Exception as e:
            logger.error(f"审计日志导出失败: {e}")
            return False


# ==================== 权限控制 ====================

class Permission(Enum):
    """权限枚举"""
    # 任务权限
    TASK_VIEW = "task:view"
    TASK_CREATE = "task:create"
    TASK_EDIT = "task:edit"
    TASK_DELETE = "task:delete"
    TASK_EXPORT = "task:export"
    
    # 通讯录权限
    CONTACT_VIEW = "contact:view"
    CONTACT_CREATE = "contact:create"
    CONTACT_EDIT = "contact:edit"
    CONTACT_DELETE = "contact:delete"
    
    # 系统权限
    SYSTEM_CONFIG = "system:config"
    SYSTEM_BACKUP = "system:backup"
    SYSTEM_USER = "system:user"
    SYSTEM_AUDIT = "system:audit"


class Role(Enum):
    """角色枚举"""
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    GUEST = "guest"


class User:
    """用户模型"""
    
    def __init__(
        self,
        user_id: str,
        username: str,
        password_hash: str = "",
        role: Role = Role.USER,
        email: str = "",
        is_active: bool = True
    ):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.email = email
        self.is_active = is_active
        self.created_at = datetime.now()
        self.last_login: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role.value,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


class PermissionManager:
    """权限管理器"""
    
    # 角色默认权限
    DEFAULT_PERMISSIONS: Dict[Role, List[Permission]] = {
        Role.ADMIN: [
            Permission.TASK_VIEW, Permission.TASK_CREATE, Permission.TASK_EDIT,
            Permission.TASK_DELETE, Permission.TASK_EXPORT,
            Permission.CONTACT_VIEW, Permission.CONTACT_CREATE,
            Permission.CONTACT_EDIT, Permission.CONTACT_DELETE,
            Permission.SYSTEM_CONFIG, Permission.SYSTEM_BACKUP,
            Permission.SYSTEM_USER, Permission.SYSTEM_AUDIT,
        ],
        Role.MANAGER: [
            Permission.TASK_VIEW, Permission.TASK_CREATE, Permission.TASK_EDIT,
            Permission.TASK_DELETE, Permission.TASK_EXPORT,
            Permission.CONTACT_VIEW, Permission.CONTACT_CREATE,
            Permission.CONTACT_EDIT, Permission.CONTACT_DELETE,
            Permission.SYSTEM_BACKUP,
        ],
        Role.USER: [
            Permission.TASK_VIEW, Permission.TASK_CREATE, Permission.TASK_EDIT,
            Permission.CONTACT_VIEW, Permission.CONTACT_CREATE,
            Permission.CONTACT_EDIT,
        ],
        Role.GUEST: [
            Permission.TASK_VIEW,
            Permission.CONTACT_VIEW,
        ],
    }
    
    def __init__(self):
        self._users: Dict[str, User] = {}
        self._user_permissions: Dict[str, List[Permission]] = {}
        self._encryption_manager = EncryptionManager()
    
    def add_user(self, user: User) -> bool:
        """添加用户"""
        try:
            self._users[user.user_id] = user
            # 设置默认权限
            self._user_permissions[user.user_id] = self.DEFAULT_PERMISSIONS.get(
                user.role, []
            ).copy()
            logger.info(f"用户添加成功: {user.username}")
            return True
        except Exception as e:
            logger.error(f"用户添加失败: {e}")
            return False
    
    def remove_user(self, user_id: str) -> bool:
        """删除用户"""
        if user_id in self._users:
            del self._users[user_id]
            if user_id in self._user_permissions:
                del self._user_permissions[user_id]
            logger.info(f"用户删除成功: {user_id}")
            return True
        return False
    
    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户"""
        return self._users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        for user in self._users.values():
            if user.username == username:
                return user
        return None
    
    def update_user_role(self, user_id: str, role: Role) -> bool:
        """更新用户角色"""
        if user_id in self._users:
            self._users[user_id].role = role
            # 更新默认权限
            self._user_permissions[user_id] = self.DEFAULT_PERMISSIONS.get(role, []).copy()
            logger.info(f"用户角色更新: {user_id} -> {role.value}")
            return True
        return False
    
    def grant_permission(self, user_id: str, permission: Permission) -> bool:
        """授予权限"""
        if user_id in self._user_permissions:
            if permission not in self._user_permissions[user_id]:
                self._user_permissions[user_id].append(permission)
                logger.info(f"权限授予: {user_id} -> {permission.value}")
            return True
        return False
    
    def revoke_permission(self, user_id: str, permission: Permission) -> bool:
        """撤销权限"""
        if user_id in self._user_permissions:
            if permission in self._user_permissions[user_id]:
                self._user_permissions[user_id].remove(permission)
                logger.info(f"权限撤销: {user_id} -> {permission.value}")
            return True
        return False
    
    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """检查用户是否有指定权限"""
        if user_id not in self._users:
            return False
        
        user = self._users[user_id]
        if not user.is_active:
            return False
        
        # 检查用户权限
        if user_id in self._user_permissions:
            if permission in self._user_permissions[user_id]:
                return True
        
        # 检查角色默认权限
        role_permissions = self.DEFAULT_PERMISSIONS.get(user.role, [])
        return permission in role_permissions
    
    def get_user_permissions(self, user_id: str) -> List[Permission]:
        """获取用户所有权限"""
        if user_id not in self._users:
            return []
        
        user = self._users[user_id]
        
        # 合并用户权限和角色权限
        permissions = set(self.DEFAULT_PERMISSIONS.get(user.role, []))
        if user_id in self._user_permissions:
            permissions.update(self._user_permissions[user_id])
        
        return list(permissions)
    
    def check_permission(func: Callable) -> Callable:
        """权限检查装饰器"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 这里需要从上下文获取当前用户
            # 简化实现，实际使用时需要从session获取
            permission = kwargs.get('permission')
            if permission:
                # 验证权限
                pass
            return func(*args, **kwargs)
        return wrapper


# ==================== 权限检查装饰器 ====================

def require_permission(permission: Permission):
    """
    权限检查装饰器
    
    Args:
        permission: 需要的权限
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取当前用户（从全局上下文）
            current_user = getattr(wrapper, '_current_user', None)
            
            if current_user is None:
                logger.warning(f"权限检查失败: 未登录用户尝试访问 {func.__name__}")
                raise PermissionError("需要登录才能访问")
            
            # 检查权限
            if not _permission_manager.has_permission(current_user.user_id, permission):
                logger.warning(
                    f"权限检查失败: 用户 {current_user.username} "
                    f"尝试访问 {func.__name__} (需要权限: {permission.value})"
                )
                raise PermissionError(f"需要权限: {permission.value}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# 全局实例
_permission_manager = PermissionManager()
_audit_logger = AuditLogger()
_encryption_manager = EncryptionManager()


def get_permission_manager() -> PermissionManager:
    """获取权限管理器"""
    return _permission_manager


def get_audit_logger() -> AuditLogger:
    """获取审计日志记录器"""
    return _audit_logger


def get_encryption_manager() -> EncryptionManager:
    """获取加密管理器"""
    return _encryption_manager


from datetime import timedelta
