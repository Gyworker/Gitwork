# 强制重新触发CI - 通过空白提交
# 用法: .\rebuild_ci.ps1

$gitCmd = "D:\Program Files\Git\cmd\git.exe"
$workDir = "D:\GITwork"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  强制重新触发CI" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $workDir

# 记录当前状态
Write-Host "[1/4] 检查Git状态..." -ForegroundColor White
$status = & $gitCmd status --short
if ($status) {
    Write-Host "   有未提交的更改:" -ForegroundColor Yellow
    Write-Host $status
    Write-Host ""
    $choice = Read-Host "是否stash更改并继续? (y/n)"
    if ($choice -eq "y") {
        & $gitCmd stash push -m "Temp stash $(Get-Date -Format 'yyyyMMdd-HHmmss')"
    } else {
        Write-Host "取消操作" -ForegroundColor Red
        exit 1
    }
}

# 创建空白提交
Write-Host "[2/4] 创建空白提交..." -ForegroundColor White
& $gitCmd config user.name "CI-Rebuild" 2>$null
& $gitCmd config user.email "ci@rebuild.local" 2>$null
$commitMsg = "Rebuild CI $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
& $gitCmd commit --allow-empty -m $commitMsg

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 提交失败" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ 空白提交已创建" -ForegroundColor Green

# 推送到远程
Write-Host "[3/4] 推送到GitHub..." -ForegroundColor White
& $gitCmd push origin main

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 推送失败" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ 已推送" -ForegroundColor Green

# 显示结果链接
Write-Host ""
Write-Host "[4/4] CI已触发!" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  等待CI运行（约1分钟）..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "查看进度: https://github.com/Gyworker/Gitwork/actions" -ForegroundColor Cyan
Write-Host ""

# 等待一段时间后检查结果
Start-Sleep -Seconds 45

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  检查CI结果..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 调用检查脚本
$checkScript = Join-Path $PSScriptRoot "check_ci.ps1"
& $checkScript -Owner Gyworker -Repo Gitwork -MaxRuns 1
