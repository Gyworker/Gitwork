# -*- coding: utf-8 -*-
"""
工具函数模块
Helper Functions Module

提供常用的工具函数
"""

import hashlib
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union


def generate_id() -> str:
    """
    生成唯一ID

    Returns:
        唯一ID字符串
    """
    return str(uuid.uuid4())


def generate_short_id() -> str:
    """
    生成短唯一ID

    Returns:
        8位唯一ID字符串
    """
    return uuid.uuid4().hex[:8]


def md5_hash(text: str) -> str:
    """
    计算MD5哈希值

    Args:
        text: 输入文本

    Returns:
        MD5哈希值
    """
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def get_current_timestamp() -> int:
    """
    获取当前时间戳（秒）

    Returns:
        当前时间戳
    """
    return int(datetime.now().timestamp())


def get_current_timestamp_ms() -> int:
    """
    获取当前时间戳（毫秒）

    Returns:
        当前时间戳（毫秒）
    """
    return int(datetime.now().timestamp() * 1000)


def timestamp_to_datetime(timestamp: int) -> datetime:
    """
    时间戳转换为datetime对象

    Args:
        timestamp: 时间戳（秒）

    Returns:
        datetime对象
    """
    return datetime.fromtimestamp(timestamp)


def datetime_to_timestamp(dt: datetime) -> int:
    """
    datetime对象转换为时间戳

    Args:
        dt: datetime对象

    Returns:
        时间戳（秒）
    """
    return int(dt.timestamp())


def format_datetime(
    dt: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    格式化日期时间

    Args:
        dt: datetime对象，默认为当前时间
        format_str: 格式化字符串

    Returns:
        格式化后的日期时间字符串
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format_str)


def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    解析日期时间字符串

    Args:
        date_str: 日期时间字符串
        format_str: 格式化字符串

    Returns:
        datetime对象
    """
    return datetime.strptime(date_str, format_str)


def get_date_range(days: int = 7) -> Tuple[datetime, datetime]:
    """
    获取日期范围

    Args:
        days: 天数

    Returns:
        (开始日期, 结束日期)元组
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def is_valid_email(email: str) -> bool:
    """
    验证邮箱格式

    Args:
        email: 邮箱地址

    Returns:
        是否有效
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_phone(phone: str) -> bool:
    """
    验证手机号格式

    Args:
        phone: 手机号

    Returns:
        是否有效
    """
    pattern = r"^1[3-9]\d{9}$"
    return bool(re.match(pattern, phone))


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    # 移除非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    filename = re.sub(illegal_chars, "_", filename)
    # 移除首尾空格和点
    filename = filename.strip().strip(".")
    # 限制长度
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[: 255 - len(ext) - 1] + "." + ext if ext else name[:255]
    return filename


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    截断字符串

    Args:
        text: 原始字符串
        max_length: 最大长度
        suffix: 后缀

    Returns:
        截断后的字符串
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """
    安全除法

    Args:
        a: 被除数
        b: 除数
        default: 默认值

    Returns:
        除法结果
    """
    try:
        return a / b if b != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    将列表分块

    Args:
        lst: 原始列表
        chunk_size: 块大小

    Returns:
        分块后的列表
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """
    扁平化字典

    Args:
        d: 原始字典
        parent_key: 父键
        sep: 分隔符

    Returns:
        扁平化后的字典
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def merge_dicts(*dicts: Dict) -> Dict:
    """
    合并多个字典

    Args:
        *dicts: 字典列表

    Returns:
        合并后的字典
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def filter_dict(d: Dict, keys: List[str]) -> Dict:
    """
    过滤字典，只保留指定的键

    Args:
        d: 原始字典
        keys: 要保留的键列表

    Returns:
        过滤后的字典
    """
    return {k: v for k, v in d.items() if k in keys}


def remove_none_values(d: Dict) -> Dict:
    """
    移除字典中的None值

    Args:
        d: 原始字典

    Returns:
        移除None值后的字典
    """
    return {k: v for k, v in d.items() if v is not None}


def calculate_percentage(part: Union[int, float], total: Union[int, float]) -> float:
    """
    计算百分比

    Args:
        part: 部分值
        total: 总值

    Returns:
        百分比（0-100）
    """
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 文件大小（字节）

    Returns:
        格式化后的大小字符串
    """
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"
