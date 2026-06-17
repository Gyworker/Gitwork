# -*- coding: utf-8 -*-
"""
MSG邮件文件导入功能验收测试
版本: V1.0
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("验收测试 1: 模块导入")
    print("=" * 60)
    
    try:
        from src.content.msg_parser import MSGParser, MSGEmail, BatchMSGParser
        print("✅ MSGParser 导入成功")
        print("✅ MSGEmail 导入成功")
        print("✅ BatchMSGParser 导入成功")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_data_structure():
    """测试数据结构"""
    print("\n" + "=" * 60)
    print("验收测试 2: MSGEmail数据结构")
    print("=" * 60)
    
    try:
        from src.content.msg_parser import MSGEmail
        
        # 创建测试邮件
        email = MSGEmail(
            subject="测试邮件",
            sender="张三",
            sender_email="zhangsan@example.com",
            body="这是一封测试邮件",
            date="2026-06-17"
        )
        
        # 验证字段
        assert email.subject == "测试邮件", "主题不匹配"
        assert email.sender == "张三", "发件人不匹配"
        assert email.sender_email == "zhangsan@example.com", "邮箱不匹配"
        
        print("✅ MSGEmail对象创建成功")
        print(f"   主题: {email.subject}")
        print(f"   发件人: {email.sender}")
        print(f"   邮箱: {email.sender_email}")
        
        return True
    except Exception as e:
        print(f"❌ 数据结构测试失败: {e}")
        return False

def test_library_status():
    """测试库状态检查"""
    print("\n" + "=" * 60)
    print("验收测试 3: MSG解析库状态")
    print("=" * 60)
    
    try:
        from src.content.msg_parser import MSGParser
        
        # 获取库信息
        info = MSGParser.get_library_info()
        available = MSGParser.is_available()
        
        print(f"库名称: {info['library']}")
        print(f"库可用: {available}")
        print(f"版本信息: {info.get('version', 'N/A')}")
        
        if available:
            print("✅ extract-msg库已安装，优先使用")
        else:
            print("ℹ️ extract-msg库未安装，将使用备用解析方案")
        
        return True
    except Exception as e:
        print(f"❌ 库状态检查失败: {e}")
        return False

def test_task_content_generation():
    """测试任务内容生成"""
    print("\n" + "=" * 60)
    print("验收测试 4: 任务内容生成")
    print("=" * 60)
    
    try:
        from src.content.msg_parser import MSGEmail
        
        email = MSGEmail(
            subject="产品报价咨询",
            sender="李四",
            sender_email="lisi@example.com",
            date="2026-06-17 10:00",
            body="请尽快提供报价清单",
            importance="高"
        )
        
        content = email.to_task_content()
        
        # 验证内容格式
        assert "【主题】产品报价咨询" in content, "主题缺失"
        assert "【发件人】李四" in content, "发件人缺失"
        assert "【邮箱】lisi@example.com" in content, "邮箱缺失"
        assert "【时间】2026-06-17 10:00" in content, "时间缺失"
        assert "【重要程度】高" in content, "重要程度缺失"
        assert "请尽快提供报价清单" in content, "正文缺失"
        
        print("✅ 任务内容生成成功")
        print("-" * 40)
        print(content[:200] + "..." if len(content) > 200 else content)
        
        return True
    except Exception as e:
        print(f"❌ 任务内容生成失败: {e}")
        return False

def test_json_serialization():
    """测试JSON序列化"""
    print("\n" + "=" * 60)
    print("验收测试 5: JSON序列化")
    print("=" * 60)
    
    try:
        from src.content.msg_parser import MSGParser, MSGEmail
        
        email = MSGEmail(
            subject="测试邮件",
            sender="张三",
            sender_email="zhangsan@example.com"
        )
        
        # 测试字典转换
        data = email.to_dict()
        assert isinstance(data, dict), "to_dict返回非字典"
        assert data['subject'] == "测试邮件", "字典内容错误"
        
        print("✅ to_dict()转换成功")
        
        # 测试JSON字符串
        json_str = MSGParser.to_json(email)
        assert isinstance(json_str, str), "to_json返回非字符串"
        assert "测试邮件" in json_str, "JSON内容错误"
        
        print("✅ to_json()转换成功")
        
        return True
    except Exception as e:
        print(f"❌ JSON序列化失败: {e}")
        return False

def test_batch_parser():
    """测试批量解析器"""
    print("\n" + "=" * 60)
    print("验收测试 6: 批量解析器")
    print("=" * 60)
    
    try:
        from src.content.msg_parser import BatchMSGParser
        
        parser = BatchMSGParser()
        
        # 验证初始化
        assert parser.results == [], "results初始化错误"
        assert parser.errors == [], "errors初始化错误"
        
        print("✅ BatchMSGParser初始化成功")
        
        # 获取摘要
        summary = parser.get_summary()
        assert 'total_files' in summary, "摘要缺少total_files"
        assert 'success_count' in summary, "摘要缺少success_count"
        assert 'error_count' in summary, "摘要缺少error_count"
        
        print("✅ 摘要生成功能正常")
        
        return True
    except Exception as e:
        print(f"❌ 批量解析器测试失败: {e}")
        return False

def test_ui_integration():
    """测试UI集成"""
    print("\n" + "=" * 60)
    print("验收测试 7: UI集成检查")
    print("=" * 60)
    
    try:
        # 检查UI文件是否存在修改
        ui_file = Path("src/ui/content_import.py")
        assert ui_file.exists(), "UI文件不存在"
        
        with open(ui_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键修改点
        checks = [
            ("MSGParser导入", "from src.content.msg_parser import MSGParser"),
            ("MSGEmail导入", "MSGEmail"),
            ("邮件(MSG)标签", "邮件(MSG)"),
            ("_load_msg_file方法", "def _load_msg_file"),
            ("_parse_outlook重写", "_parse_outlook")
        ]
        
        all_passed = True
        for name, pattern in checks:
            if pattern in content:
                print(f"✅ {name}")
            else:
                print(f"❌ {name} - 缺失")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"❌ UI集成检查失败: {e}")
        return False

def test_requirements():
    """测试依赖配置"""
    print("\n" + "=" * 60)
    print("验收测试 8: 依赖配置检查")
    print("=" * 60)
    
    try:
        req_file = Path("requirements.txt")
        assert req_file.exists(), "requirements.txt不存在"
        
        with open(req_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查extract-msg依赖
        if "extract-msg" in content:
            print("✅ extract-msg依赖已配置")
        else:
            print("❌ extract-msg依赖缺失")
            return False
        
        return True
    except Exception as e:
        print(f"❌ 依赖配置检查失败: {e}")
        return False

def test_documentation():
    """测试文档完整性"""
    print("\n" + "=" * 60)
    print("验收测试 9: 文档完整性检查")
    print("=" * 60)
    
    try:
        docs = [
            ("docs/design_msg_import_v1.0.md", "设计方案"),
            ("docs/test_cases_msg_import_v1.0.md", "测试用例"),
            ("docs/codec_review_msg_import_v1.0.md", "CodeCC评审")
        ]
        
        all_passed = True
        for path, name in docs:
            if Path(path).exists():
                print(f"✅ {name}存在")
            else:
                print(f"❌ {name}缺失")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"❌ 文档检查失败: {e}")
        return False

def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("   MSG邮件文件导入功能 V1.0 验收测试")
    print("=" * 60)
    
    results = []
    
    # 执行所有验收测试
    results.append(("模块导入", test_imports()))
    results.append(("数据结构", test_data_structure()))
    results.append(("库状态", test_library_status()))
    results.append(("任务内容生成", test_task_content_generation()))
    results.append(("JSON序列化", test_json_serialization()))
    results.append(("批量解析器", test_batch_parser()))
    results.append(("UI集成", test_ui_integration()))
    results.append(("依赖配置", test_requirements()))
    results.append(("文档完整性", test_documentation()))
    
    # 输出测试结果汇总
    print("\n" + "=" * 60)
    print("   验收测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
    
    print("-" * 60)
    print(f"  总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n" + "=" * 60)
        print("   🎉 所有验收测试通过！MSG导入功能V1.0发布就绪")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print(f"   ⚠️  有 {total - passed} 项测试未通过，请检查")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
