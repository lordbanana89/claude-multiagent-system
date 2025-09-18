#!/bin/bash
# Agent Manager - Script principale per gestione agenti con istruzioni automatiche

set -euo pipefail

PROJECT_ROOT="/Users/erik/Desktop/riona_ai/riona-ai"
cd "$PROJECT_ROOT"

# Percorso corretto di tmux
TMUX="/opt/homebrew/bin/tmux"

INITIALIZER_SCRIPT=".riona/agents/scripts/agent-initializer.sh"
ORCHESTRATOR_SCRIPT="./claude-orchestrator.sh"

# Colori
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Controlla se jq è installato
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}Warning: jq is not installed${NC}"
    echo "Some features may not work properly"
    echo "Install with: brew install jq"
fi

# Funzione per avviare sessioni tmux se non esistono
ensure_agent_sessions() {
    local agents=("backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")
    
    echo -e "${BLUE}Ensuring all agent sessions are running...${NC}"
    
    for agent in "${agents[@]}"; do
        if ! $TMUX has-session -t "$agent" 2>/dev/null; then
            echo -e "${YELLOW}Creating session: $agent${NC}"
            $TMUX new-session -d -s "$agent" -c "$PROJECT_ROOT"
            sleep 1
        else
            echo -e "${GREEN}Session exists: $agent${NC}"
        fi
    done
}

# Funzione per inizializzare agenti senza jq
simple_init_agents() {
    echo -e "${BLUE}Initializing all agents with basic setup...${NC}"
    
    local agents=("backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")
    
    for agent in "${agents[@]}"; do
        echo -e "${BLUE}Initializing $agent...${NC}"
        
        # Avvia bash nella sessione
        $TMUX send-keys -t "$agent" 'bash' Enter
        sleep 1
        
        # Imposta il working directory
        $TMUX send-keys -t "$agent" "cd $PROJECT_ROOT" Enter
        sleep 0.5
        
        # Banner di inizializzazione
        $TMUX send-keys -t "$agent" "clear" Enter
        $TMUX send-keys -t "$agent" "echo '═══════════════════════════════════════'" Enter
        $TMUX send-keys -t "$agent" "echo '🤖 $agent Agent Terminal'" Enter
        $TMUX send-keys -t "$agent" "echo '═══════════════════════════════════════'" Enter
        $TMUX send-keys -t "$agent" "echo 'Status: ✅ Initialized'" Enter
        $TMUX send-keys -t "$agent" "echo 'Project: RIONA AI'" Enter
        $TMUX send-keys -t "$agent" "echo 'Ready for commands...'" Enter
        $TMUX send-keys -t "$agent" "echo '═══════════════════════════════════════'" Enter
        $TMUX send-keys -t "$agent" "echo ''" Enter
        
        echo -e "${GREEN}✅ $agent initialized${NC}"
    done
}

# Funzione per setup completo
full_setup() {
    echo -e "${YELLOW}=== RIONA AI AGENT SYSTEM SETUP ===${NC}"
    echo ""
    
    # 1. Assicura che le sessioni tmux esistano
    ensure_agent_sessions
    echo ""
    
    # 2. Inizializza tutti gli agenti
    if command -v jq &> /dev/null && [ -f "$INITIALIZER_SCRIPT" ]; then
        echo -e "${BLUE}Initializing all agents with specific roles...${NC}"
        # Correggi anche agent-initializer.sh per usare il percorso tmux corretto
        sed -i.bak "s|tmux |$TMUX |g" "$INITIALIZER_SCRIPT" 2>/dev/null || true
        "$INITIALIZER_SCRIPT" init-all
    else
        echo -e "${BLUE}Using simple initialization...${NC}"
        simple_init_agents
    fi
    echo ""
    
    # 3. Verifica stato
    echo -e "${BLUE}Checking final status...${NC}"
    agent_status
    echo ""
    
    echo -e "${GREEN}=== SETUP COMPLETED ===${NC}"
    echo -e "${GREEN}All agents are now initialized!${NC}"
    echo ""
    echo "Next steps:"
    echo "- Use: $0 test - Test all agents"
    echo "- Use: $0 orchestrate - Run orchestrator commands"  
    echo "- Use: $0 status - Check agent status"
}

