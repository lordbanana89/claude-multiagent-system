#!/bin/bash

echo "🛑 Stopping Claude Multi-Agent System..."

# Kill processes from PID file
if [ -f ".system_pids" ]; then
    while read pid; do
        if ps -p $pid > /dev/null 2>&1; then
            kill -9 $pid 2>/dev/null
            echo "Stopped process: $pid"
        fi
    done < .system_pids
    rm -f .system_pids
fi

# Kill processes on known ports
ports=(5001 5173 8000 8888)
for port in "${ports[@]}"; do
    pid=$(lsof -ti :$port)
    if [ ! -z "$pid" ]; then
        kill -9 $pid 2>/dev/null
        echo "Stopped service on port $port"
    fi
done

# Kill TMUX sessions
tmux kill-server 2>/dev/null

echo "✅ All services stopped"
