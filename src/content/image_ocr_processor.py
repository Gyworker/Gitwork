# -*- coding: utf-8 -*-
"""
图片OCR处理器
为ContentParserService提供OCR识别功能

版本：V4.3
"""

import os
import re
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass

from src.core.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# 常量定义
# =============================================================================

# 支持的图片格式
SUPPORTED_IMAGE_FORMATS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')

# 电话号码正则表达式
PHONE_PATTERN = re.compile(
    r'(?:电话|TEL|手机|Mobile|Phone)?[:：]?\s*'
    r'(\+?86)?\s*'
    r'(?:1[3-9]\d{9}|(?:010|021|022|023|024|025|027|028|029)\d{7,8})'
)

# 邮箱正则表达式
EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
)

# 常见职位关键词
POSITION_KEYWORDS = [
    '经理', '总监', '主管', '负责人', '主任', '工程师',
    'Consultant', 'Manager', 'Director', 'Chief', 'CEO', 'CTO', 'CFO',
    'President', 'Vice', 'Senior', 'Lead', 'Head'
]

# 常见部门关键词
DEPARTMENT_KEYWORDS = [
    '部', '部门', '科', '室',
    'Department', 'Dept', 'Division', 'Team'
]

# 公司关键词
COMPANY_KEYWORDS = ['公司', '有限公司', 'Co.', 'Ltd', 'Corp', 'Inc']

# 地址关键词
ADDRESS_KEYWORDS = ['地址', 'Address', '市', '区', '路', '街', '号']


# =============================================================================
# 数据结构
# =============================================================================

@dataclass
class OCRContactInfo:
    """OCR识别的联系人信息"""
    name: str = ""
    phone: str = ""
    email: str = ""
    company: str = ""
    department: str = ""
    position: str = ""
    address: str = ""
    confidence: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'company': self.company,
            'department': self.department,
            'position': self.position,
            'address': self.address,
            'confidence': self.confidence,
        }


@dataclass
class OCRResult:
    """OCR识别结果"""
    success: bool = False
    raw_text: str = ""
    contact_info: Optional[OCRContactInfo] = None
    task_name: str = ""
    task_content: str = ""
    error: Optional[str] = None
    error_details: Optional[str] = None
    process_time_ms: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'raw_text': self.raw_text,
            'contact_info': self.contact_info.to_dict() if self.contact_info else {},
            'task_name': self.task_name,
            'task_content': self.task_content,
            'error': self.error,
            'error_details': self.error_details,
            'process_time_ms': self.process_time_ms,
        }


# =============================================================================
# OCR处理器
# =============================================================================

