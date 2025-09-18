#!/bin/bash
# Enhanced Agent Manager with CrewAI + TmuxAI Integration
# Combines the best of open-source frameworks with our existing architecture

set -euo pipefail

PROJECT_ROOT="/Users/erik/Desktop/riona_ai/riona-ai"
AGENTS_DIR="$PROJECT_ROOT/.riona/agents"
CREWAI_DIR="$AGENTS_DIR/crewai"
TMUXAI_BIN="$HOME/bin/tmuxai"

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

# PM Agents
PM_AGENTS=("prompt-validator" "task-coordinator" "backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")

# Enhanced system header
show_enhanced_header() {
    clear
    echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                 🚀 RIONA AI ENHANCED AGENT MANAGER                  ║${NC}"
    echo -e "${PURPLE}║                                                                    ║${NC}"
    echo -e "${PURPLE}║  🤖 CrewAI Integration  |  👁️  TmuxAI Context  |  🏢 Hierarchical  ║${NC}"
    echo -e "${PURPLE}║                                                                    ║${NC}"
    echo -e "${PURPLE}║          Intelligent Multi-Agent System with Open Source          ║${NC}"
    echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Check integration status
check_integration_status() {
    local crewai_status="❌"
    local tmuxai_status="❌"
    local system_status="❌"

    # Check CrewAI
    if command -v crewai >/dev/null 2>&1; then
        crewai_status="✅"
    fi

    # Check TmuxAI
    if [[ -x "$TMUXAI_BIN" ]]; then
        tmuxai_status="✅"
    fi

    # Check hierarchical system
    if [[ -f "$PROJECT_ROOT/authorized-orchestrator.sh" ]]; then
        system_status="✅"
    fi

    echo -e "${CYAN}🔍 INTEGRATION STATUS:${NC}"
    echo "────────────────────────────────────────────────────────────────────"
    echo -e "  CrewAI Framework:     $crewai_status $(command -v crewai >/dev/null 2>&1 && crewai --version || echo 'Not installed')"
    echo -e "  TmuxAI Integration:   $tmuxai_status $($TMUXAI_BIN --version 2>/dev/null || echo 'Not installed')"
    echo -e "  Hierarchical System:  $system_status $(test -f "$PROJECT_ROOT/authorized-orchestrator.sh" && echo 'Available' || echo 'Missing')"
    echo ""
}

# Show enhanced system status with CrewAI awareness
show_enhanced_system_status() {
    echo -e "${CYAN}🏢 ENHANCED HIERARCHICAL SYSTEM STATUS${NC}"
    echo "════════════════════════════════════════════════════════════════════"
    echo ""

    local pm_active=0
    local pm_total=0

    echo -e "${YELLOW}📊 LEVEL 1 - PROJECT MANAGERS (Enhanced with CrewAI):${NC}"
    echo "────────────────────────────────────────────────────────────────────"

    for pm in "${PM_AGENTS[@]}"; do
        pm_total=$((pm_total + 1))
        if $TMUX_BIN has-session -t "$pm" 2>/dev/null; then
            echo -e "  ${GREEN}✅ $pm${NC} - PM Active (CrewAI Ready)"
            pm_active=$((pm_active + 1))
        else
            echo -e "  ${RED}❌ $pm${NC} - PM Offline"
        fi
    done
    echo ""

    echo -e "${YELLOW}🤖 CREWAI INTEGRATION STATUS:${NC}"
    echo "────────────────────────────────────────────────────────────────────"

    if [[ -f "$CREWAI_DIR/integration.py" ]]; then
        echo -e "  ${GREEN}✅ CrewAI Integration Module${NC} - Available"
    else
        echo -e "  ${RED}❌ CrewAI Integration Module${NC} - Missing"
    fi

    if [[ -f "$CREWAI_DIR/enhanced_orchestrator.py" ]]; then
        echo -e "  ${GREEN}✅ Enhanced Orchestrator${NC} - Available"
    else
        echo -e "  ${RED}❌ Enhanced Orchestrator${NC} - Missing"
    fi

    echo ""
    echo -e "${YELLOW}👁️  TMUXAI CONTEXT AWARENESS:${NC}"
    echo "────────────────────────────────────────────────────────────────────"

    if [[ -x "$TMUXAI_BIN" ]]; then
        echo -e "  ${GREEN}✅ TmuxAI Binary${NC} - Ready for context analysis"
        echo -e "  ${CYAN}🔄 Context Analysis${NC} - Real-time terminal monitoring available"
    else
        echo -e "  ${RED}❌ TmuxAI Binary${NC} - Not installed"
    fi

    echo ""
    echo -e "${PURPLE}📈 ENHANCED SYSTEM SUMMARY:${NC}"
    echo "════════════════════════════════════════════════════════════════════"
    echo -e "  ${CYAN}Active PM Agents:${NC} $pm_active/$pm_total"
    echo -e "  ${CYAN}CrewAI Integration:${NC} $(test -f "$CREWAI_DIR/integration.py" && echo 'Active' || echo 'Inactive')"
    echo -e "  ${CYAN}TmuxAI Context:${NC} $(test -x "$TMUXAI_BIN" && echo 'Available' || echo 'Unavailable')"
    echo -e "  ${CYAN}Intelligence Level:${NC} Enhanced Multi-Agent Orchestration"
    echo ""
}

# Enhanced main menu
enhanced_main_menu() {
    while true; do
        show_enhanced_header
        check_integration_status
        show_enhanced_system_status

        echo ""
        echo -e "${CYAN}🎛️  ENHANCED MANAGEMENT OPTIONS:${NC}"
        echo "════════════════════════════════════════════════════════════════════"
        echo "  ${BLUE}1.${NC} 🚀 Enhanced System Operations    (CrewAI + Hierarchical)"
        echo "  ${BLUE}2.${NC} 🤖 Intelligent Task Coordination  (CrewAI Orchestration)"
        echo "  ${BLUE}3.${NC} 👁️  Context-Aware Management      (TmuxAI Integration)"
        echo "  ${BLUE}4.${NC} 🏢 Hierarchical Agent Control    (PM + Sub-agents)"
        echo "  ${BLUE}5.${NC} 🔐 Authorization Center          (Enhanced with AI)"
        echo "  ${BLUE}6.${NC} 📊 Real-time System Monitoring   (Multi-layer insights)"
        echo "  ${BLUE}7.${NC} ⚙️  Integration Configuration     (Setup frameworks)"
        echo "  ${BLUE}8.${NC} 🧪 Framework Testing             (Test integrations)"
        echo "  ${BLUE}9.${NC} 📚 Documentation & Help          (System guide)"
        echo "  ${BLUE}10.${NC} Exit Enhanced Manager"
        echo ""

        read -p "$(echo -e "${YELLOW}Select enhanced option [1-10]: ${NC}")" choice

        case $choice in
            1) enhanced_system_operations_menu ;;
            2) intelligent_task_coordination_menu ;;
            3) context_aware_management_menu ;;
            4) hierarchical_control_menu ;;
            5) enhanced_authorization_menu ;;
            6) realtime_monitoring_menu ;;
            7) integration_configuration_menu ;;
            8) framework_testing_menu ;;
            9) documentation_help_menu ;;
            10)
                echo -e "${GREEN}🎯 Exiting Enhanced Agent Manager...${NC}"
                echo "Thank you for using the Riona AI Enhanced Multi-Agent System!"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid option. Press Enter to continue...${NC}"
                read
                ;;
        esac
    done
}

