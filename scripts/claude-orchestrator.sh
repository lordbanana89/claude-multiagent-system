#!/bin/bash
# Claude Orchestrator - Coordina tutti i sub-agenti con gestione corretta di Enter e risposte

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

# Lista agenti (prompt-validator per primo, poi task-coordinator come capo squadra)
AGENTS=("prompt-validator" "task-coordinator" "backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")

# Percorso corretto di tmux
unset TMUX 2>/dev/null || true
TMUX_BIN="/opt/homebrew/bin/tmux"

# Funzione per inviare task specializzato a un vero sub-agente Claude Code
send_agent_task() {
    local agent="$1"
    local task="$2"
    local wait_time="${3:-10}"

    echo -e "${BLUE}📋 Sending specialized task to $agent agent:${NC}"
    echo -e "${PURPLE}Task: $task${NC}"
    echo ""

    # Prepara il task con contesto di agente specializzato
    local agent_prompt="AGENT TASK for ${agent} specialist:

$task

Please respond as the specialized $agent agent for the Riona AI Instagram automation platform. Analyze this task from your domain expertise and provide:

1. Technical assessment and feasibility
2. Specific implementation approach
3. Dependencies and coordination needs
4. Complexity rating (1-10)
5. Next steps and recommendations

Focus on your specialized area and be specific and actionable."

    # Invia il task all'agente
    printf '%s\n' "$agent_prompt" | $TMUX_BIN load-buffer -
    $TMUX_BIN paste-buffer -t "$agent"
    $TMUX_BIN send-keys -t "$agent" Enter

    echo -e "${GREEN}✅ Specialized task sent to $agent agent${NC}"
    echo -e "   Wait time: ${wait_time}s for agent analysis"
    echo ""

    # Attende risposta dell'agente
    sleep "$wait_time"

    # Cattura e mostra risposta dell'agente
    echo -e "${YELLOW}=== $agent AGENT RESPONSE ===${NC}"
    $TMUX_BIN capture-pane -t "$agent" -p | tail -15
    echo ""
}

# Nuova funzione per flusso coordinato: Prompt Validator → Task Coordinator → Agente Specializzato
send_coordinated_task() {
    local raw_task="$1"
    local wait_time="${2:-12}"

    echo -e "${PURPLE}🔄 COORDINATED TASK PROCESSING FLOW${NC}"
    echo -e "${CYAN}Step 1: Prompt Validation → Step 2: Task Coordination → Step 3: Agent Assignment${NC}"
    echo ""

    # STEP 1: Invia al Prompt Validator
    echo -e "${BLUE}📝 STEP 1: Sending to Prompt Validator...${NC}"
    local validator_prompt="PROMPT VALIDATION REQUEST:

Raw Task: $raw_task

Please analyze this task and provide your validation report with:
- Status (VALID/NEEDS_CLARIFICATION/INVALID)
- Recommended Agent
- Formatted Task for Task Coordinator
- Missing Information (if any)
- Dependencies

This will be forwarded to the Task Coordinator for agent assignment."

    printf '%s\n' "$validator_prompt" | $TMUX_BIN load-buffer -
    $TMUX_BIN paste-buffer -t "prompt-validator"
    $TMUX_BIN send-keys -t "prompt-validator" Enter

    echo -e "${GREEN}✅ Task sent to Prompt Validator${NC}"
    echo -e "${YELLOW}⏳ Waiting ${wait_time}s for validation...${NC}"
    sleep "$wait_time"

    # STEP 2: Invia al Task Coordinator
    echo -e "${BLUE}🎯 STEP 2: Sending to Task Coordinator for assignment...${NC}"
    local coordinator_prompt="TASK COORDINATION REQUEST:

Original Task: $raw_task

The Prompt Validator has analyzed this task. Please:
1. Review the validation report from prompt-validator
2. Determine the best specialized agent for this task
3. Send the task directly to the appropriate agent
4. Coordinate any multi-agent dependencies

Available agents: backend-api, database, frontend-ui, instagram, queue-manager, testing, deployment

Please read the prompt-validator's recommendation and assign the task to the specialized agent now."

    printf '%s\n' "$coordinator_prompt" | $TMUX_BIN load-buffer -
    $TMUX_BIN paste-buffer -t "task-coordinator"
    $TMUX_BIN send-keys -t "task-coordinator" Enter

    echo -e "${GREEN}✅ Task sent to Task Coordinator for agent assignment${NC}"
    echo -e "${YELLOW}⏳ Task Coordinator will now assign to the appropriate specialized agent${NC}"
    echo ""

    echo -e "${PURPLE}🎯 COORDINATED FLOW INITIATED${NC}"
    echo "  1. ✅ Prompt Validator: Task analyzed and validated"
    echo "  2. ✅ Task Coordinator: Reviewing and assigning to specialist"
    echo "  3. ⏳ Specialized Agent: Will receive task from coordinator"
    echo ""
    echo -e "${CYAN}💡 Monitor progress with: ./view-agents.sh all-terminals${NC}"
}

