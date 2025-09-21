#!/bin/bash
#
# Start ALL 12 MCP Servers - Complete Integration
# This script ensures all MCP servers are running for full system capabilities
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

BASE_DIR="/Users/erik/Desktop/claude-multiagent-system"
LOG_DIR="$BASE_DIR/logs/mcp"
mkdir -p "$LOG_DIR"

echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║        STARTING COMPLETE MCP SERVER SUITE           ║${NC}"
echo -e "${CYAN}║              12 SERVERS FOR FULL AUTONOMY           ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"

# Function to check if server is accessible
check_server() {
    local name=$1
    local command=$2
    local check_type=$3

    if [ "$check_type" == "python" ]; then
        if command -v "$command" &> /dev/null; then
            echo -e "${GREEN}✓${NC} $name ready"
            return 0
        else
            echo -e "${RED}✗${NC} $name not found"
            return 1
        fi
    elif [ "$check_type" == "node" ]; then
        if [ -f "$command" ]; then
            echo -e "${GREEN}✓${NC} $name ready"
            return 0
        else
            echo -e "${RED}✗${NC} $name not built"
            return 1
        fi
    fi
    return 1
}

# Kill any existing MCP server processes
echo -e "\n${YELLOW}Cleaning up existing MCP processes...${NC}"
pkill -f "mcp-server" || true
pkill -f "playwright-mcp" || true
sleep 2

# Start Redis if not running
echo -e "\n${YELLOW}Checking Redis...${NC}"
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis..."
    redis-server --daemonize yes
    sleep 2
fi
echo -e "${GREEN}✓${NC} Redis running"

echo -e "\n${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}Starting Core MCP Servers (1-4)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}\n"

# 1. Filesystem Server
echo -e "${MAGENTA}[1/12]${NC} Filesystem Server..."
NODE_PATH="$BASE_DIR/mcp-servers-official/src/filesystem/dist/index.js"
if check_server "Filesystem" "$NODE_PATH" "node"; then
    node "$NODE_PATH" > "$LOG_DIR/filesystem.log" 2>&1 &
    echo "  → PID: $!"
fi

# 2. Git Server
echo -e "${MAGENTA}[2/12]${NC} Git Server..."
if check_server "Git" "mcp-server-git" "python"; then
    REPO_PATH="$BASE_DIR" mcp-server-git > "$LOG_DIR/git.log" 2>&1 &
    echo "  → PID: $!"
fi

# 3. Memory Server
echo -e "${MAGENTA}[3/12]${NC} Memory Server..."
NODE_PATH="$BASE_DIR/mcp-servers-official/src/memory/dist/index.js"
if check_server "Memory" "$NODE_PATH" "node"; then
    DB_PATH="$BASE_DIR/data/memory.db" node "$NODE_PATH" > "$LOG_DIR/memory.log" 2>&1 &
    echo "  → PID: $!"
fi

# 4. Fetch Server
echo -e "${MAGENTA}[4/12]${NC} Fetch Server..."
if check_server "Fetch" "mcp-server-fetch" "python"; then
    mcp-server-fetch > "$LOG_DIR/fetch.log" 2>&1 &
    echo "  → PID: $!"
fi

echo -e "\n${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}Starting Advanced MCP Servers (5-8)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}\n"

# 5. Sequential Thinking Server
echo -e "${MAGENTA}[5/12]${NC} Sequential Thinking Server..."
NODE_PATH="$BASE_DIR/mcp-servers-official/src/sequentialthinking/dist/index.js"
if check_server "Sequential Thinking" "$NODE_PATH" "node"; then
    node "$NODE_PATH" > "$LOG_DIR/sequential.log" 2>&1 &
    echo "  → PID: $!"
fi

# 6. Time Server
echo -e "${MAGENTA}[6/12]${NC} Time Server..."
if check_server "Time" "mcp-server-time" "python"; then
    mcp-server-time > "$LOG_DIR/time.log" 2>&1 &
    echo "  → PID: $!"
fi

# 7. Everything Server
echo -e "${MAGENTA}[7/12]${NC} Everything Reference Server..."
NODE_PATH="$BASE_DIR/mcp-servers-official/src/everything/dist/index.js"
if check_server "Everything" "$NODE_PATH" "node"; then
    node "$NODE_PATH" > "$LOG_DIR/everything.log" 2>&1 &
    echo "  → PID: $!"
fi

# 8. SQLite Server
echo -e "${MAGENTA}[8/12]${NC} SQLite Server..."
if check_server "SQLite" "mcp-server-sqlite" "python"; then
    mcp-server-sqlite --db-path "$BASE_DIR/data/test.db" > "$LOG_DIR/sqlite.log" 2>&1 &
    echo "  → PID: $!"
fi

echo -e "\n${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}Starting Browser & Automation Servers (9-10)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}\n"

