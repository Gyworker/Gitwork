# GitHub CI 触发和检查工具
# 用法：
#   触发CI: .\trigger_ci.ps1 -Owner Gyworker -Repo Gitwork
#   检查结果: .\check_ci.ps1 -Owner Gyworker -Repo Gitwork
param(
    [string]$Owner = "Gyworker",
    [string]$Repo = "Gitwork"
)

$headers = @{
    'Accept' = 'application/vnd.github.v3+json'
    'User-Agent' = 'CI-Trigger-Tool'
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GitHub CI 触发工具" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "仓库: $Owner/$Repo" -ForegroundColor White
Write-Host ""

# 触发 workflow_dispatch
$url = "https://api.github.com/repos/$Owner/$Repo/actions/workflows/ci.yml/runs"
$body = @{
    'ref' = 'main'
} | ConvertTo-Json

Write-Host "正在触发CI..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri $url -Headers $headers -Method Post -Body $body -TimeoutSec 30
    Write-Host "✅ CI已触发!" -ForegroundColor Green
    Write-Host "   Run ID: $($response.id)" -ForegroundColor Gray
    Write-Host "   状态: $($response.status)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "查看结果: https://github.com/$Owner/$Repo/actions" -ForegroundColor Cyan
} catch {
    Write-Host "❌ 触发失败: $_" -ForegroundColor Red
    
    # 如果workflow_dispatch不可用，尝试创建空白提交
    if ($_.Exception.Response.StatusCode -eq 422) {
        Write-Host ""
        Write-Host "尝试创建空白提交..." -ForegroundColor Yellow
        $gitCmd = "$env:PROGRAMFILES\Git\cmd\git.exe"
        
        Set-Location $PSScriptRoot
        & $gitCmd config user.name "CI-Trigger" 2>$null
        & $gitCmd config user.email "ci@trigger.local" 2>$null
        & $gitCmd commit --allow-empty -m "Trigger CI $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" 2>$null
        & $gitCmd push origin main 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 已通过空白提交触发CI!" -ForegroundColor Green
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "等待30秒后自动检查结果..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# 调用 check_ci.ps1
& "$PSScriptRoot\check_ci.ps1" -Owner $Owner -Repo $Repo -MaxRuns 1
