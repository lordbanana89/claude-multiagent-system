#!/bin/bash
# Authorization System - Catena di autorizzazione gerarchica

set -euo pipefail

PROJECT_ROOT="/Users/erik/Desktop/riona_ai/riona-ai"
AUTH_DIR="$PROJECT_ROOT/.riona/agents/authorization"
PENDING_DIR="$AUTH_DIR/pending"
APPROVED_DIR="$AUTH_DIR/approved"

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

# Crea directory se non esistono
mkdir -p "$PENDING_DIR" "$APPROVED_DIR"

# Funzione per creare richiesta di autorizzazione
create_authorization_request() {
    local sub_agent="$1"
    local pm_agent="$2"
    local task="$3"
    local request_id=$(date +%s)_${sub_agent}_${RANDOM}

    echo -e "${CYAN}🔐 CREATING AUTHORIZATION REQUEST${NC}"
    echo "Sub-Agent: $sub_agent"
    echo "PM Agent: $pm_agent"
    echo "Request ID: $request_id"
    echo ""

    # Crea file di richiesta
    cat > "$PENDING_DIR/$request_id.json" << EOF
{
    "request_id": "$request_id",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "sub_agent": "$sub_agent",
    "pm_agent": "$pm_agent",
    "task": "$task",
    "status": "pending_pm_review",
    "chain": [
        {"step": 1, "actor": "sub_agent", "action": "request_permission", "status": "completed"},
        {"step": 2, "actor": "pm_agent", "action": "review_and_forward", "status": "pending"},
        {"step": 3, "actor": "orchestrator", "action": "authorize", "status": "waiting"},
        {"step": 4, "actor": "pm_agent", "action": "relay_authorization", "status": "waiting"},
        {"step": 5, "actor": "sub_agent", "action": "proceed_with_task", "status": "waiting"}
    ]
}
EOF

    echo -e "${GREEN}✅ Authorization request created: $request_id${NC}"
    return 0
}

# Funzione per inviare richiesta PM → Orchestrator
forward_to_orchestrator() {
    local request_id="$1"
    local request_file="$PENDING_DIR/$request_id.json"

    if [ ! -f "$request_file" ]; then
        echo -e "${RED}❌ Request file not found: $request_id${NC}"
        return 1
    fi

    local sub_agent=$(jq -r '.sub_agent' "$request_file")
    local pm_agent=$(jq -r '.pm_agent' "$request_file")
    local task=$(jq -r '.task' "$request_file")

    echo -e "${PURPLE}🔄 PM FORWARDING TO ORCHESTRATOR${NC}"
    echo "Request ID: $request_id"
    echo "From PM: $pm_agent"
    echo "For Sub-Agent: $sub_agent"
    echo ""

    # Aggiorna status
    jq '.status = "pending_orchestrator_authorization" | .chain[1].status = "completed" | .chain[2].status = "pending"' "$request_file" > "$request_file.tmp" && mv "$request_file.tmp" "$request_file"

    # Invia messaggio all'orchestrator
    local orchestrator_message="🔐 AUTHORIZATION REQUEST

Request ID: $request_id
PM Agent: $pm_agent
Sub-Agent: $sub_agent
Task: $task

AUTHORIZATION NEEDED:
The $pm_agent PM is requesting authorization for sub-agent $sub_agent to proceed with the following task.

Please review and respond:
- AUTHORIZE: Reply 'AUTHORIZE $request_id'
- DENY: Reply 'DENY $request_id [reason]'
- MODIFY: Reply 'MODIFY $request_id [instructions]'

Awaiting your decision..."

    echo -e "${BLUE}📤 Sending authorization request to orchestrator terminal...${NC}"
    printf '%s\n' "$orchestrator_message" | $TMUX_BIN load-buffer -

    # Invia al terminale corrente (orchestrator)
    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}$orchestrator_message${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
    echo ""

    return 0
}

# Funzione per processare autorizzazione dall'orchestrator
process_orchestrator_decision() {
    local decision="$1"
    local request_id="$2"
    local instructions="${3:-}"

    local request_file="$PENDING_DIR/$request_id.json"

    if [ ! -f "$request_file" ]; then
        echo -e "${RED}❌ Request not found: $request_id${NC}"
        return 1
    fi

    local sub_agent=$(jq -r '.sub_agent' "$request_file")
    local pm_agent=$(jq -r '.pm_agent' "$request_file")
    local task=$(jq -r '.task' "$request_file")

    case "$decision" in
        "AUTHORIZE")
            echo -e "${GREEN}✅ ORCHESTRATOR AUTHORIZATION: APPROVED${NC}"
            echo "Request ID: $request_id"
            echo ""

            # Aggiorna status
            jq '.status = "authorized" | .chain[2].status = "completed" | .chain[3].status = "pending" | .orchestrator_decision = "AUTHORIZE" | .orchestrator_timestamp = "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"' "$request_file" > "$request_file.tmp" && mv "$request_file.tmp" "$request_file"

            # Invia autorizzazione al PM
            send_authorization_to_pm "$request_id"
            ;;
        "DENY")
            echo -e "${RED}❌ ORCHESTRATOR AUTHORIZATION: DENIED${NC}"
            echo "Request ID: $request_id"
            echo "Reason: $instructions"
            echo ""

            # Aggiorna status
            jq '.status = "denied" | .chain[2].status = "completed" | .orchestrator_decision = "DENY" | .orchestrator_reason = "'"$instructions"'" | .orchestrator_timestamp = "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"' "$request_file" > "$request_file.tmp" && mv "$request_file.tmp" "$request_file"

            # Notifica PM della negazione
            send_denial_to_pm "$request_id" "$instructions"
            ;;
        "MODIFY")
            echo -e "${YELLOW}⚠️ ORCHESTRATOR AUTHORIZATION: MODIFY${NC}"
            echo "Request ID: $request_id"
            echo "Instructions: $instructions"
            echo ""

            # Aggiorna status
            jq '.status = "modification_required" | .chain[2].status = "completed" | .orchestrator_decision = "MODIFY" | .orchestrator_instructions = "'"$instructions"'" | .orchestrator_timestamp = "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"' "$request_file" > "$request_file.tmp" && mv "$request_file.tmp" "$request_file"

            # Invia istruzioni di modifica al PM
            send_modification_to_pm "$request_id" "$instructions"
            ;;
    esac
}

