# -*- coding: utf-8 -*-
"""
任务跟踪管理模块
Task Tracking Management Module

负责任务跟踪记录的管理
"""

from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QPushButton,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QDateTimeEdit,
)

from ..database.models import Task, TaskTrackRecord
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TaskTrackWidget(QWidget):
    """任务跟踪管理组件"""

    track_record_added = pyqtSignal(str)  # 发送记录ID

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """初始化任务跟踪组件"""
        super().__init__(parent)
        self.current_task_id: Optional[str] = None
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化UI"""
        layout = QHBoxLayout(self)

        # 左侧：任务选择列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # 标题
        title_label = QLabel("📊 任务跟踪管理")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        left_layout.addWidget(title_label)

        # 任务列表
        list_group = QGroupBox("选择任务")
        list_layout = QVBoxLayout()

        self.task_list = QListWidget()
        self.task_list.itemClicked.connect(self._on_task_selected)
        list_layout.addWidget(self.task_list)

        list_group.setLayout(list_layout)
        left_layout.addWidget(list_group)

        # 刷新按钮
        refresh_btn = QPushButton("刷新任务列表")
        refresh_btn.clicked.connect(self._load_tasks)
        left_layout.addWidget(refresh_btn)

        layout.addWidget(left_widget, 1)

        # 右侧：跟踪记录
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 跟踪记录表单
        form_group = QGroupBox("添加跟踪记录")
        form_layout = QFormLayout()

        # 跟踪状态
        self.track_status_combo = QComboBox()
        self.track_status_combo.addItems([
            "进行中", "已联系", "等待回复", "已答复", "已完成"
        ])
        form_layout.addRow("跟踪状态*:", self.track_status_combo)

        # 跟踪时间
        self.track_time = QDateTimeEdit()
        self.track_time.setCalendarPopup(True)
        self.track_time.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.track_time.setDateTime(self.track_time.minimumDateTime())
        form_layout.addRow("跟踪时间:", self.track_time)

        # 跟踪内容
        self.track_content_input = QTextEdit()
        self.track_content_input.setMaximumHeight(80)
        self.track_content_input.setPlaceholderText("输入跟踪记录内容...")
        form_layout.addRow("跟踪内容*:", self.track_content_input)

        form_group.setLayout(form_layout)
        right_layout.addWidget(form_group)

        # 添加按钮
        add_btn = QPushButton("添加跟踪记录")
        add_btn.clicked.connect(self._on_add_record)
        right_layout.addWidget(add_btn)

        # 跟踪记录列表
        record_group = QGroupBox("跟踪记录历史")
        record_layout = QVBoxLayout()

        self.record_table = QTableWidget()
        self.record_table.setColumnCount(4)
        self.record_table.setHorizontalHeaderLabels([
            "跟踪时间", "跟踪状态", "跟踪内容", "创建时间"
        ])
        self.record_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.record_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.record_table.setEditTriggers(QTableWidget.NoEditTriggers)
        record_layout.addWidget(self.record_table)

        record_group.setLayout(record_layout)
        right_layout.addWidget(record_group, 1)

        layout.addWidget(right_widget, 2)

        # 加载任务列表
        self._load_tasks()

    def _load_tasks(self) -> None:
        """加载任务列表"""
        try:
            tasks = Task.get_all()
            self.task_list.clear()

            for task in tasks:
                item_text = f"{task.task_name} - {task.inquirer} ({task.status})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, task.task_id)
                self.task_list.addItem(item)

            logger.info(f"加载任务列表成功，共{len(tasks)}条记录")
        except Exception as e:
            logger.error(f"加载任务列表失败: {e}")
            QMessageBox.warning(self, "错误", f"加载任务列表失败: {e}")

    def _on_task_selected(self, item: QListWidgetItem) -> None:
        """任务选中事件"""
        self.current_task_id = item.data(Qt.UserRole)
        self._load_records()

    def _load_records(self) -> None:
        """加载跟踪记录"""
        if not self.current_task_id:
            self.record_table.setRowCount(0)
            return

        try:
            records = TaskTrackRecord.get_by_task_id(self.current_task_id)
            self.record_table.setRowCount(len(records))

            for i, record in enumerate(records):
                track_time = record.track_time.strftime("%Y-%m-%d %H:%M") if record.track_time else ""
                created_at = record.created_at.strftime("%Y-%m-%d %H:%M") if record.created_at else ""

                self.record_table.setItem(i, 0, QTableWidgetItem(track_time))
                self.record_table.setItem(i, 1, QTableWidgetItem(record.track_status))
                self.record_table.setItem(i, 2, QTableWidgetItem(record.track_content))
                self.record_table.setItem(i, 3, QTableWidgetItem(created_at))

            logger.info(f"加载跟踪记录成功，共{len(records)}条记录")
        except Exception as e:
            logger.error(f"加载跟踪记录失败: {e}")
            QMessageBox.warning(self, "错误", f"加载跟踪记录失败: {e}")

    def _on_add_record(self) -> None:
        """添加跟踪记录"""
        if not self.current_task_id:
            QMessageBox.warning(self, "警告", "请先选择一个任务！")
            return

        track_content = self.track_content_input.toPlainText().strip()
        if not track_content:
            QMessageBox.warning(self, "警告", "跟踪内容不能为空！")
            self.track_content_input.setFocus()
            return

        try:
            record = TaskTrackRecord(
                task_id=self.current_task_id,
                track_content=track_content,
                track_status=self.track_status_combo.currentText(),
                track_time=self.track_time.dateTime().toPyDateTime(),
            )

            if record.save():
                self._load_records()
                self.track_content_input.clear()
                QMessageBox.information(self, "成功", "跟踪记录添加成功！")
                self.track_record_added.emit(record.record_id)
            else:
                QMessageBox.warning(self, "错误", "跟踪记录添加失败！")

        except Exception as e:
            logger.error(f"添加跟踪记录失败: {e}")
            QMessageBox.warning(self, "错误", f"添加跟踪记录失败: {e}")

    def set_task(self, task_id: str) -> None:
        """设置当前任务"""
        self.current_task_id = task_id

        # 在任务列表中选中对应任务
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item.data(Qt.UserRole) == task_id:
                self.task_list.setCurrentItem(item)
                break

    def refresh(self) -> None:
        """刷新数据"""
        self._load_tasks()
        if self.current_task_id:
            self._load_records()
