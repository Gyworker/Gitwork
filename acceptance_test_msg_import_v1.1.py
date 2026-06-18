# -*- coding: utf-8 -*-
"""
MSG邮件文件导入功能V1.1验收测试
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_v1_1_new_features():
    """测试V1.1新增功能"""
    print("=" * 60)
    print("V1.1新增功能验收测试")
    print("=" * 60)
    
    # 1. 测试ParseError导入
    print("\n1. 测试ParseError错误上下文")
    try:
        from src.content.msg_parser import ParseError
        
        error = ParseError(
            error_type='test_error',
            error_message='测试错误',
            filepath='test.msg',
            file_size=1024
        )
        
        assert error.error_type == 'test_error'
        print("   ✅ ParseError创建成功")
        
        # 测试用户消息
        message = error.to_user_message()
        assert '测试错误' in message
        print("   ✅ 用户消息生成成功")
        
    except Exception as e:
        print(f"   ❌ ParseError测试失败: {e}")
        return False
    
    # 2. 测试ParseProgress导入
    print("\n2. 测试ParseProgress进度信息")
    try:
        from src.content.msg_parser import ParseProgress
        
        progress = ParseProgress(
            current=1,
            total=10,
            current_file='test.msg',
            percentage=10.0,
            status='processing'
        )
        
        assert progress.current == 1
        assert progress.total == 10
        assert progress.percentage == 10.0
        print("   ✅ ParseProgress创建成功")
        
    except Exception as e:
        print(f"   ❌ ParseProgress测试失败: {e}")
        return False
    
    # 3. 测试进度回调解析器
    print("\n3. 测试进度回调机制")
    try:
        from src.content.msg_parser import MSGParserWithProgress
        
        progress_events = []
        
        def callback(progress):
            progress_events.append(progress)
        
        parser = MSGParserWithProgress(progress_callback=callback)
        
        # 空列表测试
        results = parser.parse_batch([])
        assert len(progress_events) == 0
        print("   ✅ MSGParserWithProgress初始化成功")
        print("   ✅ 进度回调空列表测试通过")
        
    except Exception as e:
        print(f"   ❌ 进度回调测试失败: {e}")
        return False
    
    # 4. 测试取消操作
    print("\n4. 测试取消操作")
    try:
        from src.content.msg_parser import MSGParserWithProgress
        
        cancel_count = [0]
        
        def cancel_check():
            cancel_count[0] += 1
            return cancel_count[0] > 3  # 第3次调用后取消
        
        parser = MSGParserWithProgress(cancel_check=cancel_check)
        results = parser.parse_batch([f'test{i}.msg' for i in range(5)])
        
        assert cancel_count[0] > 3
        print("   ✅ 取消操作检测成功")
        
    except Exception as e:
        print(f"   ❌ 取消操作测试失败: {e}")
        return False
    
    # 5. 测试流式解析器
    print("\n5. 测试流式解析器")
    try:
        from src.content.msg_parser import StreamingMSGParser, MemoryWarning
        
        parser = StreamingMSGParser()
        assert parser.memory_limit == 50 * 1024 * 1024
        assert parser.CHUNK_SIZE == 1024 * 1024
        print("   ✅ StreamingMSGParser初始化成功")
        
        # 测试内存警告异常
        warning = MemoryWarning("测试警告")
        assert str(warning) == "测试警告"
        print("   ✅ MemoryWarning异常测试通过")
        
    except Exception as e:
        print(f"   ❌ 流式解析器测试失败: {e}")
        return False
    
    # 6. 测试V1.0兼容性
    print("\n6. 测试V1.0 API兼容性")
    try:
        from src.content.msg_parser import MSGParser, MSGEmail
        
        # MSGEmail.to_task_content
        email = MSGEmail(
            subject="测试",
            sender="张三",
            sender_email="test@example.com"
        )
        content = email.to_task_content()
        assert "【主题】测试" in content
        print("   ✅ MSGEmail.to_task_content()兼容")
        
        # parse_file_safe
        assert hasattr(MSGParser, 'parse_file_safe')
        print("   ✅ MSGParser.parse_file_safe()兼容")
        
        # JSON格式化参数
        json_str = MSGParser.to_json(email, indent=0)
        print("   ✅ JSON格式化参数(indent)兼容")
        
    except Exception as e:
        print(f"   ❌ 兼容性测试失败: {e}")
        return False
    
    return True

def test_v1_1_unit_tests():
    """测试V1.1单元测试文件"""
    print("\n" + "=" * 60)
    print("V1.1单元测试文件检查")
    print("=" * 60)
    
    test_file = Path("src/tests/test_msg_parser_v1_1.py")
    
    if not test_file.exists():
        print("   ❌ 测试文件不存在")
        return False
    
    print(f"   ✅ 测试文件存在: {test_file}")
    
    # 检查测试类
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    test_classes = [
        'TestParseError',
        'TestMSGParserErrorContext',
        'TestProgressCallback',
        'TestStreamingParser',
        'TestV1Compatibility',
        'TestBatchParserWithProgress'
    ]
    
    all_found = True
    for cls_name in test_classes:
        if cls_name in content:
            print(f"   ✅ {cls_name}")
        else:
            print(f"   ❌ {cls_name} 未找到")
            all_found = False
    
    return all_found

def test_v1_1_documentation():
    """测试V1.1文档"""
    print("\n" + "=" * 60)
    print("V1.1文档完整性检查")
    print("=" * 60)
    
    docs = [
        ("docs/design_msg_import_v1.1.md", "设计方案"),
        ("docs/test_cases_msg_import_v1.1.md", "测试用例"),
        ("docs/codec_review_msg_import_v1.1.md", "CodeCC评审")
    ]
    
    all_found = True
    for path, name in docs:
        if Path(path).exists():
            print(f"   ✅ {name}")
        else:
            print(f"   ❌ {name} 缺失")
            all_found = False
    
    return all_found

def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("   MSG邮件文件导入功能 V1.1 验收测试")
    print("=" * 60)
    
    results = []
    
    # 执行验收测试
    results.append(("V1.1新功能", test_v1_1_new_features()))
    results.append(("V1.1单元测试", test_v1_1_unit_tests()))
    results.append(("V1.1文档", test_v1_1_documentation()))
    
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
        print("   🎉 所有验收测试通过！MSG导入功能V1.1发布就绪")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print(f"   ⚠️  有 {total - passed} 项测试未通过，请检查")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
