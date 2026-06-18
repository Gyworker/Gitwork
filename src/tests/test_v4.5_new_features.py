# -*- coding: utf-8 -*-
"""
V4.5 新功能测试用例

测试内容：
1. 通讯录重名处理 - 姓名+工号唯一标识
2. 推荐库多关键模块合并 - 同姓名多条记录自动合并
3. 信息同步刷新功能

版本：V4.5
"""

import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# 测试通讯录重名处理
# =============================================================================

class TestContactsDuplicateNames:
    """通讯录同名处理测试"""

    def test_make_unique_key_with_employee_id(self):
        """测试：生成唯一键（同名有工号）"""
        from src.database.contacts_manager import ContactsManager

        key = ContactsManager.make_unique_key("赵六", "EMP001")
        assert key == "赵六|EMP001"

    def test_make_unique_key_without_employee_id(self):
        """测试：生成唯一键（同名无工号）"""
        from src.database.contacts_manager import ContactsManager

        key = ContactsManager.make_unique_key("赵六", "")
        assert key == "赵六|"

    def test_parse_unique_key(self):
        """测试：解析唯一键"""
        from src.database.contacts_manager import ContactsManager

        name, emp_id = ContactsManager.parse_unique_key("赵六|EMP001")
        assert name == "赵六"
        assert emp_id == "EMP001"

    def test_same_name_different_employee_id(self):
        """测试：同名不同工号应生成不同唯一键"""
        from src.database.contacts_manager import ContactsManager

        key1 = ContactsManager.make_unique_key("赵六", "EMP001")
        key2 = ContactsManager.make_unique_key("赵六", "EMP002")

        assert key1 != key2  # 不同工号应该生成不同的键

    def test_different_name_same_employee_id(self):
        """测试：不同名相同工号应生成不同唯一键"""
        from src.database.contacts_manager import ContactsManager

        key1 = ContactsManager.make_unique_key("赵六", "EMP001")
        key2 = ContactsManager.make_unique_key("王五", "EMP001")

        assert key1 != key2  # 不同姓名应该生成不同的键


# =============================================================================
# 测试推荐库多关键模块合并
# =============================================================================

class TestRecommendationMerge:
    """推荐库合并测试"""

    def test_merge_recommendations_same_name(self):
        """测试：同姓名多条记录合并关键模块

        场景：
            赵六，MAC认证
            赵六，802.1x认证

        期望：
            赵六，MAC认证、802.1x认证
        """
        from src.database.recommendations import RecommendationService

        service = RecommendationService(None)

        records = [
            {'name': '赵六', 'employee_id': 'EMP001', 'key_module': 'MAC认证'},
            {'name': '赵六', 'employee_id': 'EMP001', 'key_module': '802.1x认证'},
        ]

        merged = service.merge_recommendations(records)

        assert len(merged) == 1
        assert merged[0]['name'] == '赵六'
        # 验证关键模块已合并
        assert 'MAC认证' in merged[0]['key_module']
        assert '802.1x认证' in merged[0]['key_module']
        assert merged[0]['is_merged'] is True
        assert merged[0]['merged_from'] == 2

    def test_no_merge_different_employee_id(self):
        """测试：同姓名不同工号不合并

        场景：
            赵六，EMP001，MAC认证
            赵六，EMP002，802.1x认证

        期望：
            两条独立记录，不合并（视为不同人）
        """
        from src.database.recommendations import RecommendationService

        service = RecommendationService(None)

        records = [
            {'name': '赵六', 'employee_id': 'EMP001', 'key_module': 'MAC认证'},
            {'name': '赵六', 'employee_id': 'EMP002', 'key_module': '802.1x认证'},
        ]

        merged = service.merge_recommendations(records)

        assert len(merged) == 2  # 不合并，保留两条记录

    def test_recommend_responder_mac_auth(self):
        """测试：搜索MAC认证应推荐赵六

        导入：
            赵六，MAC认证
            赵六，802.1x认证

        搜索：MAC认证

        期望：
            返回赵六，关键模块包含：MAC认证、802.1x认证
        """
        from src.database.recommendations import RecommendationService

        # 模拟数据库查询
        class MockDB:
            def execute_query(self, sql, params=None):
                # 返回包含"赵六"的记录
                return [
                    {'name': '赵六', 'employee_id': 'EMP001', 'key_module': 'MAC认证', 'phone': '13800138001'},
                    {'name': '赵六', 'employee_id': 'EMP001', 'key_module': '802.1x认证', 'phone': '13800138001'},
                ]

        service = RecommendationService(MockDB())
        result = service.recommend_responder("MAC认证")

        assert result is not None
        assert result['name'] == '赵六'
        assert 'MAC认证' in result['key_module']
        assert '802.1x认证' in result['key_module']

    def test_recommend_responder_8021x_auth(self):
        """测试：搜索802.1x认证应推荐赵六

        导入：
            赵六，MAC认证
            赵六，802.1x认证

        搜索：802.1x认证

        期望：
            返回赵六，关键模块包含：MAC认证、802.1x认证
        """
        from src.database.recommendations import RecommendationService

        class MockDB:
            def execute_query(self, sql, params=None):
                return [
                    {'name': '赵六', 'employee_id': 'EMP001', 'key_module': 'MAC认证', 'phone': '13800138001'},
                    {'name': '赵六', 'employee_id': 'EMP001', 'key_module': '802.1x认证', 'phone': '13800138001'},
                ]

        service = RecommendationService(MockDB())
        result = service.recommend_responder("802.1x认证")

        assert result is not None
        assert result['name'] == '赵六'
        assert 'MAC认证' in result['key_module']
        assert '802.1x认证' in result['key_module']


