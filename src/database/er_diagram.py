# -*- coding: utf-8 -*-
"""
数据库访问层 (M-4优化版)
Database Access Layer

提供数据库操作的封装

M-4优化内容：
1. 基础DAO类 - 提取公共CRUD逻辑
2. 动态列名获取 - 从数据库表结构动态获取
3. LRU查询缓存 - 减少数据库查询次数
4. 批量操作支持 - 优化大量数据操作
5. 索引优化 - 自动检查和优化建议

版本：V4.4
"""

import functools
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Type, Callable

from .connection import get_db_connection
from ..utils.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# 查询缓存装饰器
# =============================================================================

def cached_query(max_size: int = 100, ttl_seconds: int = 300):
    """
    查询缓存装饰器

    Args:
        max_size: 缓存最大条目数
        ttl_seconds: 缓存有效期（秒）

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        cache: OrderedDict = OrderedDict()

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{args}:{kwargs}"

            # 检查缓存
            now = datetime.now()
            if cache_key in cache:
                cached_time, cached_result = cache[cache_key]
                # 检查是否过期
                if (now - cached_time).total_seconds() < ttl_seconds:
                    # 移动到末尾（最近使用）
                    cache.move_to_end(cache_key)
                    logger.debug(f"缓存命中: {cache_key}")
                    return cached_result

            # 执行查询
            result = func(self, *args, **kwargs)

            # 更新缓存
            cache[cache_key] = (now, result)
            cache.move_to_end(cache_key)

            # 清理超出大小的缓存
            while len(cache) > max_size:
                cache.popitem(last=False)

            return result

        # 添加清除缓存方法
        wrapper.clear_cache = lambda: cache.clear()

        return wrapper

    return decorator


# =============================================================================
# 基础DAO类
# =============================================================================

class BaseDAO:
    """
    基础数据访问对象

    提供公共的CRUD操作和辅助方法
    子类只需定义表名和列名映射
    """

    # 子类必须定义
    _table_name: str = ""
    _columns: List[str] = []
    _id_column: str = "id"
    _cache_enabled: bool = True
    _cache_ttl: int = 300  # 缓存有效期（秒）

    def __init__(self) -> None:
        """初始化DAO"""
        self._db = get_db_connection()
        self._query_cache: OrderedDict = OrderedDict()
        self._columns_cache: Optional[List[str]] = None

    @property
    def table_name(self) -> str:
        """获取表名"""
        return self._table_name

    @property
    def columns(self) -> List[str]:
        """获取列名列表（动态获取）"""
        if not self._columns_cache:
            self._columns_cache = self._get_table_columns()
        return self._columns_cache or self._columns

    def _get_table_columns(self) -> List[str]:
        """
        从数据库表结构动态获取列名

        Returns:
            列名列表
        """
        try:
            sql = f"PRAGMA table_info({self._table_name})"
            rows = self._db.fetchall(sql)
            return [row[1] for row in rows] if rows else self._columns
        except Exception as e:
            logger.warning(f"获取表结构失败: {self._table_name}, 使用默认列名: {e}")
            return self._columns

    def _clear_cache(self) -> None:
        """清除查询缓存"""
        self._query_cache.clear()

    def _row_to_dict(self, row: Tuple, columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        将数据库行转换为字典（动态列名）

        Args:
            row: 数据库行元组
            columns: 列名列表（可选，默认从表结构获取）

        Returns:
            字典
        """
        if columns is None:
            columns = self.columns

        # 如果列数和行数不匹配，使用默认列名
        if len(columns) != len(row):
            logger.warning(
                f"列数不匹配: 表结构={len(columns)}, 数据={len(row)}, "
                f"表={self._table_name}"
            )
            return dict(zip(self._columns, row))

        return dict(zip(columns, row))

    def _dict_to_row(self, data: Dict[str, Any]) -> Tuple:
        """
        将字典转换为数据库行元组

        Args:
            data: 数据字典

        Returns:
            值元组
        """
        return tuple(data.get(col, None) for col in self.columns)

    def create(self, data: Dict[str, Any]) -> Optional[str]:
        """
        创建记录

        Args:
            data: 数据字典

        Returns:
            记录ID，失败返回None
        """
        try:
            from ..utils.helpers import generate_id

            # 生成ID
            id_field = self._id_column
            record_id = data.get(id_field) or generate_id()
            data[id_field] = record_id

            # 构建SQL
            columns = [k for k in data.keys() if k in self.columns]
            values = [data[k] for k in columns]

            sql = f"INSERT INTO {self._table_name} ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(columns))})"

            self._db.execute(sql, tuple(values), commit=True)
            logger.info(f"{self._table_name}记录创建成功: {record_id}")

            # 清除缓存
            self._clear_cache()

            return record_id
        except Exception as e:
            logger.error(f"创建{self._table_name}记录失败: {e}")
            return None

    def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取记录

        Args:
            record_id: 记录ID

        Returns:
            记录数据字典
        """
        try:
            sql = f"SELECT * FROM {self._table_name} WHERE {self._id_column} = ?"
            row = self._db.fetchone(sql, (record_id,))

            if row:
                return self._row_to_dict(row)
            return None
        except Exception as e:
            logger.error(f"获取{self._table_name}记录失败: {e}")
            return None

    def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取所有记录（支持过滤、分页）

        Args:
            filters: 过滤条件
            order_by: 排序字段
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            记录列表
        """
        try:
            sql = f"SELECT * FROM {self._table_name}"
            params: List[Any] = []

            # 构建WHERE条件
            if filters:
                conditions = []
                for key, value in filters.items():
                    if key in self.columns and value is not None:
                        if isinstance(value, (list, tuple)):
                            placeholders = ', '.join(['?'] * len(value))
                            conditions.append(f"{key} IN ({placeholders})")
                            params.extend(value)
                        else:
                            conditions.append(f"{key} = ?")
                            params.append(value)

                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)

            # 排序
            if order_by:
                if order_by.startswith('-'):
                    sql += f" ORDER BY {order_by[1:]} DESC"
                else:
                    sql += f" ORDER BY {order_by}"

            # 分页
            if limit is not None:
                sql += f" LIMIT {limit}"
                if offset is not None:
                    sql += f" OFFSET {offset}"

            rows = self._db.fetchall(sql, tuple(params) if params else None)
            return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取{self._table_name}列表失败: {e}")
            return []

    def update(self, record_id: str, data: Dict[str, Any]) -> bool:
        """
        更新记录

        Args:
            record_id: 记录ID
            data: 更新数据

        Returns:
            是否成功
        """
        try:
            data["updated_at"] = datetime.now()

            # 只更新存在的列
            columns = [k for k in data.keys() if k in self.columns]
            if not columns:
                return False

            set_clause = ", ".join([f"{k} = ?" for k in columns])
            sql = f"UPDATE {self._table_name} SET {set_clause} WHERE {self._id_column} = ?"

            params = [data[k] for k in columns] + [record_id]
            self._db.execute(sql, tuple(params), commit=True)

            logger.info(f"{self._table_name}记录更新成功: {record_id}")

            # 清除缓存
            self._clear_cache()

            return True
        except Exception as e:
            logger.error(f"更新{self._table_name}记录失败: {e}")
            return False

    def delete(self, record_id: str) -> bool:
        """
        删除记录

        Args:
            record_id: 记录ID

        Returns:
            是否成功
        """
        try:
            sql = f"DELETE FROM {self._table_name} WHERE {self._id_column} = ?"
            self._db.execute(sql, (record_id,), commit=True)

            logger.info(f"{self._table_name}记录删除成功: {record_id}")

            # 清除缓存
            self._clear_cache()

            return True
        except Exception as e:
            logger.error(f"删除{self._table_name}记录失败: {e}")
            return False

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        统计记录数量

        Args:
            filters: 过滤条件

        Returns:
            记录数量
        """
        try:
            sql = f"SELECT COUNT(*) FROM {self._table_name}"
            params: List[Any] = []

            if filters:
                conditions = []
                for key, value in filters.items():
                    if key in self.columns and value is not None:
                        conditions.append(f"{key} = ?")
                        params.append(value)

                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)

            result = self._db.fetchone(sql, tuple(params) if params else None)
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"统计{self._table_name}数量失败: {e}")
            return 0

    def batch_create(self, data_list: List[Dict[str, Any]]) -> List[Optional[str]]:
        """
        批量创建记录

        Args:
            data_list: 数据字典列表

        Returns:
            记录ID列表
        """
        if not data_list:
            return []

        try:
            from ..utils.helpers import generate_id

            id_field = self._id_column
            ids = []

            # 获取第一个数据的列
            first_data = data_list[0]
            columns = [k for k in first_data.keys() if k in self.columns]
            placeholders = ', '.join(['?'] * len(columns))

            sql = f"INSERT INTO {self._table_name} ({', '.join(columns)}) VALUES ({placeholders})"

            # 准备批量数据
            batch_data = []
            for data in data_list:
                record_id = data.get(id_field) or generate_id()
                data[id_field] = record_id
                ids.append(record_id)
                batch_data.append(tuple(data.get(col) for col in columns))

            # 批量执行
            self._db.executemany(sql, batch_data, commit=True)

            logger.info(f"批量创建{self._table_name}记录: {len(ids)}条")

            # 清除缓存
            self._clear_cache()

            return ids
        except Exception as e:
            logger.error(f"批量创建{self._table_name}记录失败: {e}")
            return [None] * len(data_list)

    def batch_update(self, updates: List[Tuple[str, Dict[str, Any]]]) -> int:
        """
        批量更新记录

        Args:
            updates: [(record_id, data), ...] 元组列表

        Returns:
            成功更新的记录数
        """
        if not updates:
            return 0

        try:
            count = 0
            for record_id, data in updates:
                if self.update(record_id, data):
                    count += 1

            return count
        except Exception as e:
            logger.error(f"批量更新{self._table_name}记录失败: {e}")
            return 0

    def batch_delete(self, record_ids: List[str]) -> int:
        """
        批量删除记录

        Args:
            record_ids: 记录ID列表

        Returns:
            成功删除的记录数
        """
        if not record_ids:
            return 0

        try:
            placeholders = ', '.join(['?'] * len(record_ids))
            sql = f"DELETE FROM {self._table_name} WHERE {self._id_column} IN ({placeholders})"

            cursor = self._db.execute(sql, tuple(record_ids), commit=True)
            count = cursor.rowcount if cursor else 0

            logger.info(f"批量删除{self._table_name}记录: {count}条")

            # 清除缓存
            self._clear_cache()

            return count
        except Exception as e:
            logger.error(f"批量删除{self._table_name}记录失败: {e}")
            return 0

    def exists(self, record_id: str) -> bool:
        """
        检查记录是否存在

        Args:
            record_id: 记录ID

        Returns:
            是否存在
        """
        try:
            sql = f"SELECT 1 FROM {self._table_name} WHERE {self._id_column} = ? LIMIT 1"
            result = self._db.fetchone(sql, (record_id,))
            return result is not None
        except Exception as e:
            logger.error(f"检查{self._table_name}记录存在性失败: {e}")
            return False

    def get_indexes(self) -> List[Dict[str, Any]]:
        """
        获取表的索引信息

        Returns:
            索引信息列表
        """
        try:
            sql = f"PRAGMA index_list({self._table_name})"
            rows = self._db.fetchall(sql)

            indexes = []
            for row in rows:
                index_name = row[1]
                unique = bool(row[2])

                # 获取索引列
                col_sql = f"PRAGMA index_info({index_name})"
                col_rows = self._db.fetchall(col_sql)
                columns = [col_row[2] for col_row in col_rows]

                indexes.append({
                    'name': index_name,
                    'unique': unique,
                    'columns': columns,
                })

            return indexes
        except Exception as e:
            logger.warning(f"获取索引信息失败: {e}")
            return []

    def analyze_performance(self) -> Dict[str, Any]:
        """
        分析表性能

        Returns:
            性能分析结果
        """
        try:
            # 获取表大小
            count = self.count()

            # 获取索引信息
            indexes = self.get_indexes()

            # 建议
            suggestions = []

            # 检查是否有主键索引
            if not any(idx['name'].startswith('sqlite_autoindex') for idx in indexes):
                suggestions.append({
                    'type': 'warning',
                    'message': '表没有主键索引，建议添加'
                })

            # 检查是否有过多索引
            if len(indexes) > 10:
                suggestions.append({
                    'type': 'info',
                    'message': f'索引数量较多({len(indexes)}个)，考虑合并'
                })

            return {
                'table': self._table_name,
                'row_count': count,
                'index_count': len(indexes),
                'indexes': indexes,
                'suggestions': suggestions,
            }
        except Exception as e:
            logger.error(f"性能分析失败: {e}")
            return {}


# =============================================================================
# 任务DAO (优化版)
# =============================================================================

class TaskDAO(BaseDAO):
    """任务数据访问对象（优化版）"""

    _table_name = "tasks"
    _columns = [
        "task_id", "task_name", "inquirer", "inquirer_dept", "inquirer_company",
        "inquirer_phone", "inquirer_email", "respondent", "respondent_dept",
        "industry", "key_module", "task_content", "urgency", "status",
        "expected_reply_time", "actual_reply_time", "reply_status", "reply_content",
        "created_at", "updated_at", "created_by", "remark",
    ]
    _id_column = "task_id"

    def __init__(self) -> None:
        super().__init__()
        self._query_cache: OrderedDict = OrderedDict()

    def search(self, keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        搜索任务

        Args:
            keyword: 搜索关键词
            limit: 返回数量限制

        Returns:
            匹配的任务列表
        """
        try:
            pattern = f"%{keyword}%"
            sql = """
                SELECT * FROM tasks
                WHERE task_name LIKE ?
                   OR task_content LIKE ?
                   OR inquirer LIKE ?
                   OR respondent LIKE ?
                   OR key_module LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """
            rows = self._db.fetchall(sql, (pattern,) * 5 + (limit,))
            return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(f"搜索任务失败: {e}")
            return []

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """获取指定状态的任务"""
        return self.get_all(filters={"status": status}, order_by="-created_at")

    def get_pending(self) -> List[Dict[str, Any]]:
        """获取待处理的任务"""
        return self.get_all(filters={"status": "pending"}, order_by="-created_at")

    def get_by_urgency(self, urgency: str) -> List[Dict[str, Any]]:
        """获取指定紧急程度的任务"""
        return self.get_all(filters={"urgency": urgency}, order_by="-created_at")

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取任务统计信息

        Returns:
            统计信息字典
        """
        try:
            stats = {}

            # 按状态统计
            sql = """
                SELECT status, COUNT(*) as count
                FROM tasks
                GROUP BY status
            """
            rows = self._db.fetchall(sql)
            stats['by_status'] = {row[0]: row[1] for row in rows}

            # 按紧急程度统计
            sql = """
                SELECT urgency, COUNT(*) as count
                FROM tasks
                GROUP BY urgency
            """
            rows = self._db.fetchall(sql)
            stats['by_urgency'] = {row[0]: row[1] for row in rows}

            # 总数
            stats['total'] = self.count()

            return stats
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            return {}

    def _row_to_dict(self, row: Tuple, columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """将数据库行转换为字典（使用TaskDAO的列名）"""
        return super()._row_to_dict(row, columns or self._columns)


# =============================================================================
# 任务跟踪DAO (优化版)
# =============================================================================

class TaskTrackDAO(BaseDAO):
    """任务跟踪记录数据访问对象（优化版）"""

    _table_name = "task_track_records"
    _columns = ["record_id", "task_id", "track_content", "track_status", "track_time", "created_at"]
    _id_column = "record_id"

    def __init__(self) -> None:
        super().__init__()

    def get_by_task_id(self, task_id: str) -> List[Dict[str, Any]]:
        """获取任务的跟踪记录"""
        try:
            sql = """
                SELECT * FROM task_track_records
                WHERE task_id = ?
                ORDER BY track_time DESC
            """
            rows = self._db.fetchall(sql, (task_id,))
            return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取跟踪记录失败: {e}")
            return []

    def get_by_status(self, track_status: str) -> List[Dict[str, Any]]:
        """获取指定状态的跟踪记录"""
        try:
            sql = """
                SELECT * FROM task_track_records
                WHERE track_status = ?
                ORDER BY track_time DESC
            """
            rows = self._db.fetchall(sql, (track_status,))
            return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取跟踪记录失败: {e}")
            return []

    def delete_by_task_id(self, task_id: str) -> bool:
        """删除任务的所有跟踪记录"""
        try:
            sql = "DELETE FROM task_track_records WHERE task_id = ?"
            self._db.execute(sql, (task_id,), commit=True)
            return True
        except Exception as e:
            logger.error(f"删除跟踪记录失败: {e}")
            return False


# =============================================================================
# 提醒DAO (优化版)
# =============================================================================

class ReminderDAO(BaseDAO):
    """提醒数据访问对象（优化版）"""

    _table_name = "reminders"
    _columns = ["reminder_id", "task_id", "reminder_time", "reminder_type", "is_triggered", "triggered_at", "created_at"]
    _id_column = "reminder_id"

    def __init__(self) -> None:
        super().__init__()

    def get_pending(self) -> List[Dict[str, Any]]:
        """获取待触发的提醒"""
        try:
            sql = """
                SELECT * FROM reminders
                WHERE is_triggered = 0
                  AND reminder_time <= ?
                ORDER BY reminder_time ASC
            """
            rows = self._db.fetchall(sql, (datetime.now(),))
            return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取待触发提醒失败: {e}")
            return []

    def get_by_task_id(self, task_id: str) -> List[Dict[str, Any]]:
        """获取任务的所有提醒"""
        try:
            sql = """
                SELECT * FROM reminders
                WHERE task_id = ?
                ORDER BY reminder_time DESC
            """
            rows = self._db.fetchall(sql, (task_id,))
            return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取提醒失败: {e}")
            return []

    def get_upcoming(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取即将触发的提醒"""
        try:
            from datetime import timedelta

            future_time = datetime.now() + timedelta(hours=hours)
            sql = """
                SELECT * FROM reminders
                WHERE is_triggered = 0
                  AND reminder_time <= ?
                ORDER BY reminder_time ASC
                LIMIT 50
            """
            rows = self._db.fetchall(sql, (future_time,))
            return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取即将触发提醒失败: {e}")
            return []

    def trigger(self, reminder_id: str) -> bool:
        """触发提醒"""
        try:
            sql = """
                UPDATE reminders
                SET is_triggered = 1, triggered_at = ?
                WHERE reminder_id = ?
            """
            self._db.execute(sql, (datetime.now(), reminder_id), commit=True)
            logger.info(f"提醒已触发: {reminder_id}")
            self._clear_cache()
            return True
        except Exception as e:
            logger.error(f"触发提醒失败: {e}")
            return False

    def delete_by_task_id(self, task_id: str) -> bool:
        """删除任务的所有提醒"""
        try:
            sql = "DELETE FROM reminders WHERE task_id = ?"
            self._db.execute(sql, (task_id,), commit=True)
            return True
        except Exception as e:
            logger.error(f"删除提醒失败: {e}")
            return False


