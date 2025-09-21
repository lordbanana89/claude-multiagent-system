#!/bin/bash

# 🚀 Complete MCP System Setup for Claude Multi-Agent Project
# Production-ready configuration with full integration

set -e  # Exit on error

PROJECT_DIR="/Users/erik/Desktop/claude-multiagent-system"
MCP_SERVER="$PROJECT_DIR/mcp_server_complete.py"
CLAUDE_CONFIG="$HOME/.claude/config/.claude.json"
LOG_DIR="/tmp/claude-mcp-logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     🤖 CLAUDE MULTI-AGENT SYSTEM - COMPLETE MCP SETUP        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. Create log directory
echo -e "${YELLOW}📁 Creating log directory...${NC}"
mkdir -p "$LOG_DIR"
chmod 755 "$LOG_DIR"

# 2. Check dependencies
echo -e "${YELLOW}🔍 Checking dependencies...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found!${NC}"
    exit 1
fi

# Check MCP installation
if ! python3 -c "import mcp" 2>/dev/null; then
    echo -e "${YELLOW}📦 Installing MCP...${NC}"
    pip3 install mcp
fi

# Check Claude CLI
if ! command -v claude &> /dev/null; then
    echo -e "${RED}❌ Claude CLI not found! Please install it first.${NC}"
    exit 1
fi

# Check TMUX
if ! command -v tmux &> /dev/null; then
    echo -e "${YELLOW}📦 Installing TMUX...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install tmux
    else
        sudo apt-get install -y tmux
    fi
fi

echo -e "${GREEN}✅ All dependencies satisfied${NC}"

# 3. Configure Claude for MCP
echo -e "${YELLOW}⚙️  Configuring Claude for MCP...${NC}"

# Backup existing configuration
if [ -f "$CLAUDE_CONFIG" ]; then
    cp "$CLAUDE_CONFIG" "$CLAUDE_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${GREEN}✅ Backed up existing configuration${NC}"
fi

# Update Claude configuration with Python
python3 << EOF
import json
import os

config_path = "$CLAUDE_CONFIG"
project_dir = "$PROJECT_DIR"

# Ensure config directory exists
os.makedirs(os.path.dirname(config_path), exist_ok=True)

# Load or create config
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)
else:
    config = {
        "installMethod": "manual",
        "autoUpdates": True,
        "projects": {}
    }

# Configure MCP for the project
if "projects" not in config:
    config["projects"] = {}

if project_dir not in config["projects"]:
    config["projects"][project_dir] = {
        "allowedTools": [],
        "history": [],
        "mcpContextUris": [],
        "mcpServers": {},
        "enabledMcpjsonServers": [],
        "disabledMcpjsonServers": [],
        "hasTrustDialogAccepted": True
    }

# Add MCP server configuration
config["projects"][project_dir]["mcpServers"] = {
    "coordinator": {
        "command": "python3",
        "args": ["$MCP_SERVER"],
        "env": {
            "PYTHONUNBUFFERED": "1"
        }
    }
}

config["projects"][project_dir]["enabledMcpjsonServers"] = ["coordinator"]
config["projects"][project_dir]["hasTrustDialogAccepted"] = True

# Save updated configuration
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("✅ Claude configuration updated successfully")
EOF

# 4. Start MCP Server
echo -e "${YELLOW}🚀 Starting MCP Coordinator Server...${NC}"

# Kill existing server if running
pkill -f "mcp_server_complete.py" 2>/dev/null || true

# Create server startup script
cat > "$PROJECT_DIR/start_mcp_server.sh" << 'SCRIPT'
#!/bin/bash
cd /Users/erik/Desktop/claude-multiagent-system
export PYTHONUNBUFFERED=1
python3 mcp_server_complete.py
SCRIPT
chmod +x "$PROJECT_DIR/start_mcp_server.sh"

# Start server in TMUX session
tmux kill-session -t mcp-server 2>/dev/null || true
tmux new-session -d -s mcp-server "$PROJECT_DIR/start_mcp_server.sh"

echo -e "${GREEN}✅ MCP Server started in tmux session 'mcp-server'${NC}"

# 5. Wait for server to initialize
echo -e "${YELLOW}⏳ Waiting for server initialization...${NC}"
sleep 3

# 6. Create agent startup scripts
echo -e "${YELLOW}📝 Creating agent startup scripts...${NC}"

# Create individual agent starter
cat > "$PROJECT_DIR/start_agent.sh" << 'AGENT_SCRIPT'
#!/bin/bash

