@echo off
REM =============================================
REM D Plus Skin Bot - Persistent Tunnel Startup
REM =============================================
echo.
echo ========================================
echo   D Plus Skin Facebook Bot
echo   Persistent Tunnel: nong-d.trycloudflare.com
echo ========================================
echo.
echo This will start:
echo   [1] Cloudflare Tunnel (persistent)
echo   [2] Facebook Bot
echo.
echo Your webhook URL:
echo   https://nong-d.trycloudflare.com/webhook
echo.
echo ========================================
echo.

echo [1/2] Starting Cloudflare Tunnel (Quick Tunnel)...
start "Cloudflare Tunnel" cmd /k "cloudflared tunnel --url http://localhost:8000"

timeout /t 5 /nobreak >nul

echo [2/2] Starting Facebook Bot...
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000
