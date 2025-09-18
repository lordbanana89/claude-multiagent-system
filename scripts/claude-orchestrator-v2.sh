#!/bin/bash
# Claude Orchestrator V2 - Coordina veri agenti Claude Code specializzati

set -euo pipefail

PROJECT_ROOT="/Users/erik/Desktop/riona_ai/riona-ai"
cd "$PROJECT_ROOT"

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Lista agenti
AGENTS=("backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")
AGENT_LAUNCHER="./.riona/agents/scripts/claude-agent-launcher.sh"

# Percorso tmux
unset TMUX 2>/dev/null || true
TMUX_BIN="/opt/homebrew/bin/tmux"

# Funzione per verificare se gli agenti sono attivi
check_agents_status() {
    echo -e "${BLUE}Checking Claude agents status...${NC}"

    local active_count=0
    local total_count=${#AGENTS[@]}

    for agent in "${AGENTS[@]}"; do
        if $TMUX_BIN has-session -t "claude-$agent" 2>/dev/null; then
            active_count=$((active_count + 1))
        fi
    done

    if [ $active_count -eq 0 ]; then
        echo -e "${RED}❌ No Claude agents are running${NC}"
        echo -e "${YELLOW}Starting agents automatically...${NC}"
        $AGENT_LAUNCHER start-all
        sleep 5
    elif [ $active_count -lt $total_count ]; then
        echo -e "${YELLOW}⚠️ Only $active_count/$total_count agents active${NC}"
        echo "Missing agents will be started automatically if needed"
    else
        echo -e "${GREEN}✅ All $active_count/$total_count Claude agents are active${NC}"
    fi

    return $active_count
}

# Funzione per inviare task a un agente Claude
send_task_to_claude_agent() {
    local agent="$1"
    local task="$2"
    local session_name="claude-$agent"

    # Verifica se l'agente è attivo
    if ! $TMUX_BIN has-session -t "$session_name" 2>/dev/null; then
        echo -e "${YELLOW}Starting agent: $agent${NC}"
        $AGENT_LAUNCHER start "$agent"
        sleep 3
    fi

    echo -e "${BLUE}🎯 Sending task to $agent agent:${NC}"
    echo -e "${PURPLE}Task: $task${NC}"
    echo ""

    # Prepara il task con contesto
    local formatted_task="AGENT TASK: $task

Please analyze this task from your specialized perspective as $(jq -r '.role' ".riona/agents/configs/$agent.json" 2>/dev/null || echo "the $agent specialist").

Provide:
1. Your assessment of the task feasibility
2. Specific steps you would take
3. Any dependencies or requirements from other agents
4. Estimated complexity (1-10)
5. Your recommended approach

Respond as the specialized agent you are."

    # Invia task
    $TMUX_BIN send-keys -t "$session_name" "$formatted_task" Enter

    echo -e "${GREEN}✅ Task sent to $agent agent${NC}"
    echo -e "   View response: tmux attach-session -t $session_name"
    echo -e "   Or wait for next orchestrator step..."
    echo ""
}

# Funzione per workflow coordinato con veri agenti Claude
workflow_with_claude_agents() {
    local workflow_name="$1"
    local description="${2:-}"

    echo -e "${PURPLE}🎯 CLAUDE MULTI-AGENT WORKFLOW${NC}"
    echo "================================"
    echo -e "Workflow: ${YELLOW}$workflow_name${NC}"
    if [ -n "$description" ]; then
        echo -e "Description: ${BLUE}$description${NC}"
    fi
    echo ""

    # Verifica agenti
    check_agents_status
    sleep 2

    case "$workflow_name" in
        "feature-development")
            claude_workflow_feature_development "$description"
            ;;
        "api-endpoint")
            claude_workflow_api_endpoint "$description"
            ;;
        "frontend-component")
            claude_workflow_frontend_component "$description"
            ;;
        "database-optimization")
            claude_workflow_database_optimization
            ;;
        "testing-suite")
            claude_workflow_testing_suite
            ;;
        "deployment-prep")
            claude_workflow_deployment_prep
            ;;
        "system-analysis")
            claude_workflow_system_analysis
            ;;
        *)
            echo -e "${RED}Unknown workflow: $workflow_name${NC}"
            echo "Available workflows: feature-development, api-endpoint, frontend-component, database-optimization, testing-suite, deployment-prep, system-analysis"
            return 1
            ;;
    esac
}

