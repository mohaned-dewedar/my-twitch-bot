@echo off
REM CherryBott Quick Start Script for Windows
REM Simple wrapper to launch the automated setup

echo 🍒 Starting CherryBott Launcher...

REM Change to script directory
cd /d "%~dp0"
echo Project directory: %cd%

REM Check if uv is available
uv --version >nul 2>&1
if errorlevel 1 (
    echo ❌ uv not found. Please install uv: https://astral.sh/uv/install.sh
    pause
    exit /b 1
)

REM Run the launcher
uv run python launcher.py

pause