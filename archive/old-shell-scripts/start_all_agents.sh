#!/bin/bash

PROJECT_DIR="/Users/erik/Desktop/claude-multiagent-system"

echo "🚀 Starting all Claude agents..."

agents=("backend-api" "database" "frontend-ui" "testing" "supervisor")

for agent in "${agents[@]}"; do
    echo "Starting $agent..."
    "$PROJECT_DIR/start_agent.sh" "$agent"
    sleep 3
done

echo ""
echo "✅ All agents started!"
echo ""
echo "Sessions:"
tmux list-sessions | grep claude-

echo ""
echo "To connect to an agent: tmux attach -t claude-[agent-name]"
