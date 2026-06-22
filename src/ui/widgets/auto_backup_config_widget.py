# -*- coding: utf-8 -*-
"""
自动备份配置界面模块
Auto Backup Configuration UI Module

提供自动备份功能的配置界面
"""

from datetime import datetime
from typing import Dict, Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QCheckBox, QComboBox, QSpinBox, QLabel,
    QPushButton, QTimeEdit, QMessageBox, QFormLayout,
    QLineEdit, QTextEdit, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtGui import QFont

from ...core.auto_backup_service import (
    AutoBackupConfig, BackupFrequency, get_auto_backup_service
)
from ...utils.logger import get_logger

logger = get_logger(__name__)


class AutoBackupConfigWidget(QWidget):
    """自动备份配置界面"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.auto_backup_service = get_auto_backup_service()
        self.config = self.auto_backup_service.config
        self._init_ui()
        self._load_config()

    def _init_ui(self) -> None:
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        # 滚动内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # 状态概览
        status_group = self._create_status_group()
        content_layout.addWidget(status_group)

        # 基本设置
        basic_group = self._create_basic_group()
        content_layout.addWidget(basic_group)

        # 备份策略
        strategy_group = self._create_strategy_group()
        content_layout.addWidget(strategy_group)

        # 高级设置
        advanced_group = self._create_advanced_group()
        content_layout.addWidget(advanced_group)

        # 操作按钮
        button_layout = self._create_button_layout()
        content_layout.addLayout(button_layout)

        content_layout.addStretch()

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

    def _create_status_group(self) -> QGroupBox:
        """创建状态概览组"""
        group = QGroupBox("📊 自动备份状态")
        layout = QFormLayout()

        # 启用状态
        self.status_enabled = QLabel("已禁用")
        self.status_enabled.setStyleSheet("color: gray; font-weight: bold;")
        layout.addRow("启用状态:", self.status_enabled)

        # 运行状态
        self.status_running = QLabel("未运行")
        self.status_running.setStyleSheet("color: gray;")
        layout.addRow("运行状态:", self.status_running)

        # 上次备份时间
        self.status_last_backup = QLabel("从未备份")
        layout.addRow("上次备份:", self.status_last_backup)

        # 下次备份时间
        self.status_next_backup = QLabel("未计划")
        layout.addRow("下次备份:", self.status_next_backup)

        # 自动备份次数
        self.status_backup_count = QLabel("0")
        layout.addRow("自动备份次数:", self.status_backup_count)

        group.setLayout(layout)
        return group

    def _create_basic_group(self) -> QGroupBox:
        """创建基本设置组"""
        group = QGroupBox("⚙️ 基本设置")
        layout = QFormLayout()

        # 启用自动备份
        self.enable_checkbox = QCheckBox("启用自动备份功能")
        self.enable_checkbox.stateChanged.connect(self._on_enable_changed)
        layout.addRow("", self.enable_checkbox)

        # 备份时通知
        self.notify_checkbox = QCheckBox("备份完成时发送通知")
        layout.addRow("", self.notify_checkbox)

        # 启动时备份
        self.startup_backup_checkbox = QCheckBox("程序启动时自动备份")
        layout.addRow("", self.startup_backup_checkbox)

        # 关闭时备份
        self.shutdown_backup_checkbox = QCheckBox("程序关闭时自动备份")
        layout.addRow("", self.shutdown_backup_checkbox)

        group.setLayout(layout)
        return group

    def _create_strategy_group(self) -> QGroupBox:
        """创建备份策略组"""
        group = QGroupBox("📅 备份策略")
        layout = QFormLayout()

        # 备份频率
        freq_layout = QHBoxLayout()
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems([
            "每小时",
            "每4小时",
            "每8小时",
            "每天",
            "每周",
            "每月"
        ])
        self.frequency_combo.currentIndexChanged.connect(self._on_frequency_changed)
        freq_layout.addWidget(self.frequency_combo)
        freq_layout.addStretch()
        layout.addRow("备份频率:", self.frequency_combo)

        # 备份时间（仅每日备份时显示）
        time_layout = QHBoxLayout()
        self.backup_time_edit = QTimeEdit()
        self.backup_time_edit.setDisplayFormat("HH:mm")
        self.backup_time_edit.setEnabled(False)
        time_layout.addWidget(self.backup_time_edit)
        time_layout.addStretch()
        layout.addRow("备份时间:", self.backup_time_edit)

        # 保留数量
        keep_layout = QHBoxLayout()
        self.keep_count_spin = QSpinBox()
        self.keep_count_spin.setMinimum(1)
        self.keep_count_spin.setMaximum(30)
        self.keep_count_spin.setSuffix(" 个")
        keep_layout.addWidget(self.keep_count_spin)
        keep_layout.addStretch()
        layout.addRow("保留备份数:", self.keep_count_spin)

        # 提示标签
        hint_label = QLabel("注：超过保留数量的旧备份将自动删除")
        hint_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addRow("", hint_label)

        group.setLayout(layout)
        return group

    def _create_advanced_group(self) -> QGroupBox:
        """创建高级设置组"""
        group = QGroupBox("🔧 高级设置")
        group.setCheckable(True)
        group.setChecked(False)
        layout = QFormLayout()

        # 最大备份大小
        size_layout = QHBoxLayout()
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setMinimum(10)
        self.max_size_spin.setMaximum(1000)
        self.max_size_spin.setSuffix(" MB")
        size_layout.addWidget(self.max_size_spin)
        size_layout.addStretch()
        layout.addRow("最大备份大小:", self.max_size_spin)

        # 压缩级别
        compress_layout = QHBoxLayout()
        self.compression_spin = QSpinBox()
        self.compression_spin.setMinimum(0)
        self.compression_spin.setMaximum(9)
        compress_layout.addWidget(self.compression_spin)
        compress_layout.addWidget(QLabel("(0=不压缩, 9=最大压缩)"))
        compress_layout.addStretch()
        layout.addRow("压缩级别:", self.compression_spin)

        # 包含日志
        self.include_logs_checkbox = QCheckBox("备份时包含日志文件")
        layout.addRow("", self.include_logs_checkbox)

        group.setLayout(layout)
        return group

    def _create_button_layout(self) -> QHBoxLayout:
        """创建按钮布局"""
        layout = QHBoxLayout()

        # 手动备份按钮
        backup_btn = QPushButton("🆕 立即备份")
        backup_btn.clicked.connect(self._on_manual_backup)
        layout.addWidget(backup_btn)

        # 恢复默认按钮
        reset_btn = QPushButton("🔄 恢复默认")
        reset_btn.clicked.connect(self._on_reset_config)
        layout.addWidget(reset_btn)

        # 保存按钮
        save_btn = QPushButton("💾 保存设置")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        save_btn.clicked.connect(self._on_save_config)
        layout.addWidget(save_btn)

        layout.addStretch()
        return layout

    def _frequency_text_to_value(self, text: str) -> str:
        """将频率文本转换为枚举值"""
        mapping = {
            "每小时": BackupFrequency.EVERY_HOUR.value,
            "每4小时": BackupFrequency.EVERY_4_HOURS.value,
            "每8小时": BackupFrequency.EVERY_8_HOURS.value,
            "每天": BackupFrequency.DAILY.value,
            "每周": BackupFrequency.WEEKLY.value,
            "每月": BackupFrequency.MONTHLY.value,
        }
        return mapping.get(text, BackupFrequency.DAILY.value)

    def _frequency_value_to_text(self, value: str) -> str:
        """将频率枚举值转换为文本"""
        mapping = {
            BackupFrequency.EVERY_HOUR.value: "每小时",
            BackupFrequency.EVERY_4_HOURS.value: "每4小时",
            BackupFrequency.EVERY_8_HOURS.value: "每8小时",
            BackupFrequency.EVERY_8_HOURS.value: "每8小时",
            BackupFrequency.DAILY.value: "每天",
            BackupFrequency.WEEKLY.value: "每周",
            BackupFrequency.MONTHLY.value: "每月",
        }
        return mapping.get(value, "每天")

    def _load_config(self) -> None:
        """加载配置"""
        try:
            config = self.config.to_dict()

            # 基本设置
            self.enable_checkbox.setChecked(config.get("enabled", False))
            self.notify_checkbox.setChecked(config.get("notify_on_backup", True))
            self.startup_backup_checkbox.setChecked(config.get("backup_on_startup", True))
            self.shutdown_backup_checkbox.setChecked(config.get("backup_on_shutdown", True))

            # 备份策略
            frequency_text = self._frequency_value_to_text(config.get("frequency", "daily"))
            index = self.frequency_combo.findText(frequency_text)
            if index >= 0:
                self.frequency_combo.setCurrentIndex(index)

            backup_time = config.get("backup_time", "02:00")
            time_parts = backup_time.split(":")
            self.backup_time_edit.setTime(QTime(int(time_parts[0]), int(time_parts[1])))

            self.keep_count_spin.setValue(config.get("keep_count", 7))

            # 高级设置
            self.max_size_spin.setValue(config.get("max_backup_size_mb", 100))
            self.compression_spin.setValue(config.get("compression_level", 6))
            self.include_logs_checkbox.setChecked(config.get("include_logs", False))

            # 更新状态显示
            self._update_status_display()

        except Exception as e:
            logger.error(f"加载配置失败: {e}")

    def _update_status_display(self) -> None:
        """更新状态显示"""
        status = self.auto_backup_service.get_status()

        # 启用状态
        if status["enabled"]:
            self.status_enabled.setText("已启用")
            self.status_enabled.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_enabled.setText("已禁用")
            self.status_enabled.setStyleSheet("color: gray; font-weight: bold;")

        # 运行状态
        if status["running"]:
            self.status_running.setText("运行中")
            self.status_running.setStyleSheet("color: blue;")
        else:
            self.status_running.setText("未运行")
            self.status_running.setStyleSheet("color: gray;")

        # 上次备份
        last_time = status.get("last_backup_time")
        if last_time:
            try:
                dt = datetime.fromisoformat(last_time)
                self.status_last_backup.setText(dt.strftime("%Y-%m-%d %H:%M"))
            except Exception:
                self.status_last_backup.setText(last_time)
        else:
            self.status_last_backup.setText("从未备份")

        # 下次备份
        next_time = status.get("next_backup_time")
        if next_time and status["enabled"]:
            try:
                dt = datetime.fromisoformat(next_time)
                self.status_next_backup.setText(dt.strftime("%Y-%m-%d %H:%M"))
            except Exception:
                self.status_next_backup.setText(next_time)
        else:
            self.status_next_backup.setText("未计划")

        # 备份次数
        self.status_backup_count.setText(str(status.get("auto_backup_count", 0)))

    def _on_enable_changed(self, state: int) -> None:
        """启用状态改变"""
        enabled = state == Qt.Checked

        # 启用/禁用相关控件
        self.frequency_combo.setEnabled(enabled)
        self.keep_count_spin.setEnabled(enabled)
        self.notify_checkbox.setEnabled(enabled)
        self.startup_backup_checkbox.setEnabled(enabled)
        self.shutdown_backup_checkbox.setEnabled(enabled)

    def _on_frequency_changed(self, index: int) -> None:
        """频率改变"""
        # 如果选择的是每天，启用时间选择器
        frequency_text = self.frequency_combo.currentText()
        is_daily = frequency_text in ["每天", "每周", "每月"]
        self.backup_time_edit.setEnabled(is_daily)

    def _on_manual_backup(self) -> None:
        """手动备份"""
        reply = QMessageBox.question(
            self,
            "确认备份",
            "确定要立即创建备份吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success = self.auto_backup_service.trigger_backup("手动触发")
            if success:
                QMessageBox.information(self, "成功", "备份创建成功！")
                self._update_status_display()
            else:
                QMessageBox.warning(self, "失败", "备份创建失败！")

    def _on_reset_config(self) -> None:
        """恢复默认配置"""
        reply = QMessageBox.question(
            self,
            "确认恢复",
            "确定要恢复默认配置吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 重置为默认配置
            default_config = AutoBackupConfig.DEFAULT_CONFIG.copy()
            self.config.config = default_config
            self.config.save()
            self._load_config()
            QMessageBox.information(self, "成功", "已恢复默认配置！")

    def _on_save_config(self) -> None:
        """保存配置"""
        try:
            config_dict = {
                "enabled": self.enable_checkbox.isChecked(),
                "frequency": self._frequency_text_to_value(self.frequency_combo.currentText()),
                "backup_time": self.backup_time_edit.time().toString("HH:mm"),
                "keep_count": self.keep_count_spin.value(),
                "max_backup_size_mb": self.max_size_spin.value(),
                "notify_on_backup": self.notify_checkbox.isChecked(),
                "backup_on_startup": self.startup_backup_checkbox.isChecked(),
                "backup_on_shutdown": self.shutdown_backup_checkbox.isChecked(),
                "compression_level": self.compression_spin.value(),
                "include_logs": self.include_logs_checkbox.isChecked(),
            }

            if self.auto_backup_service.update_config(config_dict):
                QMessageBox.information(self, "成功", "配置已保存！")
                self._update_status_display()
            else:
                QMessageBox.warning(self, "失败", "配置保存失败！")

        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            QMessageBox.warning(self, "错误", f"保存配置失败: {e}")

    def refresh(self) -> None:
        """刷新状态"""
        self._load_config()
