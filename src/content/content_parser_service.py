# -*- coding: utf-8 -*-
"""
内容解析服务层
将UI层与业务逻辑分离，提供统一的内容解析接口

版本：V4.1
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
import os

from src.content.msg_parser import MSGParser, MSGEmail, ParseError as MSGParseError
from src.content.image_ocr_processor import get_ocr_processor, ImageOCRProcessor
from src.core.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# 数据结构
# =============================================================================

@dataclass
class ParsedContent:
    """解析后的内容数据"""
    # 基本信息
    task_name: str = ""
    task_content: str = ""
    source: str = "unknown"
    
    # 来源信息
    source_type: str = "unknown"  # text, image, msg, wechat
    source_file: Optional[str] = None
    import_time: datetime = field(default_factory=datetime.now)
    
    # 任务相关字段
    consultant_name: str = ""
    consultant_contact: str = ""
    consultant_dept: str = ""
    key_module: str = ""
    product_model: str = ""
    
    # MSG邮件特有字段
    sender: Optional[str] = None
    sender_email: Optional[str] = None
    email_date: Optional[str] = None
    email_importance: Optional[str] = None
    email_attachments: List[str] = field(default_factory=list)
    
    # 原始数据
    raw_data: Optional[Any] = None
    
    # 错误信息
    error: Optional[str] = None
    error_details: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            'task_name': self.task_name,
            'task_content': self.task_content,
            'source': self.source,
            'source_type': self.source_type,
            'consultant_name': self.consultant_name,
            'consultant_contact': self.consultant_contact,
            'consultant_dept': self.consultant_dept,
            'key_module': self.key_module,
            'product_model': self.product_model,
        }
        
        if self.sender:
            result['sender'] = self.sender
        if self.sender_email:
            result['sender_email'] = self.sender_email
            
        return result
    
    @property
    def is_success(self) -> bool:
        """判断解析是否成功"""
        return self.error is None and bool(self.task_content)
    
    @property
    def preview(self) -> str:
        """获取预览文本"""
        if self.error:
            return f"解析失败: {self.error}"
        
        preview = f"【主题】{self.task_name or '无标题'}\n"
        if self.sender:
            preview += f"【发件人】{self.sender}"
            if self.sender_email:
                preview += f" <{self.sender_email}>"
            preview += "\n"
        if self.email_date:
            preview += f"【时间】{self.email_date}\n"
        if self.email_importance:
            preview += f"【重要程度】{self.email_importance}\n"
        
        preview += "\n" + "="*50 + "\n"
        preview += "【内容预览】\n"
        content_preview = self.task_content[:500] if self.task_content else "(无内容)"
        preview += content_preview
        if len(self.task_content or '') > 500:
            preview += "\n...(内容过长，已截断)"
        
        if self.email_attachments:
            preview += "\n\n" + "="*50 + "\n"
            preview += f"【附件】{len(self.email_attachments)}个\n"
            for att in self.email_attachments[:5]:
                preview += f"  - {att}\n"
            if len(self.email_attachments) > 5:
                preview += f"  ...等{len(self.email_attachments)}个附件"
        
        return preview


# =============================================================================
# 解析器接口
# =============================================================================

class ContentParser(ABC):
    """内容解析器基类"""
    
    @property
    @abstractmethod
    def parser_type(self) -> str:
        """解析器类型"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查解析器是否可用"""
        pass
    
    @abstractmethod
    def parse(self, content: str) -> ParsedContent:
        """
        解析内容
        
        Args:
            content: 输入内容（文本或文件路径）
            
        Returns:
            ParsedContent: 解析结果
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """获取解析器信息"""
        return {
            'type': self.parser_type,
            'available': self.is_available(),
        }


# =============================================================================
# 文本解析器
# =============================================================================

class TextParser(ContentParser):
    """文本内容解析器"""
    
    @property
    def parser_type(self) -> str:
        return "text"
    
    def is_available(self) -> bool:
        """文本解析器始终可用"""
        return True
    
    def parse(self, content: str) -> ParsedContent:
        """解析文本内容"""
        result = ParsedContent()
        result.source_type = "text"
        result.source = "text"
        
        try:
            if not content or not content.strip():
                result.error = "内容为空"
                return result
            
            # 提取任务名称（取前50个字符）
            result.task_name = content[:50].strip() if len(content) > 50 else content.strip()
            result.task_content = content.strip()
            
            # 简单的内容分析 - 尝试提取联系方式
            result.task_content = content.strip()
            
            logger.info(f"文本解析成功，长度: {len(content)}")
            
        except Exception as e:
            result.error = "文本解析失败"
            result.error_details = str(e)
            logger.error(f"文本解析异常: {e}")
        
        return result


# =============================================================================
# MSG邮件解析器
# =============================================================================

class MSGParserWrapper(ContentParser):
    """MSG邮件解析器包装器"""
    
    @property
    def parser_type(self) -> str:
        return "msg"
    
    def is_available(self) -> bool:
        """检查MSG解析库是否可用"""
        return MSGParser.is_available()
    
    def parse(self, content: str) -> ParsedContent:
        """解析MSG邮件文件"""
        result = ParsedContent()
        result.source_type = "msg"
        result.source = "msg"
        
        # 检查库是否可用
        if not self.is_available():
            result.error = "MSG解析库未安装"
            result.error_details = "请安装: pip install extract-msg"
            return result
        
        # 验证文件路径
        filepath = content.strip()
        if not filepath:
            result.error = "文件路径为空"
            return result
        
        if not filepath.lower().endswith('.msg'):
            result.error = "文件格式不正确"
            result.error_details = "请选择.msg格式的Outlook邮件文件"
            return result
        
        # 安全检查
        if not os.path.exists(filepath):
            result.error = "文件不存在"
            result.error_details = filepath
            return result
        
        result.source_file = filepath
        
        try:
            # 解析MSG文件
            email = MSGParser.parse_file_safe(filepath)
            
            # 填充解析结果
            result.task_name = email.subject or '无主题邮件'
            result.task_content = email.to_task_content()
            
            # 提取发件人信息
            result.sender = email.sender
            result.sender_email = email.sender_email
            result.email_date = email.date
            result.email_importance = email.importance
            result.email_attachments = email.attachments
            
            # 尝试从邮件中提取咨询者信息
            if email.sender:
                result.consultant_name = email.sender
            if email.sender_email:
                result.consultant_contact = email.sender_email
            
            logger.info(f"MSG解析成功: {email.subject}")
            
        except MSGParseError as e:
            result.error = "MSG解析错误"
            result.error_details = str(e)
            logger.error(f"MSG解析异常: {e}")
        except ImportError as e:
            result.error = "库导入失败"
            result.error_details = str(e)
            logger.error(f"MSG库导入失败: {e}")
        except Exception as e:
            result.error = "解析失败"
            result.error_details = str(e)
            logger.error(f"MSG解析未知异常: {e}")
        
        return result
    
    def get_info(self) -> Dict[str, Any]:
        """获取MSG解析器详细信息"""
        info = super().get_info()
        lib_info = MSGParser.get_library_info()
        info.update({
            'library_name': lib_info.get('library', 'unknown'),
            'library_version': lib_info.get('version', 'unknown'),
            'security_enabled': True,
        })
        return info


# =============================================================================
# 图片OCR解析器
# =============================================================================

class ImageParser(ContentParser):
    """图片OCR解析器"""
    
    @property
    def parser_type(self) -> str:
        return "image"
    
    def is_available(self) -> bool:
        """检查OCR库是否可用"""
        try:
            import pytesseract
            return True
        except ImportError:
            return False
    
    def parse(self, content: str) -> ParsedContent:
        """
        解析图片（OCR识别）
        
        Args:
            content: 图片文件路径
            
        Returns:
            ParsedContent: 解析结果
        """
        result = ParsedContent()
        result.source_type = "image"
        result.source = "image"
        
        filepath = content.strip()
        if not filepath:
            result.error = "图片路径为空"
            return result
        
        if not os.path.exists(filepath):
            result.error = "图片文件不存在"
            result.error_details = filepath
            return result
        
        result.source_file = filepath
        
        try:
            # 获取OCR处理器
            ocr = get_ocr_processor()
            
            if not ocr.is_available:
                result.error = "OCR库不可用"
                result.error_details = "请安装: pip install pytesseract pillow"
                result.task_name = '图片识别任务'
                result.task_content = '[OCR功能未启用]'
                return result
            
            # 执行OCR识别
            ocr_result = ocr.process_image(filepath)
            
            if ocr_result.success:
                result.task_name = ocr_result.task_name
                result.task_content = ocr_result.task_content
                
                # 填充联系人信息
                if ocr_result.contact_info:
                    if ocr_result.contact_info.name:
                        result.consultant_name = ocr_result.contact_info.name
                    if ocr_result.contact_info.phone:
                        result.consultant_contact = ocr_result.contact_info.phone
                    if ocr_result.contact_info.company:
                        result.source = ocr_result.contact_info.company
                
                logger.info(f"图片OCR识别成功: {filepath}")
            else:
                result.error = ocr_result.error or "OCR识别失败"
                result.error_details = ocr_result.error_details
                result.task_name = '图片识别任务'
                result.task_content = ocr_result.raw_text or '[OCR识别失败]'
            
        except Exception as e:
            result.error = "OCR识别失败"
            result.error_details = str(e)
            logger.error(f"OCR异常: {e}")
        
        return result


# =============================================================================
# 企业微信解析器
# =============================================================================

class WeChatParser(ContentParser):
    """企业微信解析器"""
    
    @property
    def parser_type(self) -> str:
        return "wechat"
    
    def is_available(self) -> bool:
        """企业微信解析器始终可用（占位）"""
        return True
    
    def parse(self, content: str) -> ParsedContent:
        """解析企业微信聊天记录"""
        result = ParsedContent()
        result.source_type = "wechat"
        result.source = "wechat"
        
        # TODO: 实现企业微信解析
        result.task_name = '企业微信任务'
        result.task_content = content
        result.error = "企业微信解析功能待实现"
        
        return result


# =============================================================================
# 内容解析服务
# =============================================================================

class ContentParserService:
    """
    内容解析服务
    统一管理各种内容解析器
    """
    
    # 支持的解析类型
    SUPPORTED_TYPES = ['text', 'image', 'msg', 'wechat']
    
    def __init__(self):
        """初始化解析服务"""
        self._parsers: Dict[str, ContentParser] = {}
        self._default_parser: str = 'text'
        self._init_parsers()
    
    def _init_parsers(self):
        """初始化所有解析器"""
        # 文本解析器
        self._parsers['text'] = TextParser()
        
        # MSG邮件解析器
        self._parsers['msg'] = MSGParserWrapper()
        
        # 图片解析器
        self._parsers['image'] = ImageParser()
        
        # 企业微信解析器
        self._parsers['wechat'] = WeChatParser()
    
    def get_parser(self, source_type: str) -> Optional[ContentParser]:
        """获取指定类型的解析器"""
        return self._parsers.get(source_type)
    
    def parse(self, content: str, source_type: str = None) -> ParsedContent:
        """
        解析内容
        
        Args:
            content: 内容（文本或文件路径）
            source_type: 来源类型，不指定则自动检测
            
        Returns:
            ParsedContent: 解析结果
        """
        # 自动检测类型
        if source_type is None:
            source_type = self._detect_type(content)
        
        # 获取解析器
        parser = self.get_parser(source_type)
        if parser is None:
            result = ParsedContent()
            result.error = f"不支持的解析类型: {source_type}"
            return result
        
        # 执行解析
        return parser.parse(content)
    
    def _detect_type(self, content: str) -> str:
        """自动检测内容类型"""
        content = content.strip()
        
        # 如果是文件路径
        if os.path.exists(content):
            if content.lower().endswith('.msg'):
                return 'msg'
            elif content.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                return 'image'
        
        # 如果是文本内容
        return 'text'
    
    def get_available_parsers(self) -> List[Dict[str, Any]]:
        """获取所有可用的解析器"""
        return [
            parser.get_info() 
            for parser in self._parsers.values()
        ]
    
    def check_dependencies(self) -> Dict[str, bool]:
        """检查所有依赖是否可用"""
        return {
            name: parser.is_available()
            for name, parser in self._parsers.items()
        }


# =============================================================================
# 进度回调解析器（带进度显示）
# =============================================================================

class ProgressParser:
    """
    带进度的解析器
    适用于批量文件解析场景
    """
    
    def __init__(self, 
                 source_type: str = 'msg',
                 progress_callback: Optional[Callable[[int, int, str], None]] = None):
        """
        初始化进度解析器
        
        Args:
            source_type: 解析类型
            progress_callback: 进度回调 (current, total, status)
        """
        self.source_type = source_type
        self.progress_callback = progress_callback
        self.service = ContentParserService()
        self.parser = self.service.get_parser(source_type)
    
    def parse_files(self, 
                    file_paths: List[str],
                    progress_callback: Optional[Callable[[int, int, str], None]] = None) -> List[ParsedContent]:
        """
        批量解析文件
        
        Args:
            file_paths: 文件路径列表
            progress_callback: 进度回调
            
        Returns:
            解析结果列表
        """
        callback = progress_callback or self.progress_callback
        results = []
        total = len(file_paths)
        
        for idx, filepath in enumerate(file_paths, 1):
            # 报告进度
            if callback:
                callback(idx, total, f"正在解析: {os.path.basename(filepath)}")
            
            # 解析文件
            result = self.parser.parse(filepath)
            results.append(result)
        
        # 完成
        if callback:
            callback(total, total, "解析完成")
        
        return results
    
    def parse_with_retry(self,
                         content: str,
                         max_retries: int = 3) -> ParsedContent:
        """
        带重试的解析
        
        Args:
            content: 内容
            max_retries: 最大重试次数
        """
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                result = self.parser.parse(content)
                if result.is_success:
                    return result
                last_error = result.error
            except Exception as e:
                last_error = str(e)
                logger.warning(f"解析重试 {attempt}/{max_retries}: {e}")
        
        # 返回错误结果
        result = ParsedContent()
        result.error = f"解析失败（已重试{max_retries}次）"
        result.error_details = last_error
        return result


# =============================================================================
# 单例实例
# =============================================================================

_parser_service: Optional[ContentParserService] = None


def get_parser_service() -> ContentParserService:
    """获取解析服务单例"""
    global _parser_service
    if _parser_service is None:
        _parser_service = ContentParserService()
    return _parser_service