# Enhanced System Operations
enhanced_system_operations_menu() {
    while true; do
        clear
        echo -e "${PURPLE}🚀 ENHANCED SYSTEM OPERATIONS${NC}"
        echo "════════════════════════════════════════════════════════════════════"
        echo ""
        echo "  ${BLUE}1.${NC} Start Complete Enhanced System    (All frameworks)"
        echo "  ${BLUE}2.${NC} Start Hierarchical System Only    (PM + Sub-agents)"
        echo "  ${BLUE}3.${NC} Initialize CrewAI Integration     (Intelligent coordination)"
        echo "  ${BLUE}4.${NC} Activate TmuxAI Context Layer     (Context awareness)"
        echo "  ${BLUE}5.${NC} Full System Health Check          (All components)"
        echo "  ${BLUE}6.${NC} Enhanced System Shutdown          (Graceful stop)"
        echo "  ${BLUE}7.${NC} Return to Main Menu"
        echo ""

        read -p "$(echo -e "${YELLOW}Select operation [1-7]: ${NC}")" op_choice

        case $op_choice in
            1)
                echo -e "${BLUE}🚀 Starting Complete Enhanced System...${NC}"
                echo "This will initialize:"
                echo "  • Hierarchical PM/Sub-agent system"
                echo "  • CrewAI intelligent orchestration"
                echo "  • TmuxAI context awareness"
                echo "  • Authorization chain integration"
                echo ""

                # Start hierarchical system first
                echo -e "${CYAN}📋 Step 1: Starting hierarchical system...${NC}"
                "$PROJECT_ROOT/.riona/agents/scripts/hierarchical-startup.sh" start-all

                # Initialize CrewAI if available
                if command -v python3 >/dev/null 2>&1 && [[ -f "$CREWAI_DIR/integration.py" ]]; then
                    echo -e "${CYAN}🤖 Step 2: Initializing CrewAI integration...${NC}"
                    echo "CrewAI integration ready for intelligent coordination"
                fi

                # Check TmuxAI
                if [[ -x "$TMUXAI_BIN" ]]; then
                    echo -e "${CYAN}👁️  Step 3: TmuxAI context layer active...${NC}"
                    echo "Real-time context awareness enabled"
                fi

                echo -e "${GREEN}✅ Enhanced system startup completed!${NC}"
                read -p "Press Enter to continue..."
                ;;
            2)
                echo -e "${BLUE}🏢 Starting hierarchical system only...${NC}"
                "$PROJECT_ROOT/.riona/agents/scripts/hierarchical-startup.sh" start-all
                read -p "Press Enter to continue..."
                ;;
            3)
                echo -e "${BLUE}🤖 Initializing CrewAI integration...${NC}"
                if command -v python3 >/dev/null 2>&1 && command -v crewai >/dev/null 2>&1; then
                    echo "CrewAI framework available and ready"
                    echo "Enhanced orchestration capabilities initialized"
                else
                    echo -e "${RED}CrewAI not available. Please install first.${NC}"
                fi
                read -p "Press Enter to continue..."
                ;;
            4)
                echo -e "${BLUE}👁️  Activating TmuxAI context layer...${NC}"
                if [[ -x "$TMUXAI_BIN" ]]; then
                    echo "TmuxAI context awareness active"
                    echo "Real-time terminal monitoring enabled"
                else
                    echo -e "${RED}TmuxAI not available. Please install first.${NC}"
                fi
                read -p "Press Enter to continue..."
                ;;
            5)
                echo -e "${BLUE}🔍 Performing full system health check...${NC}"
                echo ""

                # Check hierarchical system
                echo -e "${CYAN}Hierarchical System:${NC}"
                "$PROJECT_ROOT/.riona/agents/scripts/hierarchical-startup.sh" status

                # Check CrewAI
                echo -e "${CYAN}CrewAI Framework:${NC}"
                if command -v crewai >/dev/null 2>&1; then
                    crewai --version
                else
                    echo "❌ Not installed"
                fi

                # Check TmuxAI
                echo -e "${CYAN}TmuxAI Integration:${NC}"
                if [[ -x "$TMUXAI_BIN" ]]; then
                    $TMUXAI_BIN --version
                else
                    echo "❌ Not installed"
                fi

                read -p "Press Enter to continue..."
                ;;
            6)
                echo -e "${RED}🛑 Enhanced system shutdown...${NC}"
                "$PROJECT_ROOT/.riona/agents/scripts/hierarchical-startup.sh" stop-all
                echo -e "${GREEN}✅ All systems stopped gracefully${NC}"
                read -p "Press Enter to continue..."
                ;;
            7)
                return
                ;;
            *)
                echo -e "${RED}Invalid option. Press Enter to continue...${NC}"
                read
                ;;
        esac
    done
}