# Funzione per verificare tutti gli agenti con un task di test
test_all_agents() {
    local test_task="${1:-Identify yourself as a specialized agent and confirm you are ready to work on Riona AI tasks}"
    local wait_time="${2:-10}"

    echo -e "${GREEN}Testing all agents with specialized task${NC}"
    echo "========================================"

    for agent in "${AGENTS[@]}"; do
        if $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
            send_agent_task "$agent" "$test_task" "$wait_time"
        else
            echo -e "${RED}❌ Agent $agent session not found${NC}"
            echo "   Create with: tmux new-session -d -s $agent"
            echo ""
        fi
    done
}

# Funzione per inviare task a singolo agente
send_to_agent() {
    local agent="$1"
    local task="$2"
    local wait_time="${3:-10}"

    if $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
        send_agent_task "$agent" "$task" "$wait_time"
    else
        echo -e "${RED}❌ Agent $agent session not found${NC}"
        echo "   Create session with: tmux new-session -d -s $agent"
        return 1
    fi
}

# Funzione per inviare progetto completo al Task Coordinator
send_project_to_coordinator() {
    local project_type="$1"
    local project_description="$2"
    local priority="${3:-medium}"

    local coordinator_brief="🎯 PROJECT COORDINATION REQUEST

Project Type: $project_type
Description: $project_description
Priority: $priority

COORDINATOR INSTRUCTIONS:
1. Analyze project requirements and complexity
2. Identify which specialized agents are needed
3. Break down into agent-specific tasks with clear deliverables
4. Route tasks to appropriate agents with proper context
5. Monitor progress and coordinate handoffs between agents
6. Escalate any blockers or dependencies
7. Provide regular status updates

Available Specialized Agents:
• backend-api: Express.js, Node.js, API development
• database: PostgreSQL, TypeORM, schema design
• frontend-ui: React, TypeScript, UI components
• instagram: Instagram API, OAuth, media management
• queue-manager: Redis, Bull, background job processing
• testing: Jest, Playwright, QA automation
• deployment: Docker, CI/CD, infrastructure

Begin coordinated workflow and distribute tasks now."

    echo -e "${PURPLE}📋 Sending project to Task Coordinator...${NC}"
    echo -e "${BLUE}Project: $project_description${NC}"
    echo ""

    send_agent_task "task-coordinator" "$coordinator_brief" 15

    echo ""
    echo -e "${GREEN}✅ Project sent to Task Coordinator${NC}"
    echo -e "${YELLOW}💡 The coordinator will now distribute tasks to specialized agents${NC}"
    echo ""
    echo "Monitor coordination progress:"
    echo "  tmux attach-session -t task-coordinator"
    echo ""
    echo "Check agent activity:"
    echo "  ./.riona/agents/scripts/unified-agent-startup.sh monitor"
}

# Funzione per richiedere status al Task Coordinator
request_project_status() {
    local project_name="${1:-current project}"

    local status_request="STATUS UPDATE REQUEST

Project: $project_name

Please provide a comprehensive status update including:

1. OVERALL PROGRESS: Current phase and completion percentage
2. ACTIVE TASKS: Which agents are currently working on what
3. COMPLETED TASKS: What has been finished and validated
4. PENDING TASKS: What is queued or waiting for dependencies
5. BLOCKERS: Any issues preventing progress
6. NEXT STEPS: What will happen next and estimated timeline

Format as a clear, structured status report."

    echo -e "${CYAN}📊 Requesting project status from Task Coordinator...${NC}"
    send_agent_task "task-coordinator" "$status_request" 10
}

