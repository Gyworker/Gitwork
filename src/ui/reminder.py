"""
任务提醒组件
"""

from typing import List, Dict, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton,
    QFrame, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette


class ReminderWidget(QWidget):
    """
    任务提醒组件
    显示需要提醒的任务列表
    """
    
    # 信号：提醒点击
    reminder_clicked = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.reminders = []
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # ===== 标题栏 =====
        title_layout = QHBoxLayout()
        title = QLabel("⏰ 任务提醒")
        title.setFont(QFont("宋体", 11, QFont.Bold))
        title.setStyleSheet("color: #FF5722;")
        title_layout.addWidget(title)
        
        self.count_label = QLabel("(0)")
        self.count_label.setStyleSheet("color: #666;")
        title_layout.addWidget(self.count_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # ===== 提醒列表 =====
        self.reminder_list = QListWidget()
        self.reminder_list.itemClicked.connect(self._on_item_clicked)
        self.reminder_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E0E0E0;
                background-color: white;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #F0F0F0;
            }
            QListWidget::item:selected {
                background-color: #FFF3E0;
            }
        """)
        layout.addWidget(self.reminder_list, 1)
        
        # ===== 统计信息 =====
        stats_layout = QHBoxLayout()
        
        self.today_count = QLabel("今日提醒: 0")
        self.today_count.setStyleSheet("color: #666;")
        stats_layout.addWidget(self.today_count)
        
        stats_layout.addStretch()
        
        self.total_count = QLabel("总计: 0")
        self.total_count.setStyleSheet("color: #666;")
        stats_layout.addWidget(self.total_count)
        
        layout.addLayout(stats_layout)
        
    def load_reminders(self, tasks: List[Dict[str, Any]]):
        """加载提醒列表"""
        self.reminders = tasks
        self._refresh_list()
        
    def _refresh_list(self):
        """刷新列表"""
        self.reminder_list.clear()
        
        for task in self.reminders:
            item = QListWidgetItem()
            widget = self._create_reminder_item(task)
            item.setSizeHint(widget.sizeHint())
            self.reminder_list.addItem(item)
            self.reminder_list.setItemWidget(item, widget)
            
        count = len(self.reminders)
        self.count_label.setText(f"({count})")
        self.total_count.setText(f"总计: {count}")
        
        # 统计今日提醒
        # TODO: 根据任务上次提醒时间统计
        self.today_count.setText("今日提醒: 0")
        
    def _create_reminder_item(self, task: Dict[str, Any]) -> QWidget:
        """创建提醒项"""
        widget = QFrame()
        widget.setFrameShape(QFrame.StyledPanel)
        widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border-left: 3px solid #FF9800;
                padding: 8px;
            }
            QFrame:hover {
                background-color: #FFF8E1;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(3)
        
        # 重要程度标签
        importance = task.get('importance', '中')
        color_map = {'高': '#F44336', '中': '#FF9800', '低': '#4CAF50'}
        color = color_map.get(importance, '#999999')
        
        top_layout = QHBoxLayout()
        imp_label = QLabel(f"[{importance}]")
        imp_label.setStyleSheet(f"""
            color: white;
            background-color: {color};
            padding: 2px 6px;
            border-radius: 3px;
        """)
        top_layout.addWidget(imp_label)
        
        # 责任人
        responder = task.get('responder_name', '-')
        resp_label = QLabel(f"责任人: {responder}")
        resp_label.setStyleSheet("color: #666;")
        top_layout.addWidget(resp_label)
        top_layout.addStretch()
        
        layout.addLayout(top_layout)
        
        # 任务名称
        name = task.get('task_name', '未命名任务')
        name_label = QLabel(name)
        name_label.setFont(QFont("宋体", 10, QFont.Bold))
        name_label.setStyleSheet("color: #333;")
        layout.addWidget(name_label)
        
        # 截止时间
        expected_time = task.get('expected_time', '')
        if expected_time:
            time_label = QLabel(f"截止: {str(expected_time)[:16]}")
            time_label.setStyleSheet("color: #F44336; font-size: 9pt;")
            layout.addWidget(time_label)
            
        # 提醒次数
        reminder_count = task.get('reminder_count', 0)
        max_reminders = self._get_max_reminders(importance)
        reminder_label = QLabel(f"已提醒: {reminder_count}/{max_reminders}")
        reminder_label.setStyleSheet("color: #999; font-size: 9pt;")
        layout.addWidget(reminder_label)
        
        # 存储任务ID
        widget.setProperty("task_id", task.get('task_id', ''))
        
        return widget
        
    def _get_max_reminders(self, importance: str) -> int:
        """获取最大提醒次数"""
        max_map = {'高': 6, '中': 4, '低': 2}
        return max_map.get(importance, 4)
        
    def _on_item_clicked(self, item: QListWidgetItem):
        """点击提醒项"""
        widget = self.reminder_list.itemWidget(item)
        if widget:
            task_id = widget.property("task_id")
            if task_id:
                self.reminder_clicked.emit(task_id)


class ReminderDialog:
    """提醒弹窗（V1.7新增：显示任务具体内容）"""
    
    @staticmethod
    def show(task: Dict[str, Any], parent=None):
        """显示提醒弹窗"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QGroupBox
        from PyQt5.QtGui import QFont
        
        dialog = QDialog(parent)
        dialog.setWindowTitle("⏰ 任务提醒")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 重要程度
        importance = task.get('importance', '中')
        color_map = {'高': '#F44336', '中': '#FF9800', '低': '#4CAF50'}
        color = color_map.get(importance, '#999999')
        
        imp_layout = QHBoxLayout()
        imp_label = QLabel(f"[{importance}]")
        imp_label.setStyleSheet(f"""
            color: white;
            background-color: {color};
            padding: 5px 15px;
            border-radius: 5px;
            font-weight: bold;
        """)
        imp_layout.addWidget(imp_label)
        imp_layout.addStretch()
        layout.addLayout(imp_layout)
        
        # 任务名称
        name_label = QLabel(task.get('task_name', '未命名任务'))
        name_label.setFont(QFont("宋体", 14, QFont.Bold))
        layout.addWidget(name_label)
        
        # 责任人
        responder_label = QLabel(f"责任人: {task.get('responder_name', '-')}")
        layout.addWidget(responder_label)
        
        # 截止时间
        expected_time = task.get('expected_time', '')
        time_label = QLabel(f"截止时间: {str(expected_time)[:16] if expected_time else '-'}")
        time_label.setStyleSheet("color: #F44336;")
        layout.addWidget(time_label)
        
        # 已提醒次数
        reminder_count = task.get('reminder_count', 0)
        max_reminders = {'高': 6, '中': 4, '低': 2}.get(importance, 4)
        reminder_label = QLabel(f"已提醒: {reminder_count}次 (今天) / {max_reminders}次 (上限)")
        reminder_label.setStyleSheet("color: #666;")
        layout.addWidget(reminder_label)
        
        # V1.7新增：任务具体内容
        content_group = QGroupBox("📋 任务具体内容")
        content_layout = QVBoxLayout()
        
        content_text = QTextEdit()
        content_text.setPlainText(task.get('task_content', '无'))
        content_text.setReadOnly(True)
        content_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 2px solid #FFE0B2;
                border-radius: 4px;
                padding: 8px;
                max-height: 80px;
            }
        """)
        content_layout.addWidget(content_text)
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        # 提醒类型
        remind_type_label = QLabel("提醒类型:")
        remind_type_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(remind_type_label)
        
        # V1.7额外提醒时间点说明
        if importance == '高':
            times = ["11:00", "13:50", "17:30"]
        elif importance == '中':
            times = ["13:55", "17:35"]
        else:
            times = ["17:40"]
            
        for t in times:
            time_item = QLabel(f"⭐ {t} {importance}优先级额外提醒")
            time_item.setStyleSheet("color: #FF9800; padding-left: 20px;")
            layout.addWidget(time_item)
            
        info_label = QLabel("请及时处理！")
        info_label.setStyleSheet("color: #F44336; font-weight: bold;")
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        done_btn = QPushButton("✅ 已处理")
        done_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        done_btn.clicked.connect(lambda: dialog.accept())
        btn_layout.addWidget(done_btn)
        
        later_btn = QPushButton("⏰ 稍后提醒")
        later_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #FB8C00;
            }
        """)
        later_btn.clicked.connect(lambda: dialog.reject())
        btn_layout.addWidget(later_btn)
        
        layout.addLayout(btn_layout)
        
        return dialog.exec_()
