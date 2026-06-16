# ============================================================
# GitHub CI 交互式检查工具
# ============================================================
# 功能：
#   1. 查看当前CI状态
#   2. 手动触发CI（通过浏览器）
#   3. 等待并检查结果
# ============================================================

param(
    [string]$Owner = "Gyworker",
    [string]$Repo = "Gitwork"
)

$headers = @{
    'Accept' = 'application/vnd.github.v3+json'
    'User-Agent' = 'CI-Check-Tool'
}

# 颜色定义
function Write-Step { param($msg) Write-Host "[步骤] $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "[成功] $msg" -ForegroundColor Green }
function Write-Error { param($msg) Write-Host "[错误] $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "[信息] $msg" -ForegroundColor Yellow }

Clear-Host

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║          GitHub CI 交互式检查工具                         ║" -ForegroundColor Magenta
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""

# 获取最新CI状态
Write-Step "正在获取CI状态..."

try {
    $runsUrl = "https://api.github.com/repos/$Owner/$Repo/actions/runs?per_page=5"
    $runs = Invoke-RestMethod -Uri $runsUrl -Headers $headers -Method Get -TimeoutSec 15
    
    if ($runs.workflow_runs.Count -eq 0) {
        Write-Info "暂无CI运行记录"
    } else {
        Write-Host ""
        Write-Host "最近 5 次 CI 运行:" -ForegroundColor White
        Write-Host "-" * 60
        
        $runs.workflow_runs | ForEach-Object {
            $status = if ($_.conclusion -eq "success") { "[✓ 通过]" } elseif ($_.conclusion -eq "failure") { "[✗ 失败]" } else { "[运行中]" }
            $color = if ($_.conclusion -eq "success") { "Green" } elseif ($_.conclusion -eq "failure") { "Red" } else { "Yellow" }
            $time = [DateTime]::Parse($_.created_at).ToString("yyyy-MM-dd HH:mm")
            
            Write-Host "$status  $($_.name)" -ForegroundColor $color
            Write-Host "    分支: $($_.head_branch)  |  时间: $time  |  触发: $($_.triggering_actor.login)" -ForegroundColor Gray
            Write-Host ""
        }
    }
} catch {
    Write-Error "获取CI状态失败: $_"
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Magenta
Write-Host ""
Write-Host "请选择操作:" -ForegroundColor White
Write-Host ""
Write-Host "  [1] 触发手动CI (打开GitHub页面)" -ForegroundColor Cyan
Write-Host "  [2] 刷新CI状态" -ForegroundColor Cyan
Write-Host "  [3] 等待最新CI完成并显示结果" -ForegroundColor Cyan
Write-Host "  [4] 查看详细Job状态" -ForegroundColor Cyan
Write-Host "  [0] 退出" -ForegroundColor Gray
Write-Host ""

$choice = Read-Host "请输入选项 (0-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Step "正在打开GitHub Actions页面..."
        Start-Process "https://github.com/$Owner/$Repo/actions"
        Write-Host ""
        Write-Info "请在打开的页面中: 点击 'CI' workflow → 点击 'Run workflow' 按钮"
        Write-Host ""
    }
    
    "2" {
        Write-Host ""
        & $PSCommandPath
    }
    
    "3" {
        Write-Step "等待CI完成（约60秒）..."
        Write-Info "期间请在GitHub上手动触发CI..."
        Write-Host ""
        
        for ($i = 60; $i -gt 0; $i -= 10) {
            Write-Host "`r  剩余等待时间: $i 秒...  " -NoNewline -ForegroundColor Yellow
            Start-Sleep -Seconds 10
        }
        Write-Host "`r" -NoNewline
        Write-Host "                                              " -NoNewline
        Write-Host "`r" -NoNewline
        
        Write-Host ""
        Write-Step "检查最新CI结果..."
        Write-Host ""
        
        try {
            $runsUrl = "https://api.github.com/repos/$Owner/$Repo/actions/runs?per_page=1"
            $run = Invoke-RestMethod -Uri $runsUrl -Headers $headers -Method Get -TimeoutSec 15
            
            $latest = $run.workflow_runs[0]
            $status = if ($latest.conclusion -eq "success") { "✅ 通过" } elseif ($latest.conclusion -eq "failure") { "❌ 失败" } else { "🔄 运行中" }
            $time = [DateTime]::Parse($latest.created_at).ToString("yyyy-MM-dd HH:mm:ss")
            
            Write-Host "最新CI状态: $status" -ForegroundColor $(if ($latest.conclusion -eq "success") { "Green" } else { "Red" })
            Write-Host "  时间: $time" -ForegroundColor Gray
            Write-Host "  分支: $($latest.head_branch)" -ForegroundColor Gray
            Write-Host "  链接: $($latest.html_url)" -ForegroundColor Cyan
        } catch {
            Write-Error "检查失败: $_"
        }
    }
    
    "4" {
        Write-Host ""
        Write-Step "正在获取Job详情..."
        
        try {
            $runsUrl = "https://api.github.com/repos/$Owner/$Repo/actions/runs?per_page=1"
            $run = Invoke-RestMethod -Uri $runsUrl -Headers $headers -Method Get -TimeoutSec 15
            $latest = $run.workflow_runs[0]
            
            $jobsUrl = "https://api.github.com/repos/$Owner/$Repo/actions/runs/$($latest.id)/jobs"
            $jobs = Invoke-RestMethod -Uri $jobsUrl -Headers $headers -Method Get -TimeoutSec 15
            
            Write-Host ""
            Write-Host "Jobs 状态:" -ForegroundColor White
            Write-Host "-" * 60
            
            foreach ($job in $jobs.jobs) {
                $status = if ($job.conclusion -eq "success") { "✅" } elseif ($job.conclusion -eq "failure") { "❌" } else { "🔄" }
                $color = if ($job.conclusion -eq "success") { "Green" } elseif ($job.conclusion -eq "failure") { "Red" } else { "Yellow" }
                
                Write-Host "$status $($job.name)" -ForegroundColor $color
                
                if ($job.conclusion -eq "failure") {
                    Write-Host "  Steps:" -ForegroundColor Gray
                    foreach ($step in $job.steps) {
                        $icon = if ($step.conclusion -eq "success") { "  [✓]" } elseif ($step.conclusion -eq "failure") { "  [✗]" } else { "  [ ]" }
                        $scolor = if ($step.conclusion -eq "success") { "Green" } elseif ($step.conclusion -eq "failure") { "Red" } else { "Gray" }
                        Write-Host "$icon $($step.name)" -ForegroundColor $scolor
                    }
                }
                Write-Host ""
            }
        } catch {
            Write-Error "获取详情失败: $_"
        }
    }
    
    "0" {
        Write-Host ""
        Write-Host "再见!" -ForegroundColor Green
        exit 0
    }
    
    default {
        Write-Host ""
        Write-Error "无效选项"
    }
}

Write-Host ""
