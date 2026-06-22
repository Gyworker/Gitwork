# -*- coding: utf-8 -*-
"""
数据类模块单元测试
Data Classes Unit Tests:

测试数据类模块的功能
"""

import pytest
from datetime import datetime
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.data_classes import (
    TaskFilter,
    TaskCreateData,
    TaskUpdateData,
    ReminderConfig,
    WeChatMessageData,
    BackupConfig,
    LearningContact,
    LearningRecommendation,
    ExcelImportOptions,
    ImportResult,
    ExportOptions
)


class TestTaskFilter:
    """测试任务筛选数据类"""

    def test_default_values(self):
        """测试默认值"""
        filter_obj = TaskFilter()
        assert filter_obj.status is None
        assert filter_obj.urgency is None
        assert filter_obj.limit == 100
        assert filter_obj.offset == 0

    def test_with_values(self):
        """测试设置值"""
        filter_obj = TaskFilter(
            status="进行中",
            urgency="高",
            limit=50
        )
        assert filter_obj.status == "进行中"
        assert filter_obj.urgency == "高"
        assert filter_obj.limit == 50

    def test_to_dict(self):
        """测试转换为字典"""
        filter_obj = TaskFilter(status="已答复", limit=20)
        result = filter_obj.to_dict()
        assert "status" in result
        assert "limit" in result
        assert result["status"] == "已答复"
        assert result["limit"] == 20
        # None值应被排除
        assert "urgency" not in result or result.get("urgency") is not None


class TestTaskCreateData:
    """测试任务创建数据类"""

    def test_required_field(self):
        """测试必需字段"""
        data = TaskCreateData(task_name="测试任务")
        assert data.task_name == "测试任务"
        assert data.urgency == "中"  # 默认值

    def test_full_data(self):
        """测试完整数据"""
        data = TaskCreateData(
            task_name="测试任务",
            urgency="高",
            inquirer="张三",
            inquirer_dept="技术部",
            expected_reply_time=datetime(2026, 6, 30)
        )
        assert data.urgency == "高"
        assert data.inquirer == "张三"
        assert data.expected_reply_time == datetime(2026, 6, 30)

    def test_to_dict(self):
        """测试转换为字典"""
        data = TaskCreateData(
            task_name="测试",
            urgency="中"
        )
        result = data.to_dict()
        assert result["task_name"] == "测试"
        assert result["urgency"] == "中"
        assert isinstance(result["expected_reply_time"], str)  # datetime被转换


class TestTaskUpdateData:
    """测试任务更新数据类"""

    def test_partial_update(self):
        """测试部分更新"""
        data = TaskUpdateData(
            task_id="T001",
            status="已完成",
            remark="更新备注"
        )
        assert data.task_id == "T001"
        assert data.status == "已完成"
        assert data.respondent is None  # 未设置

    def test_to_dict_removes_none(self):
        """测试转换为字典移除None"""
        data = TaskUpdateData(
            task_id="T001",
            status="已完成"
        )
        result = data.to_dict()
        assert "task_id" in result
        assert "status" in result
        assert "remark" not in result  # None值应被排除


class TestReminderConfig:
    """测试提醒配置数据类"""

    def test_default_values(self):
        """测试默认值"""
        config = ReminderConfig(urgency="高")
        assert config.reminder_interval == 4
        assert config.daily_max_reminders == 4
        assert config.enabled is True

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "urgency": "中",
            "reminder_interval": 3,
            "daily_max_reminders": 5,
            "extra_reminder_times": ["09:00", "17:00"],
            "enabled": True
        }
        config = ReminderConfig.from_dict(data)
        assert config.urgency == "中"
        assert config.reminder_interval == 3
        assert len(config.extra_reminder_times) == 2


class TestWeChatMessageData:
    """测试企业微信消息数据类"""

    def test_markdown_message(self):
        """测试Markdown消息"""
        msg = WeChatMessageData(
            msg_type="markdown",
            content="# 测试标题\n这是内容"
        )
        result = msg.to_dict()
        assert result["msgtype"] == "markdown"
        assert "markdown" in result

    def test_text_message(self):
        """测试文本消息"""
        msg = WeChatMessageData(
            msg_type="text",
            content="测试内容",
            mentioned_list=["user1", "user2"]
        )
        result = msg.to_dict()
        assert result["msgtype"] == "text"
        assert result["text"]["content"] == "测试内容"
        assert len(result["text"]["mentioned_list"]) == 2


