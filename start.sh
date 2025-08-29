#!/bin/bash
#
# CherryBott Quick Start Script
# 
# Launches both the bot and the web dashboard

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🍒 Starting CherryBott with Web Dashboard..."
echo "Project directory: $SCRIPT_DIR"

# Change to project directory
cd "$SCRIPT_DIR"

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Please install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Function to cleanup background processes
cleanup() {
    echo "🛑 Shutting down services..."
    if [[ -n $WEB_PID ]]; then
        kill $WEB_PID 2>/dev/null || true
    fi
    if [[ -n $BOT_PID ]]; then
        kill $BOT_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start web dashboard in background
echo "🚀 Starting web dashboard on http://localhost:8080"
uv run python -m web.main &
WEB_PID=$!

# Wait a moment for web server to start
sleep 2

echo "🤖 Starting bot launcher..."
echo "📊 Web dashboard available at: http://localhost:8080"
echo ""

# Run the bot launcher (this will be interactive)
uv run python launcher.py

# When launcher exits, cleanup web dashboard
if [[ -n $WEB_PID ]]; then
    kill $WEB_PID 2>/dev/null || true
fi