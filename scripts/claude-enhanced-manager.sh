#!/bin/bash
# Claude-Enhanced Agent Manager
# Sistema completamente integrato con terminali Claude Code esistenti

set -euo pipefail

PROJECT_ROOT="/Users/erik/Desktop/riona_ai/riona-ai"
AGENTS_DIR="$PROJECT_ROOT/.riona/agents"
CREWAI_DIR="$AGENTS_DIR/crewai"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

unset TMUX 2>/dev/null || true
TMUX_BIN="/opt/homebrew/bin/tmux"

# Claude PM Agents
CLAUDE_PM_AGENTS=("prompt-validator" "task-coordinator" "backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")

# Enhanced header specifically for Claude integration
show_claude_header() {
    clear
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                    🤖 CLAUDE-ENHANCED AGENT MANAGER                   ║${NC}"
    echo -e "${PURPLE}║                                                                      ║${NC}"
    echo -e "${PURPLE}║  🧠 Claude Code Integration | 🔗 Direct Terminal Communication       ║${NC}"
    echo -e "${PURPLE}║                                                                      ║${NC}"
    echo -e "${PURPLE}║            No OpenAI needed - Pure Claude orchestration!             ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Check Claude integration status
check_claude_integration() {
    local active_claude_sessions=0
    local total_sessions=0

    echo -e "${CYAN}🧠 CLAUDE CODE INTEGRATION STATUS:${NC}"
    echo "──────────────────────────────────────────────────────────────────────"

    for agent in "${CLAUDE_PM_AGENTS[@]}"; do
        total_sessions=$((total_sessions + 1))
        if $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
            # Check if it's actually a Claude session
            capture_output=$($TMUX_BIN capture-pane -t "$agent" -p)
            if echo "$capture_output" | grep -q -E "(Claude Code|claude|Claude)" || echo "$capture_output" | grep -q "╭.*Claude"; then
                echo -e "  ${GREEN}✅ $agent${NC} - Claude Code Active"
                active_claude_sessions=$((active_claude_sessions + 1))
            else
                echo -e "  ${YELLOW}⚠️  $agent${NC} - Session active but not Claude"
            fi
        else
            echo -e "  ${RED}❌ $agent${NC} - Session not found"
        fi
    done

    echo ""
    echo -e "  ${CYAN}Claude Sessions Active:${NC} $active_claude_sessions/$total_sessions"

    # Check integration tools
    echo -e "${CYAN}🔧 INTEGRATION TOOLS:${NC}"
    echo "──────────────────────────────────────────────────────────────────────"

    if [[ -f "$CREWAI_DIR/claude_orchestrator.py" ]]; then
        echo -e "  ${GREEN}✅ Claude Orchestrator${NC} - Available"
    else
        echo -e "  ${RED}❌ Claude Orchestrator${NC} - Missing"
    fi

    if [[ -f "$CREWAI_DIR/claude_integration.py" ]]; then
        echo -e "  ${GREEN}✅ Claude Integration Tools${NC} - Available"
    else
        echo -e "  ${RED}❌ Claude Integration Tools${NC} - Missing"
    fi

    if command -v python3 >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ Python 3${NC} - Available"
    else
        echo -e "  ${RED}❌ Python 3${NC} - Not available"
    fi

    echo ""
}

# Enhanced main menu for Claude integration
claude_main_menu() {
    while true; do
        show_claude_header
        check_claude_integration

        echo ""
        echo -e "${CYAN}🎛️  CLAUDE-ENHANCED OPERATIONS:${NC}"
        echo "══════════════════════════════════════════════════════════════════════"
        echo "  ${BLUE}1.${NC} 🧠 Intelligent Claude Coordination    (Direct terminal orchestration)"
        echo "  ${BLUE}2.${NC} 📋 Send Task to Claude Agent          (Individual agent tasking)"
        echo "  ${BLUE}3.${NC} 🎯 Full-Stack Project Coordination    (Multi-agent collaboration)"
        echo "  ${BLUE}4.${NC} 📊 Monitor Claude Agent Activity      (Real-time progress tracking)"
        echo "  ${BLUE}5.${NC} 🔗 Open Claude Agent Terminals        (Direct terminal access)"
        echo "  ${BLUE}6.${NC} 🧪 Test Claude Integration           (Verify system functionality)"
        echo "  ${BLUE}7.${NC} ⚙️  Claude System Configuration       (Setup and optimization)"
        echo "  ${BLUE}8.${NC} 📚 Documentation & Examples          (Usage guide)"
        echo "  ${BLUE}9.${NC} Exit Claude Manager"
        echo ""

        read -p "$(echo -e "${YELLOW}Select Claude operation [1-9]: ${NC}")" choice

        case $choice in
            1) intelligent_claude_coordination ;;
            2) send_task_to_claude_agent ;;
            3) fullstack_project_coordination ;;
            4) monitor_claude_activity ;;
            5) open_claude_terminals ;;
            6) test_claude_integration ;;
            7) claude_system_configuration ;;
            8) documentation_examples ;;
            9)
                echo -e "${GREEN}🎯 Exiting Claude-Enhanced Manager...${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid option. Press Enter to continue...${NC}"
                read
                ;;
        esac
    done
}

