# -*- coding: utf-8 -*-
"""
提醒管理模块
Notification Management Module

提供任务提醒功能
"""

from typing import Optional
from datetime import datetime

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QDateTimeEdit,
    QCheckBox,
    QDialog,
    QTextEdit,
)

from ..database.models import Task, Reminder
from ..database.er_diagram import ReminderDAO
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ReminderDialog(QDialog):
    """提醒设置对话框"""

    def __init__(self, task: Task, parent: Optional[QWidget] = None) -> None:
        """初始化提醒对话框"""
        super().__init__(parent)
        self.task = task
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化UI"""
        self.setWindowTitle("设置提醒")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # 任务信息
        task_label = QLabel(f"任务: {self.task.task_name}")
        task_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(task_label)

        # 提醒时间
        form_layout = QFormLayout()

        self.reminder_time = QDateTimeEdit()
        self.reminder_time.setCalendarPopup(True)
        self.reminder_time.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.reminder_time.setDateTime(
            self.reminder_time.dateTime().addSecs(3600)  # 默认1小时后
        )
        form_layout.addRow("提醒时间*:", self.reminder_time)

        # 提醒类型
        self.reminder_type = QLineEdit()
        self.reminder_type.setText("答复提醒")
        form_layout.addRow("提醒类型:", self.reminder_type)

        # 备注
        self.remark = QTextEdit()
        self.remark.setMaximumHeight(80)
        form_layout.addRow("备注:", self.remark)

        layout.addLayout(form_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def get_reminder_data(self) -> dict:
        """获取提醒数据"""
        return {
            "task_id": self.task.task_id,
            "reminder_time": self.reminder_time.dateTime().toPyDateTime(),
            "reminder_type": self.reminder_type.text(),
            "remark": self.remark.toPlainText(),
        }


class ReminderPopup(QDialog):
    """提醒弹窗"""

    def __init__(self, reminder: dict, task: Task, parent: Optional[QWidget] = None) -> None:
        """初始化提醒弹窗"""
        super().__init__(parent)
        self.reminder = reminder
        self.task = task
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化UI"""
        self.setWindowTitle("🔔 任务提醒")
        self.setMinimumWidth(500)

        # 设置为置顶窗口
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)

        # 提醒标题
        title_label = QLabel("🔔 您有新的任务提醒")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #E91E63;")
        layout.addWidget(title_label)

        # 任务信息
        info_group = QGroupBox("任务信息")
        info_layout = QFormLayout()

        info_layout.addRow("任务名称:", QLabel(self.task.task_name))
        info_layout.addRow("咨询者:", QLabel(self.task.inquirer))
        info_layout.addRow("答复人:", QLabel(self.task.respondent))

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # 任务内容
        content_group = QGroupBox("任务具体内容")
        content_layout = QVBoxLayout()
        content_label = QLabel(self.task.task_content or "无")
        content_label.setWordWrap(True)
        content_layout.addWidget(content_label)
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)

        # 提醒信息
        reminder_group = QGroupBox("提醒信息")
        reminder_layout = QFormLayout()

        reminder_time = self.reminder.get("reminder_time")
        if isinstance(reminder_time, datetime):
            reminder_time = reminder_time.strftime("%Y-%m-%d %H:%M")
        reminder_layout.addRow("提醒时间:", QLabel(str(reminder_time)))
        reminder_layout.addRow("提醒类型:", QLabel(self.reminder.get("reminder_type", "")))

        reminder_group.setLayout(reminder_layout)
        layout.addWidget(reminder_group)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        snooze_btn = QPushButton("稍后提醒")
        snooze_btn.clicked.connect(self._on_snooze)
        btn_layout.addWidget(snooze_btn)

        dismiss_btn = QPushButton("知道了")
        dismiss_btn.clicked.connect(self.accept)
        btn_layout.addWidget(dismiss_btn)

        layout.addLayout(btn_layout)

    def _on_snooze(self) -> None:
        """稍后提醒"""
        # 延迟15分钟
        self.reminder["reminder_time"] = datetime.now().replace(
            minute=(datetime.now().minute + 15) % 60
        )
        self.accept()


