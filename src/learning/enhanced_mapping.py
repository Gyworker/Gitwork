# -*- coding: utf-8 -*-
"""
增强映射学习模块
支持从Excel文件和历史数据学习映射关系
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import pandas as pd
from difflib import SequenceMatcher

# 导入项目模块
from src.database.contacts import ContactsDB


@dataclass
class MappingRule:
    """映射规则"""
    id: int = 0
    keyword: str = ""
    responsible: str = ""
    confidence: float = 1.0
    source: str = "manual"  # 'manual', 'excel', 'history'
    usage_count: int = 0
    last_used: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'MappingRule':
        return cls(**data)


class MappingLearner:
    """映射学习器"""

    def __init__(self, db: ContactsDB):
        self.db = db
        self.rules: Dict[str, MappingRule] = {}
        self._load_rules()

    def _load_rules(self):
        """从数据库加载映射规则"""
        try:
            rules_data = self.db.execute_query(
                "SELECT * FROM mapping_rules ORDER BY usage_count DESC"
            )
            for row in rules_data:
                rule = MappingRule(
                    id=row['id'],
                    keyword=row['keyword'],
                    responsible=row['responsible'],
                    confidence=row.get('confidence', 1.0),
                    source=row.get('source', 'manual'),
                    usage_count=row.get('usage_count', 0),
                    last_used=row.get('last_used'),
                    created_at=row.get('created_at', ''),
                    updated_at=row.get('updated_at', '')
                )
                self.rules[rule.keyword.lower()] = rule
        except Exception:
            # 表可能不存在，忽略
            pass

    def _ensure_table_exists(self):
        """确保映射规则表存在"""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS mapping_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword VARCHAR(200) NOT NULL,
                    responsible VARCHAR(100) NOT NULL,
                    confidence FLOAT DEFAULT 1.0,
                    source VARCHAR(50) DEFAULT 'manual',
                    usage_count INTEGER DEFAULT 0,
                    last_used VARCHAR(50),
                    created_at VARCHAR(50),
                    updated_at VARCHAR(50)
                )
            """)
        except Exception:
            pass

    def learn_from_excel(self, file_path: str,
                        keyword_col: str = '关键词',
                        responsible_col: str = '责任人') -> int:
        """从Excel文件学习映射

        Args:
            file_path: Excel文件路径
            keyword_col: 关键词列名
            responsible_col: 责任人列名

        Returns:
            学习到的规则数量
        """
        self._ensure_table_exists()

        # 读取Excel
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path, engine='openpyxl')
        else:
            df = pd.read_excel(file_path, engine='xlrd')

        # 查找列
        headers = df.columns.tolist()
        keyword_idx = self._find_column(headers, keyword_col, ['关键词', 'keyword', '模块', 'task'])
        responsible_idx = self._find_column(headers, responsible_col, ['责任人', 'responsible', '负责人', 'owner'])

        if keyword_idx is None or responsible_idx is None:
            raise ValueError("无法识别关键词或责任人列")

        # 学习规则
        count = 0
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for _, row in df.iterrows():
            keyword = str(row.iloc[keyword_idx]).strip()
            responsible = str(row.iloc[responsible_idx]).strip()

            if keyword and keyword != 'nan' and responsible and responsible != 'nan':
                self._add_rule(
                    keyword=keyword,
                    responsible=responsible,
                    source='excel'
                )
                count += 1

        return count

    def learn_from_text(self, text: str, responsible: str) -> MappingRule:
        """从文本学习映射

        Args:
            text: 包含关键词的文本
            responsible: 责任人

        Returns:
            创建的映射规则
        """
        self._ensure_table_exists()

        # 提取关键词
        keywords = self._extract_keywords(text)
        if keywords:
            keyword = keywords[0]
        else:
            keyword = text[:50]  # 使用前50个字符

        return self._add_rule(keyword, responsible, source='manual')

    def learn_from_history(self, tasks: List[Dict]) -> int:
        """从历史任务数据学习映射

        Args:
            tasks: 历史任务列表，每个任务包含 module, responsible 等字段

        Returns:
            学习到的规则数量
        """
        self._ensure_table_exists()

        # 统计模块-责任人的出现频率
        module_responsible_count = defaultdict(lambda: defaultdict(int))

        for task in tasks:
            module = task.get('module', '')
            responsible = task.get('responsible', '')
            if module and responsible:
                module_responsible_count[module][responsible] += 1

        # 学习频率最高的映射
        count = 0
        for module, responsible_dict in module_responsible_count.items():
            if responsible_dict:
                # 选择出现频率最高的
                best_responsible = max(responsible_dict.items(), key=lambda x: x[1])
                self._add_rule(
                    keyword=module,
                    responsible=best_responsible[0],
                    confidence=min(best_responsible[1] / 10, 1.0),  # 根据频率调整置信度
                    source='history'
                )
                count += 1

        return count

    def _find_column(self, headers: List[str], target: str, alternatives: List[str]) -> Optional[int]:
        """查找匹配的列索引"""
        target_lower = target.lower()
        for idx, header in enumerate(headers):
            header_lower = header.strip().lower()
            if header_lower == target_lower or header_lower in alternatives:
                return idx
        return None

    def _extract_keywords(self, text: str) -> List[str]:
        """从文本提取关键词"""
        # 移除常见停用词
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        words = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', text)
        keywords = [w for w in words if len(w) >= 2 and w not in stop_words]
        return keywords

    def _add_rule(self, keyword: str, responsible: str,
                  confidence: float = 1.0, source: str = 'manual') -> MappingRule:
        """添加映射规则"""
        keyword_lower = keyword.lower()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if keyword_lower in self.rules:
            # 更新现有规则
            rule = self.rules[keyword_lower]
            rule.responsible = responsible
            rule.confidence = max(rule.confidence, confidence)
            rule.source = source
            rule.updated_at = now
        else:
            # 创建新规则
            rule = MappingRule(
                keyword=keyword,
                responsible=responsible,
                confidence=confidence,
                source=source,
                created_at=now,
                updated_at=now
            )
            self.rules[keyword_lower] = rule

        # 保存到数据库
        self._save_rule(rule)

        return rule

    def _save_rule(self, rule: MappingRule):
        """保存规则到数据库"""
        try:
            self.db.execute_query(
                """INSERT OR REPLACE INTO mapping_rules 
                   (keyword, responsible, confidence, source, usage_count, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (rule.keyword, rule.responsible, rule.confidence, rule.source,
                 rule.usage_count, rule.created_at, rule.updated_at)
            )
        except Exception:
            pass

    def recommend(self, task_text: str) -> Tuple[Optional[str], float]:
        """推荐责任人

        Args:
            task_text: 任务描述文本

        Returns:
            (推荐的责任人, 置信度)
        """
        # 提取关键词
        keywords = self._extract_keywords(task_text)
        if not keywords:
            return None, 0.0

        # 匹配规则
        best_match = None
        best_score = 0.0

        for keyword in keywords:
            keyword_lower = keyword.lower()

            # 精确匹配
            if keyword_lower in self.rules:
                rule = self.rules[keyword_lower]
                score = rule.confidence * 1.0  # 精确匹配权重
                if score > best_score:
                    best_score = score
                    best_match = rule.responsible

            # 模糊匹配
            for rule_key, rule in self.rules.items():
                similarity = SequenceMatcher(None, keyword_lower, rule_key).ratio()
                if similarity > 0.8:  # 相似度阈值
                    score = rule.confidence * similarity * 0.8  # 模糊匹配权重
                    if score > best_score:
                        best_score = score
                        best_match = rule.responsible

        # 更新使用统计
        if best_match:
            self._update_usage(best_match)

        return best_match, best_score

    def _update_usage(self, responsible: str):
        """更新使用统计"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for rule in self.rules.values():
            if rule.responsible == responsible:
                rule.usage_count += 1
                rule.last_used = now
                self._save_rule(rule)

    def get_all_rules(self) -> List[MappingRule]:
        """获取所有映射规则"""
        return sorted(self.rules.values(), key=lambda x: x.usage_count, reverse=True)

    def export_to_excel(self, output_path: str) -> str:
        """导出映射规则到Excel

        Args:
            output_path: 输出文件路径

        Returns:
            保存的文件路径
        """
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils import get_column_letter

        wb = Workbook()
        ws = wb.active
        ws.title = "映射规则"

        # 表头样式
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")

        # 写入表头
        headers = ['关键词', '责任人', '置信度', '来源', '使用次数', '最后使用', '创建时间']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # 写入数据
        rules = self.get_all_rules()
        for row_idx, rule in enumerate(rules, 2):
            values = [
                rule.keyword, rule.responsible, f"{rule.confidence:.1%}",
                rule.source, rule.usage_count, rule.last_used or '-', rule.created_at
            ]
            for col_idx, value in enumerate(values, 1):
                ws.cell(row=row_idx, column=col_idx, value=value)

        # 自动调整列宽
        for col_idx in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col_idx)].width = 15

        wb.save(output_path)
        return output_path

    def delete_rule(self, keyword: str) -> bool:
        """删除映射规则

        Args:
            keyword: 要删除的关键词

        Returns:
            是否删除成功
        """
        keyword_lower = keyword.lower()
        if keyword_lower in self.rules:
            del self.rules[keyword_lower]
            try:
                self.db.execute_query(
                    "DELETE FROM mapping_rules WHERE LOWER(keyword) = ?",
                    (keyword_lower,)
                )
                return True
            except Exception:
                return False
        return False
