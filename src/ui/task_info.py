# -*- coding: utf-8 -*-
"""
任务信息组件
包含所有任务字段的输入和管理

版本：V4.1 (优化版)
"""

from typing import Optional, Dict, Any
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox,
    QPushButton, QGroupBox, QDateTimeEdit,
    QScrollArea, QSizePolicy, QFrame
)
from PyQt5.QtCore import pyqtSignal, Qt, QDateTime
from PyQt5.QtGui import QFont


class TaskInfoWidget(QWidget):
    """
    任务信息组件
    包含完整的任务字段编辑功能
    """
    
    # 信号：任务提交
    task_submitted = pyqtSignal(dict)
    
    # 字段定义
    FIELDS = {
        'task_name': {'label': '任务名称', 'required': True, 'type': 'text'},
        'importance': {'label': '重要程度', 'required': True, 'type': 'combo', 
                       'options': ['高', '中', '低']},
        'status': {'label': '状态', 'required': True, 'type': 'combo',
                   'options': ['进行中', '挂起', '已答复', '完成']},
        'task_content': {'label': '任务具体内容', 'required': False, 'type': 'textarea'},
        'product_model': {'label': '产品型号和板卡', 'required': False, 'type': 'text'},
        'consultant_name': {'label': '咨询者姓名', 'required': True, 'type': 'text'},
        'consultant_contact': {'label': '咨询者联系方式', 'required': False, 'type': 'text'},
        'consultant_dept': {'label': '咨询者部门', 'required': False, 'type': 'text_edit'},
        'responder_name': {'label': '答复人姓名', 'required': False, 'type': 'text_with_recommend'},
        'responder_contact': {'label': '答复人联系方式', 'required': False, 'type': 'text'},
        'responder_dept': {'label': '答复人部门', 'required': False, 'type': 'text_edit'},
        'industry': {'label': '所属行业', 'required': False, 'type': 'text_edit'},
        'key_module': {'label': '关键模块', 'required': False, 'type': 'text_edit'},
        'remarks': {'label': '备注信息', 'required': False, 'type': 'textarea'},
        'task_time': {'label': '任务创建时间', 'required': False, 'type': 'datetime'},
        'expected_time': {'label': '预期答复时间', 'required': False, 'type': 'datetime'},
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_task_id = None
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # ===== 标题栏 =====
        self._create_title_bar(layout)
        
        # ===== 可滚动区域 =====
        scroll = self._create_scroll_area()
        self._create_form_fields(scroll)
        layout.addWidget(scroll, 1)
        
        # ===== 操作按钮 =====
        self._create_action_buttons(layout)
    
    def _create_title_bar(self, layout: QVBoxLayout):
        """创建标题栏"""
        title_layout = QHBoxLayout()
        title = QLabel("📋 任务信息")
        title.setFont(QFont("宋体", 11, QFont.Bold))
        title.setStyleSheet("color: #1976D2;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
    
    def _create_scroll_area(self) -> QScrollArea:
        """创建滚动区域"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_content = QWidget()
        scroll_content.layout = QFormLayout(scroll_content)
        scroll_content.layout.setLabelAlignment(Qt.AlignRight)
        scroll_content.layout.setSpacing(8)
        scroll_content.layout.setContentsMargins(10, 10, 10, 10)
        scroll.setWidget(scroll_content)
        return scroll
    
    def _create_form_fields(self, scroll: QScrollArea):
        """创建表单字段"""
        content = scroll.widget()
        layout = content.layout
        
        # 基本信息
        self._add_section_header(layout, "基本信息")
        self._add_basic_fields(layout)
        
        # 咨询者信息
        self._add_section_header(layout, "咨询者信息")
        self._add_consultant_fields(layout)
        
        # 答复人信息
        self._add_section_header(layout, "答复人信息")
        self._add_responder_fields(layout)
        
        # 其他信息
        self._add_section_header(layout, "其他信息")
        self._add_other_fields(layout)
    
    def _add_section_header(self, layout: QFormLayout, title: str):
        """添加分组标题"""
        label = QLabel(f"【{title}】")
        label.setFont(QFont("宋体", 10, QFont.Bold))
        label.setStyleSheet("color: #1565C0; background-color: #E3F2FD; padding: 5px;")
        layout.addRow("", label)
    
    def _add_basic_fields(self, layout: QFormLayout):
        """添加基本信息字段"""
        # 任务创建时间
        self.task_time_edit = QDateTimeEdit()
        self.task_time_edit.setDateTime(QDateTime.currentDateTime())
        self.task_time_edit.setCalendarPopup(True)
        self.task_time_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        layout.addRow("任务创建时间：", self.task_time_edit)
        
        # 预期答复时间
        self.expected_time_edit = QDateTimeEdit()
        default_time = QDateTime.currentDateTime().addDays(1)
        self.expected_time_edit.setDateTime(default_time)
        self.expected_time_edit.setCalendarPopup(True)
        self.expected_time_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        layout.addRow("预期答复时间：", self.expected_time_edit)
        
        # 任务名称
        self.task_name_edit = QLineEdit()
        self.task_name_edit.setPlaceholderText("必填，请输入任务名称...")
        self.task_name_edit.setMaxLength(100)
        layout.addRow("任务名称 *：", self.task_name_edit)
        
        # 重要程度
        self.importance_combo = QComboBox()
        self.importance_combo.addItems(['高', '中', '低'])
        self.importance_combo.setCurrentText('中')
        layout.addRow("重要程度 *：", self.importance_combo)
        
        # 状态
        self.status_combo = QComboBox()
        self.status_combo.addItems(['进行中', '挂起', '已答复', '完成'])
        layout.addRow("状态 *：", self.status_combo)
    
    def _add_consultant_fields(self, layout: QFormLayout):
        """添加咨询者信息字段"""
        # 咨询者姓名
        self.consultant_name_edit = QLineEdit()
        self.consultant_name_edit.setPlaceholderText("必填，请输入咨询者姓名...")
        self.consultant_name_edit.setMaxLength(50)
        layout.addRow("咨询者姓名 *：", self.consultant_name_edit)
        
        # 咨询者联系方式
        self.consultant_contact_edit = QLineEdit()
        self.consultant_contact_edit.setPlaceholderText("手机号或邮箱...")
        self.consultant_contact_edit.setMaxLength(100)
        layout.addRow("咨询者联系方式：", self.consultant_contact_edit)
        
        # 咨询者部门
        self.consultant_dept_edit = self._create_direct_edit_field("请输入咨询者部门...")
        layout.addRow(self._create_field_label("咨询者部门", True), self.consultant_dept_edit)
    
    def _add_responder_fields(self, layout: QFormLayout):
        """添加答复人信息字段"""
        # 答复人姓名（带智能推荐）
        responder_layout = QHBoxLayout()
        self.responder_name_edit = QLineEdit()
        self.responder_name_edit.setPlaceholderText("可输入答复人姓名...")
        self.responder_name_edit.setMaxLength(50)
        responder_layout.addWidget(self.responder_name_edit)
        
        recommend_btn = QPushButton("🔮 智能推荐")
        recommend_btn.clicked.connect(self._on_recommend)
        responder_layout.addWidget(recommend_btn)
        layout.addRow("答复人姓名：", responder_layout)
        
        # 答复人联系方式
        self.responder_contact_edit = QLineEdit()
        self.responder_contact_edit.setPlaceholderText("手机号或邮箱...")
        self.responder_contact_edit.setMaxLength(100)
        layout.addRow("答复人联系方式：", self.responder_contact_edit)
        
        # 答复人部门
        self.responder_dept_edit = self._create_direct_edit_field("请输入答复人部门...")
        layout.addRow(self._create_field_label("答复人部门", True), self.responder_dept_edit)
    
    def _add_other_fields(self, layout: QFormLayout):
        """添加其他信息字段"""
        # 产品型号和板卡
        self.product_model_edit = QLineEdit()
        self.product_model_edit.setPlaceholderText("请输入产品型号和板卡...")
        self.product_model_edit.setMaxLength(200)
        layout.addRow("产品型号和板卡：", self.product_model_edit)
        
        # 所属行业
        self.industry_edit = self._create_direct_edit_field("请输入所属行业...")
        layout.addRow(self._create_field_label("所属行业", True), self.industry_edit)
        
        # 关键模块
        self.key_module_edit = self._create_direct_edit_field("请输入关键模块，多个模块用逗号分隔...")
        layout.addRow(self._create_field_label("关键模块", True), self.key_module_edit)
        
        # 任务具体内容
        self.task_content_edit = QTextEdit()
        self.task_content_edit.setPlaceholderText("请输入任务具体内容（支持至少2000个中文字符）...")
        self.task_content_edit.setMaximumHeight(100)
        layout.addRow("任务具体内容：", self.task_content_edit)
        
        # 备注信息
        self.remarks_edit = QTextEdit()
        self.remarks_edit.setPlaceholderText("请输入备注信息...")
        self.remarks_edit.setMaximumHeight(60)
        layout.addRow("备注信息：", self.remarks_edit)
    
    def _create_field_label(self, text: str, is_direct_edit: bool = False) -> QLabel:
        """创建字段标签"""
        label = QLabel(f"{text}：")
        if is_direct_edit:
            label.setToolTip("📝 直接编辑")
        return label
    
    def _create_direct_edit_field(self, placeholder: str = "") -> QWidget:
        """创建直接编辑字段"""
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setMaxLength(100)
        edit.setStyleSheet("""
            QLineEdit {
                background-color: #FAFFFE;
                border: 1px solid #E0E0E0;
                border-radius: 3px;
                padding: 4px 8px;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;
                background-color: #FFFFFF;
            }
        """)
        return edit
    
    def _create_action_buttons(self, layout: QVBoxLayout):
        """创建操作按钮"""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.submit_btn = QPushButton("✅ 确认任务")
        self.submit_btn.setMinimumHeight(40)
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.submit_btn.clicked.connect(self._on_submit)
        btn_layout.addWidget(self.submit_btn)
        
        self.clear_btn = QPushButton("🔄 重置")
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.clicked.connect(self.clear)
        btn_layout.addWidget(self.clear_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    # =========================================================================
    # 事件处理方法
    # =========================================================================
    
    def _on_recommend(self):
        """智能推荐答复人"""
        key_module = self.key_module_edit.text().strip()
        
        if not key_module:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "提示", "请先输入关键模块，再进行推荐！")
            return
            
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "智能推荐", f"正在根据「{key_module}」匹配推荐库...")
    
    def _on_submit(self):
        """提交任务 - 主方法（已拆分）"""
        # 步骤1: 验证必填字段
        if not self._validate_required_fields():
            return
        
        # 步骤2: 收集任务数据
        task_data = self._collect_task_data()
        
        # 步骤3: 发送任务信号
        self.task_submitted.emit(task_data)
    
    def _validate_required_fields(self) -> bool:
        """
        验证必填字段
        
        Returns:
            是否验证通过
        """
        from PyQt5.QtWidgets import QMessageBox
        
        # 验证任务名称
        if not self.task_name_edit.text().strip():
            QMessageBox.warning(self, "验证失败", "请输入任务名称！")
            self.task_name_edit.setFocus()
            return False
        
        # 验证咨询者姓名
        if not self.consultant_name_edit.text().strip():
            QMessageBox.warning(self, "验证失败", "请输入咨询者姓名！")
            self.consultant_name_edit.setFocus()
            return False
        
        return True
    
    def _collect_task_data(self) -> Dict[str, Any]:
        """
        收集任务数据
        
        Returns:
            任务数据字典
        """
        return {
            'task_id': self.current_task_id,
            # 基本信息
            'task_name': self.task_name_edit.text().strip(),
            'importance': self.importance_combo.currentText(),
            'status': self.status_combo.currentText(),
            'task_content': self.task_content_edit.toPlainText().strip(),
            'product_model': self.product_model_edit.text().strip(),
            # 咨询者信息
            'consultant_name': self.consultant_name_edit.text().strip(),
            'consultant_contact': self.consultant_contact_edit.text().strip(),
            'consultant_dept': self._get_direct_edit_value(self.consultant_dept_edit),
            # 答复人信息
            'responder_name': self.responder_name_edit.text().strip(),
            'responder_contact': self.responder_contact_edit.text().strip(),
            'responder_dept': self._get_direct_edit_value(self.responder_dept_edit),
            # 其他信息
            'industry': self._get_direct_edit_value(self.industry_edit),
            'key_module': self._get_direct_edit_value(self.key_module_edit),
            'remarks': self.remarks_edit.toPlainText().strip(),
            # 时间
            'task_time': self.task_time_edit.dateTime().toPython(),
            'expected_time': self.expected_time_edit.dateTime().toPython(),
        }
    
    def _get_direct_edit_value(self, widget) -> str:
        """获取直接编辑字段的值"""
        if isinstance(widget, QLineEdit):
            return widget.text().strip()
        return ""
    
    # =========================================================================
    # 数据加载方法
    # =========================================================================
    
    def fill_from_parsed(self, parsed_data: dict):
        """填充解析后的数据"""
        if 'task_name' in parsed_data:
            self.task_name_edit.setText(parsed_data['task_name'])
        if 'task_content' in parsed_data:
            self.task_content_edit.setPlainText(parsed_data['task_content'])
        if 'consultant_name' in parsed_data:
            self.consultant_name_edit.setText(parsed_data['consultant_name'])
        if 'key_module' in parsed_data:
            self._set_direct_edit_value(self.key_module_edit, parsed_data.get('key_module', ''))
        if 'product_model' in parsed_data:
            self.product_model_edit.setText(parsed_data['product_model'])
    
    def _set_direct_edit_value(self, widget, value: str):
        """设置直接编辑字段的值"""
        if isinstance(widget, QLineEdit):
            widget.setText(value)
    
    def load_task(self, task: dict):
        """加载任务数据"""
        self.current_task_id = task.get('task_id')
        
        # 基本信息
        self.task_name_edit.setText(task.get('task_name', ''))
        self.importance_combo.setCurrentText(task.get('importance', '中'))
        self.status_combo.setCurrentText(task.get('status', '进行中'))
        self.task_content_edit.setPlainText(task.get('task_content', ''))
        self.product_model_edit.setText(task.get('product_model', ''))
        
        # 咨询者信息
        self.consultant_name_edit.setText(task.get('consultant_name', ''))
        self.consultant_contact_edit.setText(task.get('consultant_contact', ''))
        
        # 答复人信息
        self.responder_name_edit.setText(task.get('responder_name', ''))
        self.responder_contact_edit.setText(task.get('responder_contact', ''))
        
        # 备注
        self.remarks_edit.setPlainText(task.get('remarks', ''))
        
        # 直接编辑字段
        self._load_direct_edit_field(self.consultant_dept_edit, task.get('consultant_dept', ''))
        self._load_direct_edit_field(self.responder_dept_edit, task.get('responder_dept', ''))
        self._load_direct_edit_field(self.industry_edit, task.get('industry', ''))
        self._load_direct_edit_field(self.key_module_edit, task.get('key_module', ''))
        
        # 时间字段
        self._load_datetime_field(self.task_time_edit, task.get('task_time'))
        self._load_datetime_field(self.expected_time_edit, task.get('expected_time'))
    
    def _load_direct_edit_field(self, widget, value: str):
        """加载直接编辑字段"""
        if isinstance(widget, QLineEdit):
            widget.setText(value)
    
    def _load_datetime_field(self, widget, value):
        """加载时间字段"""
        if value:
            dt = QDateTime.fromString(value, 'yyyy-MM-dd HH:mm:ss')
            widget.setDateTime(dt)
    
    def clear(self):
        """清空表单"""
        self.current_task_id = None
        
        # 清除文本字段
        self._clear_text_fields()
        
        # 清除下拉框
        self.importance_combo.setCurrentText('中')
        self.status_combo.setCurrentText('进行中')
        
        # 清除直接编辑字段
        self._clear_direct_edit_fields()
        
        # 重置时间
        self.task_time_edit.setDateTime(QDateTime.currentDateTime())
        default_time = QDateTime.currentDateTime().addDays(1)
        self.expected_time_edit.setDateTime(default_time)
    
    def _clear_text_fields(self):
        """清除文本字段"""
        self.task_name_edit.clear()
        self.task_content_edit.clear()
        self.product_model_edit.clear()
        self.consultant_name_edit.clear()
        self.consultant_contact_edit.clear()
        self.responder_name_edit.clear()
        self.responder_contact_edit.clear()
        self.remarks_edit.clear()
    
    def _clear_direct_edit_fields(self):
        """清除直接编辑字段"""
        for field in ['consultant_dept_edit', 'responder_dept_edit', 
                      'industry_edit', 'key_module_edit']:
            widget = getattr(self, field, None)
            if isinstance(widget, QLineEdit):
                widget.clear()
