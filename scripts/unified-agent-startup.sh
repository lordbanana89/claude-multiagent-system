#!/bin/bash
# Unified Agent Startup - Avvia tutti gli agenti Claude Code reali con il Task Coordinator

set -euo pipefail

PROJECT_ROOT="/Users/erik/Desktop/riona_ai/riona-ai"
AGENTS_DIR="$PROJECT_ROOT/.riona/agents"
CONFIGS_DIR="$AGENTS_DIR/configs"

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

# Lista agenti in ordine di avvio (Prompt Validator per primo, poi Task Coordinator)
AGENTS=("prompt-validator" "task-coordinator" "backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")

# Funzione per creare contesto agente specializzato
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
    local responsibilities=$(jq -r '.responsibilities[]' "$config_file" | sed 's/^/• /' | paste -sd '\n' -)
    local expertise=$(jq -r '.expertise[]' "$config_file" | sed 's/^/• /' | paste -sd '\n' -)

    # Contesto specializzato basato sul tipo di agente
    case "$agent_name" in
        "task-coordinator")
            cat <<EOF
I am the Task Coordinator & Project Manager agent for the Riona AI Instagram automation platform.

COORDINATOR ROLE:
• Receive complex project requirements and break them into agent-specific tasks
• Route tasks to appropriate specialized agents based on their domain expertise
• Monitor task progress and agent responsiveness in real-time
• Coordinate cross-domain dependencies between agents
• Manage workflow orchestration and provide status updates

MY SPECIALIZED TEAM:
• backend-api: Express.js, Node.js, API development, authentication
• database: PostgreSQL, TypeORM, schema design, query optimization
• frontend-ui: React, TypeScript, UI components, responsive design
• instagram: Instagram API integration, OAuth, media management
• queue-manager: Redis, Bull queues, background job processing
• testing: Jest, Playwright, QA automation, test coverage
• deployment: Docker, CI/CD, infrastructure, production deployment

COORDINATION PROTOCOL:
When I receive a project task, I will:
1. Analyze the requirements and identify which agents are needed
2. Break down the work into agent-specific subtasks
3. Route each subtask to the appropriate specialized agent
4. Monitor progress and check agent responsiveness
5. Coordinate dependencies and handoffs between agents
6. Provide status updates and escalate any blockers

COMMUNICATION FORMAT:
• TASK ASSIGNMENT: "AGENT: [agent-name] TASK: [specific task] PRIORITY: [high/medium/low]"
• STATUS CHECK: "STATUS_REQUEST: [agent-name] - checking progress on [task]"
• COORDINATION: "DEPENDENCY: [agent1] needs output from [agent2] for [specific requirement]"

I am ready to coordinate complex multi-agent workflows and ensure efficient task distribution.

Please confirm you understand I am the Task Coordinator agent.
EOF
            ;;
        "backend-api")
            cat <<EOF
I am the Backend API Developer agent for the Riona AI Instagram automation platform.

AGENT IDENTITY:
• Role: $role
• Specialization: Express.js, Node.js, API development, backend architecture
• Coordinator: I report to task-coordinator agent and coordinate with database, queue-manager agents

MY CORE RESPONSIBILITIES:
$responsibilities

MY TECHNICAL EXPERTISE:
$expertise

PROJECT CONTEXT: $project with hexagonal architecture, PostgreSQL + TypeORM, JWT authentication

COORDINATION PROTOCOL:
• I receive tasks from task-coordinator agent
• I coordinate with database agent for schema requirements
• I coordinate with frontend-ui agent for API endpoint specifications
• I provide status updates when requested
• I escalate blockers to task-coordinator

I am ready to receive backend development tasks from the coordinator.

Please confirm you understand I am the Backend API Developer agent.
EOF
            ;;
        "database")
            cat <<EOF
I am the Database Specialist agent for the Riona AI Instagram automation platform.