# Workflow: Sviluppo feature completa con agenti Claude
claude_workflow_feature_development() {
    local feature="$1"
    echo -e "${BLUE}🚀 Claude Multi-Agent Feature Development: $feature${NC}"
    echo "=================================================="

    echo -e "${YELLOW}Phase 1: Architecture Analysis${NC}"
    send_task_to_claude_agent "backend-api" "Analyze the architecture and technical requirements for the '$feature' feature. Consider API endpoints, data models, and integration points."

    echo -e "${YELLOW}Phase 2: Database Design${NC}"
    send_task_to_claude_agent "database" "Design the database schema, entities, and relationships needed for the '$feature' feature. Consider migration strategies and performance implications."

    echo -e "${YELLOW}Phase 3: Frontend Planning${NC}"
    send_task_to_claude_agent "frontend-ui" "Plan the UI/UX components and user interactions needed for the '$feature' feature. Consider responsive design and accessibility."

    # Attendi un po' per le prime analisi
    echo -e "${BLUE}⏳ Waiting for initial analysis (30 seconds)...${NC}"
    sleep 30

    echo -e "${YELLOW}Phase 4: Implementation Coordination${NC}"
    send_task_to_claude_agent "backend-api" "Based on the database design, implement the API endpoints for the '$feature' feature."
    send_task_to_claude_agent "frontend-ui" "Based on the backend API design, implement the React components for the '$feature' feature."

    echo -e "${YELLOW}Phase 5: Quality Assurance${NC}"
    send_task_to_claude_agent "testing" "Design and implement comprehensive tests for the '$feature' feature, including unit, integration, and E2E tests."

    echo -e "${YELLOW}Phase 6: Deployment Preparation${NC}"
    send_task_to_claude_agent "deployment" "Prepare deployment configuration and documentation for the '$feature' feature."

    echo -e "${GREEN}✅ Multi-agent feature development workflow initiated for: $feature${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Monitor agent responses: tmux list-sessions | grep claude"
    echo "2. Review each agent's analysis and implementation"
    echo "3. Use orchestrator to coordinate next phases"
    echo "4. Run final validation and deployment"
}

# Workflow: Sviluppo API endpoint con coordinamento
claude_workflow_api_endpoint() {
    local endpoint="$1"
    echo -e "${BLUE}🔌 Claude API Endpoint Development: $endpoint${NC}"
    echo "============================================="

    echo -e "${YELLOW}Step 1: Data Requirements${NC}"
    send_task_to_claude_agent "database" "Analyze data requirements for the '$endpoint' API endpoint. Define entities, relationships, and query patterns."

    sleep 10

    echo -e "${YELLOW}Step 2: API Implementation${NC}"
    send_task_to_claude_agent "backend-api" "Implement the '$endpoint' API endpoint with proper validation, error handling, and documentation."

    echo -e "${YELLOW}Step 3: Frontend Integration${NC}"
    send_task_to_claude_agent "frontend-ui" "Create frontend integration and UI components that consume the '$endpoint' API."

    sleep 5

    echo -e "${YELLOW}Step 4: Testing Strategy${NC}"
    send_task_to_claude_agent "testing" "Create comprehensive tests for the '$endpoint' API endpoint, including unit tests and integration tests."

    echo -e "${GREEN}✅ API endpoint development workflow initiated for: $endpoint${NC}"
}

# Workflow: Sviluppo componente frontend
claude_workflow_frontend_component() {
    local component="$1"
    echo -e "${BLUE}🎨 Claude Frontend Component Development: $component${NC}"
    echo "=============================================="

    echo -e "${YELLOW}Step 1: Component Design${NC}"
    send_task_to_claude_agent "frontend-ui" "Design and implement the '$component' React component with TypeScript, proper state management, and responsive styling."

    echo -e "${YELLOW}Step 2: Backend Integration${NC}"
    send_task_to_claude_agent "backend-api" "Review if any new API endpoints are needed to support the '$component' component. Implement if necessary."

    sleep 10

    echo -e "${YELLOW}Step 3: Component Testing${NC}"
    send_task_to_claude_agent "testing" "Create comprehensive tests for the '$component' React component using React Testing Library."

    echo -e "${GREEN}✅ Frontend component workflow initiated for: $component${NC}"
}

# Workflow: Ottimizzazione database
claude_workflow_database_optimization() {
    echo -e "${BLUE}💾 Claude Database Optimization Workflow${NC}"
    echo "======================================="

    echo -e "${YELLOW}Step 1: Performance Analysis${NC}"
    send_task_to_claude_agent "database" "Perform comprehensive database performance analysis. Identify slow queries, missing indexes, and optimization opportunities."

    echo -e "${YELLOW}Step 2: Backend Impact Assessment${NC}"
    send_task_to_claude_agent "backend-api" "Review API endpoints that might be affected by database optimizations. Plan necessary code adjustments."

    sleep 15

    echo -e "${YELLOW}Step 3: Optimization Implementation${NC}"
    send_task_to_claude_agent "database" "Implement database optimizations including index creation, query improvements, and schema adjustments."

    echo -e "${YELLOW}Step 4: Testing & Validation${NC}"
    send_task_to_claude_agent "testing" "Create performance tests to validate database optimizations and ensure no regressions."

    echo -e "${GREEN}✅ Database optimization workflow initiated${NC}"
}