class TestBackupConfig:
    """测试备份配置数据类"""

    def test_default_values(self):
        """测试默认值"""
        config = BackupConfig()
        assert config.backup_path == "backups"
        assert config.max_backups == 10
        assert config.backup_frequency == "daily"
        assert config.backup_on_startup is False
        assert config.backup_on_shutdown is True

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "backup_path": "/custom/path",
            "max_backups": 20,
            "backup_frequency": "hourly"
        }
        config = BackupConfig.from_dict(data)
        assert config.backup_path == "/custom/path"
        assert config.max_backups == 20
        assert config.backup_frequency == "hourly"


class TestLearningContact:
    """测试学习联系人数据类"""

    def test_required_fields(self):
        """测试必需字段"""
        contact = LearningContact(name="张三")
        assert contact.name == "张三"
        assert contact.confidence == 0.5  # 默认值

    def test_full_data(self):
        """测试完整数据"""
        contact = LearningContact(
            name="张三",
            employee_id="E001",
            department="技术部",
            company="示例公司",
            industry="IT",
            task_count=10,
            confidence=0.9
        )
        assert contact.employee_id == "E001"
        assert contact.task_count == 10
        assert contact.confidence == 0.9

    def test_to_dict(self):
        """测试转换为字典"""
        contact = LearningContact(name="李四", task_count=5)
        result = contact.to_dict()
        assert result["name"] == "李四"
        assert result["task_count"] == 5


class TestLearningRecommendation:
    """测试学习推荐库数据类"""

    def test_required_fields(self):
        """测试必需字段"""
        rec = LearningRecommendation(respondent_name="王五")
        assert rec.respondent_name == "王五"

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "respondent_name": "赵六",
            "key_module": "模块A",
            "task_count": 15,
            "confidence": 0.85
        }
        rec = LearningRecommendation.from_dict(data)
        assert rec.respondent_name == "赵六"
        assert rec.key_module == "模块A"
        assert rec.confidence == 0.85


class TestExcelImportOptions:
    """测试Excel导入选项数据类"""

    def test_default_values(self):
        """测试默认值"""
        options = ExcelImportOptions()
        assert options.sheet_name is None
        assert options.header_row == 0
        assert options.skip_errors is True
        assert options.update_existing is True

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "sheet_name": "Sheet1",
            "header_row": 1,
            "skip_rows": 2,
            "field_mapping": {"A": "name", "B": "value"}
        }
        options = ExcelImportOptions.from_dict(data)
        assert options.sheet_name == "Sheet1"
        assert options.header_row == 1
        assert len(options.field_mapping) == 2


class TestImportResult:
    """测试导入结果数据类"""

    def test_success_result(self):
        """测试成功结果"""
        result = ImportResult(
            success=True,
            total_rows=100,
            imported_rows=80,
            updated_rows=15,
            failed_rows=5
        )
        assert result.success is True
        assert result.total_rows == 100
        assert result.imported_rows == 80

    def test_with_errors(self):
        """测试带错误的结果"""
        result = ImportResult(
            success=False,
            total_rows=100,
            imported_rows=50,
            failed_rows=50,
            errors=["行1错误", "行2错误"],
            warnings=["行3警告"]
        )
        assert len(result.errors) == 2
        assert len(result.warnings) == 1

    def test_to_dict(self):
        """测试转换为字典"""
        result = ImportResult(success=True, total_rows=10)
        data = result.to_dict()
        assert data["success"] is True
        assert data["total_rows"] == 10


class TestExportOptions:
    """测试导出选项数据类"""

    def test_default_values(self):
        """测试默认值"""
        options = ExportOptions()
        assert options.format == "xlsx"
        assert options.include_headers is True
        assert options.sheet_name == "数据"

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "format": "csv",
            "columns": ["name", "value"],
            "date_format": "%Y/%m/%d"
        }
        options = ExportOptions.from_dict(data)
        assert options.format == "csv"
        assert len(options.columns) == 2
        assert options.date_format == "%Y/%m/%d"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
