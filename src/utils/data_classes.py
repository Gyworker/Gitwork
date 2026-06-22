# -*- coding: utf-8 -*-
"""
数据类定义模块
Data Classes Module:

提供各种业务数据类的定义，用于替代过多参数传递
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class TaskFilter:
    """任务筛选条件数据类"""
    status: Optional[str] = None
    urgency: Optional[str] = None
    inquirer: Optional[str] = None
    respondent: Optional[str] = None
    key_module: Optional[str] = None
    industry: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search_keyword: Optional[str] = None
    limit: int = 100
    offset: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class TaskCreateData:
    """任务创建数据类"""
    task_name: str
    urgency: str = "中"
    inquirer: str = ""
    inquirer_dept: str = ""
    inquirer_company: str = ""
    inquirer_phone: str = ""
    inquirer_email: str = ""
    respondent: str = ""
    respondent_dept: str = ""
    respondent_phone: str = ""
    respondent_email: str = ""
    industry: str = ""
    key_module: str = ""
    task_content: str = ""
    expected_reply_time: Optional[datetime] = None
    remark: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        if self.expected_reply_time:
            data["expected_reply_time"] = self.expected_reply_time.isoformat()
        return data


@dataclass
class TaskUpdateData:
    """任务更新数据类"""
    task_id: str
    task_name: Optional[str] = None
    urgency: Optional[str] = None
    status: Optional[str] = None
    respondent: Optional[str] = None
    respondent_dept: Optional[str] = None
    respondent_phone: Optional[str] = None
    respondent_email: Optional[str] = None
    key_module: Optional[str] = None
    task_content: Optional[str] = None
    expected_reply_time: Optional[datetime] = None
    reply_content: Optional[str] = None
    reply_status: Optional[str] = None
    remark: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，移除None值"""
        result = {"task_id": self.task_id}
        for k, v in asdict(self).items():
            if k != "task_id" and v is not None:
                if isinstance(v, datetime):
                    result[k] = v.isoformat()
                else:
                    result[k] = v
        return result


@dataclass
class ReminderConfig:
    """提醒配置数据类"""
    urgency: str
    reminder_interval: int = 4  # 小时
    daily_max_reminders: int = 4
    extra_reminder_times: List[str] = field(default_factory=list)
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReminderConfig":
        """从字典创建"""
        return cls(
            urgency=data.get("urgency", ""),
            reminder_interval=data.get("reminder_interval", 4),
            daily_max_reminders=data.get("daily_max_reminders", 4),
            extra_reminder_times=data.get("extra_reminder_times", []),
            enabled=data.get("enabled", True)
        )


@dataclass
class WeChatMessageData:
    """企业微信消息数据类"""
    msg_type: str = "markdown"
    content: str = ""
    mentioned_list: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为企业微信API格式"""
        result = {"msgtype": self.msg_type}
        if self.msg_type == "markdown":
            result["markdown"] = {"content": self.content}
        elif self.msg_type == "text":
            result["text"] = {
                "content": self.content,
                "mentioned_list": self.mentioned_list
            }
        return result


@dataclass
class BackupConfig:
    """备份配置数据类"""
    backup_path: str = "backups"
    max_backups: int = 10
    backup_frequency: str = "daily"  # hourly, daily, weekly
    backup_on_startup: bool = False
    backup_on_shutdown: bool = True
    compression_enabled: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackupConfig":
        """从字典创建"""
        return cls(
            backup_path=data.get("backup_path", "backups"),
            max_backups=data.get("max_backups", 10),
            backup_frequency=data.get("backup_frequency", "daily"),
            backup_on_startup=data.get("backup_on_startup", False),
            backup_on_shutdown=data.get("backup_on_shutdown", True),
            compression_enabled=data.get("compression_enabled", True)
        )


@dataclass
class LearningContact:
    """学习联系人数据类"""
    name: str
    employee_id: Optional[str] = None
    department: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    source_type: str = "task"
    task_count: int = 0
    confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class LearningRecommendation:
    """学习推荐库数据类"""
    respondent_name: str
    employee_id: Optional[str] = None
    department: Optional[str] = None
    industry: Optional[str] = None
    key_module: str = ""
    all_modules: str = ""
    task_count: int = 0
    reply_count: int = 0
    confidence: float = 0.5

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearningRecommendation":
        """从字典创建"""
        return cls(
            respondent_name=data.get("respondent_name", ""),
            employee_id=data.get("employee_id"),
            department=data.get("department"),
            industry=data.get("industry"),
            key_module=data.get("key_module", ""),
            all_modules=data.get("all_modules", ""),
            task_count=data.get("task_count", 0),
            reply_count=data.get("reply_count", 0),
            confidence=data.get("confidence", 0.5)
        )


@dataclass
class ExcelImportOptions:
    """Excel导入选项数据类"""
    sheet_name: Optional[str] = None
    header_row: int = 0
    skip_rows: int = 0
    encoding: str = "utf-8"
    date_format: str = "%Y-%m-%d"
    skip_errors: bool = True
    update_existing: bool = True
    field_mapping: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExcelImportOptions":
        """从字典创建"""
        return cls(
            sheet_name=data.get("sheet_name"),
            header_row=data.get("header_row", 0),
            skip_rows=data.get("skip_rows", 0),
            encoding=data.get("encoding", "utf-8"),
            date_format=data.get("date_format", "%Y-%m-%d"),
            skip_errors=data.get("skip_errors", True),
            update_existing=data.get("update_existing", True),
            field_mapping=data.get("field_mapping", {})
        )


@dataclass
class ImportResult:
    """导入结果数据类"""
    success: bool
    total_rows: int = 0
    imported_rows: int = 0
    updated_rows: int = 0
    failed_rows: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "total_rows": self.total_rows,
            "imported_rows": self.imported_rows,
            "updated_rows": self.updated_rows,
            "failed_rows": self.failed_rows,
            "errors": self.errors,
            "warnings": self.warnings
        }


@dataclass
class ExportOptions:
    """导出选项数据类"""
    format: str = "xlsx"  # xlsx, csv
    columns: List[str] = field(default_factory=list)
    include_headers: bool = True
    date_format: str = "%Y-%m-%d %H:%M:%S"
    sheet_name: str = "数据"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExportOptions":
        """从字典创建"""
        return cls(
            format=data.get("format", "xlsx"),
            columns=data.get("columns", []),
            include_headers=data.get("include_headers", True),
            date_format=data.get("date_format", "%Y-%m-%d %H:%M:%S"),
            sheet_name=data.get("sheet_name", "数据")
        )
