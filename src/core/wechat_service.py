# -*- coding: utf-8 -*-
"""
企业微信集成服务模块
WeChat Integration Service Module:

提供企业微信Webhook消息推送功能
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

import requests

from ..database.connection import get_db_connection
from ..utils.logger import get_logger
from ..utils.exception_handler import (
    safe_execute,
    handle_network_error,
    NetworkException,
    ServiceException
)

logger = get_logger(__name__)


class WeChatService:
    """企业微信服务类"""

    # Webhook URL存储文件
    CONFIG_FILE = "wechat_config.json"

    # 紧急程度表情映射
    URGENCY_EMOJI_MAP = {"高": "🔴", "中": "🟡", "低": "🟢"}

    def __init__(self):
        """初始化企业微信服务"""
        self.db = get_db_connection()
        self.webhook_url: Optional[str] = None
        self.enabled = False
        self._load_config()

    def _load_config(self) -> None:
        """加载配置"""
        try:
            config_path = Path(self.CONFIG_FILE)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.webhook_url = config.get("webhook_url", "")
                    self.enabled = config.get("enabled", False)
            else:
                self._init_config_table()
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}")
        except OSError as e:
            logger.error(f"读取配置文件失败: {e}")
        except Exception as e:
            logger.error(f"加载企业微信配置失败: {e}")

    def _init_config_table(self) -> None:
        """初始化配置表"""
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS wechat_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key VARCHAR(50) NOT NULL UNIQUE,
                config_value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            commit=True
        )

        # 插入默认配置
        self.db.execute(
            "INSERT OR IGNORE INTO wechat_config (config_key, config_value) VALUES ('webhook_url', '')",
            commit=True
        )
        self.db.execute(
            "INSERT OR IGNORE INTO wechat_config (config_key, config_value) VALUES ('enabled', 'false')",
            commit=True
        )

    def _save_config(self) -> bool:
        """保存配置"""
        try:
            # 保存到数据库
            self.db.execute(
                "INSERT OR REPLACE INTO wechat_config (config_key, config_value) VALUES ('webhook_url', ?)",
                (self.webhook_url or "",),
                commit=True
            )
            self.db.execute(
                "INSERT OR REPLACE INTO wechat_config (config_key, config_value) VALUES ('enabled', ?)",
                ("true" if self.enabled else "false",),
                commit=True
            )

            # 保存到文件
            config_path = Path(self.CONFIG_FILE)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "webhook_url": self.webhook_url,
                    "enabled": self.enabled
                }, f, ensure_ascii=False, indent=2)

            logger.info("企业微信配置已保存")
            return True

        except (OSError, IOError) as e:
            logger.error(f"写入配置文件失败: {e}")
            return False
        except Exception as e:
            logger.error(f"保存企业微信配置失败: {e}")
            return False

    def set_webhook_url(self, webhook_url: str) -> bool:
        """设置Webhook URL"""
        if not webhook_url or not webhook_url.startswith("https://"):
            logger.error("Webhook URL格式不正确")
            return False

        self.webhook_url = webhook_url
        return self._save_config()

    def set_enabled(self, enabled: bool) -> bool:
        """设置启用状态"""
        self.enabled = enabled
        return self._save_config()

    def is_configured(self) -> bool:
        """检查是否已配置"""
        return bool(self.webhook_url and self.webhook_url.startswith("https://"))

    def _build_reminder_content(self, task_data: Dict[str, Any]) -> str:
        """构建提醒消息内容"""
        urgency = task_data.get("urgency", "中")
        urgency_emoji = self.URGENCY_EMOJI_MAP.get(urgency, "⚪")
        task_content = task_data.get('task_content', '无')[:100]

        return f"""## ⏰ 任务提醒

{urgency_emoji} **重要程度**: {urgency}
📋 **任务名称**: {task_data.get('task_name', '')}
👤 **责任人**: {task_data.get('respondent', '未指定')}
🏷️ **关键模块**: {task_data.get('key_module', '未指定')}
📝 **任务内容**: {task_content}...
🕐 **提醒时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