# Agent startup script with MCP integration
AGENT_NAME="${1:-backend-api}"
PROJECT_DIR="/Users/erik/Desktop/claude-multiagent-system"

echo "🚀 Starting agent: $AGENT_NAME"

# Kill existing session
tmux kill-session -t "claude-$AGENT_NAME" 2>/dev/null

# Create new session
tmux new-session -d -s "claude-$AGENT_NAME"

# Navigate to project directory
tmux send-keys -t "claude-$AGENT_NAME" "cd $PROJECT_DIR" Enter

# Start Claude CLI
tmux send-keys -t "claude-$AGENT_NAME" "claude" Enter

# Wait for Claude to initialize
sleep 3

# Send initial context
tmux send-keys -t "claude-$AGENT_NAME" "
I am the $AGENT_NAME agent in a multi-agent system.

Available MCP tools for coordination:
- log_activity: Log activities to shared context
- check_conflicts: Check for conflicts before actions
- register_component: Register components I create
- update_status: Update my current status
- request_collaboration: Request help from other agents
- propose_decision: Propose decisions requiring consensus
- heartbeat: Keep my status active

To use a tool, say: 'I'll use the [tool_name] tool to [action]'

My responsibilities based on my role:
$(case $AGENT_NAME in
    backend-api) echo '- Create and manage API endpoints
- Implement business logic
- Handle authentication and authorization
- Data validation and processing';;
    database) echo '- Design and maintain database schema
- Create migrations and indexes
- Optimize queries
- Ensure data integrity';;
    frontend-ui) echo '- Build user interfaces
- Implement client-side logic
- Handle user interactions
- Styling and UX';;
    testing) echo '- Write unit and integration tests
- Create end-to-end tests
- Ensure code coverage
- Validate functionality';;
    supervisor) echo '- Coordinate between agents
- Assign and track tasks
- Resolve conflicts
- Monitor progress';;
    *) echo '- Perform assigned tasks
- Coordinate with other agents';;
esac)

I'll start by sending a heartbeat and checking current system status.
" Enter

# Send initial heartbeat
sleep 2
tmux send-keys -t "claude-$AGENT_NAME" "I'll use the heartbeat tool to indicate I'm active." Enter

echo "✅ Agent $AGENT_NAME started in session claude-$AGENT_NAME"
echo "   Connect with: tmux attach -t claude-$AGENT_NAME"
AGENT_SCRIPT

chmod +x "$PROJECT_DIR/start_agent.sh"

# Create all-agents starter
cat > "$PROJECT_DIR/start_all_agents.sh" << 'ALL_SCRIPT'
#!/bin/bash

PROJECT_DIR="/Users/erik/Desktop/claude-multiagent-system"

echo "🚀 Starting all Claude agents..."

agents=("backend-api" "database" "frontend-ui" "testing" "supervisor")

for agent in "${agents[@]}"; do
    echo "Starting $agent..."
    "$PROJECT_DIR/start_agent.sh" "$agent"
    sleep 3
done

echo ""
echo "✅ All agents started!"
echo ""
echo "Sessions:"
tmux list-sessions | grep claude-

echo ""
echo "To connect to an agent: tmux attach -t claude-[agent-name]"
ALL_SCRIPT

chmod +x "$PROJECT_DIR/start_all_agents.sh"

# 7. Create monitoring script
cat > "$PROJECT_DIR/monitor_system.sh" << 'MONITOR'
#!/bin/bash

PROJECT_DIR="/Users/erik/Desktop/claude-multiagent-system"

echo "📊 Claude Multi-Agent System Monitor"
echo "===================================="

while true; do
    clear
    echo "📊 SYSTEM STATUS - $(date)"
    echo "===================================="

    # Check MCP server
    echo ""
    echo "🔧 MCP Server:"
    if pgrep -f "mcp_server_complete.py" > /dev/null; then
        echo "  ✅ Running"
    else
        echo "  ❌ Not running"
    fi

    # Check agents
    echo ""
    echo "🤖 Active Agents:"
    for session in $(tmux list-sessions 2>/dev/null | grep claude- | cut -d: -f1); do
        echo "  ✅ $session"
    done

    # Show recent activities
    echo ""
    echo "📝 Recent Activities:"
    if [ -f "/tmp/mcp_shared_context.log" ]; then
        tail -5 /tmp/mcp_shared_context.log | while read line; do
            echo "  $line"
        done
    fi

    # Database stats
    echo ""
    echo "💾 Database Stats:"
    if [ -f "/tmp/mcp_state.db" ]; then
        activities=$(sqlite3 /tmp/mcp_state.db "SELECT COUNT(*) FROM activities" 2>/dev/null || echo 0)
        components=$(sqlite3 /tmp/mcp_state.db "SELECT COUNT(*) FROM components" 2>/dev/null || echo 0)
        echo "  Activities: $activities"
        echo "  Components: $components"
    fi

    echo ""
    echo "Press Ctrl+C to exit"
    sleep 5
