#!/bin/bash
AGENT_NAME="${1:-master}"
PORT="${2:-8090}"

echo "Starting MCP Complete Terminal for: $AGENT_NAME"

# Kill existing tmux session if exists
tmux kill-session -t "claude-$AGENT_NAME" 2>/dev/null || true

# Create new session with complete bridge
tmux new-session -d -s "claude-$AGENT_NAME" \
    "export CLAUDE_AGENT_NAME=$AGENT_NAME; \
     export MCP_SERVER_URL=http://localhost:8099; \
     export MCP_WS_URL=ws://localhost:8100; \
     echo '╔═══════════════════════════════════════╗'; \
     echo '║   MCP v2 COMPLETE Terminal            ║'; \
     echo '╠═══════════════════════════════════════╣'; \
     echo '║ Agent: $AGENT_NAME'; \
     echo '║ Server: http://localhost:8099         ║'; \
     echo '║ WebSocket: ws://localhost:8100        ║'; \
     echo '║ Status: ✅ All Features Active        ║'; \
     echo '╚═══════════════════════════════════════╝'; \
     echo ''; \
     echo 'Features:'; \
     echo '  • WebSocket: Real-time updates'; \
     echo '  • Retry: Automatic reconnection'; \
     echo '  • Hooks: Claude integration active'; \
     echo ''; \
     echo 'Commands:'; \
     echo '  MCP: heartbeat'; \
     echo '  MCP: status <state>'; \
     echo '  MCP: log <activity>'; \
     echo ''; \
     claude --model opus"

# Start ttyd if port specified
if [ -n "$PORT" ]; then
    ttyd -p $PORT tmux attach-session -t "claude-$AGENT_NAME" > /dev/null 2>&1 &
    echo "Web terminal at: http://localhost:$PORT"
fi

echo "Connect: tmux attach -t claude-$AGENT_NAME"
