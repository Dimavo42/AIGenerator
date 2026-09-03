@echo off

echo ============================
echo qwen SetupScript
echo ============================

echo Checking for Python installation...

python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed.
    echo installing Python...
    winget install --id Python.Python.3 -e --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo Failed to install python
        pause
        exit /b 1
    )
    echo Python installed successfully.
    echo Please restart the script to continue.
    pause
    exit /b 0
)

echo Python is installed.
echo verifying virtual environment...
if not exist ".venv" (
    echo Creating python virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Python virtual environment created.
    echo Installing required packages...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install required packages
        pause
        exit /b 1
    )
)

start "" ".venv\Scripts\pythonw.exe" main.py
if errorlevel 1 (
    echo.
    echo The application exited with an error.
)
