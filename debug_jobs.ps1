# Debug: Check job object structure
$headers = @{
    'Accept' = 'application/vnd.github.v3+json'
    'User-Agent' = 'CI-Debug-Tool'
}

$runId = "27589018662"
$jobsUrl = "https://api.github.com/repos/Gyworker/Gitwork/actions/runs/$runId/jobs"

$jobs = Invoke-RestMethod -Uri $jobsUrl -Headers $headers -Method Get -TimeoutSec 30

$firstJob = $jobs.jobs[0]
Write-Host "First Job Properties:" -ForegroundColor Yellow
$firstJob | Get-Member -MemberType Properties | ForEach-Object { Write-Host "  $($_.Name): $($firstJob.$($_.Name))" }

Write-Host ""
Write-Host "Looking for log URL..." -ForegroundColor Yellow
Write-Host "  logs_url: $($firstJob.logs_url)"
Write-Host "  html_url: $($firstJob.html_url)"
