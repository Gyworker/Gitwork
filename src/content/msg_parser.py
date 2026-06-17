# -*- coding: utf-8 -*-
"""
MSG邮件文件解析模块
支持从Outlook MSG文件中提取邮件信息
版本：V1.0
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path

# MSG文件解析库
try:
    import extract_msg
    HAS_EXTRACT_MSG = True
except ImportError:
    HAS_EXTRACT_MSG = False


@dataclass
class MSGEmail:
    """MSG邮件数据结构"""
    subject: str = ""           # 邮件主题
    sender: str = ""           # 发件人
    sender_email: str = ""     # 发件人邮箱
    to_recipients: str = ""    # 收件人
    cc_recipients: str = ""    # 抄送
    date: str = ""             # 发送日期
    body: str = ""             # 邮件正文
    attachments: List[str] = field(default_factory=list)  # 附件列表
    importance: str = ""       # 重要程度
    categories: str = ""       # 类别
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MSGEmail':
        """从字典创建"""
        return cls(**data)
    
    def to_task_content(self) -> str:
        """转换为任务内容格式"""
        content_parts = []
        
        if self.subject:
            content_parts.append(f"【主题】{self.subject}")
        
        if self.sender:
            content_parts.append(f"【发件人】{self.sender}")
            if self.sender_email:
                content_parts.append(f"【邮箱】{self.sender_email}")
        
        if self.to_recipients:
            content_parts.append(f"【收件人】{self.to_recipients}")
        
        if self.date:
            content_parts.append(f"【时间】{self.date}")
        
        if self.importance:
            content_parts.append(f"【重要程度】{self.importance}")
        
        if self.body:
            content_parts.append(f"\n【正文】\n{self.body}")
        
        if self.attachments:
            content_parts.append(f"\n【附件】\n" + "\n".join(f"- {att}" for att in self.attachments))
        
        return "\n".join(content_parts)


class MSGParser:
    """MSG文件解析器"""
    
    # 支持的文件扩展名
    SUPPORTED_EXTENSIONS = ['.msg']
    
    # 邮件地址正则
    EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    
    # 电话号码正则
    PHONE_PATTERN = re.compile(
        r'(?:电话|TEL|手机|Mobile|Phone)?[:：]?\s*'
        r'(\+?86)?\s*'
        r'(?:1[3-9]\d{9}|(?:010|021|022|023|024|025|027|028|029)\d{7,8})'
    )
    
    @classmethod
    def is_available(cls) -> bool:
        """检查MSG解析库是否可用"""
        return HAS_EXTRACT_MSG
    
    @classmethod
    def get_library_info(cls) -> Dict[str, Any]:
        """获取库信息"""
        if HAS_EXTRACT_MSG:
            return {
                'available': True,
                'library': 'extract-msg',
                'version': getattr(extract_msg, '__version__', 'unknown')
            }
        else:
            return {
                'available': False,
                'library': 'extract-msg',
                'install_command': 'pip install extract-msg'
            }
    
    @classmethod
    def parse_file(cls, filepath: str) -> MSGEmail:
        """解析MSG文件
        
        Args:
            filepath: MSG文件路径
            
        Returns:
            MSGEmail对象
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误
            ImportError: 缺少解析库
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")
        
        if not os.path.splitext(filepath)[1].lower() == '.msg':
            raise ValueError(f"不支持的文件格式: {filepath}")
        
        if not HAS_EXTRACT_MSG:
            raise ImportError(
                "需要安装extract-msg库来解析MSG文件。\n"
                "请运行: pip install extract-msg"
            )
        
        try:
            # 使用extract_msg打开MSG文件
            msg = extract_msg.Message(filepath)
            
            # 提取邮件信息
            email = MSGEmail()
            
            # 主题
            email.subject = cls._clean_text(getattr(msg, 'subject', '') or '')
            
            # 发件人
            sender = getattr(msg, 'sender', '') or ''
            email.sender = cls._extract_name(sender)
            email.sender_email = cls._extract_email(sender)
            
            # 收件人
            to_list = getattr(msg, 'to', '') or ''
            email.to_recipients = cls._clean_text(to_list)
            
            # 抄送
            cc = getattr(msg, 'cc', '') or ''
            email.cc_recipients = cls._clean_text(cc)
            
            # 日期
            date = getattr(msg, 'date', '') or ''
            email.date = cls._format_date(date)
            
            # 正文
            email.body = cls._clean_text(getattr(msg, 'body', '') or '')
            
            # 附件
            attachments = getattr(msg, 'attachments', []) or []
            email.attachments = [cls._clean_text(str(att)) for att in attachments]
            
            # 重要程度
            importance = getattr(msg, 'importance', 1) or 1
            email.importance = cls._map_importance(importance)
            
            # 类别
            categories = getattr(msg, 'categories', '') or ''
            email.categories = cls._clean_text(categories)
            
            # 关闭消息
            try:
                msg.close()
            except:
                pass
            
            return email
            
        except Exception as e:
            raise ValueError(f"解析MSG文件失败: {e}")
    
    @classmethod
    def parse_file_safe(cls, filepath: str) -> MSGEmail:
        """安全解析MSG文件（带备用方案）
        
        Args:
            filepath: MSG文件路径
            
        Returns:
            MSGEmail对象
        """
        if HAS_EXTRACT_MSG:
            return cls.parse_file(filepath)
        else:
            return cls._parse_ole_basic(filepath)
    
    @classmethod
    def _parse_ole_basic(cls, filepath: str) -> MSGEmail:
        """基本OLE格式解析（无第三方库）"""
        email = MSGEmail()
        
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            
            # 尝试解码为文本
            try:
                text = content.decode('utf-8', errors='ignore')
            except:
                try:
                    text = content.decode('gbk', errors='ignore')
                except:
                    text = content.decode('latin-1', errors='ignore')
            
            # 提取邮件地址
            emails = cls.EMAIL_PATTERN.findall(text)
            if emails:
                email.sender_email = emails[0]
            
            # 提取主题（简化处理）
            subject_match = re.search(r'Subject[:\s]+([^\r\n]+)', text, re.IGNORECASE)
            if subject_match:
                email.subject = subject_match.group(1).strip()
            
            # 提取日期（简化处理）
            date_match = re.search(r'Date[:\s]+([^\r\n]+)', text, re.IGNORECASE)
            if date_match:
                email.date = date_match.group(1).strip()
            
            # 尝试提取正文（查找可读文本段）
            email.body = cls._extract_readable_text(text)
            
            email.subject = email.subject or "无主题"
            
        except Exception as e:
            raise ValueError(f"OLE解析失败: {e}")
        
        return email
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        
        # 移除多余空白
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def _extract_name(text: str) -> str:
        """从"姓名 <邮箱>"格式中提取姓名"""
        if not text:
            return ""
        
        # 处理 "姓名 <邮箱>" 格式
        match = re.match(r'^([^<]+?)\s*<', text)
        if match:
            return match.group(1).strip()
        
        return text.strip()
    
    @staticmethod
    def _extract_email(text: str) -> str:
        """从文本中提取邮箱地址"""
        if not text:
            return ""
        
        match = MSGParser.EMAIL_PATTERN.search(text)
        if match:
            return match.group(0)
        
        return ""
    
    @classmethod
    def _format_date(cls, date_str: str) -> str:
        """格式化日期"""
        if not date_str:
            return ""
        
        try:
            # 尝试解析日期
            if isinstance(date_str, str):
                # 移除时区信息
                date_str = re.sub(r'\s*\(.*?\)\s*', '', date_str)
                date_str = date_str.strip()
                
                # 尝试多种格式
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y/%m/%d %H:%M:%S',
                    '%d/%m/%Y %H:%M:%S',
                    '%m/%d/%Y %H:%M:%S',
                ]
                
                for fmt in formats:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        return dt.strftime('%Y-%m-%d %H:%M')
                    except ValueError:
                        continue
                
                return date_str
            else:
                return str(date_str)
        except:
            return str(date_str)
    
    @staticmethod
    def _map_importance(importance: int) -> str:
        """映射重要程度"""
        mapping = {
            0: '低',
            1: '普通',
            2: '高'
        }
        return mapping.get(importance, '普通')
    
    @classmethod
    def _extract_readable_text(cls, text: str) -> str:
        """从乱码文本中提取可读文本段"""
        # 提取可读的中文和英文段落
        readable_lines = []
        
        for line in text.split('\n'):
            line = line.strip()
            # 保留包含中文或有效ASCII字符的行
            if re.search(r'[\u4e00-\u9fff]', line) or \
               re.search(r'[a-zA-Z]{3,}', line):
                # 清理控制字符
                line = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', line)
                if len(line) > 5:
                    readable_lines.append(line)
        
        # 返回前20行
        return '\n'.join(readable_lines[:20])
    
    @classmethod
    def extract_contacts(cls, email: MSGEmail) -> List[Dict[str, str]]:
        """从邮件中提取联系人信息
        
        Args:
            email: MSGEmail对象
            
        Returns:
            联系人信息列表
        """
        contacts = []
        
        # 提取发件人
        if email.sender_email:
            contact = {
                'name': email.sender,
                'email': email.sender_email,
                'phone': '',
                'source': 'msg_import'
            }
            
            # 尝试从正文提取电话
            if email.body:
                phone_match = cls.PHONE_PATTERN.search(email.body)
                if phone_match:
                    contact['phone'] = phone_match.group(0)
            
            contacts.append(contact)
        
        # 提取正文中的邮箱（可能是回复中的联系人）
        if email.body:
            found_emails = cls.EMAIL_PATTERN.findall(email.body)
            for em in found_emails[:5]:  # 最多5个
                if em != email.sender_email:
                    contacts.append({
                        'name': '',
                        'email': em,
                        'phone': '',
                        'source': 'msg_body'
                    })
        
        return contacts
    
    @classmethod
    def to_json(cls, email: MSGEmail, filepath: str = None) -> str:
        """导出为JSON格式
        
        Args:
            email: MSGEmail对象
            filepath: 可选，保存到文件
            
        Returns:
            JSON字符串
        """
        data = email.to_dict()
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str = None, filepath: str = None) -> MSGEmail:
        """从JSON导入
        
        Args:
            json_str: JSON字符串
            filepath: 从文件读取
            
        Returns:
            MSGEmail对象
        """
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif json_str:
            data = json.loads(json_str)
        else:
            raise ValueError("必须提供json_str或filepath")
        
        return MSGEmail.from_dict(data)


