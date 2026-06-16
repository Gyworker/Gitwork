"""
市场咨询任务跟踪工具 - 主窗口
功能区布局：
- 顶部：功能按钮区
- 右侧：任务输入区
- 中间：任务信息区
- 左侧：任务跟踪区
- 底部：任务提醒区
"""

from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QPushButton, QToolBar,
    QStatusBar, QLabel, QMessageBox, QFileDialog,
    QAction, QMenuBar, QMenu, QStatusBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDateTime
from PyQt5.QtGui import QIcon, QFont

from ..config import get_config
from ..database.connection import get_db_connection
from ..database.models import TaskModel
from .widgets import (
    ContentImportWidget,
    TaskInfoWidget,
    TaskTrackWidget,
    ContactWidget,
    ReminderWidget,
)


class MainWindow(QMainWindow):
    """
    主窗口类
    布局：顶部功能按钮区 + 左右分割区（左侧任务跟踪 + 右侧任务输入/信息）
    """
    
    # 信号定义
    task_created = pyqtSignal(str)  # 任务创建信号
    task_updated = pyqtSignal(str)  # 任务更新信号
    reminder_triggered = pyqtSignal(str)  # 提醒触发信号
    
    def __init__(self):
        super().__init__()
        
        # 初始化组件
        self._init_config()
        self._init_ui()
        self._init_connections()
        self._init_reminder_timer()
        
        # 加载初始数据
        self._load_initial_data()
        
    def _init_config(self):
        """初始化配置"""
        self.config = get_config()
        self.db = get_db_connection()
        self.task_model = TaskModel(self.db)
        
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("市场咨询任务跟踪工具")
        self.setGeometry(100, 100, 1400, 900)
        
        # 设置字体
        font = QFont("宋体", 10)
        self.setFont(font)
        
        # 创建菜单栏
        self._create_menu_bar()
        
        # 创建工具栏
        self._create_toolbar()
        
        # 创建主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # ===== 功能按钮区 =====
        self.function_bar = self._create_function_bar()
        main_layout.addLayout(self.function_bar)
        
        # ===== 主内容区（左右分割）=====
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：任务跟踪区（带Tab切换）
        self.left_widget = self._create_left_panel()
        splitter.addWidget(self.left_widget)
        splitter.setStretchFactor(0, 1)
        
        # 右侧：任务输入区 + 任务信息区（上下分割）
        right_splitter = QSplitter(Qt.Vertical)
        
        # 任务输入区
        self.import_widget = ContentImportWidget()
        self.import_widget.content_parsed.connect(self._on_content_parsed)
        right_splitter.addWidget(self.import_widget)
        
        # 任务信息区
        self.task_info_widget = TaskInfoWidget()
        self.task_info_widget.task_submitted.connect(self._on_task_submitted)
        right_splitter.addWidget(self.task_info_widget)
        
        right_splitter.setStretchFactor(0, 1)
        right_splitter.setStretchFactor(1, 2)
        
        splitter.addWidget(right_splitter)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        # ===== 状态栏 =====
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("就绪")
        self.status_bar.addPermanentWidget(self.status_label)
        self._update_status("系统启动完成")
        
    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        export_action = QAction("导出任务...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._on_export)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 数据菜单
        data_menu = menubar.addMenu("数据(&D)")
        
        import_contact_action = QAction("导入通讯录...", self)
        import_contact_action.triggered.connect(self._on_import_contacts)
        data_menu.addAction(import_contact_action)
        
        import_recommend_action = QAction("导入推荐库...", self)
        import_recommend_action.triggered.connect(self._on_import_recommendations)
        data_menu.addAction(import_recommend_action)
        
        data_menu.addSeparator()
        
        manage_contact_action = QAction("通讯录管理...", self)
        manage_contact_action.triggered.connect(self._on_manage_contacts)
        data_menu.addAction(manage_contact_action)
        
        manage_recommend_action = QAction("推荐库管理...", self)
        manage_recommend_action.triggered.connect(self._on_manage_recommendations)
        data_menu.addAction(manage_recommend_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        about_action = QAction("关于...", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
        
    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # 应答中数据池
        btn_in_progress = QPushButton("应答中")
        btn_in_progress.clicked.connect(lambda: self._filter_tasks("进行中"))
        toolbar.addWidget(btn_in_progress)
        
        # 已应答数据池
        btn_answered = QPushButton("已答复")
        btn_answered.clicked.connect(lambda: self._filter_tasks("已答复"))
        toolbar.addWidget(btn_answered)
        
        # 全部数据
        btn_all = QPushButton("全部")
        btn_all.clicked.connect(lambda: self._filter_tasks("全部"))
        toolbar.addWidget(btn_all)
        
        toolbar.addSeparator()
        
        # 导出应答中
        btn_export_active = QPushButton("导出应答中")
        btn_export_active.clicked.connect(lambda: self._export_tasks("进行中"))
        toolbar.addWidget(btn_export_active)
        
        # 导出已答复
        btn_export_done = QPushButton("导出已答复")
        btn_export_done.clicked.connect(lambda: self._export_tasks("已答复"))
        toolbar.addWidget(btn_export_done)
        
        toolbar.addSeparator()
        
        # 通讯录管理
        btn_contacts = QPushButton("通讯录")
        btn_contacts.clicked.connect(self._on_manage_contacts)
        toolbar.addWidget(btn_contacts)
        
        # 推荐库管理
        btn_recommend = QPushButton("推荐库")
        btn_recommend.clicked.connect(self._on_manage_recommendations)
        toolbar.addWidget(btn_recommend)
        
    def _create_function_bar(self) -> QHBoxLayout:
        """创建功能按钮区"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 功能按钮区标题
        title = QLabel("【功能按钮区】")
        title.setStyleSheet("font-weight: bold; color: #1976D2;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        return layout
        
    def _create_left_panel(self) -> QWidget:
        """创建左侧面板（任务跟踪区 + 提醒区）"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建Tab切换
        self.left_tabs = QTabWidget()
        
        # 任务跟踪Tab
        self.task_track_widget = TaskTrackWidget()
        self.task_track_widget.task_selected.connect(self._on_task_selected)
        self.task_track_widget.task_double_clicked.connect(self._on_task_double_clicked)
        self.left_tabs.addTab(self.task_track_widget, "任务跟踪")
        
        # 任务提醒Tab
        self.reminder_widget = ReminderWidget()
        self.reminder_widget.reminder_clicked.connect(self._on_reminder_clicked)
        self.left_tabs.addTab(self.reminder_widget, "任务提醒")
        
        layout.addWidget(self.left_tabs)
        
        return widget
        
    def _init_connections(self):
        """初始化信号连接"""
        # 连接任务创建/更新信号
        self.task_created.connect(self._on_task_created)
        self.task_updated.connect(self._on_task_updated)
        
    def _init_reminder_timer(self):
        """初始化提醒定时器"""
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self._check_reminders)
        
        # 每分钟检查一次
        self.reminder_timer.start(60000)
        
    def _load_initial_data(self):
        """加载初始数据"""
        try:
            # 加载任务列表
            tasks = self.task_model.get_all_tasks()
            self.task_track_widget.load_tasks(tasks)
            
            # 更新提醒列表
            self._refresh_reminders()
            
            self._update_status(f"已加载 {len(tasks)} 个任务")
        except Exception as e:
            self._show_error(f"加载数据失败: {e}")
            
    def _on_content_parsed(self, parsed_data: dict):
        """内容解析完成回调"""
        self.task_info_widget.fill_from_parsed(parsed_data)
        self._update_status("内容解析完成，请确认任务信息")
        
    def _on_task_submitted(self, task_data: dict):
        """任务提交回调"""
        try:
            task_id = self.task_model.create_task(task_data)
            self.task_created.emit(task_id)
            
            # 刷新任务列表
            tasks = self.task_model.get_all_tasks()
            self.task_track_widget.load_tasks(tasks)
            
            # 清空输入
            self.import_widget.clear()
            self.task_info_widget.clear()
            
            self._update_status(f"任务创建成功: {task_data.get('task_name', '新任务')}")
            QMessageBox.information(self, "成功", "任务创建成功！")
            
        except Exception as e:
            self._show_error(f"创建任务失败: {e}")
            
    def _on_task_selected(self, task_id: str):
        """任务选中回调"""
        try:
            task = self.task_model.get_task(task_id)
            if task:
                self.task_info_widget.load_task(task)
        except Exception as e:
            self._show_error(f"加载任务失败: {e}")
            
    def _on_task_double_clicked(self, task_id: str):
        """任务双击回调 - 打开详情"""
        self._show_task_detail(task_id)
        
    def _on_task_created(self, task_id: str):
        """任务创建完成"""
        self._refresh_reminders()
        
    def _on_task_updated(self, task_id: str):
        """任务更新完成"""
        tasks = self.task_model.get_all_tasks()
        self.task_track_widget.load_tasks(tasks)
        
    def _on_reminder_clicked(self, task_id: str):
        """提醒点击回调"""
        self._show_reminder_dialog(task_id)
        
    def _check_reminders(self):
        """检查提醒"""
        self._refresh_reminders()
        
    def _refresh_reminders(self):
        """刷新提醒列表"""
        try:
            # 获取需要提醒的任务
            now = QDateTime.currentDateTime()
            tasks = self.task_model.get_tasks_needing_reminder(now.toPython())
            self.reminder_widget.load_reminders(tasks)
        except Exception:
            pass
        
    def _filter_tasks(self, filter_type: str):
        """筛选任务"""
        try:
            if filter_type == "全部":
                tasks = self.task_model.get_all_tasks()
            else:
                tasks = self.task_model.get_tasks_by_status(filter_type)
            self.task_track_widget.load_tasks(tasks)
            self._update_status(f"显示 {filter_type} 任务: {len(tasks)} 个")
        except Exception as e:
            self._show_error(f"筛选失败: {e}")
            
    def _export_tasks(self, export_type: str):
        """导出任务"""
        try:
            # 获取文件保存路径
            from datetime import datetime
            filename = f"任务_{export_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath, _ = QFileDialog.getSaveFileName(
                self, "导出任务", filename, "Excel文件 (*.xlsx)"
            )
            
            if filepath:
                self._do_export(filepath, export_type)
                
        except Exception as e:
            self._show_error(f"导出失败: {e}")
            
    def _do_export(self, filepath: str, export_type: str):
        """执行导出"""
        # TODO: 实现Excel导出
        self._update_status(f"导出功能开发中...")
        
    def _on_import_contacts(self):
        """导入通讯录"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "导入通讯录", "", "文本文件 (*.txt *.csv);;Excel文件 (*.xlsx *.xls)"
        )
        if filepath:
            self._import_contacts_from_file(filepath)
            
    def _import_contacts_from_file(self, filepath: str):
        """从文件导入通讯录"""
        # TODO: 实现通讯录导入
        self._update_status("通讯录导入功能开发中...")
        
    def _on_import_recommendations(self):
        """导入推荐库"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "导入推荐库", "", "文本文件 (*.txt *.csv);;Excel文件 (*.xlsx *.xls)"
        )
        if filepath:
            self._import_recommendations_from_file(filepath)
            
    def _import_recommendations_from_file(self, filepath: str):
        """从文件导入推荐库"""
        # TODO: 实现推荐库导入
        self._update_status("推荐库导入功能开发中...")
        
    def _on_manage_contacts(self):
        """通讯录管理"""
        dialog = ContactWidget()
        dialog.exec_()
        
    def _on_manage_recommendations(self):
        """推荐库管理"""
        # TODO: 实现推荐库管理弹窗
        self._update_status("推荐库管理功能开发中...")
        
    def _on_export(self):
        """导出任务"""
        self._export_tasks("全部")
        
    def _show_task_detail(self, task_id: str):
        """显示任务详情"""
        # TODO: 实现任务详情弹窗
        self._update_status(f"显示任务详情: {task_id}")
        
    def _show_reminder_dialog(self, task_id: str):
        """显示提醒弹窗"""
        # TODO: 实现提醒弹窗
        self._update_status(f"显示提醒: {task_id}")
        
    def _on_about(self):
        """关于"""
        QMessageBox.about(
            self, "关于",
            "市场咨询任务跟踪工具 V1.0\n\n"
            "一款面向市场咨询场景的任务跟踪管理工具\n"
            "实现任务信息解析、记录、查询、跟踪、提醒的一体化管理"
        )
        
    def _update_status(self, message: str):
        """更新状态栏"""
        self.status_label.setText(message)
        self.statusBar().showMessage(message, 3000)
        
    def _show_error(self, message: str):
        """显示错误"""
        QMessageBox.critical(self, "错误", message)
        self._update_status(f"错误: {message}")
        
    def closeEvent(self, event):
        """关闭窗口事件"""
        reply = QMessageBox.question(
            self, "确认退出",
            "确定要退出吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 关闭数据库连接
            if hasattr(self, 'db'):
                self.db.close()
            event.accept()
        else:
            event.ignore()
