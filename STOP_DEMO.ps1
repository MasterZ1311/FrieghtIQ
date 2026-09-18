# FreightIQ — Stop All Demo Processes
# Run this to cleanly shut down the offline demo

Write-Host "Stopping FreightIQ demo processes..." -ForegroundColor Yellow

# Kill uvicorn (backend)
Get-Process -Name "python" -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  Stopping backend process (PID: $($_.Id))..." -ForegroundColor Gray
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}

# Kill node (frontend)
Get-Process -Name "node" -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  Stopping frontend process (PID: $($_.Id))..." -ForegroundColor Gray
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 2
Write-Host "FreightIQ demo stopped." -ForegroundColor Red