> 请及时处理！"""

    @safe_execute(default_return=False, log_errors=True)
    def send_reminder_message(self, task_data: Dict[str, Any]) -> bool:
        """发送任务提醒消息"""
        if not self.enabled or not self.is_configured():
            logger.warning("企业微信未启用或未配置")
            return False

        urgency = task_data.get("urgency", "中")
        urgency_emoji = self.URGENCY_EMOJI_MAP.get(urgency, "⚪")

        message = {
            "msgtype": "markdown",
            "markdown": {
                "content": self._build_reminder_content(task_data)
            }
        }

        return self._send_message(message)

    def _build_task_created_content(self, task_data: Dict[str, Any]) -> str:
        """构建新任务创建消息内容"""
        urgency = task_data.get("urgency", "中")
        urgency_emoji = self.URGENCY_EMOJI_MAP.get(urgency, "⚪")

        return f"""## 🆕 新任务创建

📋 **任务名称**: {task_data.get('task_name', '')}
👤 **咨询者**: {task_data.get('inquirer', '未指定')}
{urgency_emoji} **重要程度**: {urgency}
📅 **创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

> 新任务已创建，请查看详情！"""

    @safe_execute(default_return=False, log_errors=True)
    def send_task_created_message(self, task_data: Dict[str, Any]) -> bool:
        """发送新任务通知"""
        if not self.enabled or not self.is_configured():
            return False

        message = {
            "msgtype": "markdown",
            "markdown": {
                "content": self._build_task_created_content(task_data)
            }
        }

        return self._send_message(message)

    def _build_task_replied_content(self, task_data: Dict[str, Any]) -> str:
        """构建任务答复消息内容"""
        return f"""## ✅ 任务已答复

📋 **任务名称**: {task_data.get('task_name', '')}
👤 **咨询者**: {task_data.get('inquirer', '未指定')}
👤 **答复人**: {task_data.get('respondent', '未指定')}
📅 **答复时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

> 任务已得到答复，请确认！"""

    @safe_execute(default_return=False, log_errors=True)
    def send_task_replied_message(self, task_data: Dict[str, Any]) -> bool:
        """发送任务已答复通知"""
        if not self.enabled or not self.is_configured():
            return False

        message = {
            "msgtype": "markdown",
            "markdown": {
                "content": self._build_task_replied_content(task_data)
            }
        }

        return self._send_message(message)

    @handle_network_error(default_return=False, retry_count=2)
    def _send_message(self, message: Dict) -> bool:
        """发送消息到企业微信"""
        if not self.webhook_url:
            logger.error("Webhook URL未设置")
            return False

        response = requests.post(
            self.webhook_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(message),
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("errcode") == 0:
                logger.info("企业微信消息发送成功")
                return True
            else:
                logger.error(f"企业微信返回错误: {result.get('errmsg')}")
                return False
        else:
            logger.error(f"企业微信请求失败: {response.status_code}")
            return False

    def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        if not self.is_configured():
            return {
                "success": False,
                "message": "Webhook URL未配置"
            }

        try:
            # 发送测试消息
            test_message = {
                "msgtype": "text",
                "text": {
                    "content": "🔔 市场咨询任务跟踪工具连接测试\n\n企业微信Webhook配置成功！"
                }
            }

            response = requests.post(
                self.webhook_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(test_message),
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("errcode") == 0:
                    return {
                        "success": True,
                        "message": "连接测试成功！"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"测试失败: {result.get('errmsg')}"
                    }
            else:
                return {
                    "success": False,
                    "message": f"HTTP错误: {response.status_code}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "请求超时"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "连接失败，请检查网络"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"请求异常: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"连接异常: {str(e)}"
            }


# 全局服务实例
_wechat_service: Optional[WeChatService] = None


def get_wechat_service() -> WeChatService:
    """获取企业微信服务实例"""
    global _wechat_service
    if _wechat_service is None:
        _wechat_service = WeChatService()
    return _wechat_service
