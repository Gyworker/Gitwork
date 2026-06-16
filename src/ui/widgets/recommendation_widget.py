# -*- coding: utf-8 -*-
"""
智能推荐模块
Smart Recommendation Module

提供智能推荐功能
"""

from typing import Optional, List, Tuple
import re

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
)

from ..database.models import Task, Recommendation
from ..database.er_diagram import RecommendationLibraryDAO
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Recommender:
    """推荐引擎"""

    def __init__(self) -> None:
        """初始化推荐引擎"""
        self.library_dao = RecommendationLibraryDAO()
        self.similarity_threshold = 0.6

    def extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        if not text:
            return []

        # 移除标点符号
        text = re.sub(r"[^\w\s]", " ", text)
        # 分词
        words = text.split()
        # 过滤停用词和短词
        stop_words = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"}
        keywords = [w for w in words if len(w) >= 2 and w not in stop_words]
        return list(set(keywords))

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        if not text1 or not text2:
            return 0.0

        keywords1 = set(self.extract_keywords(text1))
        keywords2 = set(self.extract_keywords(text2))

        if not keywords1 or not keywords2:
            return 0.0

        # Jaccard相似度
        intersection = keywords1 & keywords2
        union = keywords1 | keywords2
        similarity = len(intersection) / len(union) if union else 0.0

        return similarity

    def recommend(self, task: Task, max_results: int = 5) -> List[Tuple[Task, float]]:
        """
        为任务推荐相似任务

        Args:
            task: 目标任务
            max_results: 最大结果数

        Returns:
            相似任务列表 [(任务, 相似度), ...]
        """
        try:
            all_tasks = Task.get_all()
            results = []

            # 计算与每个任务的相似度
            target_text = f"{task.task_name} {task.task_content} {task.key_module} {task.industry}"

            for t in all_tasks:
                if t.task_id == task.task_id:
                    continue

                compare_text = f"{t.task_name} {t.task_content} {t.key_module} {t.industry}"
                similarity = self.calculate_similarity(target_text, compare_text)

                if similarity >= self.similarity_threshold:
                    results.append((t, similarity))

            # 按相似度排序
            results.sort(key=lambda x: x[1], reverse=True)

            return results[:max_results]

        except Exception as e:
            logger.error(f"推荐失败: {e}")
            return []

    def recommend_from_library(self, keywords: List[str]) -> List[dict]:
        """
        从推荐库获取推荐

        Args:
            keywords: 关键词列表

        Returns:
            推荐库条目列表
        """
        try:
            results = []
            for keyword in keywords:
                items = self.library_dao.search(keyword)
                for item in items:
                    if item not in results:
                        results.append(item)

            return results

        except Exception as e:
            logger.error(f"从推荐库获取推荐失败: {e}")
            return []


class RecommendationWidget(QWidget):
    """智能推荐组件"""

    recommendation_clicked = pyqtSignal(str)  # 发送推荐的任务ID

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """初始化推荐组件"""
        super().__init__(parent)
        self.recommender = Recommender()
        self.current_task_id: Optional[str] = None
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("🔮 智能推荐")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)

        # 任务选择
        select_group = QGroupBox("选择任务")
        select_layout = QHBoxLayout()

        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("输入任务ID...")
        self.task_input.returnPressed.connect(self._on_recommend)
        select_layout.addWidget(self.task_input)

        recommend_btn = QPushButton("获取推荐")
        recommend_btn.clicked.connect(self._on_recommend)
        select_layout.addWidget(recommend_btn)

        select_group.setLayout(select_layout)
        layout.addWidget(select_group)

        # 推荐结果
        result_group = QGroupBox("推荐结果")
        result_layout = QVBoxLayout()

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels([
            "任务名称", "咨询者", "相似度", "推荐来源", "行业"
        ])
        self.result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.result_table.itemDoubleClicked.connect(self._on_result_double_click)
        result_layout.addWidget(self.result_table)

        result_group.setLayout(result_layout)
        layout.addWidget(result_group, 1)

        # 推荐库入口
        lib_group = QGroupBox("推荐库")
        lib_layout = QVBoxLayout()

        lib_label = QLabel("基于历史任务学习积累的推荐库")
        lib_layout.addWidget(lib_label)

        manage_lib_btn = QPushButton("管理推荐库")
        manage_lib_btn.clicked.connect(self._on_manage_library)
        lib_layout.addWidget(manage_lib_btn)

        lib_group.setLayout(lib_layout)
        layout.addWidget(lib_group)

    def _on_recommend(self) -> None:
        """获取推荐"""
        task_id = self.task_input.text().strip()
        if not task_id:
            QMessageBox.warning(self, "警告", "请输入任务ID！")
            return

        task = Task.get_by_id(task_id)
        if not task:
            QMessageBox.warning(self, "错误", "任务不存在！")
            return

        self.current_task_id = task_id
        self._load_recommendations(task)

    def _load_recommendations(self, task: Task) -> None:
        """加载推荐结果"""
        try:
            # 获取相似任务推荐
            similar_tasks = self.recommender.recommend(task, max_results=10)

            # 获取关键词
            keywords = self.recommender.extract_keywords(
                f"{task.task_name} {task.task_content} {task.key_module}"
            )

            # 从推荐库获取推荐
            library_items = self.recommender.recommend_from_library(keywords)

            # 显示结果
            self.result_table.setRowCount(len(similar_tasks) + len(library_items))

            row = 0
            for t, similarity in similar_tasks:
                self.result_table.setItem(row, 0, QTableWidgetItem(t.task_name))
                self.result_table.setItem(row, 1, QTableWidgetItem(t.inquirer))
                similarity_str = f"{similarity:.2%}"
                self.result_table.setItem(row, 2, QTableWidgetItem(similarity_str))
                self.result_table.setItem(row, 3, QTableWidgetItem("相似任务"))
                self.result_table.setItem(row, 4, QTableWidgetItem(t.industry))
                row += 1

            for item in library_items:
                self.result_table.setItem(row, 0, QTableWidgetItem(item.get("related_module", "")))
                self.result_table.setItem(row, 1, QTableWidgetItem("-"))
                self.result_table.setItem(row, 2, QTableWidgetItem("-"))
                self.result_table.setItem(row, 3, QTableWidgetItem("推荐库"))
                self.result_table.setItem(row, 4, QTableWidgetItem("-"))
                row += 1

            # 保存推荐记录
            for t, similarity in similar_tasks:
                rec = Recommendation(
                    source_task_id=task.task_id,
                    target_task_id=t.task_id,
                    similarity=similarity,
                    recommendation_type="similar_task",
                )
                rec.save()

            logger.info(f"生成{len(similar_tasks)}条推荐结果")

        except Exception as e:
            logger.error(f"获取推荐失败: {e}")
            QMessageBox.warning(self, "错误", f"获取推荐失败: {e}")

    def _on_result_double_click(self, item: QTableWidgetItem) -> None:
        """结果双击事件"""
        row = item.row()
        task_name = self.result_table.item(row, 0).text()
        source = self.result_table.item(row, 3).text()

        if source == "相似任务":
            # 查找对应任务
            tasks = Task.search(task_name)
            if tasks:
                self.recommendation_clicked.emit(tasks[0].task_id)

    def _on_manage_library(self) -> None:
        """管理推荐库"""
        QMessageBox.information(self, "提示", "推荐库管理功能开发中...")

    def set_task(self, task_id: str) -> None:
        """设置当前任务并获取推荐"""
        self.task_input.setText(task_id)
        self._on_recommend()