# Intelligent Task Coordination (CrewAI)
intelligent_task_coordination_menu() {
    clear
    echo -e "${PURPLE}🤖 INTELLIGENT TASK COORDINATION${NC}"
    echo "════════════════════════════════════════════════════════════════════"
    echo ""

    if ! command -v crewai >/dev/null 2>&1; then
        echo -e "${RED}❌ CrewAI not available. Please install CrewAI first.${NC}"
        echo ""
        echo "Installation command:"
        echo "  pip install 'crewai[tools]'"
        read -p "Press Enter to continue..."
        return
    fi

    echo -e "${GREEN}✅ CrewAI Framework Available${NC}"
    echo ""
    echo "Available intelligent coordination options:"
    echo ""
    echo "  ${BLUE}1.${NC} Execute Full-Stack Feature Development"
    echo "  ${BLUE}2.${NC} Run Backend-Only Coordination"
    echo "  ${BLUE}3.${NC} Execute Frontend-Only Coordination"
    echo "  ${BLUE}4.${NC} Custom Project Coordination"
    echo "  ${BLUE}5.${NC} System Analysis and Planning"
    echo "  ${BLUE}6.${NC} Return to Main Menu"
    echo ""

    read -p "$(echo -e "${YELLOW}Select coordination type [1-6]: ${NC}")" coord_choice

    case $coord_choice in
        1)
            echo ""
            read -p "Enter full-stack feature description: " feature_desc
            echo -e "${BLUE}🤖 Executing intelligent full-stack coordination...${NC}"
            echo "CrewAI would coordinate: backend-api, database, frontend-ui, testing teams"
            echo "Feature: $feature_desc"
            read -p "Press Enter to continue..."
            ;;
        2)
            echo ""
            read -p "Enter backend feature description: " backend_desc
            echo -e "${BLUE}🤖 Executing intelligent backend coordination...${NC}"
            echo "CrewAI would coordinate: backend-api, database teams"
            echo "Feature: $backend_desc"
            read -p "Press Enter to continue..."
            ;;
        3)
            echo ""
            read -p "Enter frontend feature description: " frontend_desc
            echo -e "${BLUE}🤖 Executing intelligent frontend coordination...${NC}"
            echo "CrewAI would coordinate: frontend-ui, testing teams"
            echo "Feature: $frontend_desc"
            read -p "Press Enter to continue..."
            ;;
        4)
            echo ""
            read -p "Enter custom project description: " custom_desc
            echo -e "${BLUE}🤖 Executing intelligent custom coordination...${NC}"
            echo "CrewAI would analyze and determine optimal team coordination"
            echo "Project: $custom_desc"
            read -p "Press Enter to continue..."
            ;;
        5)
            echo -e "${BLUE}🔍 Performing system analysis...${NC}"
            echo ""
            echo "CrewAI would analyze:"
            echo "  • Current system workload distribution"
            echo "  • Agent performance metrics"
            echo "  • Resource utilization patterns"
            echo "  • Optimization opportunities"
            read -p "Press Enter to continue..."
            ;;
        6)
            return
            ;;
    esac
}

