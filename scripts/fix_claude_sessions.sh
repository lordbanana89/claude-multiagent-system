#!/bin/bash
# Fix Claude Sessions - Create real Claude Code sessions for agents

set -euo pipefail

PROJECT_ROOT="/Users/erik/Desktop/riona_ai/riona-ai"
TMUX_BIN="/opt/homebrew/bin/tmux"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${PURPLE}🔧 FIXING CLAUDE CODE SESSIONS${NC}"
echo "Creating real Claude Code sessions for agents"
echo "=" * 50

# PM Agents that need Claude Code
CLAUDE_AGENTS=("claude-prompt-validator" "claude-task-coordinator" "claude-backend-api")

create_real_claude_session() {
    local session_name="$1"
    local agent_role="$2"

    echo -e "${BLUE}🤖 Creating real Claude session: $session_name${NC}"

    # Kill existing session if it exists
    if $TMUX_BIN has-session -t "$session_name" 2>/dev/null; then
        echo -e "${YELLOW}   Terminating existing session...${NC}"
        $TMUX_BIN kill-session -t "$session_name"
        sleep 1
    fi

    # Create new session and start Claude Code
    $TMUX_BIN new-session -d -s "$session_name" -c "$PROJECT_ROOT"

    # Give time for session to initialize
    sleep 2

    # Start Claude Code
    echo -e "${CYAN}   Starting Claude Code...${NC}"
    $TMUX_BIN send-keys -t "$session_name" "claude" Enter

    # Wait for Claude to start
    sleep 8

    # Send initial context to Claude
    local context="I am the $agent_role agent in the Riona AI multi-agent system. I specialize in $agent_role tasks and am ready to collaborate with other agents through the CrewAI orchestrator."

    echo -e "${CYAN}   Sending context to Claude...${NC}"
    $TMUX_BIN send-keys -t "$session_name" "$context" Enter

    # Wait for context to be processed
    sleep 3

    echo -e "${GREEN}✅ $session_name created and ready${NC}"
}

# Create real Claude sessions
create_real_claude_session "claude-prompt-validator" "prompt validation and requirement analysis"
create_real_claude_session "claude-task-coordinator" "task coordination and project management"
create_real_claude_session "claude-backend-api" "backend API development and architecture"

echo ""
echo -e "${PURPLE}🧪 TESTING REAL CLAUDE COMMUNICATION${NC}"
echo "=" * 40

# Test communication with real Claude sessions
sleep 3

test_task="🧪 TEST: Please respond with 'CLAUDE AGENT READY' if you received this message and are functioning correctly."

for session in "claude-prompt-validator" "claude-task-coordinator"; do
    echo -e "${BLUE}📤 Testing $session...${NC}"

    $TMUX_BIN send-keys -t "$session" "$test_task" Enter

    # Wait for response
    sleep 5

    # Check for response
    output=$($TMUX_BIN capture-pane -t "$session" -p)
    if echo "$output" | grep -q "CLAUDE AGENT READY\|Claude Code\|claude"; then
        echo -e "${GREEN}✅ $session is responding${NC}"
    else
        echo -e "${YELLOW}⚠️  $session may need more time to start${NC}"
        echo "   Last output: $(echo "$output" | tail -1)"
    fi
    echo ""
done

echo -e "${PURPLE}🎉 CLAUDE SESSIONS SETUP COMPLETED!${NC}"
echo ""
echo -e "${CYAN}📋 Usage Instructions:${NC}"
echo "1. Use session names: claude-prompt-validator, claude-task-coordinator, claude-backend-api"
echo "2. These have REAL Claude Code running"
echo "3. Update web interface to use these session names"
echo ""
echo -e "${YELLOW}💡 To connect directly to a Claude session:${NC}"
echo "   tmux attach-session -t claude-prompt-validator"