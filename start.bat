@echo off
REM D Plus Skin Bot - Startup Script
echo ========================================
echo Starting D Plus Skin Facebook Bot
echo ========================================
echo.

echo [1/2] Starting Cloudflare Tunnel...
start "Cloudflare Tunnel" cmd /k "cloudflared tunnel --url http://localhost:8000"

timeout /t 5 /nobreak >nul

echo [2/2] Starting the bot...
echo.
echo Your tunnel URL will appear in the other window.
echo Use that URL + /webhook for Facebook webhook.
echo.
uvicorn main:app --reload --host 0.0.0.0 --port 8000
