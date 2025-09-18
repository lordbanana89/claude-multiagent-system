#!/bin/bash
# Authorized Orchestrator - Sistema con catena di autorizzazioni gerarchiche

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
AUTH_SYSTEM="$PROJECT_ROOT/.riona/agents/authorization/authorization-system.sh"

# PM Agents
PM_AGENTS=("prompt-validator" "task-coordinator" "backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")

# Funzione per inviare task con richiesta di autorizzazione
send_authorized_task() {
    local pm_agent="$1"
    local task="$2"

    echo -e "${PURPLE}🔐 AUTHORIZED TASK DELEGATION${NC}"
    echo -e "${CYAN}PM Agent: $pm_agent${NC}"
    echo -e "${YELLOW}Authorization Required: Yes${NC}"
    echo ""

    # Invia task al PM con richiesta di processo di autorizzazione
    local pm_prompt="🔐 AUTHORIZED HIERARCHICAL TASK COORDINATION

Task: $task

AUTHORIZATION PROCESS REQUIRED:

As the $pm_agent PM, you must follow this process:

1. ANALYZE the task and determine which sub-agents need to work on it
2. CREATE authorization requests for each sub-agent using the format:
   'REQUEST_AUTHORIZATION [sub-agent-name] [specific-task-for-sub-agent]'
3. WAIT for orchestrator authorization before delegating
4. RELAY authorization to sub-agents when approved

Your sub-agents MUST request permission before starting work.

Please start by analyzing the task and identifying which sub-agents you need:
- Which specialists from your team are required?
- What specific tasks will each perform?
- Are there any dependencies or coordination needs?

After analysis, create authorization requests for each required sub-agent."

    printf '%s\n' "$pm_prompt" | $TMUX_BIN load-buffer -
    $TMUX_BIN paste-buffer -t "$pm_agent"
    $TMUX_BIN send-keys -t "$pm_agent" Enter

    echo -e "${GREEN}✅ Authorized task sent to PM: $pm_agent${NC}"
    echo -e "${YELLOW}⏳ PM will analyze and create authorization requests${NC}"
    echo ""
}

# Funzione per workflow autorizzato completo
authorized_workflow() {
    local project_type="$1"
    local description="$2"

    echo -e "${PURPLE}🔐 AUTHORIZED HIERARCHICAL WORKFLOW${NC}"
    echo "===================================="
    echo "Project Type: $project_type"
    echo "Description: $description"
    echo "Authorization: Required at each level"
    echo ""

    # STEP 1: Validazione con autorizzazione
    echo -e "${BLUE}📝 STEP 1: Authorized Project Validation...${NC}"
    send_authorized_task "prompt-validator" "Validate and analyze project: $project_type - $description"

    sleep 5

    # STEP 2: Coordinamento con autorizzazione
    echo -e "${BLUE}🎯 STEP 2: Authorized Project Coordination...${NC}"
    send_authorized_task "task-coordinator" "Coordinate project implementation: $project_type - $description"

    sleep 3

    # STEP 3: Implementazione con autorizzazioni per team specializzati
    case "$project_type" in
        "full-stack-feature")
            echo -e "${BLUE}🔧 STEP 3: Authorized Full-Stack Implementation...${NC}"
            send_authorized_task "backend-api" "Implement backend with authorization for: $description" &
            sleep 1
            send_authorized_task "database" "Design data layer with authorization for: $description" &
            sleep 1
            send_authorized_task "frontend-ui" "Create UI with authorization for: $description" &
            sleep 1
            send_authorized_task "testing" "Create test suite with authorization for: $description" &
            wait
            ;;
        "backend-feature")
            echo -e "${BLUE}🔧 STEP 3: Authorized Backend Implementation...${NC}"
            send_authorized_task "backend-api" "Implement backend feature with authorization: $description" &
            send_authorized_task "database" "Support data requirements with authorization for: $description" &
            send_authorized_task "testing" "Test backend feature with authorization: $description" &
            wait
            ;;
    esac

    echo -e "${GREEN}🔐 AUTHORIZED WORKFLOW INITIATED${NC}"
    echo "All PM agents will request authorization before delegating to sub-agents."
}

# Funzione per gestire comandi di autorizzazione
handle_authorization_command() {
    local command="$1"
    shift

    case "$command" in
        "AUTHORIZE")
            local request_id="$1"
            echo -e "${GREEN}✅ AUTHORIZING REQUEST: $request_id${NC}"
            $AUTH_SYSTEM authorize "$request_id"
            ;;
        "DENY")
            local request_id="$1"
            local reason="${2:-No reason provided}"
            echo -e "${RED}❌ DENYING REQUEST: $request_id${NC}"
            echo "Reason: $reason"
            $AUTH_SYSTEM deny "$request_id" "$reason"
            ;;
        "MODIFY")
            local request_id="$1"
            local instructions="${2:-Please revise the request}"
            echo -e "${YELLOW}⚠️ REQUESTING MODIFICATION: $request_id${NC}"
            echo "Instructions: $instructions"
            $AUTH_SYSTEM modify "$request_id" "$instructions"
            ;;
        *)
            echo -e "${RED}Unknown authorization command: $command${NC}"
            return 1
            ;;
    esac
}

