# 市场咨询任务跟踪工具 补充设计方案V3.0

**版本**：V3.0  
**日期**：2026-06-16  
**阶段**：第二阶段补充开发  
**状态**：待评审

---

## 1. 概述

### 1.1 补充背景

本方案针对第一阶段补充开发（V2.0）完成后的功能增强需求，包括：
- 重复任务合并功能
- 操作历史记录功能
- 自动备份功能

### 1.2 设计目标

1. **重复任务合并**：智能识别并合并重复任务，减少数据冗余
2. **操作历史**：记录用户的所有操作行为，支持回溯和审计
3. **自动备份**：定时自动备份数据库和配置文件，防止数据丢失

### 1.3 功能优先级

| 功能 | 优先级 | 复杂度 | 风险 |
|------|--------|--------|------|
| 操作历史 | P0 | 中 | 低 |
| 自动备份 | P0 | 中 | 低 |
| 重复任务合并 | P1 | 高 | 中 |

---

## 2. 功能详细设计

### 2.1 操作历史记录功能

#### 2.1.1 功能描述

记录用户在系统中的所有操作行为，包括：
- 任务创建、编辑、删除
- 联系人导入、导出、编辑
- 推荐库操作
- 系统设置变更

#### 2.1.2 历史记录字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| timestamp | DATETIME | 操作时间 |
| user | VARCHAR(50) | 用户名 |
| module | VARCHAR(50) | 模块名称 |
| action | VARCHAR(50) | 操作类型 |
| target_type | VARCHAR(50) | 目标类型（task/contact/recommendation） |
| target_id | INTEGER | 目标ID |
| target_name | VARCHAR(200) | 目标名称 |
| before_value | TEXT | 操作前值（JSON格式） |
| after_value | TEXT | 操作后值（JSON格式） |
| ip_address | VARCHAR(50) | IP地址 |
| device_info | VARCHAR(200) | 设备信息 |

#### 2.1.3 操作类型定义

| 操作类型 | 描述 | 记录内容 |
|----------|------|----------|
| CREATE | 创建 | 完整记录 |
| UPDATE | 修改 | 变更前后对比 |
| DELETE | 删除 | 删除前完整记录 |
| IMPORT | 导入 | 导入数量、来源 |
| EXPORT | 导出 | 导出数量、去向 |
| LOGIN | 登录 | 登录时间、设备 |
| LOGOUT | 登出 | 登出时间 |
| MERGE | 合并 | 合并的记录列表 |
| BACKUP | 备份 | 备份文件路径 |

#### 2.1.4 历史记录表结构

```sql
CREATE TABLE operation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user VARCHAR(50) DEFAULT 'local_user',
    module VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    target_type VARCHAR(50),
    target_id INTEGER,
    target_name VARCHAR(200),
    before_value TEXT,
    after_value TEXT,
    ip_address VARCHAR(50) DEFAULT '127.0.0.1',
    device_info VARCHAR(200) DEFAULT 'Windows Desktop',
    session_id VARCHAR(100)
);

-- 创建索引提升查询性能
CREATE INDEX idx_history_timestamp ON operation_history(timestamp);
CREATE INDEX idx_history_module ON operation_history(module);
CREATE INDEX idx_history_target ON operation_history(target_type, target_id);
```

#### 2.1.5 界面设计

**操作历史面板**：
```
┌─────────────────────────────────────────────────────────────┐
│  📋 操作历史                                      [筛选] [导出] │
├─────────────────────────────────────────────────────────────┤
│  模块: [全部 ▼]  操作: [全部 ▼]  时间: [今天 ▼]  关键词: [____] │
├─────────────────────────────────────────────────────────────┤
│  时间              │ 模块    │ 操作  │ 目标      │ 操作人      │
│  ─────────────────────────────────────────────────────────  │
│  2026-06-16 16:30 │ 任务    │ 创建  │ 产品报价  │ local_user  │
│  2026-06-16 16:28 │ 联系人  │ 导入  │ 25条记录  │ local_user  │
│  2026-06-16 16:25 │ 任务    │ 编辑  │ 技术咨询  │ local_user  │
│  2026-06-16 16:20 │ 推荐库  │ 创建  │ 张三      │ local_user  │
├─────────────────────────────────────────────────────────────┤
│                                          第 1/5 页 [<] [>]  │
└─────────────────────────────────────────────────────────────┘
```

