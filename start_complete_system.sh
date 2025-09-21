#!/bin/bash

# Claude Multi-Agent System - Complete Startup Script
# This script starts all components of the system in the correct order

echo "🚀 Starting Claude Multi-Agent System..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a port is in use
check_port() {
    lsof -i :$1 > /dev/null 2>&1
    return $?
}

# Function to kill process on port
kill_port() {
    local port=$1
    local pid=$(lsof -ti :$port)
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}Killing process on port $port (PID: $pid)${NC}"
        kill -9 $pid 2>/dev/null
        sleep 1
    fi
}

# Function to start a service
start_service() {
    local name=$1
    local command=$2
    local port=$3
    local log_file=$4

    echo -e "${YELLOW}Starting $name on port $port...${NC}"

    # Check if port is already in use
    if check_port $port; then
        echo -e "${RED}Port $port is already in use. Cleaning up...${NC}"
        kill_port $port
    fi

    # Start the service
    nohup $command > $log_file 2>&1 &
    local pid=$!

    # Wait for service to start
    sleep 2

    # Check if service started successfully
    if check_port $port; then
        echo -e "${GREEN}✅ $name started successfully (PID: $pid)${NC}"
        echo $pid >> .system_pids
        return 0
    else
        echo -e "${RED}❌ Failed to start $name${NC}"
        return 1
    fi
}

# Clean up old PIDs file
rm -f .system_pids

# Create log directory
mkdir -p logs

echo ""
echo "🔧 Step 1: Starting Database Services"
echo "--------------------------------------"

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${YELLOW}Starting Redis...${NC}"
    redis-server --daemonize yes
    sleep 1
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis started${NC}"
    else
        echo -e "${RED}❌ Failed to start Redis${NC}"
    fi
else
    echo -e "${GREEN}✅ Redis is already running${NC}"
fi

echo ""
echo "🔧 Step 2: Starting Backend APIs"
echo "--------------------------------------"

# Start Main Routes API (port 5001)
start_service "Routes API" "python3 routes_api.py" 5001 "logs/routes_api.log"

# Start FastAPI Gateway (port 8888)
cd api && start_service "FastAPI Gateway" "python3 -m uvicorn main:app --host 0.0.0.0 --port 8888" 8888 "../logs/fastapi_gateway.log" && cd ..

# Start Integration Orchestrator (port 5002) - CRITICAL FOR INTEGRATION
start_service "Integration Orchestrator" "python3 integration_orchestrator.py" 5002 "logs/integration.log"

# Start Unified Gateway (port 8000) if exists
if [ -f "api/unified_gateway.py" ]; then
    cd api && start_service "Unified Gateway" "python3 -m uvicorn unified_gateway:app --host 0.0.0.0 --port 8000" 8000 "../logs/unified_gateway.log" && cd ..
fi

echo ""
echo "🔧 Step 3: Starting Agent TMUX Sessions"
echo "--------------------------------------"

# Create TMUX sessions for agents
agents=("supervisor" "master" "backend-api" "database" "frontend-ui" "testing" "instagram" "queue-manager" "deployment")

for agent in "${agents[@]}"; do
    session_name="claude-$agent"

    # Check if session exists
    if tmux has-session -t $session_name 2>/dev/null; then
        echo -e "${YELLOW}TMUX session $session_name already exists${NC}"
    else
        tmux new-session -d -s $session_name
        tmux send-keys -t $session_name "echo 'Agent $agent terminal ready'" Enter
        echo -e "${GREEN}✅ Created TMUX session: $session_name${NC}"
    fi
done

echo ""
echo "🔧 Step 4: Starting Frontend"
echo "--------------------------------------"

# Start Frontend Dev Server
cd claude-ui
if [ -f "package.json" ]; then
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing frontend dependencies...${NC}"
        npm install
    fi

    # Start the dev server
    start_service "Frontend UI" "npm run dev" 5173 "../logs/frontend.log"
else
    echo -e "${RED}Frontend directory not found${NC}"
fi
cd ..

echo ""
echo "🔧 Step 5: System Status Check"
echo "--------------------------------------"

# Function to check service status
check_service() {
    local name=$1
    local port=$2
    local url=$3

    if check_port $port; then
        # Try to make HTTP request if URL provided
        if [ ! -z "$url" ]; then
            if curl -s -o /dev/null -w "%{http_code}" $url | grep -q "200\|404"; then
                echo -e "${GREEN}✅ $name: Running on port $port${NC}"
                return 0
            else
                echo -e "${YELLOW}⚠️  $name: Port $port active but not responding to HTTP${NC}"
                return 1
            fi
        else
            echo -e "${GREEN}✅ $name: Port $port active${NC}"
            return 0
        fi
    else
        echo -e "${RED}❌ $name: Not running on port $port${NC}"
        return 1
    fi
}

# Check all services
echo ""
check_service "Routes API" 5001 "http://localhost:5001/api/health"
check_service "FastAPI Gateway" 8888 "http://localhost:8888/api/health"
check_service "Unified Gateway" 8000 "http://localhost:8000/health"
check_service "Frontend UI" 5173 "http://localhost:5173"
check_service "Redis" 6379

# Count active TMUX sessions
active_sessions=$(tmux list-sessions 2>/dev/null | grep "^claude-" | wc -l)
echo -e "${GREEN}✅ Active Agent Sessions: $active_sessions/9${NC}"

echo ""
echo "=================================="
echo -e "${GREEN}🎉 System Startup Complete!${NC}"
echo ""
echo "📋 Access Points:"
echo "   • Frontend UI: http://localhost:5173"
echo "   • Routes API: http://localhost:5001"
echo "   • FastAPI Gateway: http://localhost:8888"
echo "   • API Documentation: http://localhost:8888/docs"
echo ""
echo "📝 Logs are available in the 'logs' directory"
echo ""
echo "🛑 To stop all services, run: ./stop_system.sh"
echo ""

# Create stop script if it doesn't exist
if [ ! -f "stop_system.sh" ]; then
    cat > stop_system.sh << 'EOF'
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
EOF
    chmod +x stop_system.sh
    echo "Created stop_system.sh script"
fi