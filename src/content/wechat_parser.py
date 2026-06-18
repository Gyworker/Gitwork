# -*- coding: utf-8 -*-
"""
企业微信聊天记录解析模块
支持解析企业微信导出的聊天记录文件

版本: V1.0
功能: 完整实现企业微信聊天记录解析
"""

import os
import re
import json
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

from src.content.content_parser_service import ParsedContent
from src.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class WeChatMessage:
    """企业微信消息"""
    sender: str = ""
    time: str = ""
    content: str = ""
    is_system: bool = False
    
    # 扩展字段
    member_name: str = ""  # 成员名称
    member_id: str = ""    # 成员ID
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'sender': self.sender,
            'time': self.time,
            'content': self.content,
            'is_system': self.is_system,
            'member_name': self.member_name,
            'member_id': self.member_id
        }


@dataclass
class WeChatChatRecord:
    """企业微信聊天记录"""
    chat_name: str = ""
    start_time: str = ""
    end_time: str = ""
    messages: List[WeChatMessage] = field(default_factory=list)
    
    # 统计信息
    member_count: int = 0
    message_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'chat_name': self.chat_name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'member_count': self.member_count,
            'message_count': self.message_count,
            'messages': [m.to_dict() for m in self.messages]
        }


class WeChatParserError(Exception):
    """解析器异常"""
    pass


