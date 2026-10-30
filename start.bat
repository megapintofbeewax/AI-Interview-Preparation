@echo off
title Prep AI Platform Launcher
echo ========================================================
echo       PREP AI - AI INTERVIEW PREPARATION PLATFORM
echo             Starting Local Host Servers
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/3] Starting FastAPI Backend (http://127.0.0.1:8000)...
start "Prep AI - Backend" cmd /k "cd /d "%~dp0" && venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload"

echo [2/3] Starting Vite Frontend (http://localhost:5173)...
start "Prep AI - Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo [3/3] Opening browser in 3 seconds...
ping 127.0.0.1 -n 4 >nul
start http://localhost:5173

echo.
echo ========================================================
echo   All servers are running!
echo   * Frontend Web App : http://localhost:5173
echo   * Backend API      : http://127.0.0.1:8000
echo   * API Docs/Swagger : http://127.0.0.1:8000/docs
echo.
echo   To stop all servers at any time, run stop.bat
echo ========================================================
ping 127.0.0.1 -n 3 >nul