# Funzione per broadcast a tutti gli agenti
broadcast_command() {
    local command="$1"
    local wait_time="${2:-8}"
    
    echo -e "${GREEN}Broadcasting command to all agents: $command${NC}"
    echo "==========================================="
    
    # Invia a tutti contemporaneamente
    for agent in "${AGENTS[@]}"; do
        if $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
            echo -e "${BLUE}Sending to $agent...${NC}"
            $TMUX_BIN send-keys -t "$agent" "$command" Enter
            sleep 1
            $TMUX_BIN send-keys -t "$agent" Enter
        fi
    done
    
    # Attende e cattura risposte
    sleep "$wait_time"
    
    # Raccoglie risposte
    for agent in "${AGENTS[@]}"; do
        if $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
            echo -e "${YELLOW}=== $agent RESPONSE ===${NC}"
            $TMUX_BIN capture-pane -t "$agent" -p | tail -15
            echo ""
        fi
    done
}

# Funzione per status degli agenti
agent_status() {
    echo -e "${GREEN}Agent Status Check${NC}"
    echo "=================="
    
    for agent in "${AGENTS[@]}"; do
        if $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
            echo -e "${GREEN}✅ $agent${NC} - Active"
        else
            echo -e "${RED}❌ $agent${NC} - Not found"
        fi
    done
}

# Funzione per analisi e autorizzazione task
analyze_and_authorize() {
    local task_type="$1"
    local task_description="$2"
    local context="${3:-}"
    
    echo -e "${BLUE}🔍 TASK ANALYSIS & AUTHORIZATION${NC}"
    echo "=================================="
    echo "Task Type: $task_type"
    echo "Description: $task_description"
    if [ -n "$context" ]; then
        echo "Context: $context"
    fi
    echo ""
    
    # Fase 1: Analisi della richiesta
    echo -e "${YELLOW}📋 Phase 1: Request Analysis${NC}"
    echo "Analyzing task feasibility and requirements..."
    
    # Consulta agenti relevanti per analisi preliminare
    case "$task_type" in
        "feature-full"|"user-auth"|"api-endpoint")
            echo "→ Consulting backend-api agent for technical feasibility..."
            send_command_with_response "backend-api" "Analyze feasibility: Is '$task_description' technically feasible? What are the main challenges? Rate complexity 1-10." 8
            
            echo "→ Consulting database agent for data requirements..."
            send_command_with_response "database" "Analyze data requirements: What database changes are needed for '$task_description'? Any migration risks?" 8
            ;;
        "frontend-component"|"frontend-ui")
            echo "→ Consulting frontend-ui agent for UI feasibility..."
            send_command_with_response "frontend-ui" "Analyze UI feasibility: Is '$task_description' implementable with current tech stack? Complexity rating 1-10?" 8
            ;;
        "database-setup"|"performance")
            echo "→ Consulting database agent for impact analysis..."
            send_command_with_response "database" "Analyze impact: What are the risks and benefits of '$task_description'? Recommend proceed/halt." 8
            ;;
    esac
    
    # Fase 2: Decisione autorizzazione
    echo -e "${YELLOW}🚦 Phase 2: Authorization Decision${NC}"
    echo "Based on analysis, should we proceed?"
    echo ""
    echo "Options:"
    echo "1. ✅ Proceed - Task is feasible and recommended"
    echo "2. ⚠️  Proceed with caution - Task has risks but manageable"
    echo "3. 🔄 Modify approach - Task needs different strategy"
    echo "4. ❌ Halt - Task is not recommended/feasible"
    echo "5. 📋 Need more analysis - Require additional assessment"
    echo ""
    
    read -p "Your decision (1-5): " decision
    
    case $decision in
        1)
            echo -e "${GREEN}✅ AUTHORIZED: Proceeding with full workflow${NC}"
            return 0
            ;;
        2)
            echo -e "${YELLOW}⚠️  AUTHORIZED WITH CAUTION: Proceeding with monitoring${NC}"
            echo "Will add validation checkpoints..."
            return 0
            ;;
        3)
            echo -e "${BLUE}🔄 MODIFICATION REQUIRED${NC}"
            read -p "Enter modified approach: " modified_approach
            echo "Modified approach: $modified_approach"
            return 0
            ;;
        4)
            echo -e "${RED}❌ HALTED: Task not authorized${NC}"
            read -p "Reason for halt: " halt_reason
            echo "Halt reason recorded: $halt_reason"
            return 1
            ;;
        5)
            echo -e "${BLUE}📋 ADDITIONAL ANALYSIS REQUIRED${NC}"
            additional_analysis "$task_type" "$task_description"
            return $?
            ;;
        *)
            echo -e "${RED}Invalid choice. Defaulting to HALT.${NC}"
            return 1
            ;;
    esac
}

