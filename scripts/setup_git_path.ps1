# -*- coding: utf-8 -*-
# Git PATH配置脚本
# 功能：检测Git安装位置并添加到PATH

$ErrorActionPreference = "Stop"

Write-Host "=== Git PATH 配置脚本 ===" -ForegroundColor Cyan
Write-Host ""

# 1. 检测Git安装位置
$gitPaths = @(
    "C:\Program Files\Git\cmd",
    "C:\Program Files (x86)\Git\cmd",
    "C:\Git\cmd",
    "$env:LOCALAPPDATA\Programs\Git\cmd"
)

$gitExe = $null
foreach ($path in $gitPaths) {
    $testPath = Join-Path $path "git.exe"
    if (Test-Path $testPath) {
        $gitExe = $testPath
        $gitBin = Split-Path $path
        Write-Host "✅ 找到Git: $gitExe" -ForegroundColor Green
        break
    }
}

if (-not $gitExe) {
    Write-Host "❌ 未找到Git安装位置" -ForegroundColor Red
    Write-Host ""
    Write-Host "请确保Git已正确安装：" -ForegroundColor Yellow
    Write-Host "1. 访问 https://git-scm.com/download/win"
    Write-Host "2. 下载并运行安装程序"
    Write-Host "3. 安装时勾选 'Add Git to PATH'"
    Write-Host ""
    Write-Host "或者手动将以下路径添加到系统PATH：" -ForegroundColor Yellow
    Write-Host "C:\Program Files\Git\cmd"
    exit 1
}

# 2. 获取Git版本
$gitVersion = & $gitExe --version 2>&1
Write-Host "Git版本: $gitVersion" -ForegroundColor Green

# 3. 检查PATH中是否已包含Git
$currentPath = $env:Path
$gitInPath = $currentPath -split ';' | Where-Object { $_ -like "*Git*" }

if ($gitInPath) {
    Write-Host ""
    Write-Host "⚠️  Git已在PATH中: $gitInPath" -ForegroundColor Yellow
    Write-Host "如果仍无法使用git命令，请重启终端或IDE" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "❌ Git不在PATH中，正在添加到PATH..." -ForegroundColor Yellow
    
    # 添加到用户PATH（永久）
    $newPath = "$path;$currentPath"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    
    # 添加到当前会话
    $env:Path = $newPath
    
    Write-Host "✅ 已添加到PATH: $path" -ForegroundColor Green
    Write-Host ""
    Write-Host "请重启PowerShell/IDE以使配置生效" -ForegroundColor Yellow
}

# 4. 验证Git
Write-Host ""
Write-Host "=== 验证Git配置 ===" -ForegroundColor Cyan

# 重新加载环境变量
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

try {
    $result = git --version 2>&1
    Write-Host "✅ Git可用: $result" -ForegroundColor Green
    exit 0
} catch {
    Write-Host "❌ Git仍不可用，请手动重启终端后重试" -ForegroundColor Red
    Write-Host ""
    Write-Host "请重启PowerShell或IDE后，再次运行本脚本验证" -ForegroundColor Yellow
    exit 1
}
