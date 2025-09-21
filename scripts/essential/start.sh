#!/bin/bash
# Unified Start Script for Claude Multi-Agent System

set -e

echo "🚀 Starting Claude Multi-Agent System"
echo "======================================"

# Start Redis if not running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Starting Redis..."
    redis-server --daemonize yes
fi

# Start MCP Server
echo "Starting MCP Server..."
python3 mcp_server_complete.py &
MCP_PID=$!
echo "✅ MCP Server started (PID: $MCP_PID)"

# Start API Gateway (CRITICAL for frontend!)
echo "Starting API Gateway on port 5001..."
python3 routes_api.py &
API_PID=$!
echo "✅ API Gateway started (PID: $API_PID)"

# Start Health API
echo "Starting Health API on port 5002..."
python3 health_api.py &
HEALTH_PID=$!
echo "✅ Health API started (PID: $HEALTH_PID)"

# Start Auth API
echo "Starting Auth API on port 5003..."
python3 auth_api.py &
AUTH_PID=$!
echo "✅ Auth API started (PID: $AUTH_PID)"

# Start Frontend
if [ -d "claude-ui" ]; then
    echo "Starting Frontend..."
    cd claude-ui && npm run dev &
    FRONTEND_PID=$!
    cd ..
    echo "✅ Frontend started (PID: $FRONTEND_PID)"
fi

# Initialize TMUX agents
echo "Initializing agents..."
for agent in supervisor master backend-api database frontend-ui testing queue-manager instagram deployment; do
    tmux new-session -d -s "claude-$agent" 2>/dev/null || echo "Session claude-$agent already exists"
done

# Start terminal services
echo "Starting terminal services..."
./scripts/essential/start_terminals.sh

# Start MCP Server
echo "Starting MCP Server..."
python3 mcp_server_complete.py > /tmp/mcp_server.log 2>&1 &
MCP_SERVER_PID=$!
echo "✅ MCP Server started (PID: $MCP_SERVER_PID)"

echo ""
echo "✅ All services started!"
echo ""
echo "Access points:"
echo "  📊 Dashboard: http://localhost:5173"
echo "  🔌 Main API: http://localhost:5001"
echo "  ❤️ Health API: http://localhost:5002"
echo "  🔐 Auth API: http://localhost:5003"
echo "  🤖 MCP Server: http://localhost:9999"
echo ""
echo "Run './scripts/essential/status.sh' to check system status"