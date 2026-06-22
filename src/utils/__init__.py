# -*- coding: utf-8 -*-
"""Utils包初始化文件"""

# 导出异常处理模块
from .exception_handler import (
    AppException,
    DatabaseException,
    ValidationException,
    FileOperationException,
    NetworkException,
    ServiceException,
    safe_execute,
    handle_database_error,
    handle_file_error,
    handle_network_error,
    ErrorHandler,
    try_except
)

# 导出数据类模块
from .data_classes import (
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

__all__ = [
    # 异常处理
    'AppException',
    'DatabaseException',
    'ValidationException',
    'FileOperationException',
    'NetworkException',
    'ServiceException',
    'safe_execute',
    'handle_database_error',
    'handle_file_error',
    'handle_network_error',
    'ErrorHandler',
    'try_except',
    # 数据类
    'TaskFilter',
    'TaskCreateData',
    'TaskUpdateData',
    'ReminderConfig',
    'WeChatMessageData',
    'BackupConfig',
    'LearningContact',
    'LearningRecommendation',
    'ExcelImportOptions',
    'ImportResult',
    'ExportOptions',
]
