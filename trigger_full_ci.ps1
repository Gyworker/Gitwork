$headers = @{
    'Accept' = 'application/vnd.github.v3+json'
    'Content-Type' = 'application/json'
    'User-Agent' = 'CI-Trigger'
}

$body = @{
    ref = 'main'
    inputs = @{
        check_type = 'full'
    }
} | ConvertTo-Json

$url = 'https://api.github.com/repos/Gyworker/Gitwork/actions/workflows/ci.yml/dispatches'

Write-Host "Triggering CI with FULL check..." -ForegroundColor Cyan
try {
    Invoke-RestMethod -Uri $url -Headers $headers -Method Post -Body $body -TimeoutSec 30
    Write-Host "SUCCESS: CI triggered!" -ForegroundColor Green
    Write-Host ""
    Write-Host "View progress: https://github.com/Gyworker/Gitwork/actions" -ForegroundColor Yellow
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    
    if ($_.Exception.Response.StatusCode -eq 403) {
        Write-Host ""
        Write-Host "Tip: Please open GitHub page and trigger manually:" -ForegroundColor Yellow
        Write-Host "https://github.com/Gyworker/Gitwork/actions" -ForegroundColor Cyan
    }
}
