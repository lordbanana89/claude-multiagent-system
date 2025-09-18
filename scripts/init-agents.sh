#!/bin/bash

# Initialize all agents with bash shells

TMUX='/opt/homebrew/bin/tmux'
PROJECT_ROOT="/Users/erik/Desktop/riona_ai/riona-ai"
AGENTS=('backend-api' 'database' 'frontend-ui' 'instagram' 'queue-manager' 'testing' 'deployment')

echo "🚀 Initializing all agents with bash shells..."
echo "============================================"

for agent in "${AGENTS[@]}"; do
    echo "Initializing $agent..."
    
    # Avvia bash nella sessione
    $TMUX send-keys -t "$agent" 'bash' Enter
    sleep 1
    
    # Imposta il working directory
    $TMUX send-keys -t "$agent" "cd $PROJECT_ROOT" Enter
    sleep 0.5
    
    # Banner di inizializzazione
    $TMUX send-keys -t "$agent" "clear" Enter
    $TMUX send-keys -t "$agent" "echo '═══════════════════════════════════════'" Enter
    $TMUX send-keys -t "$agent" "echo '🤖 $agent Agent Terminal'" Enter
    $TMUX send-keys -t "$agent" "echo '═══════════════════════════════════════'" Enter
    $TMUX send-keys -t "$agent" "echo 'Status: ✅ Initialized'" Enter
    $TMUX send-keys -t "$agent" "echo 'Project: RIONA AI'" Enter
    $TMUX send-keys -t "$agent" "echo 'Directory: '$PROJECT_ROOT" Enter
    $TMUX send-keys -t "$agent" "echo '═══════════════════════════════════════'" Enter
    $TMUX send-keys -t "$agent" "echo ''" Enter
    
    echo "✅ $agent initialized"
done

echo ""
echo "✅ All agents initialized successfully!"
echo ""
echo "Testing communication..."
./claude-orchestrator.sh broadcast 'echo "Agent responding: OK"' 2

echo ""
echo "🎯 System ready for multi-agent coordination!"
echo ""
echo "Available commands:"
echo "  ./claude-orchestrator.sh status"
echo "  ./claude-orchestrator.sh broadcast <command>"
echo "  ./claude-orchestrator.sh send <agent> <command>"
echo ""
echo "To attach to an agent session:"
echo "  tmux attach -t <agent-name>"