AGENT IDENTITY:
• Role: $role
• Specialization: PostgreSQL, TypeORM, database design, migrations, data modeling
• Coordinator: I report to task-coordinator and coordinate with backend-api agent

MY CORE RESPONSIBILITIES:
$responsibilities

MY TECHNICAL EXPERTISE:
$expertise

PROJECT CONTEXT: $project with PostgreSQL database, TypeORM entities, hexagonal architecture

COORDINATION PROTOCOL:
• I receive database tasks from task-coordinator agent
• I coordinate with backend-api agent for API data requirements
• I provide schema designs and migration plans
• I report progress to task-coordinator when requested

I am ready to receive database design and optimization tasks.

Please confirm you understand I am the Database Specialist agent.
EOF
            ;;
        "frontend-ui")
            cat <<EOF
I am the Frontend UI Developer agent for the Riona AI Instagram automation platform.

AGENT IDENTITY:
• Role: $role
• Specialization: React.js, TypeScript, Tailwind CSS, component architecture
• Coordinator: I report to task-coordinator and coordinate with backend-api agent

MY CORE RESPONSIBILITIES:
$responsibilities

MY TECHNICAL EXPERTISE:
$expertise

PROJECT CONTEXT: $project with React 18 + TypeScript, TailwindCSS, TanStack Router

COORDINATION PROTOCOL:
• I receive UI/UX tasks from task-coordinator agent
• I coordinate with backend-api agent for API endpoint specifications
• I create responsive components and user interfaces
• I report progress to task-coordinator when requested

I am ready to receive frontend development and UI design tasks.

Please confirm you understand I am the Frontend UI Developer agent.
EOF
            ;;
        *)
            cat <<EOF
I am the $role agent for the Riona AI Instagram automation platform.

AGENT IDENTITY:
• Role: $role
• Description: $description
• Coordinator: I report to task-coordinator agent

MY CORE RESPONSIBILITIES:
$responsibilities

MY TECHNICAL EXPERTISE:
$expertise

PROJECT CONTEXT: $project

COORDINATION PROTOCOL:
• I receive specialized tasks from task-coordinator agent
• I coordinate with other agents as needed for my domain
• I provide status updates when requested
• I escalate any blockers to task-coordinator

I am ready to receive tasks within my specialization area.

Please confirm you understand I am the $role agent.
EOF
            ;;
    esac
}

# Funzione per inizializzare un singolo agente
initialize_agent() {
    local agent_name="$1"
    local config_file="$CONFIGS_DIR/$agent_name.json"

    if [ ! -f "$config_file" ]; then
        echo -e "${RED}Config not found: $config_file${NC}"
        return 1
    fi

    local role=$(jq -r '.role' "$config_file")

    echo -e "${BLUE}🤖 Initializing $agent_name agent...${NC}"
    echo -e "   Role: $role"

    # Termina sessione esistente se presente
    if $TMUX_BIN has-session -t "$agent_name" 2>/dev/null; then
        echo -e "${YELLOW}   Terminating existing session...${NC}"
        $TMUX_BIN kill-session -t "$agent_name"
    fi

    # Crea nuova sessione tmux
    $TMUX_BIN new-session -d -s "$agent_name" -c "$PROJECT_ROOT"

    # Avvia Claude Code reale
    $TMUX_BIN send-keys -t "$agent_name" "claude" Enter

    # Aspetta che Claude si avvii
    echo -e "${CYAN}   Starting Claude Code...${NC}"
    sleep 4

    # Crea e invia contesto specializzato
    local agent_context
    agent_context=$(create_agent_context "$agent_name")

    printf '%s\n' "$agent_context" | $TMUX_BIN load-buffer -
    $TMUX_BIN paste-buffer -t "$agent_name"
    $TMUX_BIN send-keys -t "$agent_name" Enter

    echo -e "${GREEN}✅ $agent_name agent ready${NC}"
    echo ""
}

