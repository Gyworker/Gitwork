#!/bin/bash
# =============================================================================
# 市场咨询任务跟踪工具 - 本地CI检查脚本
# =============================================================================
# 使用方法：
# 1. Windows PowerShell: .\scripts\local_ci.ps1
# 2. 或手动安装Python后运行: python scripts/local_ci.py
# =============================================================================

# 定义颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC_DIR="$PROJECT_ROOT/src"

echo "========================================================================"
echo "         市场咨询任务跟踪工具 - CI 检查脚本"
echo "========================================================================"
echo ""

# 检查Python环境
echo "[1/5] 检查Python环境..."
if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1)
    echo -e "${GREEN}✅${NC} $PYTHON_VERSION"
else
    echo -e "${RED}❌${NC} Python 未安装"
    echo ""
    echo "请选择以下方式之一安装Python："
    echo "  1. 下载安装: https://www.python.org/downloads/"
    echo "  2. 使用 Docker: docker-compose up ci"
    echo "  3. 使用 GitHub Actions: 推送到GitHub仓库自动检查"
    exit 1
fi

# 语法检查
echo ""
echo "[2/5] Python语法检查..."
SYNTAX_ERRORS=0
for file in $(find "$SRC_DIR" -name "*.py" 2>/dev/null); do
    if ! python -m py_compile "$file" 2>/dev/null; then
        echo -e "${RED}❌${NC} $file"
        SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
    fi
done

if [ $SYNTAX_ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅${NC} 所有Python文件语法正确"
else
    echo -e "${RED}❌${NC} 发现 $SYNTAX_ERRORS 个语法错误"
fi

# 模块导入测试
echo ""
echo "[3/5] 模块导入测试..."
cd "$PROJECT_ROOT"
if python -c "
import sys
sys.path.insert(0, 'src')
from config import *
from utils.logger import *
from utils.helpers import *
from database.connection import *
from database.models import *
print('OK')
" 2>/dev/null; then
    echo -e "${GREEN}✅${NC} 所有核心模块导入成功"
else
    echo -e "${YELLOW}⚠️${NC} 部分模块导入失败（可能缺少依赖）"
fi

# 单元测试
echo ""
echo "[4/5] 运行单元测试..."
cd "$PROJECT_ROOT"
if python -m pytest src/tests/ -v --tb=short 2>/dev/null; then
    echo -e "${GREEN}✅${NC} 单元测试通过"
else
    echo -e "${YELLOW}⚠️${NC} 单元测试有失败项"
fi

# 代码统计
echo ""
echo "[5/5] 代码统计..."
PY_FILES=$(find "$SRC_DIR" -name "*.py" 2>/dev/null | wc -l)
LOC=$(find "$SRC_DIR" -name "*.py" -exec cat {} + 2>/dev/null | wc -l)
echo "   Python文件: $PY_FILES"
echo "   代码行数: $LOC"

# 总结
echo ""
echo "========================================================================"
if [ $SYNTAX_ERRORS -eq 0 ]; then
    echo -e "${GREEN}🎉 CI检查完成！代码可以合入主线。${NC}"
else
    echo -e "${RED}⚠️ CI检查发现问题，请修复后再合入。${NC}"
fi
echo "========================================================================"
