# -*- coding: utf-8 -*-
"""
PyInstaller 配置文件
市场咨询任务跟踪工具
版本: V5.3
日期: 2026-06-23
"""

import sys
from pathlib import Path

block_cipher = None

# 项目路径
project_root = Path("d:/AIapple/工具任务跟踪20260611/src/market_task_tracker")

a = Analysis(
    [str(project_root / "src" / "run_app.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # 添加配置文件
        (str(project_root / "config.yaml"), "."),
        # 添加 src 目录（包含所有源代码）
        (str(project_root / "src"), "src"),
        # 添加数据目录
        (str(project_root / "data"), "data"),
        # 添加日志目录
        (str(project_root / "logs"), "logs"),
    ],
    hiddenimports=[
        # PyQt5 GUI框架
        "PyQt5",
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "PyQt5.sip",

        # 数据处理
        "pandas",
        "openpyxl",
        "PIL",
        "PIL.Image",
        "PIL.ImageTk",

        # 配置文件
        "yaml",
        "colorlog",

        # OCR支持
        "pytesseract",

        # 编码检测
        "chardet",

        # 数据库模块 (V5.3)
        "src.database.connection",
        "src.database.models",
        "src.database.er_diagram",
        "src.database.dao_base",

        # 工具模块 (V5.1)
        "src.utils.logger",
        "src.utils.helpers",
        "src.utils.exceptions",
        "src.utils.validators",
        "src.utils.exception_handler",      # 统一异常处理
        "src.utils.data_classes",            # 数据类模块

        # 核心服务模块 (V5.3)
        "src.core.reminder_service",
        "src.core.backup_service",
        "src.core.auto_backup_service",
        "src.core.theme_manager",
        "src.core.learning_service",
        "src.core.wechat_service",
        "src.core.excel_service",
        "src.core.batch_operations",
        "src.core.operation_logger",
        "src.core.content_parser_service",
        "src.core.data_pager",
        "src.core.cache_optimizer",

        # UI模块 (V5.3)
        "src.ui.main_window",
        "src.ui.task_track",
        "src.ui.task_info",
        "src.ui.contacts",
        "src.ui.content_import",
        "src.ui.reminder",
        "src.ui.statistics",
        "src.ui.recommendations",
        "src.ui.dpi_adapter",
        "src.ui.widgets.task_info_widget",
        "src.ui.widgets.task_track_widget",
        "src.ui.widgets.recommendation_widget",
        "src.ui.widgets.notification_widget",
        "src.ui.widgets.reminder_config_widget",
        "src.ui.widgets.auto_backup_config_widget",
        "src.ui.widgets.theme_config_widget",
        "src.ui.widgets.learning_widget",
        "src.ui.widgets.library_widget",     # V5.3新增
        "src.ui.widgets.import_export_widget",
        "src.ui.widgets.statistics_widget",

        # 启动模块
        "src.config",
        "src.main",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "numpy",
        "scipy",
        "IPython",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="MarketTaskTracker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version=None,
    manifest=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MarketTaskTracker",
)
