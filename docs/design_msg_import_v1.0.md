# MSG邮件文件导入功能设计方案 V1.0

## 一、功能概述

### 1.1 需求背景

根据需求文档V1.8第2.1.2节，需要支持Outlook邮件导入功能。当前实现中缺少邮件文件导入能力，本功能将实现MSG格式邮件文件的解析和任务提取。

### 1.2 功能定位

| 属性 | 说明 |
|------|------|
| 功能名称 | MSG邮件文件导入 |
| 功能类型 | 内容导入模块扩展 |
| 优先级 | P1-高 |
| 影响范围 | content_import.py, 新增msg_parser.py |

### 1.3 目标

- 支持导入Outlook导出的.msg格式邮件文件
- 解析邮件主题、发件人、时间、正文等关键信息
- 自动提取联系人信息
- 将邮件内容转换为任务数据格式

---

## 二、技术方案

### 2.1 技术选型

| 方案 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| extract-msg库 | 功能完整、解析准确 | 需要额外依赖 | **首选** |
| python-olefile备用 | 无外部依赖 | 解析能力有限 | **降级方案** |
| 自研解析 | 完全可控 | 开发周期长 | 不采用 |

### 2.2 核心组件

```
src/content/msg_parser.py
├── MSGParser          # MSG文件解析器
├── MSGEmail           # 邮件数据结构
├── BatchMSGParser     # 批量解析器
└── 辅助函数
    ├── _safe_parse()  # 安全解析包装
    └── _extract_text() # 文本提取
```

### 2.3 数据结构

```python
@dataclass
class MSGEmail:
    """MSG邮件数据结构"""
    subject: str           # 邮件主题
    sender: str            # 发件人姓名
    sender_email: str      # 发件人邮箱
    date: str              # 发送日期
    body: str              # 正文内容
    html_body: str         # HTML正文(可选)
    importance: str        # 重要程度
    attachments: List[str] # 附件列表
    to_recipients: List[str]   # 收件人列表
    cc_recipients: List[str]   # 抄送列表
```

### 2.4 解析流程

```
┌─────────────────────────────────────────────────────────┐
│                    MSG文件解析流程                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. 文件验证                                            │
│     ├── 检查文件扩展名(.msg)                            │
│     ├── 检查文件大小(限制100MB)                         │
│     └── 检查文件可读性                                  │
│                         │                               │
│                         ▼                               │
│  2. 库可用性检查                                         │
│     ├── 尝试import extract_msg                          │
│     └── 成功 → 使用extract-msg解析                      │
│         失败 → 使用olefile备用解析                      │
│                         │                               │
│                         ▼                               │
│  3. 内容提取                                            │
│     ├── 提取邮件头(主题/发件人/时间)                     │
│     ├── 提取正文(纯文本优先)                            │
│     ├── 提取附件列表                                    │
│     └── 提取收件人/抄送信息                             │
│                         │                               │
│                         ▼                               │
│  4. 数据转换                                            │
│     └── 转换为MSGEmail数据结构                          │
│                         │                               │
│                         ▼                               │
│  5. 任务内容生成                                        │
│     └── to_task_content() → 任务描述字符串              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 2.5 任务内容生成格式

```python
def to_task_content(self) -> str:
    """将邮件转换为任务内容"""
    content = f"【邮件主题】{self.subject}\n\n"
    content += f"【发件人】{self.sender} <{self.sender_email}>\n"
    content += f"【时间】{self.date}\n"
    content += f"【重要程度】{self.importance}\n\n"
    content += "【正文】\n" + self.body
    
    if self.attachments:
        content += "\n\n【附件】\n"
        for att in self.attachments:
            content += f"- {att}\n"
    
    return content