class WeChatParser:
    """
    企业微信聊天记录解析器
    
    支持的导入格式:
    1. 文本格式 (.txt) - 企业微信导出的纯文本格式
    2. JSON格式 (.json) - 企业微信导出的JSON格式
    3. CSV格式 (.csv) - 企业微信导出的CSV格式
    
    解析规则:
    1. 文本格式: "[时间] 成员: 消息内容"
    2. 自动识别咨询者姓名
    3. 提取关键模块信息
    4. 合并连续消息
    """
    
    # 支持的文件扩展名
    SUPPORTED_EXTENSIONS = ['.txt', '.json', '.csv']
    
    # 消息时间正则表达式
    TIME_PATTERN = r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?)'
    
    # 消息发送者正则表达式
    SENDER_PATTERN = r'^\[(.+?)\]\s*(?:@)?(.+?)(?:\s*@\w+)?[:：]\s*(.*)$'
    
    # 关键模块关键词
    MODULE_KEYWORDS = {
        'MAC认证': ['mac', 'MAC', 'mac地址', 'MAC地址'],
        '802.1x认证': ['802.1x', '802.1X', 'dot1x', 'DOT1X', '1x认证'],
        'Portal认证': ['portal', 'Portal', 'web认证', '网页认证'],
        'RADIUS': ['radius', 'RADIUS', 'radius服务器'],
        'AC': ['ac', 'AC', '无线控制器', '控制器'],
        'AP': ['ap', 'AP', '无线接入点', '接入点'],
        '交换机': ['交换机', 'switch', 'Switch'],
        '路由器': ['路由器', 'router', 'Router'],
        '防火墙': ['防火墙', 'firewall', 'Firewall'],
        'VPN': ['vpn', 'VPN', '虚拟专网'],
        'SD-WAN': ['sd-wan', 'SD-WAN', 'sdwan'],
        'QoS': ['qos', 'QoS', '服务质量'],
        'OSPF': ['ospf', 'OSPF', '路由协议'],
        'BGP': ['bgp', 'BGP', '边界网关协议'],
    }
    
    # 产品型号正则
    PRODUCT_PATTERN = r'([A-Z]{2,4}[-_]?\d{2,4}[-_]?[A-Z0-9]*)'
    
    @classmethod
    def is_available(cls) -> bool:
        """检查解析器是否可用"""
        return True  # 纯Python实现，始终可用
    
    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """获取支持的格式"""
        return ['.txt (文本格式)', '.json (JSON格式)', '.csv (CSV格式)']
    
    @classmethod
    def parse_file(cls, filepath: str) -> WeChatChatRecord:
        """
        解析企业微信聊天记录文件
        
        Args:
            filepath: 文件路径
            
        Returns:
            WeChatChatRecord: 聊天记录对象
            
        Raises:
            WeChatParserError: 解析错误
        """
        if not os.path.exists(filepath):
            raise WeChatParserError(f"文件不存在: {filepath}")
        
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise WeChatParserError(
                f"不支持的文件格式: {ext}\n"
                f"支持的格式: {', '.join(cls.SUPPORTED_EXTENSIONS)}"
            )
        
        logger.info(f"开始解析企业微信聊天记录: {filepath}")
        
        try:
            if ext == '.txt':
                return cls._parse_txt(filepath)
            elif ext == '.json':
                return cls._parse_json(filepath)
            elif ext == '.csv':
                return cls._parse_csv(filepath)
        except Exception as e:
            logger.error(f"解析企业微信聊天记录失败: {e}")
            raise WeChatParserError(f"解析失败: {str(e)}")
    
    @classmethod
    def parse_content(cls, content: str) -> ParsedContent:
        """
        解析内容并转换为任务信息
        
        Args:
            content: 文件路径或文本内容
            
        Returns:
            ParsedContent: 解析结果
        """
        result = ParsedContent()
        result.source_type = "wechat"
        result.source = "wechat"
        
        try:
            # 判断是文件路径还是文本内容
            if os.path.exists(content.strip()):
                filepath = content.strip()
                result.source_file = filepath
                
                # 解析聊天记录
                record = cls.parse_file(filepath)
                
                # 转换为任务信息
                result = cls._convert_to_task(record)
            else:
                # 直接解析文本内容
                result = cls._parse_text_content(content)
                
        except WeChatParserError as e:
            result.error = "企业微信解析失败"
            result.error_details = str(e)
            logger.error(f"企业微信解析异常: {e}")
        except Exception as e:
            result.error = "企业微信解析失败"
            result.error_details = str(e)
            logger.error(f"企业微信解析未知异常: {e}")
        
        return result
    
    @classmethod
    def _parse_txt(cls, filepath: str) -> WeChatChatRecord:
        """解析文本格式聊天记录"""
        record = WeChatChatRecord()
        record.chat_name = os.path.basename(filepath).replace('.txt', '')
        
        messages = []
        current_message: Optional[WeChatMessage] = None
        last_sender: Optional[str] = None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # 尝试解析消息
                msg = cls._parse_message_line(line)
                
                if msg:
                    # 检查是否是连续消息（同一人发送）
                    if last_sender == msg.sender and current_message:
                        # 合并到当前消息
                        current_message.content += '\n' + msg.content
                    else:
                        # 保存上一条消息
                        if current_message:
                            messages.append(current_message)
                        # 开始新消息
                        current_message = msg
                        last_sender = msg.sender
                else:
                    # 无法解析的行，可能是连续内容
                    if current_message and line:
                        current_message.content += '\n' + line
        
        # 保存最后一条消息
        if current_message:
            messages.append(current_message)
        
        record.messages = messages
        record.message_count = len(messages)
        
        # 提取时间范围
        if messages:
            record.start_time = messages[0].time
            record.end_time = messages[-1].time
        
        # 统计成员
        members = set(m.sender for m in messages if m.sender)
        record.member_count = len(members)
        
        logger.info(f"文本解析完成: {record.message_count}条消息, {record.member_count}个成员")
        
        return record
    
    @classmethod
    def _parse_json(cls, filepath: str) -> WeChatChatRecord:
        """解析JSON格式聊天记录"""
        record = WeChatChatRecord()
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 企业微信JSON格式
        if isinstance(data, dict):
            # 可能包含的字段
            record.chat_name = data.get('chatName', data.get('name', '未知会话'))
            
            messages_data = data.get('messages', data.get('chatlog', []))
        elif isinstance(data, list):
            messages_data = data
            record.chat_name = 'JSON会话'
        else:
            raise WeChatParserError("JSON格式不支持")
        
        messages = []
        for msg_data in messages_data:
            msg = WeChatMessage()
            
            # 提取字段（兼容多种格式）
            msg.sender = msg_data.get('sender', msg_data.get('nickName', msg_data.get('from', '')))
            msg.content = msg_data.get('content', msg_data.get('text', ''))
            msg.time = msg_data.get('time', msg_data.get('date', msg_data.get('createTime', '')))
            
            # 处理时间格式
            if isinstance(msg.time, (int, float)):
                # 时间戳
                msg.time = datetime.fromtimestamp(msg.time).strftime('%Y-%m-%d %H:%M')
            
            # 检查是否系统消息
            msg.is_system = msg_data.get('type') == 'system' or '加入' in msg.content or '离开' in msg.content
            
            if msg.content:
                messages.append(msg)
        
        record.messages = messages
        record.message_count = len(messages)
        
        if messages:
            record.start_time = messages[0].time
            record.end_time = messages[-1].time
        
        members = set(m.sender for m in messages if m.sender and not m.is_system)
        record.member_count = len(members)
        
        logger.info(f"JSON解析完成: {record.message_count}条消息, {record.member_count}个成员")
        
        return record
    
    @classmethod
    def _parse_csv(cls, filepath: str) -> WeChatChatRecord:
        """解析CSV格式聊天记录"""
        record = WeChatChatRecord()
        record.chat_name = os.path.basename(filepath).replace('.csv', '')
        
        messages = []
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            # 尝试不同的分隔符
            try:
                reader = csv.reader(f)
                rows = list(reader)
            except:
                # 尝试其他编码
                with open(filepath, 'r', encoding='gbk') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
        
        # 检测CSV列
        if rows:
            header = rows[0] if rows else []
            
            # 尝试自动识别列
            time_idx = -1
            sender_idx = -1
            content_idx = -1
            
            for idx, col in enumerate(header):
                col_lower = col.lower()
                if '时间' in col or 'date' in col_lower or 'time' in col_lower:
                    time_idx = idx
                elif '发送者' in col or 'sender' in col_lower or 'from' in col_lower or '成员' in col:
                    sender_idx = idx
                elif '内容' in col or 'content' in col_lower or 'message' in col_lower or 'text' in col_lower:
                    content_idx = idx
            
            # 如果没找到，使用默认位置
            if time_idx == -1 and len(header) >= 1:
                time_idx = 0
            if sender_idx == -1 and len(header) >= 2:
                sender_idx = 1
            if content_idx == -1 and len(header) >= 3:
                content_idx = 2
            
            # 解析数据行
            for row in rows[1:]:
                if not row or len(row) < max(time_idx, sender_idx, content_idx) + 1:
                    continue
                
                msg = WeChatMessage()
                msg.time = row[time_idx] if time_idx >= 0 else ''
                msg.sender = row[sender_idx] if sender_idx >= 0 else ''
                msg.content = row[content_idx] if content_idx >= 0 else ''
                
                if msg.content.strip():
                    messages.append(msg)
        
        record.messages = messages
        record.message_count = len(messages)
        
        if messages:
            record.start_time = messages[0].time
            record.end_time = messages[-1].time
        
        members = set(m.sender for m in messages if m.sender)
        record.member_count = len(members)
        
        logger.info(f"CSV解析完成: {record.message_count}条消息, {record.member_count}个成员")
        
        return record
    
    @classmethod
    def _parse_message_line(cls, line: str) -> Optional[WeChatMessage]:
        """解析单条消息行"""
        # 匹配格式: [时间] 成员: 内容
        match = re.match(cls.SENDER_PATTERN, line)
        
        if match:
            msg = WeChatMessage()
            msg.time = match.group(1).strip()
            msg.sender = match.group(2).strip()
            msg.content = match.group(3).strip()
            return msg
        
        return None
    
    @classmethod
    def _convert_to_task(cls, record: WeChatChatRecord) -> ParsedContent:
        """将聊天记录转换为任务信息"""
        result = ParsedContent()
        result.source_type = "wechat"
        result.source = record.chat_name
        
        # 合并所有消息内容
        all_content = '\n'.join(m.content for m in record.messages if m.content)
        
        # 提取任务名称（取第一条消息的前50字）
        if record.messages and record.messages[0].content:
            first_content = record.messages[0].content[:50]
            result.task_name = first_content
        else:
            result.task_name = record.chat_name
        
        result.task_content = all_content
        
        # 提取咨询者（通常是第一个发送消息的人）
        for msg in record.messages:
            if msg.sender and not msg.is_system:
                result.consultant_name = msg.sender
                break
        
        # 提取关键模块
        key_modules = cls._extract_key_modules(all_content)
        result.key_module = '、'.join(key_modules) if key_modules else ''
        
        # 提取产品型号
        products = cls._extract_products(all_content)
        result.product_model = '、'.join(products) if products else ''
        
        # 设置原始数据
        result.raw_data = record.to_dict()
        
        return result
    
    @classmethod
    def _parse_text_content(cls, content: str) -> ParsedContent:
        """解析文本内容（不读取文件）"""
        result = ParsedContent()
        result.source_type = "wechat"
        result.source = "wechat"
        
        lines = content.strip().split('\n')
        
        # 解析消息
        messages = []
        current_message: Optional[WeChatMessage] = None
        last_sender: Optional[str] = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            msg = cls._parse_message_line(line)
            
            if msg:
                if last_sender == msg.sender and current_message:
                    current_message.content += '\n' + msg.content
                else:
                    if current_message:
                        messages.append(current_message)
                    current_message = msg
                    last_sender = msg.sender
            elif current_message and line:
                current_message.content += '\n' + line
        
        if current_message:
            messages.append(current_message)
        
        # 提取任务信息
        if messages:
            all_content = '\n'.join(m.content for m in messages if m.content)
            result.task_name = messages[0].content[:50] if messages[0].content else '企业微信任务'
            result.task_content = all_content
            
            # 提取咨询者
            for msg in messages:
                if msg.sender and not msg.is_system:
                    result.consultant_name = msg.sender
                    break
            
            # 提取关键模块
            key_modules = cls._extract_key_modules(all_content)
            result.key_module = '、'.join(key_modules) if key_modules else ''
            
            # 提取产品型号
            products = cls._extract_products(all_content)
            result.product_model = '、'.join(products) if products else ''
        
        return result
    
    @classmethod
    def _extract_key_modules(cls, content: str) -> List[str]:
        """从内容中提取关键模块"""
        found_modules = set()
        content_lower = content.lower()
        
        for module, keywords in cls.MODULE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    found_modules.add(module)
                    break
        
        return list(found_modules)
    
    @classmethod
    def _extract_products(cls, content: str) -> List[str]:
        """从内容中提取产品型号"""
        products = set()
        
        # 匹配常见产品型号格式
        matches = re.findall(cls.PRODUCT_PATTERN, content)
        for match in matches:
            if len(match) >= 4:  # 过滤太短的匹配
                products.add(match)
        
        return list(products)
    
    @classmethod
    def get_library_info(cls) -> Dict[str, Any]:
        """获取解析器信息"""
        return {
            'name': 'WeChatParser',
            'version': '1.0',
            'author': '市场咨询任务跟踪工具',
            'supported_formats': cls.SUPPORTED_EXTENSIONS,
            'description': '企业微信聊天记录解析器',
        }