**历史详情弹窗**：
```
┌─────────────────────────────────────────────────────────────┐
│  操作详情                                           [×]      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  基本信息:                                                   │
│  • 操作时间: 2026-06-16 16:30:25                            │
│  • 操作模块: 任务                                            │
│  • 操作类型: 编辑                                            │
│  • 操作人: local_user                                       │
│                                                              │
│  目标信息:                                                   │
│  • 目标类型: 任务                                           │
│  • 目标ID: 12345                                            │
│  • 目标名称: 产品报价咨询                                    │
│                                                              │
│  变更对比:                                                   │
│  ┌────────────────────┬────────────────────┐               │
│  │ 修改前              │ 修改后              │               │
│  ├────────────────────┼────────────────────┤               │
│  │ 重要程度: 中        │ 重要程度: 高        │               │
│  │ 责任人: 张三        │ 责任人: 李四        │               │
│  │ 备注: 暂无         │ 备注: 紧急处理      │               │
│  └────────────────────┴────────────────────┘               │
│                                                              │
│                              [撤销此操作]  [关闭]             │
└─────────────────────────────────────────────────────────────┘
```

#### 2.1.6 功能实现

**核心类设计**：
```python
# src/history/operation_history.py

class OperationHistory:
    """操作历史记录器"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def log_operation(self, module, action, target_type=None, 
                     target_id=None, target_name=None,
                     before_value=None, after_value=None):
        """记录操作"""
        pass
    
    def query_history(self, filters=None, page=1, page_size=50):
        """查询历史记录"""
        pass
    
    def get_target_history(self, target_type, target_id):
        """获取指定目标的所有历史"""
        pass
    
    def export_history(self, format='excel', path=None):
        """导出历史记录"""
        pass
    
    def cleanup_old_records(self, days=90):
        """清理过期记录"""
        pass
```

---

### 2.2 自动备份功能

#### 2.2.1 功能描述

定时自动备份系统数据，支持：
- 数据库完整备份
- 配置文件备份
- 备份文件管理（保留最近N份）
- 手动备份和还原

#### 2.2.2 备份内容

| 备份项 | 说明 | 备份频率 |
|--------|------|----------|
| SQLite数据库 | tasks.db, contacts.db等 | 每次 |
| 配置文件 | config.yaml, settings.json | 每次 |
| 映射规则库 | mapping_rules.xlsx | 每次 |
| OCR识别结果 | 最近1周的OCR结果 | 每周 |
| 导入文件 | 最近1周的导入文件 | 每周 |

#### 2.2.3 备份配置

```yaml
# backup_config.yaml
backup:
  enabled: true
  auto_backup: true
  backup_interval: 4  # 小时
  max_backups: 10  # 保留最近10份
  backup_path: "./backups"
  
  retention:
    daily: 7   # 保留7天
    weekly: 4  # 保留4周
    monthly: 6 # 保留6个月
    
  compression: true  # 启用压缩
  encryption: false  # 不启用加密
  
  schedule:
    enabled: true
    times: ["08:00", "12:00", "18:00"]
```

#### 2.2.4 备份文件命名规则

```
Gitwork_backup_YYYYMMDD_HHMMSS.zip
Gitwork_backup_20260616_160000.zip
Gitwork_backup_20260616_120000.zip
Gitwork_backup_20260616_080000.zip
```

#### 2.2.5 备份存储结构

```
backups/
├── Gitwork_backup_20260616_160000.zip
├── Gitwork_backup_20260616_120000.zip
├── Gitwork_backup_20260616_080000.zip
├── Gitwork_backup_20260615_180000.zip
├── ...
└── backup_manifest.json  # 备份清单
```

#### 2.2.6 备份清单格式

