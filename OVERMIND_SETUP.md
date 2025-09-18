# 🚀 Overmind Setup Guide for Claude Multi-Agent System

## Overview

Overmind is a process manager that improves upon Foreman by using tmux to manage processes. It provides individual process control, proper log handling, and interactive debugging capabilities - perfect for managing multiple Claude agents.

## ✅ Installation

### macOS
```bash
brew install overmind
```

### Linux
```bash
# Download latest binary
wget https://github.com/DarthSim/overmind/releases/latest/download/overmind-v2.5.0-linux-amd64.gz
gunzip overmind-v2.5.0-linux-amd64.gz
chmod +x overmind-v2.5.0-linux-amd64
sudo mv overmind-v2.5.0-linux-amd64 /usr/local/bin/overmind
```

### Verify Installation
```bash
overmind --version
# Should output: Overmind version X.X.X
```

## 📋 Configuration Files

### 1. Procfile (Main Configuration)
Located at: `/Users/erik/Desktop/claude-multiagent-system/Procfile`

Defines all processes to be managed:
- 9 Claude agents (supervisor, master, backend, database, frontend, instagram, testing, queue, deployment)
- Web interface (Streamlit)
- Redis server
- Optional Dramatiq worker

### 2. Procfile.dev (Development Configuration)
Located at: `/Users/erik/Desktop/claude-multiagent-system/Procfile.dev`

Minimal setup for testing with fewer agents.

### 3. .overmind.env (Environment Variables)
Located at: `/Users/erik/Desktop/claude-multiagent-system/.overmind.env`

Contains environment variables available to all processes.

## 🚀 Quick Start

### Start All Agents
```bash
cd /Users/erik/Desktop/claude-multiagent-system
overmind start
```

### Start in Development Mode
```bash
overmind start -f Procfile.dev
```

### Start in Daemon Mode (Background)
```bash
overmind start -D
```

## 🎮 Process Control Commands

### View Process Status
```bash
overmind ps
```

Output example:
```
PROCESS     PID       STATUS
supervisor  12345     running
backend     12346     running
web         12347     running
```

### Connect to Agent (Interactive)
```bash
# Connect to supervisor agent
overmind connect supervisor

# Connect to backend agent
overmind connect backend

# View Streamlit logs
overmind connect web

# Exit connection: Ctrl+B then D (tmux detach)
```

### Restart Individual Process
```bash
# Restart just the backend agent
overmind restart backend

# Restart web interface
overmind restart web
```

### Stop Individual Process
```bash
# Stop a specific agent
overmind stop frontend
```

### Start Stopped Process
```bash
# Start a previously stopped process
overmind start frontend
```

### Stop All Processes Gracefully
```bash
overmind quit
```

### Force Kill All Processes
```bash
overmind kill
```

## 🔄 Migration from Old System

### Automated Migration
```bash
./scripts/migrate_to_overmind.sh
```

This script will:
1. Check prerequisites (Overmind, tmux)
2. Optionally stop old tmux sessions
3. Start Overmind with your choice of Procfile
4. Show process status

### Manual Migration
```bash
# 1. Stop old tmux sessions (optional)
tmux kill-server

# 2. Start Overmind
cd /Users/erik/Desktop/claude-multiagent-system
overmind start -D

# 3. Verify processes
overmind ps
```

## 🐍 Python Integration

### Using OvermindClient
```python
from core.overmind_client import OvermindClient

# Initialize client
client = OvermindClient()

# Start processes
client.start(procfile="Procfile", detached=True)

# Get process status
processes = client.get_processes()
for name, info in processes.items():
    print(f"{name}: {info['status']}")

# Restart specific process
client.restart_process("backend")

# Stop all
client.kill()
```

### Quick Status Check
```python
from core.overmind_client import quick_status

status = quick_status()
print(status)
```

## 📊 Process Status Indicators

- **running**: Process is active and running
- **stopped**: Process was stopped manually
- **exited**: Process exited (check exit code)
- **starting**: Process is starting up

## 🛠️ Troubleshooting

### Issue: "dial unix ./.overmind.sock: connect: no such file or directory"
**Solution**: Overmind is not running. Start it with `overmind start`

### Issue: "open terminal failed: not a terminal"
**Solution**: This happens when trying to connect from a non-interactive shell. Use a terminal to run `overmind connect`

### Issue: Process exits immediately
**Solution**: Check the process command in Procfile. Test it manually first.

### View Logs
```bash
# When running in daemon mode
overmind echo
```

### Check Socket
```bash
ls -la .overmind.sock
```

## 🔧 Advanced Configuration

### Custom Socket Location
```bash
export OVERMIND_SOCKET=/tmp/my-overmind.sock
overmind start
```

### Custom Port Range
```bash
# Start with base port 6000
overmind start -p 6000
```

### Process Formation (Scaling)
```bash
# Run 2 web processes, 3 workers
overmind start -m web=2,worker=3
```

### Auto-restart Failed Processes
```bash
overmind start -r backend,database
# or restart all on failure
overmind start -r all
```

## 📚 Key Advantages over Old System

1. **Individual Process Control**: Restart/stop single agents without affecting others
2. **Better Logging**: No log delays or color loss
3. **Interactive Debugging**: Connect to any agent for live debugging
4. **Automatic Port Management**: PORT environment variable handled automatically
5. **Graceful Shutdown**: Processes get time to clean up
6. **Process Isolation**: One crash doesn't bring down everything

## 🎯 Common Workflows

### Daily Development
```bash
# Morning startup
cd /Users/erik/Desktop/claude-multiagent-system
overmind start -f Procfile.dev -D

# Check status
overmind ps

# Connect to supervisor for debugging
overmind connect supervisor

# Evening shutdown
overmind quit
```

### Production Deployment
```bash
# Start all agents
overmind start -D

# Monitor
overmind ps
watch -n 5 'overmind ps'

# Restart misbehaving agent
overmind restart backend

# Graceful shutdown for maintenance
overmind quit
```

## 📝 Notes

- Overmind creates a tmux session named after your project
- Each process runs in its own tmux pane
- Environment variables from `.overmind.env` are loaded automatically
- The socket file (`.overmind.sock`) is created in the project root
- Processes inherit the working directory where Overmind was started

## 🔗 Resources

- [Overmind GitHub](https://github.com/DarthSim/overmind)
- [Overmind vs Foreman Article](https://evilmartians.com/chronicles/introducing-overmind-and-hivemind)
- [Procfile Specification](https://devcenter.heroku.com/articles/procfile)

---

**Last Updated**: December 17, 2024
**Overmind Version**: 2.5.1