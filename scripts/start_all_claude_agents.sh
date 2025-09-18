#!/bin/bash
# Start ALL working Claude Code agents

echo "🤖 STARTING ALL CLAUDE CODE AGENTS"
echo "=================================="

AGENTS=(
    "claude-backend-api"
    "claude-frontend-ui"
    "claude-database"
    "claude-instagram"
    "claude-testing"
)

for agent in "${AGENTS[@]}"; do
    echo "🚀 Starting $agent..."

    # Kill existing session
    /opt/homebrew/bin/tmux kill-session -t "$agent" 2>/dev/null

    # Create new session
    /opt/homebrew/bin/tmux new-session -d -s "$agent"

    # Go to project directory
    /opt/homebrew/bin/tmux send-keys -t "$agent" "cd /Users/erik/Desktop/riona_ai/riona-ai" Enter

    # Start Claude
    /opt/homebrew/bin/tmux send-keys -t "$agent" "claude" Enter

    echo "✅ $agent session created"
    sleep 2
done

echo ""
echo "🎉 ALL AGENTS STARTED!"
echo ""
echo "📋 Active sessions:"
/opt/homebrew/bin/tmux list-sessions | grep claude

echo ""
echo "🔧 To test an agent:"
echo "   tmux send-keys -t claude-backend-api 'Hello!' Enter"
echo "   tmux capture-pane -t claude-backend-api -p"
echo ""
echo "💡 Wait ~30 seconds for all Claude instances to fully load"