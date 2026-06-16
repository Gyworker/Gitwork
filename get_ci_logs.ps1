# Get CI Job Logs using job URL
$headers = @{
    'Accept' = 'application/vnd.github.v3+json'
    'User-Agent' = 'CI-Log-Tool'
}

$runId = "27589018662"

# Get all jobs for this run
$jobsUrl = "https://api.github.com/repos/Gyworker/Gitwork/actions/runs/$runId/jobs"
$jobs = Invoke-RestMethod -Uri $jobsUrl -Headers $headers -Method Get -TimeoutSec 30

foreach ($job in $jobs.jobs) {
    if ($job.conclusion -eq "failure") {
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "Job: $($job.name)" -ForegroundColor Yellow
        Write-Host "========================================" -ForegroundColor Red
        
        # Get job details from job URL
        $jobDetail = Invoke-RestMethod -Uri $job.url -Headers $headers -Method Get -TimeoutSec 60
        
        # Check if logs_text is available
        if ($jobDetail.logs) {
            $logContent = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($jobDetail.logs))
            $lines = $logContent -split "`n"
            
            # Find error lines
            $errorLines = $lines | Where-Object { $_ -match "error|Error|ERROR|failed|Failed|FAILED|Exception|permission|denied|E: " }
            
            if ($errorLines) {
                Write-Host ""
                Write-Host "Error Output:" -ForegroundColor Red
                foreach ($line in $errorLines | Select-Object -First 30) {
                    Write-Host $line -ForegroundColor White
                }
            } else {
                # Show last 50 lines
                Write-Host ""
                Write-Host "Last 50 lines of log:" -ForegroundColor Gray
                foreach ($line in $lines | Select-Object -Last 50) {
                    Write-Host $line -ForegroundColor Gray
                }
            }
        } else {
            Write-Host "Logs not available via API. Check:" -ForegroundColor Yellow
            Write-Host "  $($job.html_url)" -ForegroundColor Cyan
        }
        
        Write-Host ""
    }
}
