# Troubleshooting Guide

## Common Issues and Solutions

### Agent Issues

#### Agent Not Responding

**Symptoms:**
- No response to commands
- Agent shows as "offline" in dashboard
- TMUX session unresponsive

**Solutions:**

```bash
# 1. Check if TMUX session exists
tmux ls | grep claude-{agent-name}

# 2. If session exists, try attaching
tmux attach -t claude-{agent-name}

# 3. If frozen, kill and restart
tmux kill-session -t claude-{agent-name}
./scripts/restart_agent.sh {agent-name}

# 4. Check agent logs
sqlite3 mcp_system.db \
  "SELECT * FROM activity_logs WHERE agent='{agent-name}' ORDER BY timestamp DESC LIMIT 10;"
```

#### Agent Memory Issues

**Symptoms:**
- High memory usage
- Slow response times
- System warnings

**Solutions:**

```python
# Clear agent cache
import redis
r = redis.Redis()
r.flushdb()  # Clear Redis cache

# Reset agent state
from core.agent_coordinator import reset_agent
reset_agent('backend-api')

# Increase memory limit
export AGENT_MEMORY_LIMIT=2048  # MB
```

### Database Issues

#### Database Locked

**Error:** `database is locked`

**Solutions:**

```bash
# 1. Remove lock files
rm *.db-shm *.db-wal

# 2. Check for stuck processes
lsof | grep mcp_system.db
# Kill any stuck processes

# 3. Backup and recreate
cp mcp_system.db mcp_system.db.backup
sqlite3 mcp_system.db "VACUUM;"
```

#### Corrupted Database

**Symptoms:**
- SQL errors
- Missing data
- Inconsistent state

**Solutions:**

```bash
# 1. Integrity check
sqlite3 mcp_system.db "PRAGMA integrity_check;"

# 2. Recover from backup
cp mcp_system.db.backup mcp_system.db

# 3. Export and reimport
sqlite3 mcp_system.db .dump > backup.sql
rm mcp_system.db
sqlite3 mcp_system.db < backup.sql
```

### MCP Server Issues

#### Connection Refused

**Error:** `Connection refused on port 9999`

**Solutions:**

```bash
# 1. Check if server is running
ps aux | grep mcp_server

# 2. Start MCP server
python mcp_server_v2_secure.py &

# 3. Check port availability
lsof -i :9999

# 4. Use alternative port
export MCP_PORT=9998
python mcp_server_v2_secure.py --port 9998
```

#### Authentication Failures

**Error:** `401 Unauthorized`

**Solutions:**

```python
# 1. Regenerate tokens
from auth.token_manager import regenerate_all_tokens
regenerate_all_tokens()

# 2. Reset OAuth credentials
sqlite3 auth.db "DELETE FROM oauth_tokens WHERE expired < datetime('now');"

# 3. Clear session cache
sqlite3 auth.db "DELETE FROM sessions WHERE last_activity < datetime('now', '-1 hour');"
```

### API Gateway Issues

#### Service Unavailable

**Error:** `503 Service Unavailable`

**Solutions:**

```bash
# 1. Check all services
for port in 5001 5002 5003 5004; do
  curl -s http://localhost:$port/health || echo "Port $port is down"
done

# 2. Restart API services
overmind restart

# 3. Check Redis connection
redis-cli ping

# 4. Verify database connections
python -c "from core.database_manager import test_connections; test_connections()"
```

#### Rate Limiting

**Error:** `429 Too Many Requests`

**Solutions:**

```python
# 1. Increase rate limits
# In config/settings.py
RATE_LIMIT_PER_MINUTE = 1000  # Increase from 100

# 2. Clear rate limit cache
import redis
r = redis.Redis()
r.delete('rate_limit:*')

# 3. Whitelist IP
RATE_LIMIT_WHITELIST = ['127.0.0.1', '::1']
```

### Frontend Issues

#### Dashboard Not Loading

**Symptoms:**
- Blank page
- Loading spinner stuck
- Console errors

**Solutions:**

```bash
# 1. Check frontend build
cd claude-ui
npm run build

# 2. Clear cache
rm -rf node_modules/.vite
npm run dev

# 3. Check API connection
curl http://localhost:5001/api/agents

# 4. Rebuild dependencies
rm -rf node_modules package-lock.json
npm install
```

