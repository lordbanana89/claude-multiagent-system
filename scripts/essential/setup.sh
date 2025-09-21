#!/bin/bash
# Unified Setup Script for Claude Multi-Agent System

set -e

echo "🚀 Claude Multi-Agent System - Setup"
echo "===================================="

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python3 required but not installed. Aborting." >&2; exit 1; }
command -v tmux >/dev/null 2>&1 || { echo "TMUX required but not installed. Aborting." >&2; exit 1; }
command -v redis-cli >/dev/null 2>&1 || { echo "Redis required but not installed. Aborting." >&2; exit 1; }

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install dependencies
source venv/bin/activate
echo "Installing Python dependencies..."
pip install -q -r requirements.txt

# Initialize databases
echo "Initializing databases..."
for db in mcp_system.db shared_inbox.db auth.db; do
    if [ ! -f "$db" ]; then
        sqlite3 "$db" "CREATE TABLE IF NOT EXISTS init (id INTEGER PRIMARY KEY);"
        echo "✅ Created $db"
    fi
done

# Setup frontend
if [ -d "claude-ui" ]; then
    echo "Setting up frontend..."
    cd claude-ui
    npm install --silent
    cd ..
fi

echo "✅ Setup complete!"