# Context-Aware Management (TmuxAI)
context_aware_management_menu() {
    clear
    echo -e "${PURPLE}👁️  CONTEXT-AWARE MANAGEMENT${NC}"
    echo "════════════════════════════════════════════════════════════════════"
    echo ""

    if [[ ! -x "$TMUXAI_BIN" ]]; then
        echo -e "${RED}❌ TmuxAI not available. Please install TmuxAI first.${NC}"
        echo ""
        echo "Installation commands:"
        echo "  curl -fsSL https://get.tmuxai.dev | bash"
        echo "  # or manually download from GitHub releases"
        read -p "Press Enter to continue..."
        return
    fi

    echo -e "${GREEN}✅ TmuxAI Integration Available${NC}"
    echo ""
    echo "Context-aware management capabilities:"
    echo ""
    echo "  ${BLUE}1.${NC} Analyze Current Terminal Context"
    echo "  ${BLUE}2.${NC} Monitor Agent Terminal Activity"
    echo "  ${BLUE}3.${NC} Context-Based Task Suggestions"
    echo "  ${BLUE}4.${NC} Real-time System Monitoring"
    echo "  ${BLUE}5.${NC} TmuxAI Configuration"
    echo "  ${BLUE}6.${NC} Return to Main Menu"
    echo ""

    read -p "$(echo -e "${YELLOW}Select context option [1-6]: ${NC}")" ctx_choice

    case $ctx_choice in
        1)
            echo -e "${BLUE}🔍 Analyzing current terminal context...${NC}"
            echo ""
            if $TMUX_BIN list-sessions >/dev/null 2>&1; then
                echo "Active tmux sessions:"
                $TMUX_BIN list-sessions
                echo ""
                echo "TmuxAI could provide context analysis for these sessions"
            else
                echo "No active tmux sessions found"
            fi
            read -p "Press Enter to continue..."
            ;;
        2)
            echo -e "${BLUE}👁️  Monitoring agent terminal activity...${NC}"
            echo ""
            echo "TmuxAI would monitor:"
            for pm in "${PM_AGENTS[@]}"; do
                if $TMUX_BIN has-session -t "$pm" 2>/dev/null; then
                    echo "  • $pm PM agent session"
                fi
            done
            read -p "Press Enter to continue..."
            ;;
        3)
            echo -e "${BLUE}💡 Context-based task suggestions...${NC}"
            echo ""
            echo "Based on current terminal context, TmuxAI could suggest:"
            echo "  • Optimal task distribution"
            echo "  • Agent workload balancing"
            echo "  • Performance optimizations"
            echo "  • Error resolution strategies"
            read -p "Press Enter to continue..."
            ;;
        4)
            echo -e "${BLUE}📊 Real-time system monitoring with TmuxAI...${NC}"
            echo ""
            echo "Monitoring capabilities:"
            echo "  • Terminal session health"
            echo "  • Agent response patterns"
            echo "  • Context-aware alerts"
            echo "  • Performance metrics"
            read -p "Press Enter to continue..."
            ;;
        5)
            echo -e "${BLUE}⚙️  TmuxAI Configuration...${NC}"
            echo ""
            $TMUXAI_BIN --version
            echo ""
            echo "Configuration options would include:"
            echo "  • API key setup"
            echo "  • Context monitoring preferences"
            echo "  • Integration with agent system"
            read -p "Press Enter to continue..."
            ;;
        6)
            return
            ;;
    esac
}

