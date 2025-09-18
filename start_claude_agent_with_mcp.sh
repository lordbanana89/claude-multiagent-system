#!/bin/bash
# Start Claude CLI agent with MCP bridge enabled

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to start an agent
start_agent() {
    local agent_name=$1
    local session_name="claude-$agent_name"

    echo -e "${BLUE}🤖 Starting Claude agent: $agent_name${NC}"

    # Kill existing session if it exists
    tmux kill-session -t "$session_name" 2>/dev/null

    # Create new TMUX session
    tmux new-session -d -s "$session_name"

    # Set environment variables and start Claude
    tmux send-keys -t "$session_name" "export CLAUDE_AGENT_NAME='$agent_name'" Enter
    tmux send-keys -t "$session_name" "export MCP_DB_PATH='/tmp/mcp_state.db'" Enter
    tmux send-keys -t "$session_name" "export CLAUDE_PROJECT_DIR='/Users/erik/Desktop/claude-multiagent-system'" Enter

    # Add startup message
    tmux send-keys -t "$session_name" "echo ''" Enter
    tmux send-keys -t "$session_name" "echo '🌉 MCP Bridge Active for Agent: $agent_name'" Enter
    tmux send-keys -t "$session_name" "echo '📊 Database: /tmp/mcp_state.db'" Enter
    tmux send-keys -t "$session_name" "echo '🔧 Hooks: Enabled'" Enter
    tmux send-keys -t "$session_name" "echo ''" Enter

    # Start Claude CLI
    tmux send-keys -t "$session_name" "cd /Users/erik/Desktop/claude-multiagent-system" Enter
    tmux send-keys -t "$session_name" "claude" Enter

    echo -e "${GREEN}✅ Agent $agent_name started in TMUX session: $session_name${NC}"
}

# Function to demonstrate MCP integration
demonstrate_mcp() {
    local agent_name=$1
    local session_name="claude-$agent_name"

    echo -e "${YELLOW}📝 Sending MCP demo commands to $agent_name...${NC}"

    # Wait for Claude to fully start
    sleep 2

    # Send demonstration commands
    tmux send-keys -t "$session_name" "I am the $agent_name agent. I'll use the log_activity tool to announce I'm starting work on the authentication system." Enter
    sleep 1

    tmux send-keys -t "$session_name" "Let me check for conflicts with the /api/auth endpoint before implementing." Enter
    sleep 1

    tmux send-keys -t "$session_name" "I'm registering component: api:/api/auth as owned by me." Enter
    sleep 1

    tmux send-keys -t "$session_name" "Updating my status to: actively implementing authentication" Enter
}

# Main script
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}     Claude Multi-Agent System with MCP        ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# Check if MCP server is running
if ps aux | grep -q "[m]cp_server_complete.py"; then
    echo -e "${GREEN}✅ MCP Server is running${NC}"
else
    echo -e "${YELLOW}⚠️  MCP Server not detected, starting it...${NC}"
    python3 /Users/erik/Desktop/claude-multiagent-system/mcp_server_complete.py > /tmp/mcp_server.log 2>&1 &
    sleep 2
fi

# Check database
if [ -f "/tmp/mcp_state.db" ]; then
    echo -e "${GREEN}✅ MCP Database exists${NC}"
    ACTIVITY_COUNT=$(sqlite3 /tmp/mcp_state.db "SELECT COUNT(*) FROM activities;" 2>/dev/null || echo 0)
    echo -e "   📊 Activities logged: $ACTIVITY_COUNT"
else
    echo -e "${YELLOW}⚠️  MCP Database will be created on first use${NC}"
fi

# Check hooks configuration
if [ -f "/Users/erik/Desktop/claude-multiagent-system/.claude/hooks/settings.toml" ]; then
    echo -e "${GREEN}✅ Claude hooks configured${NC}"
else
    echo -e "${RED}❌ Claude hooks not configured!${NC}"
    echo "   Run: ./setup_claude_hooks.sh"
    exit 1
fi

echo ""
echo "Choose an option:"
echo "1) Start Backend API agent"
echo "2) Start Database agent"
echo "3) Start Frontend UI agent"
echo "4) Start Testing agent"
echo "5) Start all agents"
echo "6) Start with demo (Backend API)"
echo "7) Monitor MCP activity"
echo "8) View system status"
echo ""
read -p "Enter choice [1-8]: " choice

case $choice in
    1)
        start_agent "backend-api"
        ;;
    2)
        start_agent "database"
        ;;
    3)
        start_agent "frontend-ui"
        ;;
    4)
        start_agent "testing"
        ;;
    5)
        start_agent "backend-api"
        start_agent "database"
        start_agent "frontend-ui"
        start_agent "testing"
        echo ""
        echo -e "${GREEN}All agents started!${NC}"
        ;;
    6)
        start_agent "backend-api"
        demonstrate_mcp "backend-api"
        echo ""
        echo -e "${YELLOW}Demo commands sent! Check TMUX session to see MCP in action:${NC}"
        echo "   tmux attach -t claude-backend-api"
        ;;
    7)
        echo -e "${BLUE}Monitoring MCP activity...${NC}"
        echo ""
        tail -f /tmp/mcp_bridge.log
        ;;
    8)
        echo ""
        echo -e "${BLUE}📊 System Status${NC}"
        echo ""
        echo "Active Claude agents:"
        tmux list-sessions 2>/dev/null | grep claude- | while read line; do
            echo "  ✅ $line"
        done
        echo ""
        echo "Recent MCP activities:"
        sqlite3 -column -header /tmp/mcp_state.db \
            "SELECT substr(agent,1,15) as Agent,
                    substr(activity,1,40) as Activity,
                    category as Type
             FROM activities
             ORDER BY timestamp DESC
             LIMIT 5;" 2>/dev/null
        ;;
    *)
        echo -e "${RED}Invalid choice!${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo "Useful commands:"
echo "• Attach to agent:     tmux attach -t claude-<agent-name>"
echo "• Monitor bridge:      tail -f /tmp/mcp_bridge.log"
echo "• View database:       sqlite3 /tmp/mcp_state.db"
echo "• Check shared log:    tail -f /tmp/mcp_shared_context.log"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"