done
MONITOR

chmod +x "$PROJECT_DIR/monitor_system.sh"

# 8. Create system control script
cat > "$PROJECT_DIR/control_system.sh" << 'CONTROL'
#!/bin/bash

PROJECT_DIR="/Users/erik/Desktop/claude-multiagent-system"

echo "🎮 Claude Multi-Agent System Control Panel"
echo "=========================================="
echo ""
echo "1) Start MCP Server"
echo "2) Start all agents"
echo "3) Start specific agent"
echo "4) Stop all agents"
echo "5) Stop MCP Server"
echo "6) Monitor system"
echo "7) View shared context log"
echo "8) Reset system"
echo "9) Exit"
echo ""

read -p "Choice: " choice

case $choice in
    1)
        tmux new-session -d -s mcp-server "$PROJECT_DIR/start_mcp_server.sh"
        echo "✅ MCP Server started"
        ;;
    2)
        "$PROJECT_DIR/start_all_agents.sh"
        ;;
    3)
        echo "Enter agent name (backend-api, database, frontend-ui, testing, supervisor):"
        read agent_name
        "$PROJECT_DIR/start_agent.sh" "$agent_name"
        ;;
    4)
        tmux list-sessions | grep claude- | cut -d: -f1 | xargs -I {} tmux kill-session -t {}
        echo "✅ All agents stopped"
        ;;
    5)
        tmux kill-session -t mcp-server 2>/dev/null
        pkill -f "mcp_server_complete.py"
        echo "✅ MCP Server stopped"
        ;;
    6)
        "$PROJECT_DIR/monitor_system.sh"
        ;;
    7)
        tail -f /tmp/mcp_shared_context.log
        ;;
    8)
        echo "⚠️  This will reset all data. Continue? (y/n)"
        read confirm
        if [ "$confirm" = "y" ]; then
            rm -f /tmp/mcp_state.db /tmp/mcp_shared_context.log
            echo "✅ System reset"
        fi
        ;;
    9)
        exit 0
        ;;
esac
CONTROL

chmod +x "$PROJECT_DIR/control_system.sh"

# 9. Display final instructions
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    ✨ SETUP COMPLETE!                          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📋 QUICK START:${NC}"
echo -e "  1. Start all agents:  ${YELLOW}./start_all_agents.sh${NC}"
echo -e "  2. Monitor system:    ${YELLOW}./monitor_system.sh${NC}"
echo -e "  3. Control panel:     ${YELLOW}./control_system.sh${NC}"
echo ""
echo -e "${BLUE}🔧 MCP TOOLS AVAILABLE IN CLAUDE:${NC}"
echo -e "  • log_activity       - Log activities"
echo -e "  • check_conflicts    - Check for conflicts"
echo -e "  • register_component - Register components"
echo -e "  • update_status      - Update agent status"
echo -e "  • request_collaboration - Request help"
echo -e "  • propose_decision   - Propose decisions"
echo -e "  • heartbeat         - Keep alive signal"
echo ""
echo -e "${BLUE}📊 MONITORING:${NC}"
echo -e "  • MCP Server logs:   ${YELLOW}tmux attach -t mcp-server${NC}"
echo -e "  • Shared context:    ${YELLOW}tail -f /tmp/mcp_shared_context.log${NC}"
echo -e "  • Database:          ${YELLOW}sqlite3 /tmp/mcp_state.db${NC}"
echo ""
echo -e "${BLUE}🤖 CONNECT TO AGENTS:${NC}"
echo -e "  • ${YELLOW}tmux attach -t claude-backend-api${NC}"
echo -e "  • ${YELLOW}tmux attach -t claude-database${NC}"
echo -e "  • ${YELLOW}tmux attach -t claude-frontend-ui${NC}"
echo -e "  • ${YELLOW}tmux attach -t claude-testing${NC}"
echo -e "  • ${YELLOW}tmux attach -t claude-supervisor${NC}"
echo ""
echo -e "${GREEN}✅ System is ready for multi-agent coordination!${NC}"