@echo off
chcp 65001 >nul
echo ============================================
echo   市场咨询任务跟踪工具 V2.1 测试运行器
echo ============================================
echo.

cd /d "%~dp0.."

echo [1/4] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [2/4] 检查测试依赖...
python -c "import pytest" >nul 2>&1
if errorlevel 1 (
    echo [警告] 缺少pytest，正在安装...
    pip install pytest pytest-cov pandas openpyxl Pillow pytesseract
)

echo.
echo ============================================
echo   开始运行测试
echo ============================================
echo.

echo [3/4] 运行Excel导入模块测试...
python -m pytest src/tests/test_excel_import.py -v --tb=short

echo.
echo ============================================
echo   Excel导入模块测试完成
echo ============================================
echo.

echo [4/4] 运行OCR处理模块测试...
python -m pytest src/tests/test_ocr_handler.py -v --tb=short

echo.
echo ============================================
echo   OCR处理模块测试完成
echo ============================================
echo.

echo [5/4] 运行映射学习模块测试...
python -m pytest src/tests/test_enhanced_mapping.py -v --tb=short

echo.
echo ============================================
echo   映射学习模块测试完成
echo ============================================
echo.

echo [6/4] 运行代码质量检查...
python -m pylint src/content/excel_import.py src/content/ocr_handler.py src/learning/enhanced_mapping.py --disable=C0111,C0103,R0903,R0913 > nul 2>&1
if errorlevel 1 (
    echo [注意] 代码规范检查有警告，请查看上述输出
) else (
    echo [通过] 代码规范检查通过
)

echo.
echo ============================================
echo   所有测试完成！
echo ============================================
echo.
echo 生成详细测试报告请运行：
echo python -m pytest src/tests/ -v --cov=src --cov-report=html
echo.
pause
