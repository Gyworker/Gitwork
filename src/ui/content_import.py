# -*- coding: utf-8 -*-
"""
内容导入组件 - UI层
只负责UI交互，业务逻辑委托给ContentParserService

版本：V4.1 (重构版)
"""

from typing import Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QGroupBox, QRadioButton,
    QFileDialog, QMessageBox
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont

# 导入业务逻辑层
from src.content.content_parser_service import (
    get_parser_service,
    ContentParserService,
    ParsedContent,
)
from src.content.msg_parser import MSGParser


class ContentImportWidget(QWidget):
    """
    内容导入组件 (UI层)
    
    职责：
    - UI布局和交互
    - 用户输入处理
    - 调用业务服务
    
    布局：
    - 标题栏（固定）
    - 导入方式选择
    - 输入文本框
    - 操作按钮
    """
    
    # 信号：内容解析完成
    content_parsed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 业务逻辑服务
        self._parser_service: ContentParserService = get_parser_service()
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # ===== 标题栏 =====
        self._create_title_bar(layout)
        
        # ===== 导入方式选择 =====
        self._create_method_selector(layout)
        
        # ===== 输入内容区 =====
        self._create_input_area(layout)
        
        # ===== 操作按钮 =====
        self._create_action_buttons(layout)
    
    def _create_title_bar(self, layout: QVBoxLayout):
        """创建标题栏"""
        title_layout = QHBoxLayout()
        title = QLabel("📥 内容导入")
        title.setFont(QFont("宋体", 11, QFont.Bold))
        title.setStyleSheet("color: #1976D2;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        self.help_btn = QPushButton("?")
        self.help_btn.setFixedSize(25, 25)
        self.help_btn.setToolTip("查看帮助")
        self.help_btn.clicked.connect(self._show_help)
        title_layout.addWidget(self.help_btn)
        layout.addLayout(title_layout)
    
    def _create_method_selector(self, layout: QVBoxLayout):
        """创建导入方式选择器"""
        method_group = QGroupBox("导入方式")
        method_layout = QHBoxLayout(method_group)
        
        # 文本选项
        self.radio_text = QRadioButton("文本")
        self.radio_text.setChecked(True)
        self.radio_text.toggled.connect(self._on_method_changed)
        method_layout.addWidget(self.radio_text)
        
        # 图片选项
        self.radio_image = QRadioButton("图片")
        self.radio_image.toggled.connect(self._on_method_changed)
        method_layout.addWidget(self.radio_image)
        
        # MSG邮件选项
        self.radio_outlook = QRadioButton("邮件(MSG)")
        self.radio_outlook.toggled.connect(self._on_method_changed)
        method_layout.addWidget(self.radio_outlook)
        
        # 企业微信选项
        self.radio_wechat = QRadioButton("企业微信")
        self.radio_wechat.toggled.connect(self._on_method_changed)
        method_layout.addWidget(self.radio_wechat)
        
        method_layout.addStretch()
        layout.addWidget(method_group)
    
    def _create_input_area(self, layout: QVBoxLayout):
        """创建输入区域"""
        self.input_label = QLabel("📌 请输入内容：")
        self.input_label.setFont(QFont("宋体", 10))
        layout.addWidget(self.input_label)
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("在此粘贴或输入内容...")
        self.input_text.setFont(QFont("宋体", 10))
        layout.addWidget(self.input_text, 1)
        
        # 模式切换标签
        self.mode_label = QLabel("📄 文本模式")
        self.mode_label.setStyleSheet("color: #666;")
        layout.addWidget(self.mode_label)
    
    def _create_action_buttons(self, layout: QVBoxLayout):
        """创建操作按钮"""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.parse_btn = QPushButton("🔍 解析")
        self.parse_btn.setMinimumHeight(35)
        self.parse_btn.clicked.connect(self._on_parse)
        btn_layout.addWidget(self.parse_btn)
        
        self.clear_btn = QPushButton("🗑️ 清除")
        self.clear_btn.setMinimumHeight(35)
        self.clear_btn.clicked.connect(self._on_clear)
        btn_layout.addWidget(self.clear_btn)
        
        self.file_btn = QPushButton("📁 文件")
        self.file_btn.setMinimumHeight(35)
        self.file_btn.clicked.connect(self._on_open_file)
        btn_layout.addWidget(self.file_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _on_method_changed(self):
        """导入方式切换"""
        if self.radio_text.isChecked():
            self._update_for_text_mode()
        elif self.radio_image.isChecked():
            self._update_for_image_mode()
        elif self.radio_outlook.isChecked():
            self._update_for_msg_mode()
        elif self.radio_wechat.isChecked():
            self._update_for_wechat_mode()
    
    def _update_for_text_mode(self):
        """切换到文本模式"""
        self.mode_label.setText("📄 文本模式")
        self.input_label.setText("📌 请输入内容：")
        self.input_text.setPlaceholderText("在此粘贴或输入内容...")
    
    def _update_for_image_mode(self):
        """切换到图片模式"""
        self.mode_label.setText("🖼️ 图片模式（OCR识别）")
        self.input_label.setText("📌 请导入图片或拖拽图片到下方：")
        self.input_text.setPlaceholderText(
            "支持 JPG、PNG 格式...\n点击'文件'按钮导入图片"
        )
    
    def _update_for_msg_mode(self):
        """切换到MSG模式"""
        self.mode_label.setText("📧 MSG邮件模式")
        self.input_label.setText("📌 请导入邮件文件（.msg）：")
        self.input_text.setPlaceholderText(
            "支持 .msg 格式Outlook邮件文件...\n点击'文件'按钮选择MSG文件"
        )
    
    def _update_for_wechat_mode(self):
        """切换到企业微信模式"""
        self.mode_label.setText("💬 企业微信模式")
        self.input_label.setText("📌 请导入企业微信聊天记录文件：")
        self.input_text.setPlaceholderText(
            "支持企业微信导出的聊天记录文件..."
        )
    
    def _get_source_type(self) -> str:
        """获取当前选择的来源类型"""
        if self.radio_text.isChecked():
            return "text"
        elif self.radio_image.isChecked():
            return "image"
        elif self.radio_outlook.isChecked():
            return "msg"
        elif self.radio_wechat.isChecked():
            return "wechat"
        return "text"
    
    def _on_parse(self):
        """解析内容 - 调用业务服务"""
        content = self.input_text.toPlainText().strip()
        
        if not content:
            QMessageBox.warning(self, "提示", "请输入内容后再解析！")
            return
        
        try:
            # 获取来源类型
            source_type = self._get_source_type()
            
            # 调用业务服务解析
            result = self._parser_service.parse(content, source_type)
            
            # 处理解析结果
            if result.is_success:
                self.content_parsed.emit(result.to_dict())
                QMessageBox.information(
                    self, "解析成功",
                    f"成功解析内容！\n\n主题: {result.task_name}"
                )
            else:
                error_msg = result.error
                if result.error_details:
                    error_msg += f"\n\n详情: {result.error_details}"
                QMessageBox.critical(self, "解析错误", error_msg)
                
        except Exception as e:
            QMessageBox.critical(self, "解析错误", f"解析失败：{e}")
    
    def _on_clear(self):
        """清除内容"""
        self.input_text.clear()
    
    def _on_open_file(self):
        """打开文件"""
        if self.radio_image.isChecked():
            filepath, _ = QFileDialog.getOpenFileName(
                self, "选择图片", "",
                "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
            )
        elif self.radio_outlook.isChecked():
            filepath, _ = QFileDialog.getOpenFileName(
                self, "选择邮件", "",
                "Outlook邮件 (*.msg)"
            )
        else:
            filepath, _ = QFileDialog.getOpenFileName(
                self, "选择文件", "",
                "文本文件 (*.txt);;所有文件 (*.*)"
            )
            
        if filepath:
            self._load_file(filepath)
    
    def _load_file(self, filepath: str):
        """加载文件"""
        if filepath.lower().endswith('.msg'):
            self._load_msg_file(filepath)
        else:
            self._load_text_file(filepath)
    
    def _load_text_file(self, filepath: str):
        """加载文本文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self.input_text.setPlainText(content)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取文件失败：{e}")
    
    def _load_msg_file(self, filepath: str):
        """加载MSG邮件文件 - 使用业务服务"""
        try:
            # 使用业务服务解析
            parser = self._parser_service.get_parser('msg')
            if parser and not parser.is_available():
                QMessageBox.warning(
                    self, "库未安装",
                    "MSG解析库未安装。\n\n请在命令行运行:\npip install extract-msg"
                )
                return
            
            result = parser.parse(filepath)
            
            if result.is_success:
                # 显示预览
                QMessageBox.information(
                    self, "MSG文件预览",
                    result.preview + "\n\n点击'解析'按钮提取任务信息"
                )
                # 将文件路径存入输入框
                self.input_text.setPlainText(filepath)
            else:
                error_msg = result.error
                if result.error_details:
                    error_msg += f"\n\n详情: {result.error_details}"
                QMessageBox.critical(self, "错误", error_msg)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取MSG文件失败：{e}")
    
    def _show_help(self):
        """显示帮助"""
        # 检查依赖状态
        deps = self._parser_service.check_dependencies()
        
        help_text = "内容导入说明：\n\n"
        help_text += "• 文本：直接粘贴或输入文字内容\n"
        help_text += "• 图片：导入图片进行OCR识别\n"
        help_text += "• 邮件(MSG)：导入Outlook邮件文件\n"
        help_text += "• 企业微信：导入聊天记录文件\n\n"
        help_text += "依赖库状态：\n"
        for name, available in deps.items():
            status = "✓ 已安装" if available else "✗ 未安装"
            help_text += f"  {name}: {status}\n"
        help_text += "\n导入流程：\n"
        help_text += "1. 选择导入方式\n"
        help_text += "2. 点击'文件'按钮选择文件\n"
        help_text += "3. 点击'解析'提取任务信息\n"
        help_text += "4. 在右侧确认并保存任务"
        
        QMessageBox.information(self, "使用帮助", help_text)
    
    def clear(self):
        """清空输入"""
        self.input_text.clear()
        self.radio_text.setChecked(True)
