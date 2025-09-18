#!/bin/bash
# Start the fully integrated Claude Multi-Agent System

echo "🚀 Starting Claude Multi-Agent System - Integrated Mode"
echo "======================================================="

# Check dependencies
echo "Checking dependencies..."
command -v redis-server >/dev/null 2>&1 || { echo "❌ Redis not found. Please install redis."; exit 1; }
command -v tmux >/dev/null 2>&1 || { echo "❌ TMUX not found. Please install tmux."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 not found. Please install python3."; exit 1; }

# Set project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"

# Create necessary directories
mkdir -p logs
mkdir -p .auth

# Start Redis if not running
if ! pgrep -x redis-server > /dev/null; then
    echo "Starting Redis server..."
    redis-server --daemonize yes --port 6379
    sleep 2
fi

# Kill existing TMUX sessions
echo "Cleaning up existing TMUX sessions..."
for session in claude-supervisor claude-master claude-backend-api claude-database claude-frontend-ui claude-testing claude-instagram claude-queue-manager claude-deployment; do
    tmux kill-session -t $session 2>/dev/null
done

# Create TMUX sessions for agents
echo "Creating TMUX sessions for agents..."
for session in claude-supervisor claude-master claude-backend-api claude-database claude-frontend-ui claude-testing claude-instagram claude-queue-manager claude-deployment; do
    tmux new-session -d -s $session
    tmux send-keys -t $session "echo 'Agent session $session initialized'" Enter
    echo "  ✓ Created session: $session"
done

# Start Dramatiq workers
echo "Starting Dramatiq workers..."
tmux new-session -d -s dramatiq-worker
tmux send-keys -t dramatiq-worker "cd $PROJECT_ROOT && python3 -m dramatiq task_queue.actors --processes 2 --threads 4" Enter
echo "  ✓ Dramatiq workers started"

# Start Message Bus and Agent Bridges
echo "Starting integration services..."
tmux new-session -d -s integration-services
tmux send-keys -t integration-services "cd $PROJECT_ROOT && python3 -c '
import sys
import time
import logging
sys.path.insert(0, \".\")

logging.basicConfig(level=logging.INFO)

from core.message_bus import get_message_bus
from agents.agent_bridge import get_bridge_manager

# Start message bus
message_bus = get_message_bus()
message_bus.start()
print(\"✓ Message bus started\")

# Start agent bridges
bridge_manager = get_bridge_manager()
bridge_manager.start_all()
print(f\"✓ Started {len(bridge_manager.bridges)} agent bridges\")

# Keep running
print(\"Integration services running... Press Ctrl+C to stop\")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print(\"Shutting down...\")
    bridge_manager.stop_all()
    message_bus.stop()
'" Enter
echo "  ✓ Integration services started"

# Start API Gateway
echo "Starting API Gateway..."
tmux new-session -d -s api-gateway
tmux send-keys -t api-gateway "cd $PROJECT_ROOT && python3 -m uvicorn api.unified_gateway:app --host 0.0.0.0 --port 8000 --reload" Enter
echo "  ✓ API Gateway started on http://localhost:8000"

# Start Streamlit monitoring interface
echo "Starting Monitoring Interface..."
tmux new-session -d -s monitoring
tmux send-keys -t monitoring "cd $PROJECT_ROOT && streamlit run interfaces/web/complete_integration.py --server.port 8501" Enter
echo "  ✓ Monitoring interface started on http://localhost:8501"

# Wait for services to initialize
echo "Waiting for services to initialize..."
sleep 5

# Run system check
echo ""
echo "Running system check..."
python3 -c "
import sys
import requests
import time
sys.path.insert(0, '.')

# Check API Gateway
try:
    response = requests.get('http://localhost:8000/health', timeout=5)
    if response.status_code == 200:
        print('✓ API Gateway: Online')
    else:
        print('⚠️  API Gateway: Not ready')
except:
    print('❌ API Gateway: Offline')

# Check Redis
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print('✓ Redis: Connected')
except:
    print('❌ Redis: Not connected')

# Check TMUX sessions
import subprocess
result = subprocess.run(['tmux', 'ls'], capture_output=True, text=True)
sessions = len(result.stdout.strip().split('\\n')) if result.returncode == 0 else 0
print(f'✓ TMUX Sessions: {sessions} active')
"

echo ""
echo "============================================"
echo "🎉 Claude Multi-Agent System is running!"
echo "============================================"
echo ""
echo "Access points:"
echo "  • API Gateway:    http://localhost:8000"
echo "  • API Docs:       http://localhost:8000/docs"
echo "  • Monitoring UI:  http://localhost:8501"
echo ""
echo "Useful commands:"
echo "  • View logs:        tmux attach -t integration-services"
echo "  • View API logs:    tmux attach -t api-gateway"
echo "  • List sessions:    tmux ls"
echo "  • Run tests:        python3 scripts/test_integration.py"
echo "  • Stop system:      ./scripts/stop_integrated_system.sh"
echo ""
echo "To test the system:"
echo "  curl -X GET http://localhost:8000/health"
echo "  python3 scripts/test_integration.py"
echo ""