# Intelligent Claude Coordination
intelligent_claude_coordination() {
    clear
    echo -e "${PURPLE}🧠 INTELLIGENT CLAUDE COORDINATION${NC}"
    echo "══════════════════════════════════════════════════════════════════════"
    echo ""

    echo "Available coordination modes:"
    echo ""
    echo "  ${BLUE}1.${NC} Intelligent Task Distribution    (Auto-analyze and distribute)"
    echo "  ${BLUE}2.${NC} Full-Stack Feature Coordination  (Complete feature development)"
    echo "  ${BLUE}3.${NC} Custom Multi-Agent Workflow     (Define custom coordination)"
    echo "  ${BLUE}4.${NC} System Analysis & Planning       (Comprehensive system review)"
    echo "  ${BLUE}5.${NC} Return to Main Menu"
    echo ""

    read -p "$(echo -e "${YELLOW}Select coordination mode [1-5]: ${NC}")" coord_choice

    case $coord_choice in
        1)
            echo ""
            read -p "Describe the project/task for intelligent distribution: " project_desc
            if [[ -n "$project_desc" ]]; then
                echo -e "${BLUE}🧠 Running intelligent task distribution...${NC}"
                python3 -c "
import sys
sys.path.append('$CREWAI_DIR')
from claude_orchestrator import ClaudeNativeOrchestrator
orchestrator = ClaudeNativeOrchestrator()
result = orchestrator.intelligent_task_distribution('$project_desc')
print(f'✅ Task distributed to {len(result[\"required_teams\"])} Claude agents')
print(f'Teams involved: {\" \".join(result[\"required_teams\"])}')
"
                echo -e "${GREEN}✅ Intelligent coordination completed!${NC}"
            fi
            read -p "Press Enter to continue..."
            ;;
        2)
            echo ""
            read -p "Describe the full-stack feature to develop: " feature_desc
            if [[ -n "$feature_desc" ]]; then
                echo -e "${BLUE}🚀 Coordinating full-stack development...${NC}"
                python3 -c "
import sys
sys.path.append('$CREWAI_DIR')
from claude_orchestrator import ClaudeNativeOrchestrator
orchestrator = ClaudeNativeOrchestrator()
result = orchestrator.coordinate_full_stack_feature('$feature_desc')
print(f'✅ Full-stack coordination initiated')
print(f'Active coordination steps: {result[\"active_agents\"]}')
"
                echo -e "${GREEN}✅ Full-stack coordination in progress!${NC}"
                echo "Check individual Claude agent terminals for detailed progress."
            fi
            read -p "Press Enter to continue..."
            ;;
        3)
            echo ""
            echo "Custom workflow coordination coming soon..."
            echo "This will allow you to define custom agent interactions."
            read -p "Press Enter to continue..."
            ;;
        4)
            echo -e "${BLUE}📊 Running system analysis...${NC}"
            python3 -c "
import sys
sys.path.append('$CREWAI_DIR')
from claude_orchestrator import ClaudeNativeOrchestrator
orchestrator = ClaudeNativeOrchestrator()
progress = orchestrator.monitor_agent_progress()
active = len([a for a in progress['agents'].values() if a['status'] == 'active'])
print(f'System Status: {active}/9 Claude agents active')
print('Ready for intelligent coordination!')
"
            read -p "Press Enter to continue..."
            ;;
        5)
            return
            ;;
    esac
}

