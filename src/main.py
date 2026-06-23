# -*- coding: utf-8 -*-
"""
市场咨询任务跟踪工具
Market Task Tracker

程序入口文件
"""

import sys
import os
from pathlib import Path

# 设置运行环境
if os.environ.get("CI") == "true":
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
else:
    os.environ["QT_QPA_PLATFORM"] = "windows"

# PyInstaller 打包环境处理
if hasattr(sys, '_MEIPASS'):
    # 打包后的运行环境
    meipass = sys._MEIPASS
    # 将 _internal/src 添加到路径
    src_path = os.path.join(meipass, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    # 设置应用路径
    app_path = Path(meipass).parent
else:
    # 开发环境
    app_path = Path(__file__).parent

from PyQt5.QtWidgets import QApplication
from config import get_config
from database.models import init_database
from utils.logger import get_logger
from ui.main_window import MainWindow


def main():
    """主函数"""
    # 初始化日志
    logger = get_logger(__name__)
    logger.info("=" * 50)
    logger.info("市场咨询任务跟踪工具启动")
    logger.info("=" * 50)

    try:
        # 加载配置
        config = get_config()
        logger.info(f"应用名称: {config.app_name}")
        logger.info(f"应用版本: {config.app_version}")

        # 初始化数据库
        logger.info("初始化数据库...")
        if not init_database():
            logger.error("数据库初始化失败")
            return
        logger.info("数据库初始化成功")

        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName(config.app_name)
        app.setApplicationVersion(config.app_version)

        # 设置应用样式
        app.setStyle("Fusion")

        # 创建主窗口
        logger.info("创建主窗口...")
        window = MainWindow()
        window.show()

        logger.info("启动应用...")
        sys.exit(app.exec_())

    except Exception as e:
        if logger:
            logger.exception(f"应用启动失败: {e}")
        else:
            print(f"应用启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
