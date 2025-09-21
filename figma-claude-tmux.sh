#!/bin/bash

# Figma Claude TMUX Session Manager
# Crea una sessione TMUX persistente per task Figma lunghi

SESSION_NAME="figma-claude"
FIGMA_DIR="/Users/erik/Desktop/claude-multiagent-system/figma-mcp-complete"

# Colori
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   FIGMA CLAUDE TMUX SESSION MANAGER   ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════╝${NC}"

# Controlla se la sessione esiste già
if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo -e "${GREEN}✓ Sessione esistente trovata!${NC}"
    echo "Attaching to session..."
    tmux attach-session -t $SESSION_NAME
else
    echo -e "${BLUE}Creating new TMUX session: $SESSION_NAME${NC}"

    # Crea nuova sessione con 3 finestre
    tmux new-session -d -s $SESSION_NAME -n "websocket"
    tmux new-window -t $SESSION_NAME:2 -n "mcp-server"
    tmux new-window -t $SESSION_NAME:3 -n "figma-logs"

    # Window 1: WebSocket Server
    tmux send-keys -t $SESSION_NAME:1 "cd $FIGMA_DIR" C-m
    tmux send-keys -t $SESSION_NAME:1 "echo '🚀 WebSocket Server (Port 3055)'" C-m
    tmux send-keys -t $SESSION_NAME:1 "~/.bun/bin/bun run dist/socket.js" C-m

    # Window 2: MCP Server (for manual testing)
    tmux send-keys -t $SESSION_NAME:2 "cd $FIGMA_DIR" C-m
    tmux send-keys -t $SESSION_NAME:2 "echo '🤖 MCP Server Terminal'" C-m
    tmux send-keys -t $SESSION_NAME:2 "echo 'Run: node dist/talk_to_figma_mcp/server.js'" C-m

    # Window 3: Logs & Monitoring
    tmux send-keys -t $SESSION_NAME:3 "cd $FIGMA_DIR" C-m
    tmux send-keys -t $SESSION_NAME:3 "echo '📊 Monitoring Figma Operations'" C-m
    tmux send-keys -t $SESSION_NAME:3 "tail -f /tmp/figma-claude.log 2>/dev/null || echo 'Log file will appear when operations start'" C-m

    echo -e "${GREEN}✓ Session created with 3 windows:${NC}"
    echo "  1. WebSocket Server (Port 3055)"
    echo "  2. MCP Server Terminal"
    echo "  3. Logs & Monitoring"
    echo ""
    echo -e "${BLUE}Commands:${NC}"
    echo "  Attach: tmux attach -t $SESSION_NAME"
    echo "  Detach: Ctrl+B, D"
    echo "  Switch windows: Ctrl+B, [0-3]"
    echo "  Kill session: tmux kill-session -t $SESSION_NAME"
    echo ""
    echo -e "${GREEN}Attaching to session...${NC}"
    sleep 1
    tmux attach-session -t $SESSION_NAME
fi