# =============================================================================
# Python 环境自动安装脚本 (PowerShell)
# =============================================================================
# 功能：
# 1. 检测当前Python环境
# 2. 下载并安装Python 3.12（轻量级）
# 3. 配置环境变量
# 4. 安装项目依赖
# 5. 运行CI检查
# =============================================================================

param(
    [switch]$SkipCI,
    [string]$PythonVersion = "3.12.0"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "========================================================================" -ForegroundColor Cyan
}

function Write-Success { param([string]$Text); Write-Host "[OK] $Text" -ForegroundColor Green }
function Write-ErrorMsg { param([string]$Text); Write-Host "[FAIL] $Text" -ForegroundColor Red }
function Write-Info { param([string]$Text); Write-Host "[INFO] $Text" -ForegroundColor Yellow }

Write-Header "Python 环境安装脚本"

# ============================================================================
# 第1步：检测Python环境
# ============================================================================
Write-Header "步骤1: 检测Python环境"

$pythonInstalled = $false
$pythonCmd = $null

# 检查常见Python路径
$pythonPaths = @(
    "C:\Python312\python.exe",
    "C:\Python311\python.exe",
    "C:\Python310\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe"
)

foreach ($path in $pythonPaths) {
    if (Test-Path $path) {
        $pythonCmd = $path
        $pythonInstalled = $true
        break
    }
}

# 如果没找到，检查PATH中的Python
if (-not $pythonInstalled) {
    $pyCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pyCmd) {
        $pythonCmd = $pyCmd.Source
        $pythonInstalled = $true
    }
}

if ($pythonInstalled) {
    $version = & $pythonCmd --version 2>&1
    Write-Success "已检测到Python: $version"
    Write-Info "路径: $pythonCmd"
} else {
    Write-Info "未检测到Python，开始安装..."
}

# ============================================================================
# 第2步：下载Python（如果需要）
# ============================================================================
if (-not $pythonInstalled) {
    Write-Header "步骤2: 下载Python $PythonVersion"
    
    $arch = $env:PROCESSOR_ARCHITECTURE
    if ($arch -eq "AMD64") {
        $archSuffix = "amd64"
        $fileSuffix = "-amd64.exe"
    } else {
        $archSuffix = "win32"
        $fileSuffix = ".exe"
    }
    
    # Python 3.12 embeddable下载链接（轻量级，约25MB）
    $downloadUrl = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-embedded.zip"
    $downloadPath = "$env:TEMP\python-embed.zip"
    $installPath = "C:\Python312"
    
    Write-Info "下载Python embeddable包（轻量级版本，约25MB）..."
    Write-Info "URL: $downloadUrl"
    
    try {
        # 使用WebClient下载
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($downloadUrl, $downloadPath)
        Write-Success "下载完成"
        
        Write-Info "解压到: $installPath"
        Expand-Archive -Path $downloadPath -DestinationPath $installPath -Force
        
        # 配置python312._pth文件以支持pip
        $pythPthFile = Join-Path $installPath "python312._pth"
        if (Test-Path $pythPthFile) {
            $content = Get-Content $pythPthFile
            $content = $content -replace "#import site", "import site"
            Set-Content -Path $pythPthFile -Value $content
        }
        
        Write-Success "解压完成"
        
        # 添加到PATH
        $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
        if ($currentPath -notlike "*$installPath*") {
            [Environment]::SetEnvironmentVariable(
                "Path", 
                "$currentPath;$installPath", 
                "User"
            )
            $env:Path = "$env:Path;$installPath"
            Write-Success "已添加到PATH"
        }
        
        $pythonCmd = Join-Path $installPath "python.exe"
        
        # 下载get-pip.py
        $getPipUrl = "https://bootstrap.pypa.io/get-pip.py"
        $getPipPath = "$env:TEMP\get-pip.py"
        $webClient.DownloadFile($getPipUrl, $getPipPath)
        
        Write-Info "安装pip..."
        & $pythonCmd $getPipPath | Out-Null
        Write-Success "pip安装完成"
        
        # 清理临时文件
        Remove-Item $downloadPath -ErrorAction SilentlyContinue
        Remove-Item $getPipPath -ErrorAction SilentlyContinue
        
    } catch {
        Write-ErrorMsg "安装失败: $_"
        Write-Host ""
        Write-Host "手动安装步骤：" -ForegroundColor Yellow
        Write-Host "1. 访问 https://www.python.org/downloads/" -ForegroundColor Gray
        Write-Host "2. 下载Python 3.12 Windows installer (64-bit)" -ForegroundColor Gray
        Write-Host "3. 运行安装程序，勾选 'Add Python to PATH'" -ForegroundColor Gray
        Write-Host "4. 安装完成后重新运行此脚本" -ForegroundColor Gray
        exit 1
    }
}

# ============================================================================
# 第3步：验证Python安装
# ============================================================================
Write-Header "步骤3: 验证Python安装"

$version = & $pythonCmd --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Success "Python版本: $version"
} else {
    Write-ErrorMsg "Python验证失败"
    exit 1
}

# 检查pip
$pipVersion = & $pythonCmd -m pip --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Success "pip版本: $pipVersion"
} else {
    Write-Info "安装pip..."
    $getPipUrl = "https://bootstrap.pypa.io/get-pip.py"
    $getPipPath = "$env:TEMP\get-pip.py"
    (New-Object System.Net.WebClient).DownloadFile($getPipUrl, $getPipPath)
    & $pythonCmd $getPipPath | Out-Null
    Remove-Item $getPipPath -ErrorAction SilentlyContinue
    Write-Success "pip安装完成"
}

# ============================================================================
# 第4步：安装项目依赖
# ============================================================================
Write-Header "步骤4: 安装项目依赖"

Set-Location $ProjectRoot

Write-Info "升级pip..."
& $pythonCmd -m pip install --upgrade pip --quiet 2>&1 | Out-Null
Write-Success "pip升级完成"

Write-Info "安装项目依赖..."
& $pythonCmd -m pip install -r requirements.txt --quiet 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Success "项目依赖安装完成"
} else {
    Write-ErrorMsg "依赖安装失败，请检查requirements.txt"
}

Write-Info "安装开发依赖..."
& $pythonCmd -m pip install pylint pytest pytest-cov --quiet 2>&1
Write-Success "开发依赖安装完成"

# ============================================================================
# 第5步：运行CI检查
# ============================================================================
if (-not $SkipCI) {
    Write-Header "步骤5: 运行CI检查"
    
    Write-Info "运行本地CI脚本..."
    & "$PSScriptRoot\local_ci.ps1"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "CI检查全部通过！"
    } else {
        Write-ErrorMsg "CI检查有失败项"
    }
} else {
    Write-Info "跳过CI检查（使用 -SkipCI 参数）"
}

# ============================================================================
# 完成
# ============================================================================
Write-Header "安装完成！"

Write-Host ""
Write-Host "Python环境已配置完成！" -ForegroundColor Green
Write-Host ""
Write-Host "后续操作：" -ForegroundColor Cyan
Write-Host "  1. 运行CI检查: .\scripts\local_ci.ps1" -ForegroundColor Gray
Write-Host "  2. 运行测试: python -m pytest src/tests/" -ForegroundColor Gray
Write-Host "  3. 代码检查: pylint src/" -ForegroundColor Gray
Write-Host ""