# Funzione per analisi aggiuntiva
additional_analysis() {
    local task_type="$1"
    local task_description="$2"
    
    echo -e "${BLUE}📊 DEEP ANALYSIS MODE${NC}"
    echo "====================="
    
    # Consulta tutti gli agenti relevanti
    echo "→ Getting comprehensive assessment from all relevant agents..."
    
    broadcast_command "ANALYSIS REQUEST: Evaluate '$task_description' from your expertise perspective. Provide: 1) Feasibility (Yes/No), 2) Complexity (1-10), 3) Risks, 4) Dependencies, 5) Recommendation" 12
    
    echo -e "${YELLOW}Review the responses above.${NC}"
    echo "Based on comprehensive analysis:"
    echo "1. ✅ Proceed"
    echo "2. ❌ Halt"
    
    read -p "Final decision (1-2): " final_decision
    
    case $final_decision in
        1)
            echo -e "${GREEN}✅ AUTHORIZED after deep analysis${NC}"
            return 0
            ;;
        *)
            echo -e "${RED}❌ HALTED after deep analysis${NC}"
            return 1
            ;;
    esac
}

# Funzione per validazione step intermedi
validate_step() {
    local step_name="$1"
    local agent="$2"
    local expected_output="$3"
    
    echo -e "${YELLOW}🔍 STEP VALIDATION: $step_name${NC}"
    echo "Validating work from: $agent"
    echo "Expected: $expected_output"
    echo ""
    
    # Cattura output dell'agente
    local agent_output=$($TMUX_BIN capture-pane -t "$agent" -p | tail -10)
    
    echo "Agent Output (last 10 lines):"
    echo "$agent_output"
    echo ""
    
    echo "Validation Options:"
    echo "1. ✅ Accept - Work is satisfactory, continue"
    echo "2. 🔄 Retry - Ask agent to revise/improve"
    echo "3. ⚠️  Accept with notes - Continue but flag issues"
    echo "4. ❌ Reject - Stop workflow due to poor quality"
    echo ""
    
    read -p "Validation decision (1-4): " validation
    
    case $validation in
        1)
            echo -e "${GREEN}✅ STEP APPROVED: $step_name${NC}"
            return 0
            ;;
        2)
            echo -e "${YELLOW}🔄 REQUESTING REVISION${NC}"
            read -p "Feedback for agent: " feedback
            send_command_with_response "$agent" "REVISION REQUEST: $feedback. Please improve your previous work." 10
            
            # Recursive validation after revision
            validate_step "$step_name" "$agent" "$expected_output"
            return $?
            ;;
        3)
            echo -e "${YELLOW}⚠️  ACCEPTED WITH CONCERNS${NC}"
            read -p "Note concerns for later review: " concerns
            echo "Concerns logged: $concerns"
            return 0
            ;;
        4)
            echo -e "${RED}❌ STEP REJECTED - WORKFLOW HALTED${NC}"
            read -p "Rejection reason: " reason
            echo "Workflow halted due to: $reason"
            return 1
            ;;
        *)
            echo -e "${RED}Invalid choice. Defaulting to REJECT.${NC}"
            return 1
            ;;
    esac
}

