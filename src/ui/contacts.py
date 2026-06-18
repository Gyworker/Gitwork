"""
通讯录管理组件
支持手动输入和OCR扫描两种方式添加联系人
"""

import os
from typing import List, Dict, Any, Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLineEdit, QDialog, QFormLayout, QDialogButtonBox,
    QHeaderView, QMessageBox, QFileDialog, QProgressBar,
    QCheckBox, QGroupBox, QScrollArea, QFrame, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont

from src.core.logger import get_logger
from src.content.image_ocr_processor import get_ocr_processor, OCRResult

logger = get_logger(__name__)


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
        from PyQt5.QtWidgets import QFileDialog
        from src.utils.export_utils import generate_export_filename, ExportPrefix, ExportExtension
        from src.content.excel_import import ExcelExporter
        from src.database.contacts_manager import ContactsManager
        import os

        logger.info("打开通讯录导出对话框")

        # 生成带时间戳的默认文件名
        default_name = generate_export_filename(ExportPrefix.CONTACTS_EXPORT, ExportExtension.EXCEL)

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "导出通讯录",
            default_name,
            "Excel文件 (*.xlsx)"
        )

        if not filepath:
            return

        try:
            # 获取通讯录管理器
            db = ContactsManager()
            exporter = ExcelExporter(db)

            # 导出
            result = exporter.export_all(filepath)

            QMessageBox.information(
                self,
                "导出成功",
                f"通讯录已导出到:\n{result}",
                QMessageBox.Ok
            )
            logger.info(f"通讯录导出成功: {result}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "导出失败",
                f"导出通讯录时出错:\n{str(e)}",
                QMessageBox.Ok
            )
            logger.error(f"通讯录导出失败: {e}")


