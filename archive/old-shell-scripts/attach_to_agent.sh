#!/bin/bash
# Script to easily attach to Claude agent TMUX sessions

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}         Claude Agent Terminal Access           ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# Get all Claude sessions
SESSIONS=$(tmux list-sessions 2>/dev/null | grep -i claude- | cut -d: -f1)

if [ -z "$SESSIONS" ]; then
    echo -e "${RED}No Claude agent sessions found!${NC}"
    echo ""
    echo "Start agents with: ./start_claude_agent_with_mcp.sh"
    exit 1
fi

echo -e "${GREEN}Available Claude Agent Sessions:${NC}"
echo ""

# List sessions with numbers
i=1
declare -a SESSION_ARRAY
while IFS= read -r session; do
    SESSION_ARRAY[$i]=$session
    echo -e "  ${YELLOW}$i)${NC} $session"

    # Check if Claude is running in session
    PANE_CONTENT=$(tmux capture-pane -t "$session" -p 2>/dev/null | tail -5)
    if echo "$PANE_CONTENT" | grep -q "claude"; then
        echo -e "     ${GREEN}✓ Claude CLI Active${NC}"
    else
        echo -e "     ${YELLOW}○ Session exists (Claude may not be running)${NC}"
    fi

    i=$((i+1))
done <<< "$SESSIONS"

echo ""
echo -e "${BLUE}Actions:${NC}"
echo "  Enter number to attach to session"
echo "  'a' to attach to all in new terminal windows"
echo "  'q' to quit"
echo ""
read -p "Choice: " choice

if [[ "$choice" == "q" ]]; then
    exit 0
elif [[ "$choice" == "a" ]]; then
    echo -e "${YELLOW}Opening all sessions in new terminal windows...${NC}"
    for session in "${SESSION_ARRAY[@]}"; do
        if [ ! -z "$session" ]; then
            osascript -e "tell app \"Terminal\" to do script \"tmux attach -t '$session'\""
            sleep 0.5
        fi
    done
    echo -e "${GREEN}Done! Check your Terminal windows.${NC}"
elif [[ "$choice" =~ ^[0-9]+$ ]]; then
    SESSION="${SESSION_ARRAY[$choice]}"
    if [ ! -z "$SESSION" ]; then
        echo -e "${GREEN}Attaching to $SESSION...${NC}"
        echo -e "${YELLOW}(Use Ctrl+B then D to detach)${NC}"
        sleep 1
        tmux attach -t "$SESSION"
    else
        echo -e "${RED}Invalid choice!${NC}"
    fi
else
    echo -e "${RED}Invalid choice!${NC}"
fi