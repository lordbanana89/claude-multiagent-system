#!/bin/bash

# 🔄 Clean and Restart TMUX Sessions
# Pulisce le sessioni duplicate e riavvia quelle essenziali

set -e

echo "🔄 Cleaning and Restarting TMUX Sessions"
echo "=========================================="

# Colori
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Lista sessioni da rimuovere (duplicati e obsolete)
OLD_SESSIONS=(
    "claude-supervisor-agent"
    "claude-backend-api-agent"
    "claude-database-agent"
    "claude-instagram-agent"
    "claude-test-agent"
    "claude-demo-backend"
    "claude-demo-database"
    "mcp-server"
    "claude-shared-context"
)

# Lista sessioni core da mantenere/creare
CORE_SESSIONS=(
    "claude-supervisor"
    "claude-master"
    "claude-backend-api"
    "claude-database"
    "claude-frontend-ui"
    "claude-testing"
)

echo -e "${YELLOW}Step 1: Rimozione sessioni duplicate/obsolete${NC}"
for session in "${OLD_SESSIONS[@]}"; do
    if tmux has-session -t "$session" 2>/dev/null; then
        tmux kill-session -t "$session"
        echo -e "  ${RED}✗${NC} Rimossa: $session"
    fi
done

echo -e "\n${YELLOW}Step 2: Verifica sessioni core${NC}"
for session in "${CORE_SESSIONS[@]}"; do
    if tmux has-session -t "$session" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} Esistente: $session"
    else
        # Crea nuova sessione con messaggio di benvenuto
        tmux new-session -d -s "$session"

        # Invia messaggio iniziale basato sul tipo di agent
        case "$session" in
            "claude-supervisor")
                tmux send-keys -t "$session" "echo '👨‍💼 Supervisor Agent Ready'" Enter
                tmux send-keys -t "$session" "echo 'Waiting for tasks to coordinate...'" Enter
                ;;
            "claude-master")
                tmux send-keys -t "$session" "echo '🎖️ Master Agent Ready'" Enter
                tmux send-keys -t "$session" "echo 'Strategic command center online...'" Enter
                ;;
            "claude-backend-api")
                tmux send-keys -t "$session" "echo '🔧 Backend API Agent Ready'" Enter
                tmux send-keys -t "$session" "echo 'Ready to handle API development tasks...'" Enter
                ;;
            "claude-database")
                tmux send-keys -t "$session" "echo '🗄️ Database Agent Ready'" Enter
                tmux send-keys -t "$session" "echo 'Database management system online...'" Enter
                ;;
            "claude-frontend-ui")
                tmux send-keys -t "$session" "echo '🎨 Frontend UI Agent Ready'" Enter
                tmux send-keys -t "$session" "echo 'UI/UX development environment ready...'" Enter
                ;;
            "claude-testing")
                tmux send-keys -t "$session" "echo '🧪 Testing Agent Ready'" Enter
                tmux send-keys -t "$session" "echo 'QA and testing framework initialized...'" Enter
                ;;
        esac

        echo -e "  ${GREEN}+${NC} Creata: $session"
    fi
done

# Opzionale: crea sessioni aggiuntive se necessario
echo -e "\n${YELLOW}Step 3: Sessioni opzionali${NC}"

OPTIONAL_SESSIONS=(
    "claude-instagram"
    "claude-queue-manager"
    "claude-deployment"
)

read -p "Vuoi creare le sessioni opzionali? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    for session in "${OPTIONAL_SESSIONS[@]}"; do
        if ! tmux has-session -t "$session" 2>/dev/null; then
            tmux new-session -d -s "$session"

            case "$session" in
                "claude-instagram")
                    tmux send-keys -t "$session" "echo '📱 Instagram Agent Ready'" Enter
                    ;;
                "claude-queue-manager")
                    tmux send-keys -t "$session" "echo '📬 Queue Manager Agent Ready'" Enter
                    ;;
                "claude-deployment")
                    tmux send-keys -t "$session" "echo '🚀 Deployment Agent Ready'" Enter
                    ;;
            esac

            echo -e "  ${GREEN}+${NC} Creata: $session"
        fi
    done
fi

echo -e "\n${YELLOW}Step 4: Status finale${NC}"
echo "Sessioni TMUX attive:"
tmux ls 2>/dev/null | while read line; do
    session_name=$(echo "$line" | cut -d':' -f1)

    # Colora in base al tipo
    if [[ " ${CORE_SESSIONS[@]} " =~ " ${session_name} " ]]; then
        echo -e "  ${GREEN}●${NC} $session_name (core)"
    elif [[ " ${OPTIONAL_SESSIONS[@]} " =~ " ${session_name} " ]]; then
        echo -e "  ${YELLOW}●${NC} $session_name (optional)"
    else
        echo -e "  ${RED}●${NC} $session_name (other)"
    fi
done

echo -e "\n${GREEN}=========================================="
echo -e "✅ TMUX Sessions Reorganized Successfully!"
echo -e "==========================================${NC}"
echo
echo "Comandi utili:"
echo "  • Lista sessioni: tmux ls"
echo "  • Attach a sessione: tmux attach -t claude-supervisor"
echo "  • Monitor tutte: watch 'tmux ls'"
echo "  • Test sistema: python3 tests/test_system_health.py"