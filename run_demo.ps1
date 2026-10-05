# AurumLens - PowerShell Prototype Showcase Launcher
$Host.UI.RawUI.WindowTitle = "AurumLens Prototype Showcase Runner"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AurumLens - Relative-Value Intelligence & Hedge Analytics" -ForegroundColor Yellow
Write-Host "  Offline Hackathon Prototype Showcase Launcher" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Start FastAPI Engine in separate window
Write-Host "[*] Starting FastAPI Python engine backend on http://localhost:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootDir'; `$env:PYTHONPATH='engine/src'; python -m uvicorn aurumlens.api.main:app --port 8000 --reload"

Start-Sleep -Seconds 3

# Start Next.js Frontend in separate window
Write-Host "[*] Starting Next.js frontend on http://localhost:3000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootDir/web'; npm run dev"

Start-Sleep -Seconds 4

# Open default browser
Write-Host "[*] Opening prototype in browser at http://localhost:3000 ..." -ForegroundColor Green
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[✓] AurumLens Prototype Showcase is running!" -ForegroundColor Green
Write-Host "    - Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "    - Backend API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "    - Demo Runbook: docs/DEMO_RUNBOOK.md" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