```

---

## 三、UI集成方案

### 3.1 现有UI修改

**文件**: `src/ui/content_import.py`

| 修改点 | 说明 |
|--------|------|
| 导入MSGParser | 增加模块导入 |
| radio_outlook标签 | "Outlook" → "邮件(MSG)" |
| _parse_outlook方法 | 重写为MSG解析逻辑 |
| _load_file_content方法 | 增加MSG文件处理分支 |
| 新增_load_msg_file方法 | MSG文件预览加载 |

### 3.2 用户交互流程

```
1. 用户选择 "邮件(MSG)" 导入方式
2. 用户点击 "文件" 按钮
3. 系统弹出文件选择对话框(过滤.msg文件)
4. 用户选择MSG文件
5. 系统加载文件并显示预览(主题/发件人/时间)
6. 用户点击 "解析" 按钮
7. 系统解析邮件并提取任务信息
8. 右侧显示解析结果供用户确认
```

### 3.3 错误处理

| 错误场景 | 处理方式 |
|----------|----------|
| extract-msg未安装 | 提示安装，显示库信息 |
| 文件格式错误 | 显示错误对话框 |
| 文件损坏 | 显示解析失败提示 |
| 文件过大 | 超过100MB时警告 |

---

## 四、安全考虑

### 4.1 文件路径安全

```python
def _validate_path(filepath: str) -> bool:
    """验证文件路径安全性"""
    # 检查绝对路径
    abs_path = os.path.abspath(filepath)
    
    # 检查是否包含路径遍历字符
    if '..' in filepath:
        return False
    
    # 检查是否在允许的目录范围内
    allowed_dirs = [os.path.expanduser('~'), 'C:\\', 'D:\\']
    for allowed in allowed_dirs:
        if abs_path.startswith(allowed):
            return True
    
    return False
```

### 4.2 文件大小限制

```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

def _check_file_size(filepath: str) -> bool:
    """检查文件大小"""
    size = os.path.getsize(filepath)
    return size <= MAX_FILE_SIZE
```

### 4.3 异常捕获

所有MSG解析操作必须包裹在try-except中，返回安全的错误信息。

---

## 五、性能指标

| 指标 | 目标值 |
|------|--------|
| 单文件解析时间 | < 2秒 |
| 文件大小限制 | 100MB |
| 内存占用峰值 | < 200MB |
| 批量处理速度 | > 10文件/秒 |

---

## 六、测试策略

### 6.1 单元测试

| 测试项 | 测试内容 |
|--------|----------|
| MSGParser解析 | 正常MSG文件解析 |
| 降级解析 | 无extract-msg库时的解析 |
| 字段提取 | 各字段正确提取 |
| 任务内容生成 | to_task_content()格式 |
| 联系人提取 | 收件人/抄送解析 |
| 批量解析 | 目录批量处理 |
| 边界条件 | 空文件、损坏文件 |
| 安全检查 | 路径遍历防护 |

### 6.2 集成测试

| 测试项 | 测试内容 |
|--------|----------|
| UI集成 | 导入按钮、文件选择 |
| 解析流程 | 完整解析流程 |
| 错误处理 | 各错误场景 |

---

## 七、依赖项

### 7.1 Python依赖

```
# requirements.txt
extract-msg>=0.45.0    # MSG解析库(首选)
olefile>=0.46          # OLE文件解析(备用)
```

### 7.2 系统依赖

- Python 3.8+
- Windows/macOS/Linux

---

## 八、交付物清单

| 交付物 | 文件路径 | 状态 |
|--------|----------|------|
| MSG解析模块 | `src/content/msg_parser.py` | ⏳ |
| 单元测试 | `src/tests/test_msg_parser.py` | ⏳ |
| UI集成 | `src/ui/content_import.py` | ⏳ |
| 依赖配置 | `requirements.txt` | ⏳ |
| 设计文档 | `docs/design_msg_import_v1.0.md` | ✅ |
| 测试用例 | `docs/test_cases_msg_import_v1.0.md` | ⏳ |

---

## 九、版本计划

| 版本 | 内容 | 状态 |
|------|------|------|
| V1.0 | 基础MSG解析功能 | 开发中 |
| V1.1 | 优化解析性能、增强错误处理 | 计划中 |

---

## 十、风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| extract-msg库兼容性 | 中 | 提供备用解析方案 |
| MSG格式变化 | 中 | 版本检测和适配 |
| 大文件处理 | 中 | 文件大小限制和流式处理 |

---

**文档版本**: V1.0
**创建日期**: 2026-06-17
**作者**: AI Agent
**状态**: 待评审
