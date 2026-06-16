# -*- coding: utf-8 -*-
"""
Excel工具模块
提供公共的Excel操作功能
版本：V2.1
"""

from typing import List, Dict, Optional, Any
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# =============================================================================
# 样式常量
# =============================================================================

# 默认表头样式颜色
DEFAULT_HEADER_COLOR = "4472C4"
GREEN_HEADER_COLOR = "70AD47"

# 默认列宽
DEFAULT_COLUMN_WIDTH = 15

# 边框样式
DEFAULT_BORDER = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)


# =============================================================================
# 样式工厂函数
# =============================================================================

def create_header_style(color: str = DEFAULT_HEADER_COLOR) -> Dict[str, Any]:
    """创建表头样式

    Args:
        color: 背景颜色 (RGB十六进制)

    Returns:
        样式字典
    """
    return {
        'font': Font(bold=True, color="FFFFFF"),
        'fill': PatternFill(start_color=color, end_color=color, fill_type="solid"),
        'alignment': Alignment(horizontal="center", vertical="center"),
    }


def apply_style_to_cell(cell, style: Dict[str, Any]):
    """应用样式到单元格

    Args:
        cell: openpyxl单元格对象
        style: 样式字典
    """
    if 'font' in style:
        cell.font = style['font']
    if 'fill' in style:
        cell.fill = style['fill']
    if 'alignment' in style:
        cell.alignment = style['alignment']
    if 'border' in style:
        cell.border = style['border']


# =============================================================================
# Excel操作函数
# =============================================================================

def create_excel_header(ws, headers: List[str],
                        fill_color: str = DEFAULT_HEADER_COLOR) -> None:
    """创建标准Excel表头

    Args:
        ws: openpyxl工作表对象
        headers: 表头列表
        fill_color: 表头背景颜色
    """
    style = create_header_style(fill_color)

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        apply_style_to_cell(cell, style)


def auto_adjust_column_width(ws, width: int = DEFAULT_COLUMN_WIDTH) -> None:
    """自动调整列宽

    Args:
        ws: openpyxl工作表对象
        width: 默认列宽
    """
    for col_idx in range(1, ws.max_column + 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = width


def write_data_rows(ws, data: List[List[Any]], start_row: int = 2) -> None:
    """写入数据行

    Args:
        ws: openpyxl工作表对象
        data: 数据列表 (每行是一个列表)
        start_row: 起始行号
    """
    for row_idx, row_data in enumerate(data, start_row):
        for col_idx, value in enumerate(row_data, 1):
            ws.cell(row=row_idx, column=col_idx, value=value)


def create_standard_excel(headers: List[str],
                           data: List[List[Any]],
                           title: str = "Sheet1",
                           fill_color: str = DEFAULT_HEADER_COLOR) -> Workbook:
    """创建标准Excel工作簿

    Args:
        headers: 表头列表
        data: 数据列表
        title: 工作表名称
        fill_color: 表头背景颜色

    Returns:
        Workbook对象
    """
    wb = Workbook()
    ws = wb.active
    ws.title = title

    # 创建表头
    create_excel_header(ws, headers, fill_color)

    # 写入数据
    write_data_rows(ws, data)

    # 自动调整列宽
    auto_adjust_column_width(ws)

    return wb


# =============================================================================
# 数据转换函数
# =============================================================================

def dict_to_row(data: Dict, keys: List[str]) -> List[Any]:
    """将字典转换为行数据

    Args:
        data: 字典数据
        keys: 键列表 (决定列顺序)

    Returns:
        行数据列表
    """
    return [data.get(key, '') for key in keys]


def dict_list_to_rows(data_list: List[Dict], keys: List[str]) -> List[List[Any]]:
    """将字典列表转换为行数据列表

    Args:
        data_list: 字典列表
        keys: 键列表

    Returns:
        行数据列表
    """
    return [dict_to_row(data, keys) for data in data_list]


# =============================================================================
# 文件操作函数
# =============================================================================

def save_workbook(wb: Workbook, output_path: str) -> str:
    """保存工作簿

    Args:
        wb: Workbook对象
        output_path: 输出文件路径

    Returns:
        保存的文件路径
    """
    wb.save(output_path)
    return output_path


def create_export_excel(output_path: str,
                       headers: List[str],
                       data: List[List[Any]],
                       sheet_name: str = "导出数据",
                       fill_color: str = DEFAULT_HEADER_COLOR) -> str:
    """创建导出Excel文件

    Args:
        output_path: 输出文件路径
        headers: 表头列表
        data: 数据列表
        sheet_name: 工作表名称
        fill_color: 表头背景颜色

    Returns:
        保存的文件路径
    """
    wb = create_standard_excel(headers, data, sheet_name, fill_color)
    return save_workbook(wb, output_path)


# =============================================================================
# 模板生成函数
# =============================================================================

def create_template(output_path: str,
                   headers: List[str],
                   example_data: Optional[List[List[Any]]] = None,
                   fill_color: str = GREEN_HEADER_COLOR) -> str:
    """创建导入模板

    Args:
        output_path: 模板文件路径
        headers: 表头列表
        example_data: 示例数据 (可选)
        fill_color: 表头背景颜色

    Returns:
        模板文件路径
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "模板"

    # 创建表头
    create_excel_header(ws, headers, fill_color)

    # 写入示例数据
    if example_data:
        write_data_rows(ws, example_data)

    # 自动调整列宽
    auto_adjust_column_width(ws)

    # 保存
    wb.save(output_path)
    return output_path
