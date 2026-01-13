@echo off
REM Build script for creating Glowpoint distribution
REM This creates a standalone executable that doesn't require Python

echo ======================================
echo Building Glowpoint Distribution
echo ======================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    echo Please install Python 3.7 or higher from python.org
    pause
    exit /b 1
)

echo Step 1: Installing/Updating build dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Step 2: Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

echo.
echo Step 3: Building executable with PyInstaller...
echo This may take a few minutes...
pyinstaller glowpoint.spec --clean
if errorlevel 1 (
    echo Error: Build failed
    pause
    exit /b 1
)

echo.
echo Step 4: Creating distribution folder...
if not exist "Glowpoint_Portable" mkdir Glowpoint_Portable
copy dist\Glowpoint.exe Glowpoint_Portable\
copy LICENSE Glowpoint_Portable\
echo Creating distribution README...

REM Create a simple README for the distribution
(
echo Glowpoint - Portable Version
echo ============================
echo.
echo This is a standalone version of Glowpoint that does not require Python.
echo.
echo INSTALLATION:
echo -------------
echo 1. Simply double-click Glowpoint.exe to run
echo 2. The application will start in your system tray
echo 3. Right-click the tray icon for options
echo.
echo USAGE:
echo ------
echo - Toggle Spotlight: Ctrl+Shift+S
echo - Draw Blue: Ctrl+Shift+B
echo - Draw Red: Ctrl+Shift+R
echo - Draw Yellow: Ctrl+Shift+Y
echo - Draw Green: Ctrl+Shift+G
echo - Clear Drawings: Ctrl+Shift+C
echo - Quit: Ctrl+Shift+Q
echo.
echo You can customize all shortcuts in Settings ^(right-click tray icon^).
echo.
echo DISTRIBUTION:
echo -------------
echo This folder can be copied to any Windows computer and will run without
echo needing to install Python or any dependencies.
echo.
echo For more information, see: https://github.com/archiflux/Glowpoint
) > Glowpoint_Portable\README.txt

echo.
echo ======================================
echo Build Complete!
echo ======================================
echo.
echo Distribution created in: Glowpoint_Portable\
echo.
echo You can now copy the Glowpoint_Portable folder to any Windows computer
echo and run Glowpoint.exe without needing Python installed.
echo.
echo File: Glowpoint_Portable\Glowpoint.exe
echo.
pause
