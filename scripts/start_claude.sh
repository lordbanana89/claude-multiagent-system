#!/bin/bash
# Simple Claude Code Session Starter

echo "🤖 Creating Claude Code session..."

# Kill existing session if any
/opt/homebrew/bin/tmux kill-session -t claude-test 2>/dev/null

# Create new session
/opt/homebrew/bin/tmux new-session -d -s claude-test

# Go to the project directory
/opt/homebrew/bin/tmux send-keys -t claude-test "cd /Users/erik/Desktop/claude-multiagent-system" Enter

# Start Claude
/opt/homebrew/bin/tmux send-keys -t claude-test "claude" Enter

echo "✅ Session 'claude-test' created!"
echo ""
echo "🔧 To use it:"
echo "1. tmux attach -t claude-test"
echo "2. Wait for Claude to load"
echo "3. Test Claude responds"
echo "4. Detach: Ctrl+B then D"
echo ""
echo "📋 To test from outside:"
echo "   tmux send-keys -t claude-test 'Hello Claude!' Enter"
echo "   tmux capture-pane -t claude-test -p"