# =============================================================================
# 测试推荐库导入合并
# =============================================================================

class TestRecommendationImport:
    """推荐库导入合并测试"""

    def test_import_with_merge_mode(self):
        """测试：导入时合并关键模块

        现有：
            赵六，MAC认证

        导入：
            赵六，802.1x认证

        期望：
            赵六，MAC认证、802.1x认证
        """
        from src.database.recommendations import RecommendationService

        class MockModel:
            def __init__(self):
                self.records = [
                    {'id': 1, 'name': '赵六', 'employee_id': 'EMP001', 'key_module': 'MAC认证'}
                ]

            def get_all_recommendations(self):
                return self.records

            def add_recommendation(self, data):
                new_id = len(self.records) + 1
                data['id'] = new_id
                self.records.append(data)
                return new_id

            def update_recommendation(self, rec_id, data):
                for rec in self.records:
                    if rec['id'] == rec_id:
                        rec.update(data)
                        return True
                return False

        class MockDB:
            def __init__(self):
                self.model = MockModel()

        service = RecommendationService(MockDB())

        # 导入新记录
        new_records = [
            {'name': '赵六', 'employee_id': 'EMP001', 'key_module': '802.1x认证'}
        ]

        stats = service.import_with_merge(new_records, mode='merge')

        # 验证结果
        assert stats['updated'] == 1
        assert stats['added'] == 0

        # 验证合并后的关键模块
        merged_record = None
        for rec in service.model.get_all_recommendations():
            if rec['name'] == '赵六':
                merged_record = rec
                break

        assert merged_record is not None
        assert 'MAC认证' in merged_record['key_module']
        assert '802.1x认证' in merged_record['key_module']


# =============================================================================
# 测试通讯录信息同步
# =============================================================================

