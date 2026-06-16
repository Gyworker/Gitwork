# Get CI Job Details
$headers = @{
    'Accept' = 'application/vnd.github.v3+json'
    'User-Agent' = 'CI-Detail-Tool'
}

$runId = "27589018662"
$jobsUrl = "https://api.github.com/repos/Gyworker/Gitwork/actions/runs/$runId/jobs"

$jobs = Invoke-RestMethod -Uri $jobsUrl -Headers $headers -Method Get -TimeoutSec 30

foreach ($job in $jobs.jobs) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Job: $($job.name)" -ForegroundColor Yellow
    Write-Host "Status: $($job.conclusion)"
    
    if ($job.conclusion -eq "failure") {
        Write-Host ""
        Write-Host "Steps:" -ForegroundColor Gray
        foreach ($step in $job.steps) {
            if ($step.conclusion -eq "failure") {
                Write-Host "  [FAIL] $($step.name)" -ForegroundColor Red
            } elseif ($step.conclusion -eq "success") {
                Write-Host "  [PASS] $($step.name)" -ForegroundColor Green
            } else {
                Write-Host "  [     ] $($step.name)" -ForegroundColor Gray
            }
        }
    }
    Write-Host ""
}
