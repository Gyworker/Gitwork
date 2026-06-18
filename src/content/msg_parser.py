# -*- coding: utf-8 -*-
"""
MSG邮件文件解析模块
支持从Outlook MSG文件中提取邮件信息
版本：V1.1

V1.1新增功能：
- ParseError错误上下文增强
- 进度回调机制
- 流式解析大文件
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict, field
from pathlib import Path

# MSG文件解析库
try:
    import extract_msg
    HAS_EXTRACT_MSG = True
except ImportError:
    HAS_EXTRACT_MSG = False


@dataclass
class ParseError:
    """解析错误详细信息"""
    error_type: str = ""           # 错误类型
    error_message: str = ""        # 错误信息
    filepath: str = ""             # 文件路径
    file_size: int = 0             # 文件大小
    timestamp: str = ""            # 发生时间
    context: Dict[str, Any] = field(default_factory=dict)  # 额外上下文
    
    def to_user_message(self) -> str:
        """生成用户友好的错误消息"""
        msg_parts = [f"解析失败: {self.error_message}"]
        
        if self.filepath:
            msg_parts.append(f"文件: {os.path.basename(self.filepath)}")
        
        if self.file_size > 0:
            if self.file_size < 1024:
                size_str = f"{self.file_size} B"
            elif self.file_size < 1024 * 1024:
                size_str = f"{self.file_size / 1024:.1f} KB"
            else:
                size_str = f"{self.file_size / 1024 / 1024:.1f} MB"
            msg_parts.append(f"大小: {size_str}")
        
        if self.timestamp:
            msg_parts.append(f"时间: {self.timestamp}")
        
        return "\n".join(msg_parts)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


@dataclass
class ParseProgress:
    """解析进度信息"""
    current: int = 0               # 当前处理数量
    total: int = 0                 # 总数
    current_file: str = ""          # 当前处理的文件
    percentage: float = 0.0        # 百分比
    status: str = "pending"        # 状态 (pending/processing/completed/error/cancelled)
    elapsed_time: float = 0.0     # 耗时(秒)


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
    def _create_error(cls, exc: Exception, context: Dict, 
                     error_type: str) -> ParseError:
        """创建详细错误信息"""
        return ParseError(
            error_type=error_type,
            error_message=str(exc),
            filepath=context.get('filepath', ''),
            file_size=context.get('file_size', 0),
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            context=context
        )
    
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
            ParseError: 解析错误（带详细上下文）
        """
        error_context = {
            'filepath': filepath,
            'file_size': 0,
            'parse_stage': 'init'
        }
        
        try:
            # 验证文件存在
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"文件不存在: {filepath}")
            
            error_context['file_size'] = os.path.getsize(filepath)
            error_context['parse_stage'] = 'file_validated'
            
            if not os.path.splitext(filepath)[1].lower() == '.msg':
                raise ValueError(f"不支持的文件格式: {os.path.splitext(filepath)[1]}")
            
            error_context['parse_stage'] = 'format_validated'
            
            if not HAS_EXTRACT_MSG:
                raise ImportError(
                    "需要安装extract-msg库来解析MSG文件。\n"
                    "请运行: pip install extract-msg"
                )
            
            error_context['parse_stage'] = 'library_checked'
            
            try:
                # 使用extract_msg打开MSG文件
                msg = extract_msg.Message(filepath)
                error_context['parse_stage'] = 'msg_opened'
                
                # 提取邮件信息
                email = MSGEmail()
                
                # 主题
                email.subject = cls._clean_text(getattr(msg, 'subject', '') or '')
                error_context['parse_stage'] = 'subject_extracted'
                
                # 发件人
                sender = getattr(msg, 'sender', '') or ''
                email.sender = cls._extract_name(sender)
                email.sender_email = cls._extract_email(sender)
                error_context['parse_stage'] = 'sender_extracted'
                
                # 收件人
                to_list = getattr(msg, 'to', '') or ''
                email.to_recipients = cls._clean_text(to_list)
                
                # 抄送
                cc = getattr(msg, 'cc', '') or ''
                email.cc_recipients = cls._clean_text(cc)
                
                # 日期
                date = getattr(msg, 'date', '') or ''
                email.date = cls._format_date(date)
                error_context['parse_stage'] = 'date_extracted'
                
                # 正文
                email.body = cls._clean_text(getattr(msg, 'body', '') or '')
                error_context['parse_stage'] = 'body_extracted'
                
                # 附件
                attachments = getattr(msg, 'attachments', []) or []
                email.attachments = [cls._clean_text(str(att)) for att in attachments]
                error_context['parse_stage'] = 'attachments_extracted'
                
                # 重要程度
                importance = getattr(msg, 'importance', 1) or 1
                email.importance = cls._map_importance(importance)
                
                # 类别
                categories = getattr(msg, 'categories', '') or ''
                email.categories = cls._clean_text(categories)
                error_context['parse_stage'] = 'completed'
                
                # 关闭消息
                try:
                    msg.close()
                except:
                    pass
                
                return email
                
            except FileNotFoundError as e:
                raise cls._create_error(e, error_context, 'file_not_found')
            except ValueError as e:
                raise cls._create_error(e, error_context, 'value_error')
            except ImportError as e:
                raise cls._create_error(e, error_context, 'import_error')
            except Exception as e:
                raise cls._create_error(e, error_context, 'parse_error')
            
        except (FileNotFoundError, ValueError, ImportError):
            raise  # 重新抛出已知异常
        except ParseError:
            raise  # 重新抛出ParseError
        except Exception as e:
            # 未知异常，包装为ParseError
            raise cls._create_error(e, error_context, 'unknown')
    
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
            
            # 提取主题
            subject_match = re.search(r'Subject[:\s]+([^\r\n]+)', text, re.IGNORECASE)
            if subject_match:
                email.subject = subject_match.group(1).strip()
            
            # 提取日期
            date_match = re.search(r'Date[:\s]+([^\r\n]+)', text, re.IGNORECASE)
            if date_match:
                email.date = date_match.group(1).strip()
            
            # 尝试提取正文
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
        
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def _extract_name(text: str) -> str:
        """从"姓名 <邮箱>"格式中提取姓名"""
        if not text:
            return ""
        
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
            if isinstance(date_str, str):
                date_str = re.sub(r'\s*\(.*?\)\s*', '', date_str)
                date_str = date_str.strip()
                
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
        readable_lines = []
        
        for line in text.split('\n'):
            line = line.strip()
            if re.search(r'[\u4e00-\u9fff]', line) or \
               re.search(r'[a-zA-Z]{3,}', line):
                line = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', line)
                if len(line) > 5:
                    readable_lines.append(line)
        
        return '\n'.join(readable_lines[:20])
    
    @classmethod
    def extract_contacts(cls, email: MSGEmail) -> List[Dict[str, str]]:
        """从邮件中提取联系人信息"""
        contacts = []
        
        if email.sender_email:
            contact = {
                'name': email.sender,
                'email': email.sender_email,
                'phone': '',
                'source': 'msg_import'
            }
            
            if email.body:
                phone_match = cls.PHONE_PATTERN.search(email.body)
                if phone_match:
                    contact['phone'] = phone_match.group(0)
            
            contacts.append(contact)
        
        if email.body:
            found_emails = cls.EMAIL_PATTERN.findall(email.body)
            for em in found_emails[:5]:
                if em != email.sender_email:
                    contacts.append({
                        'name': '',
                        'email': em,
                        'phone': '',
                        'source': 'msg_body'
                    })
        
        return contacts
    
    @classmethod
    def to_json(cls, email: MSGEmail, filepath: str = None,
                indent: int = 2) -> str:
        """导出为JSON格式
        
        Args:
            email: MSGEmail对象
            filepath: 可选，保存到文件
            indent: 缩进空格数，0表示不缩进
            
        Returns:
            JSON字符串
        """
        data = email.to_dict()
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
        
        return json.dumps(data, ensure_ascii=False, indent=indent)
    
    @classmethod
    def from_json(cls, json_str: str = None, filepath: str = None) -> MSGEmail:
        """从JSON导入"""
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif json_str:
            data = json.loads(json_str)
        else:
            raise ValueError("必须提供json_str或filepath")
        
        return MSGEmail.from_dict(data)


