#!/bin/bash

# Migrate from old TMUX-based system to Overmind
# This script helps transition from manual tmux sessions to Overmind management

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "🔄 Migrating Claude Multi-Agent System to Overmind"
echo "=================================================="
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check if Overmind is installed
if ! command -v overmind &> /dev/null; then
    echo "❌ Overmind not found. Installing..."
    if command -v brew &> /dev/null; then
        brew install overmind
    else
        echo "❌ Please install Overmind manually:"
        echo "   brew install overmind"
        echo "   or: go install github.com/DarthSim/overmind/v2@latest"
        exit 1
    fi
else
    echo "✅ Overmind installed: $(overmind --version)"
fi

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "❌ tmux not found. Please install tmux first."
    exit 1
else
    echo "✅ tmux installed"
fi

# Change to project root
cd "$PROJECT_ROOT"

# Check for Procfile
if [ ! -f "Procfile" ]; then
    echo "❌ Procfile not found in $PROJECT_ROOT"
    echo "   Please ensure you're running this from the project root"
    exit 1
else
    echo "✅ Procfile found"
fi

echo ""
echo "📊 Current TMUX sessions:"
echo "------------------------"
tmux ls 2>/dev/null || echo "   No active tmux sessions"

echo ""
echo "⚠️  WARNING: This will stop all existing Claude agent sessions!"
echo "   Press Ctrl+C to abort, or Enter to continue..."
read -r

# Step 1: Kill any existing Overmind processes
echo ""
echo "🛑 Stopping any existing Overmind processes..."
overmind kill 2>/dev/null || true
sleep 1

# Step 2: Stop old tmux sessions (optional - can be skipped to keep them)
echo ""
echo "❓ Do you want to stop existing tmux sessions? (y/N)"
read -r STOP_TMUX

if [ "$STOP_TMUX" = "y" ] || [ "$STOP_TMUX" = "Y" ]; then
    echo "🛑 Stopping old tmux sessions..."

    # List of known Claude agent sessions
    AGENT_SESSIONS=(
        "claude-supervisor"
        "claude-master"
        "claude-backend-api"
        "claude-database"
        "claude-frontend-ui"
        "claude-instagram"
        "claude-testing"
        "claude-queue-manager"
        "claude-deployment"
    )

    for session in "${AGENT_SESSIONS[@]}"; do
        if tmux has-session -t "$session" 2>/dev/null; then
            echo "   Stopping $session..."
            tmux kill-session -t "$session" 2>/dev/null || true
        fi
    done
    echo "✅ Old sessions stopped"
else
    echo "ℹ️  Keeping existing tmux sessions (they won't be managed by Overmind)"
fi

# Step 3: Choose Procfile
echo ""
echo "📁 Which Procfile would you like to use?"
echo "   1) Procfile (full system - all agents)"
echo "   2) Procfile.dev (development - minimal agents)"
echo "   3) Custom"
echo ""
echo -n "Enter choice [1-3]: "
read -r PROCFILE_CHOICE

case $PROCFILE_CHOICE in
    1)
        PROCFILE="Procfile"
        ;;
    2)
        PROCFILE="Procfile.dev"
        ;;
    3)
        echo -n "Enter Procfile name: "
        read -r PROCFILE
        if [ ! -f "$PROCFILE" ]; then
            echo "❌ $PROCFILE not found"
            exit 1
        fi
        ;;
    *)
        echo "Invalid choice, using default Procfile"
        PROCFILE="Procfile"
        ;;
esac

echo "📄 Using: $PROCFILE"

# Step 4: Start Overmind
echo ""
echo "🚀 Starting Overmind with $PROCFILE..."
echo ""
echo "Choose startup mode:"
echo "   1) Daemon mode (background)"
echo "   2) Attached mode (see all logs)"
echo ""
echo -n "Enter choice [1-2]: "
read -r MODE_CHOICE

case $MODE_CHOICE in
    1)
        echo "Starting in daemon mode..."
        overmind start -f "$PROCFILE" -D

        # Wait for processes to start
        echo "⏳ Waiting for processes to start..."
        sleep 3

        # Show status
        echo ""
        echo "📊 Process Status:"
        overmind ps

        echo ""
        echo "✅ Migration complete! Overmind is running in daemon mode."
        echo ""
        echo "🎯 Useful commands:"
        echo "   overmind ps              - Show process status"
        echo "   overmind connect <name>  - Connect to specific agent"
        echo "   overmind restart <name>  - Restart specific agent"
        echo "   overmind echo            - View logs"
        echo "   overmind quit            - Stop all processes gracefully"
        echo "   overmind kill            - Force stop all processes"
        ;;
    2)
        echo "Starting in attached mode..."
        echo ""
        echo "ℹ️  Press Ctrl+C to stop all processes"
        echo ""
        overmind start -f "$PROCFILE"
        ;;
    *)
        echo "Invalid choice, starting in daemon mode..."
        overmind start -f "$PROCFILE" -D
        ;;
esac

echo ""
echo "📚 Documentation:"
echo "   - Connect to supervisor: overmind connect supervisor"
echo "   - Connect to backend: overmind connect backend"
echo "   - View Streamlit: overmind connect web"
echo ""
echo "🔧 To switch back to old system:"
echo "   1. Run: overmind kill"
echo "   2. Use: ./scripts/start_complete_system.sh"
echo ""
echo "🎉 Migration script completed!"