#!/bin/bash
# Start MCP Dashboard with all components

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}        MCP Multi-Agent Dashboard              ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# Function to check if a process is running
is_running() {
    pgrep -f "$1" > /dev/null 2>&1
}

# 1. Check/Start MCP Server
echo -e "${YELLOW}1. MCP Server${NC}"
if is_running "mcp_server_complete.py"; then
    echo -e "   ${GREEN}✅ Already running${NC}"
else
    echo -e "   ${YELLOW}Starting...${NC}"
    python3 /Users/erik/Desktop/claude-multiagent-system/mcp_server_complete.py > /tmp/mcp_server.log 2>&1 &
    sleep 2
    if is_running "mcp_server_complete.py"; then
        echo -e "   ${GREEN}✅ Started${NC}"
    else
        echo -e "   ${RED}❌ Failed to start${NC}"
    fi
fi

# 2. Check/Start MCP API Server
echo -e "${YELLOW}2. MCP API Server${NC}"
if is_running "mcp_api_server.py"; then
    echo -e "   ${GREEN}✅ Already running on http://localhost:5001${NC}"
else
    echo -e "   ${YELLOW}Starting...${NC}"
    python3 /Users/erik/Desktop/claude-multiagent-system/mcp_api_server.py > /tmp/mcp_api.log 2>&1 &
    sleep 2
    if is_running "mcp_api_server.py"; then
        echo -e "   ${GREEN}✅ Started on http://localhost:5001${NC}"
    else
        echo -e "   ${RED}❌ Failed to start${NC}"
    fi
fi

# 3. Check Frontend
echo -e "${YELLOW}3. Frontend Dashboard${NC}"
if is_running "vite"; then
    echo -e "   ${GREEN}✅ Already running on http://localhost:5173${NC}"
else
    echo -e "   ${YELLOW}Starting...${NC}"
    cd /Users/erik/Desktop/claude-multiagent-system/claude-ui
    npm run dev > /tmp/frontend.log 2>&1 &
    sleep 3
    if is_running "vite"; then
        echo -e "   ${GREEN}✅ Started on http://localhost:5173${NC}"
    else
        echo -e "   ${RED}❌ Failed to start${NC}"
    fi
fi

# 4. Database Status
echo -e "${YELLOW}4. Database Status${NC}"
if [ -f "/tmp/mcp_state.db" ]; then
    ACTIVITIES=$(sqlite3 /tmp/mcp_state.db "SELECT COUNT(*) FROM activities;" 2>/dev/null || echo 0)
    COMPONENTS=$(sqlite3 /tmp/mcp_state.db "SELECT COUNT(*) FROM components;" 2>/dev/null || echo 0)
    AGENTS=$(sqlite3 /tmp/mcp_state.db "SELECT COUNT(*) FROM agent_states;" 2>/dev/null || echo 0)

    echo -e "   ${GREEN}✅ Database active${NC}"
    echo -e "      Activities: ${BLUE}$ACTIVITIES${NC}"
    echo -e "      Components: ${BLUE}$COMPONENTS${NC}"
    echo -e "      Agents:     ${BLUE}$AGENTS${NC}"
else
    echo -e "   ${YELLOW}⚠️  Database will be created on first use${NC}"
fi

# 5. Active Claude Sessions
echo -e "${YELLOW}5. Claude Agent Sessions${NC}"
SESSIONS=$(tmux list-sessions 2>/dev/null | grep claude- | wc -l)
if [ $SESSIONS -gt 0 ]; then
    echo -e "   ${GREEN}✅ $SESSIONS active sessions${NC}"
    tmux list-sessions 2>/dev/null | grep claude- | while read line; do
        SESSION_NAME=$(echo $line | cut -d: -f1)
        echo -e "      • ${BLUE}$SESSION_NAME${NC}"
    done
else
    echo -e "   ${YELLOW}No active sessions${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}System Ready!${NC}"
echo ""
echo "📊 Dashboard:    http://localhost:5173"
echo "🔌 API Server:   http://localhost:5001/api/mcp/status"
echo "📝 MCP Log:      tail -f /tmp/mcp_bridge.log"
echo "💾 Database:     sqlite3 /tmp/mcp_state.db"
echo ""
echo "To start agents with MCP:"
echo "  ./start_claude_agent_with_mcp.sh"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"

# Open browser
echo ""
read -p "Open dashboard in browser? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open http://localhost:5173
fi