# =============================================================================
# 推荐库DAO (优化版)
# =============================================================================

class RecommendationLibraryDAO(BaseDAO):
    """推荐库数据访问对象（优化版）"""

    _table_name = "recommendation_library"
    _columns = ["lib_id", "keywords", "related_module", "related_content", "usage_count", "created_at", "updated_at"]
    _id_column = "lib_id"

    def __init__(self) -> None:
        super().__init__()

    def search(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索推荐库"""
        try:
            pattern = f"%{keyword}%"
            sql = """
                SELECT * FROM recommendation_library
                WHERE keywords LIKE ?
                   OR related_module LIKE ?
                   OR related_content LIKE ?
                ORDER BY usage_count DESC
                LIMIT ?
            """
            rows = self._db.fetchall(sql, (pattern,) * 3 + (limit,))

            columns = self.columns
            return [self._row_to_dict(row, columns) for row in rows]
        except Exception as e:
            logger.error(f"搜索推荐库失败: {e}")
            return []

    def increment_usage(self, lib_id: str) -> bool:
        """增加使用次数"""
        try:
            sql = """
                UPDATE recommendation_library
                SET usage_count = usage_count + 1, updated_at = ?
                WHERE lib_id = ?
            """
            self._db.execute(sql, (datetime.now(), lib_id), commit=True)
            return True
        except Exception as e:
            logger.error(f"更新使用次数失败: {e}")
            return False

    def get_top_used(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取使用次数最多的推荐"""
        try:
            sql = """
                SELECT * FROM recommendation_library
                ORDER BY usage_count DESC
                LIMIT ?
            """
            rows = self._db.fetchall(sql, (limit,))
            return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取热门推荐失败: {e}")
            return []


# =============================================================================
# 工厂函数
# =============================================================================

def create_task_dao() -> TaskDAO:
    """创建任务DAO实例"""
    return TaskDAO()


def create_task_track_dao() -> TaskTrackDAO:
    """创建任务跟踪DAO实例"""
    return TaskTrackDAO()


def create_reminder_dao() -> ReminderDAO:
    """创建提醒DAO实例"""
    return ReminderDAO()


def create_recommendation_dao() -> RecommendationLibraryDAO:
    """创建推荐库DAO实例"""
    return RecommendationLibraryDAO()


# =============================================================================
# 性能分析工具
# =============================================================================

class DatabaseAnalyzer:
    """数据库性能分析工具"""

    def __init__(self) -> None:
        self._db = get_db_connection()

    def analyze_all_tables(self) -> Dict[str, Any]:
        """
        分析所有表的性能

        Returns:
            分析结果字典
        """
        results = {}

        # 获取所有表
        tables = self._db.get_tables()

        # 分析每个表
        for table in tables:
            try:
                analyzer = BaseDAO()
                analyzer._table_name = table
                results[table] = analyzer.analyze_performance()
            except Exception as e:
                logger.warning(f"分析表 {table} 失败: {e}")
                results[table] = {'error': str(e)}

        return results

    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """
        获取慢查询分析（基于查询计划）

        Returns:
            慢查询列表
        """
        # SQLite不直接支持慢查询日志，这里返回建议
        suggestions = [
            {
                'type': 'info',
                'message': '建议在WHERE条件和JOIN字段上创建索引',
            },
            {
                'type': 'info',
                'message': '定期执行VACUUM整理数据库',
            },
            {
                'type': 'info',
                'message': '避免使用SELECT *，只查询需要的字段',
            },
        ]
        return suggestions

    def optimize_database(self) -> Dict[str, Any]:
        """
        优化数据库

        Returns:
            优化结果
        """
        results = {}

        try:
            # VACUUM
            self._db.vacuum()
            results['vacuum'] = '成功'

            # ANALYZE
            self._db.execute("ANALYZE", commit=True)
            results['analyze'] = '成功'

            logger.info("数据库优化完成")
        except Exception as e:
            results['error'] = str(e)
            logger.error(f"数据库优化失败: {e}")

        return results
