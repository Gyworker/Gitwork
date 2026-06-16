# 市场咨询任务跟踪工具 补充设计方案V3.1

**版本**：V3.1  
**日期**：2026-06-16  
**阶段**：第二阶段补充开发  
**状态**：已评审

---

## 1. 概述

### 1.1 版本变更

本方案基于V3.0版本，根据CodeCC评审意见优化后形成：

| 序号 | 评审问题 | 优化措施 |
|------|----------|----------|
| 1 | 备份失败无重试机制 | 增加重试逻辑（失败后5分钟重试，最多3次） |
| 2 | sklearn依赖体积大 | 提供轻量替代方案（简单字符串匹配） |
| 3 | 未定义磁盘空间监控 | 增加磁盘空间检查和预警 |
| 4 | 未考虑敏感信息脱敏 | 增加操作历史敏感字段脱敏 |

### 1.2 核心功能

1. **操作历史**：记录所有用户操作，支持查询、导出、清理
2. **自动备份**：定时备份，支持压缩、还原、调度
3. **重复任务检测**：智能检测和合并重复任务

---

## 2. 功能详细设计

### 2.1 操作历史记录功能

#### 2.1.1 敏感信息处理

**脱敏规则**：

| 字段类型 | 脱敏规则 | 示例 |
|----------|----------|------|
| 手机号 | 中间4位隐藏 | 138****8000 |
| 邮箱 | @前3位+***+@后 | zhang***@example.com |
| 身份证 | 前后各保留2位 | 11****33 |
| 银行卡 | 仅显示后4位 | ****1234 |

**实现代码**：

```python
import re

class SensitiveDataMasker:
    """敏感数据脱敏处理器"""
    
    @staticmethod
    def mask_phone(phone):
        """手机号脱敏"""
        if not phone or len(phone) < 7:
            return phone
        return phone[:3] + '****' + phone[-4:]
    
    @staticmethod
    def mask_email(email):
        """邮箱脱敏"""
        if not email or '@' not in email:
            return email
        parts = email.split('@')
        name = parts[0]
        if len(name) > 3:
            masked_name = name[:3] + '***'
        else:
            masked_name = '***'
        return masked_name + '@' + parts[1]
    
    @staticmethod
    def mask_field(field_name, value):
        """通用字段脱敏"""
        sensitive_fields = {
            'phone': SensitiveDataMasker.mask_phone,
            'mobile': SensitiveDataMasker.mask_phone,
            'email': SensitiveDataMasker.mask_email,
            'id_card': lambda x: x[:2] + '****' + x[-2:] if x and len(x) > 4 else x,
            'bank_card': lambda x: '****' + x[-4:] if x and len(x) >= 4 else x,
        }
        
        if field_name.lower() in sensitive_fields:
            return sensitive_fields[field_name.lower()](value)
        return value
```

#### 2.1.2 批量操作优化

```python
class BatchOperationRecorder:
    """批量操作记录器"""
    
    def record_batch_import(self, module, action, count, source):
        """记录批量导入操作"""
        record = {
            'module': module,
            'action': action,
            'operation_type': 'BATCH',
            'summary': f'批量{action} {count}条记录',
            'details': {
                'count': count,
                'source': source,
                'status': 'success'
            }
        }
        self.history.log_operation(**record)
    
    def record_batch_delete(self, module, count, ids):
        """记录批量删除操作"""
        record = {
            'module': module,
            'action': 'DELETE',
            'operation_type': 'BATCH',
            'summary': f'批量删除 {count}条记录',
            'details': {
                'count': count,
                'target_ids': ids[:10],  # 只记录前10个ID
                'total_count': count
            }
        }
        self.history.log_operation(**record)
```

#### 2.1.3 分页查询优化

```python
class HistoryQueryOptimizer:
    """历史查询优化器"""
    
    def query_with_cursor(self, filters, cursor=None, limit=50):
        """
        使用游标分页查询
        
        优点：
        - 避免OFFSET性能问题
        - 支持深度分页
        - 性能稳定
        """
        query = """
            SELECT * FROM operation_history
            WHERE timestamp < :cursor
            AND (:module IS NULL OR module = :module)
            AND (:action IS NULL OR action = :action)
            ORDER BY timestamp DESC
            LIMIT :limit
        """
        
        params = {
            'cursor': cursor or datetime.max,
            'module': filters.get('module'),
            'action': filters.get('action'),
            'limit': limit
        }
        
        results = self.db.execute(query, params)
        
        # 返回下一页游标
        next_cursor = results[-1]['timestamp'] if len(results) == limit else None
        
        return {
            'data': results,
            'next_cursor': next_cursor,
            'has_more': next_cursor is not None
        }
```

