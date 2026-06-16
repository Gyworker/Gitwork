"""
通讯录管理组件
"""

from typing import List, Dict, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLineEdit, QDialog, QFormLayout, QDialogButtonBox,
    QHeaderView, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class ContactWidget(QDialog):
    """
    通讯录管理弹窗
    支持查看、添加、编辑、删除、导入通讯录
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("通讯录管理")
        self.setMinimumSize(800, 500)
        self._init_ui()
        self._load_contacts()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # ===== 标题栏 =====
        title_layout = QHBoxLayout()
        title = QLabel("👥 通讯录管理")
        title.setFont(QFont("宋体", 12, QFont.Bold))
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # 搜索框
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索姓名、手机号、邮箱...")
        self.search_edit.setMaximumWidth(250)
        self.search_edit.textChanged.connect(self._on_search)
        title_layout.addWidget(self.search_edit)
        
        layout.addLayout(title_layout)
        
        # ===== 通讯录表格 =====
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["姓名", "工号", "手机号", "邮箱", "部门", "职位"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
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
        layout.addWidget(self.table)
        
        # ===== 操作按钮 =====
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ 添加")
        self.add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("✏️ 编辑")
        self.edit_btn.clicked.connect(self._on_edit)
        btn_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("🗑️ 删除")
        self.delete_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(self.delete_btn)
        
        btn_layout.addStretch()
        
        self.import_btn = QPushButton("📥 导入")
        self.import_btn.clicked.connect(self._on_import)
        btn_layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("📤 导出")
        self.export_btn.clicked.connect(self._on_export)
        btn_layout.addWidget(self.export_btn)
        
        layout.addLayout(btn_layout)
        
        # ===== 关闭按钮 =====
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        
    def _load_contacts(self):
        """加载通讯录"""
        # TODO: 从数据库加载
        self.contacts = []
        self._refresh_table()
        
    def _refresh_table(self):
        """刷新表格"""
        self.table.setRowCount(len(self.contacts))
        
        for row, contact in enumerate(self.contacts):
            self.table.setItem(row, 0, QTableWidgetItem(contact.get('name', '')))
            self.table.setItem(row, 1, QTableWidgetItem(contact.get('employee_id', '')))
            self.table.setItem(row, 2, QTableWidgetItem(contact.get('phone', '')))
            self.table.setItem(row, 3, QTableWidgetItem(contact.get('email', '')))
            self.table.setItem(row, 4, QTableWidgetItem(contact.get('department', '')))
            self.table.setItem(row, 5, QTableWidgetItem(contact.get('position', '')))
            
    def _on_search(self, text: str):
        """搜索"""
        if not text:
            self._refresh_table()
            return
            
        filtered = [c for c in self.contacts 
                   if text.lower() in str(c.get('name', '')).lower()
                   or text.lower() in str(c.get('phone', '')).lower()
                   or text.lower() in str(c.get('email', '')).lower()]
        
        self.table.setRowCount(len(filtered))
        for row, contact in enumerate(filtered):
            self.table.setItem(row, 0, QTableWidgetItem(contact.get('name', '')))
            self.table.setItem(row, 1, QTableWidgetItem(contact.get('employee_id', '')))
            self.table.setItem(row, 2, QTableWidgetItem(contact.get('phone', '')))
            self.table.setItem(row, 3, QTableWidgetItem(contact.get('email', '')))
            self.table.setItem(row, 4, QTableWidgetItem(contact.get('department', '')))
            self.table.setItem(row, 5, QTableWidgetItem(contact.get('position', '')))
            
    def _on_add(self):
        """添加联系人"""
        dialog = ContactEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            contact = dialog.get_data()
            self.contacts.append(contact)
            self._refresh_table()
            
    def _on_edit(self):
        """编辑联系人"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请选择要编辑的联系人！")
            return
            
        contact = self.contacts[row]
        dialog = ContactEditDialog(self, contact)
        if dialog.exec_() == QDialog.Accepted:
            self.contacts[row] = dialog.get_data()
            self._refresh_table()
            
    def _on_delete(self):
        """删除联系人"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请选择要删除的联系人！")
            return
            
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除联系人「{self.contacts[row].get('name', '')}」吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.contacts[row]
            self._refresh_table()
            
    def _on_import(self):
        """导入通讯录"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "导入通讯录", "",
            "文本文件 (*.txt *.csv);;Excel文件 (*.xlsx *.xls)"
        )
        
        if filepath:
            # TODO: 实现导入逻辑
            QMessageBox.information(self, "提示", "导入功能开发中...")
            
    def _on_export(self):
        """导出通讯录"""
        # TODO: 实现导出逻辑
        QMessageBox.information(self, "提示", "导出功能开发中...")


class ContactEditDialog(QDialog):
    """联系人编辑弹窗"""
    
    def __init__(self, parent=None, contact: Dict[str, Any] = None):
        super().__init__(parent)
        self.setWindowTitle("编辑联系人" if contact else "添加联系人")
        self.contact = contact or {}
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QFormLayout(self)
        layout.setSpacing(10)
        
        self.name_edit = QLineEdit()
        self.name_edit.setText(self.contact.get('name', ''))
        layout.addRow("姓名 *：", self.name_edit)
        
        self.employee_id_edit = QLineEdit()
        self.employee_id_edit.setText(self.contact.get('employee_id', ''))
        layout.addRow("工号：", self.employee_id_edit)
        
        self.phone_edit = QLineEdit()
        self.phone_edit.setText(self.contact.get('phone', ''))
        layout.addRow("手机号：", self.phone_edit)
        
        self.email_edit = QLineEdit()
        self.email_edit.setText(self.contact.get('email', ''))
        layout.addRow("邮箱：", self.email_edit)
        
        self.department_edit = QLineEdit()
        self.department_edit.setText(self.contact.get('department', ''))
        layout.addRow("部门：", self.department_edit)
        
        self.position_edit = QLineEdit()
        self.position_edit.setText(self.contact.get('position', ''))
        layout.addRow("职位：", self.position_edit)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
    def get_data(self) -> Dict[str, Any]:
        """获取数据"""
        return {
            'name': self.name_edit.text().strip(),
            'employee_id': self.employee_id_edit.text().strip(),
            'phone': self.phone_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'department': self.department_edit.text().strip(),
            'position': self.position_edit.text().strip(),
        }
