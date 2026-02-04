@echo off
REM =============================================
REM D Plus Skin Bot - 24/7 Monitor Startup
REM =============================================
title D Plus Skin 24/7 Monitor
echo.
echo ========================================
echo   D Plus Skin Facebook AI Monitor
echo   Status: Active Polling
echo ========================================
echo.
echo This will start the polling service that:
echo   [1] Checks for unreplied comments
echo   [2] Automatically responds with AI
echo   [3] Retries every 5 minutes
echo.
echo Log file: logs/monitor.log
echo.
echo ========================================
echo.

:loop
echo [%DATE% %TIME%] Starting monitor...
python scripts/monitor_24_7.py
echo [%DATE% %TIME%] Monitor stopped or crashed. Restarting in 10 seconds...
timeout /t 10
goto loop
