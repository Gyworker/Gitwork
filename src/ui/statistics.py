"""
统计分析界面
"""

from typing import Dict, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDialog, QTextEdit, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class StatisticsWidget(QWidget):
    """
    统计面板组件
    显示任务统计概览
    """
    
    def __init__(self, parent=None, statistics_service=None):
        super().__init__(parent)
        self.statistics_service = statistics_service
        self._init_ui()
        self._refresh()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # ===== 标题栏 =====
        title_layout = QHBoxLayout()
        title = QLabel("📊 统计分析")
        title.setFont(QFont("宋体", 12, QFont.Bold))
        title_layout.addWidget(title)
        
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self._refresh)
        title_layout.addWidget(self.refresh_btn)
        
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # ===== 可滚动区域 =====
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        # 统计卡片区
        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(10)
        content_layout.addLayout(self.cards_layout)
        
        # 状态分布
        status_group = QGroupBox("📈 任务状态分布")
        status_layout = QVBoxLayout(status_group)
        self.status_table = QTableWidget()
        self.status_table.setColumnCount(3)
        self.status_table.setHorizontalHeaderLabels(["状态", "数量", "占比"])
        self.status_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.status_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.status_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.status_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.status_table.setMaximumHeight(120)
        status_layout.addWidget(self.status_table)
        content_layout.addWidget(status_group)
        
        # 重要程度分布
        importance_group = QGroupBox("⭐ 重要程度分布")
        importance_layout = QVBoxLayout(importance_group)
        self.importance_table = QTableWidget()
        self.importance_table.setColumnCount(3)
        self.importance_table.setHorizontalHeaderLabels(["优先级", "数量", "占比"])
        self.importance_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.importance_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.importance_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.importance_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.importance_table.setMaximumHeight(100)
        importance_layout.addWidget(self.importance_table)
        content_layout.addWidget(importance_group)
        
        # 责任人统计
        responder_group = QGroupBox("👤 责任人统计 (Top 10)")
        responder_layout = QVBoxLayout(responder_group)
        self.responder_table = QTableWidget()
        self.responder_table.setColumnCount(3)
        self.responder_table.setHorizontalHeaderLabels(["责任人", "总任务", "进行中"])
        self.responder_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.responder_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.responder_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.responder_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.responder_table.setMaximumHeight(200)
        responder_layout.addWidget(self.responder_table)
        content_layout.addWidget(responder_group)
        
        # 关键模块统计
        module_group = QGroupBox("🔑 关键模块统计 (Top 10)")
        module_layout = QVBoxLayout(module_group)
        self.module_table = QTableWidget()
        self.module_table.setColumnCount(2)
        self.module_table.setHorizontalHeaderLabels(["模块", "任务数"])
        self.module_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.module_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.module_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.module_table.setMaximumHeight(200)
        module_layout.addWidget(self.module_table)
        content_layout.addWidget(module_group)
        
        # 生成报告按钮
        report_btn = QPushButton("📝 生成统计报告")
        report_btn.clicked.connect(self._show_report)
        content_layout.addWidget(report_btn)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
    def _refresh(self):
        """刷新统计数据"""
        if not self.statistics_service:
            return
            
        # 获取统计数据
        summary = self.statistics_service.get_task_summary()
        status_dist = self.statistics_service.get_status_distribution()
        importance_dist = self.statistics_service.get_importance_distribution()
        responder_stats = self.statistics_service.get_responder_stats()
        module_stats = self.statistics_service.get_module_stats()
        
        # 更新统计卡片
        self._update_cards(summary)
        
        # 更新表格
        self._update_table(self.status_table, status_dist, ['status', 'count', 'percentage'])
        self._update_table(self.importance_table, importance_dist, ['importance', 'count', 'percentage'])
        self._update_responder_table(responder_stats)
        self._update_module_table(module_stats)
        
    def _update_cards(self, summary: Dict[str, Any]):
        """更新统计卡片"""
        # 清空现有卡片
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # 创建新卡片
        cards_data = [
            ("总任务", str(summary.get('total', 0)), "#1976D2"),
            ("进行中", str(summary.get('by_status', {}).get('进行中', 0)), "#2196F3"),
            ("已完成", str(summary.get('by_status', {}).get('完成', 0)), "#4CAF50"),
            ("今日新增", str(summary.get('today_created', 0)), "#FF9800"),
        ]
        
        for i, (title, value, color) in enumerate(cards_data):
            card = self._create_card(title, value, color)
            self.cards_layout.addWidget(card, 0, i)
            
    def _create_card(self, title: str, value: str, color: str) -> QWidget:
        """创建统计卡片"""
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-left: 4px solid {color};
                border-radius: 4px;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 5, 10, 5)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 11pt;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 24, QFont.Bold))
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)
        
        return card
        
    def _update_table(self, table: QTableWidget, data: list, keys: list):
        """更新表格"""
        table.setRowCount(len(data))
        
        for row, item in enumerate(data):
            for col, key in enumerate(keys):
                value = item.get(key, '')
                cell = QTableWidgetItem(str(value))
                cell.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, col, cell)
                
    def _update_responder_table(self, data: list):
        """更新责任人表格"""
        self.responder_table.setRowCount(len(data))
        
        for row, item in enumerate(data):
            self.responder_table.setItem(row, 0, QTableWidgetItem(item.get('responder', '')))
            self.responder_table.setItem(row, 1, QTableWidgetItem(str(item.get('total_tasks', 0))))
            self.responder_table.setItem(row, 2, QTableWidgetItem(str(item.get('in_progress', 0))))
            
        # 设置对齐
        for row in range(len(data)):
            for col in range(3):
                if self.responder_table.item(row, col):
                    self.responder_table.item(row, col).setTextAlignment(Qt.AlignCenter)
                    
    def _update_module_table(self, data: list):
        """更新模块表格"""
        self.module_table.setRowCount(len(data))
        
        for row, item in enumerate(data):
            self.module_table.setItem(row, 0, QTableWidgetItem(item.get('module', '')))
            self.module_table.setItem(row, 1, QTableWidgetItem(str(item.get('count', 0))))
            
        # 设置对齐
        for row in range(len(data)):
            for col in range(2):
                if self.module_table.item(row, col):
                    self.module_table.item(row, col).setTextAlignment(Qt.AlignCenter)
                    
    def _show_report(self):
        """显示统计报告"""
        if not self.statistics_service:
            return
            
        report = self.statistics_service.generate_summary_report()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("统计报告")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(report)
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Consolas", 10))
        layout.addWidget(text_edit)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()
