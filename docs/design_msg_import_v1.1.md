# MSG邮件文件导入功能设计方案 V1.1

## 一、版本概述

### 1.1 变更说明

| 优化项 | V1.0现状 | V1.1改进 | 优先级 |
|--------|----------|----------|--------|
| 错误上下文信息 | 简单错误信息 | 详细的错误上下文（文件名、行号、堆栈） | P1 |
| 解析进度回调 | 无 | 支持进度回调，支持取消操作 | P2 |
| 流式解析大文件 | 全量加载内存 | 分块读取，内存限制 | P2 |

### 1.2 目标

- 提升错误诊断能力
- 改善大文件处理性能
- 支持用户交互反馈
- 保持代码质量优秀

---

## 二、技术方案

### 2.1 错误上下文增强

#### 2.1.1 问题分析

V1.0的错误处理存在以下问题：
- 错误信息过于简单
- 缺少文件上下文
- 无法追踪错误来源

#### 2.1.2 解决方案

```python
@dataclass
class ParseError:
    """解析错误详细信息"""
    error_type: str           # 错误类型
    error_message: str       # 错误信息
    filepath: str           # 文件路径
    file_size: int          # 文件大小
    timestamp: str          # 发生时间
    context: Dict[str, Any] # 额外上下文
    
    def to_user_message(self) -> str:
        """生成用户友好的错误消息"""
        msg = f"解析失败: {self.error_message}\n"
        msg += f"文件: {self.filepath}\n"
        if self.file_size:
            msg += f"大小: {self.file_size / 1024:.1f} KB\n"
        msg += f"时间: {self.timestamp}"
        return msg

class MSGParserV1_1:
    """增强版MSG解析器"""
    
    def parse_file(self, filepath: str) -> MSGEmail:
        """解析MSG文件，详细的错误报告"""
        error_context = {
            'filepath': filepath,
            'file_size': 0,
            'parse_stage': 'init'
        }
        
        try:
            # 验证文件存在
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"文件不存在: {filepath}")
            
            error_context['file_size'] = os.path.getsize(filepath)
            error_context['parse_stage'] = 'file_validated'
            
            # ... 解析逻辑 ...
            
        except FileNotFoundError as e:
            raise self._create_error(e, error_context, 'file_not_found')
        except ValueError as e:
            raise self._create_error(e, error_context, 'value_error')
        except Exception as e:
            raise self._create_error(e, error_context, 'unknown')
    
    def _create_error(self, exc: Exception, context: Dict, error_type: str) -> ParseError:
        """创建详细错误信息"""
        return ParseError(
            error_type=error_type,
            error_message=str(exc),
            filepath=context.get('filepath', ''),
            file_size=context.get('file_size', 0),
            timestamp=datetime.now().isoformat(),
            context=context
        )
```

### 2.2 进度回调机制

#### 2.2.1 设计方案

```python
from typing import Callable, Optional
from dataclasses import dataclass

@dataclass
class ParseProgress:
    """解析进度信息"""
    current: int             # 当前处理数量
    total: int               # 总数
    current_file: str        # 当前处理的文件
    percentage: float        # 百分比
    status: str              # 状态 (processing/completed/error/cancelled)

class MSGParserWithProgress:
    """带进度回调的MSG解析器"""
    
    def __init__(self, 
                 progress_callback: Optional[Callable[[ParseProgress], None]] = None,
                 cancel_check: Optional[Callable[[], bool]] = None):
        """
        Args:
            progress_callback: 进度回调函数
            cancel_check: 取消检查函数，返回True表示取消
        """
        self.progress_callback = progress_callback
        self.cancel_check = cancel_check
    
    def parse_batch(self, filepaths: List[str]) -> List[MSGEmail]:
        """批量解析，带进度回调"""
        results = []
        total = len(filepaths)
        
        for i, filepath in enumerate(filepaths):
            # 检查是否取消
            if self.cancel_check and self.cancel_check():
                self._report_progress(i, total, filepath, 'cancelled')
                break
            
            # 报告进度
            self._report_progress(i, total, filepath, 'processing')
            
            try:
                email = self.parse_file(filepath)
                results.append(email)
                self._report_progress(i + 1, total, filepath, 'completed')
            except Exception as e:
                self._report_progress(i + 1, total, filepath, 'error')
                # 可选择跳过错误或收集
                continue
        
        return results
    
    def _report_progress(self, current: int, total: int, 
                        filepath: str, status: str):
        """报告进度"""
        if self.progress_callback:
            progress = ParseProgress(
                current=current,
                total=total,
                current_file=os.path.basename(filepath),
                percentage=(current / total * 100) if total > 0 else 0,
                status=status
            )
            self.progress_callback(progress)
```

#### 2.2.2 使用示例

