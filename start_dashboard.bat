@echo off
echo ===================================================
echo   Starting NongD Dashboard System
echo ===================================================

:: Check for .venv
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Found .venv, using it...
    set "ACTIVATE_CMD=call .venv\Scripts\activate.bat"
) else (
    echo [WARN] .venv not found, assuming global python...
    set "ACTIVATE_CMD=echo Using global environment..."
)

:: 1. Start API Server
echo [1/3] Starting API Server (uvicorn)...
start "NongD API Server" cmd /k "colors 0A && %ACTIVATE_CMD% && echo API SERVER RUNNING... && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

:: 2. Start Comment Monitor
echo [2/3] Starting Comment Monitor Service...
start "Comment Monitor Bot" cmd /k "colors 0B && %ACTIVATE_CMD% && echo COMMENT MONITOR RUNNING... && python scripts/monitor_24_7.py"

:: 3. Launch Dashboard
echo [3/3] Launching Dashboard in Browser...
timeout /t 3 >nul
start http://localhost:8000/dashboard

echo.
echo ===================================================
echo   System is running!
echo   - API: http://localhost:8000
echo   - Dashboard: http://localhost:8000/dashboard
echo.
echo   To stop, close the opened command windows.
echo ===================================================
pause
