#!/bin/bash
# Riona AI Orchestrator Terminal Profile
# Source this file in your orchestrator terminal for quick access

# Colori per il terminale
export TERM=xterm-256color

# Path al progetto
export RIONA_PROJECT="/Users/erik/Desktop/riona_ai/riona-ai"
cd "$RIONA_PROJECT"

# Funzioni rapide per il coordinamento
project() {
    if [ -z "$1" ]; then
        echo "Usage: project \"Project description\""
        echo "Example: project \"Create user authentication system\""
        return 1
    fi
    ./claude-orchestrator.sh send task-coordinator "PROJECT COORDINATION: $1"
}

status() {
    echo "🎯 RIONA AI MULTI-AGENT SYSTEM STATUS"
    echo "===================================="
    ./.riona/agents/scripts/unified-agent-startup.sh status
}

coordinator() {
    echo "🎯 Connecting to Task Coordinator..."
    tmux attach-session -t task-coordinator
}

agent() {
    if [ -z "$1" ]; then
        echo "Available agents: task-coordinator, backend-api, database, frontend-ui, instagram, queue-manager, testing, deployment"
        return 1
    fi
    echo "🤖 Connecting to $1 agent..."
    tmux attach-session -t "$1"
}

monitor() {
    echo "🔍 Starting real-time agent monitoring..."
    ./.riona/agents/scripts/unified-agent-startup.sh monitor
}

start-agents() {
    echo "🚀 Starting complete multi-agent system..."
    ./.riona/agents/scripts/unified-agent-startup.sh start-all
}

restart-agents() {
    echo "🔄 Restarting complete multi-agent system..."
    ./.riona/agents/scripts/unified-agent-startup.sh restart-all
}

agents() {
    local cmd="${1:-status}"
    case "$cmd" in
        start|start-all)
            ./.riona/agents/scripts/unified-agent-startup.sh start-all
            ;;
        restart|restart-all)
            ./.riona/agents/scripts/unified-agent-startup.sh restart-all
            ;;
        stop|stop-all)
            ./.riona/agents/scripts/unified-agent-startup.sh stop-all
            ;;
        monitor)
            ./.riona/agents/scripts/unified-agent-startup.sh monitor
            ;;
        status|*)
            ./.riona/agents/scripts/unified-agent-startup.sh status
            ;;
    esac
}

workflow() {
    local type="${1:-feature-development}"
    local description="$2"

    if [ -z "$description" ]; then
        echo "Usage: workflow [type] \"description\""
        echo "Types: feature-development, api-endpoint, frontend-component, database-setup"
        echo "Example: workflow feature-development \"user dashboard\""
        return 1
    fi

    ./claude-orchestrator.sh workflow "$type" "$description"
}

# Alias per compatibilità
alias orchestrator='./claude-orchestrator.sh'
alias agents-status='agents status'
alias agents-monitor='agents monitor'
alias agents-start='agents start'
alias agents-restart='agents restart'
alias agents-stop='agents stop'

# Quick access to view agents
view() {
    local cmd="${1:-menu}"
    ./view-agents.sh "$cmd" "${2:-}"
}

# Quick connect function
connect() {
    local agent="${1:-task-coordinator}"
    echo "🔗 Connecting to $agent agent..."
    echo "Press Ctrl+B then D to detach from tmux session"
    tmux attach-session -t "$agent"
}

# Quick peek at agent activity
peek() {
    local agent="${1:-task-coordinator}"
    local lines="${2:-10}"
    echo "👁️  $agent Agent Activity (last $lines lines):"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tmux capture-pane -t "$agent" -p | tail -n "$lines" | sed 's/^/  /'
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Send a quick message to an agent
send() {
    local agent="${1:-task-coordinator}"
    shift
    local message="$*"

    if [ -z "$message" ]; then
        echo "Usage: send <agent> <message>"
        echo "Example: send task-coordinator \"Status update please\""
        return 1
    fi

    printf '%s\n' "$message" | tmux load-buffer -
    tmux paste-buffer -t "$agent"
    tmux send-keys -t "$agent" Enter
    echo "💬 Message sent to $agent: $message"
}

# Watch an agent in real-time
watch() {
    local agent="${1:-task-coordinator}"
    echo "👁️  Watching $agent agent in real-time..."
    echo "Press Ctrl+C to stop watching"
    echo "────────────────────────────────────────"

    while true; do
        clear
        echo "📺 $agent Agent - $(date '+%H:%M:%S')"
        echo "════════════════════════════════════════"
        tmux capture-pane -t "$agent" -p | tail -15
        echo ""
        echo "Press Ctrl+C to stop, or 'connect $agent' to attach"
        sleep 2
    done
}

# Help function
help-orchestrator() {
    echo "╔═══════════════════════════════════════════════╗"
    echo "║      🎯 RIONA AI ORCHESTRATOR TERMINAL        ║"
    echo "║            QUICK COMMAND REFERENCE            ║"
    echo "╚═══════════════════════════════════════════════╝"
    echo ""
    echo "📋 PROJECT COORDINATION:"
    echo "  project \"description\"     Send project to Task Coordinator"
    echo "  workflow \"description\"    Run coordinated workflow"
    echo ""
    echo "🤖 AGENT MANAGEMENT:"
    echo "  agents [start|restart|stop|status|monitor]"
    echo "  start-agents             Start all agents"
    echo "  restart-agents           Restart all agents"
    echo "  status                   Show agent status"
    echo "  monitor                  Real-time monitoring"
    echo ""
    echo "🔗 DIRECT CONNECTION:"
    echo "  coordinator              Connect to Task Coordinator"
    echo "  agent <name>             Connect to specific agent"
    echo ""
    echo "🛠️  SYSTEM COMMANDS:"
    echo "  ./after-reboot.sh        Complete system restore after reboot"
    echo "  orchestrator             Direct access to orchestrator"
    echo ""
    echo "📊 EXAMPLES:"
    echo "  project \"Create notification system\""
    echo "  workflow feature-development \"user dashboard\""
    echo "  agent backend-api"
    echo "  coordinator"
    echo ""
    echo "Available agents:"
    echo "  task-coordinator (capo squadra), backend-api, database,"
    echo "  frontend-ui, instagram, queue-manager, testing, deployment"
}

# Mostra banner di benvenuto
echo "╔═══════════════════════════════════════════════╗"
echo "║      🎯 RIONA AI ORCHESTRATOR TERMINAL        ║"
echo "║        Multi-Agent Coordination System        ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""
echo "Type 'help-orchestrator' for available commands"
echo "Type 'status' to check current agent status"
echo "Type 'project \"description\"' to start coordination"
echo ""

# Mostra status iniziale se gli agenti sono già avviati
if tmux has-session -t task-coordinator 2>/dev/null; then
    echo "✅ Multi-agent system is active"
    status
else
    echo "⚠️  Multi-agent system not running"
    echo "Run './after-reboot.sh' or 'start-agents' to initialize"
fi

echo ""