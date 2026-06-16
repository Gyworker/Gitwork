$headers = @{
    'Accept' = 'application/vnd.github.v3+json'
    'User-Agent' = 'CI-Check'
}

try {
    # Get latest run
    $runs = Invoke-RestMethod -Uri 'https://api.github.com/repos/Gyworker/Gitwork/actions/runs?per_page=1' -Headers $headers -Method Get -TimeoutSec 15
    $latest = $runs.workflow_runs[0]

    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Latest CI Run" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  ID:     " $latest.id -ForegroundColor White
    Write-Host "  Name:   " $latest.name -ForegroundColor White
    Write-Host "  Status: " $latest.status "/" $latest.conclusion -ForegroundColor $(if ($latest.conclusion -eq "success") { "Green" } else { "Red" })
    Write-Host "  Branch: " $latest.head_branch -ForegroundColor White
    Write-Host "  Time:   " $latest.created_at -ForegroundColor Gray
    Write-Host ""

    # Get jobs
    $jobsUrl = "https://api.github.com/repos/Gyworker/Gitwork/actions/runs/" + $latest.id + "/jobs"
    $jobs = Invoke-RestMethod -Uri $jobsUrl -Headers $headers -Method Get -TimeoutSec 15

    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Jobs" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    foreach ($j in $jobs.jobs) {
        $color = if ($j.conclusion -eq "success") { "Green" } elseif ($j.conclusion -eq "failure") { "Red" } else { "Yellow" }
        Write-Host "  [ $($j.name) ]" -ForegroundColor $color
        Write-Host "    Status: " $j.status " / " $j.conclusion -ForegroundColor Gray

        if ($j.conclusion -eq "failure") {
            Write-Host "    Steps:" -ForegroundColor Red
            foreach ($s in $j.steps) {
                $scolor = if ($s.conclusion -eq "success") { "Green" } elseif ($s.conclusion -eq "failure") { "Red" } else { "Gray" }
                Write-Host "      [ $($s.number) ] $($s.name) = $($s.conclusion)" -ForegroundColor $scolor
            }
        }
        Write-Host ""
    }
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
