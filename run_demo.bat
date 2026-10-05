@echo off
title AurumLens Prototype Showcase Runner
echo ============================================================
echo   AurumLens - Relative-Value Intelligence & Hedge Analytics
echo   Offline Hackathon Prototype Showcase Launcher
echo ============================================================
echo.

cd /d "%~dp0"

echo [*] Starting FastAPI Python engine backend on http://localhost:8000 ...
start "AurumLens FastAPI Engine" cmd /k "set PYTHONPATH=engine\src&& python -m uvicorn aurumlens.api.main:app --port 8000 --reload"

echo [*] Waiting 3 seconds for backend initialization...
timeout /t 3 /nobreak >nul

echo [*] Starting Next.js frontend on http://localhost:3000 ...
start "AurumLens Next.js UI" cmd /k "cd web && npm run dev"

echo [*] Waiting 4 seconds for frontend initialization...
timeout /t 4 /nobreak >nul

echo [*] Opening prototype in browser...
start http://localhost:3000

echo.
echo ============================================================
echo [✓] AurumLens Prototype Showcase is running!
echo     - Frontend: http://localhost:3000
echo     - Backend API Docs: http://localhost:8000/docs
echo     - Demo Runbook: docs\DEMO_RUNBOOK.md
echo ============================================================
echo.
pause