# Funzione per workflow predefiniti con analisi
workflow() {
    local workflow_name="$1"
    local description="${2:-}"
    
    echo -e "${GREEN}🎯 INTELLIGENT WORKFLOW SYSTEM${NC}"
    echo "==============================="
    echo "Workflow: $workflow_name"
    if [ -n "$description" ]; then
        echo "Description: $description"
    fi
    echo ""
    
    # FASE OBBLIGATORIA: Analisi e autorizzazione
    if ! analyze_and_authorize "$workflow_name" "$description"; then
        echo -e "${RED}🛑 Workflow terminated - Not authorized${NC}"
        return 1
    fi
    
    echo ""
    echo -e "${GREEN}🚀 Starting authorized workflow...${NC}"
    echo "========================================"
    
    case "$workflow_name" in
        "feature-full")
            workflow_feature_complete "$description"
            ;;
        "user-auth")
            workflow_user_authentication
            ;;
        "database-setup")
            workflow_database_setup
            ;;
        "frontend-component")
            workflow_frontend_component "$description"
            ;;
        "api-endpoint")
            workflow_api_endpoint "$description"
            ;;
        "testing-suite")
            workflow_testing_suite
            ;;
        "deployment")
            workflow_deployment
            ;;
        *)
            echo -e "${RED}Unknown workflow: $workflow_name${NC}"
            echo "Available workflows: feature-full, user-auth, database-setup, frontend-component, api-endpoint, testing-suite, deployment"
            return 1
            ;;
    esac
}

# Workflow coordinato tramite Task Coordinator
workflow_feature_complete() {
    local feature="$1"
    echo -e "${BLUE}🎯 Coordinated Feature Development: $feature${NC}"
    echo "Using Task Coordinator for intelligent task distribution"
    echo ""

    # Invia il progetto completo al Task Coordinator
    local project_brief="PROJECT COORDINATION REQUEST:

Feature: $feature
Type: Complete feature development
Priority: High

Please analyze this feature request and:
1. Break it down into agent-specific tasks
2. Route tasks to appropriate specialized agents
3. Monitor progress and coordinate dependencies
4. Provide status updates throughout the workflow

Coordinate with: backend-api, database, frontend-ui, testing agents as needed.

Begin coordinated workflow now."

    echo "1️⃣ Sending project to Task Coordinator..."
    send_agent_task "task-coordinator" "$project_brief" 15
    
    # Validazione fase planning
    if ! validate_step "Planning Phase" "backend-api" "Technical plan and architecture overview"; then
        return 1
    fi
    
    echo "2️⃣ Database Design..."
    send_command_with_response "database" "Design database schema and entities needed for $feature" 10
    
    # Validazione database design
    if ! validate_step "Database Design" "database" "Schema design with entities and relationships"; then
        return 1
    fi
    
    echo "3️⃣ Backend API Development..."
    send_command_with_response "backend-api" "Implement REST API endpoints for $feature" 12
    
    # Validazione backend API
    if ! validate_step "Backend API" "backend-api" "API endpoints with proper validation and error handling"; then
        return 1
    fi
    
    echo "4️⃣ Frontend UI Development..."
    send_command_with_response "frontend-ui" "Create React components and UI for $feature" 12
    
    # Validazione frontend
    if ! validate_step "Frontend UI" "frontend-ui" "React components with proper TypeScript and styling"; then
        return 1
    fi
    
    echo "5️⃣ Testing Implementation..."
    send_command_with_response "testing" "Write comprehensive tests for $feature" 10
    
    # Validazione testing
    if ! validate_step "Testing Suite" "testing" "Unit and integration tests with good coverage"; then
        return 1
    fi
    
    echo "6️⃣ Deployment Preparation..."
    send_command_with_response "deployment" "Prepare deployment configuration for $feature" 8
    
    # Validazione deployment
    if ! validate_step "Deployment Config" "deployment" "Production-ready deployment configuration"; then
        return 1
    fi
    
    echo -e "${GREEN}✅ Feature workflow completed with validation: $feature${NC}"
    
    # Validazione finale
    echo -e "${BLUE}🏁 FINAL VALIDATION${NC}"
    echo "Feature development completed. Ready for production?"
    echo "1. ✅ Approve for production"
    echo "2. 🔄 Needs additional work"
    echo "3. ❌ Not ready for production"
    
    read -p "Final approval (1-3): " final_approval
    
    case $final_approval in
        1)
            echo -e "${GREEN}🎉 FEATURE APPROVED FOR PRODUCTION: $feature${NC}"
            ;;
        2)
            echo -e "${YELLOW}⚠️  FEATURE NEEDS ADDITIONAL WORK${NC}"
            read -p "What additional work is needed: " additional_work
            echo "Additional work required: $additional_work"
            ;;
        3)
            echo -e "${RED}❌ FEATURE NOT READY FOR PRODUCTION${NC}"
            read -p "Reason for rejection: " rejection_reason
            echo "Rejection reason: $rejection_reason"
            ;;
    esac
}