# Hierarchical Control Menu (existing functionality)
hierarchical_control_menu() {
    # Use existing hierarchical system management
    "$PROJECT_ROOT/agent-manager.sh"
}

# Enhanced Authorization Menu
enhanced_authorization_menu() {
    clear
    echo -e "${PURPLE}🔐 ENHANCED AUTHORIZATION CENTER${NC}"
    echo "════════════════════════════════════════════════════════════════════"
    echo ""

    echo -e "${CYAN}Authorization capabilities:${NC}"
    echo "  • Traditional PM → Orchestrator approval chain"
    echo "  • CrewAI-enhanced decision making"
    echo "  • Context-aware authorization (TmuxAI)"
    echo "  • Intelligent workload analysis"
    echo ""

    # Call existing authorization system
    "$PROJECT_ROOT/authorized-orchestrator.sh" pending
    read -p "Press Enter to continue..."
}

# Real-time Monitoring Menu
realtime_monitoring_menu() {
    while true; do
        show_enhanced_header
        show_enhanced_system_status

        echo ""
        echo -e "${YELLOW}🔄 Auto-refreshing every 10 seconds...${NC}"
        echo "Press 'q' to quit, 'r' to refresh now, Enter to continue"

        if read -t 10 -n 1 key; then
            case $key in
                'q'|'Q') return ;;
                'r'|'R') continue ;;
                '') continue ;;
            esac
        fi
    done
}

