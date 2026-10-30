# Prep AI Platform Launcher (PowerShell)
$projectRoot = $PSScriptRoot

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "      PREP AI - AI INTERVIEW PREPARATION PLATFORM       " -ForegroundColor Yellow
Write-Host "            Starting Local Host Servers                 " -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Start Backend Server
Write-Host "[1/3] Starting FastAPI Backend on port 8000..." -ForegroundColor Gray
Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d `"$projectRoot`" && venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload" -WindowStyle Normal

# 2. Start Frontend Server
Write-Host "[2/3] Starting Vite Frontend on port 5173..." -ForegroundColor Gray
Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d `"$projectRoot\frontend`" && npm run dev" -WindowStyle Normal

# 3. Open Browser
Write-Host "[3/3] Opening browser at http://localhost:5173..." -ForegroundColor Gray
Start-Sleep -Seconds 3
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  Servers are running!" -ForegroundColor Green
Write-Host "  * Frontend : http://localhost:5173" -ForegroundColor White
Write-Host "  * Backend  : http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  * Docs     : http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Green
