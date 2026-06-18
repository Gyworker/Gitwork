@echo off
chcp 65001 > nul
echo ========================================
echo   市场咨询任务跟踪工具 V4.6
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.10或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查依赖
echo [1/3] 检查依赖...
pip show PyQt5 >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装PyQt5...
    pip install PyQt5
)

pip show openpyxl >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装openpyxl...
    pip install openpyxl
)

REM 启动应用
echo [2/3] 启动应用程序...
echo.
python "%~dp0run_market_task_tracker.py"

if errorlevel 1 (
    echo.
    echo [错误] 应用程序启动失败
    pause
    exit /b 1
)

echo.
echo [3/3] 应用程序已退出
pause
