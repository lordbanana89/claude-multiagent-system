#!/bin/bash

# 🔧 System Reset Script for Claude Multi-Agent System
# Pulisce e resetta il sistema in uno stato pulito

set -e

echo "🔧 Claude Multi-Agent System - Reset Completo"
echo "============================================="

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Kill all Python processes related to the project
echo -e "${YELLOW}[1/6] Fermando processi Python del progetto...${NC}"
pkill -f "mcp_api_server.py" 2>/dev/null || true
pkill -f "mcp_server_complete.py" 2>/dev/null || true
pkill -f "mcp_bridge.py" 2>/dev/null || true
pkill -f "claude_monitor.py" 2>/dev/null || true
pkill -f "streamlit" 2>/dev/null || true
pkill -f "dramatiq" 2>/dev/null || true
echo -e "${GREEN}✓ Processi Python fermati${NC}"

# 2. Kill Overmind if running
echo -e "${YELLOW}[2/6] Fermando Overmind...${NC}"
if [ -f .overmind.sock ]; then
    overmind kill 2>/dev/null || true
    rm -f .overmind.sock
    echo -e "${GREEN}✓ Overmind fermato${NC}"
else
    echo "  Overmind non attivo"
fi

# 3. Clean TMUX sessions
echo -e "${YELLOW}[3/6] Pulizia sessioni TMUX...${NC}"
SESSIONS=(
    "claude-supervisor"
    "claude-master"
    "claude-backend-api"
    "claude-database"
    "claude-frontend-ui"
    "claude-instagram"
    "claude-testing"
    "claude-queue-manager"
    "claude-deployment"
    "claude-supervisor-agent"
    "claude-backend-api-agent"
    "claude-database-agent"
    "claude-instagram-agent"
    "claude-shared-context"
    "claude-test-agent"
    "claude-demo-backend"
    "claude-demo-database"
    "mcp-server"
)

for session in "${SESSIONS[@]}"; do
    if tmux has-session -t "$session" 2>/dev/null; then
        tmux kill-session -t "$session"
        echo "  ✓ Rimossa sessione: $session"
    fi
done
echo -e "${GREEN}✓ Sessioni TMUX pulite${NC}"

# 4. Clean Redis data (optional - ask user)
echo -e "${YELLOW}[4/6] Redis cleanup...${NC}"
if redis-cli ping > /dev/null 2>&1; then
    read -p "Vuoi pulire i dati Redis? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        redis-cli FLUSHDB > /dev/null
        echo -e "${GREEN}✓ Redis database pulito${NC}"
    else
        echo "  Redis mantenuto"
    fi
else
    echo "  Redis non attivo"
fi

# 5. Clean temporary files and logs
echo -e "${YELLOW}[5/6] Pulizia file temporanei...${NC}"
rm -f /tmp/mcp_*.log
rm -f /tmp/claude_*.log
rm -f logs/*.log 2>/dev/null || true
rm -f dump.rdb 2>/dev/null || true
rm -f .overmind.sock 2>/dev/null || true
echo -e "${GREEN}✓ File temporanei rimossi${NC}"

# 6. Reset shared state
echo -e "${YELLOW}[6/6] Reset shared state...${NC}"
if [ -f langgraph-test/shared_state.json ]; then
    cp langgraph-test/shared_state.json langgraph-test/shared_state.json.backup.$(date +%Y%m%d_%H%M%S)
    echo '{"agents": {}, "tasks": {}, "messages": []}' > langgraph-test/shared_state.json
    echo -e "${GREEN}✓ Shared state resettato (backup creato)${NC}"
else
    echo "  Shared state non trovato"
fi

echo
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Reset Completato!${NC}"
echo -e "${GREEN}========================================${NC}"
echo
echo "Prossimi passi:"
echo "1. Avvia il sistema con: overmind start"
echo "2. Oppure usa: ./scripts/start_complete_system.sh"
echo "3. Verifica con: ./scripts/system_health_check.sh"