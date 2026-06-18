# -*- coding: utf-8 -*-
"""
V4.5 功能验证脚本
直接运行验证测试，不需要pytest
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_contacts_unique_key():
    """测试通讯录唯一键"""
    print("\n" + "="*60)
    print("测试1: 通讯录姓名+工号唯一键")
    print("="*60)

    from src.database.contacts_manager import ContactsManager

    # 测试用例
    test_cases = [
        ("赵六", "EMP001", "赵六|EMP001"),
        ("赵六", "", "赵六|"),
        ("赵六", "EMP002", "赵六|EMP002"),
        ("王五", "EMP001", "王五|EMP001"),
    ]

    all_passed = True
    for name, emp_id, expected in test_cases:
        result = ContactsManager.make_unique_key(name, emp_id)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        if result != expected:
            all_passed = False
        print(f"  {name} + {emp_id or '(无)'} → {result}  {status}")

    # 验证不同工号生成不同键
    key1 = ContactsManager.make_unique_key("赵六", "EMP001")
    key2 = ContactsManager.make_unique_key("赵六", "EMP002")
    status = "✅ PASS" if key1 != key2 else "❌ FAIL"
    if key1 == key2:
        all_passed = False
    print(f"\n  同名不同工号应生成不同键: {key1} vs {key2}  {status}")

    # 解析测试
    name, emp_id = ContactsManager.parse_unique_key("赵六|EMP001")
    status = "✅ PASS" if name == "赵六" and emp_id == "EMP001" else "❌ FAIL"
    if name != "赵六" or emp_id != "EMP001":
        all_passed = False
    print(f"  解析唯一键 '赵六|EMP001' → name={name}, emp_id={emp_id}  {status}")

    return all_passed


def test_recommendation_merge():
    """测试推荐库合并"""
    print("\n" + "="*60)
    print("测试2: 推荐库同姓名多关键模块合并")
    print("="*60)

    from src.database.recommendations import RecommendationService

    # 模拟数据库
    class MockDB:
        def execute_query(self, sql, params=None):
            return []

    service = RecommendationService(MockDB())

    # 测试用例：同姓名多条记录
    records = [
        {'name': '赵六', 'employee_id': 'EMP001', 'key_module': 'MAC认证'},
        {'name': '赵六', 'employee_id': 'EMP001', 'key_module': '802.1x认证'},
    ]

    merged = service.merge_recommendations(records)

    all_passed = True

    # 验证合并为一条记录
    status = "✅ PASS" if len(merged) == 1 else "❌ FAIL"
    if len(merged) != 1:
        all_passed = False
    print(f"  同姓名2条记录合并为1条: {len(merged)}条  {status}")

    # 验证关键模块已合并
    merged_key_modules = merged[0].get('key_module', '')
    has_mac = 'MAC认证' in merged_key_modules
    has_8021x = '802.1x认证' in merged_key_modules

    status1 = "✅ PASS" if has_mac else "❌ FAIL"
    status2 = "✅ PASS" if has_8021x else "❌ FAIL"
    if not has_mac or not has_8021x:
        all_passed = False

    print(f"  关键模块包含MAC认证: {status1}")
    print(f"  关键模块包含802.1x认证: {status2}")
    print(f"  合并后关键模块: {merged_key_modules}")

    # 验证合并标记
    is_merged = merged[0].get('is_merged', False)
    merged_from = merged[0].get('merged_from', 0)
    status1 = "✅ PASS" if is_merged else "❌ FAIL"
    status2 = "✅ PASS" if merged_from == 2 else "❌ FAIL"
    if not is_merged or merged_from != 2:
        all_passed = False
    print(f"  is_merged=True: {status1}")
    print(f"  merged_from=2: {status2}")

    return all_passed


def test_recommendation_no_merge_different_empid():
    """测试不同工号不合并"""
    print("\n" + "="*60)
    print("测试3: 同姓名不同工号不合并")
    print("="*60)

    from src.database.recommendations import RecommendationService

    class MockDB:
        def execute_query(self, sql, params=None):
            return []

    service = RecommendationService(MockDB())

    records = [
        {'name': '赵六', 'employee_id': 'EMP001', 'key_module': 'MAC认证'},
        {'name': '赵六', 'employee_id': 'EMP002', 'key_module': '802.1x认证'},
    ]

    merged = service.merge_recommendations(records)

    all_passed = True
    status = "✅ PASS" if len(merged) == 2 else "❌ FAIL"
    if len(merged) != 2:
        all_passed = False

    print(f"  同姓名不同工号应保留2条记录: {len(merged)}条  {status}")

    return all_passed


def test_smart_recommend():
    """测试智能推荐"""
    print("\n" + "="*60)
    print("测试4: 智能推荐匹配")
    print("="*60)

    from src.database.recommendations import RecommendationService

    class MockDB:
        def execute_query(self, sql, params=None):
            # 返回包含"赵六"的记录
            return [
                {'name': '赵六', 'employee_id': 'EMP001', 'key_module': 'MAC认证', 'phone': '13800138001'},
                {'name': '赵六', 'employee_id': 'EMP001', 'key_module': '802.1x认证', 'phone': '13800138001'},
            ]

    service = RecommendationService(MockDB())

    all_passed = True

    # 搜索MAC认证
    result1 = service.recommend_responder("MAC认证")
    status1 = "✅ PASS" if result1 and result1['name'] == '赵六' else "❌ FAIL"
    if not result1 or result1['name'] != '赵六':
        all_passed = False
    print(f"  搜索'MAC认证' → 推荐 {result1['name'] if result1 else 'None'}  {status1}")

    # 搜索802.1x认证
    result2 = service.recommend_responder("802.1x认证")
    status2 = "✅ PASS" if result2 and result2['name'] == '赵六' else "❌ FAIL"
    if not result2 or result2['name'] != '赵六':
        all_passed = False
    print(f"  搜索'802.1x认证' → 推荐 {result2['name'] if result2 else 'None'}  {status2}")

    # 验证返回的记录包含所有关键模块
    if result1:
        has_mac = 'MAC认证' in result1.get('key_module', '')
        has_8021x = '802.1x认证' in result1.get('key_module', '')
        status3 = "✅ PASS" if has_mac and has_8021x else "❌ FAIL"
        if not has_mac or not has_8021x:
            all_passed = False
        print(f"  推荐结果包含全部关键模块: {status3}")
        print(f"  关键模块: {result1.get('key_module', '')}")

    return all_passed


def test_contacts_sync():
    """测试通讯录同步刷新"""
    print("\n" + "="*60)
    print("测试5: 通讯录信息同步刷新")
    print("="*60)

    from src.database.contacts_manager import ContactsManager

    class MockDB:
        def __init__(self):
            self.records = []
            self.next_id = 1

        def execute_query(self, sql, params=None):
            if 'SELECT' in sql and 'WHERE' in sql:
                name = params[0]
                for rec in self.records:
                    if rec['name'] == name:
                        return [rec]
                return []
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

    all_passed = True

    # 添加第一条记录
    success1, msg1, id1 = manager.add_contact({
        'name': '赵六',
        'employee_id': 'EMP001',
        'department': '部门A',
        'phone': '13800000001'
    }, refresh_if_exists=False)

    status1 = "✅ PASS" if success1 else "❌ FAIL"
    if not success1:
        all_passed = False
    print(f"  添加赵六/部门A: {msg1}  {status1}")

    # 刷新已有记录
    success2, msg2, id2 = manager.add_contact({
        'name': '赵六',
        'employee_id': 'EMP001',
        'department': '部门B',  # 变化
        'phone': '13800000002'  # 变化
    }, refresh_if_exists=True)

    status2 = "✅ PASS" if success2 and '已刷新' in msg2 else "❌ FAIL"
    if not success2 or '已刷新' not in msg2:
        all_passed = False
    print(f"  刷新赵六为部门B: {msg2}  {status2}")

    # 验证ID相同（应该是更新而不是新增）
    status3 = "✅ PASS" if id1 == id2 else "❌ FAIL"
    if id1 != id2:
        all_passed = False
    print(f"  刷新后ID保持一致: {id1} == {id2}  {status3}")

    # 添加同名不同工号
    success3, msg3, id3 = manager.add_contact({
        'name': '赵六',
        'employee_id': 'EMP002',  # 不同工号
        'department': '部门C'
    }, refresh_if_exists=False)

    status4 = "✅ PASS" if success3 and '已添加' in msg3 else "❌ FAIL"
    if not success3 or '已添加' not in msg3:
        all_passed = False
    print(f"  添加同名不同工号赵六/EMP002: {msg3}  {status4}")

    return all_passed


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("V4.5 新功能验收测试")
    print("="*60)

    results = []

    # 运行测试
    results.append(("通讯录唯一键", test_contacts_unique_key()))
    results.append(("推荐库合并", test_recommendation_merge()))
    results.append(("不同工号不合并", test_recommendation_no_merge_different_empid()))
    results.append(("智能推荐", test_smart_recommend()))
    results.append(("通讯录同步", test_contacts_sync()))

    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有验收测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试未通过")
        return 1


if __name__ == '__main__':
    sys.exit(main())
