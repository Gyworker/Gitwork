# GitHub CI Interactive Check Tool
param(
    [string]$Owner = "Gyworker",
    [string]$Repo = "Gitwork"
)

$headers = @{
    'Accept' = 'application/vnd.github.v3+json'
    'User-Agent' = 'CI-Check-Tool'
}

Clear-Host

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GitHub CI Interactive Tool" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Repository: $Owner/$Repo" -ForegroundColor White
Write-Host ""

# Get CI status
Write-Host "Getting CI status..." -ForegroundColor Gray
try {
    $runsUrl = "https://api.github.com/repos/$Owner/$Repo/actions/runs?per_page=5"
    $runs = Invoke-RestMethod -Uri $runsUrl -Headers $headers -Method Get -TimeoutSec 15
    
    if ($runs.workflow_runs.Count -eq 0) {
        Write-Host "No CI runs found" -ForegroundColor Yellow
    } else {
        Write-Host ""
        Write-Host "Recent CI Runs:" -ForegroundColor White
        Write-Host "- " * 30
        
        $runs.workflow_runs | ForEach-Object {
            $status = if ($_.conclusion -eq "success") { "[PASS]" } elseif ($_.conclusion -eq "failure") { "[FAIL]" } else { "[RUN]" }
            $color = if ($_.conclusion -eq "success") { "Green" } elseif ($_.conclusion -eq "failure") { "Red" } else { "Yellow" }
            $time = [DateTime]::Parse($_.created_at).ToString("yyyy-MM-dd HH:mm")
            
            Write-Host "$status $($_.name)" -ForegroundColor $color
            Write-Host "    Branch: $($_.head_branch) | Time: $time | By: $($_.triggering_actor.login)" -ForegroundColor Gray
            Write-Host ""
        }
    }
} catch {
    Write-Host "Failed to get CI status: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Options:" -ForegroundColor White
Write-Host ""
Write-Host "  [1] Trigger Manual CI (Open GitHub)" -ForegroundColor Cyan
Write-Host "  [2] Refresh CI status" -ForegroundColor Cyan
Write-Host "  [3] Wait for CI to complete" -ForegroundColor Cyan
Write-Host "  [0] Exit" -ForegroundColor Gray
Write-Host ""

$choice = Read-Host "Enter choice (0-3)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Opening GitHub Actions page..." -ForegroundColor Yellow
        Start-Process "https://github.com/$Owner/$Repo/actions"
        Write-Host ""
        Write-Host "On the page: Click 'CI' workflow -> Click 'Run workflow' button" -ForegroundColor Green
    }
    
    "2" {
        Write-Host ""
        & $PSCommandPath
    }
    
    "3" {
        Write-Host ""
        Write-Host "Waiting for CI (60 seconds)..." -ForegroundColor Yellow
        Write-Host "Please trigger CI on GitHub manually..." -ForegroundColor Gray
        Write-Host ""
        
        for ($i = 60; $i -gt 0; $i -= 10) {
            Write-Host "`r  Waiting: $i sec...  " -NoNewline -ForegroundColor Yellow
            Start-Sleep -Seconds 10
        }
        Write-Host "`r`n"
        
        try {
            $runsUrl = "https://api.github.com/repos/$Owner/$Repo/actions/runs?per_page=1"
            $run = Invoke-RestMethod -Uri $runsUrl -Headers $headers -Method Get -TimeoutSec 15
            
            $latest = $run.workflow_runs[0]
            $status = if ($latest.conclusion -eq "success") { "PASS" } elseif ($latest.conclusion -eq "failure") { "FAIL" } else { "RUNNING" }
            $time = [DateTime]::Parse($latest.created_at).ToString("yyyy-MM-dd HH:mm:ss")
            
            Write-Host ""
            Write-Host "Latest CI: $status" -ForegroundColor $(if ($latest.conclusion -eq "success") { "Green" } else { "Red" })
            Write-Host "  Time: $time" -ForegroundColor Gray
            Write-Host "  Branch: $($latest.head_branch)" -ForegroundColor Gray
        } catch {
            Write-Host "Check failed: $_" -ForegroundColor Red
        }
    }
    
    "0" {
        exit 0
    }
}
Write-Host ""