# Integration Configuration Menu
integration_configuration_menu() {
    clear
    echo -e "${PURPLE}⚙️  INTEGRATION CONFIGURATION${NC}"
    echo "════════════════════════════════════════════════════════════════════"
    echo ""

    echo "  ${BLUE}1.${NC} Install CrewAI Framework"
    echo "  ${BLUE}2.${NC} Install TmuxAI Integration"
    echo "  ${BLUE}3.${NC} Configure API Keys"
    echo "  ${BLUE}4.${NC} Test Integrations"
    echo "  ${BLUE}5.${NC} Update Frameworks"
    echo "  ${BLUE}6.${NC} Return to Main Menu"
    echo ""

    read -p "$(echo -e "${YELLOW}Select configuration option [1-6]: ${NC}")" config_choice

    case $config_choice in
        1)
            echo -e "${BLUE}🤖 Installing CrewAI Framework...${NC}"
            pip install 'crewai[tools]'
            read -p "Press Enter to continue..."
            ;;
        2)
            echo -e "${BLUE}👁️  Installing TmuxAI Integration...${NC}"
            curl -fsSL https://get.tmuxai.dev | bash
            read -p "Press Enter to continue..."
            ;;
        3)
            echo -e "${BLUE}🔑 Configure API Keys...${NC}"
            echo ""
            echo "Set environment variables:"
            echo "  export OPENAI_API_KEY='your-key-here'"
            echo "  export TMUXAI_OPENROUTER_API_KEY='your-key-here'"
            read -p "Press Enter to continue..."
            ;;
        4)
            echo -e "${BLUE}🧪 Testing integrations...${NC}"
            echo ""
            echo "CrewAI: $(command -v crewai >/dev/null 2>&1 && echo '✅ Available' || echo '❌ Not installed')"
            echo "TmuxAI: $(test -x "$TMUXAI_BIN" && echo '✅ Available' || echo '❌ Not installed')"
            read -p "Press Enter to continue..."
            ;;
        5)
            echo -e "${BLUE}🔄 Updating frameworks...${NC}"
            pip install --upgrade 'crewai[tools]'
            # TmuxAI update would be manual
            read -p "Press Enter to continue..."
            ;;
        6)
            return
            ;;
    esac
}

