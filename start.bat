@echo off
REM CherryBott Quick Start Script for Windows
REM Launches both the bot and the web dashboard

echo 🍒 Starting CherryBott with Web Dashboard...

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

REM Start web dashboard in background
echo 🚀 Starting web dashboard on http://localhost:8080
start /B uv run python -m web.main

REM Wait a moment for web server to start
timeout /t 3 /nobreak >nul

echo 🤖 Starting bot launcher...
REM Run the bot launcher (this will be interactive)
uv run python launcher.py

pause