# Workflow: Suite di testing
claude_workflow_testing_suite() {
    echo -e "${BLUE}🧪 Claude Testing Suite Enhancement${NC}"
    echo "==================================="

    send_task_to_claude_agent "testing" "Analyze current test coverage and identify gaps in backend API testing."
    send_task_to_claude_agent "testing" "Analyze current test coverage and identify gaps in frontend component testing."
    send_task_to_claude_agent "testing" "Plan and implement E2E testing strategy for critical user workflows."

    echo -e "${GREEN}✅ Testing suite enhancement initiated${NC}"
}

# Workflow: Preparazione deployment
claude_workflow_deployment_prep() {
    echo -e "${BLUE}🚀 Claude Deployment Preparation${NC}"
    echo "==============================="

    send_task_to_claude_agent "deployment" "Review current deployment configuration and identify improvements for production readiness."
    send_task_to_claude_agent "testing" "Run comprehensive test suite to validate deployment readiness."
    send_task_to_claude_agent "backend-api" "Review API endpoints for production security and performance requirements."

    echo -e "${GREEN}✅ Deployment preparation initiated${NC}"
}

# Workflow: Analisi sistema
claude_workflow_system_analysis() {
    echo -e "${BLUE}📊 Claude System Analysis${NC}"
    echo "========================="

    echo -e "${YELLOW}Comprehensive system analysis across all domains...${NC}"

    send_task_to_claude_agent "backend-api" "Analyze backend architecture, identify potential improvements, and assess scalability."
    send_task_to_claude_agent "database" "Analyze database performance, schema design, and optimization opportunities."
    send_task_to_claude_agent "frontend-ui" "Analyze frontend architecture, component design, and user experience improvements."
    send_task_to_claude_agent "queue-manager" "Analyze background job processing, queue performance, and reliability."
    send_task_to_claude_agent "testing" "Analyze test coverage, quality, and identify testing gaps."
    send_task_to_claude_agent "deployment" "Analyze deployment pipeline, infrastructure, and operational procedures."

    echo -e "${GREEN}✅ Comprehensive system analysis initiated${NC}"
}

# Funzione per monitorare agenti in tempo reale
monitor_claude_agents() {
    echo -e "${GREEN}🔍 Claude Agents Real-Time Monitor${NC}"
    echo "Press Ctrl+C to stop monitoring"
    echo "================================="

    while true; do
        clear
        echo -e "${YELLOW}$(date) - Claude Multi-Agent Monitor${NC}"
        echo "======================================="

        for agent in "${AGENTS[@]}"; do
            local session_name="claude-$agent"
            if $TMUX_BIN has-session -t "$session_name" 2>/dev/null; then
                echo -e "${GREEN}✅ $agent agent${NC}"
                # Mostra ultime righe di output (più concise)
                local output=$($TMUX_BIN capture-pane -t "$session_name" -p | tail -3 | head -2)
                if [ -n "$output" ]; then
                    echo "$output" | sed 's/^/   /' | cut -c1-80
                fi
            else
                echo -e "${RED}❌ $agent - Offline${NC}"
            fi
            echo ""
        done

        echo -e "${BLUE}Commands: 'q' to quit, 'r' to restart all agents${NC}"
        sleep 3
    done
}

# Funzione per interazione rapida con agenti
quick_agent_interaction() {
    echo -e "${BLUE}🎯 Quick Agent Interaction${NC}"
    echo "=========================="

    PS3="Select agent: "
    select agent in "${AGENTS[@]}" "Exit"; do
        case $agent in
            "Exit")
                break
                ;;
            *)
                if [[ " ${AGENTS[@]} " =~ " ${agent} " ]]; then
                    echo ""
                    read -p "Enter task for $agent agent: " task
                    if [ -n "$task" ]; then
                        send_task_to_claude_agent "$agent" "$task"
                        echo ""
                        read -p "Connect to agent session? (y/n): " connect
                        if [[ $connect == "y" || $connect == "Y" ]]; then
                            $TMUX_BIN attach-session -t "claude-$agent"
                        fi
                    fi
                    echo ""
                else
                    echo "Invalid selection"
                fi
                ;;
        esac
    done
}