class TestContactsSync:
    """通讯录同步测试"""

    def test_refresh_existing_contact(self):
        """测试：刷新已存在的联系人

        场景：
            本地：赵六，EMP001，部门A，手机13800000001
            导入：赵六，EMP001，部门B，手机13800000002

        期望：
            本地更新为：赵六，EMP001，部门B，手机13800000002
        """
        from src.database.contacts_manager import ContactsManager

        class MockDB:
            def __init__(self):
                self.records = [
                    {
                        'id': 1,
                        'name': '赵六',
                        'employee_id': 'EMP001',
                        'department': '部门A',
                        'phone': '13800000001',
                        'email': '',
                        'position': '',
                        'created_at': None,
                        'updated_at': None
                    }
                ]
                self.query_results = []

            def execute_query(self, sql, params=None):
                # 查找
                if 'SELECT' in sql and 'WHERE' in sql:
                    name = params[0]
                    for rec in self.records:
                        if rec['name'] == name:
                            return [rec]
                    return []
                return []

            def execute(self, sql, params=None):
                if 'INSERT' in sql:
                    from datetime import datetime
                    new_id = len(self.records) + 1
                    self.records.append({
                        'id': new_id,
                        'name': params[0],
                        'employee_id': params[1],
                        'phone': params[2],
                        'email': params[3],
                        'department': params[4],
                        'position': params[5],
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    })

                    class Cursor:
                        lastrowid = new_id
                    return Cursor()
                elif 'UPDATE' in sql:
                    for rec in self.records:
                        if rec['id'] == params[-1]:
                            rec['name'] = params[0]
                            rec['employee_id'] = params[1]
                            rec['phone'] = params[2]
                            rec['email'] = params[3]
                            rec['department'] = params[4]
                            rec['position'] = params[5]
                            return True
                    return False
                return None

            def commit(self):
                pass

        manager = ContactsManager(MockDB())

        # 导入新数据
        new_data = {
            'name': '赵六',
            'employee_id': 'EMP001',
            'department': '部门B',
            'phone': '13800000002'
        }

        success, message, contact_id = manager.add_contact(new_data, refresh_if_exists=True)

        # 验证结果
        assert success is True
        assert '已刷新' in message
        assert contact_id == 1  # 应该更新现有记录

    def test_add_new_contact_with_same_name(self):
        """测试：添加同名但不同工号的新联系人

        场景：
            现有：赵六，EMP001
            新增：赵六，EMP002

        期望：
            两条记录都保留
        """
        from src.database.contacts_manager import ContactsManager

        class MockDB:
            def __init__(self):
                self.records = []
                self.next_id = 1

            def execute_query(self, sql, params=None):
                # 查找同名同工号
                if 'SELECT' in sql and 'WHERE' in sql:
                    name = params[0]
                    emp_id = params[1] if len(params) > 1 else ''
                    for rec in self.records:
                        if rec['name'] == name and rec.get('employee_id') == emp_id:
                            return [rec]
                    return []
                # 查找同名
                elif 'SELECT' in sql and 'ORDER BY' in sql:
                    name = params[0]
                    return [rec for rec in self.records if rec['name'] == name]
                return []

            def execute(self, sql, params=None):
                from datetime import datetime
                if 'INSERT' in sql:
                    new_id = self.next_id
                    self.next_id += 1
                    self.records.append({
                        'id': new_id,
                        'name': params[0],
                        'employee_id': params[1],
                        'phone': params[2],
                        'email': params[3],
                        'department': params[4],
                        'position': params[5],
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    })

                    class Cursor:
                        lastrowid = new_id
                    return Cursor()
                return None

            def commit(self):
                pass

        manager = ContactsManager(MockDB())

        # 添加第一条
        success1, _, id1 = manager.add_contact({
            'name': '赵六',
            'employee_id': 'EMP001'
        }, refresh_if_exists=False)

        # 添加第二条（同名不同工号）
        success2, _, id2 = manager.add_contact({
            'name': '赵六',
            'employee_id': 'EMP002'
        }, refresh_if_exists=False)

        # 验证
        assert success1 is True
        assert success2 is True  # 应该能成功添加
        assert id1 != id2  # ID应该不同


# =============================================================================
# 测试场景：完整业务流程
# =============================================================================

class TestCompleteScenario:
    """完整业务流程测试"""

    def test_scenario_recommendation_with_multiple_modules(self):
        """测试场景：推荐库多关键模块完整流程

        步骤：
        1. 批量导入多个同名不同关键模块的记录
        2. 搜索任一关键模块
        3. 验证返回合并后的完整记录
        """
        from src.database.recommendations import RecommendationService

        class MockDB:
            def __init__(self):
                self.records = []

            def execute_query(self, sql, params=None):
                keyword = params[0] if params else ''
                # 模拟包含关键字的记录
                results = []
                for rec in self.records:
                    if keyword in rec.get('key_module', ''):
                        results.append(rec)
                return results

        db = MockDB()

        # 模拟导入数据
        db.records = [
            {'name': '赵六', 'employee_id': 'EMP001', 'key_module': 'MAC认证', 'phone': '13800138001'},
            {'name': '赵六', 'employee_id': 'EMP001', 'key_module': '802.1x认证', 'phone': '13800138001'},
            {'name': '赵六', 'employee_id': 'EMP001', 'key_module': 'Portal认证', 'phone': '13800138001'},
            {'name': '王五', 'employee_id': 'EMP002', 'key_module': 'MAC认证', 'phone': '13800138002'},
        ]

        service = RecommendationService(db)

        # 搜索MAC认证
        result_mac = service.recommend_responder("MAC认证")

        # 验证MAC认证搜索结果
        assert result_mac is not None
        assert result_mac['name'] == '赵六'
        assert 'MAC认证' in result_mac['key_module']
        assert '802.1x认证' in result_mac['key_module']
        assert 'Portal认证' in result_mac['key_module']

        # 搜索802.1x认证
        result_8021x = service.recommend_responder("802.1x认证")

        # 验证802.1x认证搜索结果（应该是同一条合并后的记录）
        assert result_8021x is not None
        assert result_8021x['name'] == '赵六'
        assert 'MAC认证' in result_8021x['key_module']

        # 搜索Portal认证
        result_portal = service.recommend_responder("Portal认证")

        assert result_portal is not None
        assert result_portal['name'] == '赵六'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
