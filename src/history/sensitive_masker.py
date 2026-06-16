# -*- coding: utf-8 -*-
"""
敏感数据脱敏处理器
对手机号、邮箱、身份证等敏感信息进行脱敏处理
"""

import re
from typing import Any, Optional, Dict, Callable


class SensitiveDataMasker:
    """
    敏感数据脱敏处理器
    
    支持的脱敏类型：
    - 手机号：138****8000
    - 邮箱：zhang***@example.com
    - 身份证：11****33
    - 银行卡：****1234
    """
    
    # 手机号正则
    PHONE_PATTERN = re.compile(r'^(\d{3})\d{4}(\d{4})$')
    
    # 邮箱正则
    EMAIL_PATTERN = re.compile(r'^([^@]{1,3})\*+([^@]+@.+)$')
    
    @classmethod
    def mask_phone(cls, phone: Optional[str]) -> Optional[str]:
        """
        手机号脱敏
        
        Args:
            phone: 手机号
            
        Returns:
            str: 脱敏后的手机号
        """
        if not phone:
            return phone
        
        phone = str(phone).strip()
        
        # 处理带国家码的情况
        if phone.startswith('+86'):
            phone = phone[3:]
        
        # 移除所有非数字字符
        clean_phone = re.sub(r'[^\d]', '', phone)
        
        # 检查是否为有效手机号（11位）
        if len(clean_phone) == 11:
            match = cls.PHONE_PATTERN.match(clean_phone)
            if match:
                return f"{match.group(1)}****{match.group(2)}"
        
        return phone
    
    @classmethod
    def mask_email(cls, email: Optional[str]) -> Optional[str]:
        """
        邮箱脱敏
        
        Args:
            email: 邮箱地址
            
        Returns:
            str: 脱敏后的邮箱
        """
        if not email:
            return email
        
        email = str(email).strip()
        
        if '@' not in email:
            return email
        
        parts = email.split('@')
        local_part = parts[0]
        domain_part = '@'.join(parts[1:])
        
        # 本地部分处理
        if len(local_part) > 3:
            masked_local = local_part[:3] + '***'
        elif len(local_part) > 1:
            masked_local = local_part[0] + '***'
        else:
            masked_local = '***'
        
        return f"{masked_local}@{domain_part}"
    
    @classmethod
    def mask_id_card(cls, id_card: Optional[str]) -> Optional[str]:
        """
        身份证号脱敏
        
        Args:
            id_card: 身份证号
            
        Returns:
            str: 脱敏后的身份证号
        """
        if not id_card:
            return id_card
        
        id_card = str(id_card).strip()
        
        if len(id_card) >= 8:
            return f"{id_card[:2]}******{id_card[-2:]}"
        
        return id_card
    
    @classmethod
    def mask_bank_card(cls, bank_card: Optional[str]) -> Optional[str]:
        """
        银行卡号脱敏
        
        Args:
            bank_card: 银行卡号
            
        Returns:
            str: 脱敏后的银行卡号
        """
        if not bank_card:
            return bank_card
        
        bank_card = str(bank_card).strip()
        
        # 移除空格和横线
        clean_card = re.sub(r'[\s-]', '', bank_card)
        
        if len(clean_card) >= 4:
            return f"****{clean_card[-4:]}"
        
        return bank_card
    
    @classmethod
    def mask_name(cls, name: Optional[str]) -> Optional[str]:
        """
        姓名脱敏（保留首尾字符）
        
        Args:
            name: 姓名
            
        Returns:
            str: 脱敏后的姓名
        """
        if not name:
            return name
        
        name = str(name).strip()
        
        if len(name) <= 1:
            return name
        elif len(name) == 2:
            return name[0] + '*'
        else:
            return name[0] + '*' * (len(name) - 2) + name[-1]
    
    @classmethod
    def mask_field(cls, field_name: str, value: Any) -> Any:
        """
        通用字段脱敏
        
        根据字段名自动选择脱敏方法
        
        Args:
            field_name: 字段名
            value: 字段值
            
        Returns:
            脱敏后的值
        """
        field_name_lower = field_name.lower()
        
        # 敏感字段映射
        sensitive_fields = {
            'phone': cls.mask_phone,
            'mobile': cls.mask_phone,
            'tel': cls.mask_phone,
            'telephone': cls.mask_phone,
            'email': cls.mask_email,
            'e_mail': cls.mask_email,
            'mail': cls.mask_email,
            'id_card': cls.mask_id_card,
            'idcard': cls.mask_id_card,
            'identity': cls.mask_id_card,
            'bank_card': cls.mask_bank_card,
            'bankcard': cls.mask_bank_card,
            'card_no': cls.mask_bank_card,
            'account': cls.mask_bank_card,
            'name': cls.mask_name,
            'username': cls.mask_name,
            'real_name': cls.mask_name,
        }
        
        mask_func = sensitive_fields.get(field_name_lower)
        
        if mask_func:
            return mask_func(value)
        
        return value
    
    @classmethod
    def mask_dict(cls, data: Dict[str, Any], sensitive_fields: list = None) -> Dict[str, Any]:
        """
        对字典中的敏感字段进行脱敏
        
        Args:
            data: 原始数据字典
            sensitive_fields: 敏感字段列表，如果为None使用默认列表
            
        Returns:
            Dict: 脱敏后的数据
        """
        if sensitive_fields is None:
            sensitive_fields = [
                'phone', 'mobile', 'tel', 'email',
                'id_card', 'idcard', 'bank_card', 'name'
            ]
        
        masked_data = data.copy()
        
        for field in sensitive_fields:
            if field in masked_data:
                masked_data[field] = cls.mask_field(field, masked_data[field])
        
        return masked_data
    
    @classmethod
    def mask_operation_record(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        对操作记录进行脱敏
        
        Args:
            record: 操作记录字典
            
        Returns:
            Dict: 脱敏后的记录
        """
        masked_record = record.copy()
        
        # 脱敏before_value
        if 'before_value' in record and record['before_value']:
            try:
                import json
                if isinstance(record['before_value'], str):
                    before = json.loads(record['before_value'])
                else:
                    before = record['before_value']
                
                if isinstance(before, dict):
                    masked_record['before_value'] = json.dumps(
                        cls.mask_dict(before), ensure_ascii=False
                    )
            except (json.JSONDecodeError, TypeError):
                pass
        
        # 脱敏after_value
        if 'after_value' in record and record['after_value']:
            try:
                import json
                if isinstance(record['after_value'], str):
                    after = json.loads(record['after_value'])
                else:
                    after = record['after_value']
                
                if isinstance(after, dict):
                    masked_record['after_value'] = json.dumps(
                        cls.mask_dict(after), ensure_ascii=False
                    )
            except (json.JSONDecodeError, TypeError):
                pass
        
        return masked_record


# 便捷函数
def mask_phone(phone: str) -> str:
    """手机号脱敏"""
    return SensitiveDataMasker.mask_phone(phone)


def mask_email(email: str) -> str:
    """邮箱脱敏"""
    return SensitiveDataMasker.mask_email(email)


def mask_id_card(id_card: str) -> str:
    """身份证脱敏"""
    return SensitiveDataMasker.mask_id_card(id_card)


def mask_sensitive(value: Any, field_name: str) -> Any:
    """通用敏感数据脱敏"""
    return SensitiveDataMasker.mask_field(field_name, value)