# Send Task to Individual Claude Agent
send_task_to_claude_agent() {
    clear
    echo -e "${PURPLE}📋 SEND TASK TO CLAUDE AGENT${NC}"
    echo "══════════════════════════════════════════════════════════════════════"
    echo ""

    echo "Available Claude agents:"
    echo ""
    for i in "${!CLAUDE_PM_AGENTS[@]}"; do
        local agent="${CLAUDE_PM_AGENTS[$i]}"
        local num=$((i + 1))
        if $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
            echo -e "  ${BLUE}$num.${NC} ${GREEN}$agent${NC} - Active"
        else
            echo -e "  ${BLUE}$num.${NC} ${RED}$agent${NC} - Inactive"
        fi
    done

    echo ""
    read -p "Select Claude agent [1-${#CLAUDE_PM_AGENTS[@]}]: " agent_num

    if [[ $agent_num -ge 1 && $agent_num -le ${#CLAUDE_PM_AGENTS[@]} ]]; then
        local selected_agent="${CLAUDE_PM_AGENTS[$((agent_num - 1))]}"

        echo ""
        read -p "Enter task for $selected_agent: " task_description

        if [[ -n "$task_description" ]]; then
            # Send task using Claude orchestrator
            python3 -c "
import sys
sys.path.append('$CREWAI_DIR')
from claude_orchestrator import ClaudeNativeOrchestrator
orchestrator = ClaudeNativeOrchestrator()
success = orchestrator.send_task_to_claude('$selected_agent', '$task_description')
if success:
    print('✅ Task sent successfully to $selected_agent')
else:
    print('❌ Failed to send task to $selected_agent')
"

            echo ""
            echo -e "${CYAN}💡 Tip: Check the $selected_agent terminal to see the task and provide your response.${NC}"
        fi
    else
        echo -e "${RED}Invalid selection.${NC}"
    fi

    read -p "Press Enter to continue..."
}

# Monitor Claude Activity
monitor_claude_activity() {
    while true; do
        clear
        echo -e "${PURPLE}📊 CLAUDE AGENT ACTIVITY MONITOR${NC}"
        echo "══════════════════════════════════════════════════════════════════════"
        echo ""

        # Real-time monitoring
        python3 -c "
import sys
sys.path.append('$CREWAI_DIR')
from claude_orchestrator import ClaudeNativeOrchestrator
import time

orchestrator = ClaudeNativeOrchestrator()
progress = orchestrator.monitor_agent_progress()

print(f'📊 SYSTEM STATUS - {progress[\"timestamp\"]}')
print('=' * 60)

for agent, info in progress['agents'].items():
    if info['status'] == 'active':
        print(f'✅ {agent:20} | Active | Last: {info[\"last_checked\"]}')
    else:
        print(f'❌ {agent:20} | Inactive | Last: {info[\"last_checked\"]}')

active_count = len([a for a in progress['agents'].values() if a['status'] == 'active'])
print(f'\\n📈 Summary: {active_count}/9 agents active')
"

        echo ""
        echo -e "${YELLOW}🔄 Auto-refresh in 10 seconds... (Press 'q' to quit, 'r' to refresh now)${NC}"

        if read -t 10 -n 1 key; then
            case $key in
                'q'|'Q') return ;;
                'r'|'R') continue ;;
            esac
        fi
    done
}

# Open Claude Terminals
open_claude_terminals() {
    clear
    echo -e "${PURPLE}🔗 OPEN CLAUDE AGENT TERMINALS${NC}"
    echo "══════════════════════════════════════════════════════════════════════"
    echo ""

    echo "  ${BLUE}1.${NC} Open All Active Claude Terminals"
    echo "  ${BLUE}2.${NC} Open Specific Claude Terminal"
    echo "  ${BLUE}3.${NC} Open Core Team Terminals (first 5)"
    echo "  ${BLUE}4.${NC} Return to Main Menu"
    echo ""

    read -p "$(echo -e "${YELLOW}Select option [1-4]: ${NC}")" terminal_choice

    case $terminal_choice in
        1)
            echo -e "${BLUE}Opening all active Claude terminals...${NC}"
            for agent in "${CLAUDE_PM_AGENTS[@]}"; do
                if $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
                    osascript -e "tell application \"Terminal\" to activate" \
                              -e "tell application \"Terminal\" to do script \"echo '🧠 $agent CLAUDE AGENT'; tmux attach-session -t $agent\"" &
                    sleep 0.5
                fi
            done
            ;;
        2)
            echo ""
            echo "Available agents:"
            for i in "${!CLAUDE_PM_AGENTS[@]}"; do
                local agent="${CLAUDE_PM_AGENTS[$i]}"
                local num=$((i + 1))
                echo "  $num. $agent"
            done
            read -p "Select agent [1-${#CLAUDE_PM_AGENTS[@]}]: " agent_num
            if [[ $agent_num -ge 1 && $agent_num -le ${#CLAUDE_PM_AGENTS[@]} ]]; then
                local selected_agent="${CLAUDE_PM_AGENTS[$((agent_num - 1))]}"
                echo -e "${BLUE}Opening terminal for $selected_agent...${NC}"
                osascript -e "tell application \"Terminal\" to activate" \
                          -e "tell application \"Terminal\" to do script \"echo '🧠 $selected_agent CLAUDE AGENT'; tmux attach-session -t $selected_agent\"" &
            fi
            ;;
        3)
            echo -e "${BLUE}Opening core team terminals...${NC}"
            for agent in "${CLAUDE_PM_AGENTS[@]:0:5}"; do
                if $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
                    osascript -e "tell application \"Terminal\" to activate" \
                              -e "tell application \"Terminal\" to do script \"echo '🧠 $agent CLAUDE AGENT'; tmux attach-session -t $agent\"" &
                    sleep 0.3
                fi
            done
            ;;
        4)
            return
            ;;
    esac

    read -p "Press Enter to continue..."
}