class NotificationWidget(QWidget):
    """提醒管理组件"""

    reminder_triggered = pyqtSignal(str)  # 发送任务ID

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """初始化提醒组件"""
        super().__init__(parent)
        self.reminder_dao = ReminderDAO()
        self._init_ui()
        self._init_timer()

    def _init_ui(self) -> None:
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("🔔 提醒管理")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)

        # 提醒设置
        set_group = QGroupBox("设置提醒")
        set_layout = QHBoxLayout()

        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("输入任务ID...")
        set_layout.addWidget(self.task_input)

        set_btn = QPushButton("设置提醒")
        set_btn.clicked.connect(self._on_set_reminder)
        set_layout.addWidget(set_btn)

        set_group.setLayout(set_layout)
        layout.addWidget(set_group)

        # 待触发提醒
        pending_group = QGroupBox("待触发提醒")
        pending_layout = QVBoxLayout()

        self.pending_table = QTableWidget()
        self.pending_table.setColumnCount(4)
        self.pending_table.setHorizontalHeaderLabels([
            "任务ID", "提醒时间", "提醒类型", "操作"
        ])
        self.pending_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.pending_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.pending_table.setEditTriggers(QTableWidget.NoEditTriggers)
        pending_layout.addWidget(self.pending_table)

        pending_group.setLayout(pending_layout)
        layout.addWidget(pending_group, 1)

        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._load_pending_reminders)
        layout.addWidget(refresh_btn)

        # 加载待触发提醒
        self._load_pending_reminders()

    def _init_timer(self) -> None:
        """初始化定时器"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._check_reminders)
        self.timer.start(60000)  # 每分钟检查一次

    def _load_pending_reminders(self) -> None:
        """加载待触发提醒"""
        try:
            reminders = self.reminder_dao.get_pending()
            self.pending_table.setRowCount(len(reminders))

            for i, reminder in enumerate(reminders):
                self.pending_table.setItem(i, 0, QTableWidgetItem(reminder["task_id"]))

                reminder_time = reminder.get("reminder_time")
                if isinstance(reminder_time, datetime):
                    reminder_time = reminder_time.strftime("%Y-%m-%d %H:%M")
                self.pending_table.setItem(i, 1, QTableWidgetItem(str(reminder_time)))

                self.pending_table.setItem(i, 2, QTableWidgetItem(reminder.get("reminder_type", "")))

                # 操作按钮
                delete_btn = QPushButton("删除")
                delete_btn.clicked.connect(lambda checked, r=reminder: self._on_delete_reminder(r))
                self.pending_table.setCellWidget(i, 3, delete_btn)

            logger.info(f"加载待触发提醒成功，共{len(reminders)}条")

        except Exception as e:
            logger.error(f"加载待触发提醒失败: {e}")

    def _on_set_reminder(self) -> None:
        """设置提醒"""
        task_id = self.task_input.text().strip()
        if not task_id:
            QMessageBox.warning(self, "警告", "请输入任务ID！")
            return

        task = Task.get_by_id(task_id)
        if not task:
            QMessageBox.warning(self, "错误", "任务不存在！")
            return

        dialog = ReminderDialog(task, self)
        if dialog.exec_():
            data = dialog.get_reminder_data()
            reminder_id = self.reminder_dao.create(data)
            if reminder_id:
                QMessageBox.information(self, "成功", "提醒设置成功！")
                self._load_pending_reminders()
            else:
                QMessageBox.warning(self, "错误", "提醒设置失败！")

    def _on_delete_reminder(self, reminder: dict) -> None:
        """删除提醒"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除此提醒吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.reminder_dao.delete_by_task_id(reminder["task_id"])
            self._load_pending_reminders()

    def _check_reminders(self) -> None:
        """检查并触发提醒"""
        try:
            pending_reminders = self.reminder_dao.get_pending()

            for reminder in pending_reminders:
                task = Task.get_by_id(reminder["task_id"])
                if task:
                    # 显示提醒弹窗
                    popup = ReminderPopup(reminder, task, self)
                    if popup.exec_():
                        # 标记为已触发
                        self.reminder_dao.trigger(reminder["reminder_id"])
                        self.reminder_triggered.emit(task.task_id)

            # 刷新列表
            self._load_pending_reminders()

        except Exception as e:
            logger.error(f"检查提醒失败: {e}")

    def set_task(self, task_id: str) -> None:
        """设置当前任务"""
        self.task_input.setText(task_id)
