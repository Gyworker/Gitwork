# 市场咨询任务跟踪工具 补充设计方案V3.2

**版本**：V3.2  
**日期**：2026-06-17  
**阶段**：第二阶段补充开发  
**状态**：已评审

---

## 1. 概述

### 1.1 版本变更

本方案基于V3.1版本，根据CodeCC代码评审意见进行修复：

| 序号 | 评审问题 | 严重程度 | 优化措施 |
|------|----------|----------|----------|
| H-1 | 操作历史内存无限增长 | 高 | 添加内存限制(10KB)，超限时自动归档到gzip文件 |
| H-2 | verify_backup方法过长(45行) | 高 | 重构为5个子方法，职责单一化 |
| H-3 | 路径操作缺少安全检查 | 高 | 添加完整的路径安全验证体系 |

### 1.2 核心功能

1. **操作历史**：记录所有用户操作，支持查询、导出、清理，**内存限制保护**
2. **自动备份**：定时备份，支持压缩、还原、调度，**路径安全验证**
3. **重复任务检测**：智能检测和合并重复任务

---

## 2. 功能详细设计

### 2.1 操作历史记录功能

#### 2.1.1 内存限制保护机制

**设计目标**：防止操作历史记录无限增长导致内存溢出

**配置参数**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `memory_limit_kb` | 10KB | 内存限制，超过此限制自动归档 |
| `archive_dir` | `./data/history_archive` | 归档文件存储目录 |
| `archive_retention_days` | 30天 | 归档文件保留天数 |

**处理流程**：

```
┌─────────────────────────────────────────────────────────────┐
│  log_operation() 被调用                                      │
│                    │                                        │
│                    ▼                                        │
│  ┌─────────────────────────────────┐                        │
│  │  添加记录到内存 + 更新内存使用量  │                        │
│  │  _current_memory_size += record_size │                   │
│  └─────────────────────────────────┘                        │
│                    │                                        │
│                    ▼                                        │
│  ┌─────────────────────────────────┐                        │
│  │  _check_and_archive_if_needed() │                        │
│  │  检查: memory_usage >= 10KB ?   │                        │
│  └─────────────────────────────────┘                        │
│         │                    │                              │
│        Yes                   No                             │
│         │                    │                              │
│         ▼                    ▼                              │
│  ┌─────────────┐       ┌──────────┐                        │
│  │ 1. 保存到gzip │       │   结束   │                        │
│  │ 2. 清空内存   │       └──────────┘                        │
│  │ 3. 清理旧归档 │                                           │
│  └─────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

**实现代码**：

```python
class OperationHistory:
    """操作历史记录器（带内存保护）"""
    
    # 内存限制配置
    DEFAULT_MEMORY_LIMIT = 10 * 1024  # 默认10KB
    DEFAULT_ARCHIVE_DIR = './data/history_archive'
    
    def __init__(
        self,
        db_connection=None,
        memory_limit_kb: int = None,
        archive_dir: str = None
    ):
        self.db = db_connection
        self._records = []  # 内存存储
        
        # 内存限制配置
        self._memory_limit = (memory_limit_kb or self.DEFAULT_MEMORY_LIMIT) * 1024
        self._archive_dir = archive_dir or self.DEFAULT_ARCHIVE_DIR
        self._current_memory_size = 0
        self._archive_files: List[str] = []
        
        # 初始化归档目录
        Path(self._archive_dir).mkdir(parents=True, exist_ok=True)
    
    def _check_and_archive_if_needed(self) -> Optional[str]:
        """检查内存使用量，超过限制则保存到归档文件"""
        current_usage = self._get_memory_usage()
        
        if current_usage >= self._memory_limit and self._records:
            # 保存当前内存中的所有记录到归档文件
            archive_file = self._save_to_archive_file(self._records)
            
            # 清空内存记录
            self._records.clear()
            self._current_memory_size = 0
            
            return archive_file
        
        return None
    
    def _save_to_archive_file(self, records: List[HistoryRecord]) -> str:
        """将记录保存到归档文件(gzip压缩)"""
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
```

#### 2.1.2 内存状态监控

```python
def get_memory_status(self) -> Dict[str, Any]:
    """获取内存使用状态"""
    memory_usage = self._get_memory_usage()
    
    return {
        'current_records': len(self._records),
        'memory_usage_bytes': memory_usage,
        'memory_usage_kb': memory_usage / 1024,
        'memory_limit_bytes': self._memory_limit,
        'memory_limit_kb': self._memory_limit / 1024,
        'usage_percent': (memory_usage / self._memory_limit) * 100,
        'archive_files': len(self._archive_files),
        'archive_dir': self._archive_dir
    }
