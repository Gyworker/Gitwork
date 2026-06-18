# -*- coding: utf-8 -*-
"""
映射学习定时任务调度模块
支持按配置的时间自动执行映射学习任务

版本: V1.0
功能:
- 定时任务调度（每天1:00-6:00执行）
- 支持自定义执行时间
- 任务执行历史记录
- 错误处理和重试机制
"""

import os
import time
import threading
import schedule
from datetime import datetime, time as dt_time
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from src.core.logger import get_logger

logger = get_logger(__name__)


class ScheduleType(Enum):
    """调度类型"""
    DAILY = "daily"           # 每天
    WEEKLY = "weekly"         # 每周
    MONTHLY = "monthly"       # 每月
    ONCE = "once"             # 只执行一次


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"        # 待执行
    RUNNING = "running"        # 执行中
    SUCCESS = "success"        # 成功
    FAILED = "failed"         # 失败
    CANCELLED = "cancelled"   # 已取消


@dataclass
class ScheduledTask:
    """定时任务"""
    id: str = ""
    name: str = ""
    schedule_type: ScheduleType = ScheduleType.DAILY
    execution_time: str = "01:00"  # HH:MM格式
    execution_day: int = 0  # 每周几 (0=周一, 6=周日) 或 每月第几天
    job_func: Optional[Callable] = None
    enabled: bool = True
    max_retries: int = 3
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'schedule_type': self.schedule_type.value,
            'execution_time': self.execution_time,
            'execution_day': self.execution_day,
            'enabled': self.enabled,
            'max_retries': self.max_retries,
            'retry_count': self.retry_count
        }


