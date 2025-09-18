#!/bin/bash
# Agent Initializer - Carica automaticamente le istruzioni specifiche per ogni agente

set -euo pipefail

PROJECT_ROOT="/Users/erik/Desktop/riona_ai/riona-ai"
AGENTS_DIR="$PROJECT_ROOT/.riona/agents"
CONFIGS_DIR="$AGENTS_DIR/configs"
INSTRUCTIONS_DIR="$AGENTS_DIR/instructions"

# Colori
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

unset TMUX 2>/dev/null || true
TMUX_BIN="/opt/homebrew/bin/tmux"

# Funzione per generare istruzioni da config JSON
generate_instructions() {
    local agent_name="$1"
    local config_file="$CONFIGS_DIR/$agent_name.json"
    
    if [ ! -f "$config_file" ]; then
        echo -e "${RED}Config not found: $config_file${NC}"
        return 1
    fi
    
    # Estrae informazioni dal JSON
    local role=$(jq -r '.role' "$config_file")
    local description=$(jq -r '.description' "$config_file")
    local project=$(jq -r '.context.project' "$config_file")
    local responsibilities=$(jq -r '.responsibilities[]' "$config_file" | sed 's/^/- /')
    local expertise=$(jq -r '.expertise[]' "$config_file" | sed 's/^/- /')
    
    # Genera istruzioni complete
    cat > "$INSTRUCTIONS_DIR/$agent_name.md" <<EOF
# ${role} Agent Instructions

## Role & Identity
You are the **${role}** for the ${project}.

## Description
${description}

## Your Responsibilities
${responsibilities}

## Your Expertise Areas
${expertise}

## Project Context
- **Project**: ${project}
$(jq -r '.context | to_entries[] | "- **\(.key | gsub("_"; " ") | ascii_upcase)**: \(.value)"' "$config_file")

## Working Environment
- **Working Directory**: $(jq -r '.working_directory' "$config_file")
- **Agent Name**: $agent_name
- **Auto-load**: $(jq -r '.auto_load' "$config_file")

## Instructions for Operation
1. **Stay in Character**: Always respond as the ${role}
2. **Focus on Expertise**: Prioritize tasks within your domain
3. **Collaboration**: Work with other agents when needed
4. **Quality**: Maintain high standards in your specialized area
5. **Context Awareness**: Remember you're part of a multi-agent system

## Initialization Commands
$(jq -r '.initialization_commands[]' "$config_file" | sed 's/^/- /')

---
*Generated automatically from config: $config_file*
*Last updated: $(date)*
EOF
}

# Funzione per inviare istruzioni a un agente
send_instructions_to_agent() {
    local agent_name="$1"
    local instructions_file="$INSTRUCTIONS_DIR/$agent_name.md"
    
    if [ ! -f "$instructions_file" ]; then
        echo -e "${RED}Instructions not found: $instructions_file${NC}"
        return 1
    fi
    
    # Verifica se la sessione /opt/homebrew/bin/tmux esiste
    if ! $TMUX_BIN has-session -t "$agent_name" 2>/dev/null; then
        echo -e "${RED}Agent session not found: $agent_name${NC}"
        return 1
    fi
    
    echo -e "${BLUE}Initializing agent: $agent_name${NC}"
    
    # Invia le istruzioni come prompt (usando printf per gestire caratteri speciali)
    local role=$(jq -r '.role' "$CONFIGS_DIR/$agent_name.json")
    local description=$(jq -r '.description' "$CONFIGS_DIR/$agent_name.json")
    local responsibilities=$(jq -r '.responsibilities | join(", ")' "$CONFIGS_DIR/$agent_name.json")
    local expertise=$(jq -r '.expertise | join(", ")' "$CONFIGS_DIR/$agent_name.json")
    local project=$(jq -r '.context.project' "$CONFIGS_DIR/$agent_name.json")

    local instruction_prompt="You are now the $role agent. $description Your responsibilities include: $responsibilities. Focus on $expertise. Always work within the context of $project."

    # Invia prompt con l'identità specifica usando printf per evitare problemi di parsing
    printf '%s\n' "$instruction_prompt" | $TMUX_BIN load-buffer -
    $TMUX_BIN paste-buffer -t "$agent_name"
    $TMUX_BIN send-keys -t "$agent_name" Enter
    sleep 2
    $TMUX_BIN send-keys -t "$agent_name" Enter
    
    # Esegue i comandi di inizializzazione
    while read -r cmd; do
        if [ -n "$cmd" ]; then
            $TMUX_BIN send-keys -t "$agent_name" "$cmd" Enter
            sleep 1
            $TMUX_BIN send-keys -t "$agent_name" Enter
        fi
    done < <(jq -r '.initialization_commands[]' "$CONFIGS_DIR/$agent_name.json")
    
    echo -e "${GREEN}✅ Agent $agent_name initialized${NC}"
}