```json
{
  "backup_id": "20260616160000",
  "backup_time": "2026-06-16 16:00:00",
  "files": [
    {"name": "tasks.db", "size": 102400, "checksum": "abc123..."},
    {"name": "contacts.db", "size": 51200, "checksum": "def456..."},
    {"name": "config.yaml", "size": 2048, "checksum": "ghi789..."}
  ],
  "compression": "zip",
  "total_size": 155648,
  "status": "success"
}
```

#### 2.2.7 备份管理界面

**备份设置面板**：
```
┌─────────────────────────────────────────────────────────────┐
│  ⚙️  自动备份设置                                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ☑ 启用自动备份                                             │
│                                                              │
│  备份间隔: [4] 小时                                          │
│                                                              │
│  备份时间点:                                                 │
│  ☑ 08:00                                                    │
│  ☑ 12:00                                                    │
│  ☑ 18:00                                                    │
│  ☐ 自定义时间                                                │
│                                                              │
│  保留策略:                                                   │
│  ☑ 自动清理旧备份                                            │
│  保留最近: [10] 份备份                                       │
│                                                              │
│  ☑ 启用压缩                                                 │
│  ☐ 启用加密（需要设置密码）                                   │
│                                                              │
│  备份存储位置:                                               │
│  [D:\Gitwork\backups                    ] [浏览]            │
│                                                              │
│  当前状态: ✅ 最后备份于 2026-06-16 16:00                    │
│                                                              │
│                        [立即备份]  [保存设置]  [取消]         │
└─────────────────────────────────────────────────────────────┘
```

**备份历史面板**：
```
┌─────────────────────────────────────────────────────────────┐
│  📦 备份历史                                      [还原] [删除] │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ☑ 全选   文件数: 10   总大小: 1.5 MB                        │
│  ─────────────────────────────────────────────────────────  │
│  ☑ 2026-06-16 16:00  Gitwork_backup_20260616_160000.zip  │
│  ☐ 2026-06-16 12:00  Gitwork_backup_20260616_120000.zip  │
│  ☐ 2026-06-16 08:00  Gitwork_backup_20260616_080000.zip  │
│  ☐ 2026-06-15 18:00  Gitwork_backup_20260615_180000.zip  │
│  ☐ 2026-06-15 12:00  Gitwork_backup_20260615_120000.zip  │
│  ☐ 2026-06-15 08:00  Gitwork_backup_20260615_080000.zip  │
│  ☐ 2026-06-14 18:00  Gitwork_backup_20260614_180000.zip  │
│  ☐ 2026-06-14 12:00  Gitwork_backup_20260614_120000.zip  │
│  ☐ 2026-06-14 08:00  Gitwork_backup_20260614_080000.zip  │
│  ☐ 2026-06-13 18:00  Gitwork_backup_20260613_180000.zip  │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  💾 磁盘使用: 15.0 MB / 100.0 GB   📊 备份数量: 10          │
└─────────────────────────────────────────────────────────────┘
```

#### 2.2.8 功能实现

**核心类设计**：
```python
# src/utils/backup_manager.py

import zipfile
import hashlib
import json
from datetime import datetime
from pathlib import Path

class BackupManager:
    """备份管理器"""
    
    def __init__(self, config=None):
        self.config = config or self._default_config()
        self.backup_path = Path(self.config['backup_path'])
        self.backup_path.mkdir(parents=True, exist_ok=True)
    
    def _default_config(self):
        """默认配置"""
        return {
            'enabled': True,
            'auto_backup': True,
            'backup_interval': 4,
            'max_backups': 10,
            'backup_path': './backups',
            'compression': True,
            'retention': {
                'daily': 7,
                'weekly': 4,
                'monthly': 6
            }
        }
    
    def create_backup(self, include_ocr=False):
        """创建备份"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_path / f"Gitwork_backup_{timestamp}.zip"
        
        manifest = self._collect_files(include_ocr)
        self._create_archive(manifest, backup_file)
        self._cleanup_old_backups()
        
        return str(backup_file)
    
    def restore_backup(self, backup_file):
        """还原备份"""
        pass
    
    def list_backups(self):
        """列出所有备份"""
        pass
    
    def delete_backup(self, backup_id):
        """删除备份"""
        pass
    
    def verify_backup(self, backup_file):
        """验证备份完整性"""
        pass
```

