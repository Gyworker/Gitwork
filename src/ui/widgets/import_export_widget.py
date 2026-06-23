# -*- coding: utf-8 -*-
"""
数据导入导出模块
Data Import/Export Module

V2.1更新：
1. 将MSG邮件导入融合到内容导入，作为导入方式的一种
2. 导入方式顺序：文本粘贴 -> 图片导入 -> Outlook邮件 -> MSG文件 -> 企业微信
3. Outlook移到最右边作为最后一种方式
"""

from typing import Optional
import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QGroupBox,
    QRadioButton,
    QButtonGroup,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QCheckBox,
)
from PyQt5.QtGui import QFont

from utils.logger import get_logger

logger = get_logger(__name__)


class ImportExportWidget(QWidget):
    """
    数据导入导出组件

    V2.1更新：整合MSG邮件导入功能
    """

    import_completed = pyqtSignal(int)  # 导入完成信号，参数为导入数量

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """初始化导入导出组件"""
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化UI - V2.1更新"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title = QLabel("📥 内容导入")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # 导入方式选择区域 - V2.1更新：MSG融合到导入方式，Outlook移到最右边
        import_group = QGroupBox("导入方式")
        import_layout = QVBoxLayout(import_group)

        # 导入方式单选按钮组
        self.import_method_group = QButtonGroup()

        # 第一行：文本粘贴、图片导入、Outlook邮件（最后）
        row1_layout = QHBoxLayout()

        self.radio_text = QRadioButton("📝 文本粘贴")
        self.radio_text.setChecked(True)
        self.radio_text.toggled.connect(lambda: self._on_method_changed("text"))
        self.import_method_group.addButton(self.radio_text, 1)
        row1_layout.addWidget(self.radio_text)

        self.radio_image = QRadioButton("🖼️ 图片导入")
        self.radio_image.toggled.connect(lambda: self._on_method_changed("image"))
        self.import_method_group.addButton(self.radio_image, 2)
        row1_layout.addWidget(self.radio_image)

        self.radio_outlook = QRadioButton("📧 Outlook邮件")
        self.radio_outlook.toggled.connect(lambda: self._on_method_changed("outlook"))
        self.import_method_group.addButton(self.radio_outlook, 4)
        row1_layout.addWidget(self.radio_outlook)  # V2.1：Outlook移到最右边

        row1_layout.addStretch()
        import_layout.addLayout(row1_layout)

        # 第二行：MSG文件（V2.1新增）、企业微信
        row2_layout = QHBoxLayout()

        self.radio_msg = QRadioButton("📨 MSG邮件文件")  # V2.1：MSG作为导入方式之一
        self.radio_msg.toggled.connect(lambda: self._on_method_changed("msg"))
        self.import_method_group.addButton(self.radio_msg, 3)
        row2_layout.addWidget(self.radio_msg)

        self.radio_wecom = QRadioButton("💬 企业微信")
        self.radio_wecom.toggled.connect(lambda: self._on_method_changed("wecom"))
        self.import_method_group.addButton(self.radio_wecom, 5)
        row2_layout.addWidget(self.radio_wecom)

        row2_layout.addStretch()
        import_layout.addLayout(row2_layout)

        layout.addWidget(import_group)

        # 导入内容区域
        content_group = QGroupBox("导入内容")
        content_layout = QVBoxLayout(content_group)

        # 文本输入区域
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("请输入或粘贴需要导入的任务内容...")
        self.text_input.setMaximumHeight(150)
        content_layout.addWidget(self.text_input)

        # 图片导入区域
        self.image_input_widget = QWidget()
        self.image_input_layout = QVBoxLayout(self.image_input_widget)
        self.image_input_layout.setContentsMargins(0, 0, 0, 0)

        image_select_layout = QHBoxLayout()
        self.image_path_label = QLabel("未选择图片")
        image_select_btn = QPushButton("📂 选择图片")
        image_select_btn.clicked.connect(self._on_select_image)
        image_select_layout.addWidget(self.image_path_label)
        image_select_layout.addWidget(image_select_btn)
        self.image_input_layout.addLayout(image_select_layout)

        self.image_preview = QLabel("[图片预览区]")
        self.image_preview.setMinimumHeight(80)
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.image_preview.setStyleSheet("border: 1px solid #ccc; background: #f5f5f5;")
        self.image_input_layout.addWidget(self.image_preview)
        self.image_input_widget.hide()  # 默认隐藏

        content_layout.addWidget(self.image_input_widget)

        # MSG文件导入区域 - V2.1新增
        self.msg_input_widget = QWidget()
        self.msg_input_layout = QVBoxLayout(self.msg_input_widget)
        self.msg_input_layout.setContentsMargins(0, 0, 0, 0)

        # MSG拖拽区域
        msg_drag_layout = QHBoxLayout()
        self.msg_file_label = QLabel("📨 未选择MSG文件")
        msg_select_btn = QPushButton("📂 选择MSG文件")
        msg_select_btn.clicked.connect(self._on_select_msg)
        msg_drag_layout.addWidget(self.msg_file_label)
        msg_drag_layout.addWidget(msg_select_btn)
        self.msg_input_layout.addLayout(msg_drag_layout)

        # MSG文件列表
        self.msg_file_list = QLabel("[已选择的MSG文件列表]")
        self.msg_file_list.setStyleSheet("border: 1px solid #ccc; padding: 10px; background: #f9f9f9;")
        self.msg_input_layout.addWidget(self.msg_file_list)

        self.msg_input_widget.hide()  # 默认隐藏
        content_layout.addWidget(self.msg_input_widget)

        # Outlook导入区域
        self.outlook_input_widget = QWidget()
        self.outlook_input_layout = QVBoxLayout(self.outlook_input_widget)
        self.outlook_input_layout.setContentsMargins(0, 0, 0, 0)

        outlook_info = QLabel("📧 将从Outlook中读取选定的邮件内容")
        self.outlook_input_layout.addWidget(outlook_info)

        outlook_btn = QPushButton("📥 连接Outlook获取邮件")
        outlook_btn.clicked.connect(self._on_connect_outlook)
        self.outlook_input_layout.addWidget(outlook_btn)

        self.outlook_input_widget.hide()  # 默认隐藏
        content_layout.addWidget(self.outlook_input_widget)

        # 企业微信区域
        self.wecom_input_widget = QWidget()
        self.wecom_input_layout = QVBoxLayout(self.wecom_input_widget)
        self.wecom_input_layout.setContentsMargins(0, 0, 0, 0)

        wecom_info = QLabel("💬 支持企业微信聊天记录导入和截图OCR识别")
        self.wecom_input_layout.addWidget(wecom_info)

        self.wecom_input_layout.addWidget(QLabel("[企业微信导入功能]"))
        self.wecom_input_widget.hide()  # 默认隐藏
        content_layout.addWidget(self.wecom_input_widget)

        layout.addWidget(content_group)

        # 导入选项
        options_group = QGroupBox("导入选项")
        options_layout = QHBoxLayout(options_group)

        self.auto_parse_check = QCheckBox("自动解析内容")
        self.auto_parse_check.setChecked(True)
        options_layout.addWidget(self.auto_parse_check)

        self.auto_fill_check = QCheckBox("自动填充信息")
        self.auto_fill_check.setChecked(True)
        options_layout.addWidget(self.auto_fill_check)

        options_layout.addStretch()
        layout.addWidget(options_group)

        # 按钮区域
        btn_layout = QHBoxLayout()

        self.import_btn = QPushButton("📥 开始导入")
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        self.import_btn.clicked.connect(self._on_import)
        btn_layout.addWidget(self.import_btn)

        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.clicked.connect(self._on_clear)
        btn_layout.addWidget(clear_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)  # V2.1修复：使用addLayout代替addWidget

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        layout.addStretch()

    def _on_method_changed(self, method: str) -> None:
        """导入方式切换"""
        # 隐藏所有输入区域
        self.text_input.hide()
        self.image_input_widget.hide()
        self.msg_input_widget.hide()
        self.outlook_input_widget.hide()
        self.wecom_input_widget.hide()

        # 显示对应的输入区域
        if method == "text":
            self.text_input.show()
        elif method == "image":
            self.image_input_widget.show()
        elif method == "msg":
            self.msg_input_widget.show()  # V2.1：显示MSG区域
        elif method == "outlook":
            self.outlook_input_widget.show()
        elif method == "wecom":
            self.wecom_input_widget.show()

        logger.info(f"切换导入方式: {method}")

    def _on_select_image(self) -> None:
        """选择图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*)"
        )

        if file_path:
            self.image_path_label.setText(f"📷 {os.path.basename(file_path)}")
            logger.info(f"选择图片: {file_path}")

    def _on_select_msg(self) -> None:
        """V2.1新增：选择MSG文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择MSG邮件文件",
            "",
            "MSG邮件文件 (*.msg);;所有文件 (*)"
        )

        if file_paths:
            self.msg_file_label.setText(f"📨 已选择 {len(file_paths)} 个MSG文件")
            file_list_text = "\n".join([f"• {os.path.basename(p)}" for p in file_paths])
            self.msg_file_list.setText(file_list_text)
            logger.info(f"选择MSG文件: {file_paths}")

    def _on_connect_outlook(self) -> None:
        """连接Outlook"""
        QMessageBox.information(
            self,
            "Outlook连接",
            "正在连接Outlook...\n\n（需要Outlook客户端已安装并登录）"
        )

    def _on_import(self) -> None:
        """开始导入"""
        method_id = self.import_method_group.checkedId()

        if method_id == 1:  # 文本
            content = self.text_input.toPlainText().strip()
            if not content:
                QMessageBox.warning(self, "导入失败", "请输入要导入的内容")
                return
        elif method_id == 2:  # 图片
            if self.image_path_label.text() == "未选择图片":
                QMessageBox.warning(self, "导入失败", "请先选择图片")
                return
        elif method_id == 3:  # MSG - V2.1
            if self.msg_file_label.text() == "📨 未选择MSG文件":
                QMessageBox.warning(self, "导入失败", "请先选择MSG文件")
                return
        elif method_id == 4:  # Outlook
            QMessageBox.information(self, "导入", "正在从Outlook导入...")
        elif method_id == 5:  # 企业微信
            QMessageBox.information(self, "导入", "正在从企业微信导入...")

        # 模拟导入
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        for i in range(101):
            self.progress_bar.setValue(i)
            QApplication.processEvents()

        self.progress_bar.setVisible(False)

        QMessageBox.information(self, "导入成功", "数据导入成功！")
        self.import_completed.emit(1)
        logger.info("导入完成")

    def _on_clear(self) -> None:
        """清空内容"""
        self.text_input.clear()
        self.image_path_label.setText("未选择图片")
        self.msg_file_label.setText("📨 未选择MSG文件")
        self.msg_file_list.setText("[已选择的MSG文件列表]")
        logger.info("清空导入内容")


# 添加缺失的导入
from PyQt5.QtWidgets import QApplication
