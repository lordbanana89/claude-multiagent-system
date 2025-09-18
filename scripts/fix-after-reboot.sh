#!/bin/bash

# RIONA AI - SOLUZIONE COMPLETA POST-RIAVVIO
# Risolve tutti i problemi dopo il riavvio del Mac

echo "╔═══════════════════════════════════════════════╗"
echo "║    RIONA AI - FIX COMPLETO POST-RIAVVIO      ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

PROJECT_ROOT="/Users/erik/Desktop/riona_ai/riona-ai"
TMUX="/opt/homebrew/bin/tmux"

cd "$PROJECT_ROOT"

echo "🔧 STEP 1: Ripristino permessi di esecuzione..."
chmod +x *.sh 2>/dev/null
chmod +x .riona/agents/scripts/*.sh 2>/dev/null
echo "✅ Permessi ripristinati"
echo ""

echo "🚀 STEP 2: Creazione sessioni tmux..."
agents=("backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")

for agent in "${agents[@]}"; do
    if ! $TMUX has-session -t "$agent" 2>/dev/null; then
        $TMUX new-session -d -s "$agent" -c "$PROJECT_ROOT"
        echo "  ✅ Creata sessione: $agent"
    else
        echo "  ✓ Sessione esistente: $agent"
    fi
done
echo ""

echo "🤖 STEP 3: Inizializzazione agenti..."
for agent in "${agents[@]}"; do
    # Avvia bash
    $TMUX send-keys -t "$agent" 'bash' Enter
    sleep 0.3
    
    # Working directory
    $TMUX send-keys -t "$agent" "cd $PROJECT_ROOT" Enter
    sleep 0.2
    
    # Clear e banner
    $TMUX send-keys -t "$agent" "clear" Enter
    $TMUX send-keys -t "$agent" "echo '🤖 $agent Agent - READY'" Enter
    
    echo "  ✅ $agent inizializzato"
done
echo ""

echo "📊 STEP 4: Verifica sistema..."
./claude-orchestrator.sh status
echo ""

echo "═══════════════════════════════════════════════"
echo "✅ SISTEMA COMPLETAMENTE RIPRISTINATO!"
echo "═══════════════════════════════════════════════"
echo ""
echo "✨ Ora puoi:"
echo "  1. Aprire VS Code"
echo "  2. Aprire un nuovo terminale (Cmd+J)"
echo "  3. Il terminale Orchestrator funzionerà senza errori"
echo ""
echo "📌 Comandi disponibili:"
echo "  ./claude-orchestrator.sh status"
echo "  ./claude-orchestrator.sh broadcast 'comando'"
echo "  ./agent-manager.sh menu"
echo ""
echo "💡 TIP: Salva questo comando per uso futuro:"
echo "  ./fix-after-reboot.sh"
