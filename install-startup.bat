@echo off
set SCRIPT_PATH=%~dp0start-persistent.bat
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SHORTCUT_NAME=D-Plus-Skin-Bot.lnk

echo ========================================
echo   Installing Bot to Windows Startup
echo ========================================
echo.
echo Target Script: %SCRIPT_PATH%
echo Startup Folder: %STARTUP_FOLDER%
echo.

powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%STARTUP_FOLDER%\%SHORTCUT_NAME%');$s.TargetPath='%SCRIPT_PATH%';$s.WorkingDirectory='%~dp0';$s.Save()"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] The bot will now start automatically when you log in to Windows.
    echo.
) else (
    echo.
    echo [ERROR] Failed to create startup shortcut.
    echo.
)

pause
