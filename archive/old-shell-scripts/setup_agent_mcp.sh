#!/bin/bash
# Setup script for Claude agents with MCP

AGENT_NAME=$1
if [ -z "$AGENT_NAME" ]; then
    echo "Usage: $0 <agent-name>"
    echo "Example: $0 supervisor"
    exit 1
fi

# Normalize agent name
AGENT_NAME=$(echo "$AGENT_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
SESSION_NAME="claude-$AGENT_NAME"

echo "🔧 Setting up MCP for agent: $AGENT_NAME"

# Check if session exists
if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Creating new TMUX session: $SESSION_NAME"
    tmux new-session -d -s "$SESSION_NAME"
fi

# Kill any running Claude process
tmux send-keys -t "$SESSION_NAME" C-c 2>/dev/null
sleep 1

# Clear and setup environment
tmux send-keys -t "$SESSION_NAME" "clear" Enter

# Export MCP environment variables
tmux send-keys -t "$SESSION_NAME" "# MCP Configuration for $AGENT_NAME" Enter
tmux send-keys -t "$SESSION_NAME" "export CLAUDE_AGENT_NAME='$AGENT_NAME'" Enter
tmux send-keys -t "$SESSION_NAME" "export MCP_DB_PATH='/tmp/mcp_state.db'" Enter
tmux send-keys -t "$SESSION_NAME" "export CLAUDE_PROJECT_DIR='/Users/erik/Desktop/claude-multiagent-system'" Enter
tmux send-keys -t "$SESSION_NAME" "export MCP_ENABLED=true" Enter
tmux send-keys -t "$SESSION_NAME" "export MCP_BRIDGE_ENABLED=true" Enter

# Setup hooks directory for MCP bridge
tmux send-keys -t "$SESSION_NAME" "export CLAUDE_HOOKS_DIR='\$CLAUDE_PROJECT_DIR/.claude-hooks'" Enter
tmux send-keys -t "$SESSION_NAME" "mkdir -p \$CLAUDE_HOOKS_DIR" Enter

# Create a hook file for MCP bridge
cat > /tmp/mcp_hook_$AGENT_NAME.sh << 'EOF'
#!/bin/bash
# MCP Bridge Hook
if [ -n "$MCP_ENABLED" ]; then
    # Log to MCP database
    sqlite3 /tmp/mcp_state.db "INSERT INTO activities (id, agent, timestamp, activity, category, status) VALUES ('hook_$$_$(date +%s)', '$CLAUDE_AGENT_NAME', datetime('now'), 'Hook executed', 'system', 'active');" 2>/dev/null
fi
EOF

# Copy hook to hooks directory
tmux send-keys -t "$SESSION_NAME" "cat > \$CLAUDE_HOOKS_DIR/pre-prompt.sh << 'EOF'" Enter
tmux send-keys -t "$SESSION_NAME" "#!/bin/bash" Enter
tmux send-keys -t "$SESSION_NAME" "# MCP Bridge Hook for $AGENT_NAME" Enter
tmux send-keys -t "$SESSION_NAME" "sqlite3 /tmp/mcp_state.db \"INSERT OR REPLACE INTO agent_states (agent, last_seen, status, current_task) VALUES ('\$CLAUDE_AGENT_NAME', datetime('now'), 'active', 'Processing');\" 2>/dev/null" Enter
tmux send-keys -t "$SESSION_NAME" "EOF" Enter
tmux send-keys -t "$SESSION_NAME" "chmod +x \$CLAUDE_HOOKS_DIR/pre-prompt.sh" Enter

# Navigate to project directory
tmux send-keys -t "$SESSION_NAME" "cd \$CLAUDE_PROJECT_DIR" Enter

# Display configuration
tmux send-keys -t "$SESSION_NAME" "echo ''" Enter
tmux send-keys -t "$SESSION_NAME" "echo '✅ MCP Configuration Complete for $AGENT_NAME'" Enter
tmux send-keys -t "$SESSION_NAME" "echo '==================================='" Enter
tmux send-keys -t "$SESSION_NAME" "echo 'Agent Name: '\$CLAUDE_AGENT_NAME" Enter
tmux send-keys -t "$SESSION_NAME" "echo 'MCP Database: '\$MCP_DB_PATH" Enter
tmux send-keys -t "$SESSION_NAME" "echo 'Project Dir: '\$CLAUDE_PROJECT_DIR" Enter
tmux send-keys -t "$SESSION_NAME" "echo 'MCP Enabled: '\$MCP_ENABLED" Enter
tmux send-keys -t "$SESSION_NAME" "echo ''" Enter
tmux send-keys -t "$SESSION_NAME" "echo '🚀 Starting Claude CLI with MCP...'" Enter
tmux send-keys -t "$SESSION_NAME" "echo ''" Enter

# Start Claude
tmux send-keys -t "$SESSION_NAME" "claude" Enter

# Log to MCP database
sqlite3 /tmp/mcp_state.db << SQL
INSERT INTO activities (id, agent, timestamp, activity, category, status)
VALUES ('setup_${AGENT_NAME}_$(date +%s)', 'system', datetime('now'),
        'MCP setup completed for ${AGENT_NAME}', 'configuration', 'completed');

INSERT OR REPLACE INTO agent_states (agent, last_seen, status, current_task)
VALUES ('${AGENT_NAME}', datetime('now'), 'active', 'Claude CLI with MCP');
SQL

echo "✅ Agent $AGENT_NAME is now running with MCP enabled"
echo "   Session: $SESSION_NAME"
echo "   Port: Check MultiTerminal for ttyd access"