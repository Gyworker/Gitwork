# -*- coding: utf-8 -*-
"""
Excel导入模块
支持从Excel文件导入通讯录数据
"""

import os
import re
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import pandas as pd
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

# 导入项目模块
from src.database.contacts import ContactsDB


@dataclass
class ExcelContact:
    """Excel联系人数据结构"""
    姓名: str = ""
    电话: str = ""
    邮箱: str = ""
    公司: str = ""
    部门: str = ""
    职位: str = ""
    备注: str = ""
    source: str = "excel"
    import_batch: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'ExcelContact':
        return cls(**data)


class ExcelHeaderMapper:
    """Excel表头映射器"""

    # 表头别名映射
    HEADER_MAPPINGS = {
        '姓名': ['姓名', 'name', '名称', '名字', 'contact'],
        '电话': ['电话', 'phone', '手机', 'mobile', 'tel', 'telephone', '号码'],
        '邮箱': ['邮箱', 'email', '邮件', 'e-mail', 'mail'],
        '公司': ['公司', 'company', '企业', 'organization', 'org'],
        '部门': ['部门', 'department', 'dept', '科室'],
        '职位': ['职位', 'position', 'title', '职务', 'job'],
        '备注': ['备注', 'remark', 'note', 'notes', '说明'],
    }

    @classmethod
    def find_header_mapping(cls, headers: List[str]) -> Dict[str, int]:
        """智能查找表头映射

        Args:
            headers: Excel列名列表

        Returns:
            字段名到列索引的映射
        """
        mapping = {}
        normalized_headers = [h.strip().lower() for h in headers]

        for field, aliases in cls.HEADER_MAPPINGS.items():
            for idx, header in enumerate(normalized_headers):
                if header in [a.lower() for a in aliases]:
                    mapping[field] = idx
                    break

        return mapping


class ExcelImporter:
    """Excel导入器"""

    def __init__(self, db: ContactsDB):
        self.db = db
        self.batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.last_import_path = ""
        self._import_records = []

    def import_from_file(self, file_path: str,
                        sheet_name: Optional[str] = None,
                        header_row: int = 1) -> Dict:
        """从Excel文件导入通讯录

        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称，None则读取第一个
            header_row: 表头所在行号

        Returns:
            导入结果字典
        """
        result = {
            'success': True,
            'total': 0,
            'added': 0,
            'duplicate': 0,
            'errors': [],
            'records': []
        }

        try:
            # 读取Excel文件
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path, sheet_name=sheet_name,
                                   header=header_row - 1, engine='openpyxl')
            elif file_path.endswith('.xls'):
                df = pd.read_excel(file_path, sheet_name=sheet_name,
                                   header=header_row - 1, engine='xlrd')
            else:
                raise ValueError(f"不支持的文件格式: {file_path}")

            # 获取表头映射
            headers = df.columns.tolist()
            header_map = ExcelHeaderMapper.find_header_mapping(headers)

            if '姓名' not in header_map:
                result['success'] = False
                result['errors'].append("无法识别姓名列")
                return result

            # 处理每一行数据
            for idx, row in df.iterrows():
                try:
                    contact = self._parse_row(row, header_map)
                    if contact.姓名:  # 姓名必填
                        result['records'].append(contact)
                        result['total'] += 1
                except Exception as e:
                    result['errors'].append(f"第{idx+2}行解析错误: {str(e)}")

            # 检测重复
            unique_records = []
            existing_contacts = self.db.get_all_contacts()
            existing_keys = set(
                f"{c.get('name', '')}|{c.get('phone', '')}"
                for c in existing_contacts
            )

            for record in result['records']:
                key = f"{record.姓名}|{record.电话}"
                if key not in existing_keys:
                    unique_records.append(record)
                    result['added'] += 1
                else:
                    result['duplicate'] += 1

            # 保存导入记录
            self._import_records = unique_records
            self.last_import_path = file_path

        except Exception as e:
            result['success'] = False
            result['errors'].append(f"文件读取错误: {str(e)}")

        return result

    def _parse_row(self, row: pd.Series, header_map: Dict[str, int]) -> ExcelContact:
        """解析单行数据"""
        contact = ExcelContact()
        contact.import_batch = self.batch_id

        for field, col_idx in header_map.items():
            if col_idx < len(row):
                value = str(row.iloc[col_idx]).strip()
                if value and value != 'nan':
                    setattr(contact, field, value)

        return contact

    def save_to_database(self) -> int:
        """保存到数据库"""
        saved = 0
        for record in self._import_records:
            self.db.add_contact(
                name=record.姓名,
                phone=record.电话,
                email=record.邮箱,
                company=record.公司,
                department=record.部门,
                position=record.职位,
                remark=record.备注,
                source=record.source,
                import_batch=record.import_batch,
                raw_data=json.dumps(record.to_dict(), ensure_ascii=False)
            )
            saved += 1
        return saved

    def save_to_excel(self, output_path: Optional[str] = None) -> str:
        """保存导入记录到Excel文件

        Args:
            output_path: 输出路径，None则使用默认路径

        Returns:
            保存的文件路径
        """
        if not self._import_records:
            raise ValueError("没有导入记录")

        if output_path is None:
            # 默认保存到data/imports目录
            imports_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'data', 'imports'
            )
            os.makedirs(imports_dir, exist_ok=True)
            output_path = os.path.join(
                imports_dir,
                f"contacts_{self.batch_id}.xlsx"
            )

        # 创建工作簿
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "导入通讯录"

        # 定义样式
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")

        # 写入表头
        headers = ['姓名', '电话', '邮箱', '公司', '部门', '职位', '备注', '导入批次']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment

        # 写入数据
        for row_idx, record in enumerate(self._import_records, 2):
            values = [
                record.姓名, record.电话, record.邮箱, record.公司,
                record.部门, record.职位, record.备注, record.import_batch
            ]
            for col_idx, value in enumerate(values, 1):
                ws.cell(row=row_idx, column=col_idx, value=value)

        # 自动调整列宽
        for col_idx in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col_idx)].width = 15

        # 保存文件
        wb.save(output_path)
        return output_path

    def load_from_excel(self, file_path: str) -> List[ExcelContact]:
        """从Excel文件读取已编辑的导入记录

        Args:
            file_path: Excel文件路径

        Returns:
            联系人列表
        """
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path, engine='openpyxl')
        else:
            df = pd.read_excel(file_path, engine='xlrd')

        headers = df.columns.tolist()
        header_map = ExcelHeaderMapper.find_header_mapping(headers)

        records = []
        for idx, row in df.iterrows():
            contact = self._parse_row(row, header_map)
            if contact.姓名:
                records.append(contact)

        self._import_records = records
        return records


