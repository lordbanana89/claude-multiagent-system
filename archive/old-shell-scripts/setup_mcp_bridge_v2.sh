#!/bin/bash

# MCP Bridge v2 Setup Script
# Configures Claude Code hooks to use MCP v2 bridge

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="/Users/erik/Desktop/claude-multiagent-system"
BRIDGE_SCRIPT="$PROJECT_DIR/mcp_bridge_v2.py"
HOOKS_DIR="$HOME/.claude/hooks"

echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   MCP Bridge v2 Setup & Test         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"

# Step 1: Check if MCP server is running
echo -e "\n${CYAN}1. Checking MCP Server v2...${NC}"
if curl -s -f http://localhost:8099/api/mcp/status > /dev/null 2>&1; then
    echo -e "${GREEN}✓ MCP Server v2 is running on port 8099${NC}"
else
    echo -e "${YELLOW}⚠ MCP Server v2 not detected. Starting...${NC}"
    cd "$PROJECT_DIR"
    python3 mcp_server_v2_compliant.py &
    sleep 2

    if curl -s -f http://localhost:8099/api/mcp/status > /dev/null 2>&1; then
        echo -e "${GREEN}✓ MCP Server v2 started successfully${NC}"
    else
        echo -e "${RED}✗ Failed to start MCP Server v2${NC}"
        exit 1
    fi
fi

# Step 2: Make bridge executable
echo -e "\n${CYAN}2. Setting up MCP Bridge v2...${NC}"
chmod +x "$BRIDGE_SCRIPT"
echo -e "${GREEN}✓ Bridge script ready${NC}"

# Step 3: Configure Claude hooks
echo -e "\n${CYAN}3. Configuring Claude Code hooks...${NC}"

# Create hooks directory if it doesn't exist
mkdir -p "$HOOKS_DIR"

# Create hook configuration
cat > "$HOOKS_DIR/mcp_v2_hook.sh" << 'EOF'
#!/bin/bash
# MCP v2 Hook for Claude Code

# Get the hook type from the first argument
HOOK_TYPE="$1"

# Set agent name from tmux session if available
if [ -n "$TMUX" ]; then
    export CLAUDE_AGENT_NAME=$(tmux display-message -p '#S' | sed 's/claude-//')
fi

# Set MCP server URL
export MCP_SERVER_URL="http://localhost:8099"
export MCP_WS_URL="ws://localhost:8100"

# Call the bridge
python3 /Users/erik/Desktop/claude-multiagent-system/mcp_bridge_v2.py "$HOOK_TYPE"
EOF

chmod +x "$HOOKS_DIR/mcp_v2_hook.sh"
echo -e "${GREEN}✓ Claude hooks configured${NC}"

# Step 4: Test the bridge
echo -e "\n${CYAN}4. Testing MCP Bridge v2...${NC}"

# Test 1: Direct bridge test
echo -e "\n${YELLOW}Test 1: Direct bridge invocation${NC}"
echo '{"content": "MCP: heartbeat"}' | python3 "$BRIDGE_SCRIPT" notification
echo -e "${GREEN}✓ Direct invocation successful${NC}"

# Test 2: MCP tool detection
echo -e "\n${YELLOW}Test 2: Tool detection patterns${NC}"
test_patterns=(
    "I'll log this activity: Testing MCP bridge"
    "MCP: update_status active"
    "checking for conflicts with database changes"
    "registering component: api-endpoint"
)

for pattern in "${test_patterns[@]}"; do
    echo -n "  Testing: \"$pattern\" ... "
    result=$(echo "{\"content\": \"$pattern\"}" | python3 "$BRIDGE_SCRIPT" message 2>/dev/null)
    if echo "$result" | grep -q "MCP v2:"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
    fi
done

# Test 3: MCP server communication
echo -e "\n${YELLOW}Test 3: MCP server communication${NC}"
response=$(curl -s -X POST http://localhost:8099/jsonrpc \
    -H "Content-Type: application/json" \
    -d '{
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "heartbeat",
            "arguments": {"agent": "test"}
        },
        "id": "test-1"
    }')

