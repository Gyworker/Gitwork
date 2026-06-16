# GitHub CI Check Tool
# Usage: .\check_ci.ps1 -Owner Gyworker -Repo Gitwork

param(
    [string]$Owner = "Gyworker",
    [string]$Repo = "Gitwork",
    [int]$MaxRuns = 5
)

$ErrorActionPreference = "Continue"

# Colors
$GRAY = "DarkGray"
$CYAN = "Cyan"
$RED = "Red"
$GREEN = "Green"
$YELLOW = "Yellow"
$WHITE = "White"

function Write-Header {
    param($Text)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor $CYAN
    Write-Host " $Text" -ForegroundColor $CYAN
    Write-Host "========================================" -ForegroundColor $CYAN
}

function Get-StatusText {
    param($Status, $Conclusion)
    if ($Conclusion -eq "success") {
        return "[PASS]"
    } elseif ($Conclusion -eq "failure") {
        return "[FAIL]"
    } elseif ($Conclusion -eq "cancelled") {
        return "[CANC]"
    } elseif ($Status -eq "in_progress") {
        return "[RUN]"
    } elseif ($Status -eq "queued") {
        return "[WAIT]"
    } else {
        return "[???] $Conclusion"
    }
}

# Main Program
Write-Header "GitHub CI Check Tool"
Write-Host "Repository: $Owner/$Repo" -ForegroundColor $YELLOW
Write-Host ""

# Build API URL
$apiUrl = "https://api.github.com/repos/$Owner/$Repo/actions/runs?per_page=$MaxRuns"

$headers = @{
    "Accept" = "application/vnd.github.v3+json"
    "User-Agent" = "CI-Check-Tool"
}

try {
    $results = Invoke-RestMethod -Uri $apiUrl -Headers $headers -Method Get -TimeoutSec 30
} catch {
    Write-Host "ERROR: Failed to get CI results: $_" -ForegroundColor $RED
    exit 1
}

$workflow_runs = $results.workflow_runs

if ($workflow_runs.Count -eq 0) {
    Write-Host "No CI runs found." -ForegroundColor $YELLOW
    exit 0
}

# Display latest runs
Write-Header "Latest $MaxRuns CI Runs"

foreach ($run in $workflow_runs) {
    $status = Get-StatusText -Status $run.status -Conclusion $run.conclusion
    $time = Get-Date $run.created_at -Format "yyyy-MM-dd HH:mm:ss"
    
    Write-Host ""
    Write-Host "----------------------------------------" -ForegroundColor $GRAY
    Write-Host "Trigger: $($run.event)" -ForegroundColor $GRAY
    Write-Host "Branch: $($run.head_branch)" -ForegroundColor $GRAY
    Write-Host "Time: $time" -ForegroundColor $GRAY
    
    if ($run.conclusion -eq "success") {
        Write-Host "Status: $status" -ForegroundColor $GREEN
    } elseif ($run.conclusion -eq "failure") {
        Write-Host "Status: $status" -ForegroundColor $RED
        Write-Host "URL: $($run.html_url)" -ForegroundColor $CYAN
        
        # Get failed job details
        $jobsUrl = "https://api.github.com/repos/$Owner/$Repo/actions/runs/$($run.id)/jobs"
        try {
            $jobs = Invoke-RestMethod -Uri $jobsUrl -Headers $headers -Method Get -TimeoutSec 30
            $failedJobs = $jobs.jobs | Where-Object { $_.conclusion -eq "failure" }
            
            if ($failedJobs) {
                Write-Host ""
                Write-Host "  Failed Jobs:" -ForegroundColor $RED
                foreach ($job in $failedJobs) {
                    Write-Host "    - $($job.name)" -ForegroundColor $RED
                }
            }
        } catch {
            # Ignore job details error
        }
    } elseif ($run.status -eq "in_progress") {
        Write-Host "Status: $status" -ForegroundColor $YELLOW
    } else {
        Write-Host "Status: $status" -ForegroundColor $GRAY
    }
}

# Summary
Write-Host ""
Write-Header "Summary"

$successCount = ($workflow_runs | Where-Object { $_.conclusion -eq "success" }).Count
$failureCount = ($workflow_runs | Where-Object { $_.conclusion -eq "failure" }).Count
$runningCount = ($workflow_runs | Where-Object { $_.status -eq "in_progress" }).Count

Write-Host "Last $MaxRuns runs:" -ForegroundColor $WHITE
Write-Host "  [PASS] Success: $successCount" -ForegroundColor $GREEN
Write-Host "  [FAIL] Failed: $failureCount" -ForegroundColor $RED
Write-Host "  [RUN]  Running: $runningCount" -ForegroundColor $YELLOW

$latest = $workflow_runs[0]
if ($latest.conclusion -eq "success") {
    Write-Host ""
    Write-Host "Latest CI: ALL PASSED!" -ForegroundColor $GREEN
} elseif ($latest.conclusion -eq "failure") {
    Write-Host ""
    Write-Host "Latest CI: HAS FAILURES!" -ForegroundColor $RED
} else {
    Write-Host ""
    Write-Host "Latest CI: Still running..." -ForegroundColor $YELLOW
}

Write-Host ""
Write-Host "View Details: https://github.com/$Owner/$Repo/actions" -ForegroundColor $CYAN
