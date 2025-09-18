#!/bin/bash
# Claude Code Multi-Agent Launcher - Avvia vere sessioni Claude Code specializzate

set -euo pipefail

PROJECT_ROOT="/Users/erik/Desktop/riona_ai/riona-ai"
AGENTS_DIR="$PROJECT_ROOT/.riona/agents"
CONFIGS_DIR="$AGENTS_DIR/configs"
SESSIONS_DIR="$AGENTS_DIR/sessions"

# Colori
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Assicurati che tmux sia configurato correttamente
unset TMUX 2>/dev/null || true
TMUX_BIN="/opt/homebrew/bin/tmux"

# Crea directory sessions se non esiste
mkdir -p "$SESSIONS_DIR"

# Funzione per creare file di contesto specializzato
create_agent_context() {
    local agent_name="$1"
    local config_file="$CONFIGS_DIR/$agent_name.json"

    if [ ! -f "$config_file" ]; then
        echo -e "${RED}Config not found: $config_file${NC}"
        return 1
    fi

    local role=$(jq -r '.role' "$config_file")
    local description=$(jq -r '.description' "$config_file")
    local project=$(jq -r '.context.project' "$config_file")
    local responsibilities=$(jq -r '.responsibilities[]' "$config_file" | sed 's/^/- /')
    local expertise=$(jq -r '.expertise[]' "$config_file" | sed 's/^/- /')
    local working_dir=$(jq -r '.working_directory' "$config_file")

    # Crea file di contesto per Claude Code
    cat > "$SESSIONS_DIR/$agent_name-context.md" <<EOF
# $role Agent Context

## Identity
You are the **$role** for $project.

## Description
$description

## Your Responsibilities
$responsibilities

## Your Expertise Areas
$expertise

## Project Context
$(jq -r '.context | to_entries[] | "- **\(.key | ascii_upcase)**: \(.value)"' "$config_file")

## Working Directory
$working_dir

## Instructions
1. **Stay in Character**: Always respond as the $role
2. **Focus on Domain**: Prioritize tasks within your expertise
3. **Collaborate**: Work with other agents when cross-domain tasks arise
4. **Quality First**: Maintain high standards in your specialized area
5. **Context Awareness**: You're part of a multi-agent system working on $project

## Agent Communication Protocol
- When you receive a task, analyze it from your domain perspective
- If a task requires expertise outside your domain, suggest which agent should handle it
- Always provide concrete, actionable responses
- Use your specialized knowledge to add value to every interaction

## Current Session
- **Agent**: $agent_name
- **Role**: $role
- **Status**: Active and ready for domain-specific tasks
EOF

    echo "$SESSIONS_DIR/$agent_name-context.md"
}

# Funzione per avviare una sessione Claude Code con contesto
start_claude_agent_session() {
    local agent_name="$1"
    local config_file="$CONFIGS_DIR/$agent_name.json"

    if [ ! -f "$config_file" ]; then
        echo -e "${RED}Config not found: $config_file${NC}"
        return 1
    fi

    echo -e "${BLUE}Starting Claude Code session for: $agent_name${NC}"

    # Crea contesto specializzato
    local context_file
    context_file=$(create_agent_context "$agent_name")

    # Crea sessione tmux con Claude Code
    local session_name="claude-$agent_name"

    # Termina sessione esistente se presente
    $TMUX_BIN kill-session -t "$session_name" 2>/dev/null || true

    # Crea nuova sessione tmux
    $TMUX_BIN new-session -d -s "$session_name" -c "$PROJECT_ROOT"

    # Imposta variabile d'ambiente per Claude Code con contesto
    $TMUX_BIN send-keys -t "$session_name" "export CLAUDE_AGENT_CONTEXT='$context_file'" Enter
    sleep 1

    # Avvia Claude Code in modalità agente
    $TMUX_BIN send-keys -t "$session_name" "claude-code --agent-mode" Enter
    sleep 3

    # Invia il contesto iniziale direttamente a Claude Code
    $TMUX_BIN send-keys -t "$session_name" "I am now acting as the $(jq -r '.role' "$config_file") agent for the Riona AI project. I have received my specialized context and am ready to work within my domain expertise. Please acknowledge that I am ready." Enter

    echo -e "${GREEN}✅ Claude agent session started: $session_name${NC}"
    echo -e "   Context file: $context_file"
    echo -e "   Connect with: tmux attach-session -t $session_name"
}

# Funzione per avviare tutti gli agenti
start_all_agents() {
    echo -e "${YELLOW}Starting all Claude Code agent sessions...${NC}"
    echo "========================================="

    local agents=("backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")

    for agent in "${agents[@]}"; do
        echo -e "${BLUE}Processing agent: $agent${NC}"
        start_claude_agent_session "$agent"
        echo ""
        sleep 3
    done

    echo -e "${GREEN}All Claude agents started successfully!${NC}"
    echo ""
    list_active_sessions
}

# Funzione per riavviare un singolo agente
restart_agent() {
    local agent_name="$1"

    if [ ! -f "$CONFIGS_DIR/$agent_name.json" ]; then
        echo -e "${RED}Agent config not found: $agent_name${NC}"
        return 1
    fi

    echo -e "${YELLOW}Restarting Claude agent: $agent_name${NC}"

    # Termina sessione esistente
    $TMUX_BIN kill-session -t "claude-$agent_name" 2>/dev/null || true

    # Avvia nuova sessione
    start_claude_agent_session "$agent_name"

    echo -e "${GREEN}Agent restarted: $agent_name${NC}"
}