class ExcelExporter:
    """Excel导出器"""

    def __init__(self, db: ContactsDB):
        self.db = db

    def export_all(self, output_path: str) -> str:
        """导出全部通讯录

        Args:
            output_path: 输出文件路径

        Returns:
            保存的文件路径
        """
        contacts = self.db.get_all_contacts()
        return self._create_excel(contacts, output_path)

    def export_filtered(self, output_path: str,
                       filters: Optional[Dict] = None) -> str:
        """导出筛选后的通讯录

        Args:
            output_path: 输出文件路径
            filters: 筛选条件

        Returns:
            保存的文件路径
        """
        contacts = self.db.search_contacts(
            keyword=filters.get('keyword', '') if filters else '',
            company=filters.get('company', '') if filters else ''
        )
        return self._create_excel(contacts, output_path)

    def _create_excel(self, contacts: List[Dict], output_path: str) -> str:
        """创建Excel文件"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "通讯录"

        # 表头样式
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")

        # 写入表头
        headers = ['姓名', '电话', '邮箱', '公司', '部门', '职位', '备注']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment

        # 写入数据
        for row_idx, contact in enumerate(contacts, 2):
            values = [
                contact.get('name', ''),
                contact.get('phone', ''),
                contact.get('email', ''),
                contact.get('company', ''),
                contact.get('department', ''),
                contact.get('position', ''),
                contact.get('remark', ''),
            ]
            for col_idx, value in enumerate(values, 1):
                ws.cell(row=row_idx, column=col_idx, value=value)

        # 自动调整列宽
        for col_idx in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col_idx)].width = 18

        # 保存
        wb.save(output_path)
        return output_path

    def create_template(self, output_path: str) -> str:
        """创建导入模板

        Args:
            output_path: 模板文件路径

        Returns:
            模板文件路径
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "通讯录模板"

        # 表头样式
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")

        # 写入表头
        headers = ['姓名*', '电话', '邮箱', '公司', '部门', '职位', '备注']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment

        # 添加示例数据
        example_data = [
            ['张三', '13800138000', 'zhangsan@example.com', '示例公司', '市场部', '经理', 'VIP客户'],
            ['李四', '13900139000', 'lisi@example.com', '示例公司', '销售部', '主管', ''],
        ]

        for row_idx, row_data in enumerate(example_data, 2):
            for col_idx, value in enumerate(row_data, 1):
                ws.cell(row=row_idx, column=col_idx, value=value)

        # 自动调整列宽
        for col_idx in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col_idx)].width = 18

        wb.save(output_path)
        return output_path
