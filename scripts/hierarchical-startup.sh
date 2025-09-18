#!/bin/bash
# Hierarchical Agent Startup - Sistema multi-agente gerarchico con PM e sub-teams

set -euo pipefail

PROJECT_ROOT="/Users/erik/Desktop/riona_ai/riona-ai"
AGENTS_DIR="$PROJECT_ROOT/.riona/agents"
HIERARCHY_DIR="$AGENTS_DIR/hierarchy"
TEAMS_DIR="$HIERARCHY_DIR/teams"

# Colori
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

unset TMUX 2>/dev/null || true
TMUX_BIN="/opt/homebrew/bin/tmux"

# PM Agents (Level 1 - Coordinatori di area)
PM_AGENTS=("prompt-validator" "task-coordinator" "backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")

# Sub-agents per team (Level 2 - Implementatori specializzati)
get_team_members() {
    local team="$1"
    case "$team" in
        "backend-api-team")
            echo "api-architect endpoint-developer middleware-specialist auth-security-expert performance-optimizer"
            ;;
        "frontend-ui-team")
            echo "ui-architect component-developer state-manager styling-specialist accessibility-expert"
            ;;
        "database-team")
            echo "schema-designer migration-specialist query-optimizer data-validator backup-recovery-expert"
            ;;
        "testing-team")
            echo "unit-test-specialist integration-tester e2e-automation-expert performance-tester security-tester"
            ;;
        "deployment-team")
            echo "ci-cd-specialist container-expert monitoring-setup security-hardening scaling-specialist"
            ;;
        "instagram-team")
            echo "api-connector content-scheduler analytics-processor media-handler automation-expert"
            ;;
        "queue-manager-team")
            echo "job-scheduler worker-manager queue-optimizer failure-handler monitoring-specialist"
            ;;
        "prompt-validator-team")
            echo "prompt-analyzer requirement-extractor task-classifier complexity-assessor"
            ;;
        "task-coordinator-team")
            echo "project-planner resource-allocator dependency-tracker progress-monitor"
            ;;
    esac
}

# Lista dei team
TEAMS=("backend-api-team" "frontend-ui-team" "database-team" "testing-team" "deployment-team" "instagram-team" "queue-manager-team" "prompt-validator-team" "task-coordinator-team")

# Funzione per avviare un agente con contesto specializzato
start_hierarchical_agent() {
    local agent_name="$1"
    local team="${2:-}"
    local is_pm="${3:-false}"

    echo -e "${BLUE}🤖 Starting $agent_name agent...${NC}"

    # Termina sessione esistente se presente
    if $TMUX_BIN has-session -t "$agent_name" 2>/dev/null; then
        echo -e "${YELLOW}   Terminating existing session...${NC}"
        $TMUX_BIN kill-session -t "$agent_name" 2>/dev/null || true
        sleep 1
    fi

    # Crea nuova sessione tmux per l'agente
    $TMUX_BIN new-session -d -s "$agent_name" -c "$PROJECT_ROOT"

    # Avvia Claude Code reale
    echo -e "${CYAN}   Starting Claude Code...${NC}"
    $TMUX_BIN send-keys -t "$agent_name" "claude" Enter
    sleep 4

    # Determina il file di configurazione
    local config_file=""
    if [ "$is_pm" = "true" ]; then
        config_file="$AGENTS_DIR/configs/$agent_name.json"
    else
        config_file="$TEAMS_DIR/$team/$agent_name.json"
    fi

    # Crea contesto se il file di configurazione non esiste
    if [ ! -f "$config_file" ] && [ "$is_pm" = "false" ]; then
        echo "Creating basic config for sub-agent $agent_name in team $team"
        mkdir -p "$(dirname "$config_file")"
        cat > "$config_file" << EOF
{
  "agent_name": "$agent_name",
  "team": "$team",
  "role": "Specialized $agent_name agent",
  "context": "You are the $agent_name specialist in the $team team. Focus on your specialized area and coordinate with your PM agent."
}
EOF
    fi

    # Leggi la configurazione e crea il contesto
    if [ -f "$config_file" ]; then
        local role=$(jq -r '.role // "Specialized Agent"' "$config_file" 2>/dev/null || echo "Specialized Agent")
        local context=$(jq -r '.context // "Specialized agent context"' "$config_file" 2>/dev/null || echo "Specialized agent context")

        local agent_prompt="AGENT INITIALIZATION - $agent_name

You are now the $role for the Riona AI Instagram automation platform.

$context

System Context: You are part of a hierarchical multi-agent system:
- Level 1: PM Agents (Project Managers for each area)
- Level 2: Sub-Agents (Specialized implementation teams)

Your role in the hierarchy: $([ "$is_pm" = "true" ] && echo "PM Agent - Area Coordinator" || echo "Sub-Agent - Specialized Implementer")
$([ "$is_pm" = "false" ] && echo "Team: $team")

Always identify yourself with your specialized role and be ready to receive tasks from your coordination layer."

        # Invia il contesto all'agente
        printf '%s\n' "$agent_prompt" | $TMUX_BIN load-buffer -
        $TMUX_BIN paste-buffer -t "$agent_name"
        $TMUX_BIN send-keys -t "$agent_name" Enter

        sleep 2
        echo -e "${GREEN}✅ $agent_name agent ready${NC}"
    else
        echo -e "${RED}❌ Config file not found for $agent_name${NC}"
        return 1
    fi
}

