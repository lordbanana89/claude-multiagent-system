#!/bin/bash
# Interactive Terminal Manager for Claude Agents

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

clear

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         ${CYAN}🤖 Claude Multi-Agent Terminal Manager${BLUE}               ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to check if Claude is running in session
check_claude_running() {
    local session=$1
    local output=$(tmux capture-pane -t "$session" -p 2>/dev/null | tail -10)

    if echo "$output" | grep -q "Welcome to Claude"; then
        return 0  # Claude is running
    elif echo "$output" | grep -q "claude"; then
        return 0  # Claude is running
    else
        return 1  # Claude not running
    fi
}

# Function to start Claude in session
start_claude_in_session() {
    local session=$1
    local agent_name=$2

    echo -e "${YELLOW}Starting Claude in session $session...${NC}"

    # Set environment variables
    tmux send-keys -t "$session" "export CLAUDE_AGENT_NAME='$agent_name'" Enter
    tmux send-keys -t "$session" "export MCP_DB_PATH='/tmp/mcp_state.db'" Enter
    tmux send-keys -t "$session" "export CLAUDE_PROJECT_DIR='/Users/erik/Desktop/claude-multiagent-system'" Enter

    # Start Claude
    tmux send-keys -t "$session" "cd /Users/erik/Desktop/claude-multiagent-system" Enter
    tmux send-keys -t "$session" "claude" Enter

    sleep 2

    if check_claude_running "$session"; then
        echo -e "${GREEN}✅ Claude started successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  Claude may be starting...${NC}"
    fi
}

# Define standard agents
declare -A AGENTS
AGENTS["backend-api"]="Backend API Agent"
AGENTS["database"]="Database Agent"
AGENTS["frontend-ui"]="Frontend UI Agent"
AGENTS["testing"]="Testing Agent"
AGENTS["supervisor"]="Supervisor Agent"
AGENTS["master"]="Master Agent"
AGENTS["instagram"]="Instagram Agent"
AGENTS["deployment"]="Deployment Agent"
AGENTS["queue-manager"]="Queue Manager Agent"

echo -e "${CYAN}📊 System Status${NC}"
echo -e "${CYAN}────────────────────────────────────────────────────────${NC}"
echo ""

# Check each agent
for agent_key in "${!AGENTS[@]}"; do
    agent_name="${AGENTS[$agent_key]}"
    session_name="claude-$agent_key"

    printf "${BLUE}%-20s${NC}" "$agent_name:"

    # Check if session exists
    if tmux has-session -t "$session_name" 2>/dev/null; then
        if check_claude_running "$session_name"; then
            echo -e " ${GREEN}● Session Active - Claude Running${NC}"
        else
            echo -e " ${YELLOW}● Session Active - Claude NOT Running${NC}"
        fi
    else
        echo -e " ${RED}○ No Session${NC}"
    fi
done

echo ""
echo -e "${CYAN}────────────────────────────────────────────────────────${NC}"
echo ""
echo -e "${MAGENTA}Actions:${NC}"
echo "  1) Start ALL agents with MCP"
echo "  2) Start specific agent"
echo "  3) Attach to agent terminal"
echo "  4) Stop agent"
echo "  5) View MCP activities"
echo "  6) Clean up orphaned sessions"
echo "  7) Status refresh"
echo "  q) Quit"
echo ""
read -p "Choice: " choice

case $choice in
    1)
        echo -e "${YELLOW}Starting all agents...${NC}"
        for agent_key in "${!AGENTS[@]}"; do
            session_name="claude-$agent_key"
            if ! tmux has-session -t "$session_name" 2>/dev/null; then
                tmux new-session -d -s "$session_name"
                start_claude_in_session "$session_name" "$agent_key"
            else
                echo -e "${CYAN}$agent_key already has session${NC}"
            fi
        done
        ;;

    2)
        echo "Select agent to start:"
        i=1
        declare -a AGENT_ARRAY
        for agent_key in "${!AGENTS[@]}"; do
            echo "  $i) ${AGENTS[$agent_key]}"
            AGENT_ARRAY[$i]=$agent_key
            ((i++))
        done
        read -p "Number: " num

        if [ ! -z "${AGENT_ARRAY[$num]}" ]; then
            agent_key="${AGENT_ARRAY[$num]}"
            session_name="claude-$agent_key"

            if ! tmux has-session -t "$session_name" 2>/dev/null; then
                tmux new-session -d -s "$session_name"
            fi

            start_claude_in_session "$session_name" "$agent_key"
        fi
        ;;

    3)
        echo "Select agent to attach:"
        SESSIONS=$(tmux list-sessions 2>/dev/null | grep claude- | cut -d: -f1)
        i=1
        declare -a SESSION_ARRAY
        while IFS= read -r session; do
            echo "  $i) $session"
            SESSION_ARRAY[$i]=$session
            ((i++))
        done <<< "$SESSIONS"

        read -p "Number: " num

        if [ ! -z "${SESSION_ARRAY[$num]}" ]; then
            echo -e "${GREEN}Attaching to ${SESSION_ARRAY[$num]}...${NC}"
            echo -e "${YELLOW}Use Ctrl+B then D to detach${NC}"
            sleep 1
            tmux attach -t "${SESSION_ARRAY[$num]}"
        fi
        ;;

    4)
        echo "Select agent to stop:"
        SESSIONS=$(tmux list-sessions 2>/dev/null | grep claude- | cut -d: -f1)
        i=1
        declare -a SESSION_ARRAY
        while IFS= read -r session; do
            echo "  $i) $session"
            SESSION_ARRAY[$i]=$session
            ((i++))
        done <<< "$SESSIONS"

        read -p "Number: " num

        if [ ! -z "${SESSION_ARRAY[$num]}" ]; then
            tmux kill-session -t "${SESSION_ARRAY[$num]}"
            echo -e "${GREEN}Stopped ${SESSION_ARRAY[$num]}${NC}"
        fi
        ;;

    5)
        echo -e "${CYAN}Recent MCP Activities:${NC}"
        sqlite3 -column -header /tmp/mcp_state.db \
            "SELECT substr(agent,1,15) as Agent,
                    substr(activity,1,50) as Activity,
                    datetime(timestamp) as Time
             FROM activities
             ORDER BY timestamp DESC
             LIMIT 10;" 2>/dev/null || echo "No activities found"
        ;;

    6)
        echo -e "${YELLOW}Cleaning up orphaned sessions...${NC}"
        # Kill sessions with weird names
        tmux list-sessions 2>/dev/null | grep -E "claude-.*-agent" | cut -d: -f1 | while read session; do
            echo "  Removing: $session"
            tmux kill-session -t "$session"
        done
        echo -e "${GREEN}Cleanup complete${NC}"
        ;;

    7)
        exec "$0"
        ;;

    q)
        exit 0
        ;;

    *)
        echo -e "${RED}Invalid choice${NC}"
        ;;
esac

echo ""
echo -e "${CYAN}Press Enter to continue...${NC}"
read
exec "$0"