# =============================================================================
# 批量解析器
# =============================================================================

class WeChatBatchParser:
    """企业微信聊天记录批量解析器"""
    
    def __init__(self):
        self.parser = WeChatParser()
        self.results: List[WeChatChatRecord] = []
        self.errors: List[Dict[str, str]] = []
    
    def parse_directory(
        self,
        directory: str,
        recursive: bool = False,
        extensions: Optional[List[str]] = None
    ) -> List[WeChatChatRecord]:
        """
        批量解析目录下的聊天记录文件
        
        Args:
            directory: 目录路径
            recursive: 是否递归搜索子目录
            extensions: 文件扩展名过滤
            
        Returns:
            解析成功的聊天记录列表
        """
        if extensions is None:
            extensions = WeChatParser.SUPPORTED_EXTENSIONS
        
        results = []
        errors = []
        
        # 获取文件列表
        if recursive:
            files = []
            for ext in extensions:
                files.extend(Path(directory).rglob(f'*{ext}'))
        else:
            files = []
            for ext in extensions:
                files.extend(Path(directory).glob(f'*{ext}'))
        
        logger.info(f"找到 {len(files)} 个待解析文件")
        
        # 逐个解析
        for filepath in files:
            try:
                record = self.parser.parse_file(str(filepath))
                results.append(record)
                logger.info(f"解析成功: {filepath}")
            except WeChatParserError as e:
                errors.append({
                    'file': str(filepath),
                    'error': str(e)
                })
                logger.warning(f"解析失败: {filepath} - {e}")
        
        self.results = results
        self.errors = errors
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取批量解析统计"""
        total_messages = sum(r.message_count for r in self.results)
        total_members = len(set(
            m.sender 
            for r in self.results 
            for m in r.messages 
            if m.sender
        ))
        
        return {
            'total_files': len(self.results) + len(self.errors),
            'success_count': len(self.results),
            'error_count': len(self.errors),
            'total_messages': total_messages,
            'total_members': total_members,
            'errors': self.errors
        }


# =============================================================================
# 单例实例
# =============================================================================

_wechat_parser: Optional[WeChatParser] = None


def get_wechat_parser() -> WeChatParser:
    """获取企业微信解析器单例"""
    global _wechat_parser
    if _wechat_parser is None:
        _wechat_parser = WeChatParser()
    return _wechat_parser