```python
def my_progress_callback(progress: ParseProgress):
    """自定义进度回调"""
    print(f"[{progress.percentage:.1f}%] {progress.current_file} - {progress.status}")
    # 可更新UI进度条

def should_cancel() -> bool:
    """检查是否应取消"""
    return user_clicked_cancel_button

parser = MSGParserWithProgress(
    progress_callback=my_progress_callback,
    cancel_check=should_cancel
)

results = parser.parse_batch(['file1.msg', 'file2.msg', ...])
```

### 2.3 流式解析大文件

#### 2.3.1 问题分析

V1.0的问题：
- 大文件一次性加载到内存
- 没有内存使用限制
- 可能导致内存溢出

#### 2.3.2 解决方案

```python
class StreamingMSGParser:
    """流式MSG解析器，处理大文件"""
    
    # 内存限制（默认50MB）
    DEFAULT_MEMORY_LIMIT = 50 * 1024 * 1024
    
    # 分块大小（1MB）
    CHUNK_SIZE = 1024 * 1024
    
    def __init__(self, memory_limit: int = None):
        self.memory_limit = memory_limit or self.DEFAULT_MEMORY_LIMIT
    
    def parse_large_file(self, filepath: str) -> MSGEmail:
        """流式解析大文件，控制内存使用"""
        
        file_size = os.path.getsize(filepath)
        
        # 小文件直接解析
        if file_size < self.CHUNK_SIZE * 2:
            return self._parse_standard(filepath)
        
        # 大文件使用流式解析
        return self._parse_streaming(filepath, file_size)
    
    def _parse_streaming(self, filepath: str, file_size: int) -> MSGEmail:
        """流式解析实现"""
        email = MSGEmail()
        
        with open(filepath, 'rb') as f:
            # 1. 读取文件头（包含元数据）
            header = f.read(self.CHUNK_SIZE)
            self._parse_header(header, email)
            
            # 2. 检查内存使用
            self._check_memory_usage(file_size)
            
            # 3. 分块读取正文
            body_parts = []
            while True:
                chunk = f.read(self.CHUNK_SIZE)
                if not chunk:
                    break
                body_parts.append(chunk)
                
                # 定期检查内存
                if len(body_parts) % 10 == 0:
                    self._check_memory_usage(file_size)
            
            # 4. 合并正文
            body = b''.join(body_parts)
            email.body = self._decode_body(body)
        
        return email
    
    def _check_memory_usage(self, file_size: int):
        """检查内存使用，超过限制则抛出警告"""
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        if memory_info.rss > self.memory_limit:
            raise MemoryWarning(
                f"内存使用超过限制: {memory_info.rss / 1024 / 1024:.1f}MB "
                f"限制: {self.memory_limit / 1024 / 1024:.1f}MB"
            )
```

---

## 三、API兼容性

### 3.1 V1.0兼容

V1.1保持对V1.0 API的完全兼容：

```python
# V1.0 API - 继续支持
email = MSGParser.parse_file("test.msg")
email = MSGParser.parse_file_safe("test.msg")

# V1.1 新API - 可选使用
parser = MSGParserWithProgress(callback)
parser.parse_batch(files)
```

### 3.2 新增API

```python
# 错误详情
error = ParseError(...)
print(error.to_user_message())

# 进度回调
parser = MSGParserWithProgress(progress_callback=func)

# 流式解析
parser = StreamingMSGParser(memory_limit=100*1024*1024)
```

---

## 四、测试策略

### 4.1 新增测试用例

| 测试项 | 测试内容 |
|--------|----------|
| ParseError创建 | 错误信息完整性 |
| ParseError用户消息 | 消息格式化 |
| 进度回调触发 | 各阶段回调调用 |
| 取消操作 | cancel_check生效 |
| 流式解析内存限制 | 内存超限处理 |
| 大文件分块处理 | 分块读取正确 |

### 4.2 性能测试

| 指标 | 目标 |
|------|------|
| 进度回调延迟 | <100ms |
| 内存峰值(100MB文件) | <60MB |
| 取消操作响应 | <500ms |

---

## 五、交付物

| 文件 | 说明 | 状态 |
|------|------|------|
| `msg_parser.py` | 增强版解析器 | ⏳ |
| `test_msg_parser_v1.1.py` | 新增测试 | ⏳ |
| `design_msg_import_v1.1.md` | 设计文档 | ✅ |

---

## 六、版本计划

| 版本 | 内容 | 状态 |
|------|------|------|
| V1.0 | 基础解析功能 | ✅ 完成 |
| V1.1 | 错误上下文、进度回调、流式解析 | ⏳ 开发中 |

---

**文档版本**: V1.1
**创建日期**: 2026-06-18
**作者**: AI Agent
**状态**: 待评审
