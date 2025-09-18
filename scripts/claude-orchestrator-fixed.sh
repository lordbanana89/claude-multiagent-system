#!/bin/bash

# Claude Orchestrator Script - Fixed for tmux path
TMUX='/opt/homebrew/bin/tmux'
PROJECT_ROOT="/Users/erik/Desktop/riona_ai/riona-ai"
AGENTS=('backend-api' 'database' 'frontend-ui' 'instagram' 'queue-manager' 'testing' 'deployment')

case "$1" in
    status)
        echo '📊 System Status:'
        echo '==================='
        for agent in "${AGENTS[@]}"; do
            if $TMUX has-session -t "$agent" 2>/dev/null; then
                echo "✅ $agent: Active"
            else
                echo "❌ $agent: Not found"
            fi
        done
        echo ''
        echo 'Active tmux sessions:'
        $TMUX list-sessions 2>/dev/null || echo "No tmux sessions active"
        ;;
    
    create-sessions)
        echo '🚀 Creating all agent sessions...'
        for agent in "${AGENTS[@]}"; do
            if ! $TMUX has-session -t "$agent" 2>/dev/null; then
                echo "Creating session: $agent"
                $TMUX new-session -d -s "$agent" -c "$PROJECT_ROOT"
            else
                echo "Session exists: $agent"
            fi
        done
        echo '✅ All sessions ready!'
        ;;
    
    broadcast)
        shift
        echo "📢 Broadcasting: $*"
        for agent in "${AGENTS[@]}"; do
            if $TMUX has-session -t "$agent" 2>/dev/null; then
                $TMUX send-keys -t "$agent" "$*" Enter
                echo "   → Sent to $agent"
            else
                echo "   ❌ $agent session not found - creating..."
                $TMUX new-session -d -s "$agent" -c "$PROJECT_ROOT"
                sleep 1
                $TMUX send-keys -t "$agent" "$*" Enter
                echo "   → Created and sent to $agent"
            fi
        done
        ;;
    
    send)
        agent=$2
        shift 2
        echo "📨 Sending to $agent: $*"
        if $TMUX has-session -t "$agent" 2>/dev/null; then
            $TMUX send-keys -t "$agent" "$*" Enter
            echo "   ✓ Message delivered"
        else
            echo "   ❌ Agent session not found - creating..."
            $TMUX new-session -d -s "$agent" -c "$PROJECT_ROOT"
            sleep 1
            $TMUX send-keys -t "$agent" "$*" Enter
            echo "   ✓ Created session and delivered message"
        fi
        ;;
    
    attach)
        agent=${2:-backend-api}
        echo "📎 Attaching to $agent session..."
        if $TMUX has-session -t "$agent" 2>/dev/null; then
            $TMUX attach-session -t "$agent"
        else
            echo "❌ Session $agent not found"
        fi
        ;;
    
    *)
        echo 'Claude Orchestrator - Multi-Agent Coordinator'
        echo '============================================'
        echo 'Usage:'
        echo '  ./claude-orchestrator-fixed.sh status              - Show system status'
        echo '  ./claude-orchestrator-fixed.sh create-sessions     - Create all agent sessions'
        echo '  ./claude-orchestrator-fixed.sh broadcast <command> - Send to all agents'
        echo '  ./claude-orchestrator-fixed.sh send <agent> <cmd>  - Send to specific agent'
        echo '  ./claude-orchestrator-fixed.sh attach [agent]      - Attach to agent session'
        echo ''
        echo 'Available agents:'
        echo '  backend-api, database, frontend-ui, instagram,'
        echo '  queue-manager, testing, deployment'
        ;;
esac
