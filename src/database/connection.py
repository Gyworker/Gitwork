# -*- coding: utf-8 -*-
"""
数据库连接模块
Database Connection Module

负责数据库连接管理和事务处理
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Generator, List, Optional, Tuple

from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseConnection:
    """数据库连接类"""

    _instance: Optional["DatabaseConnection"] = None

    def __new__(cls) -> "DatabaseConnection":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初始化数据库连接"""
        self._connection: Optional[sqlite3.Connection] = None
        self._config = get_config()
        self._initialize_database()

    def _get_database_path(self) -> str:
        """获取数据库路径"""
        db_path = self._config.database_path

        # 如果是相对路径，转换为绝对路径
        if not os.path.isabs(db_path):
            root_dir = Path(__file__).parent.parent.parent
            db_path = root_dir / db_path

        return str(db_path)

    def _initialize_database(self) -> None:
        """初始化数据库"""
        db_path = self._get_database_path()
        db_dir = os.path.dirname(db_path)

        # 确保数据库目录存在
        if db_dir:
            Path(db_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"数据库路径: {db_path}")

    def connect(self) -> sqlite3.Connection:
        """
        连接数据库

        Returns:
            数据库连接对象
        """
        if self._connection is None:
            db_path = self._get_database_path()
            self._connection = sqlite3.connect(
                db_path, check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES
            )
            # 启用外键约束
            self._connection.execute("PRAGMA foreign_keys = ON")
            # 设置超时时间
            self._connection.execute("PRAGMA busy_timeout = 5000")
            logger.info("数据库连接成功")

        return self._connection

    def disconnect(self) -> None:
        """断开数据库连接"""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            logger.info("数据库连接已关闭")

    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        return self.connect()

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """
        事务上下文管理器

        Yields:
            数据库连接对象
        """
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"事务回滚: {e}")
            raise

    def execute(
        self,
        sql: str,
        params: Optional[Tuple] = None,
        commit: bool = False,
    ) -> sqlite3.Cursor:
        """
        执行SQL语句

        Args:
            sql: SQL语句
            params: 参数元组
            commit: 是否提交

        Returns:
            游标对象
        """
        conn = self.connect()
        cursor = conn.cursor()

        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            if commit:
                conn.commit()

            return cursor
        except sqlite3.Error as e:
            logger.error(f"SQL执行错误: {sql}, 错误: {e}")
            raise

    def executemany(
        self,
        sql: str,
        params_list: List[Tuple],
        commit: bool = False,
    ) -> sqlite3.Cursor:
        """
        批量执行SQL语句

        Args:
            sql: SQL语句
            params_list: 参数元组列表
            commit: 是否提交

        Returns:
            游标对象
        """
        conn = self.connect()
        cursor = conn.cursor()

        try:
            cursor.executemany(sql, params_list)

            if commit:
                conn.commit()

            return cursor
        except sqlite3.Error as e:
            logger.error(f"批量SQL执行错误: {sql}, 错误: {e}")
            raise

    def fetchone(
        self,
        sql: str,
        params: Optional[Tuple] = None,
    ) -> Optional[Tuple]:
        """
        查询单条记录

        Args:
            sql: SQL语句
            params: 参数元组

        Returns:
            查询结果元组，如果没有结果返回None
        """
        cursor = self.execute(sql, params)
        result = cursor.fetchone()
        cursor.close()
        return result

    def fetchall(
        self,
        sql: str,
        params: Optional[Tuple] = None,
    ) -> List[Tuple]:
        """
        查询所有记录

        Args:
            sql: SQL语句
            params: 参数元组

        Returns:
            查询结果列表
        """
        cursor = self.execute(sql, params)
        results = cursor.fetchall()
        cursor.close()
        return results

    def fetchmany(
        self,
        sql: str,
        params: Optional[Tuple] = None,
        size: int = 100,
    ) -> List[Tuple]:
        """
        查询多条记录

        Args:
            sql: SQL语句
            params: 参数元组
            size: 返回记录数

        Returns:
            查询结果列表
        """
        cursor = self.execute(sql, params)
        results = cursor.fetchmany(size)
        cursor.close()
        return results

    def insert(self, table: str, data: dict) -> int:
        """
        插入数据

        Args:
            table: 表名
            data: 数据字典

        Returns:
            插入记录的ID
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        cursor = self.execute(sql, tuple(data.values()), commit=True)
        return cursor.lastrowid if cursor else 0

    def update(
        self,
        table: str,
        data: dict,
        where: str,
        where_params: Optional[Tuple] = None,
    ) -> int:
        """
        更新数据

        Args:
            table: 表名
            data: 数据字典
            where: WHERE条件
            where_params: WHERE参数

        Returns:
            影响的记录数
        """
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"

        params = tuple(data.values())
        if where_params:
            params = params + where_params

        cursor = self.execute(sql, params, commit=True)
        return cursor.rowcount if cursor else 0

    def delete(
        self,
        table: str,
        where: str,
        where_params: Optional[Tuple] = None,
    ) -> int:
        """
        删除数据

        Args:
            table: 表名
            where: WHERE条件
            where_params: WHERE参数

        Returns:
            影响的记录数
        """
        sql = f"DELETE FROM {table} WHERE {where}"
        cursor = self.execute(sql, where_params, commit=True)
        return cursor.rowcount if cursor else 0

    def table_exists(self, table_name: str) -> bool:
        """
        检查表是否存在

        Args:
            table_name: 表名

        Returns:
            是否存在
        """
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.fetchone(sql, (table_name,))
        return result is not None

    def get_tables(self) -> List[str]:
        """
        获取所有表名

        Returns:
            表名列表
        """
        sql = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        results = self.fetchall(sql)
        return [row[0] for row in results]

    def backup(self, backup_path: str) -> bool:
        """
        备份数据库

        Args:
            backup_path: 备份文件路径

        Returns:
            是否备份成功
        """
        try:
            db_path = self._get_database_path()
            conn = self.connect()
            backup_conn = sqlite3.connect(backup_path)
            conn.backup(backup_conn)
            backup_conn.close()
            logger.info(f"数据库备份成功: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return False

    def vacuum(self) -> bool:
        """
        整理数据库

        Returns:
            是否成功
        """
        try:
            self.execute("VACUUM", commit=True)
            logger.info("数据库整理完成")
            return True
        except Exception as e:
            logger.error(f"数据库整理失败: {e}")
            return False


# 全局数据库连接实例
_db_connection: Optional[DatabaseConnection] = None


def get_db_connection() -> DatabaseConnection:
    """获取数据库连接实例"""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection


def get_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    return get_db_connection().get_connection()


@contextmanager
def transaction() -> Generator[sqlite3.Connection, None, None]:
    """事务上下文管理器"""
    db = get_db_connection()
    with db.transaction() as conn:
        yield conn
