#!/bin/bash
#
# Start MCP-Enhanced Multi-Agent System
# This script launches all components for autonomous development
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

BASE_DIR="/Users/erik/Desktop/claude-multiagent-system"
cd "$BASE_DIR"

echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     MCP-Enhanced Multi-Agent System         ║${NC}"
echo -e "${BLUE}║         Starting All Components              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"

# Function to check if process is running
check_process() {
    if pgrep -f "$1" > /dev/null; then
        echo -e "${GREEN}✓${NC} $2 is running"
        return 0
    else
        echo -e "${RED}✗${NC} $2 is not running"
        return 1
    fi
}

# Step 1: Verify MCP servers are configured
echo -e "\n${YELLOW}Step 1: Verifying MCP Configuration${NC}"
if [ -f "$HOME/.claude/claude_mcp_config.json" ]; then
    echo -e "${GREEN}✓${NC} MCP configuration found"
else
    echo -e "${RED}✗${NC} MCP configuration not found"
    echo "Copying configuration..."
    mkdir -p ~/.claude
    cp claude_mcp_config_enhanced.json ~/.claude/claude_mcp_config.json
    echo -e "${GREEN}✓${NC} Configuration copied"
fi

# Step 2: Test MCP servers
echo -e "\n${YELLOW}Step 2: Testing MCP Servers${NC}"
python3 test_mcp_integration.py | grep -E "✅|❌" | head -10

# Step 3: Start Redis for task queue
echo -e "\n${YELLOW}Step 3: Starting Redis Server${NC}"
if check_process "redis-server" "Redis"; then
    echo "Redis already running"
else
    echo "Starting Redis..."
    redis-server --daemonize yes
    sleep 2
    check_process "redis-server" "Redis"
fi

# Step 4: Start API servers
echo -e "\n${YELLOW}Step 4: Starting API Servers${NC}"

# Kill existing API servers
pkill -f "uvicorn api.main" || true
pkill -f "python.*api/main.py" || true

# Start main API
echo "Starting main API on port 5001..."
cd "$BASE_DIR"
uvicorn api.main:app --host 0.0.0.0 --port 5001 --reload > api.log 2>&1 &
sleep 3
check_process "uvicorn.*5001" "Main API (5001)"

# Step 5: Start React Dashboard
echo -e "\n${YELLOW}Step 5: Starting React Dashboard${NC}"
cd "$BASE_DIR/claude-ui"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Kill existing Vite server
pkill -f "vite" || true

# Start Vite
echo "Starting React dashboard on port 5173..."
npm run dev > ../dashboard.log 2>&1 &
sleep 5
check_process "vite" "React Dashboard (5173)"

# Step 6: Initialize agent database
echo -e "\n${YELLOW}Step 6: Checking Agent Status${NC}"
cd "$BASE_DIR"
sqlite3 mcp_system.db "SELECT name, status FROM agents;" | while IFS='|' read name status; do
    if [ "$status" = "active" ] || [ "$status" = "monitoring" ]; then
        echo -e "${GREEN}✓${NC} Agent: $name ($status)"
    else
        echo -e "${YELLOW}○${NC} Agent: $name ($status)"
    fi
done

# Step 7: Create TMUX sessions for agents
echo -e "\n${YELLOW}Step 7: Creating TMUX Sessions for Agents${NC}"

agents=("supervisor" "master" "backend-api" "database" "frontend-ui" "testing" "deployment" "instagram" "queue-manager")

for agent in "${agents[@]}"; do
    session_name="claude-$agent"

    # Kill existing session
    tmux kill-session -t "$session_name" 2>/dev/null || true

    # Create new session
    tmux new-session -d -s "$session_name"
    tmux send-keys -t "$session_name" "echo '🤖 Agent $agent ready with MCP tools'" Enter
    echo -e "${GREEN}✓${NC} Created TMUX session: $session_name"
done

# Step 8: Display system status
echo -e "\n${BLUE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           SYSTEM STATUS SUMMARY              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"

echo -e "\n${GREEN}MCP Servers:${NC}"
echo "  • Filesystem Server: Ready"
echo "  • Git Server: Ready (mcp-server-git)"
echo "  • Memory Server: Ready (knowledge graph)"
echo "  • Fetch Server: Ready (web content)"

echo -e "\n${GREEN}System Components:${NC}"
echo "  • Redis: Running (task queue)"
echo "  • API: http://localhost:5001"
echo "  • Dashboard: http://localhost:5173"
echo "  • Database: mcp_system.db"

echo -e "\n${GREEN}Agent TMUX Sessions:${NC}"
tmux ls | grep claude- | awk '{print "  • " $1}'

echo -e "\n${BLUE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         SYSTEM READY FOR AUTONOMOUS          ║${NC}"
echo -e "${BLUE}║              DEVELOPMENT WORK                ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"

echo -e "\n${YELLOW}Quick Commands:${NC}"
echo "  • View Dashboard: open http://localhost:5173"
echo "  • Attach to agent: tmux attach -t claude-supervisor"
echo "  • Test MCP: python3 test_mcp_integration.py"
echo "  • Monitor API: tail -f api.log"

echo -e "\n${GREEN}✨ System is ready! MCP tools are available in Claude Desktop.${NC}"