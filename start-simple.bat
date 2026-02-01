@echo off
REM D Plus Skin Bot - Simple Startup
echo ========================================
echo Starting D Plus Skin Bot
echo ========================================
echo.
echo Make sure to run in TWO separate terminals:
echo.
echo Terminal 1 (This one):
echo   uvicorn main:app --reload --host 0.0.0.0 --port 8000
echo.
echo Terminal 2:
echo   cloudflared tunnel run --token eyJhIjoiOTZlZmZhNGVkZTUzZmU4ODcyNzUzNTA4Y2Q0OTc4ZmYiLCJ0IjoiYWZkYTE4NDktZjVlNS00MmZlLTlhZjctMWJkYTNlMGViYjRkIiwicyI6Ik9EZG1NRE01TUdNdE5tRTRZUzAwWmpVNExUbGhPVEl0TURrNU1UYzBNR0ZqWm1ZMSJ9
echo.
echo Starting bot now...
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000