---

### 2.3 重复任务合并功能

#### 2.3.1 功能描述

智能识别和合并重复任务，包括：
- 基于内容相似度的重复检测
- 基于关键词的重复检测
- 自动合并或手动确认合并
- 合并历史追溯

#### 2.3.2 重复检测算法

**检测维度**：

| 维度 | 权重 | 说明 |
|------|------|------|
| 任务名称相似度 | 0.4 | 使用TF-IDF+余弦相似度 |
| 咨询者相同 | 0.3 | 姓名+联系方式匹配 |
| 时间接近 | 0.2 | 创建时间在7天内 |
| 内容相似度 | 0.1 | 具体内容关键词重叠 |

**相似度计算公式**：
```
Similarity = 0.4 × NameSim + 0.3 × ContactSim + 0.2 × TimeSim + 0.1 × ContentSim

重复判定阈值: Similarity >= 0.75
```

#### 2.3.3 重复检测表结构

```sql
-- 重复任务记录表
CREATE TABLE duplicate_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_group_id VARCHAR(50) NOT NULL,  -- 重复组ID
    task_id INTEGER NOT NULL,
    similarity_score FLOAT DEFAULT 0.0,
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',  -- pending/merged/ignored
    merged_into INTEGER,  -- 合并到的任务ID
    merged_at DATETIME,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- 创建索引
CREATE INDEX idx_dup_group ON duplicate_tasks(task_group_id);
CREATE INDEX idx_dup_status ON duplicate_tasks(status);
```

#### 2.3.4 合并策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| 自动合并 | 系统自动合并高置信度重复 | 相似度>=0.95 |
| 建议合并 | 提示用户确认合并 | 0.85<=相似度<0.95 |
| 手动检查 | 列出疑似重复供用户判断 | 0.75<=相似度<0.85 |
| 忽略 | 不作为重复处理 | 相似度<0.75 |

#### 2.3.5 合并规则

**合并时保留的数据**：

| 字段 | 合并策略 |
|------|----------|
| 任务名称 | 保留最完整的 |
| 重要程度 | 保留最高的 |
| 创建时间 | 保留最早的 |
| 任务内容 | 合并去重 |
| 咨询者信息 | 保留最新的 |
| 答复人信息 | 保留最新的 |
| 提醒设置 | 保留最早的 |
| 操作历史 | 合并所有历史 |

**合并后字段处理**：

| 字段 | 处理方式 |
|------|----------|
| 状态 | 保留优先级最高的 |
| 已提醒次数 | 累加 |
| 完成时间 | 保留最早的 |

#### 2.3.6 重复检测界面

**重复任务检测面板**：
```
┌─────────────────────────────────────────────────────────────┐
│  🔍 重复任务检测                                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  检测设置:                                                   │
│  相似度阈值: [━━━━━━━━●━━━━━] 75%                            │
│  ☑ 名称相似度    ☑ 咨询者相同    ☑ 时间接近    ☐ 内容相似度  │
│                                                              │
│  时间范围: [最近1个月 ▼]    [开始检测]                       │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  检测结果: 找到 3 组疑似重复任务                               │
│                                                              │
│  ┌─ 重复组 #1 (相似度: 92%) ─────────────────────────────┐   │
│  │  ☑ [任务#1001] 产品报价咨询 - 高优先级               │   │
│  │  ☑ [任务#1005] 产品报价咨询 - 中优先级               │   │
│  │                                                        │   │
│  │  咨询者: 张三 (138****8000)                           │   │
│  │  创建时间: 2026-06-10 vs 2026-06-12                  │   │
│  │                                                        │   │
│  │  [自动合并] [查看详情] [忽略此组]                       │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─ 重复组 #2 (相似度: 87%) ─────────────────────────────┐   │
│  │  ☑ [任务#1020] 技术方案咨询                          │   │
│  │  ☑ [任务#1023] 技术方案咨询                          │   │
│  │                                                        │   │
│  │  [确认合并] [查看详情] [忽略此组]                       │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─ 重复组 #3 (相似度: 78%) ─────────────────────────────┐   │
│  │  ☑ [任务#1050] 路由器配置问题                         │   │
│  │  ☑ [任务#1055] 路由器配置咨询                         │   │
│  │                                                        │   │
│  │  [需要人工确认] [查看详情] [忽略此组]                    │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                              │
│                        [合并全部] [导出报告] [关闭]            │
└─────────────────────────────────────────────────────────────┘
```

