# -*- coding: utf-8 -*-
"""
主题管理服务模块
Theme Management Service Module

提供应用主题的加载、切换和管理功能
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional
from enum import Enum

from PyQt5.QtWidgets import QApplication

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ThemeType(Enum):
    """主题类型枚举"""
    LIGHT = "light"      # 浅色主题
    DARK = "dark"        # 深色主题
    AUTO = "auto"        # 自动（跟随系统）

    @property
    def display_name(self) -> str:
        """获取显示名称"""
        names = {
            "light": "浅色主题",
            "dark": "深色主题",
            "auto": "自动切换"
        }
        return names.get(self.value, self.value)


class ThemeColors:
    """主题颜色配置"""

    # 浅色主题颜色
    LIGHT = {
        # 主色
        "primary": "#1976D2",
        "primary_dark": "#1565C0",
        "primary_light": "#42A5F5",
        "accent": "#FF5722",

        # 背景色
        "bg_main": "#FFFFFF",
        "bg_secondary": "#F5F5F5",
        "bg_tertiary": "#EEEEEE",
        "bg_card": "#FFFFFF",

        # 文字颜色
        "text_primary": "#212121",
        "text_secondary": "#757575",
        "text_disabled": "#BDBDBD",
        "text_on_primary": "#FFFFFF",

        # 边框颜色
        "border": "#E0E0E0",
        "border_focus": "#1976D2",

        # 状态颜色
        "success": "#4CAF50",
        "warning": "#FF9800",
        "error": "#F44336",
        "info": "#2196F3",

        # 导航栏
        "nav_bg": "#FAFAFA",
        "nav_item_hover": "#E3F2FD",
        "nav_item_selected": "#BBDEFB",
        "nav_item_text": "#424242",

        # 表格
        "table_header": "#F5F5F5",
        "table_row_odd": "#FFFFFF",
        "table_row_even": "#FAFAFA",
        "table_row_hover": "#E3F2FD",

        # 按钮
        "btn_primary_bg": "#1976D2",
        "btn_primary_text": "#FFFFFF",
        "btn_secondary_bg": "#F5F5F5",
        "btn_secondary_text": "#424242",

        # 输入框
        "input_bg": "#FFFFFF",
        "input_border": "#E0E0E0",
        "input_focus_border": "#1976D2",

        # 分割线
        "divider": "#E0E0E0",

        # 图标
        "icon": "#757575",
        "icon_hover": "#424242",
    }

    # 深色主题颜色
    DARK = {
        # 主色
        "primary": "#90CAF9",
        "primary_dark": "#64B5F6",
        "primary_light": "#BBDEFB",
        "accent": "#FF7043",

        # 背景色
        "bg_main": "#121212",
        "bg_secondary": "#1E1E1E",
        "bg_tertiary": "#2D2D2D",
        "bg_card": "#1E1E1E",

        # 文字颜色
        "text_primary": "#FFFFFF",
        "text_secondary": "#B0B0B0",
        "text_disabled": "#666666",
        "text_on_primary": "#000000",

        # 边框颜色
        "border": "#424242",
        "border_focus": "#90CAF9",

        # 状态颜色
        "success": "#81C784",
        "warning": "#FFB74D",
        "error": "#E57373",
        "info": "#64B5F6",

        # 导航栏
        "nav_bg": "#1E1E1E",
        "nav_item_hover": "#2D3A4A",
        "nav_item_selected": "#37474F",
        "nav_item_text": "#E0E0E0",

        # 表格
        "table_header": "#2D2D2D",
        "table_row_odd": "#1E1E1E",
        "table_row_even": "#252525",
        "table_row_hover": "#2D3A4A",

        # 按钮
        "btn_primary_bg": "#90CAF9",
        "btn_primary_text": "#000000",
        "btn_secondary_bg": "#424242",
        "btn_secondary_text": "#E0E0E0",

        # 输入框
        "input_bg": "#2D2D2D",
        "input_border": "#424242",
        "input_focus_border": "#90CAF9",

        # 分割线
        "divider": "#424242",

        # 图标
        "icon": "#B0B0B0",
        "icon_hover": "#E0E0E0",
    }


class ThemeConfig:
    """主题配置管理"""

    DEFAULT_CONFIG = {
        "theme_type": "light",           # 主题类型
        "font_size": 10,                  # 字体大小
        "font_family": "Microsoft YaHei",  # 字体
        "window_opacity": 1.0,           # 窗口透明度
        "animations_enabled": True,       # 动画开关
    }

    def __init__(self) -> None:
        """初始化配置"""
        self.config_dir = Path(__file__).parent.parent.parent.parent / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "theme_config.json"
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    merged = self.DEFAULT_CONFIG.copy()
                    merged.update(config)
                    return merged
            except Exception as e:
                logger.error(f"加载主题配置失败: {e}")
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()

    def save(self) -> bool:
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"保存主题配置失败: {e}")
            return False

    def get(self, key: str, default=None):
        """获取配置值"""
        return self.config.get(key, default)

    def set(self, key: str, value) -> None:
        """设置配置值"""
        self.config[key] = value
        self.save()

    @property
    def theme_type(self) -> ThemeType:
        """获取主题类型"""
        theme_str = self.config.get("theme_type", "light")
        try:
            return ThemeType(theme_str)
        except ValueError:
            return ThemeType.LIGHT


class ThemeManager:
    """主题管理器（单例模式）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            try:
                cls._instance = super().__new__(cls)
            except MemoryError:
                logger.error("内存不足，无法创建主题管理器实例")
                raise
            except Exception as e:
                logger.warning(f"创建主题管理器实例时出现异常: {e}")
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化主题管理器"""
        if not hasattr(self, '_initialized'):
            self.config = ThemeConfig()
            self.current_theme = self.config.theme_type
            self.colors = self._get_colors()
            self._initialized = True
            logger.info(f"主题管理器初始化，主题: {self.current_theme.value}")

    def _get_colors(self) -> Dict:
        """获取当前主题颜色"""
        if self.current_theme == ThemeType.DARK:
            return ThemeColors.DARK
        else:
            return ThemeColors.LIGHT

    def apply_theme(self, theme_type: ThemeType) -> None:
        """应用主题"""
        if theme_type == self.current_theme:
            return

        self.current_theme = theme_type
        self.config.set("theme_type", theme_type.value)
        self.colors = self._get_colors()

        # 应用到QApplication
        app = QApplication.instance()
        if app:
            app.setStyleSheet(self.generate_stylesheet())

        logger.info(f"主题已切换: {theme_type.value}")

    def generate_stylesheet(self) -> str:
        """生成完整的QSS样式表"""
        colors = self.colors
        font_size = self.config.get("font_size", 10)
        font_family = self.config.get("font_family", "Microsoft YaHei")

        return f"""
        /* 全局样式 */
        * {{
            font-family: "{font_family}", Arial, sans-serif;
            font-size: {font_size}pt;
        }}

        QMainWindow {{
            background-color: {colors['bg_main']};
            color: {colors['text_primary']};
        }}

        QWidget {{
            background-color: {colors['bg_main']};
            color: {colors['text_primary']};
        }}

        /* 标签 */
        QLabel {{
            color: {colors['text_primary']};
            background-color: transparent;
        }}

        /* 按钮 */
        QPushButton {{
            background-color: {colors['btn_primary_bg']};
            color: {colors['btn_primary_text']};
            border: none;
            padding: 6px 16px;
            border-radius: 4px;
            min-width: 70px;
        }}

        QPushButton:hover {{
            background-color: {colors['primary_dark']};
        }}

        QPushButton:pressed {{
            background-color: {colors['primary_dark']};
        }}

        QPushButton:disabled {{
            background-color: {colors['bg_tertiary']};
            color: {colors['text_disabled']};
        }}

        QPushButton#secondary {{
            background-color: {colors['btn_secondary_bg']};
            color: {colors['btn_secondary_text']};
        }}

        /* 输入框 */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {colors['input_bg']};
            color: {colors['text_primary']};
            border: 1px solid {colors['input_border']};
            border-radius: 4px;
            padding: 4px 8px;
            selection-background-color: {colors['primary']};
            selection-color: {colors['text_on_primary']};
        }}

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 2px solid {colors['input_focus_border']};
        }}

        /* 组合框 */
        QComboBox {{
            background-color: {colors['input_bg']};
            color: {colors['text_primary']};
            border: 1px solid {colors['input_border']};
            border-radius: 4px;
            padding: 4px 8px;
        }}

        QComboBox:hover {{
            border-color: {colors['border_focus']};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}

        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {colors['text_secondary']};
        }}

        QComboBox QAbstractItemView {{
            background-color: {colors['bg_card']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            selection-background-color: {colors['primary']};
            selection-color: {colors['text_on_primary']};
        }}

        /* 表格 */
        QTableWidget, QTableView {{
            background-color: {colors['bg_main']};
            alternate-background-color: {colors['table_row_even']};
            color: {colors['text_primary']};
            gridline-color: {colors['border']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
        }}

        QTableWidget::item, QTableView::item {{
            background-color: {colors['table_row_odd']};
            padding: 4px;
        }}

        QTableWidget::item:selected, QTableView::item:selected {{
            background-color: {colors['primary']};
            color: {colors['text_on_primary']};
        }}

        QHeaderView::section {{
            background-color: {colors['table_header']};
            color: {colors['text_primary']};
            padding: 6px;
            border: none;
            border-bottom: 2px solid {colors['primary']};
            font-weight: bold;
        }}

        /* 列表 */
        QListWidget {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_primary']};
            border: none;
            outline: none;
        }}

        QListWidget::item {{
            padding: 8px 12px;
            border-radius: 4px;
            margin: 2px 4px;
        }}

        QListWidget::item:hover {{
            background-color: {colors['nav_item_hover']};
        }}

        QListWidget::item:selected {{
            background-color: {colors['nav_item_selected']};
            color: {colors['text_primary']};
        }}

        /* 滚动条 */
        QScrollBar:vertical {{
            background-color: {colors['bg_secondary']};
            width: 12px;
            border-radius: 6px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {colors['border']};
            border-radius: 6px;
            min-height: 30px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {colors['text_secondary']};
        }}

        QScrollBar:horizontal {{
            background-color: {colors['bg_secondary']};
            height: 12px;
            border-radius: 6px;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {colors['border']};
            border-radius: 6px;
            min-width: 30px;
        }}

        /* 工具栏 */
        QToolBar {{
            background-color: {colors['bg_secondary']};
            border: none;
            spacing: 4px;
            padding: 4px;
        }}

        /* 菜单 */
        QMenuBar {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_primary']};
            border-bottom: 1px solid {colors['border']};
        }}

        QMenuBar::item:selected {{
            background-color: {colors['nav_item_hover']};
        }}

        QMenu {{
            background-color: {colors['bg_card']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
        }}

        QMenu::item {{
            padding: 6px 24px;
        }}

        QMenu::item:selected {{
            background-color: {colors['primary']};
            color: {colors['text_on_primary']};
        }}

        /* 分组框 */
        QGroupBox {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            margin-top: 12px;
            padding-top: 12px;
            font-weight: bold;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            color: {colors['primary']};
        }}

        /* 选项卡 */
        QTabWidget::pane {{
            background-color: {colors['bg_secondary']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
        }}

        QTabBar::tab {{
            background-color: {colors['bg_tertiary']};
            color: {colors['text_secondary']};
            padding: 8px 16px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}

        QTabBar::tab:selected {{
            background-color: {colors['bg_secondary']};
            color: {colors['primary']};
            font-weight: bold;
        }}

        QTabBar::tab:hover {{
            background-color: {colors['nav_item_hover']};
        }}

        /* 工具提示 */
        QToolTip {{
            background-color: {colors['bg_card']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            padding: 4px;
        }}

        /* 复选框 */
        QCheckBox {{
            color: {colors['text_primary']};
            spacing: 8px;
        }}

        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {colors['border']};
            border-radius: 3px;
            background-color: {colors['input_bg']};
        }}

        QCheckBox::indicator:checked {{
            background-color: {colors['primary']};
            border-color: {colors['primary']};
        }}

        QCheckBox::indicator:hover {{
            border-color: {colors['primary']};
        }}

        /* 单选按钮 */
        QRadioButton {{
            color: {colors['text_primary']};
            spacing: 8px;
        }}

        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {colors['border']};
            border-radius: 9px;
            background-color: {colors['input_bg']};
        }}

        QRadioButton::indicator:checked {{
            background-color: {colors['primary']};
            border-color: {colors['primary']};
        }}

        /* 状态栏 */
        QStatusBar {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_secondary']};
            border-top: 1px solid {colors['border']};
        }}

        /* 滑块 */
        QSlider::groove:horizontal {{
            border: 1px solid {colors['border']};
            height: 6px;
            background-color: {colors['bg_tertiary']};
            border-radius: 3px;
        }}

        QSlider::handle:horizontal {{
            background-color: {colors['primary']};
            width: 14px;
            margin: -4px 0;
            border-radius: 7px;
        }}

        /* 进度条 */
        QProgressBar {{
            background-color: {colors['bg_tertiary']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            text-align: center;
        }}

        QProgressBar::chunk {{
            background-color: {colors['primary']};
            border-radius: 4px;
        }}

        /* 分割器 */
        QSplitter::handle {{
            background-color: {colors['border']};
        }}

        QSplitter::handle:horizontal {{
            width: 2px;
        }}

        QSplitter::handle:vertical {{
            height: 2px;
        }}

        /* 卡片样式 */
        .card {{
            background-color: {colors['bg_card']};
            border: 1px solid {colors['border']};
            border-radius: 8px;
            padding: 12px;
        }}

        /* 标题样式 */
        .title {{
            color: {colors['text_primary']};
            font-size: 18px;
            font-weight: bold;
        }}

        /* 次要文字 */
        .secondary-text {{
            color: {colors['text_secondary']};
            font-size: 12px;
        }}

        /* 状态指示 */
        .status-success {{ color: {colors['success']}; }}
        .status-warning {{ color: {colors['warning']}; }}
        .status-error {{ color: {colors['error']}; }}
        .status-info {{ color: {colors['info']}; }}
        """

    def toggle_theme(self) -> None:
        """切换主题"""
        if self.current_theme == ThemeType.LIGHT:
            new_theme = ThemeType.DARK
        else:
            new_theme = ThemeType.LIGHT

        self.apply_theme(new_theme)

    def get_current_theme(self) -> ThemeType:
        """获取当前主题"""
        return self.current_theme

    def get_colors(self) -> Dict:
        """获取当前主题颜色"""
        return self.colors.copy()

    def set_font_size(self, size: int) -> None:
        """设置字体大小"""
        self.config.set("font_size", size)
        self.apply_theme(self.current_theme)

    def get_font_size(self) -> int:
        """获取字体大小"""
        return self.config.get("font_size", 10)


# 全局获取函数
_theme_manager_instance = None

def get_theme_manager() -> ThemeManager:
    """获取主题管理器单例"""
    global _theme_manager_instance
    if _theme_manager_instance is None:
        _theme_manager_instance = ThemeManager()
    return _theme_manager_instance