# Funzione per mostrare richieste pending
show_pending_authorizations() {
    echo -e "${CYAN}🔐 PENDING AUTHORIZATION REQUESTS${NC}"
    echo ""
    $AUTH_SYSTEM pending
    echo ""
    echo -e "${YELLOW}Commands to manage requests:${NC}"
    echo "  $0 auth AUTHORIZE <request-id>              # Approve request"
    echo "  $0 auth DENY <request-id> [reason]          # Deny request"
    echo "  $0 auth MODIFY <request-id> [instructions]  # Request changes"
}

# Funzione per broadcast con autorizzazione
authorized_broadcast() {
    local message="$1"

    echo -e "${PURPLE}📢 AUTHORIZED BROADCAST TO ALL PMs${NC}"
    echo "Message: $message"
    echo "Authorization: Required for any actions"
    echo ""

    for pm in "${PM_AGENTS[@]}"; do
        if $TMUX_BIN has-session -t "$pm" 2>/dev/null; then
            echo -e "${BLUE}Broadcasting to $pm PM...${NC}"

            local auth_message="🔐 AUTHORIZED BROADCAST: $message

IMPORTANT: Any actions based on this message require authorization.
If you need to delegate tasks to sub-agents, follow the authorization process:
1. REQUEST_AUTHORIZATION [sub-agent] [task]
2. Wait for orchestrator approval
3. Relay authorization to sub-agent"

            printf '%s\n' "$auth_message" | $TMUX_BIN load-buffer -
            $TMUX_BIN paste-buffer -t "$pm"
            $TMUX_BIN send-keys -t "$pm" Enter
            sleep 1
        fi
    done

    echo -e "${GREEN}✅ Authorized broadcast sent to all PM agents${NC}"
}

# Menu interattivo per autorizzazioni
authorization_menu() {
    while true; do
        clear
        echo -e "${PURPLE}🔐 RIONA AI AUTHORIZATION CONTROL CENTER${NC}"
        echo "========================================"
        echo ""

        # Mostra pending requests
        $AUTH_SYSTEM pending

        echo ""
        echo -e "${CYAN}AUTHORIZATION OPTIONS:${NC}"
        echo "1. Show pending requests"
        echo "2. Authorize request"
        echo "3. Deny request"
        echo "4. Modify request"
        echo "5. Send authorized task"
        echo "6. Run authorized workflow"
        echo "7. Exit"
        echo ""

        read -p "Select option: " choice

        case $choice in
            1)
                show_pending_authorizations
                read -p "Press Enter to continue..."
                ;;
            2)
                read -p "Enter request ID to authorize: " req_id
                handle_authorization_command "AUTHORIZE" "$req_id"
                read -p "Press Enter to continue..."
                ;;
            3)
                read -p "Enter request ID to deny: " req_id
                read -p "Enter reason: " reason
                handle_authorization_command "DENY" "$req_id" "$reason"
                read -p "Press Enter to continue..."
                ;;
            4)
                read -p "Enter request ID to modify: " req_id
                read -p "Enter modification instructions: " instructions
                handle_authorization_command "MODIFY" "$req_id" "$instructions"
                read -p "Press Enter to continue..."
                ;;
            5)
                echo "Available PM agents: ${PM_AGENTS[*]}"
                read -p "Enter PM agent: " pm_agent
                read -p "Enter task: " task
                send_authorized_task "$pm_agent" "$task"
                read -p "Press Enter to continue..."
                ;;
            6)
                echo "Workflow types: full-stack-feature, backend-feature, frontend-feature, deployment"
                read -p "Enter workflow type: " wf_type
                read -p "Enter description: " description
                authorized_workflow "$wf_type" "$description"
                read -p "Press Enter to continue..."
                ;;
            7)
                break
                ;;
        esac
    done
}

# Main
if [ $# -eq 0 ]; then
    echo -e "${PURPLE}🔐 Riona AI Authorized Orchestrator${NC}"
    echo "==================================="
    echo ""
    echo "Usage: $0 <command> [args...]"
    echo ""
    echo "🔐 AUTHORIZED COMMANDS:"
    echo "  delegate <pm-agent> <task>           Send authorized task to PM"
    echo "  workflow <type> <description>        Run authorized workflow"
    echo "  broadcast <message>                  Authorized broadcast to all PMs"
    echo "  auth <AUTHORIZE|DENY|MODIFY> <id>    Handle authorization request"
    echo "  pending                             Show pending authorization requests"
    echo "  menu                                Interactive authorization menu"
    echo ""
    echo "🔄 AUTHORIZATION FLOW:"
    echo "  1. Sub-Agent requests permission from PM"
    echo "  2. PM forwards request to Orchestrator"
    echo "  3. Orchestrator approves/denies/modifies"
    echo "  4. PM relays decision to Sub-Agent"
    echo "  5. Sub-Agent proceeds (if authorized)"
    echo ""
    echo "Examples:"
    echo "  $0 delegate backend-api \"Create user API with authorization\""
    echo "  $0 auth AUTHORIZE 1640995200_api-architect_12345"
    echo "  $0 auth DENY 1640995200_schema-designer_67890 \"Insufficient requirements\""
    echo "  $0 menu"
    exit 1
fi

case "$1" in
    "delegate")
        send_authorized_task "$2" "$3"
        ;;
    "workflow")
        authorized_workflow "$2" "${3:-}"
        ;;
    "broadcast")
        authorized_broadcast "$2"
        ;;
    "auth")
        handle_authorization_command "$2" "${3:-}" "${4:-}"
        ;;
    "pending")
        show_pending_authorizations
        ;;
    "menu")
        authorization_menu
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use $0 without arguments for help"
        exit 1
        ;;
esac