**合并详情弹窗**：
```
┌─────────────────────────────────────────────────────────────┐
│  合并详情 - 重复组 #1                                  [×]   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  重复分析:                                                   │
│  • 名称相似度: 100% (完全相同)                                │
│  • 咨询者: 完全匹配 (张三 13800138000)                        │
│  • 时间间隔: 2天                                             │
│  • 内容相似度: 85%                                           │
│                                                              │
│  合并预览:                                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 合并后任务                                            │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │ 任务名称: 产品报价咨询                                 │  │
│  │ 重要程度: 高 (保留最高的)                              │  │
│  │ 创建时间: 2026-06-10 (保留最早的)                     │  │
│  │ 已提醒: 5次 (累加)                                    │  │
│  │ 状态: 进行中                                          │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  被合并任务:                                                 │
│  • 任务#1005: 产品报价咨询 (2026-06-12) → 将被归档           │
│                                                              │
│  合并后操作历史:                                             │
│  • 记录合并操作到操作历史                                    │
│  • 被合并任务保留为归档状态                                  │
│                                                              │
│                        [确认合并] [取消]                      │
└─────────────────────────────────────────────────────────────┘
```

#### 2.3.7 功能实现

**核心类设计**：
```python
# src/core/duplicate_detector.py

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from datetime import datetime, timedelta

class DuplicateDetector:
    """重复任务检测器"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.vectorizer = TfidfVectorizer(
            token_pattern=r'[\u4e00-\u9fa5]+|[a-zA-Z]+',  # 中文和英文分词
            max_features=500
        )
        self.similarity_threshold = 0.75
    
    def detect_duplicates(self, tasks=None, threshold=None):
        """检测重复任务"""
        if tasks is None:
            tasks = self._load_tasks()
        
        threshold = threshold or self.similarity_threshold
        duplicates = []
        
        # 计算名称相似度
        name_sim_matrix = self._calculate_name_similarity(tasks)
        
        # 检测重复组
        for i, task1 in enumerate(tasks):
            for j, task2 in enumerate(tasks[i+1:], start=i+1):
                similarity = self._calculate_overall_similarity(
                    task1, task2, name_sim_matrix[i, j]
                )
                
                if similarity >= threshold:
                    duplicates.append({
                        'task1': task1,
                        'task2': task2,
                        'similarity': similarity,
                        'factors': self._get_similarity_factors(task1, task2)
                    })
        
        return self._group_duplicates(duplicates)
    
    def _calculate_name_similarity(self, tasks):
        """计算任务名称TF-IDF相似度"""
        names = [t['name'] for t in tasks]
        tfidf_matrix = self.vectorizer.fit_transform(names)
        return cosine_similarity(tfidf_matrix)
    
    def _calculate_overall_similarity(self, task1, task2, name_sim):
        """计算整体相似度"""
        # 名称相似度 (权重0.4)
        name_score = name_sim * 0.4
        
        # 咨询者相似度 (权重0.3)
        contact_score = self._calculate_contact_similarity(task1, task2) * 0.3
        
        # 时间接近度 (权重0.2)
        time_score = self._calculate_time_proximity(task1, task2) * 0.2
        
        # 内容相似度 (权重0.1)
        content_score = self._calculate_content_similarity(task1, task2) * 0.1
        
        return name_score + contact_score + time_score + content_score
    
    def merge_tasks(self, task_ids, primary_task_id=None):
        """合并重复任务"""
        pass
    
    def undo_merge(self, merge_record_id):
        """撤销合并"""
        pass
```