# Funzione per avviare tutti gli agenti
start_all_agents() {
    echo -e "${PURPLE}🚀 UNIFIED AGENT STARTUP SYSTEM${NC}"
    echo "==============================="
    echo -e "${YELLOW}Starting complete multi-agent system for Riona AI...${NC}"
    echo ""

    local start_time=$(date +%s)

    # Avvia Task Coordinator per primo
    echo -e "${CYAN}📋 PHASE 1: Starting Task Coordinator (Team Leader)${NC}"
    echo "------------------------------------------------"
    initialize_agent "task-coordinator"
    sleep 2

    # Avvia agenti specializzati
    echo -e "${CYAN}🔧 PHASE 2: Starting Specialized Agents${NC}"
    echo "-------------------------------------"

    for agent in "${AGENTS[@]}"; do
        if [[ "$agent" != "task-coordinator" ]]; then
            initialize_agent "$agent"
            sleep 1
        fi
    done

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo -e "${GREEN}🎉 ALL AGENTS INITIALIZED SUCCESSFULLY!${NC}"
    echo "======================================="
    echo -e "${BLUE}Total startup time: ${duration}s${NC}"
    echo -e "${BLUE}Active agents: ${#AGENTS[@]}${NC}"
    echo ""

    # Verifica status
    agent_status_check

    echo ""
    echo -e "${PURPLE}SYSTEM READY FOR COORDINATED WORKFLOWS!${NC}"
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo "  ./claude-orchestrator.sh send task-coordinator \"PROJECT: Create user notification system\""
    echo "  ./claude-orchestrator.sh workflow feature-development \"notification-system\""
    echo "  tmux attach-session -t task-coordinator"
}