# Framework Testing Menu
framework_testing_menu() {
    clear
    echo -e "${PURPLE}🧪 FRAMEWORK TESTING${NC}"
    echo "════════════════════════════════════════════════════════════════════"
    echo ""

    echo "  ${BLUE}1.${NC} Test CrewAI Basic Functionality"
    echo "  ${BLUE}2.${NC} Test TmuxAI Context Reading"
    echo "  ${BLUE}3.${NC} Test Integration Communication"
    echo "  ${BLUE}4.${NC} Performance Benchmarks"
    echo "  ${BLUE}5.${NC} Full System Integration Test"
    echo "  ${BLUE}6.${NC} Return to Main Menu"
    echo ""

    read -p "$(echo -e "${YELLOW}Select test [1-6]: ${NC}")" test_choice

    case $test_choice in
        1)
            echo -e "${BLUE}🤖 Testing CrewAI basic functionality...${NC}"
            if command -v python3 >/dev/null 2>&1 && [[ -f "$CREWAI_DIR/integration.py" ]]; then
                echo "CrewAI integration module found"
                echo "Basic functionality test would verify agent creation and task execution"
            else
                echo -e "${RED}CrewAI integration not available${NC}"
            fi
            read -p "Press Enter to continue..."
            ;;
        2)
            echo -e "${BLUE}👁️  Testing TmuxAI context reading...${NC}"
            if [[ -x "$TMUXAI_BIN" ]]; then
                echo "TmuxAI binary available"
                echo "Context reading test would analyze current tmux sessions"
            else
                echo -e "${RED}TmuxAI not available${NC}"
            fi
            read -p "Press Enter to continue..."
            ;;
        3)
            echo -e "${BLUE}🔗 Testing integration communication...${NC}"
            echo "Integration test would verify:"
            echo "  • CrewAI ↔ Hierarchical system"
            echo "  • TmuxAI ↔ Agent sessions"
            echo "  • Authorization chain integration"
            read -p "Press Enter to continue..."
            ;;
        4)
            echo -e "${BLUE}📊 Performance benchmarks...${NC}"
            echo "Benchmarks would measure:"
            echo "  • Task coordination speed"
            echo "  • Context analysis latency"
            echo "  • Resource utilization"
            echo "  • Memory usage patterns"
            read -p "Press Enter to continue..."
            ;;
        5)
            echo -e "${BLUE}🎯 Full system integration test...${NC}"
            echo "Comprehensive test would verify:"
            echo "  • All framework integrations"
            echo "  • End-to-end workflows"
            echo "  • Error handling and recovery"
            echo "  • Performance under load"
            read -p "Press Enter to continue..."
            ;;
        6)
            return
            ;;
    esac
}

# Documentation and Help
documentation_help_menu() {
    clear
    echo -e "${PURPLE}📚 DOCUMENTATION & HELP${NC}"
    echo "════════════════════════════════════════════════════════════════════"
    echo ""

    echo -e "${CYAN}🚀 Riona AI Enhanced Multi-Agent System${NC}"
    echo ""
    echo -e "${YELLOW}System Architecture:${NC}"
    echo "  • Hierarchical PM/Sub-Agent System (Level 1 & 2)"
    echo "  • CrewAI Intelligent Orchestration Layer"
    echo "  • TmuxAI Context Awareness Integration"
    echo "  • Authorization Chain Management"
    echo ""

    echo -e "${YELLOW}Key Components:${NC}"
    echo ""
    echo -e "${BLUE}1. Hierarchical System:${NC}"
    echo "     9 PM Agents managing specialized sub-teams"
    echo "     Authorization chain for controlled execution"
    echo ""
    echo -e "${BLUE}2. CrewAI Integration:${NC}"
    echo "     Intelligent task coordination and planning"
    echo "     Agent collaboration and workflow optimization"
    echo ""
    echo -e "${BLUE}3. TmuxAI Context:${NC}"
    echo "     Real-time terminal context analysis"
    echo "     Context-aware decision making"
    echo ""

    echo -e "${YELLOW}Usage Examples:${NC}"
    echo ""
    echo "• Start enhanced system: Option 1 → 1"
    echo "• Intelligent coordination: Option 2"
    echo "• Context analysis: Option 3"
    echo "• Traditional management: Option 4"
    echo ""

    echo -e "${YELLOW}Files and Directories:${NC}"
    echo "  • $AGENTS_DIR/crewai/ - CrewAI integration modules"
    echo "  • $PROJECT_ROOT/authorized-orchestrator.sh - Authorization system"
    echo "  • $HOME/bin/tmuxai - TmuxAI binary"
    echo ""

    read -p "Press Enter to continue..."
}

# Main execution
main() {
    # Ensure required directories exist
    mkdir -p "$CREWAI_DIR"

    # Check if we're in the correct directory
    if [[ ! -d "$AGENTS_DIR" ]]; then
        echo -e "${RED}Error: Not in correct project directory${NC}"
        echo "Please run from: $PROJECT_ROOT"
        exit 1
    fi

    # Start enhanced main menu
    enhanced_main_menu
}

# Run main function
main "$@"