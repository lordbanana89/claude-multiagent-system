# 🔧 Troubleshooting Guide

Common issues and solutions for Claude Multi-Agent System.

## Table of Contents

- [Installation Issues](#installation-issues)
- [TMUX Issues](#tmux-issues)
- [Redis Issues](#redis-issues)
- [Queue System Issues](#queue-system-issues)
- [Overmind Issues](#overmind-issues)
- [Agent Issues](#agent-issues)
- [Performance Issues](#performance-issues)
- [Web Interface Issues](#web-interface-issues)

---

## Installation Issues

### Python Dependencies

#### Problem: `ModuleNotFoundError: No module named 'dramatiq'`

**Solution:**
```bash
pip install dramatiq[redis]
```

#### Problem: `ImportError: cannot import name 'Empty' from 'queue'`

**Cause:** Package naming conflict between your `queue/` directory and Python's built-in module.

**Solution:**
The package has been renamed to `task_queue/`. Update your imports:
```python
# Old (incorrect)
from queue import QueueClient

# New (correct)
from task_queue import QueueClient
```

### System Dependencies

#### Problem: `tmux: command not found`

**Solution:**

macOS:
```bash
brew install tmux
```

Linux:
```bash
sudo apt-get install tmux  # Ubuntu/Debian
sudo yum install tmux       # RHEL/CentOS
```

#### Problem: Overmind not installed

**Solution:**
```bash
# macOS
brew install overmind

# Linux
wget https://github.com/DarthSim/overmind/releases/latest/download/overmind-v2.5.1-linux-amd64.gz
gunzip overmind-v2.5.1-linux-amd64.gz
chmod +x overmind-v2.5.1-linux-amd64
sudo mv overmind-v2.5.1-linux-amd64 /usr/local/bin/overmind
```

---

## TMUX Issues

### Lost Commands (Race Conditions)

#### Problem: Commands sent to agents are lost or not executed

**Cause:** TMUX race condition when sending commands too quickly.

**Solution:**
Ensure the delay is configured properly:
```python
# In config/settings.py
TMUX_COMMAND_DELAY = 0.1  # MANDATORY - DO NOT REDUCE

# Or set environment variable
export TMUX_COMMAND_DELAY=0.1
```

### Session Not Found

#### Problem: `session not found: claude-supervisor`

**Solution:**

1. Check if session exists:
```bash
tmux ls
```

2. Create missing session:
```bash
tmux new-session -d -s claude-supervisor
```

3. Or use the startup script:
```bash
./scripts/start_complete_system.sh
```

### Can't Attach to Session

#### Problem: `no current client` or `no PTY`

**Solution:**
```bash
# Ensure you're in a terminal (not a script)
tmux attach -t claude-supervisor

# Or use Overmind to connect
overmind connect supervisor
```

---

## Redis Issues

### Connection Refused

#### Problem: `Could not connect to Redis at localhost:6379`

**Solution:**

1. Check if Redis is running:
```bash
redis-cli ping
```

2. Start Redis:
```bash
# Direct
redis-server

# With Overmind
overmind start redis

# With Docker
docker run -d -p 6379:6379 redis:7.2
```

3. Check Redis logs:
```bash
redis-cli monitor
```

### High Memory Usage

#### Problem: Redis using too much memory

**Solution:**

1. Check memory usage:
```bash
redis-cli info memory
```

2. Clear old data:
```bash
redis-cli FLUSHDB  # Clear current database
redis-cli FLUSHALL # Clear all databases (careful!)
```

3. Configure max memory:
```bash
redis-server --maxmemory 2gb --maxmemory-policy lru
```

### Authentication Failed

#### Problem: `NOAUTH Authentication required`

**Solution:**

Set Redis password in environment:
```bash
export REDIS_URL=redis://:password@localhost:6379/0
```

---

## Queue System Issues

### Worker Not Processing Messages

#### Problem: Messages queued but not processed

**Solution:**

1. Check if worker is running:
```bash
ps aux | grep dramatiq
```

2. Start worker manually:
```bash
python -m dramatiq task_queue.worker
```

3. Check worker logs:
```bash
python -m dramatiq task_queue.worker --verbose
```

4. Verify broker connection:
```python
from task_queue import broker
print(type(broker).__name__)  # Should be "RedisBroker"
```

### StubBroker Instead of RedisBroker

#### Problem: Using StubBroker in production

**Solution:**

1. Ensure Redis is running
2. Check broker initialization:
```python
from task_queue.broker import check_broker_health
health = check_broker_health()
print(health['status'])
```

3. Fix broker configuration:
```python
# In task_queue/broker.py
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
```

### Dead Letter Queue

#### Problem: Messages ending up in DLQ

**Solution:**

1. Check failed messages:
```bash
redis-cli lrange dramatiq:dead_letter_queue 0 -1
```

2. Review logs:
```bash
cat logs/dlq_tasks.jsonl
```

3. Reprocess failed messages:
```python
from task_queue import broker
# Custom logic to reprocess DLQ messages
```

---

## Overmind Issues

### Socket Connection Error

#### Problem: `dial unix ./.overmind.sock: connect: no such file or directory`

**Solution:**

1. Overmind is not running. Start it:
```bash
overmind start
```

2. Check if socket exists:
```bash
ls -la .overmind.sock
```

3. Kill and restart:
```bash
overmind kill
overmind start
```

### Process Won't Start

#### Problem: Process exits immediately

**Solution:**

1. Check Procfile syntax:
```bash
cat Procfile
```

2. Test command directly:
```bash
# Test the command from Procfile
streamlit run interfaces/web/complete_integration.py
```

3. Check logs:
```bash
overmind echo  # Show all process outputs
```

### Can't Connect to Process

#### Problem: `overmind connect supervisor` fails

**Solution:**

1. Ensure process is running:
```bash
overmind ps
```

2. Restart the specific process:
```bash
overmind restart supervisor
```

3. Check for port conflicts:
```bash
lsof -i :8501  # Check if port is in use
```

---

## Agent Issues

### Agent Not Responding

#### Problem: Agent doesn't execute commands

**Solution:**

1. Check agent session:
```python
from core.tmux_client import TMUXClient
exists = TMUXClient.session_exists("claude-supervisor")
print(f"Session exists: {exists}")
```

2. Check agent health:
```python
from monitoring.health import check_agents_health
health = check_agents_health()
print(health.to_dict())
```

3. Restart agent:
```bash
overmind restart supervisor
```

### Agent Session Corrupted

#### Problem: Agent session exists but not working

**Solution:**

1. Kill the corrupted session:
```bash
tmux kill-session -t claude-supervisor
```

2. Recreate session:
```bash
tmux new-session -d -s claude-supervisor
```

3. Or use the fix script:
```bash
./scripts/fix_claude_sessions.sh
```

---

## Performance Issues

### Slow Message Processing

#### Problem: Queue throughput is low

**Solution:**

1. Increase worker processes:
```bash
python -m dramatiq task_queue.worker --processes 4 --threads 8
```

2. Check Redis latency:
```bash
redis-cli --latency
```

3. Monitor queue depth:
```python
from task_queue import QueueClient
client = QueueClient()
stats = client.get_stats()
print(f"Queue depth: {stats}")
```

### High CPU Usage

#### Problem: System using too much CPU

**Solution:**

1. Check process usage:
```bash
top -o cpu  # macOS
top        # Linux (press 'P' to sort by CPU)
```

2. Limit worker threads:
```bash
python -m dramatiq task_queue.worker --processes 1 --threads 2
```

3. Add delays between operations:
```python
import time
time.sleep(0.1)  # Add small delays
```

### Memory Leaks

#### Problem: Memory usage keeps growing

**Solution:**

1. Monitor memory:
```python
from monitoring.metrics import memory_usage_gauge
# Check memory metrics
```

2. Restart workers periodically:
```bash
# Add to crontab
0 */4 * * * overmind restart dramatiq
```

3. Clear old state:
```bash
# Clear old shared state
rm langgraph-test/shared_state.json.backup*
```

---

## Web Interface Issues

### Streamlit Won't Start

#### Problem: `streamlit: command not found`

**Solution:**
```bash
pip install streamlit
```

### Port Already in Use

#### Problem: `Address already in use: 8501`

**Solution:**

1. Find process using port:
```bash
lsof -i :8501
```

2. Kill the process:
```bash
kill -9 <PID>
```

3. Or use different port:
```bash
streamlit run interfaces/web/complete_integration.py --server.port 8502
```

### WebSocket Connection Failed

#### Problem: Real-time updates not working

**Solution:**

1. Check WebSocket support:
```python
# In browser console
console.log(typeof(WebSocket))
```

2. Check firewall/proxy settings
3. Use polling fallback:
```python
# Add to Streamlit app
st.experimental_rerun()  # Force refresh
```

---

## Diagnostic Commands

### Quick Health Check

```bash
# Run comprehensive health check
python -c "from monitoring.health import check_system_health; import json; print(json.dumps(check_system_health(), indent=2))"
```

### Check All Components

```bash
# Create diagnostic script
cat > diagnose.py << 'EOF'
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("🔍 System Diagnostic")
print("=" * 50)

# Check Redis
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, socket_timeout=2)
    r.ping()
    print("✅ Redis: Connected")
except:
    print("❌ Redis: Not available")

# Check TMUX
try:
    from core.tmux_client import TMUXClient
    sessions = TMUXClient.list_sessions()
    print(f"✅ TMUX: {len(sessions)} sessions")
except:
    print("❌ TMUX: Not available")

# Check Queue
try:
    from task_queue import broker
    print(f"✅ Queue: {type(broker).__name__}")
except:
    print("❌ Queue: Not configured")

# Check Overmind
try:
    from core.overmind_client import OvermindClient
    client = OvermindClient()
    processes = client.get_processes()
    print(f"✅ Overmind: {len(processes)} processes")
except:
    print("❌ Overmind: Not running")

print("=" * 50)
EOF

python diagnose.py
```

### Generate Support Bundle

```bash
# Create support bundle for debugging
cat > support_bundle.sh << 'EOF'
#!/bin/bash
BUNDLE="support_bundle_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BUNDLE

# System info
echo "System Information" > $BUNDLE/system_info.txt
uname -a >> $BUNDLE/system_info.txt
python --version >> $BUNDLE/system_info.txt

# Process list
ps aux | grep -E "(tmux|redis|dramatiq|overmind|streamlit)" > $BUNDLE/processes.txt

# TMUX sessions
tmux ls > $BUNDLE/tmux_sessions.txt 2>&1

# Redis info
redis-cli info > $BUNDLE/redis_info.txt 2>&1

# Overmind status
overmind ps > $BUNDLE/overmind_status.txt 2>&1

# Recent logs
tail -n 100 logs/*.log > $BUNDLE/recent_logs.txt 2>&1

# Config files (without secrets)
grep -v password config/settings.py > $BUNDLE/config.txt

# Create archive
tar -czf $BUNDLE.tar.gz $BUNDLE/
rm -rf $BUNDLE/

echo "Support bundle created: $BUNDLE.tar.gz"
EOF

chmod +x support_bundle.sh
./support_bundle.sh
```

---

## Getting Help

If you're still experiencing issues:

1. **Check the logs:**
   ```bash
   tail -f logs/*.log
   ```

2. **Run tests:**
   ```bash
   python tests/test_phase0.py
   python tests/test_dramatiq.py
   ```

3. **Enable debug mode:**
   ```bash
   export DEBUG=true
   export LOG_LEVEL=DEBUG
   ```

4. **Report an issue:**
   - Include the support bundle
   - Describe steps to reproduce
   - Include error messages
   - Note your environment (OS, Python version, etc.)

---

## Emergency Recovery

If the system is completely broken:

```bash
# Kill everything
tmux kill-server
overmind kill
pkill -f dramatiq
pkill -f streamlit
redis-cli FLUSHALL

# Clean state
rm -f .overmind.sock
rm -f langgraph-test/shared_state.json
rm -rf logs/*.log

# Restart fresh
overmind start
```

---

**Remember:** Most issues can be resolved by:
1. Checking if services are running (Redis, TMUX, Overmind)
2. Reviewing logs for error messages
3. Restarting the affected component
4. Ensuring proper configuration in `config/settings.py`