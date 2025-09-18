#!/bin/bash
# Hierarchical Orchestrator - Coordina il sistema multi-agente gerarchico

set -euo pipefail

PROJECT_ROOT="/Users/erik/Desktop/riona_ai/riona-ai"
cd "$PROJECT_ROOT"

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

unset TMUX 2>/dev/null || true
TMUX_BIN="/opt/homebrew/bin/tmux"

# PM Agents (Level 1)
PM_AGENTS=("prompt-validator" "task-coordinator" "backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")

# Funzione per inviare task gerarchico (PM → Sub-team)
send_hierarchical_task() {
    local pm_agent="$1"
    local task="$2"
    local wait_time="${3:-10}"

    echo -e "${PURPLE}🏢 HIERARCHICAL TASK DELEGATION${NC}"
    echo -e "${CYAN}PM Agent: $pm_agent → Sub-team delegation${NC}"
    echo ""

    # STEP 1: Invia al PM Agent
    echo -e "${BLUE}📋 STEP 1: Sending to PM Agent ($pm_agent)...${NC}"
    local pm_prompt="HIERARCHICAL TASK COORDINATION

Task: $task

As the PM Agent for your area, please:

1. ANALYZE this task from your domain perspective
2. BREAK DOWN the task into specialized sub-tasks
3. DELEGATE specific parts to your sub-agent specialists
4. COORDINATE the overall execution
5. ENSURE quality and consistency across your team

Your sub-team specialists are ready to receive delegated tasks.
Please analyze and delegate appropriately.

Focus on project management and coordination rather than direct implementation."

    printf '%s\n' "$pm_prompt" | $TMUX_BIN load-buffer -
    $TMUX_BIN paste-buffer -t "$pm_agent"
    $TMUX_BIN send-keys -t "$pm_agent" Enter

    echo -e "${GREEN}✅ Task sent to PM Agent: $pm_agent${NC}"
    echo -e "${YELLOW}⏳ PM will now analyze and delegate to sub-team...${NC}"
    echo ""

    echo -e "${PURPLE}🎯 HIERARCHICAL FLOW INITIATED${NC}"
    echo "  1. ✅ PM Agent: Task received and analyzing"
    echo "  2. ⏳ Sub-Team: Will receive delegated tasks from PM"
    echo "  3. ⏳ Implementation: Specialists will execute their parts"
    echo ""
    echo -e "${CYAN}💡 Monitor with: ./view-agents.sh all-terminals${NC}"
}

# Funzione per workflow completo gerarchico
hierarchical_workflow() {
    local project_type="$1"
    local description="$2"

    echo -e "${PURPLE}🏗️  HIERARCHICAL PROJECT WORKFLOW${NC}"
    echo "================================="
    echo "Project Type: $project_type"
    echo "Description: $description"
    echo ""

    # STEP 1: Prompt Validation
    echo -e "${BLUE}📝 STEP 1: Project Validation...${NC}"
    send_hierarchical_task "prompt-validator" "Validate and analyze project: $project_type - $description"

    sleep 8

    # STEP 2: Task Coordination
    echo -e "${BLUE}🎯 STEP 2: Project Coordination...${NC}"
    send_hierarchical_task "task-coordinator" "Coordinate project implementation: $project_type - $description"

    sleep 5

    # STEP 3: Delegazione ai PM specializzati
    case "$project_type" in
        "full-stack-feature")
            echo -e "${BLUE}🔧 STEP 3: Full-Stack Implementation...${NC}"
            send_hierarchical_task "backend-api" "Implement backend for: $description" &
            send_hierarchical_task "database" "Design data layer for: $description" &
            send_hierarchical_task "frontend-ui" "Create UI for: $description" &
            send_hierarchical_task "testing" "Create test suite for: $description" &
            wait
            ;;
        "backend-feature")
            echo -e "${BLUE}🔧 STEP 3: Backend Implementation...${NC}"
            send_hierarchical_task "backend-api" "Implement backend feature: $description" &
            send_hierarchical_task "database" "Support data requirements for: $description" &
            send_hierarchical_task "testing" "Test backend feature: $description" &
            wait
            ;;
        "frontend-feature")
            echo -e "${BLUE}🎨 STEP 3: Frontend Implementation...${NC}"
            send_hierarchical_task "frontend-ui" "Implement frontend feature: $description" &
            send_hierarchical_task "testing" "Test UI feature: $description" &
            wait
            ;;
        "deployment")
            echo -e "${BLUE}🚀 STEP 3: Deployment Process...${NC}"
            send_hierarchical_task "deployment" "Deploy and setup: $description" &
            send_hierarchical_task "testing" "Test deployment: $description" &
            wait
            ;;
    esac

    echo -e "${GREEN}🎉 HIERARCHICAL WORKFLOW INITIATED${NC}"
    echo "All PM agents and their sub-teams are now coordinating the implementation."
}

# Funzione per broadcast gerarchico (tutti i PM)
broadcast_to_pms() {
    local message="$1"

    echo -e "${PURPLE}📢 BROADCASTING TO ALL PM AGENTS${NC}"
    echo "==============================="
    echo "Message: $message"
    echo ""

    for pm in "${PM_AGENTS[@]}"; do
        if $TMUX_BIN has-session -t "$pm" 2>/dev/null; then
            echo -e "${BLUE}Broadcasting to $pm PM...${NC}"
            printf '%s\n' "PM BROADCAST: $message" | $TMUX_BIN load-buffer -
            $TMUX_BIN paste-buffer -t "$pm"
            $TMUX_BIN send-keys -t "$pm" Enter
            sleep 1
        fi
    done

    echo -e "${GREEN}✅ Broadcast sent to all PM agents${NC}"
}

# Funzione per status gerarchico
hierarchical_status() {
    echo -e "${PURPLE}🏢 HIERARCHICAL SYSTEM STATUS${NC}"
    echo "============================="

    ./.riona/agents/scripts/hierarchical-startup.sh status
}

# Main
if [ $# -eq 0 ]; then
    echo -e "${PURPLE}🏢 Riona AI Hierarchical Orchestrator${NC}"
    echo "===================================="
    echo ""
    echo "Usage: $0 <command> [args...]"
    echo ""
    echo "🎯 HIERARCHICAL COMMANDS:"
    echo "  delegate <pm-agent> <task>       Send task to PM agent for sub-team delegation"
    echo "  workflow <type> <description>    Run hierarchical project workflow"
    echo "  broadcast <message>              Send message to all PM agents"
    echo "  status                          Show hierarchical system status"
    echo ""
    echo "🔧 WORKFLOW TYPES:"
    echo "  full-stack-feature              Complete feature (backend + frontend + database + testing)"
    echo "  backend-feature                 Backend-focused feature"
    echo "  frontend-feature               Frontend-focused feature"
    echo "  deployment                     Deployment and infrastructure"
    echo ""
    echo "Examples:"
    echo "  $0 delegate backend-api \"Create user authentication API\""
    echo "  $0 workflow full-stack-feature \"User profile management\""
    echo "  $0 broadcast \"Project status update required\""
    echo "  $0 status"
    echo ""
    echo "🚀 Start hierarchical system: ./.riona/agents/scripts/hierarchical-startup.sh start-all"
    exit 1
fi

case "$1" in
    "delegate")
        send_hierarchical_task "$2" "$3" "${4:-10}"
        ;;
    "workflow")
        hierarchical_workflow "$2" "${3:-}"
        ;;
    "broadcast")
        broadcast_to_pms "$2"
        ;;
    "status")
        hierarchical_status
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use $0 without arguments for help"
        exit 1
        ;;
esac