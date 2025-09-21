# Quickstart Guide

## Prerequisites

### System Requirements
- macOS or Linux (Ubuntu 20.04+)
- Python 3.11+
- Node.js 18+
- 8GB RAM minimum
- 10GB free disk space

### Required Software

```bash
# macOS
brew install tmux redis overmind sqlite3

# Ubuntu/Debian
sudo apt-get install tmux redis-server sqlite3
# Install Overmind from: https://github.com/DarthSim/overmind/releases
```

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd claude-multiagent-system
```

### 2. Python Environment Setup

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd claude-ui
npm install
npm run build
cd ..
```

### 4. Initialize Databases

```bash
# Create necessary databases
sqlite3 mcp_system.db < scripts/init_mcp_db.sql
sqlite3 shared_inbox.db < scripts/init_inbox_db.sql
sqlite3 auth.db < scripts/init_auth_db.sql
```

## Starting the System

### Option 1: Overmind (Recommended)

```bash
# Start all services with Overmind
overmind start

# Check status
overmind connect
```

### Option 2: Manual Start

```bash
# Start Redis
redis-server &

# Start MCP Server
python mcp_server_v2_secure.py &

# Start API Gateway
python routes_api.py &

# Start Frontend
cd claude-ui && npm run dev &

# Initialize agents
./scripts/init_all_agents.sh
```

## Verify Installation

### 1. Check Services

```bash
# Check TMUX sessions
tmux ls

# Expected output:
# claude-supervisor: 1 windows
# claude-master: 1 windows
# claude-backend-api: 1 windows
# ... (all 9 agents)
```

### 2. Access Dashboard

Open your browser and navigate to:
- **React Dashboard**: http://localhost:5173
- **API Health Check**: http://localhost:5001/health
- **MCP Server**: http://localhost:9999/status

### 3. Test Agent Communication

```bash
# Send test message to an agent
curl -X POST http://localhost:5001/api/mcp/agents/supervisor/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Status report"}'
```

## Quick Commands

```bash
# View agent logs
tmux attach -t claude-supervisor

# Check system status
sqlite3 mcp_system.db "SELECT name, status FROM agents;"

# Stop all services
overmind stop

# Restart specific agent
tmux kill-session -t claude-backend-api
tmux new-session -d -s claude-backend-api
```

## Common Issues

### Port Already in Use

```bash
# Find and kill process on port
lsof -i :5001
kill -9 <PID>
```

### TMUX Session Already Exists

```bash
# Kill existing session
tmux kill-session -t <session-name>
```

### Database Lock Error

```bash
# Reset database locks
rm *.db-shm *.db-wal
```

## Next Steps

- [Configure Agents](../agents/) - Customize agent behavior
- [API Reference](../api/reference.md) - Explore available endpoints
- [Workflows Guide](../workflows/common-tasks.md) - Learn common workflows
- [Troubleshooting](../workflows/troubleshooting.md) - Detailed problem resolution