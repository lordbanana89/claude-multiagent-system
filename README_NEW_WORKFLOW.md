# Claude Multi-Agent System - Quick Start Guide

## Prerequisites

### Required Software
```bash
# macOS (Homebrew)
brew install tmux redis overmind

# Linux
sudo apt-get install tmux redis-server
# Install Overmind from releases: https://github.com/DarthSim/overmind/releases

# Python dependencies
pip install -r requirements.txt
```

> **Python version**: Use Python 3.11 for both local development and CI parity.

## Quick Start

### 1. Initialize the System
```bash
# Clone repository
git clone <repository-url>
cd claude-multiagent-system

# Install Python dependencies
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Verify configuration
python tests/test_phase0.py
```

### 2. Start the System with Overmind
```bash
# Start all services (uses Procfile.tmux by default)
overmind start

# Or start specific services
overmind start -l supervisor,redis,web

# Check status
overmind ps
```

### 3. Access Components

#### Web Interface
```bash
# Open in browser
open http://localhost:8501

# Features:
# - Agent status monitoring
# - Task queue management
# - Real-time logs
# - System health checks
```

#### Agent TMUX Sessions
```bash
# List all sessions
tmux ls

# Attach to specific agent
tmux attach -t claude-supervisor
tmux attach -t claude-backend-api

# Or use Overmind
overmind connect supervisor
```

#### Queue Management
```bash
# Send task to agent
python -c "
from task_queue import QueueClient
client = QueueClient()
client.send_command('backend-api', 'echo Hello from queue')
"

# Check queue stats
python -c "
from task_queue import QueueClient
client = QueueClient()
print(client.get_stats())
"
```

## Architecture Overview

### Core Components

1. **TMUX Sessions** (`claude-*`)
   - Each agent runs in isolated TMUX session
   - Managed by Overmind via Procfile.tmux
   - Sessions persist across restarts

2. **Overmind Process Manager**
   - Manages all system processes
   - Configuration: `.overmind.env`
   - Default Procfile: `Procfile.tmux`

3. **Redis + Dramatiq Queue**
   - High-performance message queue
   - 8,000+ messages/second throughput
   - Automatic retry with exponential backoff

4. **Central Configuration** (`config/settings.py`)
   - All paths relative to PROJECT_ROOT
   - Agent session mapping
   - Feature flags

### Agent Types

| Agent | Session Name | Role |
|-------|-------------|------|
| supervisor | claude-supervisor | Task coordination |
| master | claude-master | Crisis management |
| backend-api | claude-backend-api | Backend development |
| database | claude-database | Database management |
| frontend-ui | claude-frontend-ui | Frontend development |
| testing | claude-testing | Testing & QA |
| instagram | claude-instagram | Social integration |
| queue-manager | claude-queue-manager | Queue management |
| deployment | claude-deployment | DevOps |

## Common Operations

### Start/Stop Services
```bash
# Start all
overmind start

# Stop all
overmind kill

# Restart specific service
overmind restart web
overmind restart dramatiq
```

### Send Tasks to Agents
```python
from core.claude_orchestrator import ClaudeNativeOrchestrator

orchestrator = ClaudeNativeOrchestrator()

# Send task to specific agent
orchestrator.send_task_to_claude(
    "backend-api",
    "Create user authentication API",
    "Context: REST API with JWT tokens"
)

# Monitor progress
progress = orchestrator.monitor_agent_progress()
print(progress)
```

### Run Tests
```bash
# Phase 0 - Configuration
python tests/test_phase0.py

# Dramatiq queue
python tests/test_dramatiq.py

# Full system
python tests/final_system_test.py
```

## Troubleshooting

### Common Issues

#### TMUX Sessions Not Created
```bash
# Manually create sessions
tmux new-session -d -s claude-supervisor
tmux new-session -d -s claude-backend-api
# ... etc

# Or use startup script
./scripts/start_complete_system.sh
```

#### Redis Connection Failed
```bash
# Check Redis
redis-cli ping

# Start Redis manually
redis-server

# Or with Docker
docker run -d -p 6379:6379 redis:7.2
```

#### Overmind Socket Error
```bash
# Clean socket
rm -f .overmind.sock

# Restart Overmind
overmind kill
overmind start
```

### Logs and Monitoring
```bash
# View all logs
tail -f logs/*.log

# Overmind logs
overmind echo

# Redis monitor
redis-cli monitor

# System health check
python -c "
from monitoring.health import check_system_health
import json
print(json.dumps(check_system_health(), indent=2))
"
```

## Development Workflow

### 1. Planning Phase
```python
# Use orchestrator for task distribution
from core.claude_orchestrator import ClaudeNativeOrchestrator

orchestrator = ClaudeNativeOrchestrator()
result = orchestrator.intelligent_task_distribution(
    "Create user profile system with social integration"
)
```

### 2. Implementation
- Agents receive tasks via TMUX sessions
- Queue system handles async communication
- Web interface for monitoring

### 3. Testing
```bash
# Run test suite
pytest tests/

# Integration tests
python tests/test_integration.py
```

### 4. Deployment
```bash
# Production with Docker
docker-compose up -d

# Or with systemd
sudo systemctl start claude-multiagent
```

## Configuration

### Environment Variables (.overmind.env)
```bash
# Core settings
PROJECT_ROOT=/Users/erik/Desktop/claude-multiagent-system
REDIS_URL=redis://localhost:6379/0

# Feature flags
FEATURE_DRAMATIQ=true
FEATURE_OVERMIND=true

# Default Procfile
OVERMIND_PROCFILE=Procfile.tmux
```

### Agent Instructions
- Located in `instructions/` directory
- One file per agent (e.g., `backend-api.md`)
- Auto-loaded on agent startup

## Advanced Usage

### Custom Task Chains
```python
from task_queue import QueueClient

client = QueueClient()
chain_id = client.create_task_chain([
    {
        "agent_id": "backend-api",
        "command": "python migrate.py",
        "description": "Run migrations",
        "delay": 5
    },
    {
        "agent_id": "testing",
        "command": "pytest tests/",
        "description": "Run tests",
        "delay": 2
    }
])
```

### Parallel Tasks
```python
msg_ids = client.create_parallel_tasks([
    ("backend-api", "Build API"),
    ("frontend-ui", "Build UI"),
    ("database", "Setup database")
])
```

### Health Monitoring
```python
from monitoring.health import HealthChecker

checker = HealthChecker()
health = checker.get_system_health()

if health.status == "unhealthy":
    # Trigger alerts
    pass
```

## Support

- **Documentation**: `docs/` directory
- **Troubleshooting**: `docs/TROUBLESHOOTING.md`
- **API Reference**: `docs/API_REFERENCE.md`
- **Architecture**: `docs/ARCHITECTURE.md`

## License

MIT License - See LICENSE file for details
