#!/bin/bash
# Initialize Existing Sessions - Converte sessioni tmux esistenti in agenti Claude Code

set -euo pipefail

PROJECT_ROOT="/Users/erik/Desktop/riona_ai/riona-ai"
AGENTS_DIR="$PROJECT_ROOT/.riona/agents"
CONFIGS_DIR="$AGENTS_DIR/configs"

# Colori
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

unset TMUX 2>/dev/null || true
TMUX_BIN="/opt/homebrew/bin/tmux"

# Lista delle sessioni target
AGENTS=("backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")

# Funzione per inizializzare una sessione esistente
initialize_session() {
    local agent_name="$1"
    local config_file="$CONFIGS_DIR/$agent_name.json"

    if [ ! -f "$config_file" ]; then
        echo -e "${RED}Config not found: $config_file${NC}"
        return 1
    fi

    # Verifica se la sessione esiste
    if ! $TMUX_BIN has-session -t "$agent_name" 2>/dev/null; then
        echo -e "${RED}Session $agent_name not found. Creating...${NC}"
        $TMUX_BIN new-session -d -s "$agent_name" -c "$PROJECT_ROOT"
    fi

    echo -e "${BLUE}Initializing $agent_name session with Claude Code...${NC}"

    # Pulisce la sessione
    $TMUX_BIN send-keys -t "$agent_name" "clear" Enter
    sleep 1

    # Avvia Claude Code nella sessione
    $TMUX_BIN send-keys -t "$agent_name" "claude-code" Enter
    sleep 3

    # Invia il contesto iniziale dell'agente
    local role=$(jq -r '.role' "$config_file")
    local description=$(jq -r '.description' "$config_file")
    local responsibilities=$(jq -r '.responsibilities | join(", ")' "$config_file")
    local expertise=$(jq -r '.expertise | join(", ")' "$config_file")

    local initialization_prompt="I am now the $role agent for the Riona AI Instagram automation platform.

My role: $role
Description: $description
Responsibilities: $responsibilities
Expertise: $expertise

I am ready to receive and respond to specialized tasks within my domain. I will provide technical analysis, implementation approaches, and coordinate with other agents as needed.

Please acknowledge that I am ready as the $role agent."

    # Invia l'inizializzazione
    printf '%s\n' "$initialization_prompt" | $TMUX_BIN load-buffer -
    $TMUX_BIN paste-buffer -t "$agent_name"
    $TMUX_BIN send-keys -t "$agent_name" Enter

    echo -e "${GREEN}✅ $agent_name session initialized with Claude Code${NC}"
}

# Funzione per inizializzare tutte le sessioni
initialize_all_sessions() {
    echo -e "${YELLOW}Initializing all existing sessions with Claude Code...${NC}"
    echo "================================================="

    for agent in "${AGENTS[@]}"; do
        initialize_session "$agent"
        echo ""
        sleep 2
    done

    echo -e "${GREEN}All sessions initialized with Claude Code!${NC}"
    echo ""
    echo "You can now use:"
    echo "  ./claude-orchestrator.sh test"
    echo "  ./claude-orchestrator.sh send <agent> <task>"
}

# Funzione per verificare lo stato delle sessioni
check_sessions_status() {
    echo -e "${YELLOW}Session Status Check${NC}"
    echo "==================="

    for agent in "${AGENTS[@]}"; do
        if $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
            echo -e "${GREEN}✅ $agent${NC} - Session active"
            # Test se Claude Code è in esecuzione
            local output=$($TMUX_BIN capture-pane -t "$agent" -p | tail -3)
            if echo "$output" | grep -q "claude-code\|Claude"; then
                echo -e "   ${BLUE}Claude Code appears to be running${NC}"
            else
                echo -e "   ${YELLOW}May need Claude Code initialization${NC}"
            fi
        else
            echo -e "${RED}❌ $agent${NC} - Session not found"
        fi
    done
}

# Main
case "${1:-}" in
    "init-all")
        initialize_all_sessions
        ;;
    "init")
        if [ -z "${2:-}" ]; then
            echo "Usage: $0 init <agent_name>"
            exit 1
        fi
        initialize_session "$2"
        ;;
    "status")
        check_sessions_status
        ;;
    *)
        echo "Initialize Existing Sessions with Claude Code"
        echo "==========================================="
        echo ""
        echo "Usage: $0 <command> [args]"
        echo ""
        echo "Commands:"
        echo "  init-all           Initialize all existing sessions with Claude Code"
        echo "  init <agent>       Initialize specific session"
        echo "  status             Check sessions status"
        echo ""
        echo "Available sessions: backend-api, database, frontend-ui, instagram, queue-manager, testing, deployment"
        echo ""
        echo "After initialization, use:"
        echo "  ./claude-orchestrator.sh test"
        echo "  ./claude-orchestrator.sh send <agent> <task>"
        exit 1
        ;;
esac