class ImageOCRProcessor:
    """
    图片OCR处理器
    支持名片、海报、文档等图片的文字识别
    """

    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        初始化OCR处理器

        Args:
            tesseract_cmd: Tesseract可执行文件路径（可选）
        """
        self.tesseract_cmd = tesseract_cmd
        self._is_available = None

    @property
    def is_available(self) -> bool:
        """检查OCR是否可用"""
        if self._is_available is not None:
            return self._is_available

        try:
            import pytesseract
            from PIL import Image

            # 如果指定了tesseract路径
            if self.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

            # 测试OCR是否可用
            test_image = Image.new('RGB', (100, 100))
            pytesseract.image_to_string(test_image, lang='chi_sim+eng')
            self._is_available = True
            logger.info("OCR库可用")

        except ImportError as e:
            logger.warning(f"OCR库未安装: {e}")
            self._is_available = False
        except Exception as e:
            logger.warning(f"OCR库不可用: {e}")
            self._is_available = False

        return self._is_available

    def process_image(self, image_path: str) -> OCRResult:
        """
        处理图片并提取文字

        Args:
            image_path: 图片文件路径

        Returns:
            OCRResult: 识别结果
        """
        import time
        start_time = time.perf_counter()

        result = OCRResult()

        # 检查是否可用
        if not self.is_available:
            result.error = "OCR库不可用"
            result.error_details = "请安装: pip install pytesseract pillow"
            return result

        # 验证文件
        if not image_path or not os.path.exists(image_path):
            result.error = "图片文件不存在"
            result.error_details = image_path
            return result

        # 检查文件格式
        ext = os.path.splitext(image_path)[1].lower()
        if ext not in SUPPORTED_IMAGE_FORMATS:
            result.error = "不支持的图片格式"
            result.error_details = f"支持格式: {', '.join(SUPPORTED_IMAGE_FORMATS)}"
            return result

        try:
            # 导入图像处理库
            from PIL import Image, ImageEnhance, ImageFilter
            import pytesseract

            # 打开并预处理图片
            image = Image.open(image_path)

            # 转换为灰度图（提高OCR准确率）
            if image.mode != 'L':
                image = image.convert('L')

            # 提高对比度
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)

            # 锐化
            image = image.filter(ImageFilter.SHARPEN)

            # OCR识别
            raw_text = pytesseract.image_to_string(
                image,
                lang='chi_sim+eng',
                config='--psm 6'  # 假设统一文本块
            )

            result.success = True
            result.raw_text = raw_text

            # 提取联系人信息
            result.contact_info = self._extract_contact_info(raw_text)

            # 生成任务内容
            result.task_content = self._generate_task_content(raw_text, result.contact_info)
            result.task_name = self._generate_task_name(result.contact_info)

            result.process_time_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"OCR识别成功: {image_path}, 耗时: {result.process_time_ms:.2f}ms")

        except ImportError as e:
            result.error = "OCR库导入失败"
            result.error_details = str(e)
            logger.error(f"OCR导入异常: {e}")
        except Exception as e:
            result.error = "OCR识别失败"
            result.error_details = str(e)
            logger.error(f"OCR处理异常: {e}")

        return result

    def _extract_contact_info(self, text: str) -> OCRContactInfo:
        """从识别的文本中提取联系人信息"""
        info = OCRContactInfo()
        confidence_factors = []

        lines = text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 提取电话号码
            phone_match = PHONE_PATTERN.search(line)
            if phone_match and not info.phone:
                info.phone = phone_match.group(0)
                confidence_factors.append(0.3)

            # 提取邮箱
            email_match = EMAIL_PATTERN.search(line)
            if email_match and not info.email:
                info.email = email_match.group(0)
                confidence_factors.append(0.2)

            # 提取姓名（通常在第一行或靠近电话/邮箱）
            if not info.name and self._is_name_line(line):
                info.name = line[:20]  # 限制长度
                confidence_factors.append(0.3)

            # 提取公司
            if any(kw in line for kw in COMPANY_KEYWORDS) and not info.company:
                info.company = line[:50]
                confidence_factors.append(0.1)

            # 提取部门
            if any(kw in line for kw in DEPARTMENT_KEYWORDS) and not info.department:
                info.department = line[:30]
                confidence_factors.append(0.05)

            # 提取职位
            if any(kw in line for kw in POSITION_KEYWORDS) and not info.position:
                info.position = line[:30]
                confidence_factors.append(0.05)

            # 提取地址
            if any(kw in line for kw in ADDRESS_KEYWORDS) and not info.address:
                info.address = line[:100]
                confidence_factors.append(0.05)

        # 计算置信度
        info.confidence = sum(confidence_factors) if confidence_factors else 0.0

        return info

    def _is_name_line(self, line: str) -> bool:
        """判断是否为姓名行"""
        # 姓名通常2-4个汉字或英文名
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', line))
        english_chars = len(re.findall(r'[a-zA-Z]', line))

        # 排除包含特殊字符和关键词的行
        excluded_keywords = ['电话', '手机', '邮箱', 'email', 'phone', '公司', '部门', '地址']
        if any(kw in line for kw in excluded_keywords):
            return False

        # 姓名特征：主要是中文字符或纯英文
        if chinese_chars >= 2 and chinese_chars <= 5 and len(line) <= 10:
            return True
        if english_chars >= 2 and english_chars <= 20 and len(line) <= 25:
            return True

        return False

    def _generate_task_name(self, contact_info: OCRContactInfo) -> str:
        """生成任务名称"""
        if contact_info.name:
            return f"【咨询】{contact_info.name}"
        if contact_info.company:
            return f"【咨询】{contact_info.company}"
        return "【图片识别】任务咨询"

    def _generate_task_content(self, raw_text: str, contact_info: OCRContactInfo) -> str:
        """生成任务内容"""
        content_parts = []

        # 添加标题
        content_parts.append("【图片OCR识别内容】")
        content_parts.append("=" * 50)

        # 添加原始文本
        content_parts.append("\n【原始识别文本】\n")
        content_parts.append(raw_text)

        # 添加提取的联系人信息
        if contact_info.name or contact_info.phone or contact_info.email:
            content_parts.append("\n【提取的联系人信息】")
            if contact_info.name:
                content_parts.append(f"姓名: {contact_info.name}")
            if contact_info.phone:
                content_parts.append(f"电话: {contact_info.phone}")
            if contact_info.email:
                content_parts.append(f"邮箱: {contact_info.email}")
            if contact_info.company:
                content_parts.append(f"公司: {contact_info.company}")
            if contact_info.department:
                content_parts.append(f"部门: {contact_info.department}")
            if contact_info.position:
                content_parts.append(f"职位: {contact_info.position}")
            if contact_info.address:
                content_parts.append(f"地址: {contact_info.address}")
            content_parts.append(f"\n识别置信度: {contact_info.confidence:.1%}")

        return '\n'.join(content_parts)


# =============================================================================
# 单例实例
# =============================================================================

_ocr_processor: Optional[ImageOCRProcessor] = None


def get_ocr_processor() -> ImageOCRProcessor:
    """获取OCR处理器单例"""
    global _ocr_processor
    if _ocr_processor is None:
        _ocr_processor = ImageOCRProcessor()
    return _ocr_processor