---

## 3. 技术设计

### 3.1 模块结构

```
src/
├── history/
│   ├── __init__.py
│   ├── operation_history.py      # 操作历史记录
│   └── history_manager.py        # 历史管理UI
├── backup/
│   ├── __init__.py
│   ├── backup_manager.py         # 备份管理器
│   ├── backup_scheduler.py       # 备份调度器
│   └── backup_restore.py         # 备份还原
├── duplicate/
│   ├── __init__.py
│   ├── duplicate_detector.py     # 重复检测器
│   └── merge_handler.py          # 合并处理器
└── utils/
    └── backup_config.yaml        # 备份配置文件
```

### 3.2 数据库变更

```sql
-- 操作历史表
CREATE TABLE operation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user VARCHAR(50) DEFAULT 'local_user',
    module VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    target_type VARCHAR(50),
    target_id INTEGER,
    target_name VARCHAR(200),
    before_value TEXT,
    after_value TEXT,
    ip_address VARCHAR(50) DEFAULT '127.0.0.1',
    device_info VARCHAR(200) DEFAULT 'Windows Desktop',
    session_id VARCHAR(100)
);

CREATE INDEX idx_history_timestamp ON operation_history(timestamp);
CREATE INDEX idx_history_module ON operation_history(module);
CREATE INDEX idx_history_target ON operation_history(target_type, target_id);

-- 备份记录表
CREATE TABLE backup_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_id VARCHAR(50) UNIQUE NOT NULL,
    backup_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    file_path VARCHAR(500),
    file_size INTEGER,
    checksum VARCHAR(100),
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 重复任务表
CREATE TABLE duplicate_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_group_id VARCHAR(50) NOT NULL,
    task_id INTEGER NOT NULL,
    similarity_score FLOAT DEFAULT 0.0,
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    merged_into INTEGER,
    merged_at DATETIME,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE INDEX idx_dup_group ON duplicate_tasks(task_group_id);
CREATE INDEX idx_dup_status ON duplicate_tasks(status);
```

### 3.3 依赖项

| 包 | 版本 | 用途 |
|----|------|------|
| scikit-learn | >=1.0 | TF-IDF向量计算 |
| schedule | >=1.1 | 备份调度 |
| APScheduler | >=3.10 | 定时任务调度 |

---

## 4. 测试用例设计

### 4.1 操作历史测试

| 用例ID | 用例名称 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| TC-HIST-001 | 记录任务创建 | 无 | 创建新任务 | 历史记录正确 |
| TC-HIST-002 | 记录任务编辑 | 有任务 | 编辑任务信息 | 记录变更前后 |
| TC-HIST-003 | 记录任务删除 | 有任务 | 删除任务 | 记录完整数据 |
| TC-HIST-004 | 记录联系人导入 | 有Excel文件 | 导入通讯录 | 记录导入数量 |
| TC-HIST-005 | 查询历史记录 | 有历史记录 | 设置筛选条件 | 返回匹配结果 |
| TC-HIST-006 | 导出历史记录 | 有历史记录 | 导出为Excel | 生成文件 |
| TC-HIST-007 | 查看任务历史 | 有任务历史 | 点击任务查看历史 | 显示所有历史 |
| TC-HIST-008 | 清理过期记录 | 有90天以上记录 | 执行清理 | 删除过期数据 |

### 4.2 自动备份测试