#### WebSocket Disconnections

**Symptoms:**
- Real-time updates not working
- Connection drops frequently

**Solutions:**

```javascript
// Increase timeout in claude-ui/src/config.js
export const WS_CONFIG = {
  reconnectInterval: 5000,
  maxReconnectAttempts: 10,
  heartbeatInterval: 30000
};

// Enable debug logging
localStorage.setItem('DEBUG', 'websocket:*');
```

### Performance Issues

#### Slow Task Execution

**Solutions:**

```bash
# 1. Check system resources
top -b -n 1 | head -20

# 2. Analyze slow queries
sqlite3 mcp_system.db "EXPLAIN QUERY PLAN SELECT * FROM tasks;"

# 3. Add indexes
sqlite3 mcp_system.db "CREATE INDEX idx_tasks_status ON tasks(status);"

# 4. Optimize Redis
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

#### High CPU Usage

**Solutions:**

```python
# 1. Profile code
import cProfile
cProfile.run('process_tasks()')

# 2. Limit concurrent tasks
MAX_CONCURRENT_TASKS = 3  # Reduce from 10

# 3. Enable CPU throttling
import resource
resource.setrlimit(resource.RLIMIT_CPU, (60, 120))  # Soft, hard limits
```

## Debug Commands

### System Status

```bash
# Complete system check
./scripts/system_health_check.sh

# Agent status
for agent in supervisor master backend-api database frontend-ui testing; do
  echo "=== $agent ==="
  curl -s http://localhost:5001/api/agents/$agent/status | jq .
done

# Database stats
sqlite3 mcp_system.db "
  SELECT 'Agents:', COUNT(*) FROM agents
  UNION ALL
  SELECT 'Tasks:', COUNT(*) FROM tasks
  UNION ALL
  SELECT 'Messages:', COUNT(*) FROM messages_v2
  UNION ALL
  SELECT 'Activities:', COUNT(*) FROM activity_logs;
"
```

### Logging

```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# View logs
tail -f logs/mcp_server.log
tail -f logs/api_gateway.log

# Agent-specific logs
tmux capture-pane -t claude-supervisor -p | tail -100
```

### Reset Procedures

#### Soft Reset

```bash
# Restart services without data loss
overmind restart
```

#### Hard Reset

```bash
# WARNING: This will clear all data
./scripts/hard_reset.sh

# Manual steps:
1. Stop all services
overmind stop

2. Clear databases
rm *.db

3. Clear Redis
redis-cli FLUSHALL

4. Reinitialize
./scripts/init_system.sh

5. Start services
overmind start
```

## Emergency Procedures

### System Recovery

```bash
#!/bin/bash
# emergency_recovery.sh

echo "Starting emergency recovery..."

# 1. Stop everything
tmux kill-server
pkill -f python
pkill -f node

# 2. Backup current state
mkdir -p backups/emergency_$(date +%Y%m%d_%H%M%S)
cp *.db backups/emergency_*/

# 3. Reset to known good state
git stash
git checkout main
git pull

# 4. Reinstall dependencies
pip install -r requirements.txt
cd claude-ui && npm install && cd ..

# 5. Restore from backup
cp backups/last_known_good/*.db .

# 6. Start minimal services
python mcp_server_v2_secure.py &
python routes_api.py &

echo "Recovery complete. Start agents manually."
```

### Data Recovery

```sql
-- Recover deleted tasks
SELECT * FROM tasks WHERE deleted_at IS NOT NULL;

-- Restore from audit log
INSERT INTO tasks (id, title, status)
SELECT
  json_extract(data, '$.task_id'),
  json_extract(data, '$.title'),
  'recovered'
FROM audit_trail
WHERE action = 'task_deleted'
  AND timestamp > datetime('now', '-1 day');
```

## Contact Support

If issues persist after trying these solutions:

1. **Check Documentation**: Review relevant sections in `/docs`
2. **Search Issues**: Check GitHub issues for similar problems
3. **Enable Debug Mode**: Set `DEBUG=true` for detailed logs
4. **Collect Diagnostics**: Run `./scripts/collect_diagnostics.sh`
5. **Report Issue**: Create GitHub issue with diagnostic output