---

### 2.2 自动备份功能

#### 2.2.1 备份重试机制

```python
class BackupRetryManager:
    """备份重试管理器"""
    
    def __init__(self):
        self.max_retries = 3
        self.retry_interval = 300  # 5分钟
        self.retry_count = 0
    
    def create_backup_with_retry(self, backup_func):
        """带重试的备份创建"""
        while self.retry_count < self.max_retries:
            try:
                result = backup_func()
                self.retry_count = 0  # 重置重试计数
                return {'success': True, 'result': result}
            except BackupError as e:
                self.retry_count += 1
                if self.retry_count < self.max_retries:
                    self._wait_before_retry()
                    self._log_retry_attempt(e)
                else:
                    return {
                        'success': False,
                        'error': str(e),
                        'retries': self.retry_count
                    }
    
    def _wait_before_retry(self):
        """等待重试间隔"""
        time.sleep(self.retry_interval)
    
    def _log_retry_attempt(self, error):
        """记录重试尝试"""
        self.db.log_backup_retry({
            'attempt': self.retry_count,
            'error': str(error),
            'next_retry_at': datetime.now() + timedelta(seconds=self.retry_interval)
        })
```

#### 2.2.2 磁盘空间监控

```python
import shutil

class DiskSpaceMonitor:
    """磁盘空间监控器"""
    
    def __init__(self, min_free_space_gb=1.0):
        self.min_free_space = min_free_space_gb * 1024 * 1024 * 1024  # 转换为字节
    
    def check_space_available(self, path):
        """检查指定路径所在磁盘的可用空间"""
        stat = shutil.disk_usage(path)
        return stat.free
    
    def is_space_sufficient(self, path, required_size=None):
        """检查空间是否充足"""
        free_space = self.check_space_available(path)
        required = required_size or self.min_free_space
        return free_space >= required
    
    def get_space_warning(self, path):
        """获取空间警告信息"""
        free_space = self.check_space_available(path)
        free_gb = free_space / (1024 ** 3)
        
        if free_gb < 0.5:
            return {
                'level': 'critical',
                'message': f'磁盘空间严重不足！剩余 {free_gb:.2f} GB',
                'action': '立即清理备份或联系管理员'
            }
        elif free_gb < 1.0:
            return {
                'level': 'warning',
                'message': f'磁盘空间不足，剩余 {free_gb:.2f} GB',
                'action': '建议清理旧备份'
            }
        else:
            return {
                'level': 'normal',
                'message': f'磁盘空间充足，剩余 {free_gb:.2f} GB',
                'action': None
            }
    
    def pre_backup_check(self, backup_path, estimated_size=None):
        """备份前空间检查"""
        warning = self.get_space_warning(backup_path)
        
        if warning['level'] == 'critical':
            raise BackupSpaceError(
                f"磁盘空间严重不足，无法创建备份。{warning['message']}"
            )
        
        if warning['level'] == 'warning':
            logger.warning(warning['message'])
        
        return warning
```

#### 2.2.3 备份配置优化

```yaml
# backup_config.yaml
backup:
  enabled: true
  auto_backup: true
  backup_interval: 4  # 小时
  
  # 重试配置
  retry:
    enabled: true
    max_retries: 3
    retry_interval: 300  # 5分钟
  
  # 磁盘空间配置
  disk_space:
    min_free_space_gb: 1.0
    auto_cleanup_on_low_space: true
  
  max_backups: 10
  backup_path: "./backups"
  
  compression: true
  
  retention:
    daily: 7
    weekly: 4
    monthly: 6
  
  schedule:
    enabled: true
    times: ["08:00", "12:00", "18:00"]
```

---

### 2.3 重复任务检测功能

#### 2.3.1 轻量级检测方案

