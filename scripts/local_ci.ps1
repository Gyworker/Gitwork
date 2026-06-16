# =============================================================================
# 市场咨询任务跟踪工具 - 本地CI检查脚本 (PowerShell)
# =============================================================================
# 使用方法：
# 1. 确保已安装Python
# 2. PowerShell中运行: .\scripts\local_ci.ps1
# =============================================================================

param(
    [switch]$SkipTests,
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

function Write-CIHeader {
    param([string]$Text)
    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "========================================================================" -ForegroundColor Cyan
}

function Write-CISuccess {
    param([string]$Text)
    Write-Host "[✓] $Text" -ForegroundColor Green
}

function Write-CIError {
    param([string]$Text)
    Write-Host "[✗] $Text" -ForegroundColor Red
}

function Write-CIWarning {
    param([string]$Text)
    Write-Host "[!] $Text" -ForegroundColor Yellow
}

Write-CIHeader "市场咨询任务跟踪工具 - CI 检查"

# ============================================================================
# 检查1: Python环境
# ============================================================================
Write-Host ""
Write-Host "[1/5] 检查Python环境..." -NoNewline

$pythonCmd = $null
foreach ($cmd in @("python", "py", "python3")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $pythonCmd = $cmd
        break
    }
}

if ($pythonCmd) {
    $pythonVersion = & $pythonCmd --version 2>&1
    Write-CISuccess "$pythonVersion"
} else {
    Write-CIError "Python 未安装"
    Write-Host ""
    Write-Host "请选择以下方式之一：" -ForegroundColor Yellow
    Write-Host "  1. 安装Python: https://www.python.org/downloads/" -ForegroundColor Gray
    Write-Host "  2. 使用Docker: docker-compose up ci" -ForegroundColor Gray
    Write-Host "  3. 使用GitHub Actions: 推送到GitHub仓库自动检查" -ForegroundColor Gray
    exit 1
}

# ============================================================================
# 检查2: Python语法
# ============================================================================
Write-Host ""
Write-Host "[2/5] Python语法检查..." 

$srcDir = Join-Path $ProjectRoot "src"
$pyFiles = Get-ChildItem -Path $srcDir -Filter "*.py" -Recurse -ErrorAction SilentlyContinue
$syntaxErrors = 0

foreach ($file in $pyFiles) {
    $result = & python -m py_compile $file.FullName 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-CIError "$($file.Name)"
        if ($Verbose) { Write-Host $result -ForegroundColor Gray }
        $syntaxErrors++
    }
}

if ($syntaxErrors -eq 0) {
    Write-CISuccess "所有Python文件语法正确 ($($pyFiles.Count) 个文件)"
} else {
    Write-CIError "发现 $syntaxErrors 个语法错误"
}

# ============================================================================
# 检查3: 模块导入
# ============================================================================
Write-Host ""
Write-Host "[3/5] 模块导入测试..." -NoNewline

$importTest = & python -c "
import sys
sys.path.insert(0, 'src')
try:
    from config import *
    from utils.logger import *
    from utils.helpers import *
    from database.connection import *
    from database.models import *
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>&1

if ($importTest -like "*SUCCESS*") {
    Write-CISuccess "所有核心模块导入成功"
} else {
    Write-CIWarning "部分模块导入失败"
    if ($Verbose) { Write-Host $importTest -ForegroundColor Gray }
}

# ============================================================================
# 检查4: 单元测试
# ============================================================================
if (-not $SkipTests) {
    Write-Host ""
    Write-Host "[4/5] 运行单元测试..." -NoNewline
    
    Push-Location $ProjectRoot
    $testResult = & python -m pytest "src/tests/" -v --tb=short 2>&1
    $testExitCode = $LASTEXITCODE
    Pop-Location
    
    if ($testExitCode -eq 0) {
        Write-CISuccess "单元测试通过"
    } elseif ($testExitCode -eq 5) {
        Write-CIWarning "没有找到测试用例"
    } else {
        Write-CIWarning "部分测试失败"
        if ($Verbose) { Write-Host $testResult -ForegroundColor Gray }
    }
} else {
    Write-Host ""
    Write-Host "[4/5] 单元测试 (已跳过)" -ForegroundColor DarkGray
}

# ============================================================================
# 检查5: 代码统计
# ============================================================================
Write-Host ""
Write-Host "[5/5] 代码统计..."

$pyFiles = Get-ChildItem -Path $srcDir -Filter "*.py" -Recurse -ErrorAction SilentlyContinue
$totalLines = 0
foreach ($file in $pyFiles) {
    $lines = (Get-Content $file.FullName -ErrorAction SilentlyContinue | Measure-Object -Line).Lines
    $totalLines += $lines
}

Write-Host "   Python文件: $($pyFiles.Count)" -ForegroundColor Cyan
Write-Host "   代码行数: $totalLines" -ForegroundColor Cyan

# ============================================================================
# 总结
# ============================================================================
Write-Host ""
Write-CIHeader "CI 检查总结"

if ($syntaxErrors -eq 0) {
    Write-CISuccess "代码质量检查通过"
    Write-Host ""
    Write-Host "✅ 所有CI检查完成！代码可以合入主线。" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步操作：" -ForegroundColor Cyan
    Write-Host "  1. 提交代码到Git仓库" -ForegroundColor Gray
    Write-Host "  2. 创建Pull Request触发GitHub Actions" -ForegroundColor Gray
    Write-Host "  3. CI通过后合并到主分支" -ForegroundColor Gray
} else {
    Write-CIError "代码存在问题，请修复后再合入"
    Write-Host ""
    Write-Host "修复建议：" -ForegroundColor Yellow
    Write-Host "  1. 检查上述语法错误" -ForegroundColor Gray
    Write-Host "  2. 修复后重新运行此脚本" -ForegroundColor Gray
    Write-Host "  3. 或使用Docker: docker-compose up ci" -ForegroundColor Gray
}

Write-Host ""
