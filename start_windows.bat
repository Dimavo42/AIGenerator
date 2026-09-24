@echo off
cd /d "%~dp0"

echo ============================
echo AIGenerator Windows Launcher
echo ============================

echo Checking for Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed.
    echo Installing Python...
    winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo Failed to install Python.
        pause
        exit /b 1
    )
    echo Python installed successfully.
    echo Please close this window and run start_windows.bat again.
    pause
    exit /b 0
)
echo Python is installed.

python setup.py
if errorlevel 1 (
    echo.
    echo Setup failed.
    pause
    exit /b 1
)
