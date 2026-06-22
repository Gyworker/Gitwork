# -*- coding: utf-8 -*-
"""
学习积累界面模块
Learning Accumulation UI Module:

提供学习积累功能的管理界面
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTabWidget,
    QProgressBar,
    QTextEdit,
    QMessageBox,
    QDialog,
    QDateEdit,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QSplitter,
)
from PyQt5.QtGui import QColor

from ...core.learning_service import (
    get_learning_service,
    get_contact_learning_service,
    get_recommendation_learning_service,
)
from ...database.models import Task
from ...utils.logger import get_logger

logger = get_logger(__name__)


class LearningWidget(QWidget):
    """学习积累管理组件"""

    learning_completed = pyqtSignal(dict)  # 学习完成信号

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """初始化学习积累组件"""
        super().__init__(parent)
        self.learning_service = get_learning_service()
        self.contact_service = get_contact_learning_service()
        self.recommendation_service = get_recommendation_learning_service()
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("📚 学习积累")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)

        # 创建选项卡
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # 通讯录学习页
        self.contact_tab = self._create_contact_tab()
        self.tabs.addTab(self.contact_tab, "👥 通讯录学习")

        # 推荐库学习页
        self.recommendation_tab = self._create_recommendation_tab()
        self.tabs.addTab(self.recommendation_tab, "🔮 推荐库学习")

        # 统计页
        self.statistics_tab = self._create_statistics_tab()
        self.tabs.addTab(self.statistics_tab, "📊 学习统计")

        # 批量学习页
        self.batch_tab = self._create_batch_tab()
        self.tabs.addTab(self.batch_tab, "⚡ 批量学习")

        layout.addStretch()

    def _create_contact_tab(self) -> QWidget:
        """创建通讯录学习页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 搜索区域
        search_group = QGroupBox("搜索学习到的联系人")
        search_layout = QHBoxLayout()

        self.contact_search_input = QLineEdit()
        self.contact_search_input.setPlaceholderText("输入联系人姓名或公司搜索...")
        search_layout.addWidget(self.contact_search_input)

        search_btn = QPushButton("🔍 搜索")
        search_btn.clicked.connect(self._on_search_contacts)
        search_layout.addWidget(search_btn)

        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

        # 联系人列表
        list_group = QGroupBox("学习到的联系人")
        list_layout = QVBoxLayout()

        self.contact_table = QTableWidget()
        self.contact_table.setColumnCount(8)
        self.contact_table.setHorizontalHeaderLabels([
            "姓名", "工号", "来源", "部门", "公司", "行业", "任务次数", "置信度"
        ])
        self.contact_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.contact_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 工号
        self.contact_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.contact_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.contact_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.contact_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.contact_table.setSelectionBehavior(QTableWidget.SelectRows)
        list_layout.addWidget(self.contact_table)

        list_group.setLayout(list_layout)
        layout.addWidget(list_group, 1)

        # 操作按钮
        btn_layout = QHBoxLayout()

        refresh_btn = QPushButton("🔄 刷新列表")
        refresh_btn.clicked.connect(self._on_refresh_contacts)
        btn_layout.addWidget(refresh_btn)

        export_btn = QPushButton("📤 导出到通讯录")
        export_btn.clicked.connect(self._on_export_contacts)
        btn_layout.addWidget(export_btn)

        merge_btn = QPushButton("🔗 合并重名")
        merge_btn.clicked.connect(self._on_merge_contacts)
        btn_layout.addWidget(merge_btn)

        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # 加载初始数据
        self._on_refresh_contacts()

        return widget

    def _create_recommendation_tab(self) -> QWidget:
        """创建推荐库学习页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 搜索区域
        search_group = QGroupBox("搜索推荐库")
        search_layout = QHBoxLayout()

        self.rec_search_input = QLineEdit()
        self.rec_search_input.setPlaceholderText("输入关键模块搜索...")
        search_layout.addWidget(self.rec_search_input)

        search_btn = QPushButton("🔍 搜索")
        search_btn.clicked.connect(self._on_search_recommendations)
        search_layout.addWidget(search_btn)

        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

        # 推荐库列表
        list_group = QGroupBox("学习到的推荐库")
        list_layout = QVBoxLayout()

        # 视图切换
        view_layout = QHBoxLayout()
        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems(["详细视图", "汇总视图"])
        self.view_mode_combo.currentIndexChanged.connect(self._on_view_mode_changed)
        view_layout.addWidget(QLabel("显示模式:"))
        view_layout.addWidget(self.view_mode_combo)
        view_layout.addStretch()
        list_layout.addLayout(view_layout)

        self.recommendation_table = QTableWidget()
        self.recommendation_table.setColumnCount(9)
        self.recommendation_table.setHorizontalHeaderLabels([
            "答复人", "工号", "关键模块", "所有模块", "部门", "行业",
            "任务数", "答复数", "置信度"
        ])
        self.recommendation_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.recommendation_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 工号
        self.recommendation_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.recommendation_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)  # 所有模块
        self.recommendation_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.recommendation_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.recommendation_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeToContents)
        self.recommendation_table.setSelectionBehavior(QTableWidget.SelectRows)
        list_layout.addWidget(self.recommendation_table)

        list_group.setLayout(list_layout)
        layout.addWidget(list_group, 1)

        # 操作按钮
        btn_layout = QHBoxLayout()

        refresh_btn = QPushButton("🔄 刷新列表")
        refresh_btn.clicked.connect(self._on_refresh_recommendations)
        btn_layout.addWidget(refresh_btn)

        view_modules_btn = QPushButton("📋 查看相关模块")
        view_modules_btn.clicked.connect(self._on_view_related_modules)
        btn_layout.addWidget(view_modules_btn)

        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # 加载初始数据
        self._on_refresh_recommendations()

        return widget

    def _create_statistics_tab(self) -> QWidget:
        """创建统计页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 统计卡片
        stats_group = QGroupBox("学习统计概览")
        stats_layout = QFormLayout()

        self.total_contacts_label = QLabel("0")
        self.total_contacts_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2196F3;")
        stats_layout.addRow("学习到的联系人:", self.total_contacts_label)

        self.total_recommendations_label = QLabel("0")
        self.total_recommendations_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        stats_layout.addRow("推荐库条目:", self.total_recommendations_label)

        self.unique_modules_label = QLabel("0")
        self.unique_modules_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #FF9800;")
        stats_layout.addRow("关键模块数量:", self.unique_modules_label)

        self.unique_industries_label = QLabel("0")
        self.unique_industries_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #9C27B0;")
        stats_layout.addRow("涉及行业数量:", self.unique_industries_label)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # 行业分布
        industry_group = QGroupBox("行业分布")
        industry_layout = QVBoxLayout()

        self.industry_list = QListWidget()
        industry_layout.addWidget(self.industry_list)

        industry_group.setLayout(industry_layout)
        layout.addWidget(industry_group, 1)

        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新统计")
        refresh_btn.clicked.connect(self._on_refresh_statistics)
        layout.addWidget(refresh_btn)

        return widget

    def _create_batch_tab(self) -> QWidget:
        """创建批量学习页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 说明
        info_label = QLabel(
            "⚡ 批量学习功能将从所有任务数据中自动学习和积累信息。\n"
            "这将分析现有的所有任务，提取咨询者、答复人、关键模块等信息的关联关系。"
        )
        info_label.setStyleSheet("padding: 10px; background: #FFF3E0; border-radius: 5px;")
        layout.addWidget(info_label)

        # 批量学习按钮
        learn_group = QGroupBox("执行批量学习")
        learn_layout = QVBoxLayout()

        learn_btn = QPushButton("🚀 开始批量学习")
        learn_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 15px;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        learn_btn.clicked.connect(self._on_batch_learn)
        learn_layout.addWidget(learn_btn)

        self.batch_progress = QProgressBar()
        self.batch_progress.setMinimum(0)
        self.batch_progress.setMaximum(100)
        self.batch_progress.setValue(0)
        learn_layout.addWidget(self.batch_progress)

        self.batch_log = QTextEdit()
        self.batch_log.setMaximumHeight(150)
        self.batch_log.setReadOnly(True)
        learn_layout.addWidget(self.batch_log)

        learn_group.setLayout(learn_layout)
        layout.addWidget(learn_group)

        # 从任务学习
        task_group = QGroupBox("从单个任务学习")
        task_layout = QHBoxLayout()

        self.task_id_input = QLineEdit()
        self.task_id_input.setPlaceholderText("输入任务ID...")
        task_layout.addWidget(self.task_id_input)

        learn_task_btn = QPushButton("📝 学习此任务")
        learn_task_btn.clicked.connect(self._on_learn_single_task)
        task_layout.addWidget(learn_task_btn)

        task_group.setLayout(task_layout)
        layout.addWidget(task_group)

        return widget

    def _on_search_contacts(self) -> None:
        """搜索联系人"""
        keyword = self.contact_search_input.text().strip()
        contacts = self.contact_service.get_learned_contacts(keyword=keyword, limit=100)
        self._display_contacts(contacts)

    def _on_refresh_contacts(self) -> None:
        """刷新联系人列表"""
        contacts = self.contact_service.get_learned_contacts(limit=100)
        self._display_contacts(contacts)

    def _display_contacts(self, contacts: List[Dict]) -> None:
        """显示联系人列表"""
        self.contact_table.setRowCount(len(contacts))

        for i, contact in enumerate(contacts):
            self.contact_table.setItem(i, 0, QTableWidgetItem(contact.get("name", "")))
            self.contact_table.setItem(i, 1, QTableWidgetItem(contact.get("employee_id", "")))  # 工号
            self.contact_table.setItem(i, 2, QTableWidgetItem(contact.get("source_type", "")))
            self.contact_table.setItem(i, 3, QTableWidgetItem(contact.get("department", "")))
            self.contact_table.setItem(i, 4, QTableWidgetItem(contact.get("company", "")))
            self.contact_table.setItem(i, 5, QTableWidgetItem(contact.get("industry", "")))
            self.contact_table.setItem(i, 6, QTableWidgetItem(str(contact.get("task_count", 0))))

            confidence = contact.get("confidence", 0.5)
            confidence_item = QTableWidgetItem(f"{confidence:.0%}")
            # 根据置信度设置颜色
            if confidence >= 0.8:
                confidence_item.setBackground(QColor("#C8E6C9"))  # 绿色
            elif confidence >= 0.5:
                confidence_item.setBackground(QColor("#FFF9C4"))  # 黄色
            else:
                confidence_item.setBackground(QColor("#FFCDD2"))  # 红色
            self.contact_table.setItem(i, 7, confidence_item)

    def _on_export_contacts(self) -> None:
        """导出联系人到通讯录"""
        selected_rows = self.contact_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要导出的联系人！")
            return

        row = selected_rows[0].row()
        name = self.contact_table.item(row, 0).text()

        count = self.contact_service.export_to_contacts([name])

        if count > 0:
            QMessageBox.information(self, "成功", f"已导出 {count} 个联系人到通讯录！")
        else:
            QMessageBox.warning(self, "失败", "导出失败！")

    def _on_merge_contacts(self) -> None:
        """合并重名联系人"""
        selected_rows = self.contact_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要合并的联系人！")
            return

        row = selected_rows[0].row()
        name = self.contact_table.item(row, 0).text()

        # 查找同名联系人
        duplicates = self.contact_service.find_duplicates(name)

        if len(duplicates) < 2:
            QMessageBox.information(self, "提示", f"联系人 {name} 没有重名，无需合并！")
            return

        # 显示重名列表，让用户选择保留哪个
        msg = f"发现 {len(duplicates)} 个同名联系人：\n\n"
        for i, dup in enumerate(duplicates):
            emp_id = dup.get("employee_id") or "无工号"
            company = dup.get("company") or "无公司"
            task_count = dup.get("task_count", 0)
            msg += f"{i + 1}. 工号: {emp_id}, 公司: {company}, 任务数: {task_count}\n"

        msg += "\n请选择要保留的联系人编号，其他将被合并："

        # 简单处理：保留第一个，其余合并
        reply = QMessageBox.question(
            self,
            "合并重名联系人",
            msg,
            QMessageBox.Yes | QMessageBox.Cancel
        )

        if reply == QMessageBox.Yes:
            # 保留第一个，合并其他的任务数
            keep_id = duplicates[0]["id"]
            other_ids = [d["id"] for d in duplicates[1:]]

            if self.contact_service.merge_contacts(other_ids, keep_id):
                QMessageBox.information(self, "成功", f"已将 {len(other_ids)} 个重名联系人合并到保留记录！")
                self._on_refresh_contacts()
            else:
                QMessageBox.warning(self, "失败", "合并失败！")

    def _on_search_recommendations(self) -> None:
        """搜索推荐库"""
        keyword = self.rec_search_input.text().strip()
        recommendations = self.recommendation_service.get_recommendations(key_module=keyword, limit=100)
        self._display_recommendations(recommendations)

    def _on_refresh_recommendations(self) -> None:
        """刷新推荐库列表"""
        recommendations = self.recommendation_service.get_recommendations(limit=100)
        self._display_recommendations(recommendations)

    def _display_recommendations(self, recommendations: List[Dict], is_aggregated: bool = False) -> None:
        """显示推荐库列表

        Args:
            recommendations: 推荐数据列表
            is_aggregated: 是否为汇总视图
        """
        self.recommendation_table.setRowCount(len(recommendations))

        for i, rec in enumerate(recommendations):
            self.recommendation_table.setItem(i, 0, QTableWidgetItem(rec.get("respondent_name", "")))
            self.recommendation_table.setItem(i, 1, QTableWidgetItem(rec.get("employee_id", "")))  # 工号

            if is_aggregated:
                # 汇总视图：显示所有模块
                all_modules = rec.get("all_modules", "")
                self.recommendation_table.setItem(i, 2, QTableWidgetItem(""))  # 关键模块列留空
                self.recommendation_table.setItem(i, 3, QTableWidgetItem(all_modules))  # 所有模块
                self.recommendation_table.setItem(i, 4, QTableWidgetItem(rec.get("department", "")))
                self.recommendation_table.setItem(i, 5, QTableWidgetItem(rec.get("industry", "")))
                self.recommendation_table.setItem(i, 6, QTableWidgetItem(str(rec.get("total_task_count", 0))))
                self.recommendation_table.setItem(i, 7, QTableWidgetItem(str(rec.get("total_reply_count", 0))))
                confidence = rec.get("max_confidence", 0.5)
            else:
                # 详细视图
                self.recommendation_table.setItem(i, 2, QTableWidgetItem(rec.get("key_module", "")))
                self.recommendation_table.setItem(i, 3, QTableWidgetItem(rec.get("all_modules", "")))  # 所有模块
                self.recommendation_table.setItem(i, 4, QTableWidgetItem(rec.get("department", "")))
                self.recommendation_table.setItem(i, 5, QTableWidgetItem(rec.get("industry", "")))
                self.recommendation_table.setItem(i, 6, QTableWidgetItem(str(rec.get("task_count", 0))))
                self.recommendation_table.setItem(i, 7, QTableWidgetItem(str(rec.get("reply_count", 0))))
                confidence = rec.get("confidence", 0.5)

            confidence_item = QTableWidgetItem(f"{confidence:.0%}")
            if confidence >= 0.8:
                confidence_item.setBackground(QColor("#C8E6C9"))
            elif confidence >= 0.5:
                confidence_item.setBackground(QColor("#FFF9C4"))
            else:
                confidence_item.setBackground(QColor("#FFCDD2"))
            self.recommendation_table.setItem(i, 8, confidence_item)

    def _on_view_mode_changed(self) -> None:
        """视图模式切换"""
        self._on_refresh_recommendations()

    def _on_refresh_recommendations(self) -> None:
        """刷新推荐库列表"""
        keyword = self.rec_search_input.text().strip()
        is_aggregated = self.view_mode_combo.currentIndex() == 1  # 汇总视图

        if is_aggregated:
            recommendations = self.recommendation_service.get_aggregated_recommendations(
                key_module=keyword, limit=100
            )
        else:
            recommendations = self.recommendation_service.get_recommendations(
                key_module=keyword, limit=100
            )

        self._display_recommendations(recommendations, is_aggregated)

    def _on_view_related_modules(self) -> None:
        """查看相关模块"""
        selected_rows = self.recommendation_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要查看的推荐库条目！")
            return

        row = selected_rows[0].row()
        key_module = self.recommendation_table.item(row, 2).text()

        related = self.recommendation_service.get_related_modules(key_module)

        if related:
            QMessageBox.information(
                self, "相关模块",
                f"与「{key_module}」相关的模块：\n\n" + "\n".join([f"• {m}" for m in related])
            )
        else:
            QMessageBox.information(self, "相关模块", f"未找到与「{key_module}」相关的模块")

    def _on_refresh_statistics(self) -> None:
        """刷新统计"""
        stats = self.learning_service.get_statistics()

        self.total_contacts_label.setText(str(stats.get("total_learned_contacts", 0)))
        self.total_recommendations_label.setText(str(stats.get("total_recommendations", 0)))
        self.unique_modules_label.setText(str(stats.get("unique_modules", 0)))
        self.unique_industries_label.setText(str(stats.get("unique_industries", 0)))

        # 更新行业分布
        self.industry_list.clear()
        # 从recommendation_learning获取行业分布
        from ...database.connection import get_db_connection
        db = get_db_connection()
        rows = db.fetchall(
            """
            SELECT industry, COUNT(*) as count
            FROM recommendation_learning
            WHERE industry IS NOT NULL AND industry != ''
            GROUP BY industry
            ORDER BY count DESC
            LIMIT 10
            """
        )
        for row in rows:
            self.industry_list.addItem(f"📊 {row[0]}: {row[1]} 条记录")

    def _on_batch_learn(self) -> None:
        """执行批量学习"""
        reply = QMessageBox.question(
            self, "确认批量学习",
            "批量学习将分析所有任务数据，这可能需要一些时间。\n是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply != QMessageBox.Yes:
            return

        self.batch_log.clear()
        self.batch_log.append("🚀 开始批量学习...")

        def progress_callback(current: int, total: int, message: str) -> None:
            self.batch_progress.setValue(current)
            self.batch_log.append(message)

        try:
            result = self.learning_service.learn_from_all_tasks(progress_callback)

            if result.get("success"):
                self.batch_log.append(f"\n✅ 批量学习完成！")
                self.batch_log.append(f"   总任务数: {result.get('total_tasks', 0)}")
                self.batch_log.append(f"   学习联系人: {result.get('contacts_learned', 0)}")
                self.batch_log.append(f"   学习推荐库: {result.get('recommendations_learned', 0)}")

                # 刷新各页面
                self._on_refresh_contacts()
                self._on_refresh_recommendations()
                self._on_refresh_statistics()

                self.learning_completed.emit(result)
            else:
                self.batch_log.append(f"\n❌ 批量学习失败: {result.get('error', '未知错误')}")

        except Exception as e:
            logger.error(f"批量学习失败: {e}")
            self.batch_log.append(f"\n❌ 批量学习失败: {e}")

    def _on_learn_single_task(self) -> None:
        """从单个任务学习"""
        task_id = self.task_id_input.text().strip()

        if not task_id:
            QMessageBox.warning(self, "提示", "请输入任务ID！")
            return

        task = Task.get_by_id(task_id)
        if not task:
            QMessageBox.warning(self, "错误", "任务不存在！")
            return

        task_data = task.to_dict()
        task_data["respondent_phone"] = ""
        task_data["respondent_email"] = ""

        success = self.learning_service.learn_from_task(task_data)

        if success:
            QMessageBox.information(self, "成功", "任务信息已学习！")
            self._on_refresh_contacts()
            self._on_refresh_recommendations()
        else:
            QMessageBox.warning(self, "失败", "学习失败！")

    def refresh_all(self) -> None:
        """刷新所有页面"""
        self._on_refresh_contacts()
        self._on_refresh_recommendations()
        self._on_refresh_statistics()