# Funzione per inviare autorizzazione al PM
send_authorization_to_pm() {
    local request_id="$1"
    local request_file="$PENDING_DIR/$request_id.json"

    local sub_agent=$(jq -r '.sub_agent' "$request_file")
    local pm_agent=$(jq -r '.pm_agent' "$request_file")
    local task=$(jq -r '.task' "$request_file")

    echo -e "${BLUE}📤 Sending authorization to PM: $pm_agent${NC}"

    local pm_message="✅ AUTHORIZATION GRANTED

Request ID: $request_id
Sub-Agent: $sub_agent
Task: $task

ORCHESTRATOR DECISION: APPROVED

Please relay this authorization to your sub-agent $sub_agent and instruct them to proceed with the task.

Send to sub-agent: 'PROCEED $request_id - You are authorized to begin work on: $task'"

    if $TMUX_BIN has-session -t "$pm_agent" 2>/dev/null; then
        printf '%s\n' "$pm_message" | $TMUX_BIN load-buffer -
        $TMUX_BIN paste-buffer -t "$pm_agent"
        $TMUX_BIN send-keys -t "$pm_agent" Enter

        echo -e "${GREEN}✅ Authorization sent to PM: $pm_agent${NC}"

        # Aggiorna status
        jq '.chain[3].status = "completed" | .chain[4].status = "pending"' "$request_file" > "$request_file.tmp" && mv "$request_file.tmp" "$request_file"
    else
        echo -e "${RED}❌ PM agent $pm_agent not found${NC}"
    fi
}

# Funzione per inviare negazione al PM
send_denial_to_pm() {
    local request_id="$1"
    local reason="$2"
    local request_file="$PENDING_DIR/$request_id.json"

    local sub_agent=$(jq -r '.sub_agent' "$request_file")
    local pm_agent=$(jq -r '.pm_agent' "$request_file")

    local pm_message="❌ AUTHORIZATION DENIED

Request ID: $request_id
Sub-Agent: $sub_agent

ORCHESTRATOR DECISION: DENIED
Reason: $reason

Please inform your sub-agent $sub_agent that the request has been denied and provide alternative guidance."

    if $TMUX_BIN has-session -t "$pm_agent" 2>/dev/null; then
        printf '%s\n' "$pm_message" | $TMUX_BIN load-buffer -
        $TMUX_BIN paste-buffer -t "$pm_agent"
        $TMUX_BIN send-keys -t "$pm_agent" Enter

        echo -e "${RED}❌ Denial sent to PM: $pm_agent${NC}"
    fi
}

# Funzione per mostrare richieste pending
show_pending_requests() {
    echo -e "${PURPLE}🔐 PENDING AUTHORIZATION REQUESTS${NC}"
    echo "=================================="
    echo ""

    if [ ! "$(ls -A "$PENDING_DIR" 2>/dev/null)" ]; then
        echo -e "${YELLOW}No pending requests${NC}"
        return 0
    fi

    for request_file in "$PENDING_DIR"/*.json; do
        [ ! -f "$request_file" ] && continue

        local request_id=$(basename "$request_file" .json)
        local sub_agent=$(jq -r '.sub_agent' "$request_file")
        local pm_agent=$(jq -r '.pm_agent' "$request_file")
        local status=$(jq -r '.status' "$request_file")
        local task=$(jq -r '.task' "$request_file" | cut -c1-60)

        echo -e "${CYAN}Request ID: $request_id${NC}"
        echo "  Sub-Agent: $sub_agent"
        echo "  PM Agent: $pm_agent"
        echo "  Status: $status"
        echo "  Task: $task..."
        echo ""
    done
}

# Main
case "${1:-}" in
    "create")
        create_authorization_request "$2" "$3" "$4"
        ;;
    "forward")
        forward_to_orchestrator "$2"
        ;;
    "authorize")
        process_orchestrator_decision "AUTHORIZE" "$2"
        ;;
    "deny")
        process_orchestrator_decision "DENY" "$2" "$3"
        ;;
    "modify")
        process_orchestrator_decision "MODIFY" "$2" "$3"
        ;;
    "pending")
        show_pending_requests
        ;;
    *)
        echo -e "${PURPLE}Authorization System - Catena di autorizzazione gerarchica${NC}"
        echo "========================================================="
        echo ""
        echo "Usage: $0 <command> [args...]"
        echo ""
        echo "Commands:"
        echo "  create <sub-agent> <pm-agent> <task>    Create authorization request"
        echo "  forward <request-id>                   Forward request to orchestrator"
        echo "  authorize <request-id>                 Authorize request"
        echo "  deny <request-id> <reason>             Deny request"
        echo "  modify <request-id> <instructions>     Request modifications"
        echo "  pending                                Show pending requests"
        echo ""
        echo "Authorization Chain:"
        echo "  1. Sub-Agent creates request"
        echo "  2. PM reviews and forwards to Orchestrator"
        echo "  3. Orchestrator authorizes/denies/modifies"
        echo "  4. PM relays decision to Sub-Agent"
        echo "  5. Sub-Agent proceeds (if authorized)"
        ;;
esac