| 用例ID | 用例名称 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| TC-BACK-001 | 创建手动备份 | 无 | 点击立即备份 | 生成备份文件 |
| TC-BACK-002 | 自动备份触发 | 启用自动备份 | 到达预定时间 | 自动创建备份 |
| TC-BACK-003 | 还原备份 | 有备份文件 | 选择备份还原 | 数据恢复 |
| TC-BACK-004 | 验证备份完整性 | 有备份文件 | 验证checksum | 显示验证结果 |
| TC-BACK-005 | 清理旧备份 | 超过保留数量 | 自动/手动清理 | 删除旧备份 |
| TC-BACK-006 | 备份压缩 | 启用压缩 | 创建备份 | 生成zip文件 |
| TC-BACK-007 | 备份失败处理 | 网络异常 | 创建备份失败 | 记录错误信息 |
| TC-BACK-008 | 备份设置保存 | 无 | 修改备份设置 | 保存成功 |

### 4.3 重复任务检测测试

| 用例ID | 用例名称 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| TC-DUP-001 | 检测完全重复 | 有相同任务 | 执行检测 | 识别重复 |
| TC-DUP-002 | 检测相似任务 | 有相似任务 | 执行检测 | 识别相似 |
| TC-DUP-003 | 自动合并 | 相似度>=0.95 | 执行合并 | 任务合并 |
| TC-DUP-004 | 手动合并 | 有待确认重复 | 确认合并 | 任务合并 |
| TC-DUP-005 | 忽略重复 | 有疑似重复 | 点击忽略 | 不再提示 |
| TC-DUP-006 | 撤销合并 | 已合并任务 | 撤销合并 | 恢复任务 |
| TC-DUP-007 | 导出检测报告 | 有检测结果 | 导出Excel | 生成报告 |
| TC-DUP-008 | 调整检测阈值 | 无 | 修改阈值 | 检测结果变化 |

---

## 5. 验收标准

### 5.1 操作历史

- [ ] 记录所有任务操作（创建、编辑、删除）
- [ ] 记录所有联系人操作（导入、导出、编辑）
- [ ] 记录所有推荐库操作
- [ ] 支持按模块、操作类型、时间筛选
- [ ] 支持查看操作详情和变更对比
- [ ] 支持导出历史记录
- [ ] 支持自动清理90天前的记录

### 5.2 自动备份

- [ ] 支持手动创建备份
- [ ] 支持定时自动备份
- [ ] 备份文件使用zip压缩
- [ ] 支持备份完整性验证（checksum）
- [ ] 支持备份还原
- [ ] 自动清理超过保留期限的备份
- [ ] 备份失败时记录错误信息

### 5.3 重复任务检测

- [ ] 基于名称相似度检测
- [ ] 基于咨询者信息检测
- [ ] 基于时间接近度检测
- [ ] 支持可配置的相似度阈值
- [ ] 自动合并高置信度重复（>=95%）
- [ ] 手动确认中等置信度重复（85%-95%）
- [ ] 支持合并操作撤销
- [ ] 保留合并操作历史

---

## 6. 风险评估

| 风险项 | 影响 | 概率 | 缓解措施 |
|--------|------|------|----------|
| 重复检测误判 | 中 | 中 | 提供手动确认和忽略功能 |
| 备份存储空间不足 | 中 | 低 | 自动清理旧备份，提示用户 |
| 合并操作不可逆 | 高 | 低 | 提供撤销功能，保留合并记录 |
| 大数据量检测慢 | 中 | 中 | 分批处理，显示进度 |
| sklearn依赖问题 | 低 | 低 | 使用轻量级替代方案 |

---

## 7. 进度计划

| 任务 | 工时 | 开始日期 | 完成日期 |
|------|------|----------|----------|
| 操作历史模块开发 | 2人天 | 2026-06-16 | 2026-06-17 |
| 自动备份模块开发 | 2人天 | 2026-06-17 | 2026-06-18 |
| 重复任务检测开发 | 3人天 | 2026-06-18 | 2026-06-20 |
| UI界面开发 | 2人天 | 2026-06-20 | 2026-06-22 |
| 测试与文档 | 2人天 | 2026-06-22 | 2026-06-24 |
| CodeCC评审 | 1人天 | 2026-06-24 | 2026-06-25 |

**预计完成日期：2026-06-25**

---

## 8. 版本变更记录

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| 3.0 | 2026-06-16 | 初始版本，包含操作历史、自动备份、重复任务合并 |