@dataclass
class TaskExecution:
    """任务执行记录"""
    task_id: str = ""
    task_name: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    result: str = ""
    error: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'retry_count': self.retry_count
        }
    
    @property
    def duration(self) -> float:
        """执行耗时（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


class MappingScheduler:
    """
    映射学习定时任务调度器
    
    功能:
    1. 定时执行映射学习任务
    2. 支持每天/每周/每月执行
    3. 自动重试失败任务
    4. 任务执行历史记录
    5. 线程安全
    
    使用示例:
        scheduler = MappingScheduler()
        scheduler.start()
        
        # 添加每天凌晨1点执行的任务
        scheduler.add_daily_task(
            name="映射学习",
            execution_time="01:00",
            job_func=lambda: learner.learn_from_history()
        )
    """
    
    # 默认执行时间范围
    DEFAULT_START_HOUR = 1   # 凌晨1点
    DEFAULT_END_HOUR = 6     # 凌晨6点
    
    def __init__(self, db=None):
        """
        初始化调度器
        
        Args:
            db: 数据库连接（用于保存执行记录）
        """
        self.db = db
        self.tasks: Dict[str, ScheduledTask] = {}
        self.execution_history: List[TaskExecution] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        logger.info("MappingScheduler初始化完成")
    
    def start(self) -> bool:
        """
        启动调度器
        
        Returns:
            bool: 是否启动成功
        """
        with self._lock:
            if self._running:
                logger.warning("调度器已在运行中")
                return False
            
            self._running = True
            self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self._thread.start()
            
            logger.info("调度器已启动")
            return True
    
    def stop(self) -> bool:
        """
        停止调度器
        
        Returns:
            bool: 是否停止成功
        """
        with self._lock:
            if not self._running:
                logger.warning("调度器未运行")
                return False
            
            self._running = False
            
            if self._thread:
                self._thread.join(timeout=5)
            
            logger.info("调度器已停止")
            return True
    
    def is_running(self) -> bool:
        """检查调度器是否运行中"""
        return self._running
    
    def add_daily_task(
        self,
        name: str,
        execution_time: str = "01:00",
        job_func: Optional[Callable] = None,
        enabled: bool = True,
        max_retries: int = 3
    ) -> str:
        """
        添加每日执行的任务
        
        Args:
            name: 任务名称
            execution_time: 执行时间 (HH:MM)
            job_func: 执行函数
            enabled: 是否启用
            max_retries: 最大重试次数
            
        Returns:
            str: 任务ID
        """
        task_id = f"daily_{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        task = ScheduledTask(
            id=task_id,
            name=name,
            schedule_type=ScheduleType.DAILY,
            execution_time=execution_time,
            job_func=job_func,
            enabled=enabled,
            max_retries=max_retries
        )
        
        self.tasks[task_id] = task
        schedule.every().day.at(execution_time).do(self._execute_task, task_id)
        
        logger.info(f"添加每日任务: {name}, 执行时间: {execution_time}")
        
        return task_id
    
    def add_weekly_task(
        self,
        name: str,
        execution_time: str,
        execution_day: int = 0,
        job_func: Optional[Callable] = None,
        enabled: bool = True,
        max_retries: int = 3
    ) -> str:
        """
        添加每周执行的任务
        
        Args:
            name: 任务名称
            execution_time: 执行时间 (HH:MM)
            execution_day: 每周第几天 (0=周一, 6=周日)
            job_func: 执行函数
            enabled: 是否启用
            max_retries: 最大重试次数
            
        Returns:
            str: 任务ID
        """
        task_id = f"weekly_{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        task = ScheduledTask(
            id=task_id,
            name=name,
            schedule_type=ScheduleType.WEEKLY,
            execution_time=execution_time,
            execution_day=execution_day,
            job_func=job_func,
            enabled=enabled,
            max_retries=max_retries
        )
        
        self.tasks[task_id] = task
        
        # 根据星期几调度
        if execution_day == 0:
            schedule.every().monday.at(execution_time).do(self._execute_task, task_id)
        elif execution_day == 1:
            schedule.every().tuesday.at(execution_time).do(self._execute_task, task_id)
        elif execution_day == 2:
            schedule.every().wednesday.at(execution_time).do(self._execute_task, task_id)
        elif execution_day == 3:
            schedule.every().thursday.at(execution_time).do(self._execute_task, task_id)
        elif execution_day == 4:
            schedule.every().friday.at(execution_time).do(self._execute_task, task_id)
        elif execution_day == 5:
            schedule.every().saturday.at(execution_time).do(self._execute_task, task_id)
        elif execution_day == 6:
            schedule.every().sunday.at(execution_time).do(self._execute_task, task_id)
        
        logger.info(f"添加每周任务: {name}, 执行时间: {execution_time}, 星期{execution_day}")
        
        return task_id
    
    def add_monthly_task(
        self,
        name: str,
        execution_time: str,
        execution_day: int = 1,
        job_func: Optional[Callable] = None,
        enabled: bool = True,
        max_retries: int = 3
    ) -> str:
        """
        添加每月执行的任务
        
        Args:
            name: 任务名称
            execution_time: 执行时间 (HH:MM)
            execution_day: 每月第几天
            job_func: 执行函数
            enabled: 是否启用
            max_retries: 最大重试次数
            
        Returns:
            str: 任务ID
        """
        task_id = f"monthly_{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        task = ScheduledTask(
            id=task_id,
            name=name,
            schedule_type=ScheduleType.MONTHLY,
            execution_time=execution_time,
            execution_day=execution_day,
            job_func=job_func,
            enabled=enabled,
            max_retries=max_retries
        )
        
        self.tasks[task_id] = task
        # 注意：schedule库不直接支持每月执行，使用自定义实现
        schedule.every().day.at(execution_time).do(self._execute_task, task_id)
        
        logger.info(f"添加每月任务: {name}, 执行时间: {execution_time}, 日期{execution_day}")
        
        return task_id
    
    def remove_task(self, task_id: str) -> bool:
        """
        移除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否移除成功
        """
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.info(f"移除任务: {task_id}")
            return True
        return False
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            logger.info(f"启用任务: {task_id}")
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            logger.info(f"禁用任务: {task_id}")
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[ScheduledTask]:
        """获取所有任务"""
        return list(self.tasks.values())
    
    def get_execution_history(
        self,
        task_id: Optional[str] = None,
        limit: int = 100
    ) -> List[TaskExecution]:
        """获取执行历史"""
        history = self.execution_history
        
        if task_id:
            history = [h for h in history if h.task_id == task_id]
        
        return history[-limit:]
    
    def execute_now(self, task_id: str) -> bool:
        """
        立即执行任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否执行成功
        """
        if task_id not in self.tasks:
            logger.error(f"任务不存在: {task_id}")
            return False
        
        task = self.tasks[task_id]
        execution = self._do_execute(task)
        
        return execution.status == TaskStatus.SUCCESS
    
    def _run_scheduler(self):
        """调度器主循环"""
        logger.info("调度器线程启动")
        
        while self._running:
            try:
                schedule.run_pending()
                time.sleep(1)  # 每秒检查一次
            except Exception as e:
                logger.error(f"调度器异常: {e}")
                time.sleep(5)  # 出错后等待5秒
        
        logger.info("调度器线程退出")
    
    def _execute_task(self, task_id: str):
        """执行任务（由schedule调用）"""
        task = self.tasks.get(task_id)
        if not task:
            return
        
        # 检查是否启用
        if not task.enabled:
            logger.debug(f"任务已禁用，跳过执行: {task.name}")
            return
        
        # 检查是否在允许的时间范围内
        if not self._is_in_execution_window():
            logger.debug(f"不在执行时间窗口内，跳过: {task.name}")
            return
        
        # 检查是否需要按月/周执行
        if task.schedule_type == ScheduleType.MONTHLY:
            if datetime.now().day != task.execution_day:
                return
        elif task.schedule_type == ScheduleType.WEEKLY:
            if datetime.now().weekday() != task.execution_day:
                return
        
        # 执行任务
        execution = self._do_execute(task)
        
        # 如果失败且可重试
        if execution.status == TaskStatus.FAILED and task.retry_count < task.max_retries:
            self._retry_task(task)
    
    def _is_in_execution_window(self) -> bool:
        """检查是否在执行时间窗口内"""
        now = datetime.now()
        hour = now.hour
        return self.DEFAULT_START_HOUR <= hour < self.DEFAULT_END_HOUR
    
    def _do_execute(self, task: ScheduledTask) -> TaskExecution:
        """执行任务"""
        execution = TaskExecution(
            task_id=task.id,
            task_name=task.name,
            start_time=datetime.now()
        )
        
        logger.info(f"开始执行任务: {task.name}")
        
        try:
            if task.job_func:
                result = task.job_func()
                execution.result = str(result) if result else "执行成功"
            else:
                execution.result = "无执行函数"
            
            execution.status = TaskStatus.SUCCESS
            task.retry_count = 0  # 重置重试计数
            logger.info(f"任务执行成功: {task.name}")
            
        except Exception as e:
            execution.status = TaskStatus.FAILED
            execution.error = str(e)
            task.retry_count += 1
            logger.error(f"任务执行失败: {task.name}, 错误: {e}")
        
        execution.end_time = datetime.now()
        self.execution_history.append(execution)
        
        # 保存到数据库
        self._save_execution(execution)
        
        return execution
    
    def _retry_task(self, task: ScheduledTask):
        """重试任务"""
        import random
        
        # 随机等待1-5分钟
        wait_time = random.randint(60, 300)
        logger.info(f"任务将在 {wait_time} 秒后重试: {task.name}")
        
        def delayed_retry():
            time.sleep(wait_time)
            if task.enabled and self._is_in_execution_window():
                self._do_execute(task)
        
        thread = threading.Thread(target=delayed_retry, daemon=True)
        thread.start()
    
    def _save_execution(self, execution: TaskExecution):
        """保存执行记录到数据库"""
        if not self.db:
            return
        
        try:
            self.db.execute(
                """
                INSERT INTO scheduler_history 
                (task_id, task_name, start_time, end_time, status, result, error, retry_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    execution.task_id,
                    execution.task_name,
                    execution.start_time.isoformat() if execution.start_time else None,
                    execution.end_time.isoformat() if execution.end_time else None,
                    execution.status.value,
                    execution.result,
                    execution.error,
                    execution.retry_count
                )
            )
        except Exception as e:
            logger.error(f"保存执行记录失败: {e}")


