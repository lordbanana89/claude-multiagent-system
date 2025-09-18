#!/bin/bash
# View Agents - Script per visualizzare e connettersi ai terminali degli agenti

set -euo pipefail

PROJECT_ROOT="/Users/erik/Desktop/riona_ai/riona-ai"
TMUX_BIN="/opt/homebrew/bin/tmux"

# Colori
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Lista agenti principali (Prompt Validator per primo)
AGENTS=("prompt-validator" "task-coordinator" "backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")

# Funzione per mostrare preview di una sessione
show_agent_preview() {
    local agent="$1"
    local lines="${2:-5}"

    if ! $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
        echo -e "${RED}❌ $agent - Session not found${NC}"
        return 1
    fi

    echo -e "${CYAN}🤖 $agent Agent Preview:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Cattura le ultime righe dell'agente
    local content=$($TMUX_BIN capture-pane -t "$agent" -p | tail -n "$lines")

    if [ -n "$content" ]; then
        echo "$content" | sed 's/^/  /'
    else
        echo -e "  ${YELLOW}(No recent activity)${NC}"
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "Connect: ${GREEN}tmux attach-session -t $agent${NC}"
    echo ""
}

# Funzione per mostrare tutti i preview
show_all_previews() {
    echo -e "${PURPLE}🎯 RIONA AI MULTI-AGENT TERMINALS OVERVIEW${NC}"
    echo "=========================================="
    echo ""

    for agent in "${AGENTS[@]}"; do
        show_agent_preview "$agent" 3
    done
}

# Funzione per monitoring real-time side-by-side
monitor_agents_grid() {
    echo -e "${CYAN}🔍 Real-Time Agent Grid Monitor${NC}"
    echo "Press Ctrl+C to exit"
    echo "==============================="
    echo ""

    while true; do
        clear
        echo -e "${PURPLE}$(date '+%Y-%m-%d %H:%M:%S') - Multi-Agent Grid Monitor${NC}"
        echo "=================================================================="

        # Mostra 4 agenti per riga
        local row1=("task-coordinator" "backend-api" "database" "frontend-ui")
        local row2=("instagram" "queue-manager" "testing" "deployment")

        # Prima riga
        printf "%-20s %-20s %-20s %-20s\n" "${row1[@]}"
        printf "%-20s %-20s %-20s %-20s\n" "──────────────────" "──────────────────" "──────────────────" "──────────────────"

        # Status prima riga
        local status1=()
        for agent in "${row1[@]}"; do
            if $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
                local last_line=$($TMUX_BIN capture-pane -t "$agent" -p | tail -1 | cut -c1-18)
                status1+=("$last_line")
            else
                status1+=("❌ Offline")
            fi
        done
        printf "%-20s %-20s %-20s %-20s\n" "${status1[@]}"

        echo ""

        # Seconda riga
        printf "%-20s %-20s %-20s %-20s\n" "${row2[@]}"
        printf "%-20s %-20s %-20s %-20s\n" "──────────────────" "──────────────────" "──────────────────" "──────────────────"

        # Status seconda riga
        local status2=()
        for agent in "${row2[@]}"; do
            if $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
                local last_line=$($TMUX_BIN capture-pane -t "$agent" -p | tail -1 | cut -c1-18)
                status2+=("$last_line")
            else
                status2+=("❌ Offline")
            fi
        done
        printf "%-20s %-20s %-20s %-20s\n" "${status2[@]}"

        echo ""
        echo -e "${YELLOW}Commands: Ctrl+C to exit, Select agent number to connect${NC}"

        sleep 2
    done
}

# Menu interattivo per connessione agenti
interactive_agent_menu() {
    echo -e "${PURPLE}🎯 AGENT CONNECTION MENU${NC}"
    echo "========================="
    echo ""

    local i=1
    for agent in "${AGENTS[@]}"; do
        if $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
            echo -e "${GREEN}$i) $agent${NC} - Active"
        else
            echo -e "${RED}$i) $agent${NC} - Offline"
        fi
        i=$((i + 1))
    done

    echo ""
    echo "0) Show all previews"
    echo "g) Grid monitor"
    echo "q) Quit"
    echo ""

    read -p "Select agent (1-8) or option: " choice

    case $choice in
        [1-8])
            local selected_agent="${AGENTS[$((choice-1))]}"
            if $TMUX_BIN has-session -t "$selected_agent" 2>/dev/null; then
                echo -e "${CYAN}🤖 Connecting to $selected_agent agent...${NC}"
                echo -e "${YELLOW}Press Ctrl+B then D to detach${NC}"
                sleep 1
                $TMUX_BIN attach-session -t "$selected_agent"
            else
                echo -e "${RED}❌ Agent $selected_agent is not active${NC}"
                read -p "Press Enter to continue..."
                interactive_agent_menu
            fi
            ;;
        0)
            show_all_previews
            read -p "Press Enter to continue..."
            interactive_agent_menu
            ;;
        g|G)
            monitor_agents_grid
            ;;
        q|Q)
            exit 0
            ;;
        *)
            echo "Invalid choice"
            interactive_agent_menu
            ;;
    esac
}

