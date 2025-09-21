#!/bin/bash

# MCP v2 Agent Terminal Startup Script
# Starts ttyd terminals for all agents with MCP v2 integration

echo "╔══════════════════════════════════════╗"
echo "║   MCP v2 Agent Terminal Manager      ║"
echo "╚══════════════════════════════════════╝"

# Configuration
MCP_SERVER="http://localhost:8099"
MCP_WEBSOCKET="ws://localhost:8100"
BASE_DIR="/Users/erik/Desktop/claude-multiagent-system"

# Define agents and their ports
declare -A AGENTS=(
    ["backend-api"]=8090
    ["database"]=8091
    ["frontend-ui"]=8092
    ["testing"]=8093
    ["instagram"]=8094
    ["supervisor"]=8095
    ["master"]=8096
    ["deployment"]=8097
    ["queue-manager"]=8098
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    lsof -i :$1 >/dev/null 2>&1
    return $?
}

# Function to kill process on port
kill_port() {
    local port=$1
    local pid=$(lsof -t -i:$port)
    if [ ! -z "$pid" ]; then
        kill -9 $pid 2>/dev/null
        echo -e "${YELLOW}Killed process on port $port${NC}"
    fi
}

# Function to create tmux session if not exists
create_tmux_session() {
    local agent=$1
    local session_name="claude-$agent"

    if ! tmux has-session -t "$session_name" 2>/dev/null; then
        echo -e "${YELLOW}Creating tmux session for $agent...${NC}"

        # Create session with proper environment
        tmux new-session -d -s "$session_name" -c "$BASE_DIR"

        # Set MCP environment variables
        tmux send-keys -t "$session_name" "export MCP_SERVER=$MCP_SERVER" Enter
        tmux send-keys -t "$session_name" "export MCP_WEBSOCKET=$MCP_WEBSOCKET" Enter
        tmux send-keys -t "$session_name" "export AGENT_NAME=$agent" Enter

        # Source any agent-specific configuration
        if [ -f "$BASE_DIR/agents/$agent/config.sh" ]; then
            tmux send-keys -t "$session_name" "source $BASE_DIR/agents/$agent/config.sh" Enter
        fi

        # Initialize MCP client for the agent
        tmux send-keys -t "$session_name" "echo '═══════════════════════════════════════'" Enter
        tmux send-keys -t "$session_name" "echo '  MCP v2 Agent Terminal: $agent'" Enter
        tmux send-keys -t "$session_name" "echo '  Server: $MCP_SERVER'" Enter
        tmux send-keys -t "$session_name" "echo '  WebSocket: $MCP_WEBSOCKET'" Enter
        tmux send-keys -t "$session_name" "echo '═══════════════════════════════════════'" Enter
        tmux send-keys -t "$session_name" "echo ''" Enter

        # Start MCP client connection
        tmux send-keys -t "$session_name" "python3 -c \"
import sys
sys.path.append('$BASE_DIR')
from mcp_client_v2 import MCPClient

client = MCPClient('$MCP_SERVER')
print(f'✓ Connected to MCP v2 server')
print(f'✓ Agent {agent} ready')
print('')
print('Available commands:')
print('  mcp.tools() - List available tools')
print('  mcp.resources() - List resources')
print('  mcp.prompts() - List prompts')
print('  mcp.call(tool, params) - Execute tool')
print('')
\"" Enter

        echo -e "${GREEN}✓ Created tmux session for $agent${NC}"
    else
        echo -e "${GREEN}✓ Tmux session for $agent already exists${NC}"
    fi
}

