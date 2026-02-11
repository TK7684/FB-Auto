@echo off
echo ==========================================
echo   CSV Fixer Pro Max - Starting...
echo ==========================================
echo.

:: Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"

:: Start Backend (in its own window, from the correct directory)
start "CSV Fixer Backend" cmd /k "cd /d %SCRIPT_DIR% && python server.py"

:: Wait for backend to start
echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

:: Start Frontend (in its own window, from web subdirectory)
start "CSV Fixer Frontend" cmd /k "cd /d %SCRIPT_DIR%web && npm run dev -- -p 3001"

echo.
echo ==========================================
echo   Dashboard:  http://localhost:3001
echo   Backend:    http://localhost:8001
echo ==========================================
echo.
echo Both servers are starting in separate windows.
echo Close this window when done.
pause
