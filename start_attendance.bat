@echo off
echo Smart Attendance System
echo =====================
echo.
echo Starting the application...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Run the launcher
python launch_app.py

pause