class ContactEditDialog(QDialog):
    """
    联系人编辑弹窗

    支持两种输入方式：
    1. 手动输入 - 传统的表单输入
    2. OCR扫描 - 从名片/文档图片中自动识别联系人信息
    """

    def __init__(self, parent=None, contact: Dict[str, Any] = None):
        super().__init__(parent)
        self.setWindowTitle("编辑联系人" if contact else "添加联系人")
        self.contact = contact or {}
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # ===== 模式选择标签页 =====
        self._create_mode_selection(main_layout)

        # ===== 手动输入表单区域 =====
        self._create_manual_input_form(main_layout)

        # ===== OCR扫描区域 =====
        self._create_ocr_scan_area(main_layout)

        # ===== 按钮区域 =====
        self._create_buttons(main_layout)

    def _create_mode_selection(self, parent_layout: QVBoxLayout):
        """创建模式选择区域"""
        mode_group = QGroupBox("输入方式")
        mode_layout = QHBoxLayout(mode_group)

        self.mode_manual = QCheckBox("📝 手动输入")
        self.mode_manual.setChecked(True)
        self.mode_manual.stateChanged.connect(self._on_mode_changed)

        self.mode_ocr = QCheckBox("📷 OCR扫描")
        self.mode_ocr.stateChanged.connect(self._on_mode_changed)

        mode_layout.addWidget(self.mode_manual)
        mode_layout.addWidget(self.mode_ocr)
        mode_layout.addStretch()

        parent_layout.addWidget(mode_group)

    def _create_manual_input_form(self, parent_layout: QVBoxLayout):
        """创建手动输入表单"""
        self.form_scroll = QScrollArea()
        self.form_scroll.setWidgetResizable(True)
        self.form_scroll.setFrameShape(QFrame.NoFrame)

        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(12)

        # 姓名
        self.name_edit = QLineEdit()
        self.name_edit.setText(self.contact.get('name', ''))
        self.name_edit.setPlaceholderText("输入姓名")
        form_layout.addRow("姓名 *：", self.name_edit)

        # 工号
        self.employee_id_edit = QLineEdit()
        self.employee_id_edit.setText(self.contact.get('employee_id', ''))
        self.employee_id_edit.setPlaceholderText("输入工号")
        form_layout.addRow("工号：", self.employee_id_edit)

        # 手机号
        self.phone_edit = QLineEdit()
        self.phone_edit.setText(self.contact.get('phone', ''))
        self.phone_edit.setPlaceholderText("输入手机号")
        form_layout.addRow("手机号：", self.phone_edit)

        # 邮箱
        self.email_edit = QLineEdit()
        self.email_edit.setText(self.contact.get('email', ''))
        self.email_edit.setPlaceholderText("输入邮箱")
        form_layout.addRow("邮箱：", self.email_edit)

        # 部门
        self.department_edit = QLineEdit()
        self.department_edit.setText(self.contact.get('department', ''))
        self.department_edit.setPlaceholderText("输入部门")
        form_layout.addRow("部门：", self.department_edit)

        # 职位
        self.position_edit = QLineEdit()
        self.position_edit.setText(self.contact.get('position', ''))
        self.position_edit.setPlaceholderText("输入职位")
        form_layout.addRow("职位：", self.position_edit)

        self.form_scroll.setWidget(form_widget)
        parent_layout.addWidget(self.form_scroll)

    def _create_ocr_scan_area(self, parent_layout: QVBoxLayout):
        """创建OCR扫描区域"""
        self.ocr_group = QGroupBox("📷 OCR扫描名片/文档")
        self.ocr_group.setVisible(False)  # 默认隐藏
        ocr_layout = QVBoxLayout(self.ocr_group)
        ocr_layout.setSpacing(10)

        # 说明文字
        tip_label = QLabel(
            "从名片、宣传册、会议资料等图片中自动识别联系人信息\n"
            "支持的图片格式：PNG, JPG, JPEG, BMP, GIF, TIFF, WebP"
        )
        tip_label.setStyleSheet("color: #666; font-size: 12px;")
        tip_label.setWordWrap(True)
        ocr_layout.addWidget(tip_label)

        # 图片路径选择
        path_layout = QHBoxLayout()
        self.ocr_path_edit = QLineEdit()
        self.ocr_path_edit.setPlaceholderText("选择要识别的图片文件...")
        self.ocr_path_edit.setReadOnly(True)
        path_layout.addWidget(self.ocr_path_edit)

        self.ocr_browse_btn = QPushButton("浏览...")
        self.ocr_browse_btn.clicked.connect(self._on_browse_image)
        path_layout.addWidget(self.ocr_browse_btn)
        ocr_layout.addLayout(path_layout)

        # OCR设置
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("识别语言："))
        self.lang_combo = QPushButton("中文+英文 (chi_sim+eng)")
        self.lang_combo.setEnabled(False)
        settings_layout.addWidget(self.lang_combo)
        settings_layout.addStretch()
        ocr_layout.addLayout(settings_layout)

        # 识别按钮
        self.ocr_scan_btn = QPushButton("🔍 开始OCR识别")
        self.ocr_scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.ocr_scan_btn.clicked.connect(self._on_ocr_scan)
        ocr_layout.addWidget(self.ocr_scan_btn)

        # 进度条
        self.ocr_progress = QProgressBar()
        self.ocr_progress.setVisible(False)
        self.ocr_progress.setTextVisible(True)
        ocr_layout.addWidget(self.ocr_progress)

        # 识别结果预览
        result_label = QLabel("识别结果预览：")
        ocr_layout.addWidget(result_label)

        self.ocr_result_text = QLabel("等待扫描...")
        self.ocr_result_text.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                padding: 10px;
                border-radius: 4px;
                min-height: 60px;
            }
        """)
        self.ocr_result_text.setWordWrap(True)
        self.ocr_result_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        ocr_layout.addWidget(self.ocr_result_text)

        # 应用识别结果按钮
        self.apply_ocr_btn = QPushButton("✓ 应用识别结果")
        self.apply_ocr_btn.setEnabled(False)
        self.apply_ocr_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.apply_ocr_btn.clicked.connect(self._on_apply_ocr_result)
        ocr_layout.addWidget(self.apply_ocr_btn)

        parent_layout.addWidget(self.ocr_group)

    def _create_buttons(self, parent_layout: QVBoxLayout):
        """创建底部按钮"""
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        parent_layout.addWidget(buttons)

    def _on_mode_changed(self, state):
        """切换输入模式"""
        sender = self.sender()

        # 取消其他选中
        if sender == self.mode_manual and state:
            self.mode_ocr.setChecked(False)
            self.form_scroll.setVisible(True)
            self.ocr_group.setVisible(False)
        elif sender == self.mode_ocr and state:
            self.mode_manual.setChecked(False)
            self.form_scroll.setVisible(False)
            self.ocr_group.setVisible(True)

        # 至少选中一个
        if not self.mode_manual.isChecked() and not self.mode_ocr.isChecked():
            self.mode_manual.setChecked(True)
            self.form_scroll.setVisible(True)
            self.ocr_group.setVisible(False)

    def _on_browse_image(self):
        """浏览选择图片"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "选择要OCR识别的图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp);;所有文件 (*.*)"
        )

        if filepath:
            self.ocr_path_edit.setText(filepath)
            self.ocr_scan_btn.setEnabled(True)
            self.ocr_result_text.setText("已选择图片，点击「开始OCR识别」按钮进行识别")
            self.apply_ocr_btn.setEnabled(False)
            self._last_ocr_result = None

    def _on_ocr_scan(self):
        """执行OCR扫描"""
        filepath = self.ocr_path_edit.text().strip()

        if not filepath:
            QMessageBox.warning(self, "提示", "请先选择要识别的图片文件！")
            return

        if not os.path.exists(filepath):
            QMessageBox.warning(self, "提示", "选择的图片文件不存在！")
            return

        # 禁用扫描按钮，显示进度
        self.ocr_scan_btn.setEnabled(False)
        self.ocr_scan_btn.setText("🔄 识别中...")
        self.ocr_progress.setVisible(True)
        self.ocr_progress.setRange(0, 0)  # 不确定进度
        QApplication.processEvents()

        try:
            # 执行OCR识别
            ocr = get_ocr_processor()

            if not ocr.is_available:
                self.ocr_result_text.setText(
                    "<span style='color: red;'>❌ OCR库不可用</span><br>"
                    "请先安装OCR依赖：<br>"
                    "pip install pytesseract pillow<br>"
                    "并下载Tesseract引擎"
                )
                return

            # 执行识别
            result = ocr.process_image(filepath)
            self._last_ocr_result = result

            # 更新UI
            if result.success:
                self._display_ocr_result(result)
                self.apply_ocr_btn.setEnabled(True)
            else:
                self.ocr_result_text.setText(
                    f"<span style='color: red;'>❌ 识别失败</span><br>"
                    f"错误：{result.error or '未知错误'}<br>"
                    f"详情：{result.error_details or '无'}"
                )
                self.apply_ocr_btn.setEnabled(False)

        except Exception as e:
            logger.error(f"OCR扫描异常: {e}")
            self.ocr_result_text.setText(
                f"<span style='color: red;'>❌ OCR扫描异常</span><br>"
                f"错误信息：{str(e)}"
            )
            self.apply_ocr_btn.setEnabled(False)

        finally:
            # 恢复UI状态
            self.ocr_scan_btn.setEnabled(True)
            self.ocr_scan_btn.setText("🔍 开始OCR识别")
            self.ocr_progress.setVisible(False)

    def _display_ocr_result(self, result: OCRResult):
        """显示OCR识别结果"""
        info = result.contact_info

        preview_lines = []
        preview_lines.append("<div style='font-family: monospace;'>")
        preview_lines.append("<b>✅ 识别成功</b><br>")
        preview_lines.append(f"识别耗时：{result.process_time_ms:.2f}ms<br>")
        preview_lines.append("<hr>")

        if info and (info.name or info.phone or info.email):
            preview_lines.append("<b>📋 提取的联系人信息：</b><br>")
            if info.name:
                preview_lines.append(f"&nbsp;&nbsp;👤 姓名：{info.name}<br>")
            if info.phone:
                preview_lines.append(f"&nbsp;&nbsp;📞 电话：{info.phone}<br>")
            if info.email:
                preview_lines.append(f"&nbsp;&nbsp;✉️ 邮箱：{info.email}<br>")
            if info.company:
                preview_lines.append(f"&nbsp;&nbsp;🏢 公司：{info.company}<br>")
            if info.department:
                preview_lines.append(f"&nbsp;&nbsp;📁 部门：{info.department}<br>")
            if info.position:
                preview_lines.append(f"&nbsp;&nbsp;💼 职位：{info.position}<br>")
            if info.confidence > 0:
                preview_lines.append(f"<br>&nbsp;&nbsp;📊 识别置信度：<b>{info.confidence:.0%}</b><br>")
        else:
            preview_lines.append("<b>⚠️ 未提取到联系人信息</b><br>")
            preview_lines.append("请检查图片是否清晰，或手动输入联系人信息。<br>")

        if result.raw_text:
            preview_lines.append("<hr>")
            preview_lines.append("<b>📄 原始识别文本：</b><br>")
            # 截断过长的文本
            raw_display = result.raw_text[:500] + ('...' if len(result.raw_text) > 500 else '')
            preview_lines.append(f"<pre style='font-size: 11px;'>{raw_display}</pre>")

        preview_lines.append("</div>")

        self.ocr_result_text.setText('\n'.join(preview_lines))

    def _on_apply_ocr_result(self):
        """应用OCR识别结果到表单"""
        if not self._last_ocr_result or not self._last_ocr_result.success:
            QMessageBox.warning(self, "提示", "没有可应用的识别结果！")
            return

        info = self._last_ocr_result.contact_info
        if not info:
            QMessageBox.warning(self, "提示", "识别结果中没有联系人信息！")
            return

        # 切换到手动模式并填充数据
        self.mode_manual.setChecked(True)
        self.mode_ocr.setChecked(False)
        self.form_scroll.setVisible(True)
        self.ocr_group.setVisible(False)

        # 填充表单字段
        if info.name:
            self.name_edit.setText(info.name)
        if info.phone:
            self.phone_edit.setText(info.phone)
        if info.email:
            self.email_edit.setText(info.email)
        if info.department:
            self.department_edit.setText(info.department)
        if info.position:
            self.position_edit.setText(info.position)

        # 切换焦点到姓名输入框
        self.name_edit.setFocus()

        QMessageBox.information(
            self,
            "应用成功",
            f"已成功将OCR识别结果填充到表单！\n\n"
            f"请核对识别结果是否正确，\n"
            f"如有误差请手动修改。"
        )

    def _on_save(self):
        """保存前验证"""
        # 切换到手动模式并验证
        if not self.mode_manual.isChecked():
            self.mode_manual.setChecked(True)
            self.mode_ocr.setChecked(False)

        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "验证失败", "姓名不能为空！")
            self.name_edit.setFocus()
            return

        self.accept()

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