# Workflow: User Authentication
workflow_user_authentication() {
    echo -e "${BLUE}🔐 User Authentication Workflow${NC}"
    
    echo "1️⃣ Database Schema..."
    send_command_with_response "database" "Design user authentication schema with JWT support" 8
    
    echo "2️⃣ Backend Auth API..."
    send_command_with_response "backend-api" "Implement JWT authentication endpoints (login, register, refresh)" 10
    
    echo "3️⃣ Frontend Auth Components..."
    send_command_with_response "frontend-ui" "Create login/register forms and auth state management" 10
    
    echo "4️⃣ Auth Testing..."
    send_command_with_response "testing" "Write authentication flow tests" 8
    
    echo -e "${GREEN}✅ Authentication workflow completed${NC}"
}

# Workflow: Database Setup
workflow_database_setup() {
    echo -e "${BLUE}💾 Database Setup Workflow${NC}"
    
    echo "1️⃣ Schema Analysis..."
    send_command_with_response "database" "Analyze current schema and suggest optimizations" 8
    
    echo "2️⃣ Migration Planning..."
    send_command_with_response "database" "Plan necessary database migrations" 8
    
    echo "3️⃣ Performance Review..."
    send_command_with_response "database" "Review indexes and query performance" 8
    
    echo -e "${GREEN}✅ Database setup workflow completed${NC}"
}

# Workflow: Frontend Component
workflow_frontend_component() {
    local component="$1"
    echo -e "${BLUE}🎨 Frontend Component Workflow: $component${NC}"
    
    echo "1️⃣ Component Design..."
    send_command_with_response "frontend-ui" "Design and implement $component React component" 10
    
    echo "2️⃣ Styling & Responsive..."
    send_command_with_response "frontend-ui" "Add Tailwind styling and responsive design for $component" 8
    
    echo "3️⃣ Component Testing..."
    send_command_with_response "testing" "Write React component tests for $component" 8
    
    echo -e "${GREEN}✅ Component workflow completed: $component${NC}"
}

# Workflow: API Endpoint
workflow_api_endpoint() {
    local endpoint="$1"
    echo -e "${BLUE}🔌 API Endpoint Workflow: $endpoint${NC}"
    
    echo "1️⃣ Database Requirements..."
    send_command_with_response "database" "Define data requirements for $endpoint API" 6
    
    echo "2️⃣ API Implementation..."
    send_command_with_response "backend-api" "Implement $endpoint API endpoint with validation and error handling" 10
    
    echo "3️⃣ API Testing..."
    send_command_with_response "testing" "Write API integration tests for $endpoint" 8
    
    echo -e "${GREEN}✅ API endpoint workflow completed: $endpoint${NC}"
}

# Workflow: Testing Suite
workflow_testing_suite() {
    echo -e "${BLUE}🧪 Testing Suite Workflow${NC}"
    
    echo "1️⃣ Backend API Tests..."
    send_command_with_response "testing" "Review and enhance backend API test coverage" 8
    
    echo "2️⃣ Frontend Component Tests..."
    send_command_with_response "testing" "Review and enhance frontend component test coverage" 8
    
    echo "3️⃣ Integration Tests..."
    send_command_with_response "testing" "Create end-to-end integration tests" 10
    
    echo "4️⃣ Test Report..."
    send_command_with_response "testing" "Generate comprehensive test coverage report" 6
    
    echo -e "${GREEN}✅ Testing workflow completed${NC}"
}

