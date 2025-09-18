#!/bin/bash
# Activate Claude Code in existing agent sessions

set -euo pipefail

PROJECT_ROOT="/Users/erik/Desktop/riona_ai/riona-ai"
TMUX_BIN="/opt/homebrew/bin/tmux"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

# PM Agents to activate
PM_AGENTS=("prompt-validator" "task-coordinator" "backend-api" "database" "frontend-ui")

echo -e "${PURPLE}🤖 ACTIVATING CLAUDE CODE IN AGENT SESSIONS${NC}"
echo "=" * 60

activate_claude_in_session() {
    local session_name="$1"

    echo -e "${BLUE}🔄 Activating Claude in $session_name...${NC}"

    # Check if session exists
    if ! $TMUX_BIN has-session -t "$session_name" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Session $session_name not found, creating new one...${NC}"
        $TMUX_BIN new-session -d -s "$session_name" -c "$PROJECT_ROOT"
        sleep 1
    fi

    # Send Claude command
    $TMUX_BIN send-keys -t "$session_name" 'claude' Enter

    echo -e "${GREEN}✅ Claude command sent to $session_name${NC}"

    # Wait for Claude to start
    sleep 3

    # Send initial context
    local agent_context="I am the $session_name agent in the Riona AI multi-agent system. I'm ready to receive and process tasks from the CrewAI orchestrator."

    $TMUX_BIN send-keys -t "$session_name" "$agent_context" Enter

    echo -e "${GREEN}✅ $session_name activated and ready${NC}"
}

# Activate Claude in all PM agent sessions
for agent in "${PM_AGENTS[@]}"; do
    activate_claude_in_session "$agent"
    echo ""
done

echo -e "${PURPLE}🎉 CLAUDE ACTIVATION COMPLETED${NC}"
echo "=" * 40
echo -e "${CYAN}Now testing communication...${NC}"

# Test communication
sleep 5

echo -e "${BLUE}📋 Testing task communication...${NC}"

test_task="Hello! This is a test task from the CrewAI orchestrator. Please confirm you received this message and are ready to work."

for agent in "${PM_AGENTS[@]:0:2}"; do  # Test first 2 agents
    echo -e "${CYAN}📤 Sending test task to $agent...${NC}"
    $TMUX_BIN send-keys -t "$agent" "$test_task" Enter
done

echo ""
echo -e "${GREEN}🎯 ACTIVATION AND TESTING COMPLETED!${NC}"
echo -e "${YELLOW}💡 Check your agent terminals to see Claude Code active${NC}"
echo -e "${YELLOW}💡 You can now use the web interface to send tasks${NC}"