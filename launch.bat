@echo off
@chcp 65001 >nul
title Pexels Video Downloader

REM Simple launcher for Pexels Video Downloader
REM Automatically sets up environment and starts the application

echo Pexels 4K Video Downloader
echo ==========================

REM Change to the script directory
cd /d "%~dp0"

REM Set environment variables to use the project's Python
set PYTHONPATH=%CD%\python
set PATH=%CD%\python;%CD%\python\Scripts;%PATH%

REM Create downloads directory if it doesn't exist
if not exist downloads mkdir downloads

echo Starting application...
python enhanced_pexels_downloader.py

if %errorlevel% neq 0 (
    echo.
    echo Error running enhanced version, trying simple version...
    python simple_pexels_downloader.py
)

echo.
echo Press any key to exit...
pause >nul