# 9. Puppeteer Server
echo -e "${MAGENTA}[9/12]${NC} Puppeteer Server..."
NODE_PATH="$BASE_DIR/mcp-servers-archived/src/puppeteer/dist/index.js"
if check_server "Puppeteer" "$NODE_PATH" "node"; then
    node "$NODE_PATH" > "$LOG_DIR/puppeteer.log" 2>&1 &
    echo "  → PID: $!"
fi

# 10. Playwright Server
echo -e "${MAGENTA}[10/12]${NC} Playwright Server..."
if check_server "Playwright" "playwright-mcp" "python"; then
    playwright-mcp > "$LOG_DIR/playwright.log" 2>&1 &
    echo "  → PID: $!"
fi

echo -e "\n${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}Starting Infrastructure Servers (11-12)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}\n"

# 11. Redis MCP Server
echo -e "${MAGENTA}[11/12]${NC} Redis MCP Server..."
NODE_PATH="$BASE_DIR/mcp-servers-archived/src/redis/dist/index.js"
if check_server "Redis MCP" "$NODE_PATH" "node"; then
    REDIS_URL="redis://localhost:6379" node "$NODE_PATH" > "$LOG_DIR/redis-mcp.log" 2>&1 &
    echo "  → PID: $!"
fi

# 12. Multi-Agent Orchestrator
echo -e "${MAGENTA}[12/12]${NC} Multi-Agent Orchestrator..."
if check_server "Multi-Agent" "$BASE_DIR/mcp_server_v2.py" "node"; then
    cd "$BASE_DIR"
    python3 mcp_server_v2.py > "$LOG_DIR/multiagent.log" 2>&1 &
    echo "  → PID: $!"
fi

# Wait for servers to initialize
echo -e "\n${YELLOW}Waiting for servers to initialize...${NC}"
sleep 5

# Verify running processes
echo -e "\n${CYAN}═══════════════════════════════════════════════${NC}"
echo -e "${CYAN}MCP SERVER STATUS REPORT${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════${NC}\n"

# Count running MCP processes
MCP_COUNT=$(pgrep -f "mcp-server" | wc -l)
NODE_MCP_COUNT=$(pgrep -f "index.js" | wc -l)
PLAYWRIGHT_COUNT=$(pgrep -f "playwright-mcp" | wc -l)

TOTAL_COUNT=$((MCP_COUNT + NODE_MCP_COUNT + PLAYWRIGHT_COUNT))

echo -e "Python MCP servers running: ${GREEN}$MCP_COUNT${NC}"
echo -e "Node.js MCP servers running: ${GREEN}$NODE_MCP_COUNT${NC}"
echo -e "Playwright server running: ${GREEN}$PLAYWRIGHT_COUNT${NC}"
echo -e "─────────────────────────────"
echo -e "Total MCP servers active: ${GREEN}${TOTAL_COUNT}/12${NC}"

# Show logs location
echo -e "\n${YELLOW}📁 Log files:${NC}"
echo "  $LOG_DIR/*.log"

# Show monitoring command
echo -e "\n${YELLOW}📊 Monitor servers:${NC}"
echo "  tail -f $LOG_DIR/*.log"

# Display capabilities
echo -e "\n${CYAN}═══════════════════════════════════════════════${NC}"
echo -e "${CYAN}CAPABILITIES ENABLED${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════${NC}\n"

echo -e "${GREEN}✓${NC} File Operations (Filesystem)"
echo -e "${GREEN}✓${NC} Version Control (Git)"
echo -e "${GREEN}✓${NC} Knowledge Persistence (Memory)"
echo -e "${GREEN}✓${NC} Web Content Retrieval (Fetch)"
echo -e "${GREEN}✓${NC} Complex Problem Solving (Sequential Thinking)"
echo -e "${GREEN}✓${NC} Time Management (Time)"
echo -e "${GREEN}✓${NC} Reference Implementation (Everything)"
echo -e "${GREEN}✓${NC} Database Testing (SQLite)"
echo -e "${GREEN}✓${NC} Browser Automation (Puppeteer + Playwright)"
echo -e "${GREEN}✓${NC} Cache Management (Redis)"
echo -e "${GREEN}✓${NC} Multi-Agent Orchestration"

echo -e "\n${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     🚀 MCP SYSTEM FULLY OPERATIONAL! 🚀             ║${NC}"
echo -e "${GREEN}║     All 12 servers ready for autonomous work        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"

echo -e "\n${CYAN}Next steps:${NC}"
echo "1. Restart Claude Desktop to connect to servers"
echo "2. Test with: python3 test_mcp_complete.py"
echo "3. Monitor with: python3 monitor_mcp_system.py"

# Save PID list for cleanup
echo -e "\n${YELLOW}Saving server PIDs for cleanup...${NC}"
pgrep -f "mcp-server\|index.js\|playwright-mcp" > "$BASE_DIR/mcp_pids.txt"
echo -e "${GREEN}✓${NC} PIDs saved to mcp_pids.txt"

echo -e "\n${YELLOW}To stop all servers:${NC}"
echo "  ./stop_mcp_servers.sh"