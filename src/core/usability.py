"""
用户体验优化模块
提供快捷键、主题、通知等功能
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field

from src.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Shortcut:
    """快捷键定义"""
    key: str
    modifiers: List[str] = field(default_factory=list)
    description: str = ""
    action: Optional[Callable] = None
    
    def to_qt_sequence(self) -> str:
        """转换为Qt快捷键序列"""
        parts = self.modifiers + [self.key]
        return "+".join(parts)


class ShortcutManager:
    """快捷键管理器"""
    
    # 默认快捷键
    DEFAULT_SHORTCUTS: Dict[str, Shortcut] = {
        "new_task": Shortcut(
            key="N",
            modifiers=["Ctrl"],
            description="新建任务"
        ),
        "save": Shortcut(
            key="S",
            modifiers=["Ctrl"],
            description="保存"
        ),
        "search": Shortcut(
            key="F",
            modifiers=["Ctrl"],
            description="搜索"
        ),
        "refresh": Shortcut(
            key="R",
            modifiers=["Ctrl"],
            description="刷新"
        ),
        "export": Shortcut(
            key="E",
            modifiers=["Ctrl", "Shift"],
            description="导出数据"
        ),
        "import": Shortcut(
            key="I",
            modifiers=["Ctrl", "Shift"],
            description="导入数据"
        ),
        "settings": Shortcut(
            key=",",
            modifiers=["Ctrl"],
            description="设置"
        ),
        "help": Shortcut(
            key="F1",
            description="帮助"
        ),
        "quit": Shortcut(
            key="Q",
            modifiers=["Ctrl"],
            description="退出"
        ),
        "delete": Shortcut(
            key="Delete",
            description="删除"
        ),
        "edit": Shortcut(
            key="Enter",
            description="编辑"
        ),
        "escape": Shortcut(
            key="Escape",
            description="取消/关闭"
        ),
    }
    
    def __init__(self):
        self._shortcuts: Dict[str, Shortcut] = self.DEFAULT_SHORTCUTS.copy()
        self._custom_shortcuts: Dict[str, Shortcut] = {}
    
    def get(self, name: str) -> Optional[Shortcut]:
        """获取快捷键"""
        if name in self._custom_shortcuts:
            return self._custom_shortcuts[name]
        return self._shortcuts.get(name)
    
    def set(self, name: str, shortcut: Shortcut):
        """设置快捷键"""
        self._custom_shortcuts[name] = shortcut
        logger.info(f"Shortcut set: {name} = {shortcut.to_qt_sequence()}")
    
    def reset(self, name: str):
        """重置快捷键"""
        if name in self._custom_shortcuts:
            del self._custom_shortcuts[name]
            logger.info(f"Shortcut reset: {name}")
    
    def reset_all(self):
        """重置所有快捷键"""
        self._custom_shortcuts.clear()
        logger.info("All shortcuts reset to defaults")
    
    def get_all(self) -> Dict[str, Shortcut]:
        """获取所有快捷键"""
        result = self._shortcuts.copy()
        result.update(self._custom_shortcuts)
        return result
    
    def export_config(self) -> Dict[str, dict]:
        """导出配置"""
        config = {}
        for name, shortcut in self._custom_shortcuts.items():
            config[name] = {
                "key": shortcut.key,
                "modifiers": shortcut.modifiers,
                "description": shortcut.description,
            }
        return config
    
    def import_config(self, config: Dict[str, dict]):
        """导入配置"""
        for name, data in config.items():
            if name in self.DEFAULT_SHORTCUTS:
                self._custom_shortcuts[name] = Shortcut(
                    key=data.get("key", ""),
                    modifiers=data.get("modifiers", []),
                    description=data.get("description", ""),
                )


class ThemeManager:
    """主题管理器"""
    
    # 内置主题
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
        },
    }
    
    def __init__(self):
        self._current_theme = "light"
        self._custom_themes: Dict[str, Dict] = {}
        self._listeners: List[Callable] = []
    
    def get_theme(self, name: Optional[str] = None) -> Dict:
        """获取主题"""
        theme_name = name or self._current_theme
        
        if theme_name in self._custom_themes:
            return self._custom_themes[theme_name]
        
        return self.THEMES.get(theme_name, self.THEMES["light"])
    
    def set_theme(self, name: str):
        """设置主题"""
        if name not in self.THEMES and name not in self._custom_themes:
            logger.warning(f"Theme not found: {name}")
            return
        
        old_theme = self._current_theme
        self._current_theme = name
        
        if old_theme != name:
            self._notify_listeners()
        
        logger.info(f"Theme changed: {old_theme} -> {name}")
    
    def add_custom_theme(self, name: str, theme: Dict):
        """添加自定义主题"""
        self._custom_themes[name] = theme
        logger.info(f"Custom theme added: {name}")
    
    def remove_custom_theme(self, name: str):
        """移除自定义主题"""
        if name in self._custom_themes:
            del self._custom_themes[name]
            logger.info(f"Custom theme removed: {name}")
    
    def get_current_theme_name(self) -> str:
        """获取当前主题名称"""
        return self._current_theme
    
    def get_all_themes(self) -> Dict[str, Dict]:
        """获取所有主题"""
        return {
            **self.THEMES,
            **self._custom_themes,
        }
    
    def add_listener(self, callback: Callable):
        """添加主题变更监听器"""
        self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable):
        """移除主题变更监听器"""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _notify_listeners(self):
        """通知监听器"""
        theme = self.get_theme()
        for callback in self._listeners:
            try:
                callback(theme)
            except Exception as e:
                logger.error(f"Theme listener error: {e}")


class NotificationManager:
    """通知管理器"""
    
    def __init__(self):
        self._notifications: List[Dict] = []
        self._max_notifications = 100
    
    def add(self, title: str, message: str, level: str = "info"):
        """
        添加通知
        
        Args:
            title: 标题
            message: 消息内容
            level: 级别 (info, success, warning, error)
        """
        notification = {
            "id": len(self._notifications),
            "title": title,
            "message": message,
            "level": level,
            "timestamp": self._get_timestamp(),
            "read": False,
        }
        
        self._notifications.append(notification)
        
        # 保持最大数量
        if len(self._notifications) > self._max_notifications:
            self._notifications.pop(0)
        
        logger.info(f"Notification added: [{level}] {title}")
        return notification["id"]
    
    def get_all(self) -> List[Dict]:
        """获取所有通知"""
        return self._notifications.copy()
    
    def get_unread(self) -> List[Dict]:
        """获取未读通知"""
        return [n for n in self._notifications if not n["read"]]
    
    def mark_read(self, notification_id: int):
        """标记已读"""
        for n in self._notifications:
            if n["id"] == notification_id:
                n["read"] = True
                break
    
    def mark_all_read(self):
        """标记全部已读"""
        for n in self._notifications:
            n["read"] = True
    
    def clear(self):
        """清除所有通知"""
        self._notifications.clear()
    
    def clear_read(self):
        """清除已读通知"""
        self._notifications = [n for n in self._notifications if not n["read"]]
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class StatusBarManager:
    """状态栏管理器"""
    
    def __init__(self):
        self._items: Dict[str, str] = {}
        self._listeners: List[Callable] = []
    
    def set_item(self, key: str, value: str):
        """设置状态项"""
        self._items[key] = value
        self._notify()
    
    def remove_item(self, key: str):
        """移除状态项"""
        if key in self._items:
            del self._items[key]
            self._notify()
    
    def get_status(self) -> str:
        """获取完整状态文本"""
        parts = [v for v in self._items.values() if v]
        return " | ".join(parts)
    
    def add_listener(self, callback: Callable):
        """添加监听器"""
        self._listeners.append(callback)
    
    def _notify(self):
        """通知变更"""
        status = self.get_status()
        for callback in self._listeners:
            try:
                callback(status)
            except Exception as e:
                logger.error(f"StatusBar listener error: {e}")


class ProgressManager:
    """进度管理器"""
    
    def __init__(self):
        self._progress: Dict[str, float] = {}
        self._messages: Dict[str, str] = {}
        self._listeners: List[Callable] = []
    
    def set_progress(self, task_id: str, value: float, message: str = ""):
        """
        设置进度
        
        Args:
            task_id: 任务ID
            value: 进度值 (0-100)
            message: 状态消息
        """
        self._progress[task_id] = max(0, min(100, value))
        if message:
            self._messages[task_id] = message
        self._notify()
    
    def complete(self, task_id: str):
        """标记完成"""
        self._progress[task_id] = 100
        self._notify()
    
    def remove(self, task_id: str):
        """移除进度"""
        if task_id in self._progress:
            del self._progress[task_id]
        if task_id in self._messages:
            del self._messages[task_id]
        self._notify()
    
    def get_progress(self, task_id: str) -> float:
        """获取进度"""
        return self._progress.get(task_id, 0)
    
    def get_all(self) -> Dict[str, Dict]:
        """获取所有进度"""
        return {
            task_id: {
                "progress": self._progress[task_id],
                "message": self._messages.get(task_id, ""),
            }
            for task_id in self._progress
        }
    
    def is_active(self) -> bool:
        """是否有进行中的任务"""
        return any(v < 100 for v in self._progress.values())
    
    def add_listener(self, callback: Callable):
        """添加监听器"""
        self._listeners.append(callback)
    
    def _notify(self):
        """通知变更"""
        for callback in self._listeners:
            try:
                callback(self.get_all())
            except Exception as e:
                logger.error(f"Progress listener error: {e}")
