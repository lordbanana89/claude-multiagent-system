#!/bin/bash

PROJECT_DIR="/Users/erik/Desktop/claude-multiagent-system"

echo "🎮 Claude Multi-Agent System Control Panel"
echo "=========================================="
echo ""
echo "1) Start MCP Server"
echo "2) Start all agents"
echo "3) Start specific agent"
echo "4) Stop all agents"
echo "5) Stop MCP Server"
echo "6) Monitor system"
echo "7) View shared context log"
echo "8) Reset system"
echo "9) Exit"
echo ""

read -p "Choice: " choice

case $choice in
    1)
        tmux new-session -d -s mcp-server "$PROJECT_DIR/start_mcp_server.sh"
        echo "✅ MCP Server started"
        ;;
    2)
        "$PROJECT_DIR/start_all_agents.sh"
        ;;
    3)
        echo "Enter agent name (backend-api, database, frontend-ui, testing, supervisor):"
        read agent_name
        "$PROJECT_DIR/start_agent.sh" "$agent_name"
        ;;
    4)
        tmux list-sessions | grep claude- | cut -d: -f1 | xargs -I {} tmux kill-session -t {}
        echo "✅ All agents stopped"
        ;;
    5)
        tmux kill-session -t mcp-server 2>/dev/null
        pkill -f "mcp_server_complete.py"
        echo "✅ MCP Server stopped"
        ;;
    6)
        "$PROJECT_DIR/monitor_system.sh"
        ;;
    7)
        tail -f /tmp/mcp_shared_context.log
        ;;
    8)
        echo "⚠️  This will reset all data. Continue? (y/n)"
        read confirm
        if [ "$confirm" = "y" ]; then
            rm -f /tmp/mcp_state.db /tmp/mcp_shared_context.log
            echo "✅ System reset"
        fi
        ;;
    9)
        exit 0
        ;;
esac
