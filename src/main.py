# -*- coding: utf-8 -*-
"""
市场咨询任务跟踪工具
Market Task Tracker

程序入口文件
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication

from .config import get_config
from .database.models import init_database
from .utils.logger import get_logger
from .ui.main_window import MainWindow


def setup_environment() -> None:
    """设置运行环境"""
    import os
    
    # 设置Qt平台插件路径
    # CI环境使用offscreen模式，无GUI
    # 生产环境使用windows模式
    if os.environ.get("CI") == "true":
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    else:
        os.environ["QT_QPA_PLATFORM"] = "windows"


def main() -> None:
    """主函数"""
    # 设置运行环境
    setup_environment()

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

        # 初始化自动备份服务
        logger.info("初始化自动备份服务...")
        from .core.auto_backup_service import get_auto_backup_service
        auto_backup_service = get_auto_backup_service()
        auto_backup_service.start()  # 启动自动备份定时器
        logger.info("自动备份服务初始化完成")

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
        logger.exception(f"应用启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