class BatchMSGParser:
    """批量MSG文件解析器"""
    
    def __init__(self):
        self.parser = MSGParser()
        self.results: List[MSGEmail] = []
        self.errors: List[Dict[str, str]] = []
    
    def parse_directory(self, directory: str, recursive: bool = False) -> List[MSGEmail]:
        """解析目录中的所有MSG文件
        
        Args:
            directory: 目录路径
            recursive: 是否递归子目录
            
        Returns:
            解析成功的邮件列表
        """
        self.results = []
        self.errors = []
        
        if not os.path.exists(directory):
            raise FileNotFoundError(f"目录不存在: {directory}")
        
        # 收集MSG文件
        msg_files = []
        
        if recursive:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith('.msg'):
                        msg_files.append(os.path.join(root, file))
        else:
            for file in os.listdir(directory):
                filepath = os.path.join(directory, file)
                if os.path.isfile(filepath) and file.lower().endswith('.msg'):
                    msg_files.append(filepath)
        
        # 解析每个文件
        for filepath in sorted(msg_files):
            try:
                email = self.parser.parse_file_safe(filepath)
                self.results.append(email)
            except Exception as e:
                self.errors.append({
                    'file': filepath,
                    'error': str(e)
                })
        
        return self.results
    
    def get_summary(self) -> Dict[str, Any]:
        """获取解析摘要"""
        return {
            'total_files': len(self.results) + len(self.errors),
            'success_count': len(self.results),
            'error_count': len(self.errors),
            'errors': self.errors
        }