# Menu principale
show_menu() {
    echo -e "${PURPLE}Claude Orchestrator V2 - Real Multi-Agent System${NC}"
    echo "================================================="
    echo ""
    echo "🤖 AGENT MANAGEMENT:"
    echo "1. Start all Claude agents"
    echo "2. Check agents status"
    echo "3. Restart all agents"
    echo "4. Stop all agents"
    echo ""
    echo "🎯 INTELLIGENT WORKFLOWS:"
    echo "5. Feature development (full)"
    echo "6. API endpoint development"
    echo "7. Frontend component creation"
    echo "8. Database optimization"
    echo "9. Testing suite enhancement"
    echo "10. Deployment preparation"
    echo "11. System analysis (all domains)"
    echo ""
    echo "💬 AGENT INTERACTION:"
    echo "12. Quick agent interaction"
    echo "13. Monitor agents real-time"
    echo "14. Connect to agent session"
    echo ""
    echo "0. Exit"
    echo "================================================="
}

# Main
if [ $# -eq 0 ]; then
    show_menu
    read -p "Select option: " choice

    case $choice in
        1)
            $AGENT_LAUNCHER start-all
            ;;
        2)
            $AGENT_LAUNCHER status
            ;;
        3)
            echo -e "${YELLOW}Restarting all agents...${NC}"
            $AGENT_LAUNCHER stop-all
            sleep 2
            $AGENT_LAUNCHER start-all
            ;;
        4)
            $AGENT_LAUNCHER stop-all
            ;;
        5)
            read -p "Feature name: " feature
            workflow_with_claude_agents "feature-development" "$feature"
            ;;
        6)
            read -p "API endpoint name: " endpoint
            workflow_with_claude_agents "api-endpoint" "$endpoint"
            ;;
        7)
            read -p "Component name: " component
            workflow_with_claude_agents "frontend-component" "$component"
            ;;
        8)
            workflow_with_claude_agents "database-optimization"
            ;;
        9)
            workflow_with_claude_agents "testing-suite"
            ;;
        10)
            workflow_with_claude_agents "deployment-prep"
            ;;
        11)
            workflow_with_claude_agents "system-analysis"
            ;;
        12)
            quick_agent_interaction
            ;;
        13)
            monitor_claude_agents
            ;;
        14)
            PS3="Select agent session to connect: "
            select agent in "${AGENTS[@]}" "Cancel"; do
                case $agent in
                    "Cancel")
                        break
                        ;;
                    *)
                        if [[ " ${AGENTS[@]} " =~ " ${agent} " ]]; then
                            $TMUX_BIN attach-session -t "claude-$agent"
                            break
                        fi
                        ;;
                esac
            done
            ;;
        0)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid option"
            exit 1
            ;;
    esac
else
    # Modalità command line
    case "$1" in
        "agents")
            $AGENT_LAUNCHER "${@:2}"
            ;;
        "workflow")
            workflow_with_claude_agents "$2" "${3:-}"
            ;;
        "task")
            if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
                echo "Usage: $0 task <agent> <task_description>"
                exit 1
            fi
            send_task_to_claude_agent "$2" "$3"
            ;;
        "monitor")
            monitor_claude_agents
            ;;
        "status")
            check_agents_status
            ;;
        "connect")
            if [ -z "${2:-}" ]; then
                echo "Usage: $0 connect <agent_name>"
                exit 1
            fi
            $TMUX_BIN attach-session -t "claude-$2"
            ;;
        *)
            echo "Claude Orchestrator V2 - Real Multi-Agent System"
            echo "==============================================="
            echo ""
            echo "Usage: $0 <command> [args...]"
            echo ""
            echo "🤖 AGENT MANAGEMENT:"
            echo "  agents start-all             Start all Claude agents"
            echo "  agents status                Check agents status"
            echo "  agents stop-all              Stop all agents"
            echo "  status                       Quick status check"
            echo ""
            echo "🎯 WORKFLOWS:"
            echo "  workflow feature-development <name>    Full feature development"
            echo "  workflow api-endpoint <name>           API endpoint development"
            echo "  workflow frontend-component <name>     Frontend component creation"
            echo "  workflow database-optimization         Database optimization"
            echo "  workflow testing-suite                 Testing enhancement"
            echo "  workflow deployment-prep               Deployment preparation"
            echo "  workflow system-analysis               System analysis"
            echo ""
            echo "💬 INTERACTION:"
            echo "  task <agent> <description>   Send task to specific agent"
            echo "  connect <agent>              Connect to agent session"
            echo "  monitor                      Real-time agent monitoring"
            echo ""
            echo "Examples:"
            echo "  $0 workflow feature-development \"user-profile\""
            echo "  $0 task backend-api \"optimize user authentication endpoint\""
            echo "  $0 connect frontend-ui"
            echo "  $0 agents start-all"
            exit 1
            ;;
    esac
fi