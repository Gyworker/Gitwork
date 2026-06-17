"""
内容导入组件
支持：文本粘贴、图片OCR、MSG邮件文件、企业微信
"""

from typing import Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QGroupBox, QRadioButton,
    QFileDialog, QMessageBox
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont

# 导入内容解析模块
from src.content.msg_parser import MSGParser, MSGEmail


class ContentImportWidget(QWidget):
    """
    内容导入组件
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
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # ===== 标题栏 =====
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
        
        # ===== 导入方式选择 =====
        method_group = QGroupBox("导入方式")
        method_layout = QHBoxLayout(method_group)
        
        self.radio_text = QRadioButton("文本")
        self.radio_text.setChecked(True)
        self.radio_text.toggled.connect(self._on_method_changed)
        method_layout.addWidget(self.radio_text)
        
        self.radio_image = QRadioButton("图片")
        self.radio_image.toggled.connect(self._on_method_changed)
        method_layout.addWidget(self.radio_image)
        
        self.radio_outlook = QRadioButton("邮件(MSG)")
        self.radio_outlook.toggled.connect(self._on_method_changed)
        method_layout.addWidget(self.radio_outlook)
        
        self.radio_wechat = QRadioButton("企业微信")
        self.radio_wechat.toggled.connect(self._on_method_changed)
        method_layout.addWidget(self.radio_wechat)
        
        method_layout.addStretch()
        layout.addWidget(method_group)
        
        # ===== 输入内容区 =====
        self.input_label = QLabel("📌 请输入内容：")
        self.input_label.setFont(QFont("宋体", 10))
        layout.addWidget(self.input_label)
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("在此粘贴或输入内容...")
        self.input_text.setFont(QFont("宋体", 10))
        layout.addWidget(self.input_text, 1)
        
        # ===== 模式切换标签 =====
        self.mode_label = QLabel("📄 文本模式")
        self.mode_label.setStyleSheet("color: #666;")
        layout.addWidget(self.mode_label)
        
        # ===== 操作按钮 =====
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
            self.mode_label.setText("📄 文本模式")
            self.input_label.setText("📌 请输入内容：")
            self.input_text.setPlaceholderText("在此粘贴或输入内容...")
        elif self.radio_image.isChecked():
            self.mode_label.setText("🖼️ 图片模式（OCR识别）")
            self.input_label.setText("📌 请导入图片或拖拽图片到下方：")
            self.input_text.setPlaceholderText("支持 JPG、PNG 格式...\n点击'文件'按钮导入图片")
        elif self.radio_outlook.isChecked():
            self.mode_label.setText("📧 MSG邮件模式")
            self.input_label.setText("📌 请导入邮件文件（.msg）：")
            self.input_text.setPlaceholderText("支持 .msg 格式Outlook邮件文件...\n点击'文件'按钮选择MSG文件")
        elif self.radio_wechat.isChecked():
            self.mode_label.setText("💬 企业微信模式")
            self.input_label.setText("📌 请导入企业微信聊天记录文件：")
            self.input_text.setPlaceholderText("支持企业微信导出的聊天记录文件...")
            
    def _on_parse(self):
        """解析内容"""
        content = self.input_text.toPlainText().strip()
        
        if not content:
            QMessageBox.warning(self, "提示", "请输入内容后再解析！")
            return
            
        try:
            # 根据导入方式进行解析
            if self.radio_text.isChecked():
                parsed = self._parse_text(content)
            elif self.radio_image.isChecked():
                parsed = self._parse_image(content)
            elif self.radio_outlook.isChecked():
                parsed = self._parse_outlook(content)
            elif self.radio_wechat.isChecked():
                parsed = self._parse_wechat(content)
            else:
                parsed = {}
                
            self.content_parsed.emit(parsed)
            
        except Exception as e:
            QMessageBox.critical(self, "解析错误", f"解析失败：{e}")
            
    def _parse_text(self, content: str) -> dict:
        """解析文本内容"""
        # TODO: 实现文本解析逻辑
        # 目前返回占位数据
        return {
            'task_name': content[:50] if len(content) > 50 else content,
            'task_content': content,
            'source': 'text'
        }
        
    def _parse_image(self, content: str) -> dict:
        """解析图片（OCR）"""
        # TODO: 实现OCR识别
        return {
            'task_name': '图片识别任务',
            'task_content': content,
            'source': 'image'
        }
        
    def _parse_outlook(self, content: str) -> dict:
        """解析MSG邮件文件"""
        # 检查MSG解析库是否可用
        if not MSGParser.is_available():
            QMessageBox.warning(
                self, "库未安装",
                "MSG解析库未安装，部分功能可能受限。\n"
                "建议安装: pip install extract-msg"
            )
        
        # content此时应该是文件路径
        filepath = content.strip()
        
        if not filepath or not filepath.endswith('.msg'):
            return {
                'task_name': '邮件任务',
                'task_content': '请先选择MSG邮件文件',
                'source': 'msg'
            }
        
        try:
            # 解析MSG文件
            email = MSGParser.parse_file_safe(filepath)
            
            # 构建任务数据
            task_data = {
                'task_name': email.subject or '无主题邮件',
                'task_content': email.to_task_content(),
                'source': 'msg',
                'sender': email.sender,
                'sender_email': email.sender_email,
                'date': email.date,
                'importance': email.importance,
                'attachments': email.attachments,
                # 额外信息供后续处理
                '_raw_email': email
            }
            
            return task_data
            
        except ImportError as e:
            QMessageBox.critical(self, "解析错误", str(e))
            return {
                'task_name': '邮件任务',
                'task_content': f'解析失败: {str(e)}',
                'source': 'msg',
                'error': str(e)
            }
        except Exception as e:
            QMessageBox.critical(self, "解析错误", f"解析MSG文件失败: {e}")
            return {
                'task_name': '邮件任务',
                'task_content': f'解析失败: {str(e)}',
                'source': 'msg',
                'error': str(e)
            }
        
    def _parse_wechat(self, content: str) -> dict:
        """解析企业微信"""
        # TODO: 实现企业微信解析
        return {
            'task_name': '企业微信任务',
            'task_content': content,
            'source': 'wechat'
        }
        
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
            self._load_file_content(filepath)
            
    def _load_file_content(self, filepath: str):
        """加载文件内容"""
        try:
            # MSG文件特殊处理
            if filepath.lower().endswith('.msg'):
                self._load_msg_file(filepath)
                return
            
            # 普通文本文件
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self.input_text.setPlainText(content)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取文件失败：{e}")
    
    def _load_msg_file(self, filepath: str):
        """加载MSG邮件文件"""
        try:
            # 尝试解析MSG文件
            email = MSGParser.parse_file_safe(filepath)
            
            # 显示邮件预览
            preview = f"【主题】{email.subject or '无主题'}\n"
            preview += f"【发件人】{email.sender or ''} <{email.sender_email}>\n"
            preview += f"【时间】{email.date}\n"
            preview += f"【重要程度】{email.importance}\n"
            preview += "\n" + "="*50 + "\n"
            preview += "【正文预览】\n"
            preview += email.body[:500] if email.body else "(无正文)"
            if len(email.body or '') > 500:
                preview += "\n...(正文过长，已截断)"
            
            if email.attachments:
                preview += "\n\n" + "="*50 + "\n"
                preview += f"【附件】{len(email.attachments)}个\n"
                for att in email.attachments[:5]:
                    preview += f"  - {att}\n"
            
            # 将文件路径存入输入框（用于解析时使用）
            self.input_text.setPlaceholderText(f"[MSG文件已加载]\n{filepath}")
            self.input_text.setPlainText(filepath)
            
            QMessageBox.information(
                self, "MSG文件预览",
                f"已加载邮件文件:\n{filepath}\n\n"
                f"主题: {email.subject or '无主题'}\n"
                f"发件人: {email.sender or email.sender_email}\n"
                f"时间: {email.date}\n\n"
                f"点击'解析'按钮提取任务信息"
            )
            
        except ImportError as e:
            QMessageBox.critical(
                self, "库未安装", 
                f"{str(e)}\n\n"
                "请在命令行运行:\npip install extract-msg"
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取MSG文件失败：{e}")
            
    def _show_help(self):
        """显示帮助"""
        # 检查MSG库状态
        msg_lib_info = MSGParser.get_library_info()
        msg_status = "已安装" if msg_lib_info['available'] else "未安装"
        
        QMessageBox.information(
            self, "使用帮助",
            "内容导入说明：\n\n"
            "• 文本：直接粘贴或输入文字内容\n"
            "• 图片：导入图片进行OCR识别\n"
            "• 邮件(MSG)：导入Outlook邮件文件\n"
            "  MSG解析库状态：" + msg_status + "\n"
            "• 企业微信：导入聊天记录文件\n\n"
            "导入流程：\n"
            "1. 选择导入方式\n"
            "2. 点击'文件'按钮选择文件\n"
            "3. 点击'解析'提取任务信息\n"
            "4. 在右侧确认并保存任务"
        )
        
    def clear(self):
        """清空输入"""
        self.input_text.clear()
        self.radio_text.setChecked(True)