# Funzione per avviare tutti i PM agents
start_pm_agents() {
    echo -e "${PURPLE}🎯 LEVEL 1: Starting PM Agents (Area Coordinators)${NC}"
    echo "=================================================="

    for pm in "${PM_AGENTS[@]}"; do
        start_hierarchical_agent "$pm" "" "true"
        sleep 1
    done
}

# Funzione per avviare tutti i sub-agent teams
start_sub_teams() {
    echo -e "${PURPLE}👥 LEVEL 2: Starting Sub-Agent Teams${NC}"
    echo "=================================="

    for team in "${TEAMS[@]}"; do
        echo -e "${CYAN}🔧 Starting $team...${NC}"

        # Get team members
        local members_string=$(get_team_members "$team")
        IFS=' ' read -ra members <<< "$members_string"

        for member in "${members[@]}"; do
            start_hierarchical_agent "$member" "$team" "false"
            sleep 0.5
        done

        echo -e "${GREEN}✅ $team ready${NC}"
        echo ""
    done
}

# Funzione per status completo del sistema gerarchico
hierarchical_status() {
    echo -e "${PURPLE}🏢 HIERARCHICAL SYSTEM STATUS${NC}"
    echo "============================="
    echo ""

    echo -e "${CYAN}📊 LEVEL 1 - PM AGENTS (Area Coordinators):${NC}"
    for pm in "${PM_AGENTS[@]}"; do
        if $TMUX_BIN has-session -t "$pm" 2>/dev/null; then
            echo -e "${GREEN}✅ $pm${NC} - Active PM"
        else
            echo -e "${RED}❌ $pm${NC} - Offline"
        fi
    done
    echo ""

    echo -e "${CYAN}👥 LEVEL 2 - SUB-AGENT TEAMS (Specialists):${NC}"
    local total_subs=0
    local active_subs=0

    for team in "${TEAMS[@]}"; do
        echo -e "${YELLOW}$team:${NC}"
        local members_string=$(get_team_members "$team")
        IFS=' ' read -ra members <<< "$members_string"

        for member in "${members[@]}"; do
            total_subs=$((total_subs + 1))
            if $TMUX_BIN has-session -t "$member" 2>/dev/null; then
                echo -e "  ${GREEN}✅ $member${NC} - Active"
                active_subs=$((active_subs + 1))
            else
                echo -e "  ${RED}❌ $member${NC} - Offline"
            fi
        done
        echo ""
    done

    echo -e "${PURPLE}📈 SYSTEM SUMMARY:${NC}"
    echo "  PM Agents: $(echo "${PM_AGENTS[@]}" | wc -w)/$(echo "${PM_AGENTS[@]}" | wc -w)"
    echo "  Sub-Agents: $active_subs/$total_subs"
    echo "  Total Agents: $((active_subs + $(echo "${PM_AGENTS[@]}" | wc -w)))"
}

# Main function
case "${1:-}" in
    "start-all")
        echo -e "${PURPLE}🏢 RIONA AI HIERARCHICAL MULTI-AGENT SYSTEM${NC}"
        echo "============================================="
        echo -e "${YELLOW}Starting complete hierarchical system...${NC}"
        echo ""

        start_pm_agents
        echo ""
        start_sub_teams

        echo -e "${GREEN}🎉 HIERARCHICAL SYSTEM FULLY OPERATIONAL!${NC}"
        echo "========================================"
        hierarchical_status
        ;;

    "start-pms")
        start_pm_agents
        ;;

    "start-subs")
        start_sub_teams
        ;;

    "status")
        hierarchical_status
        ;;

    "stop-all")
        echo -e "${RED}🛑 Stopping all hierarchical agents...${NC}"

        # Stop PM agents
        for pm in "${PM_AGENTS[@]}"; do
            $TMUX_BIN kill-session -t "$pm" 2>/dev/null || true
        done

        # Stop sub-agents
        for team in "${TEAMS[@]}"; do
            local members_string=$(get_team_members "$team")
            IFS=' ' read -ra members <<< "$members_string"
            for member in "${members[@]}"; do
                $TMUX_BIN kill-session -t "$member" 2>/dev/null || true
            done
        done

        echo -e "${GREEN}✅ All agents stopped${NC}"
        ;;

    *)
        echo -e "${PURPLE}Riona AI Hierarchical Agent System${NC}"
        echo "=================================="
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  start-all      Start complete hierarchical system (PM + Sub-agents)"
        echo "  start-pms      Start only PM agents (Level 1)"
        echo "  start-subs     Start only sub-agent teams (Level 2)"
        echo "  status         Show hierarchical system status"
        echo "  stop-all       Stop all agents"
        echo ""
        echo "System Architecture:"
        echo "  • Level 1: 9 PM Agents (Area Coordinators)"
        echo "  • Level 2: ~40 Sub-Agents (Specialized Implementation Teams)"
        echo ""
        exit 1
        ;;
esac