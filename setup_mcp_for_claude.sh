#!/bin/bash

# Setup MCP for Claude Code CLI
echo "🚀 Configurazione MCP per Claude Multi-Agent System"
echo "===================================================="

PROJECT_DIR="/Users/erik/Desktop/claude-multiagent-system"
CLAUDE_CONFIG="$HOME/.claude/config/.claude.json"

# 1. Backup della configurazione esistente
echo "📦 Backup configurazione esistente..."
cp "$CLAUDE_CONFIG" "$CLAUDE_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"

# 2. Aggiorna configurazione Claude con MCP
echo "⚙️ Aggiornamento configurazione Claude..."

# Usa Python per modificare JSON in modo sicuro
python3 << EOF
import json

config_path = "$CLAUDE_CONFIG"

# Leggi configurazione esistente
with open(config_path, 'r') as f:
    config = json.load(f)

# Aggiungi configurazione MCP per il progetto
if "projects" not in config:
    config["projects"] = {}

project_path = "$PROJECT_DIR"
if project_path not in config["projects"]:
    config["projects"][project_path] = {}

# Configura MCP servers per il progetto
config["projects"][project_path]["mcpServers"] = {
    "shared-context": {
        "command": "python3",
        "args": ["$PROJECT_DIR/mcp_coordinator_server.py"],
        "env": {},
        "name": "Claude Multi-Agent Coordinator",
        "description": "Shared context and coordination for multi-agent system"
    }
}

# Abilita MCP per il progetto
config["projects"][project_path]["enabledMcpjsonServers"] = ["shared-context"]

# Scrivi configurazione aggiornata
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("✅ Configurazione aggiornata con successo!")
EOF

# 3. Avvia MCP Server in background
echo ""
echo "🔧 Avvio MCP Coordinator Server..."

# Kill existing server if running
pkill -f "mcp_coordinator_server.py" 2>/dev/null

# Start in background with nohup
nohup python3 "$PROJECT_DIR/mcp_coordinator_server.py" > /tmp/mcp_server.log 2>&1 &
MCP_PID=$!

echo "✅ MCP Server avviato (PID: $MCP_PID)"
echo "   Log: tail -f /tmp/mcp_server.log"

# 4. Test della connessione
echo ""
echo "🧪 Test connessione MCP..."
sleep 2

if ps -p $MCP_PID > /dev/null; then
    echo "✅ MCP Server è attivo!"
else
    echo "❌ MCP Server non è partito. Controlla i log."
    exit 1
fi

# 5. Istruzioni per gli agenti
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✨ SETUP COMPLETATO!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📋 PROSSIMI PASSI:"
echo ""
echo "1. Avvia gli agenti Claude nei terminali TMUX:"
echo "   tmux new-session -d -s claude-backend-api"
echo "   tmux send-keys -t claude-backend-api 'cd $PROJECT_DIR && claude' Enter"
echo ""
echo "2. Gli agenti ora hanno accesso ai tools MCP:"
echo "   - log_activity: per loggare attività"
echo "   - check_conflicts: per verificare conflitti"
echo "   - get_agent_status: per vedere altri agenti"
echo "   - register_component: per registrare componenti"
echo "   - coordinate_decision: per decisioni condivise"
echo ""
echo "3. Monitora il contesto condiviso:"
echo "   tail -f /tmp/mcp_shared_context.log"
echo ""
echo "4. Verifica server MCP:"
echo "   ps aux | grep mcp_coordinator"
echo ""
echo "════════════════════════════════════════════════════════════════"

# 6. Crea script helper per avviare agenti
cat > "$PROJECT_DIR/start_claude_agent.sh" << 'SCRIPT'
#!/bin/bash
# Helper script per avviare un agente Claude con MCP

AGENT_NAME="${1:-backend-api}"
PROJECT_DIR="/Users/erik/Desktop/claude-multiagent-system"

echo "🚀 Avvio agente Claude: $AGENT_NAME"

# Kill sessione esistente se presente
tmux kill-session -t "claude-$AGENT_NAME" 2>/dev/null

# Crea nuova sessione
tmux new-session -d -s "claude-$AGENT_NAME"

# Vai alla directory del progetto
tmux send-keys -t "claude-$AGENT_NAME" "cd $PROJECT_DIR" Enter

# Avvia Claude (MCP si configura automaticamente per questo progetto)
tmux send-keys -t "claude-$AGENT_NAME" "claude" Enter

echo "✅ Agente avviato: claude-$AGENT_NAME"
echo "   Connetti con: tmux attach -t claude-$AGENT_NAME"
SCRIPT

chmod +x "$PROJECT_DIR/start_claude_agent.sh"

echo ""
echo "💡 Script helper creato: ./start_claude_agent.sh [nome-agente]"
echo "   Esempio: ./start_claude_agent.sh backend-api"