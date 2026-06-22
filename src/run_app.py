# -*- coding: utf-8 -*-
"""
市场咨询任务跟踪工具
Market Task Tracker

独立程序入口文件
用于 PyInstaller 打包

使用绝对导入，避免打包后相对导入失效
"""

import sys
import os
from pathlib import Path

def setup_environment() -> None:
    """设置运行环境"""
    # 设置Qt平台插件路径
    # CI环境使用offscreen模式，无GUI
    # 生产环境使用windows模式
    if os.environ.get("CI") == "true":
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    else:
        os.environ["QT_QPA_PLATFORM"] = "windows"


def get_application_path() -> Path:
    """获取应用程序路径（兼容 PyInstaller）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 创建的临时文件夹路径
        return Path(sys._MEIPASS)
    else:
        # 正常运行时的脚本路径
        return Path(__file__).parent


def main() -> None:
    """主函数"""
    # 设置运行环境
    setup_environment()

    # 获取应用路径（兼容 PyInstaller）
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后
        app_path = Path(sys._MEIPASS)
        # 将打包后的 src 目录添加到 Python 搜索路径
        sys.path.insert(0, str(app_path / "src"))
    else:
        # 开发环境
        app_path = Path(__file__).parent
        # 将 src 目录添加到 Python 搜索路径
        sys.path.insert(0, str(app_path))

    try:
        # 动态导入，使用 src.* 前缀
        from src.utils.logger import get_logger
        logger = get_logger(__name__)

        logger.info("=" * 50)
        logger.info("市场咨询任务跟踪工具启动")
        logger.info(f"应用路径: {app_path}")
        logger.info("=" * 50)

        # 加载配置
        from src.config import get_config
        config = get_config()
        logger.info(f"应用名称: {config.app_name}")
        logger.info(f"应用版本: {config.app_version}")

        # 初始化数据库
        logger.info("初始化数据库...")
        from src.database.models import init_database
        if not init_database():
            logger.error("数据库初始化失败")
            return
        logger.info("数据库初始化成功")

        # 初始化自动备份服务
        logger.info("初始化自动备份服务...")
        from src.core.auto_backup_service import get_auto_backup_service
        auto_backup_service = get_auto_backup_service()
        auto_backup_service.start()  # 启动自动备份定时器
        logger.info("自动备份服务初始化完成")

        # 创建应用
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
        app.setApplicationName(config.app_name)
        app.setApplicationVersion(config.app_version)

        # 设置应用样式
        app.setStyle("Fusion")

        # 创建主窗口
        logger.info("创建主窗口...")
        from src.ui.main_window import MainWindow
        window = MainWindow()
        window.show()

        logger.info("启动应用...")
        sys.exit(app.exec_())

    except Exception as e:
        try:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.exception(f"应用启动失败: {e}")
        except:
            import traceback
            print(f"应用启动失败: {e}", file=sys.stderr)
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
