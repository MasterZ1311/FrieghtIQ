# FreightIQ — Offline Demo Startup Script
# Run this on demo day if internet is unavailable
# Requires: Python venv set up in backend/, Node.js installed
# Usage: Right-click -> Run with PowerShell (or: powershell -File START_OFFLINE_DEMO.ps1)

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "   FreightIQ OFFLINE DEMO — SIH26006" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
$pythonOk = (Get-Command python -ErrorAction SilentlyContinue) -ne $null
$nodeOk = (Get-Command node -ErrorAction SilentlyContinue) -ne $null
$venvOk = Test-Path "e:\SIH21006\backend\venv\Scripts\activate.ps1"
$dbOk = Test-Path "e:\SIH21006\backend\freightiq.db"

if (-not $pythonOk) { Write-Host "ERROR: Python not found. Install Python 3.11+." -ForegroundColor Red; exit 1 }
if (-not $nodeOk)   { Write-Host "ERROR: Node.js not found. Install Node.js 20+." -ForegroundColor Red; exit 1 }
if (-not $venvOk)   { Write-Host "ERROR: Python venv not found. Run: cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt" -ForegroundColor Red; exit 1 }
if (-not $dbOk)     { Write-Host "WARNING: Database not found. Backend will seed on startup..." -ForegroundColor Yellow }

Write-Host "[1/3] Starting FreightIQ Backend (FastAPI on port 8000)..." -ForegroundColor Yellow

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location e:\SIH21006\backend; .\venv\Scripts\Activate.ps1; Write-Host 'Backend starting...' -ForegroundColor Green; uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"
) -WindowStyle Normal

Write-Host "   Waiting for backend to initialize (12 seconds)..." -ForegroundColor Gray
Start-Sleep -Seconds 12

# Health check
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
    Write-Host "   Backend: ONLINE (status OK)" -ForegroundColor Green
} catch {
    Write-Host "   Backend: Still starting... (this is normal, continue)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[2/3] Starting FreightIQ Frontend (Next.js on port 3000)..." -ForegroundColor Yellow

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location e:\SIH21006\frontend; Write-Host 'Frontend starting...' -ForegroundColor Green; npm run dev"
) -WindowStyle Normal

Write-Host "   Waiting for frontend to compile (15 seconds)..." -ForegroundColor Gray
Start-Sleep -Seconds 15

Write-Host ""
Write-Host "[3/3] Opening FreightIQ in browser..." -ForegroundColor Yellow
Start-Process "http://localhost:3000"
Start-Sleep -Seconds 2
Start-Process "http://localhost:8000/docs"

Write-Host ""
Write-Host "=================================================" -ForegroundColor Green
Write-Host "   FREIGHTIQ OFFLINE DEMO IS READY" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host "   Frontend Dashboard : http://localhost:3000" -ForegroundColor White
Write-Host "   API Documentation  : http://localhost:8000/docs" -ForegroundColor White
Write-Host "   API Health Check   : http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "   DEMO SCENARIOS TO SHOW JUDGES:" -ForegroundColor Cyan
Write-Host "   1. Dashboard -> Regime Gauge (BEAR/BULL state)" -ForegroundColor White
Write-Host "   2. Ports -> Thoothukudi (VOCPA) -> Green Hub badge" -ForegroundColor White
Write-Host "   3. Copilot -> Ask about Australia-Thoothukudi coal route" -ForegroundColor White
Write-Host "   4. Scenarios -> See all 6 validated P&L scenarios" -ForegroundColor White
Write-Host "   5. Economics -> Carbon CII + EU ETS calculation" -ForegroundColor White
Write-Host ""
Write-Host "   To STOP: Run STOP_DEMO.ps1" -ForegroundColor Gray
Write-Host "=================================================" -ForegroundColor Green