# =============================================================================
# 映射学习任务集成
# =============================================================================

class MappingLearningScheduler(MappingScheduler):
    """
    映射学习专用调度器
    
    预配置:
    - 每天凌晨1:00-6:00执行
    - 自动学习历史任务映射关系
    """
    
    def __init__(self, db=None, mapping_learner=None):
        """
        初始化映射学习调度器
        
        Args:
            db: 数据库连接
            mapping_learner: 映射学习器实例
        """
        super().__init__(db)
        self.mapping_learner = mapping_learner
    
    def setup_default_tasks(self):
        """设置默认的映射学习任务"""
        if self.mapping_learner:
            # 每天凌晨1:00执行历史学习
            self.add_daily_task(
                name="历史任务映射学习",
                execution_time="01:00",
                job_func=lambda: self.mapping_learner.learn_from_history(),
                enabled=True
            )
            
            # 每周一凌晨2:00执行文本导入学习
            self.add_weekly_task(
                name="文本映射学习",
                execution_time="02:00",
                execution_day=0,  # 周一
                job_func=lambda: self.mapping_learner.learn_from_text(""),
                enabled=False  # 默认禁用，需手动启用
            )
            
            # 每月1日凌晨3:00执行Excel导入学习
            self.add_monthly_task(
                name="Excel映射学习",
                execution_time="03:00",
                execution_day=1,  # 每月1日
                job_func=lambda: self.mapping_learner.learn_from_excel(""),
                enabled=False  # 默认禁用，需手动启用
            )
            
            logger.info("默认映射学习任务配置完成")


# =============================================================================
# 单例实例
# =============================================================================

_scheduler: Optional[MappingLearningScheduler] = None


def get_mapping_scheduler(db=None, mapping_learner=None) -> MappingLearningScheduler:
    """获取映射学习调度器单例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = MappingLearningScheduler(db, mapping_learner)
    return _scheduler


def start_scheduler(db=None, mapping_learner=None) -> bool:
    """启动映射学习调度器"""
    scheduler = get_mapping_scheduler(db, mapping_learner)
    scheduler.setup_default_tasks()
    return scheduler.start()


def stop_scheduler() -> bool:
    """停止映射学习调度器"""
    global _scheduler
    if _scheduler:
        return _scheduler.stop()
    return False


def add_mapping_learn_task(
    name: str,
    execution_time: str = "01:00",
    schedule_type: ScheduleType = ScheduleType.DAILY
) -> str:
    """添加映射学习任务"""
    scheduler = get_mapping_scheduler()
    return scheduler.add_daily_task(name, execution_time)
