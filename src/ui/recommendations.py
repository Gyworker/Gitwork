"""
推荐库管理界面
"""

from typing import List, Dict, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLineEdit, QDialog, QFormLayout, QDialogButtonBox,
    QHeaderView, QMessageBox, QFileDialog, QTextEdit,
    QGroupBox, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class RecommendationWidget(QDialog):
    """
    推荐库管理弹窗
    支持查看、添加、编辑、删除、导入导出推荐库
    """
    
    def __init__(self, parent=None, db_connection=None):
        super().__init__(parent)
        self.db = db_connection
        self.setWindowTitle("推荐库管理")
        self.setMinimumSize(900, 550)
        self._init_ui()
        self._load_recommendations()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # ===== 标题栏 =====
        title_layout = QHBoxLayout()
        title = QLabel("🔮 推荐库管理")
        title.setFont(QFont("宋体", 12, QFont.Bold))
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # 搜索框
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索姓名、关键模块...")
        self.search_edit.setMaximumWidth(250)
        self.search_edit.textChanged.connect(self._on_search)
        title_layout.addWidget(self.search_edit)
        
        layout.addLayout(title_layout)
        
        # ===== 分割布局 =====
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：推荐列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["姓名", "关键模块", "部门", "职位", "手机", "邮箱"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E0E0E0;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 6px;
                border: 1px solid #E0E0E0;
                font-weight: bold;
            }
        """)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self.table)
        
        splitter.addWidget(left_widget)
        
        # 右侧：详情面板
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        detail_group = QGroupBox("详细信息")
        detail_layout = QFormLayout()
        
        self.detail_name = QLabel("-")
        self.detail_module = QLabel("-")
        self.detail_dept = QLabel("-")
        self.detail_position = QLabel("-")
        self.detail_phone = QLabel("-")
        self.detail_email = QLabel("-")
        self.detail_expertise = QLabel("-")
        
        detail_layout.addRow("姓名：", self.detail_name)
        detail_layout.addRow("关键模块：", self.detail_module)
        detail_layout.addRow("部门：", self.detail_dept)
        detail_layout.addRow("职位：", self.detail_position)
        detail_layout.addRow("手机：", self.detail_phone)
        detail_layout.addRow("邮箱：", self.detail_email)
        detail_layout.addRow("专业领域：", self.detail_expertise)
        
        detail_group.setLayout(detail_layout)
        right_layout.addWidget(detail_group)
        
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        # ===== 操作按钮 =====
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ 添加")
        self.add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("✏️ 编辑")
        self.edit_btn.clicked.connect(self._on_edit)
        self.edit_btn.setEnabled(False)
        btn_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("🗑️ 删除")
        self.delete_btn.clicked.connect(self._on_delete)
        self.delete_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_btn)
        
        btn_layout.addStretch()
        
        self.import_btn = QPushButton("📥 导入")
        self.import_btn.clicked.connect(self._on_import)
        btn_layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("📤 导出")
        self.export_btn.clicked.connect(self._on_export)
        btn_layout.addWidget(self.export_btn)
        
        layout.addLayout(btn_layout)
        
        # ===== 导入说明 =====
        help_label = QLabel("💡 导入格式：姓名，关键模块[, 工号, 手机号, 邮箱, 部门, 职位, 专业领域]")
        help_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(help_label)
        
        # ===== 关闭按钮 =====
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        
    def _load_recommendations(self):
        """加载推荐库"""
        # TODO: 从数据库加载
        self.recommendations = []
        self._refresh_table()
        
    def _refresh_table(self):
        """刷新表格"""
        self.table.setRowCount(len(self.recommendations))
        
        for row, rec in enumerate(self.recommendations):
            self.table.setItem(row, 0, QTableWidgetItem(rec.get('name', '')))
            self.table.setItem(row, 1, QTableWidgetItem(rec.get('key_module', '')))
            self.table.setItem(row, 2, QTableWidgetItem(rec.get('department', '')))
            self.table.setItem(row, 3, QTableWidgetItem(rec.get('position', '')))
            self.table.setItem(row, 4, QTableWidgetItem(rec.get('phone', '')))
            self.table.setItem(row, 5, QTableWidgetItem(rec.get('email', '')))
            
    def _on_search(self, text: str):
        """搜索"""
        if not text:
            self._refresh_table()
            return
            
        filtered = [r for r in self.recommendations
                   if text.lower() in str(r.get('name', '')).lower()
                   or text.lower() in str(r.get('key_module', '')).lower()]
        
        self.table.setRowCount(len(filtered))
        for row, rec in enumerate(filtered):
            self.table.setItem(row, 0, QTableWidgetItem(rec.get('name', '')))
            self.table.setItem(row, 1, QTableWidgetItem(rec.get('key_module', '')))
            self.table.setItem(row, 2, QTableWidgetItem(rec.get('department', '')))
            self.table.setItem(row, 3, QTableWidgetItem(rec.get('position', '')))
            self.table.setItem(row, 4, QTableWidgetItem(rec.get('phone', '')))
            self.table.setItem(row, 5, QTableWidgetItem(rec.get('email', '')))
            
    def _on_selection_changed(self):
        """选中变化"""
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            rec = self.recommendations[row] if row < len(self.recommendations) else {}
            self._show_detail(rec)
            self.edit_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
        else:
            self._clear_detail()
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            
    def _show_detail(self, rec: Dict[str, Any]):
        """显示详情"""
        self.detail_name.setText(rec.get('name', '-'))
        self.detail_module.setText(rec.get('key_module', '-'))
        self.detail_dept.setText(rec.get('department', '-'))
        self.detail_position.setText(rec.get('position', '-'))
        self.detail_phone.setText(rec.get('phone', '-'))
        self.detail_email.setText(rec.get('email', '-'))
        self.detail_expertise.setText(rec.get('expertise', '-'))
        
    def _clear_detail(self):
        """清空详情"""
        self.detail_name.setText("-")
        self.detail_module.setText("-")
        self.detail_dept.setText("-")
        self.detail_position.setText("-")
        self.detail_phone.setText("-")
        self.detail_email.setText("-")
        self.detail_expertise.setText("-")
        
    def _on_add(self):
        """添加推荐"""
        dialog = RecommendationEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            rec = dialog.get_data()
            self.recommendations.append(rec)
            self._refresh_table()
            QMessageBox.information(self, "成功", "添加成功！")
            
    def _on_edit(self):
        """编辑推荐"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请选择要编辑的记录！")
            return
            
        rec = self.recommendations[row]
        dialog = RecommendationEditDialog(self, rec)
        if dialog.exec_() == QDialog.Accepted:
            self.recommendations[row] = dialog.get_data()
            self._refresh_table()
            self._on_selection_changed()
            QMessageBox.information(self, "成功", "编辑成功！")
            
    def _on_delete(self):
        """删除推荐"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请选择要删除的记录！")
            return
            
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除「{self.recommendations[row].get('name', '')}」的推荐记录吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.recommendations[row]
            self._refresh_table()
            self._clear_detail()
            QMessageBox.information(self, "成功", "删除成功！")
            
    def _on_import(self):
        """导入推荐库"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "导入推荐库", "",
            "CSV文件 (*.csv);;文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if filepath:
            # TODO: 实现导入逻辑
            QMessageBox.information(self, "提示", "导入功能开发中...\n\n推荐格式：\n姓名，关键模块")
            
    def _on_export(self):
        """导出推荐库"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出推荐库", "推荐库.csv",
            "CSV文件 (*.csv)"
        )
        
        if filepath:
            # TODO: 实现导出逻辑
            QMessageBox.information(self, "提示", "导出功能开发中...")


class RecommendationEditDialog(QDialog):
    """推荐编辑弹窗"""
    
    def __init__(self, parent=None, recommendation: Dict[str, Any] = None):
        super().__init__(parent)
        self.setWindowTitle("编辑推荐" if recommendation else "添加推荐")
        self.recommendation = recommendation or {}
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QFormLayout(self)
        layout.setSpacing(10)
        
        self.name_edit = QLineEdit()
        self.name_edit.setText(self.recommendation.get('name', ''))
        self.name_edit.setPlaceholderText("必填")
        layout.addRow("姓名 *：", self.name_edit)
        
        self.module_edit = QLineEdit()
        self.module_edit.setText(self.recommendation.get('key_module', ''))
        self.module_edit.setPlaceholderText("必填，多个用逗号分隔")
        layout.addRow("关键模块 *：", self.module_edit)
        
        self.employee_id_edit = QLineEdit()
        self.employee_id_edit.setText(self.recommendation.get('employee_id', ''))
        layout.addRow("工号：", self.employee_id_edit)
        
        self.phone_edit = QLineEdit()
        self.phone_edit.setText(self.recommendation.get('phone', ''))
        layout.addRow("手机号：", self.phone_edit)
        
        self.email_edit = QLineEdit()
        self.email_edit.setText(self.recommendation.get('email', ''))
        layout.addRow("邮箱：", self.email_edit)
        
        self.department_edit = QLineEdit()
        self.department_edit.setText(self.recommendation.get('department', ''))
        layout.addRow("部门：", self.department_edit)
        
        self.position_edit = QLineEdit()
        self.position_edit.setText(self.recommendation.get('position', ''))
        layout.addRow("职位：", self.position_edit)
        
        self.expertise_edit = QTextEdit()
        self.expertise_edit.setPlainText(self.recommendation.get('expertise', ''))
        self.expertise_edit.setMaximumHeight(60)
        layout.addRow("专业领域：", self.expertise_edit)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
    def _on_accept(self):
        """确认"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "提示", "姓名不能为空！")
            return
            
        if not self.module_edit.text().strip():
            QMessageBox.warning(self, "提示", "关键模块不能为空！")
            return
            
        self.accept()
        
    def get_data(self) -> Dict[str, Any]:
        """获取数据"""
        return {
            'name': self.name_edit.text().strip(),
            'key_module': self.module_edit.text().strip(),
            'employee_id': self.employee_id_edit.text().strip(),
            'phone': self.phone_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'department': self.department_edit.text().strip(),
            'position': self.position_edit.text().strip(),
            'expertise': self.expertise_edit.toPlainText().strip(),
        }
