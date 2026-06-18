# -*- coding: utf-8 -*-
"""
测试结果收集脚本
用于收集和汇总测试执行结果
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
TEST_DIR = PROJECT_ROOT / "src" / "tests"

def run_tests():
    """运行测试并收集结果"""
    print("=" * 70)
    print("  市场咨询任务跟踪工具 V4.4 单元测试")
    print("=" * 70)
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  项目: {PROJECT_ROOT}")
    print("=" * 70)
    print()

    # 切换到项目目录
    os.chdir(str(PROJECT_ROOT))

    # 运行pytest
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "src/tests/", "-v", "--tb=short", "--color=no"],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    print()
    print("=" * 70)
    print("  测试结果摘要")
    print("=" * 70)

    # 解析结果
    output = result.stdout + result.stderr

    # 统计信息
    passed_count = output.count(" PASSED")
    failed_count = output.count(" FAILED")
    skipped_count = output.count(" SKIPPED")
    error_count = output.count(" ERROR")

    total = passed_count + failed_count + skipped_count + error_count

    print(f"  总测试数: {total}")
    print(f"  通过: {passed_count}")
    print(f"  失败: {failed_count}")
    print(f"  跳过: {skipped_count}")
    print(f"  错误: {error_count}")
    print()

    if failed_count == 0 and error_count == 0:
        print("  ✅ 所有测试通过！")
    else:
        print(f"  ⚠️  有 {failed_count + error_count} 项测试未通过")

    print("=" * 70)

    # 保存结果到文件
    report_file = PROJECT_ROOT / "logs" / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    report_file.parent.mkdir(exist_ok=True)

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("  市场咨询任务跟踪工具 V4.4 单元测试报告\n")
        f.write("=" * 70 + "\n")
        f.write(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"  项目: {PROJECT_ROOT}\n")
        f.write("=" * 70 + "\n\n")
        f.write(result.stdout)
        if result.stderr:
            f.write("\nSTDERR:\n")
            f.write(result.stderr)
        f.write("\n\n" + "=" * 70 + "\n")
        f.write(f"  总测试数: {total}\n")
        f.write(f"  通过: {passed_count}\n")
        f.write(f"  失败: {failed_count}\n")
        f.write(f"  跳过: {skipped_count}\n")
        f.write(f"  错误: {error_count}\n")
        f.write("=" * 70 + "\n")

    print(f"\n报告已保存到: {report_file}")

    return 0 if (failed_count == 0 and error_count == 0) else 1

if __name__ == "__main__":
    sys.exit(run_tests())