class MSGParserWithProgress:
    """带进度回调的MSG解析器"""
    
    def __init__(self, 
                 progress_callback: Optional[Callable[[ParseProgress], None]] = None,
                 cancel_check: Optional[Callable[[], bool]] = None):
        """
        Args:
            progress_callback: 进度回调函数
            cancel_check: 取消检查函数，返回True表示取消
        """
        self.progress_callback = progress_callback
        self.cancel_check = cancel_check
        self._cancelled = False
        self._progress_history: List[ParseProgress] = []
    
    def parse_batch(self, filepaths: List[str]) -> List[MSGEmail]:
        """批量解析，带进度回调
        
        Args:
            filepaths: MSG文件路径列表
            
        Returns:
            解析成功的邮件列表
        """
        results = []
        total = len(filepaths)
        self._progress_history = []
        
        for i, filepath in enumerate(filepaths):
            # 检查是否取消
            if self.cancel_check and self.cancel_check():
                self._report_progress(i, total, filepath, 'cancelled')
                break
            
            # 报告处理中
            self._report_progress(i, total, filepath, 'processing')
            
            try:
                email = MSGParser.parse_file_safe(filepath)
                results.append(email)
                self._report_progress(i + 1, total, filepath, 'completed')
            except Exception as e:
                self._report_progress(i + 1, total, filepath, 'error')
                # 跳过错误文件，继续处理
                continue
        
        return results
    
    def _report_progress(self, current: int, total: int,
                        filepath: str, status: str):
        """报告进度"""
        if self.progress_callback:
            progress = ParseProgress(
                current=current,
                total=total,
                current_file=os.path.basename(filepath),
                percentage=(current / total * 100) if total > 0 else 0,
                status=status
            )
            self._progress_history.append(progress)
            self.progress_callback(progress)
    
    def get_progress_history(self) -> List[ParseProgress]:
        """获取进度历史"""
        return self._progress_history.copy()