# Funzione per aprire 4 terminali separati e indipendenti collegati agli agenti
create_multi_pane_session() {
    echo -e "${CYAN}🚀 Opening 4 INDEPENDENT terminal windows for direct agent interaction...${NC}"
    echo -e "${YELLOW}Each terminal window will connect directly to a specific agent${NC}"
    echo ""

    # Verifica che gli agenti principali siano attivi
    local agents_to_show=("task-coordinator" "backend-api" "database" "frontend-ui")
    local agent_icons=("🎯" "🔧" "💾" "🎨")
    local agent_names=("TASK COORDINATOR" "BACKEND API" "DATABASE" "FRONTEND UI")

    echo -e "${BLUE}📋 Verifying agents are active...${NC}"
    for agent in "${agents_to_show[@]}"; do
        if ! $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
            echo -e "${RED}❌ Agent $agent is not active! Start agents first.${NC}"
            echo "Run: ./.riona/agents/scripts/unified-agent-startup.sh start-all"
            return 1
        fi
        echo -e "${GREEN}✅ $agent is active${NC}"
    done

    echo ""
    echo -e "${PURPLE}🚀 Launching 4 independent terminal windows...${NC}"

    # Apre 4 terminali macOS indipendenti, ognuno collegato a un agente specifico
    for i in {0..3}; do
        local agent="${agents_to_show[$i]}"
        local icon="${agent_icons[$i]}"
        local name="${agent_names[$i]}"

        echo -e "${CYAN}Opening terminal for: $icon $name${NC}"

        # Usa osascript per aprire un nuovo terminale macOS
        osascript -e "tell application \"Terminal\" to activate" \
                 -e "tell application \"Terminal\" to do script \"echo '$icon $name AGENT TERMINAL'; echo 'Direct connection to $agent agent'; echo 'You can interact directly with this agent'; echo '═══════════════════════════════════════════════'; tmux attach-session -t $agent\"" &

        # Piccola pausa tra l'apertura di ogni terminale
        sleep 1
    done

    # Aspetta che tutti i terminali si aprano
    sleep 3

    echo ""
    echo -e "${GREEN}✅ 4 INDEPENDENT agent terminals opened successfully!${NC}"
    echo ""
    echo -e "${PURPLE}🎯 OPENED TERMINAL WINDOWS:${NC}"
    echo "  • Terminal 1: 🎯 Task Coordinator Agent"
    echo "  • Terminal 2: 🔧 Backend API Agent"
    echo "  • Terminal 3: 💾 Database Agent"
    echo "  • Terminal 4: 🎨 Frontend UI Agent"
    echo ""
    echo -e "${CYAN}📋 DIRECT INTERACTION:${NC}"
    echo "  • Each terminal is COMPLETELY INDEPENDENT"
    echo "  • Type directly in any terminal to interact with that agent"
    echo "  • Perfect for manual confirmations and complex debugging"
    echo "  • Switch between terminal windows normally (Cmd+Tab, etc.)"
    echo "  • Close terminals when done (Cmd+W) - agents keep running"
    echo ""
    echo -e "${YELLOW}💡 USAGE TIPS:${NC}"
    echo "  • Each window = Direct connection to agent terminal"
    echo "  • No tmux navigation needed - they're separate windows!"
    echo "  • Ideal for parallel work and manual agent supervision"
    echo "  • Agents continue running even if you close terminal windows"
    echo ""
    echo -e "${GREEN}All terminals are now open and ready for interaction! 🚀${NC}"
}

