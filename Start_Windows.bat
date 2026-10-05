@echo off
title ThumbDrive Audio Player
cd /d "%~dp0"

if exist "server_bin\server_win.exe" (
    start "" "server_bin\server_win.exe"
) else if exist "thumbdrive_runner.py" (
    echo [ThumbDrive] Executable server_bin\server_win.exe not found.
    echo [ThumbDrive] Launching python thumbdrive_runner.py fallback...
    python thumbdrive_runner.py
) else (
    echo.
    echo ===================================================================
    echo ERROR: 'server_bin\server_win.exe' was not found!
    echo ===================================================================
    echo Please ensure you have downloaded the compiled executables into
    echo server_bin\ or assembled the drive using package_thumbdrive.py.
    echo.
    pause
)
