#!/bin/bash

# Fix script per orchestrator

cd /Users/erik/Desktop/riona_ai/riona-ai

# Backup dello script originale
cp claude-orchestrator.sh claude-orchestrator.sh.backup

# Crea file temporaneo con sed
cat claude-orchestrator.sh | \
sed 's/^AGENTS=.*/&\n\n# Percorso corretto di tmux\nTMUX="\/opt\/homebrew\/bin\/tmux"/' | \
sed 's/tmux send-keys/$TMUX send-keys/g' | \
sed 's/tmux capture-pane/$TMUX capture-pane/g' | \
sed 's/tmux has-session/$TMUX has-session/g' > claude-orchestrator-temp.sh

# Sostituisci il file originale
mv claude-orchestrator-temp.sh claude-orchestrator.sh
chmod +x claude-orchestrator.sh

echo "✅ Orchestrator principale aggiornato!"

# Test
./claude-orchestrator.sh status