```python
class LightweightDuplicateDetector:
    """
    轻量级重复检测器
    
    不依赖sklearn，使用简单字符串匹配算法
    适用于数据量较小（<10000条）的场景
    """
    
    def __init__(self, threshold=0.75):
        self.threshold = threshold
    
    def calculate_similarity(self, text1, text2):
        """计算两个文本的相似度（简单算法）"""
        if not text1 or not text2:
            return 0.0
        
        # 转换为小写
        t1 = text1.lower()
        t2 = text2.lower()
        
        # Jaccard相似度（基于字符）
        set1 = set(t1)
        set2 = set(t2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        jaccard = intersection / union if union > 0 else 0
        
        # 包含关系检测
        contains = 1.0 if (t1 in t2 or t2 in t1) else 0.0
        
        # 综合相似度
        return max(jaccard, contains * 0.8)
    
    def calculate_contact_similarity(self, task1, task2):
        """计算咨询者相似度"""
        # 姓名相似度
        name_sim = self.calculate_similarity(
            task1.get('consultant_name', ''),
            task2.get('consultant_name', '')
        )
        
        # 电话相似度
        phone_sim = self.calculate_similarity(
            self._normalize_phone(task1.get('consultant_phone', '')),
            self._normalize_phone(task2.get('consultant_phone', ''))
        )
        
        return max(name_sim, phone_sim * 0.9)
    
    def _normalize_phone(self, phone):
        """标准化电话号码"""
        return re.sub(r'[^\d]', '', phone)
    
    def detect_duplicates(self, tasks):
        """检测重复任务"""
        duplicates = []
        
        for i, task1 in enumerate(tasks):
            for j, task2 in enumerate(tasks[i+1:], start=i+1):
                # 计算各项相似度
                name_sim = self.calculate_similarity(
                    task1['name'], task2['name']
                )
                contact_sim = self.calculate_contact_similarity(task1, task2)
                time_sim = self._calculate_time_proximity(task1, task2)
                
                # 加权计算总体相似度
                overall = (
                    0.4 * name_sim +
                    0.3 * contact_sim +
                    0.2 * time_sim
                )
                
                if overall >= self.threshold:
                    duplicates.append({
                        'task1': task1,
                        'task2': task2,
                        'similarity': overall,
                        'factors': {
                            'name': name_sim,
                            'contact': contact_sim,
                            'time': time_sim
                        }
                    })
        
        return self._group_duplicates(duplicates)
```

#### 2.3.2 可插拔算法设计

```python
from abc import ABC, abstractmethod

class DuplicateDetectionAlgorithm(ABC):
    """重复检测算法基类"""
    
    @abstractmethod
    def calculate_similarity(self, text1, text2) -> float:
        """计算相似度"""
        pass
    
    @abstractmethod
    def detect_duplicates(self, tasks: list) -> list:
        """检测重复"""
        pass

class TFIDFDetector(DuplicateDetectionAlgorithm):
    """TF-IDF检测器（依赖sklearn）"""
    
    def __init__(self, threshold=0.75):
        self.threshold = threshold
        self.vectorizer = TfidfVectorizer(...)
    
    def calculate_similarity(self, text1, text2) -> float:
        # TF-IDF + 余弦相似度
        pass

class LightweightDetector(DuplicateDetectionAlgorithm):
    """轻量级检测器（无外部依赖）"""
    
    def __init__(self, threshold=0.75):
        self.threshold = threshold
    
    def calculate_similarity(self, text1, text2) -> float:
        # Jaccard + 包含关系
        pass

class DuplicateDetectorFactory:
    """检测器工厂"""
    
    DETECTORS = {
        'tfidf': TFIDFDetector,
        'lightweight': LightweightDetector
    }
    
    @classmethod
    def create_detector(cls, algorithm='lightweight', **kwargs):
        """创建检测器"""
        detector_class = cls.DETECTORS.get(algorithm, LightweightDetector)
        return detector_class(**kwargs)
```

#### 2.3.3 同义词支持（可选）

```python
class SynonymDictionary:
    """同义词词典"""
    
    def __init__(self):
        self.synonyms = {
            '路由器': ['router', '路由', '路由设备'],
            '交换机': ['switch', '交换', '交换设备'],
            '防火墙': ['firewall', 'FW', '墙'],
            '配置': ['设置', 'setup', 'config'],
            '问题': ['故障', 'issue', '问题', '报错'],
            '咨询': ['询问', '咨询', 'query'],
        }
    
    def normalize(self, text):
        """文本标准化"""
        for standard_word, synonyms in self.synonyms.items():
            for synonym in synonyms:
                if synonym in text:
                    text = text.replace(synonym, standard_word)
        return text
    
    def expand_query(self, keyword):
        """扩展查询词"""
        for standard_word, synonyms in self.synonyms.items():
            if keyword == standard_word:
                return [standard_word] + synonyms
        return [keyword]
```