# Funzione per status degli agenti
agent_status() {
    echo -e "${GREEN}Agent Status Check${NC}"
    echo "=================="
    
    local agents=("backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")
    
    for agent in "${agents[@]}"; do
        if $TMUX has-session -t "$agent" 2>/dev/null; then
            echo -e "${GREEN}✅ $agent${NC} - Active"
        else
            echo -e "${RED}❌ $agent${NC} - Not found"
        fi
    done
}

# Funzione per test rapido
quick_test() {
    echo -e "${BLUE}Testing all agents...${NC}"
    "$ORCHESTRATOR_SCRIPT" broadcast "echo 'Agent responding: OK'" 3
}

# Funzione per reinizializzazione dopo riavvio
auto_recover() {
    echo -e "${YELLOW}Auto-recovery mode - Reinitializing agents after restart${NC}"
    
    ensure_agent_sessions
    sleep 2
    
    simple_init_agents
    
    echo -e "${GREEN}Auto-recovery completed!${NC}"
}

# Menu principale
show_menu() {
    echo -e "${YELLOW}RIONA AI - Multi-Agent System Manager${NC}"
    echo "====================================="
    echo "1. Full Setup (first time or after restart)"
    echo "2. Test all agents"
    echo "3. Reinitialize all agents"
    echo "4. Check agent status"
    echo "5. Run orchestrator"
    echo "6. Auto-recovery (after system restart)"
    echo "7. Attach to agent session"
    echo "0. Exit"
    echo "====================================="
}

# Main
case "${1:-}" in
    "setup"|"init")
        full_setup
        ;;
    "test")
        quick_test
        ;;
    "recover"|"auto-recover")
        auto_recover
        ;;
    "reinit")
        ensure_agent_sessions
        simple_init_agents
        ;;
    "status")
        agent_status
        ;;
    "orchestrate")
        shift
        "$ORCHESTRATOR_SCRIPT" "$@"
        ;;
    "sessions")
        ensure_agent_sessions
        ;;
    "attach")
        agent="${2:-backend-api}"
        echo "Attaching to $agent session..."
        echo "Press Ctrl+B then D to detach"
        $TMUX attach-session -t "$agent"
        ;;
    "menu")
        show_menu
        read -p "Select option: " choice
        case $choice in
            1) full_setup ;;
            2) quick_test ;;
            3) 
                ensure_agent_sessions
                simple_init_agents
                ;;
            4) agent_status ;;
            5) 
                echo "Available commands: test, broadcast, send, status"
                read -p "Orchestrator command: " cmd
                "$ORCHESTRATOR_SCRIPT" $cmd
                ;;
            6) auto_recover ;;
            7)
                read -p "Agent name (default: backend-api): " agent
                agent="${agent:-backend-api}"
                $TMUX attach-session -t "$agent"
                ;;
            0) echo "Exiting..."; exit 0 ;;
            *) echo "Invalid option" ;;
        esac
        ;;
    *)
        echo "RIONA AI Multi-Agent System Manager"
        echo ""
        echo "Usage: $0 <command> [args]"
        echo ""
        echo "Commands:"
        echo "  setup              Full setup (first time or after restart)"
        echo "  test               Test all agents" 
        echo "  recover            Auto-recovery after system restart"
        echo "  reinit             Reinitialize all agents"
        echo "  status             Check all agents status"
        echo "  orchestrate <cmd>  Run orchestrator commands"
        echo "  sessions           Ensure all tmux sessions exist"
        echo "  attach [agent]     Attach to agent session"
        echo "  menu               Interactive menu"
        echo ""
        echo "Examples:"
        echo "  $0 setup                    # First time setup"
        echo "  $0 test                     # Test all agents"
        echo "  $0 orchestrate broadcast 'pwd'  # Broadcast command"
        echo "  $0 recover                  # After system restart"
        echo "  $0 attach backend-api       # Attach to backend agent"
        ;;
esac