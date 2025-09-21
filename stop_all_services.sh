#!/bin/bash

# Stop all services for Claude Multi-Agent System

echo "🛑 Stopping Claude Multi-Agent System..."
echo "========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Kill processes on specific ports
ports=(5001 8888 5173)
for port in "${ports[@]}"; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping service on port $port...${NC}"
        lsof -ti :$port | xargs kill -9 2>/dev/null || true
        echo -e "${GREEN}✅ Stopped service on port $port${NC}"
    else
        echo -e "${YELLOW}No service running on port $port${NC}"
    fi
done

# Stop TMUX sessions
echo ""
echo "Stopping TMUX sessions..."
agents=("supervisor" "master" "backend-api" "database" "frontend-ui" "testing" "instagram" "queue-manager" "deployment")

for agent in "${agents[@]}"; do
    session_name="claude-$agent"
    if tmux has-session -t $session_name 2>/dev/null; then
        tmux kill-session -t $session_name
        echo -e "${GREEN}✅ Stopped TMUX session: $session_name${NC}"
    fi
done

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
echo "========================================="