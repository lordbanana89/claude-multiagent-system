#!/bin/bash
# Start all agent responders in background

AGENTS=("master" "backend-api" "database" "frontend-ui" "testing" "instagram" "queue-manager" "deployment")

echo "=== STARTING ALL AGENT RESPONDERS ==="

for agent in "${AGENTS[@]}"; do
    echo "Starting $agent..."
    python3 /Users/erik/Desktop/claude-multiagent-system/agent_responder.py "$agent" > "/tmp/${agent}.log" 2>&1 &
    echo "  PID: $!"
    sleep 0.5
done

echo ""
echo "All agents started. Logs in /tmp/<agent-name>.log"
echo "Use 'ps aux | grep agent_responder' to see running agents"
echo "Use 'pkill -f agent_responder' to stop all agents"