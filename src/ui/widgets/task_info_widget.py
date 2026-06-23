# -*- coding: utf-8 -*-
"""
任务信息管理模块
Task Information Management Module

负责任务信息的显示和编辑
"""

from typing import Optional, Callable

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
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDateTimeEdit,
    QMessageBox,
)

from database.models import Task, init_database
from database.connection import get_db_connection
from utils.logger import get_logger

logger = get_logger(__name__)


class TaskInfoWidget(QWidget):
    """任务信息管理组件"""

    task_selected = pyqtSignal(str)  # 任务ID
    task_created = pyqtSignal(str)   # 新建任务ID
    task_updated = pyqtSignal(str)    # 更新任务ID

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """初始化任务信息组件"""
        super().__init__(parent)
        self.current_task_id: Optional[str] = None
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 标题区域
        title_layout = QHBoxLayout()
        title_label = QLabel("📋 任务信息管理")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # 新建任务按钮
        self.new_task_btn = QPushButton("新建任务")
        self.new_task_btn.setMaximumWidth(120)
        self.new_task_btn.clicked.connect(self._on_new_task)
        title_layout.addWidget(self.new_task_btn)

        # 刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setMaximumWidth(80)
        self.refresh_btn.clicked.connect(self._load_tasks)
        title_layout.addWidget(self.refresh_btn)

        layout.addLayout(title_layout)

        # 任务列表区域
        list_group = QGroupBox("任务列表")
        list_layout = QVBoxLayout()

        # 搜索栏
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词搜索...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        list_layout.addLayout(search_layout)

        # 任务列表表格
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(7)
        self.task_table.setHorizontalHeaderLabels([
            "任务ID", "任务名称", "咨询者", "答复人", "状态", "重要程度", "创建时间"
        ])
        self.task_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.task_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.task_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.task_table.itemClicked.connect(self._on_task_selected)
        list_layout.addWidget(self.task_table)

        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        # 任务详情区域
        detail_group = QGroupBox("任务详情")
        detail_layout = QFormLayout()

        # 基本信息
        self.task_name_input = QLineEdit()
        self.task_name_input.setMaxLength(200)
        detail_layout.addRow("任务名称*:", self.task_name_input)

        # 咨询者信息
        self.inquirer_input = QLineEdit()
        self.inquirer_input.setMaxLength(50)
        detail_layout.addRow("咨询者姓名:", self.inquirer_input)

        self.inquirer_dept_input = QLineEdit()
        self.inquirer_dept_input.setMaxLength(100)
        detail_layout.addRow("咨询者部门:", self.inquirer_dept_input)

        self.inquirer_company_input = QLineEdit()
        self.inquirer_company_input.setMaxLength(200)
        detail_layout.addRow("咨询者公司:", self.inquirer_company_input)

        # 答复人信息
        self.respondent_input = QLineEdit()
        self.respondent_input.setMaxLength(50)
        detail_layout.addRow("答复人姓名:", self.respondent_input)

        self.respondent_dept_input = QLineEdit()
        self.respondent_dept_input.setMaxLength(100)
        detail_layout.addRow("答复人部门:", self.respondent_dept_input)

        # 行业和模块
        self.industry_input = QLineEdit()
        self.industry_input.setMaxLength(100)
        detail_layout.addRow("所属行业:", self.industry_input)

        self.key_module_input = QLineEdit()
        self.key_module_input.setMaxLength(200)
        detail_layout.addRow("关键模块:", self.key_module_input)

        # 任务内容
        self.task_content_input = QTextEdit()
        self.task_content_input.setMaximumHeight(100)
        detail_layout.addRow("任务内容:", self.task_content_input)

        # 状态设置
        status_layout = QHBoxLayout()
        self.urgency_combo = QComboBox()
        self.urgency_combo.addItems(["低", "中", "高"])
        status_layout.addWidget(self.urgency_combo)
        status_layout.addWidget(QLabel("重要程度"))

        status_layout.addSpacing(20)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["进行中", "挂起", "已答复", "完成"])
        status_layout.addWidget(self.status_combo)
        status_layout.addWidget(QLabel("状态"))

        status_layout.addStretch()
        detail_layout.addRow("", status_layout)

        # 预期答复时间
        self.expected_reply_time = QDateTimeEdit()
        self.expected_reply_time.setCalendarPopup(True)
        self.expected_reply_time.setDisplayFormat("yyyy-MM-dd HH:mm")
        detail_layout.addRow("预期答复时间:", self.expected_reply_time)

        # 备注
        self.remark_input = QTextEdit()
        self.remark_input.setMaximumHeight(60)
        detail_layout.addRow("备注:", self.remark_input)

        detail_group.setLayout(detail_layout)
        layout.addWidget(detail_group)

        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.save_btn = QPushButton("保存")
        self.save_btn.setMaximumWidth(100)
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setEnabled(False)
        btn_layout.addWidget(self.save_btn)

        self.delete_btn = QPushButton("删除")
        self.delete_btn.setMaximumWidth(100)
        self.delete_btn.clicked.connect(self._on_delete)
        self.delete_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_btn)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.setMaximumWidth(100)
        self.clear_btn.clicked.connect(self._on_clear)
        btn_layout.addWidget(self.clear_btn)

        layout.addLayout(btn_layout)

        # 加载任务列表
        self._load_tasks()

    def _load_tasks(self) -> None:
        """加载任务列表"""
        try:
            tasks = Task.get_all()
            self._display_tasks(tasks)
            logger.info(f"加载任务列表成功，共{len(tasks)}条记录")
        except Exception as e:
            logger.error(f"加载任务列表失败: {e}")
            QMessageBox.warning(self, "错误", f"加载任务列表失败: {e}")

    def _display_tasks(self, tasks: list) -> None:
        """显示任务列表"""
        self.task_table.setRowCount(len(tasks))

        for i, task in enumerate(tasks):
            self.task_table.setItem(i, 0, QTableWidgetItem(task.task_id))
            self.task_table.setItem(i, 1, QTableWidgetItem(task.task_name))
            self.task_table.setItem(i, 2, QTableWidgetItem(task.inquirer))
            self.task_table.setItem(i, 3, QTableWidgetItem(task.respondent))
            self.task_table.setItem(i, 4, QTableWidgetItem(task.status))
            self.task_table.setItem(i, 5, QTableWidgetItem(task.urgency))

            created_at = task.created_at.strftime("%Y-%m-%d %H:%M") if task.created_at else ""
            self.task_table.setItem(i, 6, QTableWidgetItem(created_at))

    def _on_task_selected(self, item: QTableWidgetItem) -> None:
        """任务选中事件"""
        row = item.row()
        task_id = self.task_table.item(row, 0).text()
        self._load_task_detail(task_id)
        self.task_selected.emit(task_id)

    def _load_task_detail(self, task_id: str) -> None:
        """加载任务详情"""
        task = Task.get_by_id(task_id)
        if task:
            self.current_task_id = task_id
            self.task_name_input.setText(task.task_name)
            self.inquirer_input.setText(task.inquirer)
            self.inquirer_dept_input.setText(task.inquirer_dept)
            self.inquirer_company_input.setText(task.inquirer_company)
            self.respondent_input.setText(task.respondent)
            self.respondent_dept_input.setText(task.respondent_dept)
            self.industry_input.setText(task.industry)
            self.key_module_input.setText(task.key_module)
            self.task_content_input.setPlainText(task.task_content)
            self.urgency_combo.setCurrentText(task.urgency)
            self.status_combo.setCurrentText(task.status)
            self.remark_input.setPlainText(task.remark)

            if task.expected_reply_time:
                self.expected_reply_time.setDateTime(task.expected_reply_time)

            self.save_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)

    def _on_new_task(self) -> None:
        """新建任务"""
        self.current_task_id = None
        self._clear_form()
        self.task_name_input.setFocus()
        logger.info("新建任务")

    def _on_save(self) -> None:
        """保存任务"""
        task_name = self.task_name_input.text().strip()
        if not task_name:
            QMessageBox.warning(self, "警告", "任务名称不能为空！")
            self.task_name_input.setFocus()
            return

        try:
            if self.current_task_id:
                # 更新现有任务
                task = Task.get_by_id(self.current_task_id)
                if not task:
                    QMessageBox.warning(self, "错误", "任务不存在！")
                    return
            else:
                # 创建新任务
                task = Task()

            # 更新任务属性
            task.task_name = task_name
            task.inquirer = self.inquirer_input.text().strip()
            task.inquirer_dept = self.inquirer_dept_input.text().strip()
            task.inquirer_company = self.inquirer_company_input.text().strip()
            task.respondent = self.respondent_input.text().strip()
            task.respondent_dept = self.respondent_dept_input.text().strip()
            task.industry = self.industry_input.text().strip()
            task.key_module = self.key_module_input.text().strip()
            task.task_content = self.task_content_input.toPlainText().strip()
            task.urgency = self.urgency_combo.currentText()
            task.status = self.status_combo.currentText()
            task.remark = self.remark_input.toPlainText().strip()
            task.expected_reply_time = self.expected_reply_time.dateTime().toPyDateTime()

            if task.save():
                self.current_task_id = task.task_id
                self._load_tasks()
                QMessageBox.information(self, "成功", "任务保存成功！")

                if self.current_task_id:
                    self.task_updated.emit(self.current_task_id)
            else:
                QMessageBox.warning(self, "错误", "任务保存失败！")

        except Exception as e:
            logger.error(f"保存任务失败: {e}")
            QMessageBox.warning(self, "错误", f"保存任务失败: {e}")

    def _on_delete(self) -> None:
        """删除任务"""
        if not self.current_task_id:
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除此任务吗？\n删除后将无法恢复。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                task = Task.get_by_id(self.current_task_id)
                if task and task.delete():
                    self._clear_form()
                    self._load_tasks()
                    QMessageBox.information(self, "成功", "任务删除成功！")
                else:
                    QMessageBox.warning(self, "错误", "任务删除失败！")
            except Exception as e:
                logger.error(f"删除任务失败: {e}")
                QMessageBox.warning(self, "错误", f"删除任务失败: {e}")

    def _on_clear(self) -> None:
        """清空表单"""
        self._clear_form()

    def _clear_form(self) -> None:
        """清空表单"""
        self.current_task_id = None
        self.task_name_input.clear()
        self.inquirer_input.clear()
        self.inquirer_dept_input.clear()
        self.inquirer_company_input.clear()
        self.respondent_input.clear()
        self.respondent_dept_input.clear()
        self.industry_input.clear()
        self.key_module_input.clear()
        self.task_content_input.clear()
        self.urgency_combo.setCurrentIndex(1)  # 默认"中"
        self.status_combo.setCurrentIndex(0)    # 默认"进行中"
        self.remark_input.clear()
        self.expected_reply_time.setDateTime(
            self.expected_reply_time.minimumDateTime()
        )
        self.save_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    def _on_search(self, text: str) -> None:
        """搜索任务"""
        if not text.strip():
            self._load_tasks()
            return

        try:
            tasks = Task.search(text.strip())
            self._display_tasks(tasks)
        except Exception as e:
            logger.error(f"搜索任务失败: {e}")
