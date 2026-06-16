# -*- coding: utf-8 -*-
"""
数据验证模块
Validation Module

提供数据验证功能
"""

import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from datetime import datetime

from .exceptions import ValidationException


class Validator:
    """验证器基类"""

    def __init__(self, error_message: Optional[str] = None) -> None:
        """
        初始化验证器

        Args:
            error_message: 自定义错误消息
        """
        self.error_message = error_message or "验证失败"

    def validate(self, value: Any) -> bool:
        """
        验证值

        Args:
            value: 要验证的值

        Returns:
            是否验证通过
        """
        raise NotImplementedError

    def get_error_message(self) -> str:
        """获取错误消息"""
        return self.error_message


class RequiredValidator(Validator):
    """必填验证器"""

    def __init__(self, field_name: str = "字段") -> None:
        super().__init__(f"{field_name}不能为空")

    def validate(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False
        if isinstance(value, (list, dict)) and not value:
            return False
        return True


class LengthValidator(Validator):
    """长度验证器"""

    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        field_name: str = "字段",
    ) -> None:
        self.min_length = min_length
        self.max_length = max_length
        self.field_name = field_name

        if min_length and max_length:
            message = f"{field_name}长度必须在{min_length}到{max_length}之间"
        elif min_length:
            message = f"{field_name}长度不能少于{min_length}"
        elif max_length:
            message = f"{field_name}长度不能超过{max_length}"
        else:
            message = f"{field_name}长度不符合要求"

        super().__init__(message)

    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        length = len(str(value))
        if self.min_length is not None and length < self.min_length:
            return False
        if self.max_length is not None and length > self.max_length:
            return False
        return True


class EmailValidator(Validator):
    """邮箱验证器"""

    def __init__(self) -> None:
        super().__init__("邮箱格式不正确")

    def validate(self, value: Any) -> bool:
        if not value:
            return True
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, str(value)))


class PhoneValidator(Validator):
    """手机号验证器"""

    def __init__(self) -> None:
        super().__init__("手机号格式不正确")

    def validate(self, value: Any) -> bool:
        if not value:
            return True
        pattern = r"^1[3-9]\d{9}$"
        return bool(re.match(pattern, str(value)))


class RegexValidator(Validator):
    """正则验证器"""

    def __init__(self, pattern: str, error_message: str = "格式不正确") -> None:
        super().__init__(error_message)
        self.pattern = re.compile(pattern)

    def validate(self, value: Any) -> bool:
        if not value:
            return True
        return bool(self.pattern.match(str(value)))


class RangeValidator(Validator):
    """范围验证器"""

    def __init__(
        self,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        field_name: str = "值",
    ) -> None:
        self.min_value = min_value
        self.max_value = max_value
        self.field_name = field_name

        if min_value and max_value:
            message = f"{field_name}必须在{min_value}到{max_value}之间"
        elif min_value:
            message = f"{field_name}不能小于{min_value}"
        elif max_value:
            message = f"{field_name}不能大于{max_value}"
        else:
            message = f"{field_name}超出范围"

        super().__init__(message)

    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        try:
            num_value = float(value)
            if self.min_value is not None and num_value < self.min_value:
                return False
            if self.max_value is not None and num_value > self.max_value:
                return False
            return True
        except (ValueError, TypeError):
            return False


class DateTimeValidator(Validator):
    """日期时间验证器"""

    def __init__(self, format_string: str = "%Y-%m-%d %H:%M:%S") -> None:
        super().__init__(f"日期格式不正确，应为{format_string}")
        self.format_string = format_string

    def validate(self, value: Any) -> bool:
        if not value:
            return True
        if isinstance(value, datetime):
            return True
        try:
            datetime.strptime(str(value), self.format_string)
            return True
        except ValueError:
            return False


class EnumValidator(Validator):
    """枚举验证器"""

    def __init__(self, allowed_values: List[Any], field_name: str = "值") -> None:
        super().__init__(f"{field_name}必须是以下值之一: {', '.join(map(str, allowed_values))}")
        self.allowed_values = allowed_values

    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        return value in self.allowed_values


class ValidatorChain:
    """验证器链"""

    def __init__(self) -> None:
        self._validators: List[Tuple[Validator, str]] = []

    def add(self, validator: Validator, field_name: str = "field") -> "ValidatorChain":
        """
        添加验证器

        Args:
            validator: 验证器实例
            field_name: 字段名称

        Returns:
            self
        """
        self._validators.append((validator, field_name))
        return self

    def required(self, field_name: str = "field") -> "ValidatorChain":
        """添加必填验证"""
        return self.add(RequiredValidator(field_name), field_name)

    def length(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        field_name: str = "field",
    ) -> "ValidatorChain":
        """添加长度验证"""
        return self.add(LengthValidator(min_length, max_length, field_name), field_name)

    def email(self, field_name: str = "email") -> "ValidatorChain":
        """添加邮箱验证"""
        return self.add(EmailValidator(), field_name)

    def phone(self, field_name: str = "phone") -> "ValidatorChain":
        """添加手机号验证"""
        return self.add(PhoneValidator(), field_name)

    def range(
        self,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        field_name: str = "value",
    ) -> "ValidatorChain":
        """添加范围验证"""
        return self.add(RangeValidator(min_value, max_value, field_name), field_name)

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证数据

        Args:
            data: 要验证的数据字典

        Returns:
            (是否验证通过, 错误消息列表)
        """
        errors = []

        for validator, field_name in self._validators:
            value = data.get(field_name)
            if not validator.validate(value):
                errors.append(f"{field_name}: {validator.get_error_message()}")

        return len(errors) == 0, errors


class TaskValidator:
    """任务数据验证器"""

    @staticmethod
    def validate_task_name(name: str) -> bool:
        """验证任务名称"""
        if not name or not name.strip():
            raise ValidationException("任务名称不能为空", field="task_name")
        if len(name) > 200:
            raise ValidationException("任务名称不能超过200个字符", field="task_name")
        return True

    @staticmethod
    def validate_email(email: str) -> bool:
        """验证邮箱"""
        if email and not EmailValidator().validate(email):
            raise ValidationException("邮箱格式不正确", field="email")
        return True

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """验证手机号"""
        if phone and not PhoneValidator().validate(phone):
            raise ValidationException("手机号格式不正确", field="phone")
        return True

    @staticmethod
    def validate_status(status: str) -> bool:
        """验证状态"""
        allowed_statuses = ["进行中", "挂起", "已答复", "完成"]
        if status not in allowed_statuses:
            raise ValidationException(
                f"状态必须是以下值之一: {', '.join(allowed_statuses)}",
                field="status"
            )
        return True

    @staticmethod
    def validate_urgency(urgency: str) -> bool:
        """验证重要程度"""
        allowed_urgencies = ["低", "中", "高"]
        if urgency not in allowed_urgencies:
            raise ValidationException(
                f"重要程度必须是以下值之一: {', '.join(allowed_urgencies)}",
                field="urgency"
            )
        return True
