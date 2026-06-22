# -*- coding: utf-8 -*-
"""
主窗口模块
Main Window Module

负责应用程序的主窗口界面
"""

from typing import Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QLabel,
    QPushButton,
    QStatusBar,
    QMenuBar,
    QMenu,
    QAction,
    QToolBar,
)

from ..config import get_config
from ..utils.logger import get_logger
from ..database.models import Task
from .widgets.task_info_widget import TaskInfoWidget
from .widgets.task_track_widget import TaskTrackWidget
from .widgets.recommendation_widget import RecommendationWidget
from .widgets.notification_widget import NotificationWidget
from .widgets.import_export_widget import ImportExportWidget
from .widgets.statistics_widget import StatisticsWidget
from .widgets.library_widget import LibraryWidget
from .widgets.learning_widget import LearningWidget
from .widgets.auto_backup_config_widget import AutoBackupConfigWidget

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self) -> None:
        """初始化主窗口"""
        super().__init__()

        self.config = get_config()
        self._init_ui()
        self._init_menu()
        self._init_toolbar()
        self._init_statusbar()

        # 加载窗口状态
        self._load_window_state()

        logger.info("主窗口初始化完成")

    def _init_ui(self) -> None:
        """初始化UI"""
        # 设置窗口属性
        self.setWindowTitle(self.config.app_name)
        self.setGeometry(100, 100, 1280, 720)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QHBoxLayout(central_widget)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)

        # 创建左侧导航
        self.nav_list = QListWidget()
        self.nav_list.setMaximumWidth(200)
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)

        # 添加导航项
        nav_items = [
            "📋 任务信息",
            "📊 任务跟踪",
            "🔮 智能推荐",
            "🔔 提醒管理",
            "📁 数据导入",
            "📈 统计分析",
            "📚 推荐库",
            "📚 学习积累",
            "💾 自动备份",  # 新增
        ]

        for item_text in nav_items:
            item = QListWidgetItem(item_text)
            self.nav_list.addItem(item)

        # 创建右侧工作区
        self.work_area = QStackedWidget()

        # 创建各功能组件
        self.task_info_widget = TaskInfoWidget()
        self.task_track_widget = TaskTrackWidget()
        self.recommendation_widget = RecommendationWidget()
        self.notification_widget = NotificationWidget()
        self.import_export_widget = ImportExportWidget()
        self.statistics_widget = StatisticsWidget()
        self.library_widget = LibraryWidget()
        self.learning_widget = LearningWidget()
        self.auto_backup_config_widget = AutoBackupConfigWidget()  # 自动备份配置

        # 添加到工作区
        self.work_area.addWidget(self.task_info_widget)
        self.work_area.addWidget(self.task_track_widget)
        self.work_area.addWidget(self.recommendation_widget)
        self.work_area.addWidget(self.notification_widget)
        self.work_area.addWidget(self.import_export_widget)
        self.work_area.addWidget(self.statistics_widget)
        self.work_area.addWidget(self.library_widget)
        self.work_area.addWidget(self.learning_widget)
        self.work_area.addWidget(self.auto_backup_config_widget)  # 自动备份配置

        # 添加到分割器
        splitter.addWidget(self.nav_list)
        splitter.addWidget(self.work_area)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        # 设置默认选中的导航项
        self.nav_list.setCurrentRow(0)

        # 连接信号
        self._connect_signals()

    def _connect_signals(self) -> None:
        """连接组件信号"""
        # 任务信息组件信号
        self.task_info_widget.task_selected.connect(self._on_task_selected)
        self.task_info_widget.task_created.connect(self._on_task_created)
        self.task_info_widget.task_updated.connect(self._on_task_updated)

        # 任务跟踪组件信号
        self.task_track_widget.track_record_added.connect(self._on_track_record_added)

        # 推荐组件信号
        self.recommendation_widget.recommendation_clicked.connect(self._on_recommendation_clicked)

        # 提醒组件信号
        self.notification_widget.reminder_triggered.connect(self._on_reminder_triggered)

    def _on_task_selected(self, task_id: str) -> None:
        """任务选中事件"""
        logger.info(f"任务选中: {task_id}")
        self.statusBar().showMessage(f"已选中任务: {task_id}", 3000)

    def _on_task_created(self, task_id: str) -> None:
        """任务创建事件"""
        logger.info(f"新任务创建: {task_id}")
        self.statusBar().showMessage(f"新任务创建成功: {task_id}", 3000)

        # 自动学习任务信息
        try:
            from ..core.learning_service import get_learning_service
            task = Task.get_by_id(task_id)
            if task:
                task_data = task.to_dict()
                task_data["respondent_phone"] = ""
                task_data["respondent_email"] = ""
                learning_service = get_learning_service()
                learning_service.learn_from_task(task_data)
                logger.info(f"任务信息已自动学习: {task_id}")
        except Exception as e:
            logger.error(f"自动学习失败: {e}")

    def _on_task_updated(self, task_id: str) -> None:
        """任务更新事件"""
        logger.info(f"任务更新: {task_id}")
        self.statusBar().showMessage(f"任务更新成功: {task_id}", 3000)

    def _on_track_record_added(self, record_id: str) -> None:
        """跟踪记录添加事件"""
        logger.info(f"跟踪记录添加: {record_id}")
        self.statusBar().showMessage("跟踪记录添加成功", 3000)

    def _on_recommendation_clicked(self, task_id: str) -> None:
        """推荐任务点击事件"""
        logger.info(f"推荐任务点击: {task_id}")
        self.nav_list.setCurrentRow(0)  # 切换到任务信息页面
        self.task_info_widget._load_task_detail(task_id)

    def _on_reminder_triggered(self, task_id: str) -> None:
        """提醒触发事件"""
        logger.info(f"提醒触发: {task_id}")
        self.nav_list.setCurrentRow(0)  # 切换到任务信息页面
        self.task_info_widget._load_task_detail(task_id)

    def _init_menu(self) -> None:
        """初始化菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        new_action = QAction("新建任务(&N)", self)
        new_action.setShortcut("Ctrl+N")
        file_menu.addAction(new_action)

        import_action = QAction("导入(&I)...", self)
        import_action.setShortcut("Ctrl+I")
        file_menu.addAction(import_action)

        export_action = QAction("导出(&E)...", self)
        export_action.setShortcut("Ctrl+E")
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")

        copy_action = QAction("复制(&C)", self)
        copy_action.setShortcut("Ctrl+C")
        edit_menu.addAction(copy_action)

        paste_action = QAction("粘贴(&V)", self)
        paste_action.setShortcut("Ctrl+V")
        edit_menu.addAction(paste_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")

        refresh_action = QAction("刷新(&R)", self)
        refresh_action.setShortcut("F5")
        view_menu.addAction(refresh_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _init_toolbar(self) -> None:
        """初始化工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # 新建任务按钮
        new_task_btn = QPushButton("新建任务")
        new_task_btn.setMaximumWidth(100)
        toolbar.addWidget(new_task_btn)

        toolbar.addSeparator()

        # 导入按钮
        import_btn = QPushButton("导入")
        import_btn.setMaximumWidth(80)
        toolbar.addWidget(import_btn)

        # 导出按钮
        export_btn = QPushButton("导出")
        export_btn.setMaximumWidth(80)
        toolbar.addWidget(export_btn)

        toolbar.addSeparator()

        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.setMaximumWidth(80)
        toolbar.addWidget(refresh_btn)

    def _init_statusbar(self) -> None:
        """初始化状态栏"""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        # 添加状态标签
        self.status_label = QLabel("就绪")
        self.statusBar.addWidget(self.status_label)

        # 添加定时器更新状态栏
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(60000)  # 每分钟更新一次

    def _on_nav_changed(self, index: int) -> None:
        """
        导航切换事件

        Args:
            index: 当前索引
        """
        self.work_area.setCurrentIndex(index)
        logger.info(f"切换到工作区: {index}")

    def _show_about(self) -> None:
        """显示关于对话框"""
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.about(
            self,
            "关于",
            f"{self.config.app_name}\n"
            f"版本: {self.config.app_version}\n\n"
            f"市场咨询任务跟踪管理工具\n"
            f"提升团队协作效率",
        )

    def _update_status(self) -> None:
        """更新状态栏"""
        from datetime import datetime

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status_label.setText(f"就绪 | {current_time}")

    def _load_window_state(self) -> None:
        """加载窗口状态"""
        # 读取窗口大小配置
        width = self.config.get("ui.window.width", 1280)
        height = self.config.get("ui.window.height", 720)
        min_width = self.config.get("ui.window.min_width", 1024)
        min_height = self.config.get("ui.window.min_height", 600)

        self.resize(width, height)
        self.setMinimumSize(min_width, min_height)

    def _save_window_state(self) -> None:
        """保存窗口状态"""
        geometry = self.geometry()
        self.config.set("ui.window.width", geometry.width())
        self.config.set("ui.window.height", geometry.height())
        self.config.save_config()

    def closeEvent(self, event) -> None:
        """关闭事件"""
        # 关闭时自动备份
        try:
            from ..core.auto_backup_service import get_auto_backup_service
            auto_backup = get_auto_backup_service()
            if auto_backup.config.get("backup_on_shutdown", True):
                if auto_backup.config.should_backup_now():
                    logger.info("执行关闭时自动备份...")
                    auto_backup.trigger_backup("关闭备份")
        except Exception as e:
            logger.error(f"关闭时备份失败: {e}")

        self._save_window_state()
        logger.info("应用关闭")
        event.accept()
