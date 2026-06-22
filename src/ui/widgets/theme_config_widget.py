# -*- coding: utf-8 -*-
"""
主题配置界面模块
Theme Configuration UI Module

提供主题切换的配置界面
"""

from typing import Dict, Optional

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QComboBox,
    QCheckBox,
    QSlider,
    QScrollArea,
    QFrame,
    QApplication,
)
from PyQt5.QtCore import Qt, pyqtSignal

from ...core.theme_manager import get_theme_manager, ThemeType
from ...utils.logger import get_logger

logger = get_logger(__name__)


class ThemeConfigWidget(QWidget):
    """主题配置界面"""

    theme_changed = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """初始化主题配置界面"""
        super().__init__(parent)
        self.theme_manager = get_theme_manager()
        self._init_ui()
        self._load_current_settings()

    def _init_ui(self) -> None:
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("🎨 主题设置")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1976D2;")
        layout.addWidget(title_label)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(20)

        # 1. 当前主题状态
        scroll_layout.addWidget(self._create_status_group())

        # 2. 主题选择
        scroll_layout.addWidget(self._create_theme_selection_group())

        # 3. 字体设置
        scroll_layout.addWidget(self._create_font_settings_group())

        # 4. 预览区域
        scroll_layout.addWidget(self._create_preview_group())

        # 5. 快捷操作
        scroll_layout.addWidget(self._create_quick_actions_group())

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        layout.addStretch()

    def _create_status_group(self) -> QGroupBox:
        """创建状态显示组"""
        group = QGroupBox("当前状态")
        layout = QVBoxLayout(group)

        # 当前主题
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel("当前主题:"))
        self.current_theme_label = QLabel()
        self.current_theme_label.setStyleSheet("font-weight: bold; color: #1976D2;")
        current_layout.addWidget(self.current_theme_label)
        current_layout.addStretch()
        layout.addLayout(current_layout)

        # 主题类型
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("主题类型:"))
        self.theme_type_label = QLabel()
        self.theme_type_label.setStyleSheet("font-weight: bold;")
        type_layout.addWidget(self.theme_type_label)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # 字体大小
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("字体大小:"))
        self.font_size_label = QLabel()
        self.font_size_label.setStyleSheet("font-weight: bold;")
        font_layout.addWidget(self.font_size_label)
        font_layout.addStretch()
        layout.addLayout(font_layout)

        return group

    def _create_theme_selection_group(self) -> QGroupBox:
        """创建主题选择组"""
        group = QGroupBox("主题选择")
        layout = QVBoxLayout(group)

        # 主题类型选择
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("选择主题:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("浅色主题", "light")
        self.theme_combo.addItem("深色主题", "dark")
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)

        # 主题描述
        desc_label = QLabel("💡 提示: 浅色主题适合白天使用，深色主题适合夜间使用")
        desc_label.setStyleSheet("color: #666; font-size: 12px; padding: 5px;")
        layout.addWidget(desc_label)

        return group

    def _create_font_settings_group(self) -> QGroupBox:
        """创建字体设置组"""
        group = QGroupBox("字体设置")
        layout = QVBoxLayout(group)

        # 字体大小滑块
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("字体大小:"))
        self.font_slider = QSlider(Qt.Horizontal)
        self.font_slider.setMinimum(8)
        self.font_slider.setMaximum(16)
        self.font_slider.setTickPosition(QSlider.TicksBelow)
        self.font_slider.setTickInterval(1)
        self.font_slider.valueChanged.connect(self._on_font_size_changed)
        size_layout.addWidget(self.font_slider)
        self.font_size_value_label = QLabel("10 pt")
        self.font_size_value_label.setStyleSheet("font-weight: bold; min-width: 50px;")
        size_layout.addWidget(self.font_size_value_label)
        layout.addLayout(size_layout)

        # 字体大小预设
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("预设:"))
        for size in [9, 10, 11, 12]:
            btn = QPushButton(f"{size}")
            btn.setObjectName(f"preset_{size}")
            btn.setFixedSize(40, 28)
            btn.clicked.connect(lambda checked, s=size: self._set_font_size(s))
            preset_layout.addWidget(btn)
        preset_layout.addStretch()
        layout.addLayout(preset_layout)

        return group

    def _create_preview_group(self) -> QGroupBox:
        """创建预览组"""
        group = QGroupBox("效果预览")
        layout = QVBoxLayout(group)

        # 预览卡片
        preview_card = QFrame()
        preview_card.setFrameShape(QFrame.StyledPanel)
        preview_card.setObjectName("preview_card")
        card_layout = QVBoxLayout(preview_card)

        # 预览标题
        preview_title = QLabel("预览标题")
        preview_title.setObjectName("preview_title")
        preview_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        card_layout.addWidget(preview_title)

        # 预览内容
        preview_text = QLabel("这是一段预览文字，用于展示不同主题下的显示效果。")
        preview_text.setObjectName("preview_text")
        preview_text.setWordWrap(True)
        card_layout.addWidget(preview_text)

        # 预览按钮
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QPushButton("主要按钮"))
        btn_layout.addWidget(QPushButton("次要按钮"))
        btn_layout.addWidget(QPushButton("危险按钮"))
        btn_layout.addStretch()
        card_layout.addLayout(btn_layout)

        # 预览输入框
        preview_input = QLabel("预览输入框: [                    ]")
        preview_input.setObjectName("preview_input")
        card_layout.addWidget(preview_input)

        layout.addWidget(preview_card)

        return group

    def _create_quick_actions_group(self) -> QGroupBox:
        """创建快捷操作组"""
        group = QGroupBox("快捷操作")
        layout = QHBoxLayout(group)

        # 切换按钮
        self.toggle_btn = QPushButton("🌙 切换到深色主题")
        self.toggle_btn.setObjectName("secondary")
        self.toggle_btn.clicked.connect(self._on_toggle_theme)
        layout.addWidget(self.toggle_btn)

        # 应用按钮
        apply_btn = QPushButton("✅ 应用主题")
        apply_btn.clicked.connect(self._on_apply_theme)
        layout.addWidget(apply_btn)

        # 重置按钮
        reset_btn = QPushButton("🔄 重置")
        reset_btn.setObjectName("secondary")
        reset_btn.clicked.connect(self._on_reset_theme)
        layout.addWidget(reset_btn)

        layout.addStretch()

        return group

    def _load_current_settings(self) -> None:
        """加载当前设置"""
        # 加载主题
        theme_type = self.theme_manager.get_current_theme()
        theme_index = self.theme_combo.findData(theme_type.value)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)

        # 加载字体大小
        font_size = self.theme_manager.get_font_size()
        self.font_slider.setValue(font_size)
        self.font_size_value_label.setText(f"{font_size} pt")

        # 更新状态显示
        self._update_status_display()

    def _update_status_display(self) -> None:
        """更新状态显示"""
        theme_type = self.theme_manager.get_current_theme()

        # 主题名称
        theme_names = {
            "light": "浅色主题",
            "dark": "深色主题",
            "auto": "自动切换"
        }
        self.current_theme_label.setText(theme_names.get(theme_type.value, "未知"))

        # 主题类型
        self.theme_type_label.setText(theme_type.display_name)

        # 字体大小
        self.font_size_label.setText(f"{self.theme_manager.get_font_size()} pt")

        # 更新切换按钮文本
        if theme_type == ThemeType.LIGHT:
            self.toggle_btn.setText("🌙 切换到深色主题")
        else:
            self.toggle_btn.setText("☀️ 切换到浅色主题")

    def _on_theme_changed(self, index: int) -> None:
        """主题改变事件"""
        theme_value = self.theme_combo.itemData(index)
        self._update_status_display()
        logger.info(f"主题选择改变: {theme_value}")

    def _on_font_size_changed(self, value: int) -> None:
        """字体大小改变事件"""
        self.font_size_value_label.setText(f"{value} pt")

    def _set_font_size(self, size: int) -> None:
        """设置字体大小"""
        self.font_slider.setValue(size)
        self.theme_manager.set_font_size(size)
        self._update_status_display()
        logger.info(f"字体大小设置为: {size}")

    def _on_toggle_theme(self) -> None:
        """切换主题按钮点击"""
        self.theme_manager.toggle_theme()

        # 更新UI
        theme_type = self.theme_manager.get_current_theme()
        theme_index = self.theme_combo.findData(theme_type.value)
        if theme_index >= 0:
            self.theme_combo.blockSignals(True)
            self.theme_combo.setCurrentIndex(theme_index)
            self.theme_combo.blockSignals(False)

        self._update_status_display()
        self.theme_changed.emit(theme_type.value)

    def _on_apply_theme(self) -> None:
        """应用主题按钮点击"""
        theme_value = self.theme_combo.currentData()
        theme_type = ThemeType(theme_value)

        self.theme_manager.apply_theme(theme_type)
        self.theme_manager.set_font_size(self.font_slider.value())

        self._update_status_display()
        self.theme_changed.emit(theme_type.value)

        logger.info(f"主题已应用: {theme_value}")

    def _on_reset_theme(self) -> None:
        """重置按钮点击"""
        # 重置为主题
        self.theme_manager.apply_theme(ThemeType.LIGHT)

        # 重置字体大小
        self.theme_manager.set_font_size(10)

        # 更新UI
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentIndex(0)
        self.theme_combo.blockSignals(False)
        self.font_slider.setValue(10)

        self._update_status_display()
        self.theme_changed.emit("light")

        logger.info("主题已重置为默认")

    def refresh_theme(self) -> None:
        """刷新主题"""
        self._load_current_settings()
