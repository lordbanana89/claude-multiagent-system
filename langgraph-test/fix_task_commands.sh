#!/bin/bash

# 🔧 Fix Task Commands - Corregge il problema di sincronizzazione
# Carica i comandi task con la giusta configurazione

echo "🔧 Fixing Task Commands Configuration..."

# Imposta variabili corrette per la sessione corrente
SESSION_NAME=$(tmux display-message -p '#S' 2>/dev/null || echo "claude-backend-api")
export AGENT_SESSION="$SESSION_NAME"
export SHARED_STATE_FILE="/Users/erik/Desktop/claude-multiagent-system/langgraph-test/shared_state.json"

echo "✅ Configuration set:"
echo "   AGENT_SESSION: $AGENT_SESSION"
echo "   SHARED_STATE_FILE: $SHARED_STATE_FILE"

# Source i comandi task
source /Users/erik/Desktop/claude-multiagent-system/langgraph-test/task_commands.sh

echo "🎯 Task commands loaded and configured!"
echo "💡 Try: task-status"