# Function to start ttyd terminal
start_terminal() {
    local agent=$1
    local port=$2

    # Check if port is already in use
    if check_port $port; then
        echo -e "${YELLOW}Port $port is in use, killing existing process...${NC}"
        kill_port $port
        sleep 1
    fi

    # Start ttyd
    echo -e "Starting terminal for ${GREEN}$agent${NC} on port ${GREEN}$port${NC}..."

    ttyd \
        -p $port \
        -t fontSize=14 \
        -t 'theme={"background":"#1a1a1a","foreground":"#00ff00"}' \
        -t titleFixed="MCP Agent: $agent" \
        -t enableSixel=true \
        -t enableTrzsz=true \
        -t enableZmodem=true \
        --writable \
        --once \
        tmux attach-session -t "claude-$agent" &

    sleep 0.5

    # Verify terminal started
    if check_port $port; then
        echo -e "${GREEN}✓ Terminal for $agent started on http://localhost:$port${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to start terminal for $agent${NC}"
        return 1
    fi
}

# Main execution
main() {
    echo ""
    echo "Starting MCP v2 Agent Terminals..."
    echo "═══════════════════════════════════════"

    # Check prerequisites
    echo -e "\n${YELLOW}Checking prerequisites...${NC}"

    # Check if ttyd is installed
    if ! command -v ttyd &> /dev/null; then
        echo -e "${RED}✗ ttyd is not installed${NC}"
        echo "Install with: brew install ttyd (macOS) or apt-get install ttyd (Linux)"
        exit 1
    fi

    # Check if tmux is installed
    if ! command -v tmux &> /dev/null; then
        echo -e "${RED}✗ tmux is not installed${NC}"
        echo "Install with: brew install tmux (macOS) or apt-get install tmux (Linux)"
        exit 1
    fi

    # Check if MCP server is running
    if ! curl -s $MCP_SERVER/api/mcp/status >/dev/null 2>&1; then
        echo -e "${RED}✗ MCP server is not running at $MCP_SERVER${NC}"
        echo "Start with: python3 mcp_server_v2_compliant.py"
        exit 1
    fi

    echo -e "${GREEN}✓ All prerequisites met${NC}"

    # Create tmux sessions and start terminals
    echo -e "\n${YELLOW}Starting agent terminals...${NC}"

    local success_count=0
    local fail_count=0

    for agent in "${!AGENTS[@]}"; do
        port=${AGENTS[$agent]}

        echo ""
        echo "Processing $agent..."

        # Create tmux session
        create_tmux_session "$agent"

        # Start terminal
        if start_terminal "$agent" "$port"; then
            ((success_count++))
        else
            ((fail_count++))
        fi
    done

    # Summary
    echo ""
    echo "═══════════════════════════════════════"
    echo "Terminal Startup Complete"
    echo "═══════════════════════════════════════"
    echo -e "${GREEN}✓ Successfully started: $success_count terminals${NC}"

    if [ $fail_count -gt 0 ]; then
        echo -e "${RED}✗ Failed: $fail_count terminals${NC}"
    fi

    echo ""
    echo "Access terminals at:"
    for agent in "${!AGENTS[@]}"; do
        port=${AGENTS[$agent]}
        if check_port $port; then
            echo -e "  ${GREEN}$agent${NC}: http://localhost:$port"
        fi
    done

    echo ""
    echo "Frontend Dashboard: http://localhost:5173"
    echo ""
    echo "To attach to a tmux session directly:"
    echo "  tmux attach-session -t claude-<agent-name>"
    echo ""
    echo "To stop all terminals:"
    echo "  ./stop_agent_terminals.sh"
}

# Handle script arguments
case "${1:-}" in
    stop)
        echo "Stopping all agent terminals..."
        for port in "${AGENTS[@]}"; do
            kill_port $port
        done
        echo "All terminals stopped"
        ;;
    restart)
        $0 stop
        sleep 2
        $0
        ;;
    status)
        echo "Agent Terminal Status:"
        for agent in "${!AGENTS[@]}"; do
            port=${AGENTS[$agent]}
            if check_port $port; then
                echo -e "  ${GREEN}✓${NC} $agent (port $port): Running"
            else
                echo -e "  ${RED}✗${NC} $agent (port $port): Not running"
            fi
        done
        ;;
    *)
        main
        ;;
esac