# Workflow: Deployment
workflow_deployment() {
    echo -e "${BLUE}🚀 Deployment Workflow${NC}"
    
    echo "1️⃣ Pre-deployment Checks..."
    send_command_with_response "testing" "Run full test suite for deployment readiness" 10
    
    echo "2️⃣ Build & Package..."
    send_command_with_response "deployment" "Prepare production build and Docker containers" 10
    
    echo "3️⃣ Infrastructure Check..."
    send_command_with_response "deployment" "Verify infrastructure and deployment pipeline" 8
    
    echo "4️⃣ Deploy..."
    send_command_with_response "deployment" "Execute deployment to staging environment" 12
    
    echo -e "${GREEN}✅ Deployment workflow completed${NC}"
}

# Funzione per monitoring real-time
monitor() {
    echo -e "${GREEN}🔍 Real-time Agent Monitoring${NC}"
    echo "Press Ctrl+C to stop monitoring"
    echo "================================"
    
    while true; do
        clear
        echo -e "${YELLOW}$(date)${NC}"
        echo "=========================="
        
        for agent in "${AGENTS[@]}"; do
            if $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
                echo -e "${GREEN}✅ $agent${NC}"
                # Mostra ultime 2 righe output
                $TMUX_BIN capture-pane -t "$agent" -p | tail -2 | sed 's/^/   /'
            else
                echo -e "${RED}❌ $agent - Not Active${NC}"
            fi
            echo ""
        done
        
        sleep 5
    done
}

# Funzione per health check completo
health_check() {
    echo -e "${GREEN}🏥 System Health Check${NC}"
    echo "======================="
    
    local healthy=0
    local total=0
    
    for agent in "${AGENTS[@]}"; do
        total=$((total + 1))
        echo -n "Checking $agent... "
        
        if $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
            # Test responsiveness
            $TMUX_BIN send-keys -t "$agent" "echo health-check-$(date +%s)" Enter
            sleep 2
            
            local response=$($TMUX_BIN capture-pane -t "$agent" -p | tail -5)
            if echo "$response" | grep -q "health-check"; then
                echo -e "${GREEN}✅ Healthy${NC}"
                healthy=$((healthy + 1))
            else
                echo -e "${YELLOW}⚠️ Unresponsive${NC}"
            fi
        else
            echo -e "${RED}❌ Offline${NC}"
        fi
    done
    
    echo "======================="
    echo -e "Health Score: ${GREEN}$healthy${NC}/$total agents healthy"
    
    if [ $healthy -eq $total ]; then
        echo -e "${GREEN}🎉 All systems operational!${NC}"
    elif [ $healthy -gt $((total / 2)) ]; then
        echo -e "${YELLOW}⚠️ Some agents need attention${NC}"
    else
        echo -e "${RED}🚨 System degraded - immediate attention required${NC}"
    fi
}

# Funzione per analisi performance
performance_analysis() {
    echo -e "${GREEN}⚡ Performance Analysis${NC}"
    echo "======================"
    
    echo "📊 Analyzing system performance..."
    
    echo "1️⃣ Backend API Performance..."
    send_command_with_response "backend-api" "Analyze current API performance and identify bottlenecks" 10
    
    echo "2️⃣ Database Performance..."
    send_command_with_response "database" "Review database query performance and suggest optimizations" 10
    
    echo "3️⃣ Frontend Performance..."
    send_command_with_response "frontend-ui" "Analyze frontend bundle size and rendering performance" 8
    
    echo "4️⃣ Queue Performance..."
    send_command_with_response "queue-manager" "Review background job performance and queue metrics" 8
    
    echo -e "${GREEN}✅ Performance analysis completed${NC}"
}

# Menu principale
show_menu() {
    echo -e "${YELLOW}Claude Orchestrator - Enhanced Multi-Agent Manager${NC}"
    echo "=================================================="
    echo "📊 BASIC OPERATIONS:"
    echo "1. Test all agents (pwd)"
    echo "2. Broadcast command to all agents"
    echo "3. Send command to single agent"
    echo "4. Agent status check"
    echo ""
    echo "🎯 COORDINATED WORKFLOWS (via Task Coordinator):"
    echo "5. Complete feature development"
    echo "6. Send project to Task Coordinator"
    echo "7. Request project status"
    echo "8. Database optimization"
    echo "9. Frontend component creation"
    echo "10. API endpoint development"
    echo "11. Testing suite execution"
    echo "12. Deployment workflow"
    echo ""
    echo "🔍 MONITORING & HEALTH:"
    echo "13. Real-time monitoring"
    echo "14. System health check"
    echo "15. Performance analysis"
    echo ""
    echo "0. Exit"
    echo "=================================================="
}

