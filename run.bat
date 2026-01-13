@echo off
REM Launcher script for Glowpoint (Windows)
REM Supports both standalone executable and Python script modes

REM First, check if standalone executable exists
if exist "dist\Glowpoint.exe" (
    echo Running Glowpoint from standalone executable...
    start "" "dist\Glowpoint.exe"
    exit /b 0
)

if exist "Glowpoint_Portable\Glowpoint.exe" (
    echo Running Glowpoint from portable distribution...
    start "" "Glowpoint_Portable\Glowpoint.exe"
    exit /b 0
)

if exist "Glowpoint.exe" (
    echo Running Glowpoint standalone executable...
    start "" "Glowpoint.exe"
    exit /b 0
)

REM No executable found, try Python mode
echo No standalone executable found, attempting to run with Python...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed and no standalone executable was found
    echo.
    echo To run Glowpoint, you can either:
    echo   1. Install Python 3.7+ from python.org and run this script again
    echo   2. Get the portable version (Glowpoint.exe) from a colleague
    echo   3. Build the portable version yourself by running: build_dist.bat
    echo.
    pause
    exit /b 1
)

REM Check if required packages are installed
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo Installing required dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Run Glowpoint with Python
echo Running Glowpoint with Python...
python glowpoint.py