# Test Claude Integration
test_claude_integration() {
    clear
    echo -e "${PURPLE}🧪 TEST CLAUDE INTEGRATION${NC}"
    echo "══════════════════════════════════════════════════════════════════════"
    echo ""

    echo -e "${BLUE}Running comprehensive Claude integration test...${NC}"
    echo ""

    python3 "$CREWAI_DIR/claude_integration.py"

    echo ""
    read -p "Press Enter to continue..."
}

# Documentation
documentation_examples() {
    clear
    echo -e "${PURPLE}📚 CLAUDE INTEGRATION DOCUMENTATION${NC}"
    echo "══════════════════════════════════════════════════════════════════════"
    echo ""

    echo -e "${YELLOW}🧠 Claude-Enhanced Multi-Agent System${NC}"
    echo ""
    echo "This system integrates CrewAI orchestration directly with your existing"
    echo "Claude Code terminal sessions. No OpenAI API keys needed!"
    echo ""

    echo -e "${YELLOW}Key Features:${NC}"
    echo "• Direct communication with Claude terminals via tmux"
    echo "• Intelligent task distribution based on project analysis"
    echo "• Real-time coordination across multiple Claude agents"
    echo "• Context-aware workflow management"
    echo "• No external API dependencies"
    echo ""

    echo -e "${YELLOW}Usage Examples:${NC}"
    echo ""
    echo -e "${CYAN}1. Intelligent Coordination:${NC}"
    echo "   Select option 1 → Intelligent Task Distribution"
    echo "   Describe your project, system analyzes and distributes automatically"
    echo ""

    echo -e "${CYAN}2. Full-Stack Development:${NC}"
    echo "   Select option 1 → Full-Stack Feature Coordination"
    echo "   System coordinates backend, frontend, database, and testing teams"
    echo ""

    echo -e "${CYAN}3. Individual Task Assignment:${NC}"
    echo "   Select option 2 → Send Task to Claude Agent"
    echo "   Send specific tasks to individual Claude agents"
    echo ""

    echo -e "${YELLOW}System Architecture:${NC}"
    echo "• 9 Claude PM Agents (prompt-validator, task-coordinator, etc.)"
    echo "• Python orchestration layer with direct tmux integration"
    echo "• Real-time monitoring and progress tracking"
    echo "• Intelligent project analysis and team selection"
    echo ""

    read -p "Press Enter to continue..."
}

# Main execution
main() {
    # Check if we're in the correct directory
    if [[ ! -d "$AGENTS_DIR" ]]; then
        echo -e "${RED}Error: Not in correct project directory${NC}"
        echo "Please run from: $PROJECT_ROOT"
        exit 1
    fi

    # Start Claude main menu
    claude_main_menu
}

# Run main function
main "$@"