#!/bin/bash
#
# CherryBott Quick Start Script
# 
# Simple wrapper to launch the automated setup

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🍒 Starting CherryBott Launcher..."
echo "Project directory: $SCRIPT_DIR"

# Change to project directory
cd "$SCRIPT_DIR"

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Please install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Run the launcher
uv run python launcher.py