# Funzione per verificare status di tutti gli agenti
agent_status_check() {
    echo -e "${YELLOW}📊 AGENT STATUS CHECK${NC}"
    echo "==================="

    local active_count=0
    local total_count=${#AGENTS[@]}

    for agent in "${AGENTS[@]}"; do
        if $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
            echo -e "${GREEN}✅ $agent${NC} - Active (tmux attach-session -t $agent)"
            active_count=$((active_count + 1))
        else
            echo -e "${RED}❌ $agent${NC} - Offline"
        fi
    done

    echo "==================="
    echo -e "Status: ${GREEN}$active_count${NC}/$total_count agents active"

    if [ $active_count -eq $total_count ]; then
        echo -e "${GREEN}🎉 All agents operational!${NC}"
    else
        echo -e "${YELLOW}⚠️ Some agents need attention${NC}"
    fi
}

# Funzione per riavviare un agente specifico
restart_agent() {
    local agent_name="$1"

    if [[ ! " ${AGENTS[@]} " =~ " ${agent_name} " ]]; then
        echo -e "${RED}Invalid agent: $agent_name${NC}"
        echo "Available agents: ${AGENTS[*]}"
        return 1
    fi

    echo -e "${YELLOW}🔄 Restarting $agent_name agent...${NC}"
    initialize_agent "$agent_name"
    echo -e "${GREEN}✅ $agent_name restarted successfully${NC}"
}

# Funzione per terminare tutti gli agenti
stop_all_agents() {
    echo -e "${YELLOW}🛑 Stopping all agents...${NC}"

    local stopped_count=0

    for agent in "${AGENTS[@]}"; do
        if $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
            $TMUX_BIN kill-session -t "$agent"
            echo -e "${GREEN}✅ Stopped: $agent${NC}"
            stopped_count=$((stopped_count + 1))
        fi
    done

    echo -e "${GREEN}🎯 Stopped $stopped_count agent sessions${NC}"
}

# Funzione per monitoraggio real-time
monitor_agents() {
    echo -e "${GREEN}🔍 Real-Time Agent Monitor${NC}"
    echo "Press Ctrl+C to stop monitoring"
    echo "==============================="

    while true; do
        clear
        echo -e "${CYAN}$(date) - Multi-Agent System Monitor${NC}"
        echo "======================================="

        # Status Task Coordinator (prioritario)
        if $TMUX_BIN has-session -t "task-coordinator" 2>/dev/null; then
            echo -e "${PURPLE}🎯 TASK COORDINATOR${NC}"
            local output=$($TMUX_BIN capture-pane -t "task-coordinator" -p | tail -2 | head -1)
            if [ -n "$output" ]; then
                echo "   $(echo "$output" | cut -c1-70)..."
            fi
            echo ""
        fi

        # Status altri agenti
        for agent in "${AGENTS[@]}"; do
            if [[ "$agent" != "task-coordinator" ]]; then
                if $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
                    echo -e "${GREEN}✅ $agent${NC}"
                    local output=$($TMUX_BIN capture-pane -t "$agent" -p | tail -2 | head -1)
                    if [ -n "$output" ]; then
                        echo "   $(echo "$output" | cut -c1-60)..."
                    fi
                else
                    echo -e "${RED}❌ $agent - Offline${NC}"
                fi
            fi
        done

        echo ""
        echo -e "${BLUE}Commands: Ctrl+C to quit${NC}"
        sleep 3
    done
}

# Main
case "${1:-}" in
    "start-all"|"start")
        start_all_agents
        ;;
    "restart-all")
        echo -e "${YELLOW}🔄 Restarting entire multi-agent system...${NC}"
        stop_all_agents
        sleep 2
        start_all_agents
        ;;
    "restart")
        if [ -z "${2:-}" ]; then
            echo "Usage: $0 restart <agent_name>"
            echo "Available agents: ${AGENTS[*]}"
            exit 1
        fi
        restart_agent "$2"
        ;;
    "stop-all"|"stop")
        stop_all_agents
        ;;
    "status")
        agent_status_check
        ;;
    "monitor")
        monitor_agents
        ;;
    "list")
        echo -e "${BLUE}Available Agents:${NC}"
        echo "================="
        for agent in "${AGENTS[@]}"; do
            local role=""
            if [ -f "$CONFIGS_DIR/$agent.json" ]; then
                role=" - $(jq -r '.role' "$CONFIGS_DIR/$agent.json")"
            fi
            echo -e "${GREEN}$agent${NC}$role"
        done
        ;;
    *)
        echo -e "${PURPLE}Unified Agent Startup System${NC}"
        echo "============================"
        echo ""
        echo "Usage: $0 <command> [args]"
        echo ""
        echo -e "${CYAN}🚀 SYSTEM MANAGEMENT:${NC}"
        echo "  start-all              Start complete multi-agent system"
        echo "  restart-all            Restart entire system"
        echo "  stop-all               Stop all agents"
        echo "  status                 Check all agent status"
        echo "  monitor                Real-time agent monitoring"
        echo ""
        echo -e "${CYAN}🤖 INDIVIDUAL AGENTS:${NC}"
        echo "  restart <agent>        Restart specific agent"
        echo "  list                   List all available agents"
        echo ""
        echo -e "${CYAN}📋 AGENT ROSTER:${NC}"
        echo "  task-coordinator       Task distribution and monitoring"
        echo "  backend-api           Express.js, Node.js, API development"
        echo "  database              PostgreSQL, TypeORM, schema design"
        echo "  frontend-ui           React, TypeScript, UI components"
        echo "  instagram             Instagram API, OAuth, media management"
        echo "  queue-manager         Redis, Bull queues, background jobs"
        echo "  testing               Jest, Playwright, QA automation"
        echo "  deployment            Docker, CI/CD, infrastructure"
        echo ""
        echo -e "${YELLOW}Examples:${NC}"
        echo "  $0 start-all                    # Start complete system"
        echo "  $0 restart task-coordinator     # Restart coordinator"
        echo "  $0 monitor                      # Monitor all agents"
        echo ""
        echo -e "${GREEN}After startup, use:${NC}"
        echo "  ./claude-orchestrator.sh send task-coordinator \"PROJECT: [description]\""
        exit 1
        ;;
esac