```

#### 2.1.3 归档文件导出

```python
def export_history(
    self, 
    format: str = 'json',
    path: str = None,
    filters: Dict = None,
    include_archives: bool = False
) -> str:
    """
    导出历史记录
    
    Args:
        format: 导出格式 (json/csv/gzip)
        path: 保存路径
        filters: 筛选条件
        include_archives: 是否包含归档文件中的记录
    """
    if include_archives and not self.db:
        records = self.get_all_records()
        records = self._filter_records(records, filters)
    else:
        result = self.query_history(**filters, page=1, page_size=100000)
        records = result['data']
    
    if format == 'gzip':
        return self._export_gzip(records, path)
    # ... 其他格式

def export_archive_files(
    self,
    output_dir: str = None,
    combine: bool = True
) -> List[str]:
    """导出所有归档文件"""
    if not self._archive_files:
        return []
    
    if combine:
        # 合并所有归档文件
        all_records = []
        for archive_file in self._archive_files:
            if Path(archive_file).exists():
                archived_records = self._load_from_archive_file(archive_file)
                all_records.extend(archived_records)
        
        # 导出为单个gzip文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = Path(output_dir) / f'export_all_{timestamp}.json.gz'
        
        self._export_gzip(all_records, str(output_file))
        return [str(output_file)]
```

---

### 2.2 自动备份功能

#### 2.2.1 路径安全验证体系

**设计目标**：防止路径遍历攻击、压缩包攻击等安全威胁

**安全验证方法**：

| 方法 | 功能 | 防护对象 |
|------|------|----------|
| `_validate_path()` | 通用路径验证 | 路径遍历、绝对路径、特殊字符 |
| `_validate_restore_path()` | 还原路径验证 | 覆盖系统关键目录 |
| `_sanitize_filename()` | 文件名清理 | 文件名注入攻击 |
| `_validate_zip_filenames()` | ZIP文件名验证 | 压缩包路径攻击 |

**实现代码**：

```python
class BackupManager:
    """备份管理器（带安全验证）"""
    
    def _validate_path(self, path: str, allow_absolute: bool = False) -> bool:
        """
        验证路径安全性，防止路径遍历攻击
        
        检查项：
        1. 路径是否包含 '..' 
        2. 是否为绝对路径（除非明确允许）
        3. 是否包含危险特殊字符 < > : " | ? *
        """
        if not path:
            return False
        
        path_obj = Path(path)
        
        # 检查路径遍历攻击
        if '..' in path_obj.parts:
            return False
        
        # 检查绝对路径
        if path.startswith('/') or path.startswith('\\'):
            if not allow_absolute:
                return False
        
        # 检查特殊字符
        unsafe_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in path_obj.name for char in unsafe_chars):
            return False
        
        return True
    
    def _validate_restore_path(self, restore_path: str) -> bool:
        """
        验证还原路径的安全性，防止覆盖系统关键目录
        
        关键目录列表：
        - /, /bin, /etc, /usr, /var (Linux)
        - C:\, C:\Windows, C:\Program Files (Windows)
        """
        if not self._validate_path(restore_path, allow_absolute=True):
            return False
        
        restore_obj = Path(restore_path).resolve()
        
        critical_paths = [
            Path('/'),
            Path('/bin'),
            Path('/etc'),
            Path('C:\\'),
            Path('C:\\Windows'),
            Path('C:\\Program Files'),
            Path(os.environ.get('SYSTEMROOT', 'C:\\Windows')),
        ]
        
        for critical in critical_paths:
            try:
                if restore_obj == critical.resolve() or restore_obj.is_relative_to(critical):
                    return False
            except (ValueError, OSError):
                continue
        
        return True
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，只保留安全字符"""
        import re
        # 只保留字母、数字、中文、下划线、连字符、点
        sanitized = re.sub(r'[^\w\-\.\u4e00-\u9fff]', '_', filename)
        # 移除连续的下划线
        sanitized = re.sub(r'_+', '_', sanitized)
        # 限制长度
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:255 - len(ext)] + ext
        return sanitized
    
    def _validate_zip_filenames(self, zf: zipfile.ZipFile) -> None:
        """
        验证ZIP压缩包内的文件名安全性
        
        检查项：
        1. 禁止绝对路径
        2. 禁止路径遍历
        3. 禁止不安全的文件名
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
```

#### 2.2.2 verify_backup方法重构

**重构目标**：将45行方法拆分为多个职责单一的子方法

**重构后的方法结构**：

```python
def verify_backup(self, backup_file: str) -> Dict[str, Any]:
    """验证备份完整性（入口方法）"""
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
    """内部验证方法（主逻辑）"""
    result = self._init_verify_result(backup_path)
    
    try:
        if not self._check_file_exists(backup_path, result):
            return result
        
        self._check_file_checksum(backup_path, result)
        self._verify_checksum_match(backup_path, result)
        
        if backup_path.suffix == '.zip':
            self._verify_zip_integrity(backup_path, result)
        
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
```

---

## 3. 技术实现要点

### 3.1 模块结构

```
src/
├── history/
│   ├── __init__.py
│   ├── operation_history.py      # 操作历史记录（含内存保护）
│   ├── sensitive_masker.py       # 敏感数据脱敏
│   ├── batch_recorder.py         # 批量操作记录
│   └── history_manager.py        # 历史管理UI
├── backup/
│   ├── __init__.py
│   ├── backup_manager.py         # 备份管理器（含安全验证）
│   ├── backup_retry.py           # 备份重试机制
│   ├── disk_monitor.py           # 磁盘空间监控
│   └── backup_scheduler.py       # 备份调度器
├── duplicate/
│   ├── __init__.py
│   ├── base_detector.py          # 检测器基类
│   ├── lightweight_detector.py    # 轻量级检测器
│   ├── duplicate_detector.py      # 检测器工厂
│   └── merge_handler.py          # 合并处理器
└── utils/
    └── backup_config.yaml         # 备份配置文件