# Funzione per aprire terminali per TUTTI gli 9 agenti
open_all_agent_terminals() {
    echo -e "${CYAN}🚀 Opening terminals for ALL 9 AGENTS...${NC}"
    echo -e "${YELLOW}Each agent gets its own independent terminal window${NC}"
    echo ""

    # Lista completa di tutti gli agenti
    local all_agents=("prompt-validator" "task-coordinator" "backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")
    local all_icons=("✅" "🎯" "🔧" "💾" "🎨" "📱" "⚙️" "🧪" "🚀")
    local all_names=("PROMPT VALIDATOR" "TASK COORDINATOR" "BACKEND API" "DATABASE" "FRONTEND UI" "INSTAGRAM" "QUEUE MANAGER" "TESTING" "DEPLOYMENT")

    echo -e "${BLUE}📋 Verifying all 9 agents are active...${NC}"
    for agent in "${all_agents[@]}"; do
        if ! $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
            echo -e "${RED}❌ Agent $agent is not active! Start agents first.${NC}"
            echo "Run: ./.riona/agents/scripts/unified-agent-startup.sh start-all"
            return 1
        fi
        echo -e "${GREEN}✅ $agent is active${NC}"
    done

    echo ""
    echo -e "${PURPLE}🚀 Launching 9 independent terminal windows...${NC}"

    # Apre tutti i 9 terminali
    for i in {0..8}; do
        local agent="${all_agents[$i]}"
        local icon="${all_icons[$i]}"
        local name="${all_names[$i]}"

        echo -e "${CYAN}Opening terminal for: $icon $name${NC}"

        # Usa osascript per aprire un nuovo terminale macOS
        osascript -e "tell application \"Terminal\" to activate" \
                 -e "tell application \"Terminal\" to do script \"echo '$icon $name AGENT TERMINAL'; echo 'Direct connection to $agent agent'; echo 'You can interact directly with this agent'; echo '═══════════════════════════════════════════════'; tmux attach-session -t $agent\"" &

        # Piccola pausa tra l'apertura di ogni terminale
        sleep 0.8
    done

    # Aspetta che tutti i terminali si aprano
    sleep 4

    echo ""
    echo -e "${GREEN}✅ ALL 9 AGENT TERMINALS opened successfully!${NC}"
    echo ""
    echo -e "${PURPLE}🎯 ALL OPENED TERMINAL WINDOWS:${NC}"
    echo "  • Terminal 1: ✅ Prompt Validator Agent"
    echo "  • Terminal 2: 🎯 Task Coordinator Agent"
    echo "  • Terminal 3: 🔧 Backend API Agent"
    echo "  • Terminal 4: 💾 Database Agent"
    echo "  • Terminal 5: 🎨 Frontend UI Agent"
    echo "  • Terminal 6: 📱 Instagram Agent"
    echo "  • Terminal 7: ⚙️ Queue Manager Agent"
    echo "  • Terminal 8: 🧪 Testing Agent"
    echo "  • Terminal 9: 🚀 Deployment Agent"
    echo ""
    echo -e "${CYAN}📋 COMPLETE AGENT ACCESS:${NC}"
    echo "  • All 9 agents in separate terminal windows"
    echo "  • Each terminal is COMPLETELY INDEPENDENT"
    echo "  • Type directly in any terminal to interact with that agent"
    echo "  • Switch between terminals with Cmd+Tab"
    echo "  • Perfect for full system coordination and supervision"
    echo ""
    echo -e "${YELLOW}💡 FULL CONTROL:${NC}"
    echo "  • Complete multi-agent system visibility"
    echo "  • Direct interaction with every specialized agent"
    echo "  • Ideal for complex project coordination"
    echo "  • All agents accessible simultaneously"
    echo ""
    echo -e "${GREEN}Complete multi-agent terminal access ready! 🎉${NC}"
}

