#!/bin/bash
# Stop the fully integrated Claude Multi-Agent System

echo "🛑 Stopping Claude Multi-Agent System"
echo "====================================="

# Kill TMUX sessions
echo "Stopping TMUX sessions..."
for session in claude-supervisor claude-master claude-backend-api claude-database claude-frontend-ui claude-testing claude-instagram claude-queue-manager claude-deployment dramatiq-worker integration-services api-gateway monitoring; do
    tmux kill-session -t $session 2>/dev/null && echo "  ✓ Stopped: $session"
done

# Stop Redis if we started it
echo "Checking Redis..."
if pgrep -x redis-server > /dev/null; then
    echo "  Stopping Redis server..."
    redis-cli shutdown 2>/dev/null
    echo "  ✓ Redis stopped"
fi

echo ""
echo "✓ All services stopped"
echo ""