# Funzione per inizializzare tutti gli agenti
initialize_all_agents() {
    echo -e "${YELLOW}Initializing all agents with their specific roles...${NC}"
    
    # Crea directory se non esiste
    mkdir -p "$INSTRUCTIONS_DIR"
    
    # Lista degli agenti
    local agents=("backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")
    
    for agent in "${agents[@]}"; do
        echo -e "${BLUE}Processing agent: $agent${NC}"
        
        # Genera istruzioni
        generate_instructions "$agent"
        
        # Invia istruzioni all'agente
        send_instructions_to_agent "$agent"
        
        sleep 3
    done
    
    echo -e "${GREEN}All agents initialized with their specific roles!${NC}"
}

# Funzione per reinizializzare un singolo agente
reinitialize_agent() {
    local agent_name="$1"
    
    if [ ! -f "$CONFIGS_DIR/$agent_name.json" ]; then
        echo -e "${RED}Agent config not found: $agent_name${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}Reinitializing agent: $agent_name${NC}"
    
    generate_instructions "$agent_name"
    send_instructions_to_agent "$agent_name"
    
    echo -e "${GREEN}Agent $agent_name reinitialized!${NC}"
}

# Funzione per verificare lo stato degli agenti
check_agent_status() {
    echo -e "${YELLOW}Checking agent initialization status...${NC}"
    
    local agents=("backend-api" "database" "frontend-ui" "instagram" "queue-manager" "testing" "deployment")
    
    for agent in "${agents[@]}"; do
        if $TMUX_BIN has-session -t "$agent" 2>/dev/null; then
            if [ -f "$INSTRUCTIONS_DIR/$agent.md" ]; then
                echo -e "${GREEN}✅ $agent${NC} - Session active, instructions ready"
            else
                echo -e "${YELLOW}⚠️  $agent${NC} - Session active, instructions missing"
            fi
        else
            echo -e "${RED}❌ $agent${NC} - Session not found"
        fi
    done
}

# Main
case "${1:-}" in
    "init-all")
        initialize_all_agents
        ;;
    "init")
        if [ -z "${2:-}" ]; then
            echo "Usage: $0 init <agent_name>"
            exit 1
        fi
        reinitialize_agent "$2"
        ;;
    "status")
        check_agent_status
        ;;
    "generate")
        if [ -z "${2:-}" ]; then
            echo "Usage: $0 generate <agent_name>"
            exit 1
        fi
        generate_instructions "$2"
        echo -e "${GREEN}Instructions generated for $2${NC}"
        ;;
    *)
        echo "Agent Initializer - Multi-agent instruction management"
        echo ""
        echo "Usage: $0 <command> [args]"
        echo ""
        echo "Commands:"
        echo "  init-all           Initialize all agents with their roles"
        echo "  init <agent>       Initialize specific agent"
        echo "  status            Check agent initialization status"
        echo "  generate <agent>  Generate instructions file for agent"
        echo ""
        echo "Available agents: backend-api, database, frontend-ui, instagram, queue-manager, testing, deployment"
        exit 1
        ;;
esac
