#!/bin/bash

# 🚀 Avvia Agenti Claude con MCP Configurato
echo "════════════════════════════════════════════════════════════════"
echo "       🤖 CLAUDE MULTI-AGENT SYSTEM CON MCP"
echo "════════════════════════════════════════════════════════════════"
echo ""

PROJECT_DIR="/Users/erik/Desktop/claude-multiagent-system"

# Funzione per avviare un agente
start_agent() {
    local agent_name="$1"
    local session_name="claude-$agent_name"

    echo "🚀 Avvio agente: $agent_name"

    # Kill sessione esistente
    tmux kill-session -t "$session_name" 2>/dev/null

    # Crea nuova sessione
    tmux new-session -d -s "$session_name"

    # Configura ambiente
    tmux send-keys -t "$session_name" "cd $PROJECT_DIR" Enter

    # IMPORTANTE: Informa l'agente del sistema multi-agent e MCP
    tmux send-keys -t "$session_name" "# Agent: $agent_name" Enter
    tmux send-keys -t "$session_name" "# Part of Multi-Agent System" Enter
    tmux send-keys -t "$session_name" "# MCP Server configured in ~/.claude/config/.claude.json" Enter

    # Avvia Claude
    tmux send-keys -t "$session_name" "claude" Enter

    # Dopo 3 secondi, invia istruzioni iniziali
    sleep 3

    tmux send-keys -t "$session_name" "
You are the $agent_name agent in a multi-agent system. Other agents include:
- backend-api: Backend development and APIs
- database: Database schema and queries
- frontend-ui: User interface development
- testing: Test creation and validation
- supervisor: Overall coordination

IMPORTANT: You have MCP tools available for coordination:
- Use 'log_activity' to announce what you're doing
- Use 'check_conflicts' before major changes
- Use 'get_agent_status' to see what others are doing
- Use 'register_component' when creating new components
- Use 'coordinate_decision' for important decisions

To use MCP tools, simply say something like:
'I'll use the log_activity MCP tool to announce: Starting work on user authentication'

The shared context is automatically maintained through MCP.
" Enter

    echo "✅ Agente $agent_name avviato in sessione $session_name"
}

# Menu di selezione
echo "📋 Cosa vuoi fare?"
echo ""
echo "1) Avvia TUTTI gli agenti"
echo "2) Avvia agente backend-api"
echo "3) Avvia agente database"
echo "4) Avvia agente frontend-ui"
echo "5) Avvia agente testing"
echo "6) Avvia agente supervisor"
echo "7) Mostra sessioni attive"
echo "8) Visualizza contesto condiviso"
echo ""
read -p "Scelta (1-8): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Avvio di tutti gli agenti..."
        start_agent "backend-api"
        sleep 2
        start_agent "database"
        sleep 2
        start_agent "frontend-ui"
        sleep 2
        start_agent "testing"
        sleep 2
        start_agent "supervisor"
        echo ""
        echo "✨ Tutti gli agenti sono attivi!"
        ;;

    2) start_agent "backend-api" ;;
    3) start_agent "database" ;;
    4) start_agent "frontend-ui" ;;
    5) start_agent "testing" ;;
    6) start_agent "supervisor" ;;

    7)
        echo ""
        echo "📊 Sessioni TMUX attive:"
        tmux list-sessions | grep claude || echo "Nessuna sessione Claude attiva"
        ;;

    8)
        echo ""
        echo "📄 Contesto condiviso (ultimi 20 eventi):"
        if [ -f "/tmp/mcp_shared_context.log" ]; then
            tail -20 /tmp/mcp_shared_context.log
        else
            echo "File di log non trovato. MCP server potrebbe non essere attivo."
        fi
        ;;

    *)
        echo "❌ Scelta non valida"
        exit 1
        ;;
esac

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📝 COMANDI UTILI:"
echo ""
echo "Connetti a un agente:"
echo "  tmux attach -t claude-backend-api"
echo ""
echo "Visualizza contesto condiviso:"
echo "  tail -f /tmp/mcp_shared_context.log"
echo ""
echo "Lista sessioni:"
echo "  tmux list-sessions | grep claude"
echo ""
echo "Esci da TMUX:"
echo "  Ctrl+B poi D"
echo ""
echo "════════════════════════════════════════════════════════════════"

# Se sono stati avviati agenti, mostra esempio di workflow
if [[ $choice -ge 1 && $choice -le 6 ]]; then
    echo ""
    echo "💡 ESEMPIO DI COORDINAMENTO:"
    echo ""
    echo "1. Backend agent:"
    echo "   'I'll use the log_activity tool: Creating /api/users endpoint'"
    echo ""
    echo "2. Database agent:"
    echo "   'Let me check conflicts first with check_conflicts tool'"
    echo "   'I'll use log_activity: Creating users table'"
    echo ""
    echo "3. Frontend agent:"
    echo "   'I'll use get_agent_status to see what others are doing'"
    echo "   'Now I'll create the user form to match the API'"
    echo ""
fi