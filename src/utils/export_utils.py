# -*- coding: utf-8 -*-
"""
导出工具模块
提供统一的导出文件名生成功能，自动添加时间戳

版本: V1.0
"""

from datetime import datetime
from typing import Optional


def generate_export_filename(
    prefix: str,
    extension: str,
    include_timestamp: bool = True
) -> str:
    """
    生成导出文件名，自动添加时间戳
    
    Args:
        prefix: 文件名前缀（如 "统计报告"、"任务列表"）
        extension: 文件扩展名（如 "xlsx"、"json"、"csv"）
        include_timestamp: 是否包含时间戳，默认 True
        
    Returns:
        str: 生成的完整文件名
        
    Examples:
        >>> generate_export_filename("统计报告", "xlsx")
        '统计报告_20260618_164500.xlsx'
        
        >>> generate_export_filename("任务列表", "csv", include_timestamp=False)
        '任务列表.csv'
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 清理扩展名
    if extension.startswith('.'):
        extension = extension[1:]
    
    if include_timestamp:
        return f"{prefix}_{timestamp}.{extension}"
    else:
        return f"{prefix}.{extension}"


def get_timestamp() -> str:
    """获取当前时间戳字符串"""
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def format_datetime(dt: Optional[datetime] = None, format_str: str = '%Y%m%d_%H%M%S') -> str:
    """
    格式化日期时间
    
    Args:
        dt: 日期时间对象，None 则使用当前时间
        format_str: 格式字符串
        
    Returns:
        str: 格式化后的日期时间字符串
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format_str)


# 导出文件名前缀常量
class ExportPrefix:
    """导出文件名前缀常量"""
    # 统计报表
    STATISTICS_REPORT = "统计报告"
    TASK_SUMMARY = "任务统计"
    
    # 任务相关
    TASK_LIST = "任务列表"
    TASK_EXPORT = "任务导出"
    
    # 通讯录相关
    CONTACTS = "通讯录"
    CONTACTS_EXPORT = "通讯录导出"
    
    # 推荐库相关
    RECOMMENDATIONS = "推荐库"
    RECOMMENDATIONS_EXPORT = "推荐库导出"
    
    # 操作历史
    OPERATION_HISTORY = "操作历史"
    HISTORY_EXPORT = "历史记录"
    
    # 映射学习
    MAPPING_RULES = "映射规则"
    MAPPING_EXPORT = "映射学习导出"
    
    # 验收报告
    ACCEPTANCE_REPORT = "验收报告"
    TEST_REPORT = "测试报告"
    
    # 日志导出
    AUDIT_LOG = "审计日志"
    LOG_EXPORT = "日志导出"


# 导出文件扩展名常量
class ExportExtension:
    """导出文件扩展名常量"""
    EXCEL = "xlsx"
    CSV = "csv"
    JSON = "json"
    TXT = "txt"
    HTML = "html"
    MARKDOWN = "md"
    PDF = "pdf"
    GZIP = "json.gz"
