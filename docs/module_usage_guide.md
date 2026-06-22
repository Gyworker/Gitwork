# 新增模块使用说明

## 概述

本文档说明V5.1优化中新增的模块及其使用方法。

---

## 1. 统一异常处理模块

**文件**: `src/utils/exception_handler.py`

### 1.1 自定义异常类

```python
from src.utils.exception_handler import (
    AppException,
    DatabaseException,
    ValidationException,
    FileOperationException,
    NetworkException,
    ServiceException
)

# 使用示例
raise DatabaseException("数据库连接失败", details={"host": "localhost"})
```

### 1.2 异常处理装饰器

#### safe_execute 装饰器
```python
from src.utils.exception_handler import safe_execute

@safe_execute(default_return=False, error_message="操作失败")
def risky_operation():
    # 可能抛出异常的操作
    pass
```

#### handle_database_error 装饰器
```python
from src.utils.exception_handler import handle_database_error

@handle_database_error
def query_database():
    # 数据库操作
    pass
```

#### handle_file_error 装饰器
```python
from src.utils.exception_handler import handle_file_error

@handle_file_error(default_return=None)
def read_file():
    with open("data.txt", "r") as f:
        return f.read()
```

#### handle_network_error 装饰器
```python
from src.utils.exception_handler import handle_network_error

@handle_network_error(default_return=None, retry_count=2)
def fetch_data():
    response = requests.get("https://api.example.com")
    return response.json()
```

### 1.3 ErrorHandler 工具类
```python
from src.utils.exception_handler import ErrorHandler

# 分类错误
category = ErrorHandler.categorize_error(ValueError("test"))
# category = "validation"

# 格式化错误信息
info = ErrorHandler.format_error_info(error, include_traceback=True)
```

---

## 2. 数据类模块

**文件**: `src/utils/data_classes.py`

### 2.1 任务相关数据类

#### TaskFilter - 任务筛选
```python
from src.utils.data_classes import TaskFilter

filter_obj = TaskFilter(
    status="进行中",
    urgency="高",
    limit=50
)
```

#### TaskCreateData - 任务创建
```python
from src.utils.data_classes import TaskCreateData
from datetime import datetime

task = TaskCreateData(
    task_name="测试任务",
    urgency="高",
    inquirer="张三",
    expected_reply_time=datetime(2026, 6, 30)
)
```

#### TaskUpdateData - 任务更新
```python
from src.utils.data_classes import TaskUpdateData

update = TaskUpdateData(
    task_id="T001",
    status="已完成",
    remark="更新备注"
)
```

### 2.2 配置相关数据类

#### BackupConfig - 备份配置
```python
from src.utils.data_classes import BackupConfig

config = BackupConfig(
    backup_path="/custom/path",
    backup_frequency="hourly",
    max_backups=20
)
```

#### ReminderConfig - 提醒配置
```python
from src.utils.data_classes import ReminderConfig

config = ReminderConfig(
    urgency="高",
    reminder_interval=3,
    daily_max_reminders=6,
    extra_reminder_times=["09:00", "17:00"]
)
```

### 2.3 导入导出数据类

#### ExcelImportOptions - 导入选项
```python
from src.utils.data_classes import ExcelImportOptions

options = ExcelImportOptions(
    sheet_name="数据",
    header_row=1,
    field_mapping={"A": "name", "B": "value"}
)
```

#### ImportResult - 导入结果
```python
from src.utils.data_classes import ImportResult

result = ImportResult(
    success=True,
    total_rows=100,
    imported_rows=80,
    failed_rows=5,
    errors=["行10格式错误"]
)
```

---

## 3. 单元测试

**文件**: `src/tests/test_exception_handler.py`
**文件**: `src/tests/test_data_classes.py`

### 运行测试
```bash
cd src/market_task_tracker
py -m pytest src/tests/test_exception_handler.py -v
py -m pytest src/tests/test_data_classes.py -v
```

### 测试覆盖

#### 异常处理模块测试
- ✅ 自定义异常类测试
- ✅ safe_execute装饰器测试
- ✅ handle_database_error装饰器测试
- ✅ handle_file_error装饰器测试
- ✅ handle_network_error装饰器测试
- ✅ ErrorHandler工具类测试
- ✅ try_except装饰器测试

#### 数据类模块测试
- ✅ TaskFilter 测试
- ✅ TaskCreateData 测试
- ✅ TaskUpdateData 测试
- ✅ ReminderConfig 测试
- ✅ BackupConfig 测试
- ✅ LearningContact 测试
- ✅ LearningRecommendation 测试
- ✅ ExcelImportOptions 测试
- ✅ ImportResult 测试
- ✅ ExportOptions 测试

---

## 4. 迁移指南

### 4.1 旧代码迁移

#### 替换直接except Exception
```python
# 旧代码
try:
    do_something()
except Exception as e:
    logger.error(f"操作失败: {e}")
    return False

# 新代码
from src.utils.exception_handler import safe_execute

@safe_execute(default_return=False, error_message="操作失败")
def do_something():
    # 操作逻辑
    pass
```

#### 替换多参数传递
```python
# 旧代码
def create_task(name, urgency, inquirer, dept, company, phone, email, ...):
    pass

# 新代码
from src.utils.data_classes import TaskCreateData

def create_task(task_data: TaskCreateData):
    pass

task = TaskCreateData(name="...", urgency="...", ...)
create_task(task)
```

---

## 5. 最佳实践

1. **异常处理**: 优先使用提供的装饰器，避免裸except Exception
2. **数据传递**: 使用数据类替代多参数传递，提高代码可读性
3. **日志记录**: 使用合适的日志级别（debug/info/warning/error）
4. **单元测试**: 新增功能需要同步编写单元测试
5. **文档更新**: 新模块需要更新相关使用文档

---

**更新时间**: 2026-06-22
**版本**: V5.1
