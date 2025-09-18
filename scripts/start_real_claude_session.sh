#!/bin/bash
# Start REAL Claude Code Session - Must be run manually in terminal

echo "🤖 STARTING REAL CLAUDE CODE SESSION"
echo "===================================="

AGENT_NAME="claude-backend-api"

echo "Creating tmux session: $AGENT_NAME"
/opt/homebrew/bin/tmux new-session -d -s "$AGENT_NAME"

echo "Starting Claude Code in session..."
/opt/homebrew/bin/tmux send-keys -t "$AGENT_NAME" "cd /Users/erik/Desktop/riona_ai/riona-ai" Enter

# Wait a moment
sleep 2

echo "Launching Claude Code..."
/opt/homebrew/bin/tmux send-keys -t "$AGENT_NAME" "claude" Enter

echo ""
echo "✅ Session created! Now you need to:"
echo "1. Attach to the session: tmux attach -t $AGENT_NAME"
echo "2. Wait for Claude Code to load and be ready"
echo "3. Test that Claude responds to your messages"
echo "4. Detach with Ctrl+B then D"
echo ""
echo "⚠️  IMPORTANT: Claude Code must be fully loaded and interactive"
echo "   before any automation will work!"
echo ""
echo "🔧 To test the session works:"
echo "   tmux send-keys -t $AGENT_NAME 'Hello Claude!' Enter"
echo "   tmux capture-pane -t $AGENT_NAME -p"