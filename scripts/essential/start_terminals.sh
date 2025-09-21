#!/bin/bash
# Start TTY terminals for all agents

echo "🖥️  Starting TTY terminals for agents..."

# Check if ttyd is installed
if ! command -v ttyd &> /dev/null; then
    echo "❌ ttyd not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ttyd
    else
        echo "Please install ttyd manually: https://github.com/tsl0922/ttyd"
        exit 1
    fi
fi

# Start ttyd for each agent with direct port assignment
echo "Starting Supervisor on port 8095..."
ttyd -p 8095 --writable tmux attach-session -t claude-supervisor > /dev/null 2>&1 &

echo "Starting Master on port 8096..."
ttyd -p 8096 --writable tmux attach-session -t claude-master > /dev/null 2>&1 &

echo "Starting Backend API on port 8090..."
ttyd -p 8090 --writable tmux attach-session -t claude-backend-api > /dev/null 2>&1 &

echo "Starting Database on port 8091..."
ttyd -p 8091 --writable tmux attach-session -t claude-database > /dev/null 2>&1 &

echo "Starting Frontend UI on port 8092..."
ttyd -p 8092 --writable tmux attach-session -t claude-frontend-ui > /dev/null 2>&1 &

echo "Starting Testing on port 8093..."
ttyd -p 8093 --writable tmux attach-session -t claude-testing > /dev/null 2>&1 &

echo "Starting Instagram on port 8094..."
ttyd -p 8094 --writable tmux attach-session -t claude-instagram > /dev/null 2>&1 &

echo "Starting Queue Manager on port 8097..."
ttyd -p 8097 --writable tmux attach-session -t claude-queue-manager > /dev/null 2>&1 &

echo "Starting Deployment on port 8098..."
ttyd -p 8098 --writable tmux attach-session -t claude-deployment > /dev/null 2>&1 &

sleep 2

echo ""
echo "✅ All terminals started!"
echo ""
echo "Terminal URLs:"
echo "  Supervisor: http://localhost:8095"
echo "  Master: http://localhost:8096"
echo "  Backend API: http://localhost:8090"
echo "  Database: http://localhost:8091"
echo "  Frontend UI: http://localhost:8092"
echo "  Testing: http://localhost:8093"
echo "  Instagram: http://localhost:8094"
echo "  Queue Manager: http://localhost:8097"
echo "  Deployment: http://localhost:8098"