@echo off
@chcp 65001 >nul
title Pexels Video Downloader

REM Pexels Video Downloader Launcher
REM Automatically sets up the project Python environment and starts the application

echo ================================
echo Pexels 4K Video Downloader - Enhanced Version
echo ================================
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Set environment variables to use the project's Python
set PYTHONPATH=%CD%\python
set PATH=%CD%\python;%CD%\python\Scripts;%PATH%

echo Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python environment not found
    echo Please ensure python.exe is in the project directory
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo Checking and installing dependencies...
python -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo Warning: Dependency installation may have failed, attempting to continue...
    echo.
)

REM Create downloads directory if it doesn't exist
if not exist downloads mkdir downloads

echo.
echo Starting Pexels Video Downloader...
echo ================================
echo.

REM Run the main application
python enhanced_pexels_downloader.py

echo.
echo Program has exited.
echo.
echo Press any key to exit...
pause >nul