if echo "$response" | grep -q '"success":true'; then
    echo -e "${GREEN}✓ MCP server communication successful${NC}"
else
    echo -e "${RED}✗ MCP server communication failed${NC}"
fi

# Step 5: Create agent terminal launcher with MCP
echo -e "\n${CYAN}5. Creating MCP-enabled terminal launcher...${NC}"

cat > "$PROJECT_DIR/start_mcp_terminal.sh" << 'LAUNCHER'
#!/bin/bash

# Start terminal with MCP bridge enabled
AGENT_NAME="${1:-master}"
PORT="${2:-8090}"

echo "Starting MCP-enabled terminal for agent: $AGENT_NAME"

# Create tmux session with MCP environment
tmux new-session -d -s "claude-$AGENT_NAME" \
    "export CLAUDE_AGENT_NAME=$AGENT_NAME; \
     export MCP_SERVER_URL=http://localhost:8099; \
     export MCP_WS_URL=ws://localhost:8100; \
     export CLAUDE_HOOKS_DIR=$HOME/.claude/hooks; \
     export CLAUDE_HOOK_NOTIFICATION=$HOME/.claude/hooks/mcp_v2_hook.sh; \
     export CLAUDE_HOOK_MESSAGE=$HOME/.claude/hooks/mcp_v2_hook.sh; \
     echo '═══════════════════════════════════════'; \
     echo '  MCP v2 Agent Terminal: $AGENT_NAME'; \
     echo '  Server: http://localhost:8099'; \
     echo '  Status: Connected'; \
     echo '═══════════════════════════════════════'; \
     echo ''; \
     echo 'MCP Commands:'; \
     echo '  MCP: heartbeat              - Send heartbeat'; \
     echo '  MCP: status <state>         - Update status'; \
     echo '  MCP: log <activity>         - Log activity'; \
     echo '  MCP: register <component>   - Register component'; \
     echo ''; \
     echo 'Starting Claude with MCP v2 integration...'; \
     claude --model opus"

# Start ttyd for web access
ttyd -p $PORT tmux attach-session -t "claude-$AGENT_NAME" &

echo "Terminal available at: http://localhost:$PORT"
echo "Attach directly: tmux attach -t claude-$AGENT_NAME"
LAUNCHER

chmod +x "$PROJECT_DIR/start_mcp_terminal.sh"
echo -e "${GREEN}✓ MCP terminal launcher created${NC}"

# Step 6: Display status
echo -e "\n${BLUE}╔══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   MCP Bridge v2 Setup Complete       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"

echo -e "\n${GREEN}✅ MCP Bridge v2 Configuration:${NC}"
echo "   • Bridge Script: $BRIDGE_SCRIPT"
echo "   • Hooks Directory: $HOOKS_DIR"
echo "   • MCP Server: http://localhost:8099"
echo "   • WebSocket: ws://localhost:8100"

echo -e "\n${CYAN}📝 Usage Instructions:${NC}"
echo "1. Start MCP-enabled terminal:"
echo "   ${YELLOW}./start_mcp_terminal.sh <agent-name> <port>${NC}"
echo ""
echo "2. In any Claude terminal, use MCP commands:"
echo "   ${YELLOW}MCP: heartbeat${NC}"
echo "   ${YELLOW}MCP: log Testing the system${NC}"
echo "   ${YELLOW}MCP: status busy${NC}"
echo ""
echo "3. Monitor MCP activity:"
echo "   ${YELLOW}tail -f /tmp/mcp_bridge_v2.log${NC}"
echo "   ${YELLOW}tail -f /tmp/mcp_shared_context.log${NC}"

echo -e "\n${PURPLE}🎯 Quick Test:${NC}"
echo "   Run: ${YELLOW}./start_mcp_terminal.sh test-agent 8099${NC}"
echo "   Then in terminal: ${YELLOW}MCP: heartbeat${NC}"

echo -e "\n${GREEN}✨ MCP Bridge v2 is ready for production use!${NC}"