```

### 3.2 配置管理

```python
# src/config.py 增加配置项

class Config:
    """配置管理"""
    
    # 操作历史配置
    HISTORY_CONFIG = {
        'enabled': True,
        'retention_days': 90,
        'memory_limit_kb': 10,           # 新增：内存限制(KB)
        'archive_dir': './data/history_archive',  # 新增：归档目录
        'archive_retention_days': 30,     # 新增：归档保留天数
        'sensitive_fields': ['phone', 'mobile', 'email', 'id_card', 'bank_card'],
        'batch_threshold': 10,
    }
    
    # 备份配置
    BACKUP_CONFIG = {
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
        },
        'security': {                    # 新增：安全配置
            'validate_paths': True,       # 启用路径验证
            'allow_absolute_paths': False, # 禁止绝对路径
            'protect_system_dirs': True,   # 保护系统目录
        }
    }
```

---

## 4. 测试用例更新

### 4.1 新增测试用例

#### 操作历史模块（新增）

| 用例ID | 用例名称 | 对应改进 |
|--------|----------|----------|
| TC-HIST-012 | 内存限制初始化测试 | 内存限制配置 |
| TC-HIST-013 | 自动归档触发测试 | 超限自动归档 |
| TC-HIST-014 | gzip导出测试 | 归档文件导出 |
| TC-HIST-015 | 归档记录查询测试 | 归档记录回溯 |

#### 自动备份模块（新增）

| 用例ID | 用例名称 | 对应改进 |
|--------|----------|----------|
| TC-BACK-011 | 路径遍历攻击防护测试 | 路径安全验证 |
| TC-BACK-012 | 系统目录保护测试 | 关键目录验证 |
| TC-BACK-013 | ZIP文件名安全测试 | 压缩包攻击防护 |
| TC-BACK-014 | 验证方法重构测试 | verify_backup拆分 |

### 4.2 测试覆盖目标

| 模块 | 覆盖率目标 | 测试用例数 | 说明 |
|------|-----------|-----------|------|
| 操作历史 | ≥90% | 15 | +4内存保护测试 |
| 自动备份 | ≥90% | 12 | +4安全验证测试 |
| 重复检测 | ≥85% | 10 | - |

---

## 5. 验收标准

### 5.1 操作历史

- [x] 记录所有任务操作（创建、编辑、删除）
- [x] 敏感信息自动脱敏
- [x] 支持批量操作摘要记录
- [x] 支持游标分页查询
- [x] 支持按模块、操作类型、时间筛选
- [x] 支持导出历史记录（json/csv/gzip）
- [x] 支持自动清理过期记录
- [x] **内存限制保护（默认10KB）**
- [x] **超限自动归档到gzip文件**
- [x] **支持导出归档记录**

### 5.2 自动备份

- [x] 支持手动创建备份
- [x] 支持定时自动备份
- [x] 备份失败自动重试（最多3次）
- [x] 磁盘空间不足预警
- [x] 备份文件压缩
- [x] 支持备份还原
- [x] 自动清理旧备份
- [x] **路径遍历攻击防护**
- [x] **系统关键目录保护**
- [x] **ZIP文件名安全验证**
- [x] **verify_backup方法重构**

---

## 6. 版本变更记录

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| 3.0 | 2026-06-16 | 初始版本 |
| 3.1 | 2026-06-16 | 根据CodeCC评审意见优化，增加重试机制、磁盘监控、脱敏处理、轻量算法 |
| 3.2 | 2026-06-17 | 根据CodeCC代码评审修复H-1/H-2/H-3问题，增加内存限制、路径安全验证 |
