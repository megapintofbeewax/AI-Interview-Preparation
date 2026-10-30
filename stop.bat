@echo off
title Stopping Prep AI Platform...
echo ========================================================
echo       PREP AI - Stopping Local Host Servers
echo ========================================================
echo.

echo [1/2] Terminating backend processes on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [2/2] Terminating frontend dev processes on port 5173...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo ========================================================
echo   Both Frontend and Backend servers have been stopped!
echo   Ports 5173 and 8000 are freed.
echo ========================================================
ping 127.0.0.1 -n 3 >nul
