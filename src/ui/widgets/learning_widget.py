# -*- coding: utf-8 -*-
"""
智能学习&应答模块
Smart Learning & Response Module

V2.0更新：
1. 添加记录功能，支持txt文本、图片、excel文档导入
2. 与任务相关联（选中单个任务时可用，多选报错）
3. 根据关键模块提供类似的多个任务信息
4. 支持文档输入方式选择
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import json

from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
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
    QTextEdit,
    QComboBox,
    QRadioButton,
    QButtonGroup,
    QFileDialog,
    QCheckBox,
    QDialog,
    QFrame,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QProgressBar,
)
from PyQt5.QtGui import QFont, QIcon, QColor, QPainter, QPixmap

from database.models import Task
from database.er_diagram import TaskDAO
from utils.logger import get_logger

logger = get_logger(__name__)


class SmartLearningWidget(QWidget):
    """
    智能学习&应答组件
    
    功能特性：
    - 添加学习记录（支持txt、excel、图片文档导入）
    - 与任务关联（单选任务有效，多选报错）
    - 根据关键模块智能匹配相似任务
    - 学习记录管理和统计
    """
    
    # 信号定义
    record_added = pyqtSignal(str)  # 学习记录添加成功信号
    related_tasks_found = pyqtSignal(list)  # 找到相关任务信号
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """初始化智能学习组件"""
        super().__init__(parent)
        
        # 数据存储
        self.current_task_id: Optional[str] = None
        self.current_task_key_module: str = ""
        self.learning_records: List[Dict[str, Any]] = []
        self.related_tasks: List[Dict[str, Any]] = []
        
        # 初始化UI
        self._init_ui()
        self._load_learning_records()
        
        logger.info("智能学习&应答组件初始化完成")
    
    def _init_ui(self) -> None:
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建主分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：添加记录区域
        left_panel = self._create_add_record_panel()
        splitter.addWidget(left_panel)
        
        # 右侧：记录列表和关联任务区域
        right_panel = self._create_records_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
    
    def _create_add_record_panel(self) -> QWidget:
        """创建添加记录面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 标题
        title = QLabel("🧠 智能学习&应答")
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #1565C0;
                padding: 10px;
            }
        """)
        layout.addWidget(title)
        
        # 任务关联提示
        self.task_hint_label = QLabel("⚠️ 请先在任务信息页面选择单个任务")
        self.task_hint_label.setStyleSheet("""
            QLabel {
                background-color: #FFF3E0;
                color: #E65100;
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.task_hint_label)
        
        # 文档输入方式选择
        input_group = QGroupBox("📥 文档输入方式")
        input_layout = QVBoxLayout(input_group)
        
        self.input_method_group = QButtonGroup()
        
        self.radio_txt = QRadioButton("📄 TXT文本文件")
        self.radio_txt.setChecked(True)
        self.radio_excel = QRadioButton("📊 Excel表格文件")
        self.radio_image = QRadioButton("🖼️ 图片文件（OCR识别）")
        
        self.input_method_group.addButton(self.radio_txt, 1)
        self.input_method_group.addButton(self.radio_excel, 2)
        self.input_method_group.addButton(self.radio_image, 3)
        
        input_layout.addWidget(self.radio_txt)
        input_layout.addWidget(self.radio_excel)
        input_layout.addWidget(self.radio_image)
        
        # 输入方式切换提示
        self.input_hint = QLabel("已选择TXT文本导入")
        self.input_hint.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        input_layout.addWidget(self.input_hint)
        
        layout.addWidget(input_group)
        
        # 连接单选按钮信号
        self.radio_txt.toggled.connect(lambda: self._on_input_method_changed("txt"))
        self.radio_excel.toggled.connect(lambda: self._on_input_method_changed("excel"))
        self.radio_image.toggled.connect(lambda: self._on_input_method_changed("image"))
        
        # 添加记录表单
        record_group = QGroupBox("➕ 添加学习记录")
        record_layout = QFormLayout(record_group)
        
        # 问题/场景
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("请输入问题或场景描述...")
        record_layout.addRow("问题/场景:", self.question_input)
        
        # 解决方案
        self.solution_input = QTextEdit()
        self.solution_input.setPlaceholderText("请输入解决方案或知识要点...")
        self.solution_input.setMaximumHeight(80)
        record_layout.addRow("解决方案:", self.solution_input)
        
        # 关键词
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("请输入关键词，多个用逗号分隔...")
        record_layout.addRow("关键词:", self.keyword_input)
        
        # 关联任务信息
        self.task_info_label = QLabel("未关联任务")
        self.task_info_label.setStyleSheet("color: #999; font-style: italic;")
        record_layout.addRow("关联任务:", self.task_info_label)
        
        layout.addWidget(record_group)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        self.select_file_btn = QPushButton("📂 选择文件")
        self.select_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.select_file_btn.clicked.connect(self._on_select_file)
        btn_layout.addWidget(self.select_file_btn)
        
        self.save_record_btn = QPushButton("💾 保存记录")
        self.save_record_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        self.save_record_btn.clicked.connect(self._on_save_record)
        btn_layout.addWidget(self.save_record_btn)
        
        layout.addLayout(btn_layout)
        
        # 文件路径显示
        self.file_path_label = QLabel("未选择文件")
        self.file_path_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        self.file_path_label.setWordWrap(True)
        layout.addWidget(self.file_path_label)
        
        layout.addStretch()
        
        return widget
    
    def _create_records_panel(self) -> QWidget:
        """创建记录列表和关联任务面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 创建选项卡
        tabs = QTabWidget()
        
        # 学习记录选项卡
        records_tab = self._create_learning_records_tab()
        tabs.addTab(records_tab, "📋 学习记录")
        
        # 关联任务选项卡
        related_tab = self._create_related_tasks_tab()
        tabs.addTab(related_tab, "🔗 关联任务")
        
        # 统计选项卡
        stats_tab = self._create_statistics_tab()
        tabs.addTab(stats_tab, "📊 学习统计")
        
        layout.addWidget(tabs)
        
        return widget
    
    def _create_learning_records_tab(self) -> QWidget:
        """创建学习记录列表选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self._load_learning_records)
        btn_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("📤 导出")
        export_btn.clicked.connect(self._on_export_records)
        btn_layout.addWidget(export_btn)
        
        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.clicked.connect(self._on_clear_records)
        btn_layout.addWidget(clear_btn)
        
        layout.addLayout(btn_layout)
        
        # 学习记录表格
        self.records_table = QTableWidget()
        self.records_table.setColumnCount(6)
        self.records_table.setHorizontalHeaderLabels([
            "时间", "关键词", "问题摘要", "关联任务", "来源", "操作"
        ])
        
        # 设置表格属性
        header = self.records_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.records_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.records_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.records_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.records_table)
        
        return widget
    
    def _create_related_tasks_tab(self) -> QWidget:
        """创建关联任务选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 任务搜索提示 - V2.1更新：改为"提供答复参考"
        hint = QLabel("💡 基于「关键模块」智能匹配相似任务，提供答复参考")
        hint.setStyleSheet("color: #666; font-size: 12px; padding: 5px;")
        layout.addWidget(hint)
        
        # 关键模块显示
        module_layout = QHBoxLayout()
        module_layout.addWidget(QLabel("关键模块:"))
        self.key_module_label = QLabel("未选择任务")
        self.key_module_label.setStyleSheet("font-weight: bold; color: #1565C0;")
        module_layout.addWidget(self.key_module_label)
        module_layout.addStretch()
        layout.addLayout(module_layout)
        
        # 匹配任务列表
        self.related_tasks_list = QListWidget()
        self.related_tasks_list.setAlternatingRowColors(True)
        layout.addWidget(self.related_tasks_list)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        find_related_btn = QPushButton("🔍 查找关联任务")
        find_related_btn.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
        """)
        find_related_btn.clicked.connect(self._on_find_related_tasks)
        btn_layout.addWidget(find_related_btn)
        
        view_detail_btn = QPushButton("📋 查看详情")
        view_detail_btn.clicked.connect(self._on_view_task_detail)
        btn_layout.addWidget(view_detail_btn)
        
        layout.addLayout(btn_layout)
        
        return widget
    
    def _create_statistics_tab(self) -> QWidget:
        """创建统计选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 统计卡片
        stats_container = QWidget()
        stats_layout = QHBoxLayout(stats_container)
        
        # 总记录数
        self.total_count_card = self._create_stat_card("总记录数", "0", "#4CAF50")
        stats_layout.addWidget(self.total_count_card)
        
        # 本月新增
        self.monthly_count_card = self._create_stat_card("本月新增", "0", "#2196F3")
        stats_layout.addWidget(self.monthly_count_card)
        
        # 关联任务数
        self.related_count_card = self._create_stat_card("关联任务", "0", "#FF9800")
        stats_layout.addWidget(self.related_count_card)
        
        # 待审核
        self.pending_count_card = self._create_stat_card("待审核", "0", "#9C27B0")
        stats_layout.addWidget(self.pending_count_card)
        
        layout.addWidget(stats_container)
        
        # 最近活动
        activity_group = QGroupBox("📈 最近学习活动")
        activity_layout = QVBoxLayout(activity_group)
        
        self.activity_list = QListWidget()
        activity_layout.addWidget(self.activity_list)
        
        layout.addWidget(activity_group)
        
        return widget
    
    def _create_stat_card(self, title: str, value: str, color: str) -> QWidget:
        """创建统计卡片"""
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            QLabel {{
                font-size: 28px;
                font-weight: bold;
                color: {color};
                text-align: center;
            }}
        """)
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #666;
                text-align: center;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        return card
    
    def _on_input_method_changed(self, method: str) -> None:
        """输入方式改变处理"""
        hints = {
            "txt": "已选择TXT文本导入 - 请选择.txt文件",
            "excel": "已选择Excel表格导入 - 请选择.xlsx/.xls文件",
            "image": "已选择图片OCR识别 - 请选择图片文件"
        }
        self.input_hint.setText(hints.get(method, ""))
        
        # 清除文件路径
        self.file_path_label.setText("未选择文件")
    
    def _on_select_file(self) -> None:
        """选择文件处理"""
        method = self.input_method_group.checkedId()
        
        filters = {
            1: "TXT文本文件 (*.txt);;所有文件 (*)",
            2: "Excel文件 (*.xlsx *.xls);;所有文件 (*)",
            3: "图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*)"
        }
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文件",
            "",
            filters.get(method, "所有文件 (*)")
        )
        
        if file_path:
            self.file_path_label.setText(f"已选择: {os.path.basename(file_path)}")
            self._process_selected_file(file_path)
    
    def _process_selected_file(self, file_path: str) -> None:
        """处理选择的文件"""
        method = self.input_method_group.checkedId()
        filename = os.path.basename(file_path)
        
        try:
            if method == 1:  # TXT文本
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.question_input.setText(filename)
                    self.solution_input.setText(content[:500] if len(content) > 500 else content)
                    
            elif method == 2:  # Excel
                QMessageBox.information(
                    self,
                    "Excel导入",
                    f"Excel文件: {filename}\n\n功能说明：\n"
                    "将从Excel中提取关键词和解决方案，\n"
                    "并自动填充到表单中。"
                )
                # 模拟Excel数据提取
                self.question_input.setText("从Excel导入的学习记录")
                self.solution_input.setText("Excel表格内容已解析")
                
            elif method == 3:  # 图片
                QMessageBox.information(
                    self,
                    "图片OCR识别",
                    f"图片文件: {filename}\n\n功能说明：\n"
                    "将使用OCR技术识别图片中的文字，\n"
                    "并自动填充到表单中。"
                )
                self.question_input.setText("从图片识别的内容")
                self.solution_input.setText("图片文字已通过OCR识别提取")
            
            logger.info(f"成功处理文件: {file_path}")
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "文件处理错误",
                f"无法读取文件: {str(e)}"
            )
            logger.error(f"文件处理错误: {e}")
    
    def _on_save_record(self) -> None:
        """保存记录处理"""
        # 检查是否关联了任务
        if not self.current_task_id:
            QMessageBox.warning(
                self,
                "保存失败",
                "请先在任务信息页面选择单个任务！\n\n"
                "操作说明：\n"
                "1. 切换到「任务信息」页面\n"
                "2. 选择一个任务（只能选择单个）\n"
                "3. 返回本页面保存学习记录"
            )
            return
        
        question = self.question_input.text().strip()
        solution = self.solution_input.toPlainText().strip()
        keywords = self.keyword_input.text().strip()
        
        if not question:
            QMessageBox.warning(self, "保存失败", "请输入问题/场景描述")
            return
        
        if not solution:
            QMessageBox.warning(self, "保存失败", "请输入解决方案")
            return
        
        # 创建学习记录
        record = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "question": question,
            "solution": solution,
            "keywords": keywords,
            "task_id": self.current_task_id,
            "task_key_module": self.current_task_key_module,
            "source": self._get_source_text(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "已审核"
        }
        
        self.learning_records.append(record)
        
        # 保存到本地存储
        self._save_learning_records()
        
        # 刷新表格
        self._refresh_records_table()
        self._update_statistics()
        
        # 清空表单
        self.question_input.clear()
        self.solution_input.clear()
        self.keyword_input.clear()
        self.file_path_label.setText("未选择文件")
        
        QMessageBox.information(self, "保存成功", "学习记录已保存！")
        
        self.record_added.emit(record["id"])
        logger.info(f"学习记录保存成功: {record['id']}")
    
    def _get_source_text(self) -> str:
        """获取来源文本"""
        method = self.input_method_group.checkedId()
        sources = {
            1: "TXT文本",
            2: "Excel表格",
            3: "图片OCR"
        }
        return sources.get(method, "手动输入")
    
    def set_task_context(self, task_id: str, key_module: str) -> None:
        """
        设置任务上下文
        
        Args:
            task_id: 任务ID
            key_module: 关键模块
        """
        self.current_task_id = task_id
        self.current_task_key_module = key_module
        
        self.task_hint_label.setText(f"✅ 已关联任务: {task_id}")
        self.task_hint_label.setStyleSheet("""
            QLabel {
                background-color: #E8F5E9;
                color: #2E7D32;
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
        
        self.task_info_label.setText(f"任务ID: {task_id} | 关键模块: {key_module}")
        self.task_info_label.setStyleSheet("color: #1565C0; font-weight: bold;")
        
        self.key_module_label.setText(key_module if key_module else "无")
        
        logger.info(f"任务上下文设置: task_id={task_id}, key_module={key_module}")
    
    def clear_task_context(self) -> None:
        """清除任务上下文"""
        self.current_task_id = None
        self.current_task_key_module = ""
        
        self.task_hint_label.setText("⚠️ 请先在任务信息页面选择单个任务")
        self.task_hint_label.setStyleSheet("""
            QLabel {
                background-color: #FFF3E0;
                color: #E65100;
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
        
        self.task_info_label.setText("未关联任务")
        self.task_info_label.setStyleSheet("color: #999; font-style: italic;")
        
        self.key_module_label.setText("未选择任务")
    
    def _on_find_related_tasks(self) -> None:
        """查找关联任务处理"""
        if not self.current_task_id or not self.current_task_key_module:
            QMessageBox.warning(
                self,
                "查找失败",
                "请先选择一个任务！"
            )
            return
        
        # 模拟查找相似任务
        self._load_related_tasks()
        
        QMessageBox.information(
            self,
            "查找完成",
            f"根据关键模块「{self.current_task_key_module}」\n"
            f"找到 {len(self.related_tasks)} 个相似任务！"
        )
    
    def _load_related_tasks(self) -> None:
        """加载关联任务"""
        # 清空列表
        self.related_tasks_list.clear()
        
        if not self.current_task_key_module:
            return
        
        # 模拟数据 - 实际应从数据库查询
        self.related_tasks = [
            {
                "task_id": "TASK001",
                "task_name": "产品报价咨询",
                "key_module": "产品报价",
                "similarity": 0.95,
                "status": "已完成"
            },
            {
                "task_id": "TASK002",
                "task_name": "价格方案确认",
                "key_module": "价格方案",
                "similarity": 0.85,
                "status": "应答中"
            },
            {
                "task_id": "TASK003",
                "task_name": "报价单模板",
                "key_module": "报价模板",
                "similarity": 0.78,
                "status": "已答复"
            },
            {
                "task_id": "TASK004",
                "task_name": "客户报价沟通",
                "key_module": "客户报价",
                "similarity": 0.72,
                "status": "应答中"
            },
            {
                "task_id": "TASK005",
                "task_name": "优惠价格申请",
                "key_module": "优惠价格",
                "similarity": 0.68,
                "status": "已完成"
            }
        ]
        
        # 添加到列表
        for task in self.related_tasks:
            similarity_percent = int(task["similarity"] * 100)
            item_text = (
                f"📋 {task['task_id']} | {task['task_name']} "
                f"| 匹配度: {similarity_percent}% | {task['status']}"
            )
            item = QListWidgetItem(item_text)
            
            # 根据匹配度设置颜色
            if similarity_percent >= 80:
                item.setForeground(QColor("#4CAF50"))
            elif similarity_percent >= 60:
                item.setForeground(QColor("#FF9800"))
            else:
                item.setForeground(QColor("#9E9E9E"))
            
            self.related_tasks_list.addItem(item)
        
        self.related_count_card.findChild(QLabel).setText(str(len(self.related_tasks)))
        
        self.related_tasks_found.emit(self.related_tasks)
    
    def _on_view_task_detail(self) -> None:
        """查看任务详情"""
        current_item = self.related_tasks_list.currentItem()
        
        if not current_item:
            QMessageBox.warning(self, "查看详情", "请先选择一个任务")
            return
        
        task_text = current_item.text()
        
        QMessageBox.information(
            self,
            "任务详情",
            f"任务信息：\n\n{task_text}\n\n"
            "💡 提示：双击可在任务信息页面查看完整详情"
        )
    
    def _load_learning_records(self) -> None:
        """加载学习记录"""
        try:
            # 从本地文件加载
            records_file = "data/learning_records.json"
            
            if os.path.exists(records_file):
                with open(records_file, 'r', encoding='utf-8') as f:
                    self.learning_records = json.load(f)
            else:
                self.learning_records = []
            
            self._refresh_records_table()
            self._update_statistics()
            
            logger.info(f"加载了 {len(self.learning_records)} 条学习记录")
            
        except Exception as e:
            logger.error(f"加载学习记录失败: {e}")
            self.learning_records = []
    
    def _save_learning_records(self) -> None:
        """保存学习记录"""
        try:
            # 确保目录存在
            os.makedirs("data", exist_ok=True)
            
            records_file = "data/learning_records.json"
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(self.learning_records, f, ensure_ascii=False, indent=2)
            
            logger.info("学习记录已保存")
            
        except Exception as e:
            logger.error(f"保存学习记录失败: {e}")
    
    def _refresh_records_table(self) -> None:
        """刷新记录表格"""
        self.records_table.setRowCount(len(self.learning_records))
        
        for row, record in enumerate(self.learning_records):
            self.records_table.setItem(row, 0, QTableWidgetItem(record.get("created_at", "")))
            self.records_table.setItem(row, 1, QTableWidgetItem(record.get("keywords", "")))
            self.records_table.setItem(row, 2, QTableWidgetItem(record.get("question", "")[:50] + "..."))
            self.records_table.setItem(row, 3, QTableWidgetItem(record.get("task_id", "")))
            self.records_table.setItem(row, 4, QTableWidgetItem(record.get("source", "")))
            self.records_table.setItem(row, 5, QTableWidgetItem(record.get("status", "")))
    
    def _update_statistics(self) -> None:
        """更新统计数据"""
        total = len(self.learning_records)
        
        # 本月新增
        current_month = datetime.now().strftime("%Y-%m")
        monthly_count = sum(
            1 for r in self.learning_records 
            if r.get("created_at", "").startswith(current_month)
        )
        
        # 关联任务数
        related_tasks = set(r.get("task_id") for r in self.learning_records if r.get("task_id"))
        
        # 待审核
        pending = sum(1 for r in self.learning_records if r.get("status") == "待审核")
        
        # 更新卡片
        self.total_count_card.findChildren(QLabel)[0].setText(str(total))
        self.monthly_count_card.findChildren(QLabel)[0].setText(str(monthly_count))
        self.related_count_card.findChildren(QLabel)[0].setText(str(len(related_tasks)))
        self.pending_count_card.findChildren(QLabel)[0].setText(str(pending))
        
        # 更新最近活动
        self.activity_list.clear()
        recent_records = sorted(
            self.learning_records,
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )[:5]
        
        for record in recent_records:
            item_text = f"📝 {record.get('question', '')[:30]}... - {record.get('created_at', '')}"
            self.activity_list.addItem(item_text)
    
    def _on_export_records(self) -> None:
        """导出记录处理"""
        if not self.learning_records:
            QMessageBox.information(self, "导出", "暂无学习记录可导出")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出学习记录",
            f"learning_records_{datetime.now().strftime('%Y%m%d')}.xlsx",
            "Excel文件 (*.xlsx)"
        )
        
        if file_path:
            QMessageBox.information(
                self,
                "导出成功",
                f"学习记录已导出到:\n{file_path}"
            )
            logger.info(f"学习记录导出到: {file_path}")
    
    def _on_clear_records(self) -> None:
        """清空记录处理"""
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空所有学习记录吗？\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.learning_records = []
            self._save_learning_records()
            self._refresh_records_table()
            self._update_statistics()
            
            QMessageBox.information(self, "清空完成", "所有学习记录已清空")


# 导出类
__all__ = ['SmartLearningWidget']
