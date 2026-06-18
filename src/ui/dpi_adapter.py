# -*- coding: utf-8 -*-
"""
UI适配模块
UI Adaptation Module

提供DPI适配、响应式布局等UI优化功能
"""

import os
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass

from PyQt5.QtCore import QSettings, QSize, Qt, QRect
from PyQt5.QtGui import QFont, QGuiApplication, QIcon
from PyQt5.QtWidgets import QApplication, QWidget

from src.utils.logger import get_logger

logger = get_logger(__name__)


# ==================== DPI适配 ====================

class DPIAdapter:
    """
    DPI适配器
    自动适配不同分辨率和DPI设置
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        
        # 获取系统DPI信息
        self._screen = QGuiApplication.primaryScreen()
        self._dpi = self._get_dpi()
        self._scale_factor = self._calculate_scale_factor()
        
        logger.info(f"DPI适配初始化: DPI={self._dpi}, 缩放因子={self._scale_factor}")
    
    def _get_dpi(self) -> int:
        """获取系统DPI"""
        if self._screen:
            return int(self._screen.logicalDotsPerInch())
        return 96
    
    def _calculate_scale_factor(self) -> float:
        """计算缩放因子"""
        base_dpi = 96
        return self._dpi / base_dpi
    
    def scale(self, value: int) -> int:
        """
        根据DPI缩放数值
        
        Args:
            value: 原始数值
            
        Returns:
            缩放后的数值
        """
        scaled = value * self._scale_factor
        return max(1, int(scaled))
    
    def scale_font_size(self, base_size: int) -> int:
        """
        缩放字体大小
        
        Args:
            base_size: 基础字体大小
            
        Returns:
            缩放后的字体大小
        """
        # 字体缩放更平滑，使用0.8倍因子
        scaled = base_size * (0.8 + 0.2 * self._scale_factor)
        return max(8, min(72, int(scaled)))
    
    def get_font(self, family: str = "Microsoft YaHei", base_size: int = 10) -> QFont:
        """
        获取适配的字体
        
        Args:
            family: 字体家族
            base_size: 基础大小
            
        Returns:
            适配后的字体
        """
        font = QFont(family)
        font.setPointSize(self.scale_font_size(base_size))
        return font
    
    def scale_size(self, width: int, height: int) -> Tuple[int, int]:
        """
        缩放尺寸
        
        Args:
            width: 原始宽度
            height: 原始高度
            
        Returns:
            (缩放后宽度, 缩放后高度)
        """
        return self.scale(width), self.scale(height)
    
    def scale_rect(self, x: int, y: int, width: int, height: int) -> QRect:
        """
        缩放矩形区域
        
        Args:
            x, y: 位置
            width, height: 尺寸
            
        Returns:
            缩放后的QRect
        """
        return QRect(
            self.scale(x),
            self.scale(y),
            self.scale(width),
            self.scale(height)
        )
    
    def get_dpi_info(self) -> Dict[str, Any]:
        """获取DPI信息"""
        return {
            "dpi": self._dpi,
            "scale_factor": round(self._scale_factor, 2),
            "is_high_dpi": self._dpi > 120,
            "is_very_high_dpi": self._dpi > 192,
        }


# ==================== 响应式布局 ====================

class ResponsiveLayout:
    """
    响应式布局管理器
    根据窗口大小自动调整布局
    """
    
    # 断点定义
    BREAKPOINTS = {
        "xs": 480,   # 超小屏幕
        "sm": 768,   # 小屏幕
        "md": 1024,  # 中等屏幕
        "lg": 1280,  # 大屏幕
        "xl": 1920,  # 超大屏幕
    }
    
    def __init__(self):
        self._current_breakpoint = "lg"
        self._listeners: list = []
    
    def get_breakpoint(self, width: int) -> str:
        """
        根据宽度获取断点
        
        Args:
            width: 窗口宽度
            
        Returns:
            断点名称
        """
        if width < self.BREAKPOINTS["xs"]:
            return "xs"
        elif width < self.BREAKPOINTS["sm"]:
            return "sm"
        elif width < self.BREAKPOINTS["md"]:
            return "md"
        elif width < self.BREAKPOINTS["lg"]:
            return "lg"
        else:
            return "xl"
    
    def update_breakpoint(self, width: int):
        """更新断点并通知监听器"""
        new_breakpoint = self.get_breakpoint(width)
        if new_breakpoint != self._current_breakpoint:
            self._current_breakpoint = new_breakpoint
            self._notify_listeners()
    
    def get_column_count(self) -> int:
        """获取列数"""
        counts = {
            "xs": 1,
            "sm": 2,
            "md": 4,
            "lg": 6,
            "xl": 8,
        }
        return counts.get(self._current_breakpoint, 4)
    
    def get_spacing(self) -> int:
        """获取间距"""
        spacings = {
            "xs": 4,
            "sm": 8,
            "md": 12,
            "lg": 16,
            "xl": 20,
        }
        return spacings.get(self._current_breakpoint, 12)
    
    def get_icon_size(self) -> int:
        """获取图标大小"""
        sizes = {
            "xs": 16,
            "sm": 20,
            "md": 24,
            "lg": 32,
            "xl": 48,
        }
        return sizes.get(self._current_breakpoint, 24)
    
    def add_listener(self, callback):
        """添加监听器"""
        self._listeners.append(callback)
    
    def _notify_listeners(self):
        """通知监听器"""
        for callback in self._listeners:
            try:
                callback(self._current_breakpoint)
            except Exception as e:
                logger.error(f"响应式布局监听器错误: {e}")


# ==================== 窗口状态管理 ====================

class WindowStateManager:
    """
    窗口状态管理器
    保存和恢复窗口位置、大小等状态
    """
    
    def __init__(self, app_name: str = "Gitwork"):
        self._settings = QSettings(
            "Gitwork",
            app_name
        )
        self._default_size = QSize(1200, 800)
        self._min_size = QSize(800, 600)
    
    def save_window_state(self, window: QWidget):
        """
        保存窗口状态
        
        Args:
            window: 窗口实例
        """
        try:
            self._settings.beginGroup("WindowState")
            
            # 保存几何信息
            self._settings.setValue("geometry", window.saveGeometry())
            self._settings.setValue("windowState", window.saveState())
            
            # 保存位置和大小
            self._settings.setValue("pos", window.pos())
            self._settings.setValue("size", window.size())
            self._settings.setValue("maximized", window.isMaximized())
            
            self._settings.endGroup()
            self._settings.sync()
            
            logger.debug("窗口状态已保存")
        except Exception as e:
            logger.error(f"保存窗口状态失败: {e}")
    
    def restore_window_state(self, window: QWidget) -> bool:
        """
        恢复窗口状态
        
        Args:
            window: 窗口实例
            
        Returns:
            是否恢复成功
        """
        try:
            self._settings.beginGroup("WindowState")
            
            # 恢复几何信息
            geometry = self._settings.value("geometry")
            if geometry:
                window.restoreGeometry(geometry)
            
            # 恢复位置和大小
            pos = self._settings.value("pos")
            size = self._settings.value("size")
            
            if pos and size:
                window.resize(size)
                window.move(pos)
            
            # 恢复最大化状态
            maximized = self._settings.value("maximized", False, type=bool)
            if maximized:
                window.showMaximized()
            
            self._settings.endGroup()
            
            logger.debug("窗口状态已恢复")
            return True
            
        except Exception as e:
            logger.error(f"恢复窗口状态失败: {e}")
            return False
    
    def save_preference(self, key: str, value: Any):
        """保存用户偏好"""
        self._settings.beginGroup("Preferences")
        self._settings.setValue(key, value)
        self._settings.endGroup()
        self._settings.sync()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """获取用户偏好"""
        self._settings.beginGroup("Preferences")
        value = self._settings.value(key, default)
        self._settings.endGroup()
        return value
    
    def get_default_size(self) -> QSize:
        """获取默认窗口大小"""
        return self._default_size
    
    def get_min_size(self) -> QSize:
        """获取最小窗口大小"""
        return self._min_size


# ==================== 主题适配 ====================

class ThemeAdapter:
    """
    主题适配器
    提供更丰富的主题支持
    """
    
    THEMES = {
        "light": {
            "name": "浅色",
            "background": "#FFFFFF",
            "foreground": "#333333",
            "primary": "#0078D4",
            "secondary": "#F3F3F3",
            "accent": "#005A9E",
            "border": "#E1E1E1",
            "success": "#107C10",
            "warning": "#FFB900",
            "error": "#D13438",
            "font_family": "Microsoft YaHei",
        },
        "dark": {
            "name": "深色",
            "background": "#1E1E1E",
            "foreground": "#CCCCCC",
            "primary": "#0078D4",
            "secondary": "#2D2D2D",
            "accent": "#3794FF",
            "border": "#404040",
            "success": "#6CCB5F",
            "warning": "#FFB900",
            "error": "#F85149",
            "font_family": "Microsoft YaHei",
        },
        "blue": {
            "name": "蓝色",
            "background": "#FFFFFF",
            "foreground": "#1A1A1A",
            "primary": "#0078D4",
            "secondary": "#F5F9FF",
            "accent": "#005A9E",
            "border": "#CCE4F7",
            "success": "#107C10",
            "warning": "#FFB900",
            "error": "#D13438",
            "font_family": "Microsoft YaHei",
        },
        "green": {
            "name": "绿色护眼",
            "background": "#F5F9F5",
            "foreground": "#333333",
            "primary": "#28A745",
            "secondary": "#E8F5E9",
            "accent": "#1B5E20",
            "border": "#C8E6C9",
            "success": "#107C10",
            "warning": "#FFB900",
            "error": "#D13438",
            "font_family": "Microsoft YaHei",
        },
        "sepia": {
            "name": "护眼纸色",
            "background": "#F4ECD8",
            "foreground": "#5B4636",
            "primary": "#8B4513",
            "secondary": "#FAF3E0",
            "accent": "#A0522D",
            "border": "#D4C4A8",
            "success": "#107C10",
            "warning": "#FFB900",
            "error": "#D13438",
            "font_family": "Microsoft YaHei",
        },
    }
    
    def __init__(self):
        self._current_theme = "light"
        self._listeners = []
        self._state_manager = WindowStateManager()
        
        # 从偏好加载主题
        saved_theme = self._state_manager.get_preference("theme", "light")
        if saved_theme in self.THEMES:
            self._current_theme = saved_theme
    
    def get_theme(self, name: Optional[str] = None) -> Dict[str, str]:
        """获取主题"""
        theme_name = name or self._current_theme
        return self.THEMES.get(theme_name, self.THEMES["light"])
    
    def set_theme(self, name: str) -> bool:
        """设置主题"""
        if name not in self.THEMES:
            logger.warning(f"主题不存在: {name}")
            return False
        
        old_theme = self._current_theme
        self._current_theme = name
        
        # 保存偏好
        self._state_manager.save_preference("theme", name)
        
        # 通知监听器
        self._notify_listeners()
        
        logger.info(f"主题切换: {old_theme} -> {name}")
        return True
    
    def get_current_theme_name(self) -> str:
        """获取当前主题名称"""
        return self._current_theme
    
    def get_all_themes(self) -> Dict[str, str]:
        """获取所有主题名称"""
        return {k: v["name"] for k, v in self.THEMES.items()}
    
    def apply_theme_to_widget(self, widget: QWidget):
        """应用主题到控件"""
        theme = self.get_theme()
        
        # 设置样式表
        stylesheet = f"""
            QWidget {{
                background-color: {theme['background']};
                color: {theme['foreground']};
                font-family: {theme['font_family']};
            }}
        """
        
        widget.setStyleSheet(stylesheet)
    
    def add_listener(self, callback):
        """添加主题变更监听器"""
        self._listeners.append(callback)
    
    def _notify_listeners(self):
        """通知监听器"""
        theme = self.get_theme()
        for callback in self._listeners:
            try:
                callback(theme)
            except Exception as e:
                logger.error(f"主题适配器监听器错误: {e}")


# ==================== 快捷键管理 ====================

class ShortcutAdapter:
    """
    快捷键适配器
    管理全局快捷键
    """
    
    DEFAULT_SHORTCUTS = {
        "new_task": ("Ctrl+N", "新建任务"),
        "save": ("Ctrl+S", "保存"),
        "search": ("Ctrl+F", "搜索"),
        "refresh": ("Ctrl+R", "刷新"),
        "export": ("Ctrl+Shift+E", "导出"),
        "import": ("Ctrl+Shift+I", "导入"),
        "settings": ("Ctrl+,", "设置"),
        "help": ("F1", "帮助"),
        "quit": ("Ctrl+Q", "退出"),
        "delete": ("Delete", "删除"),
        "edit": ("Enter", "编辑"),
        "escape": ("Escape", "取消"),
        "copy": ("Ctrl+C", "复制"),
        "paste": ("Ctrl+V", "粘贴"),
        "undo": ("Ctrl+Z", "撤销"),
        "redo": ("Ctrl+Y", "重做"),
    }
    
    def __init__(self):
        self._shortcuts: Dict[str, str] = self.DEFAULT_SHORTCUTS.copy()
        self._state_manager = WindowStateManager()
        
        # 从偏好加载快捷键
        self._load_shortcuts()
    
    def _load_shortcuts(self):
        """加载快捷键配置"""
        saved = self._state_manager.get_preference("shortcuts")
        if saved:
            self._shortcuts.update(saved)
    
    def get_shortcut(self, name: str) -> Optional[str]:
        """获取快捷键"""
        return self._shortcuts.get(name)
    
    def set_shortcut(self, name: str, shortcut: str):
        """设置快捷键"""
        self._shortcuts[name] = shortcut
        self._save_shortcuts()
    
    def _save_shortcuts(self):
        """保存快捷键配置"""
        self._state_manager.save_preference("shortcuts", self._shortcuts)
    
    def reset_shortcut(self, name: str):
        """重置快捷键"""
        if name in self.DEFAULT_SHORTCUTS:
            self._shortcuts[name] = self.DEFAULT_SHORTCUTS[name][0]
            self._save_shortcuts()
    
    def reset_all(self):
        """重置所有快捷键"""
        self._shortcuts = self.DEFAULT_SHORTCUTS.copy()
        self._save_shortcuts()
    
    def get_all_shortcuts(self) -> Dict[str, Tuple[str, str]]:
        """获取所有快捷键"""
        return {
            name: (shortcut, desc)
            for name, (shortcut, desc) in self.DEFAULT_SHORTCUTS.items()
            if name in self._shortcuts
        }


# 全局实例
_dpi_adapter = DPIAdapter()
_responsive_layout = ResponsiveLayout()
_window_state_manager = WindowStateManager()
_theme_adapter = ThemeAdapter()
_shortcut_adapter = ShortcutAdapter()


def get_dpi_adapter() -> DPIAdapter:
    """获取DPI适配器"""
    return _dpi_adapter


def get_responsive_layout() -> ResponsiveLayout:
    """获取响应式布局管理器"""
    return _responsive_layout


def get_window_state_manager() -> WindowStateManager:
    """获取窗口状态管理器"""
    return _window_state_manager


def get_theme_adapter() -> ThemeAdapter:
    """获取主题适配器"""
    return _theme_adapter


def get_shortcut_adapter() -> ShortcutAdapter:
    """获取快捷键适配器"""
    return _shortcut_adapter