# Main
if [ $# -eq 0 ]; then
    show_menu
    read -p "Select option: " choice
    
    case $choice in
        1)
            test_all_agents "pwd"
            ;;
        2)
            read -p "Enter command: " cmd
            read -p "Wait time (default 8): " wait
            wait=${wait:-8}
            broadcast_command "$cmd" "$wait"
            ;;
        3)
            read -p "Agent name: " agent
            read -p "Command: " cmd
            read -p "Wait time (default 8): " wait
            wait=${wait:-8}
            send_to_agent "$agent" "$cmd" "$wait"
            ;;
        4)
            agent_status
            ;;
        5)
            read -p "Feature name: " feature
            workflow "feature-full" "$feature"
            ;;
        6)
            read -p "Project type: " project_type
            read -p "Project description: " project_desc
            read -p "Priority (high/medium/low): " priority
            priority=${priority:-medium}
            send_project_to_coordinator "$project_type" "$project_desc" "$priority"
            ;;
        7)
            read -p "Project name (or press enter for current): " project_name
            request_project_status "$project_name"
            ;;
        8)
            workflow "database-setup"
            ;;
        9)
            read -p "Component name: " component
            workflow "frontend-component" "$component"
            ;;
        10)
            read -p "Endpoint name: " endpoint
            workflow "api-endpoint" "$endpoint"
            ;;
        11)
            workflow "testing-suite"
            ;;
        12)
            workflow "deployment"
            ;;
        13)
            monitor
            ;;
        14)
            health_check
            ;;
        15)
            performance_analysis
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
        "test")
            test_all_agents "${2:-pwd}" "${3:-8}"
            ;;
        "broadcast")
            broadcast_command "$2" "${3:-8}"
            ;;
        "send")
            send_to_agent "$2" "$3" "${4:-8}"
            ;;
        "coordinate")
            send_coordinated_task "$2" "${3:-12}"
            ;;
        "status")
            agent_status
            ;;
        "workflow")
            workflow "$2" "${3:-}"
            ;;
        "monitor")
            monitor
            ;;
        "health")
            health_check
            ;;
        "performance")
            performance_analysis
            ;;
        "menu")
            show_menu
            read -p "Select option: " choice
            # Reimplementa la logica del menu qui se necessario
            ;;
        *)
            echo "Usage: $0 <command> [args...]"
            echo ""
            echo "📊 BASIC OPERATIONS:"
            echo "  test [command] [wait_time]        Test all agents"
            echo "  broadcast <command> [wait_time]   Send command to all agents"
            echo "  send <agent> <command> [wait_time] Send command to specific agent"
            echo "  coordinate <task> [wait_time]     Send task through validation → coordination → assignment"
            echo "  status                            Check agent status"
            echo ""
            echo "🎯 INTELLIGENT WORKFLOWS:"
            echo "  workflow feature-full <name>     Complete feature development"
            echo "  workflow user-auth               User authentication setup"
            echo "  workflow database-setup          Database optimization"
            echo "  workflow frontend-component <name> Frontend component creation"
            echo "  workflow api-endpoint <name>     API endpoint development"
            echo "  workflow testing-suite           Testing suite execution"
            echo "  workflow deployment              Deployment workflow"
            echo ""
            echo "🔍 MONITORING & HEALTH:"
            echo "  monitor                          Real-time monitoring"
            echo "  health                           System health check"
            echo "  performance                      Performance analysis"
            echo "  menu                             Interactive menu"
            echo ""
            echo "Examples:"
            echo "  $0 coordinate \"Create user profile dashboard\""
            echo "  $0 workflow feature-full \"user-profile\""
            echo "  $0 workflow api-endpoint \"user-settings\""
            echo "  $0 broadcast \"pwd\""
            echo "  $0 health"
            exit 1
            ;;
    esac
fi
