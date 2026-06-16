"""
任务跟踪组件
显示和管理所有任务的状态
"""

from typing import List, Dict, Any, Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QToolButton, QMenu, QAction,
    QStyledItemDelegate, QStyleOptionViewItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QBrush


class TaskTrackWidget(QWidget):
    """
    任务跟踪组件
    显示任务列表，支持筛选、搜索、分页等功能
    """
    
    # 信号：任务选中
    task_selected = pyqtSignal(str)
    # 信号：任务双击
    task_double_clicked = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = []
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # ===== 标题栏 =====
        title_layout = QHBoxLayout()
        title = QLabel("📋 任务跟踪")
        title.setFont(QFont("宋体", 11, QFont.Bold))
        title.setStyleSheet("color: #1976D2;")
        title_layout.addWidget(title)
        
        self.count_label = QLabel("(0)")
        self.count_label.setStyleSheet("color: #666;")
        title_layout.addWidget(self.count_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # ===== 任务表格 =====
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "☑", "序号", "任务名称", "状态", "重要", "责任人",
            "关键模块", "创建时间", "操作", "咨询者"
        ])
        
        # 设置表格属性
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setShowGrid(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        
        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # 复选框
        header.setSectionResizeMode(1, QHeaderView.Fixed)   # 序号
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 任务名称
        header.setSectionResizeMode(3, QHeaderView.Fixed)    # 状态
        header.setSectionResizeMode(4, QHeaderView.Fixed)    # 重要
        header.setSectionResizeMode(5, QHeaderView.Fixed)     # 责任人
        header.setSectionResizeMode(6, QHeaderView.Fixed)    # 关键模块
        header.setSectionResizeMode(7, QHeaderView.Fixed)    # 创建时间
        header.setSectionResizeMode(8, QHeaderView.Fixed)    # 操作
        header.setSectionResizeMode(9, QHeaderView.Fixed)    # 咨询者
        
        self.table.setColumnWidth(0, 25)
        self.table.setColumnWidth(1, 40)
        self.table.setColumnWidth(3, 60)
        self.table.setColumnWidth(4, 50)
        self.table.setColumnWidth(5, 60)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(7, 90)
        self.table.setColumnWidth(8, 90)
        self.table.setColumnWidth(9, 60)
        
        # 设置行高
        self.table.verticalHeader().setDefaultSectionSize(35)
        
        # 信号连接
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.cellDoubleClicked.connect(self._on_double_click)
        
        # 设置样式
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E0E0E0;
                background-color: white;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #E3F2FD;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 6px;
                border: 1px solid #E0E0E0;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.table)
        
        # ===== 底部操作栏 =====
        bottom_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self._on_refresh)
        bottom_layout.addWidget(self.refresh_btn)
        
        bottom_layout.addStretch()
        
        self.total_label = QLabel("共 0 条任务")
        self.total_label.setStyleSheet("color: #666;")
        bottom_layout.addWidget(self.total_label)
        
        layout.addLayout(bottom_layout)
        
    def load_tasks(self, tasks: List[Dict[str, Any]]):
        """加载任务列表"""
        self.tasks = tasks
        self.table.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            self._add_task_row(row, task)
            
        self.count_label.setText(f"({len(tasks)})")
        self.total_label.setText(f"共 {len(tasks)} 条任务")
        
    def _add_task_row(self, row: int, task: Dict[str, Any]):
        """添加任务行"""
        # 复选框
        checkbox = QTableWidgetItem()
        checkbox.setCheckState(Qt.Unchecked)
        checkbox.setFlags(checkbox.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, 0, checkbox)
        
        # 序号
        seq_item = QTableWidgetItem(str(row + 1))
        seq_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 1, seq_item)
        
        # 任务名称
        name_item = QTableWidgetItem(task.get('task_name', ''))
        name_item.setToolTip(task.get('task_content', ''))
        self.table.setItem(row, 2, name_item)
        
        # 状态
        status = task.get('status', '进行中')
        status_item = QTableWidgetItem(status)
        status_item.setTextAlignment(Qt.AlignCenter)
        self._apply_status_color(status_item, status)
        self.table.setItem(row, 3, status_item)
        
        # 重要程度
        importance = task.get('importance', '中')
        imp_item = QTableWidgetItem(importance)
        imp_item.setTextAlignment(Qt.AlignCenter)
        self._apply_importance_color(imp_item, importance)
        self.table.setItem(row, 4, imp_item)
        
        # 责任人
        responder = task.get('responder_name', '-')
        self.table.setItem(row, 5, QTableWidgetItem(responder))
        
        # 关键模块
        module = task.get('key_module', '-')
        module_item = QTableWidgetItem(module)
        module_item.setToolTip(module)
        self.table.setItem(row, 6, module_item)
        
        # 创建时间
        create_time = task.get('task_time', '')
        if create_time:
            if isinstance(create_time, str) and len(create_time) > 10:
                create_time = create_time[:16]
        self.table.setItem(row, 7, QTableWidgetItem(str(create_time)))
        
        # 操作按钮
        action_widget = self._create_action_buttons(task)
        self.table.setCellWidget(row, 8, action_widget)
        
        # 咨询者
        consultant = task.get('consultant_name', '-')
        self.table.setItem(row, 9, QTableWidgetItem(consultant))
        
        # 存储任务ID
        self.table.item(row, 0).setData(Qt.UserRole, task.get('task_id'))
        
    def _create_action_buttons(self, task: Dict[str, Any]) -> QWidget:
        """创建操作按钮"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # 详情按钮
        detail_btn = QPushButton("详情")
        detail_btn.setFixedSize(35, 22)
        detail_btn.clicked.connect(lambda: self._on_detail(task.get('task_id')))
        layout.addWidget(detail_btn)
        
        # 提醒按钮
        reminder_count = task.get('reminder_count', 0)
        reminder_btn = QPushButton(f"提醒({reminder_count})")
        reminder_btn.setFixedSize(45, 22)
        reminder_btn.clicked.connect(lambda: self._on_reminder(task.get('task_id')))
        layout.addWidget(reminder_btn)
        
        return widget
        
    def _apply_status_color(self, item: QTableWidgetItem, status: str):
        """应用状态颜色"""
        colors = {
            '进行中': '#2196F3',  # 蓝色
            '挂起': '#FF9800',    # 橙色
            '已答复': '#4CAF50',  # 绿色
            '完成': '#9E9E9E',    # 灰色
        }
        color = colors.get(status, '#333333')
        item.setBackground(QBrush(QColor(color)))
        item.setForeground(QBrush(QColor('white')))
        
    def _apply_importance_color(self, item: QTableWidgetItem, importance: str):
        """应用重要程度颜色"""
        colors = {
            '高': '#F44336',  # 红色
            '中': '#FF9800',  # 橙色
            '低': '#4CAF50',  # 绿色
        }
        color = colors.get(importance, '#333333')
        item.setBackground(QBrush(QColor(color)))
        item.setForeground(QBrush(QColor('white')))
        
    def _on_selection_changed(self):
        """选中行变化"""
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            task_id = self.table.item(row, 0).data(Qt.UserRole)
            if task_id:
                self.task_selected.emit(task_id)
                
    def _on_double_click(self, row: int, col: int):
        """双击单元格"""
        task_id = self.table.item(row, 0).data(Qt.UserRole)
        if task_id:
            self.task_double_clicked.emit(task_id)
            
    def _on_detail(self, task_id: str):
        """查看详情"""
        self.task_double_clicked.emit(task_id)
        
    def _on_reminder(self, task_id: str):
        """提醒"""
        self.task_selected.emit(task_id)
        # TODO: 触发提醒弹窗
        
    def _on_refresh(self):
        """刷新"""
        # TODO: 重新加载任务
        pass
        
    def get_selected_task_id(self) -> Optional[str]:
        """获取选中的任务ID"""
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            return self.table.item(row, 0).data(Qt.UserRole)
        return None
