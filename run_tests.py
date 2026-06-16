#!/usr/bin/env python
"""
测试运行脚本
用于本地运行单元测试
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import pytest
    
    # 运行测试
    exit_code = pytest.main([
        "src/tests/",
        "-v",
        "--tb=short",
        "-x",  # 遇到第一个失败就停止
    ])
    
    sys.exit(exit_code)
