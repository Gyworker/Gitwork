# -*- coding: utf-8 -*-
"""
Excel导入导出模块
Excel Import/Export Module:

提供Excel数据的批量导入和任务导出功能
"""

import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Callable, Any
from pathlib import Path

from ..database.connection import get_db_connection
from ..utils.logger import get_logger
from ..utils.exception_handler import (
    safe_execute,
    handle_file_error,
    FileOperationException,
    ValidationException,
    DatabaseException
)
import sqlite3

logger = get_logger(__name__)


class ExcelExporter:
    """Excel导出器"""

    def __init__(self):
        """初始化导出器"""
        self.db = get_db_connection()

    def export_tasks(self, 
                     status_filter: Optional[str] = None,
                     output_path: Optional[str] = None,
                     progress_callback: Optional[Callable] = None) -> Optional[str]:
        """
        导出任务到Excel

        Args:
            status_filter: 状态筛选（进行中/已答复/全部）
            output_path: 输出文件路径
            progress_callback: 进度回调函数

        Returns:
            导出文件路径，失败返回None
        """
        try:
            if progress_callback:
                progress_callback(10, 100, "正在查询任务数据...")

            # 构建查询
            if status_filter == "进行中":
                sql = """
                    SELECT task_id, task_name, urgency, status,
                           inquirer, inquirer_dept, inquirer_company,
                           inquirer_phone, inquirer_email,
                           respondent, respondent_dept,
                           industry, key_module, task_content,
                           expected_reply_time, reply_status,
                           created_at, updated_at, remark
                    FROM tasks
                    WHERE status IN ('进行中', '挂起')
                    ORDER BY 
                        CASE urgency WHEN '高' THEN 1 WHEN '中' THEN 2 WHEN '低' THEN 3 END,
                        created_at DESC
                """
            elif status_filter == "已答复":
                sql = """
                    SELECT task_id, task_name, urgency, status,
                           inquirer, inquirer_dept, inquirer_company,
                           inquirer_phone, inquirer_email,
                           respondent, respondent_dept,
                           industry, key_module, task_content,
                           expected_reply_time, reply_status,
                           created_at, updated_at, remark
                    FROM tasks
                    WHERE status IN ('已答复', '完成')
                    ORDER BY created_at DESC
                """
            else:
                sql = """
                    SELECT task_id, task_name, urgency, status,
                           inquirer, inquirer_dept, inquirer_company,
                           inquirer_phone, inquirer_email,
                           respondent, respondent_dept,
                           industry, key_module, task_content,
                           expected_reply_time, reply_status,
                           created_at, updated_at, remark
                    FROM tasks
                    ORDER BY 
                        CASE urgency WHEN '高' THEN 1 WHEN '中' THEN 2 WHEN '低' THEN 3 END,
                        created_at DESC
                """

            if progress_callback:
                progress_callback(30, 100, "正在获取任务列表...")

            rows = self.db.fetchall(sql)

            if progress_callback:
                progress_callback(50, 100, f"共 {len(rows)} 条任务，正在生成Excel...")

            # 转换为DataFrame
            columns = [
                "任务ID", "任务名称", "重要程度", "状态",
                "咨询者", "咨询者部门", "咨询者公司",
                "咨询者电话", "咨询者邮箱",
                "答复人", "答复人部门",
                "所属行业", "关键模块", "任务内容",
                "预期答复时间", "答复状态",
                "创建时间", "更新时间", "备注"
            ]

            data = []
            for row in rows:
                data.append({
                    "任务ID": row[0],
                    "任务名称": row[1],
                    "重要程度": row[2],
                    "状态": row[3],
                    "咨询者": row[4],
                    "咨询者部门": row[5],
                    "咨询者公司": row[6],
                    "咨询者电话": row[7],
                    "咨询者邮箱": row[8],
                    "答复人": row[9],
                    "答复人部门": row[10],
                    "所属行业": row[11],
                    "关键模块": row[12],
                    "任务内容": row[13],
                    "预期答复时间": row[14].strftime("%Y-%m-%d %H:%M") if row[14] else "",
                    "答复状态": row[15],
                    "创建时间": row[16].strftime("%Y-%m-%d %H:%M") if row[16] else "",
                    "更新时间": row[17].strftime("%Y-%m-%d %H:%M") if row[17] else "",
                    "备注": row[18]
                })

            df = pd.DataFrame(data, columns=columns)

            if progress_callback:
                progress_callback(80, 100, "正在保存文件...")

            # 生成文件名
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filter_name = status_filter if status_filter else "全部"
                output_path = f"任务导出_{filter_name}_{timestamp}.xlsx"

            # 保存Excel
            df.to_excel(output_path, index=False, engine='openpyxl')

            if progress_callback:
                progress_callback(100, 100, f"导出完成！共 {len(rows)} 条任务")

            logger.info(f"任务导出成功: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"导出任务失败: {e}")
            return None

    def export_contacts(self, 
                        output_path: Optional[str] = None,
                        progress_callback: Optional[Callable] = None) -> Optional[str]:
        """导出通讯录到Excel"""
        try:
            if progress_callback:
                progress_callback(20, 100, "正在查询通讯录...")

            rows = self.db.fetchall(
                """
                SELECT name, employee_id, phone, email, department, position,
                       created_at, updated_at
                FROM contacts
                ORDER BY name
                """
            )

            if progress_callback:
                progress_callback(60, 100, f"共 {len(rows)} 条通讯录，正在生成Excel...")

            columns = ["姓名", "工号", "手机号", "邮箱", "部门", "职位", "创建时间", "更新时间"]
            data = []
            for row in rows:
                data.append({
                    "姓名": row[0], "工号": row[1], "手机号": row[2], "邮箱": row[3],
                    "部门": row[4], "职位": row[5],
                    "创建时间": row[6].strftime("%Y-%m-%d %H:%M") if row[6] else "",
                    "更新时间": row[7].strftime("%Y-%m-%d %H:%M") if row[7] else ""
                })

            df = pd.DataFrame(data, columns=columns)

            if progress_callback:
                progress_callback(80, 100, "正在保存文件...")

            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"通讯录导出_{timestamp}.xlsx"

            df.to_excel(output_path, index=False, engine='openpyxl')

            if progress_callback:
                progress_callback(100, 100, f"导出完成！共 {len(rows)} 条通讯录")

            logger.info(f"通讯录导出成功: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"导出通讯录失败: {e}")
            return None

    def export_recommendations(self, 
                               output_path: Optional[str] = None,
                               progress_callback: Optional[Callable] = None) -> Optional[str]:
        """导出推荐库到Excel"""
        try:
            if progress_callback:
                progress_callback(20, 100, "正在查询推荐库...")

            try:
                rows = self.db.fetchall(
                    """SELECT name, employee_id, phone, email, department,
                              position, key_module, expertise
                       FROM recommendation_library ORDER BY name"""
                )
            except (DatabaseException, sqlite3.OperationalError):
                logger.warning("推荐库表不存在，尝试备用表")
                rows = self.db.fetchall(
                    """SELECT name, employee_id, phone, email, department,
                              position, key_module, expertise
                       FROM recommendations ORDER BY name"""
                )

            if progress_callback:
                progress_callback(60, 100, f"共 {len(rows)} 条记录，正在生成Excel...")

            columns = ["姓名", "工号", "手机号", "邮箱", "部门", "职位", "关键模块", "专业领域"]
            data = []
            for row in rows:
                data.append({
                    "姓名": row[0], "工号": row[1], "手机号": row[2], "邮箱": row[3],
                    "部门": row[4], "职位": row[5], "关键模块": row[6],
                    "专业领域": row[7] if len(row) > 7 else ""
                })

            df = pd.DataFrame(data, columns=columns)

            if progress_callback:
                progress_callback(80, 100, "正在保存文件...")

            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"推荐库导出_{timestamp}.xlsx"

            df.to_excel(output_path, index=False, engine='openpyxl')

            if progress_callback:
                progress_callback(100, 100, f"导出完成！共 {len(rows)} 条记录")

            logger.info(f"推荐库导出成功: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"导出推荐库失败: {e}")
            return None


class BatchImporter:
    """批量导入器"""

    def __init__(self):
        """初始化导入器"""
        self.db = get_db_connection()

    def import_tasks_from_excel(self, file_path: str,
                                progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """从Excel批量导入任务"""
        try:
            if progress_callback:
                progress_callback(10, 100, "正在读取Excel文件...")

            df = pd.read_excel(file_path, engine='openpyxl')

            if progress_callback:
                progress_callback(30, 100, f"共 {len(df)} 条记录，正在导入...")

            success_count = 0
            error_count = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    task_data = {
                        "task_name": str(row.get("任务名称", "")),
                        "urgency": str(row.get("重要程度", "中")),
                        "status": str(row.get("状态", "进行中")),
                        "inquirer": str(row.get("咨询者", "")),
                        "inquirer_dept": str(row.get("咨询者部门", "")),
                        "inquirer_company": str(row.get("咨询者公司", "")),
                        "inquirer_phone": str(row.get("咨询者电话", "")),
                        "inquirer_email": str(row.get("咨询者邮箱", "")),
                        "respondent": str(row.get("答复人", "")),
                        "respondent_dept": str(row.get("答复人部门", "")),
                        "industry": str(row.get("所属行业", "")),
                        "key_module": str(row.get("关键模块", "")),
                        "task_content": str(row.get("任务内容", "")),
                        "remark": str(row.get("备注", ""))
                    }

                    if not task_data["task_name"]:
                        raise ValueError("任务名称不能为空")

                    from ..utils.helpers import generate_id
                    task_id = generate_id()

                    self.db.execute(
                        """INSERT INTO tasks 
                           (task_id, task_name, urgency, status, inquirer, inquirer_dept,
                            inquirer_company, inquirer_phone, inquirer_email,
                            respondent, respondent_dept, industry, key_module, task_content, remark)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (task_id, task_data["task_name"], task_data["urgency"], task_data["status"],
                         task_data["inquirer"], task_data["inquirer_dept"], task_data["inquirer_company"],
                         task_data["inquirer_phone"], task_data["inquirer_email"], task_data["respondent"],
                         task_data["respondent_dept"], task_data["industry"], task_data["key_module"],
                         task_data["task_content"], task_data["remark"]),
                        commit=True
                    )
                    success_count += 1

                    if progress_callback:
                        progress = 30 + int((index + 1) / len(df) * 60)
                        progress_callback(progress, 100, f"正在导入... {index + 1}/{len(df)}")

                except Exception as e:
                    error_count += 1
                    errors.append({"row": index + 2, "error": str(e)})

            if progress_callback:
                progress_callback(100, 100, f"导入完成！成功 {success_count} 条，失败 {error_count} 条")

            result = {"success": success_count, "error": error_count, "errors": errors, "total": len(df)}
            logger.info(f"批量导入任务完成: 成功 {success_count}, 失败 {error_count}")
            return result

        except Exception as e:
            logger.error(f"批量导入任务失败: {e}")
            return {"success": 0, "error": 1, "errors": [{"row": 0, "error": str(e)}], "total": 0}

    def import_contacts_from_excel(self, file_path: str,
                                   progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """从Excel批量导入通讯录"""
        try:
            if progress_callback:
                progress_callback(10, 100, "正在读取Excel文件...")

            df = pd.read_excel(file_path, engine='openpyxl')

            if progress_callback:
                progress_callback(30, 100, f"共 {len(df)} 条记录，正在导入...")

            success_count = 0
            error_count = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    contact_data = {
                        "name": str(row.get("姓名", "")),
                        "employee_id": str(row.get("工号", "")),
                        "phone": str(row.get("手机号", "")),
                        "email": str(row.get("邮箱", "")),
                        "department": str(row.get("部门", "")),
                        "position": str(row.get("职位", ""))
                    }

                    if not contact_data["name"]:
                        raise ValueError("姓名不能为空")

                    from ..utils.helpers import generate_id
                    contact_id = generate_id()

                    self.db.execute(
                        """INSERT INTO contacts 
                           (id, name, employee_id, phone, email, department, position)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (contact_id, contact_data["name"], contact_data["employee_id"],
                         contact_data["phone"], contact_data["email"],
                         contact_data["department"], contact_data["position"]),
                        commit=True
                    )
                    success_count += 1

                    if progress_callback:
                        progress = 30 + int((index + 1) / len(df) * 60)
                        progress_callback(progress, 100, f"正在导入... {index + 1}/{len(df)}")

                except Exception as e:
                    error_count += 1
                    errors.append({"row": index + 2, "error": str(e)})

            if progress_callback:
                progress_callback(100, 100, f"导入完成！成功 {success_count} 条，失败 {error_count} 条")

            result = {"success": success_count, "error": error_count, "errors": errors, "total": len(df)}
            logger.info(f"批量导入通讯录完成: 成功 {success_count}, 失败 {error_count}")
            return result

        except Exception as e:
            logger.error(f"批量导入通讯录失败: {e}")
            return {"success": 0, "error": 1, "errors": [{"row": 0, "error": str(e)}], "total": 0}


# 全局实例
_excel_exporter: Optional[ExcelExporter] = None
_batch_importer: Optional[BatchImporter] = None


def get_excel_exporter() -> ExcelExporter:
    """获取Excel导出器实例"""
    global _excel_exporter
    if _excel_exporter is None:
        _excel_exporter = ExcelExporter()
    return _excel_exporter


def get_batch_importer() -> BatchImporter:
    """获取批量导入器实例"""
    global _batch_importer
    if _batch_importer is None:
        _batch_importer = BatchImporter()
    return _batch_importer