# Funzione per creare una vista a 8 pannelli per tutti gli agenti
create_full_agent_dashboard() {
    local session_name="riona-full-dashboard"

    # Termina sessione esistente se presente
    $TMUX_BIN kill-session -t "$session_name" 2>/dev/null || true

    echo -e "${CYAN}🔧 Creating full 8-agent dashboard...${NC}"

    # Crea sessione base
    $TMUX_BIN new-session -d -s "$session_name" -c "$PROJECT_ROOT"

    # Crea layout complesso per 8 pannelli (4x2)
    $TMUX_BIN split-window -h  # Split verticale
    $TMUX_BIN split-window -h  # Split di nuovo verticale (3 colonne)
    $TMUX_BIN select-pane -t 0
    $TMUX_BIN split-window -h  # Split il primo pannello (4 colonne)

    # Ora dividi ogni colonna orizzontalmente per avere 8 pannelli
    for i in {0..3}; do
        $TMUX_BIN select-pane -t $i
        $TMUX_BIN split-window -v
    done

    # Verifica che tutti gli agenti siano attivi
    echo -e "${BLUE}📺 Verifying all agents are active...${NC}"
    for agent in "${AGENTS[@]}"; do
        if ! $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
            echo -e "${RED}❌ Agent $agent is not active! Start agents first.${NC}"
            echo "Run: ./.riona/agents/scripts/unified-agent-startup.sh start-all"
            return 1
        fi
    done

    # Connette direttamente ogni pannello al terminale dell'agente reale
    local agents_for_dashboard=("task-coordinator" "backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")
    local agent_icons=("🎯" "🔧" "💾" "🎨" "📱" "⚙️" "🧪" "🚀")

    echo -e "${BLUE}📺 Connecting each pane to REAL agent terminal...${NC}"
    for i in {0..7}; do
        local agent="${agents_for_dashboard[$i]}"
        local icon="${agent_icons[$i]}"

        $TMUX_BIN select-pane -t $i
        $TMUX_BIN send-keys "clear" Enter
        $TMUX_BIN send-keys "echo -e '${CYAN}$icon ${agent^^} REAL TERMINAL${NC}'" Enter
        $TMUX_BIN send-keys "echo -e '${PURPLE}Direct connection to $agent agent${NC}'" Enter
        $TMUX_BIN send-keys "echo '$(printf '=%.0s' {1..25})'" Enter
        # CONNESSIONE DIRETTA AL TERMINALE DELL'AGENTE
        $TMUX_BIN send-keys "tmux attach-session -t $agent" Enter
    done

    sleep 3

    echo -e "${GREEN}✅ Full 8-agent dashboard with REAL terminals created: $session_name${NC}"
    echo ""
    echo -e "${PURPLE}🎯 ALL 8 REAL AGENT TERMINALS:${NC}"
    echo "  • Pane 0: 🎯 Task Coordinator    • Pane 4: 📱 Instagram"
    echo "  • Pane 1: 🔧 Backend API        • Pane 5: ⚙️ Queue Manager"
    echo "  • Pane 2: 💾 Database           • Pane 6: 🧪 Testing"
    echo "  • Pane 3: 🎨 Frontend UI        • Pane 7: 🚀 Deployment"
    echo ""
    echo -e "${CYAN}📋 DIRECT INTERACTION CONTROLS:${NC}"
    echo "  • Ctrl+B then arrow keys: Navigate between agent terminals"
    echo "  • Type directly: Interact with selected agent (REAL interaction!)"
    echo "  • Ctrl+B then q: Show pane numbers for quick navigation"
    echo "  • Ctrl+B then [: Scroll mode (q to exit)"
    echo "  • Ctrl+B then D: Detach (all agents continue running)"
    echo ""
    echo -e "${YELLOW}💡 REAL TERMINAL INTERACTION:${NC}"
    echo "  • Each pane = REAL agent terminal (not monitoring)"
    echo "  • Direct commands and responses with agents"
    echo "  • Perfect for manual confirmations and complex tasks"
    echo "  • All 8 specialized agents accessible simultaneously"
    echo ""
    echo -e "${GREEN}Connect with: tmux attach-session -t $session_name${NC}"

    read -p "Connect now? (y/n): " connect
    if [[ $connect == "y" || $connect == "Y" ]]; then
        $TMUX_BIN attach-session -t "$session_name"
    fi
}

# Main
case "${1:-}" in
    "preview"|"show")
        agent="${2:-all}"
        if [[ "$agent" == "all" ]]; then
            show_all_previews
        else
            show_agent_preview "$agent" 10
        fi
        ;;
    "monitor"|"grid")
        monitor_agents_grid
        ;;
    "menu"|"connect")
        interactive_agent_menu
        ;;
    "multi-pane"|"pane")
        create_multi_pane_session
        ;;
    "all-terminals"|"all")
        open_all_agent_terminals
        ;;
    "full-dashboard"|"full")
        create_full_agent_dashboard
        ;;
    "list")
        echo -e "${BLUE}Active Agent Sessions:${NC}"
        echo "====================="
        for agent in "${AGENTS[@]}"; do
            if $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
                echo -e "${GREEN}✅ $agent${NC} - tmux attach-session -t $agent"
            else
                echo -e "${RED}❌ $agent${NC} - Not active"
            fi
        done
        ;;
    *)
        echo -e "${PURPLE}Agent Viewer - Visualizza e connetti ai terminali degli agenti${NC}"
        echo "============================================================"
        echo ""
        echo "Usage: $0 <command> [agent]"
        echo ""
        echo -e "${CYAN}COMMANDS:${NC}"
        echo "  preview [agent]          Show preview of agent terminal(s)"
        echo "  monitor                  Real-time grid monitoring"
        echo "  menu                     Interactive connection menu"
        echo "  multi-pane               Open 4 independent terminals (main agents)"
        echo "  all-terminals            Open 9 independent terminals (ALL agents)"
        echo "  full-dashboard           Create 8-pane dashboard (all agents)"
        echo "  list                     List all active agent sessions"
        echo ""
        echo -e "${CYAN}DIRECT CONNECTIONS:${NC}"
        for agent in "${AGENTS[@]}"; do
            echo "  tmux attach-session -t $agent"
        done
        echo ""
        echo -e "${YELLOW}Examples:${NC}"
        echo "  $0 preview                    # Show all agent previews"
        echo "  $0 preview task-coordinator   # Show specific agent"
        echo "  $0 menu                       # Interactive menu"
        echo "  $0 monitor                    # Real-time grid"
        echo "  $0 multi-pane                 # Open 4 main agent terminals"
        echo "  $0 all-terminals              # Open ALL 9 agent terminals"
        echo ""
        echo -e "${GREEN}Quick start: $0 menu${NC}"
        exit 1
        ;;
esac