---

## 3. 技术实现要点

### 3.1 模块结构

```
src/
├── history/
│   ├── __init__.py
│   ├── operation_history.py      # 操作历史记录
│   ├── sensitive_masker.py       # 敏感数据脱敏
│   ├── batch_recorder.py         # 批量操作记录
│   └── history_manager.py        # 历史管理UI
├── backup/
│   ├── __init__.py
│   ├── backup_manager.py         # 备份管理器
│   ├── backup_retry.py           # 备份重试机制
│   ├── disk_monitor.py           # 磁盘空间监控
│   └── backup_scheduler.py       # 备份调度器
├── duplicate/
│   ├── __init__.py
│   ├── base_detector.py          # 检测器基类
│   ├── tfidf_detector.py         # TF-IDF检测器
│   ├── lightweight_detector.py    # 轻量级检测器
│   ├── duplicate_detector.py      # 检测器工厂
│   ├── synonym_dict.py           # 同义词词典
│   └── merge_handler.py          # 合并处理器
└── utils/
    └── backup_config.yaml        # 备份配置文件
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
        'sensitive_fields': ['phone', 'mobile', 'email', 'id_card', 'bank_card'],
        'batch_threshold': 10,  # 超过此数量使用批量记录
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
        }
    }
    
    # 重复检测配置
    DUPLICATE_CONFIG = {
        'enabled': True,
        'threshold': 0.75,
        'algorithm': 'lightweight',  # lightweight 或 tfidf
        'auto_merge_threshold': 0.95,
        'manual_confirm_threshold': 0.85,
    }
```

---

## 4. 测试用例更新

### 4.1 新增测试用例

| 用例ID | 用例名称 | 对应改进 |
|--------|----------|----------|
| TC-HIST-009 | 敏感信息脱敏测试 | 脱敏处理 |
| TC-HIST-010 | 批量操作记录测试 | 批量操作优化 |
| TC-HIST-011 | 游标分页查询测试 | 分页优化 |
| TC-BACK-009 | 备份重试机制测试 | 重试机制 |
| TC-BACK-010 | 磁盘空间不足测试 | 空间监控 |
| TC-DUP-009 | 轻量级检测算法测试 | 轻量算法 |
| TC-DUP-010 | 算法切换测试 | 可插拔算法 |

### 4.2 测试覆盖目标

| 模块 | 覆盖率目标 | 测试用例数 |
|------|-----------|-----------|
| 操作历史 | ≥85% | 11 |
| 自动备份 | ≥85% | 10 |
| 重复检测 | ≥85% | 10 |

---

## 5. 验收标准

### 5.1 操作历史

- [x] 记录所有任务操作（创建、编辑、删除）
- [x] 敏感信息自动脱敏
- [x] 支持批量操作摘要记录
- [x] 支持游标分页查询
- [x] 支持按模块、操作类型、时间筛选
- [x] 支持导出历史记录
- [x] 支持自动清理过期记录

### 5.2 自动备份

- [x] 支持手动创建备份
- [x] 支持定时自动备份
- [x] 备份失败自动重试（最多3次）
- [x] 磁盘空间不足预警
- [x] 备份文件压缩
- [x] 支持备份还原
- [x] 自动清理旧备份

### 5.3 重复任务检测

- [x] 支持轻量级检测算法（无sklearn依赖）
- [x] 支持TF-IDF检测算法（可选）
- [x] 基于名称相似度检测
- [x] 基于咨询者信息检测
- [x] 支持可配置的相似度阈值
- [x] 自动合并高置信度重复（>=95%）
- [x] 手动确认中等置信度重复
- [x] 支持合并撤销

---

## 6. 版本变更记录

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| 3.0 | 2026-06-16 | 初始版本 |
| 3.1 | 2026-06-16 | 根据CodeCC评审意见优化，增加重试机制、磁盘监控、脱敏处理、轻量算法 |