class StreamingMSGParser:
    """流式MSG解析器，处理大文件"""
    
    # 内存限制（默认50MB）
    DEFAULT_MEMORY_LIMIT = 50 * 1024 * 1024
    
    # 分块大小（1MB）
    CHUNK_SIZE = 1024 * 1024
    
    def __init__(self, memory_limit: int = None):
        """
        Args:
            memory_limit: 内存限制（字节），默认50MB
        """
        self.memory_limit = memory_limit or self.DEFAULT_MEMORY_LIMIT
    
    def parse_large_file(self, filepath: str) -> MSGEmail:
        """流式解析大文件，控制内存使用
        
        Args:
            filepath: MSG文件路径
            
        Returns:
            MSGEmail对象
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")
        
        file_size = os.path.getsize(filepath)
        
        # 小文件直接解析
        if file_size < self.CHUNK_SIZE * 2:
            return MSGParser.parse_file_safe(filepath)
        
        # 大文件使用流式解析
        return self._parse_streaming(filepath, file_size)
    
    def _parse_streaming(self, filepath: str, file_size: int) -> MSGEmail:
        """流式解析实现"""
        email = MSGEmail()
        
        with open(filepath, 'rb') as f:
            # 1. 读取文件头（包含元数据）
            header = f.read(self.CHUNK_SIZE)
            self._parse_header(header, email)
            
            # 2. 检查内存使用
            self._check_memory_usage(file_size)
            
            # 3. 分块读取正文
            body_parts = []
            bytes_read = self.CHUNK_SIZE
            
            while bytes_read < file_size:
                # 检查是否取消
                chunk_size = min(self.CHUNK_SIZE, file_size - bytes_read)
                chunk = f.read(chunk_size)
                
                if not chunk:
                    break
                
                body_parts.append(chunk)
                bytes_read += chunk_size
                
                # 定期检查内存
                if len(body_parts) % 10 == 0:
                    self._check_memory_usage(file_size)
            
            # 4. 合并并解码正文
            body = b''.join(body_parts)
            email.body = self._decode_body(body)
        
        return email
    
    def _parse_header(self, header: bytes, email: MSGEmail):
        """解析MSG文件头"""
        try:
            text = header.decode('utf-8', errors='ignore')
            
            # 提取主题
            subject_match = re.search(r'Subject[:\s]+([^\r\n]+)', text, re.IGNORECASE)
            if subject_match:
                email.subject = subject_match.group(1).strip()
            
            # 提取发件人
            sender_match = re.search(r'Sender[:\s]+([^\r\n]+)', text, re.IGNORECASE)
            if sender_match:
                sender = sender_match.group(1).strip()
                email.sender = MSGParser._extract_name(sender)
                email.sender_email = MSGParser._extract_email(sender)
            
            # 提取日期
            date_match = re.search(r'Date[:\s]+([^\r\n]+)', text, re.IGNORECASE)
            if date_match:
                email.date = MSGParser._format_date(date_match.group(1).strip())
            
        except Exception:
            pass
    
    def _decode_body(self, body: bytes) -> str:
        """解码正文"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
        
        for encoding in encodings:
            try:
                return body.decode(encoding, errors='ignore')
            except Exception:
                continue
        
        return body.decode('utf-8', errors='ignore')
    
    def _check_memory_usage(self, file_size: int):
        """检查内存使用"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # 预估总内存使用（文件大小的2-3倍）
            estimated_usage = file_size * 2
            
            if memory_info.rss + estimated_usage > self.memory_limit:
                raise MemoryWarning(
                    f"内存使用将超过限制。"
                    f"当前: {memory_info.rss / 1024 / 1024:.1f}MB, "
                    f"限制: {self.memory_limit / 1024 / 1024:.1f}MB"
                )
        except ImportError:
            # psutil未安装，跳过内存检查
            pass


class MemoryWarning(Exception):
    """内存警告异常"""
    pass


class BatchMSGParser:
    """批量MSG文件解析器"""
    
    def __init__(self):
        self.parser = MSGParser()
        self.results: List[MSGEmail] = []
        self.errors: List[Dict[str, str]] = []
    
    def parse_directory(self, directory: str, 
                        recursive: bool = False,
                        progress_callback: Optional[Callable[[ParseProgress], None]] = None,
                        cancel_check: Optional[Callable[[], bool]] = None) -> List[MSGEmail]:
        """解析目录中的所有MSG文件
        
        Args:
            directory: 目录路径
            recursive: 是否递归子目录
            progress_callback: 进度回调函数
            cancel_check: 取消检查函数
            
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
        
        # 使用带进度的解析器
        if progress_callback or cancel_check:
            progress_parser = MSGParserWithProgress(
                progress_callback=progress_callback,
                cancel_check=cancel_check
            )
            self.results = progress_parser.parse_batch(msg_files)
            
            # 收集错误
            for filepath in msg_files:
                if not any(e.current_file == os.path.basename(filepath) 
                          for e in progress_parser.get_progress_history()):
                    self.errors.append({
                        'file': filepath,
                        'error': 'Not processed'
                    })
        else:
            # 原有逻辑
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
