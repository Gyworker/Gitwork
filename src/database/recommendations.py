"""
推荐库管理模块
管理答复人推荐信息，支持智能匹配
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class RecommendationModel:
    """推荐库数据模型"""
    
    TABLE_NAME = "recommendations"
    
    def __init__(self, db_connection):
        self.db = db_connection
        
    def create_table(self) -> bool:
        """创建推荐库表"""
        sql = """
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL,
            employee_id VARCHAR(20),
            phone VARCHAR(20),
            email VARCHAR(100),
            department VARCHAR(50),
            position VARCHAR(50),
            key_module VARCHAR(200),
            expertise VARCHAR(200),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        try:
            self.db.execute(sql)
            self.db.commit()
            return True
        except Exception:
            return False
            
    def add_recommendation(self, data: Dict[str, Any]) -> Optional[int]:
        """添加推荐记录"""
        sql = """
        INSERT INTO recommendations 
        (name, employee_id, phone, email, department, position, key_module, expertise)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            cursor = self.db.execute(sql, (
                data.get('name'),
                data.get('employee_id'),
                data.get('phone'),
                data.get('email'),
                data.get('department'),
                data.get('position'),
                data.get('key_module'),
                data.get('expertise')
            ))
            self.db.commit()
            return cursor.lastrowid
        except Exception:
            return None
            
    def get_recommendation(self, rec_id: int) -> Optional[Dict[str, Any]]:
        """获取推荐记录"""
        sql = "SELECT * FROM recommendations WHERE id = ?"
        try:
            result = self.db.execute_query(sql, (rec_id,))
            if result:
                return result[0]
            return None
        except Exception:
            return None
            
    def get_all_recommendations(self) -> List[Dict[str, Any]]:
        """获取所有推荐记录"""
        sql = "SELECT * FROM recommendations ORDER BY updated_at DESC"
        try:
            return self.db.execute_query(sql)
        except Exception:
            return []
            
    def search_by_key_module(self, keyword: str) -> List[Dict[str, Any]]:
        """根据关键模块搜索"""
        sql = """
        SELECT * FROM recommendations 
        WHERE key_module LIKE ? 
        ORDER BY updated_at DESC
        """
        try:
            return self.db.execute_query(sql, (f"%{keyword}%",))
        except Exception:
            return []
            
    def update_recommendation(self, rec_id: int, data: Dict[str, Any]) -> bool:
        """更新推荐记录"""
        sql = """
        UPDATE recommendations SET
            name = ?,
            employee_id = ?,
            phone = ?,
            email = ?,
            department = ?,
            position = ?,
            key_module = ?,
            expertise = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
        try:
            self.db.execute(sql, (
                data.get('name'),
                data.get('employee_id'),
                data.get('phone'),
                data.get('email'),
                data.get('department'),
                data.get('position'),
                data.get('key_module'),
                data.get('expertise'),
                rec_id
            ))
            self.db.commit()
            return True
        except Exception:
            return False
            
    def delete_recommendation(self, rec_id: int) -> bool:
        """删除推荐记录"""
        sql = "DELETE FROM recommendations WHERE id = ?"
        try:
            self.db.execute(sql, (rec_id,))
            self.db.commit()
            return True
        except Exception:
            return False
            
    def import_batch(self, records: List[Dict[str, Any]]) -> int:
        """批量导入推荐记录"""
        count = 0
        for record in records:
            if self.add_recommendation(record):
                count += 1
        return count
        
    def export_all(self) -> List[Dict[str, Any]]:
        """导出所有推荐记录"""
        return self.get_all_recommendations()


class RecommendationService:
    """推荐服务"""
    
    def __init__(self, db_connection):
        self.model = RecommendationModel(db_connection)
        
    def recommend_responder(self, key_module: str) -> Optional[Dict[str, Any]]:
        """
        根据关键模块推荐答复人
        匹配规则：key_module包含搜索关键字
        """
        if not key_module:
            return None
            
        # 分割多个关键字
        keywords = [k.strip() for k in key_module.replace('/', ',').split(',')]
        
        for keyword in keywords:
            if keyword:
                results = self.model.search_by_key_module(keyword)
                if results:
                    # 返回第一条匹配记录
                    # 联系方式优先级：手机号 > 邮箱
                    record = results[0]
                    contact = record.get('phone') or record.get('email', '')
                    record['preferred_contact'] = contact
                    return record
                    
        return None
        
    def get_recommendation_source(self, key_module: str) -> str:
        """获取推荐来源说明"""
        keywords = [k.strip() for k in key_module.replace('/', ',').split(',')]
        
        for keyword in keywords:
            if keyword:
                results = self.model.search_by_key_module(keyword)
                if results:
                    return f"推荐库（智能匹配关键模块：{keyword}）"
                    
        return "无匹配推荐"