# Funzione per listare sessioni attive
list_active_sessions() {
    echo -e "${YELLOW}Active Claude Agent Sessions:${NC}"
    echo "============================"

    local agents=("backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")
    local active_count=0

    for agent in "${agents[@]}"; do
        local session_name="claude-$agent"
        if $TMUX_BIN has-session -t "$session_name" 2>/dev/null; then
            echo -e "${GREEN}✅ $agent${NC} - tmux attach-session -t $session_name"
            active_count=$((active_count + 1))
        else
            echo -e "${RED}❌ $agent${NC} - Session not found"
        fi
    done

    echo "============================"
    echo -e "Active sessions: ${GREEN}$active_count${NC}/7"
}

# Funzione per terminare tutti gli agenti
stop_all_agents() {
    echo -e "${YELLOW}Stopping all Claude agent sessions...${NC}"

    local agents=("backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")
    local stopped_count=0

    for agent in "${agents[@]}"; do
        local session_name="claude-$agent"
        if $TMUX_BIN has-session -t "$session_name" 2>/dev/null; then
            $TMUX_BIN kill-session -t "$session_name"
            echo -e "${GREEN}✅ Stopped: $agent${NC}"
            stopped_count=$((stopped_count + 1))
        fi
    done

    echo -e "${GREEN}Stopped $stopped_count agent sessions${NC}"
}

# Funzione per inviare comando a un agente
send_to_claude_agent() {
    local agent_name="$1"
    local command="$2"
    local session_name="claude-$agent_name"

    if ! $TMUX_BIN has-session -t "$session_name" 2>/dev/null; then
        echo -e "${RED}Agent session not found: $agent_name${NC}"
        return 1
    fi

    echo -e "${BLUE}Sending to $agent_name:${NC} $command"

    # Invia comando
    $TMUX_BIN send-keys -t "$session_name" "$command" Enter

    echo -e "${GREEN}Command sent to agent: $agent_name${NC}"
    echo -e "View response with: tmux attach-session -t $session_name"
}

# Funzione per health check
health_check() {
    echo -e "${GREEN}Claude Agents Health Check${NC}"
    echo "========================="

    local agents=("backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")
    local healthy=0
    local total=7

    for agent in "${agents[@]}"; do
        local session_name="claude-$agent"
        echo -n "Checking $agent... "

        if $TMUX_BIN has-session -t "$session_name" 2>/dev/null; then
            # Test basic responsiveness
            $TMUX_BIN send-keys -t "$session_name" "echo 'Health check: I am $(jq -r '.role' "$CONFIGS_DIR/$agent.json") and I am ready to work.'" Enter
            sleep 1
            echo -e "${GREEN}✅ Active${NC}"
            healthy=$((healthy + 1))
        else
            echo -e "${RED}❌ Offline${NC}"
        fi
    done

    echo "========================="
    echo -e "Health Score: ${GREEN}$healthy${NC}/$total agents active"

    if [ $healthy -eq $total ]; then
        echo -e "${GREEN}🎉 All Claude agents operational!${NC}"
    elif [ $healthy -gt $((total / 2)) ]; then
        echo -e "${YELLOW}⚠️ Some agents need attention${NC}"
    else
        echo -e "${RED}🚨 System degraded - restart required${NC}"
    fi
}

# Main
case "${1:-}" in
    "start-all")
        start_all_agents
        ;;
    "start")
        if [ -z "${2:-}" ]; then
            echo "Usage: $0 start <agent_name>"
            exit 1
        fi
        start_claude_agent_session "$2"
        ;;
    "restart")
        if [ -z "${2:-}" ]; then
            echo "Usage: $0 restart <agent_name>"
            exit 1
        fi
        restart_agent "$2"
        ;;
    "stop-all")
        stop_all_agents
        ;;
    "list"|"status")
        list_active_sessions
        ;;
    "send")
        if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
            echo "Usage: $0 send <agent_name> <command>"
            exit 1
        fi
        send_to_claude_agent "$2" "$3"
        ;;
    "health")
        health_check
        ;;
    "context")
        if [ -z "${2:-}" ]; then
            echo "Usage: $0 context <agent_name>"
            exit 1
        fi
        create_agent_context "$2"
        echo -e "${GREEN}Context created for $2${NC}"
        ;;
    *)
        echo "Claude Code Multi-Agent Launcher"
        echo "==============================="
        echo ""
        echo "Usage: $0 <command> [args]"
        echo ""
        echo "Commands:"
        echo "  start-all              Start all Claude agent sessions"
        echo "  start <agent>          Start specific Claude agent session"
        echo "  restart <agent>        Restart specific agent"
        echo "  stop-all               Stop all agent sessions"
        echo "  list                   List active sessions"
        echo "  status                 Check session status"
        echo "  send <agent> <cmd>     Send command to specific agent"
        echo "  health                 Health check all agents"
        echo "  context <agent>        Generate context file for agent"
        echo ""
        echo "Available agents: backend-api, database, frontend-ui, instagram, queue-manager, testing, deployment"
        echo ""
        echo "Examples:"
        echo "  $0 start-all                           # Start all agents"
        echo "  $0 start backend-api                   # Start backend API agent"
        echo "  $0 send frontend-ui 'create login component'  # Send task to frontend agent"
        echo "  $0 health                              # Check all agents health"
        echo ""
        echo "Connect to agent session:"
        echo "  tmux attach-session -t claude-<agent-name>"
        echo "  Example: tmux attach-session -t claude-backend-api"
        exit 1
        ;;
esac