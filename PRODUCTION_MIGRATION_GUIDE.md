# MCP v2 Production Migration Guide

## Executive Summary

This guide provides step-by-step instructions for migrating from the existing pattern-matching MCP system to the full MCP v2 compliant system with JSON-RPC 2.0 protocol. The migration preserves all existing functionality while adding enterprise-grade features.

## Table of Contents

1. [Pre-Migration Checklist](#pre-migration-checklist)
2. [System Requirements](#system-requirements)
3. [Backup Procedures](#backup-procedures)
4. [Migration Steps](#migration-steps)
5. [Agent Terminal Integration](#agent-terminal-integration)
6. [Validation & Testing](#validation--testing)
7. [Rollback Plan](#rollback-plan)
8. [Post-Migration Tasks](#post-migration-tasks)

---

## Pre-Migration Checklist

### ✅ Required Before Starting

- [ ] Current system backup completed
- [ ] Database backup verified (`/tmp/mcp_state.db`)
- [ ] All agents are in stable state
- [ ] Maintenance window scheduled (2-4 hours)
- [ ] Team notified of migration
- [ ] Rollback plan reviewed
- [ ] Test environment validated

### ✅ Version Requirements

```bash
# Check versions
python3 --version  # Required: 3.11+
node --version     # Required: 18+
npm --version      # Required: 9+
sqlite3 --version  # Required: 3.39+
```

### ✅ Dependencies Installation

```bash
# Python dependencies
pip3 install -r requirements.txt

# Additional for MCP v2
pip3 install aiohttp websockets cryptography PyJWT authlib jsonschema psutil aiocache aiosqlite

# Frontend dependencies
cd claude-ui
npm install
```

---

## System Requirements

### Hardware Requirements

| Component | Minimum | Recommended | Production |
|-----------|---------|-------------|------------|
| CPU | 2 cores | 4 cores | 8+ cores |
| RAM | 4 GB | 8 GB | 16+ GB |
| Storage | 10 GB | 20 GB | 50+ GB SSD |
| Network | 100 Mbps | 1 Gbps | 10 Gbps |

### Software Requirements

- **Operating System**: Linux (Ubuntu 20.04+), macOS 12+
- **Python**: 3.11+ with async support
- **Node.js**: 18+ LTS
- **Database**: SQLite 3.39+ (or PostgreSQL 14+ for production)
- **Cache**: Redis 6+ (optional but recommended)
- **Reverse Proxy**: Nginx 1.20+ (production)

### Port Requirements

| Service | Port | Description |
|---------|------|-------------|
| MCP Server (HTTP) | 8099 | Main API endpoint |
| WebSocket | 8100 | Real-time communication |
| React Frontend | 5173 | Development UI |
| Agent Terminals | 8090-8098 | Individual agent terminals |
| Redis | 6379 | Cache service (optional) |

---

## Backup Procedures

### 1. Database Backup

```bash
#!/bin/bash
# backup_mcp_database.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/mcp"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup SQLite database
sqlite3 /tmp/mcp_state.db ".backup $BACKUP_DIR/mcp_state_${TIMESTAMP}.db"

# Backup agent states
cp -r /Users/erik/Desktop/claude-multiagent-system/agent_states $BACKUP_DIR/agent_states_${TIMESTAMP}

# Create compressed archive
tar -czf $BACKUP_DIR/mcp_backup_${TIMESTAMP}.tar.gz \
    $BACKUP_DIR/mcp_state_${TIMESTAMP}.db \
    $BACKUP_DIR/agent_states_${TIMESTAMP}

echo "Backup completed: $BACKUP_DIR/mcp_backup_${TIMESTAMP}.tar.gz"
```

### 2. Configuration Backup

```bash
# Backup configurations
cp -r /Users/erik/Desktop/claude-multiagent-system/.claude /backup/claude_config
cp /Users/erik/Desktop/claude-multiagent-system/*.json /backup/config_files/
```

---

## Migration Steps

### Phase 1: Stop Current Services

```bash
# 1. Stop existing MCP server
pkill -f "mcp_api_server_optimized.py"

# 2. Stop pattern matching bridge
pkill -f "mcp_bridge.py"

# 3. Stop frontend (if running)
pkill -f "npm run dev"

# 4. Verify all services stopped
ps aux | grep -E "mcp|claude" | grep -v grep
```

### Phase 2: Database Migration

```bash
# 1. Run database migration script
python3 migrate_database.py

# 2. Verify new tables created
sqlite3 /tmp/mcp_state.db ".tables"

# Expected output should include:
# capabilities, resources, prompts, resource_access_log
# consent_records, data_processing_records, hipaa_access_logs
# performance_metrics, query_performance, cache_stats
```

### Phase 3: Start MCP v2 Server

```bash
# 1. Start the compliant MCP v2 server
python3 mcp_server_v2_compliant.py &

# 2. Verify server is running
curl http://localhost:8099/api/mcp/status

# 3. Check WebSocket server
python3 mcp_websocket_client.py test
```

### Phase 4: Agent Terminal Integration

```bash
# 1. Update agent configurations
for agent in backend-api database frontend-ui testing instagram supervisor master; do
    echo "Updating agent: $agent"

    # Update tmux session
    tmux send-keys -t "claude-$agent" C-c Enter
    tmux send-keys -t "claude-$agent" "export MCP_SERVER=http://localhost:8099" Enter
    tmux send-keys -t "claude-$agent" "export MCP_WEBSOCKET=ws://localhost:8100" Enter
done

# 2. Start ttyd terminals for each agent
./start_agent_terminals.sh

# 3. Verify terminal access
for port in {8090..8098}; do
    curl -I http://localhost:$port 2>/dev/null | head -n 1
done
```

### Phase 5: Frontend Integration

```bash
# 1. Update frontend configuration
cd claude-ui

# 2. Ensure vite.config.ts has correct proxy settings
cat vite.config.ts | grep -A 5 "proxy:"

# 3. Start frontend with MCP v2 support
npm run dev

# 4. Access frontend
open http://localhost:5173
```

---

## Agent Terminal Integration

### Critical Integration Points

The Agent Terminal is the **MOST IMPORTANT** part of the system. It must be properly integrated with MCP v2.

### 1. Terminal Port Mapping

```javascript
// Ensure MultiTerminal.tsx has correct port mapping
const TERMINAL_PORT_MAP = {
    'backend-api': 8090,
    'database': 8091,
    'frontend-ui': 8092,
    'testing': 8093,
    'instagram': 8094,
    'supervisor': 8095,
    'master': 8096,
    'deployment': 8097,
    'queue-manager': 8098
};
```

### 2. MCP Integration in Terminals

```javascript
// Update terminal to use MCP v2
const mcpClient = new MCPClient({
    server: 'http://localhost:8099',
    websocket: 'ws://localhost:8100',
    hooks: {
        onToolCall: (tool) => console.log('Tool called:', tool),
        onResourceAccess: (resource) => console.log('Resource accessed:', resource)
    }
});
```

### 3. Start Agent Terminals Script

```bash
#!/bin/bash
# start_agent_terminals.sh

AGENTS=("backend-api" "database" "frontend-ui" "testing" "instagram" "supervisor" "master" "deployment" "queue-manager")
PORTS=(8090 8091 8092 8093 8094 8095 8096 8097 8098)

for i in "${!AGENTS[@]}"; do
    agent="${AGENTS[$i]}"
    port="${PORTS[$i]}"

    # Start ttyd for agent
    ttyd -p $port -t fontSize=14 -t 'theme={"background":"#1a1a1a"}' \
         tmux attach-session -t "claude-$agent" &

    echo "Started terminal for $agent on port $port"
done

echo "All agent terminals started. Access at http://localhost:8090-8098"
```

---

## Validation & Testing

### 1. Core Functionality Tests

```bash
# Run test suites
python3 test_mcp_v2.py           # Core MCP tests
python3 test_mcp_security.py     # Security tests
python3 test_mcp_integration.py  # Integration tests
python3 test_mcp_compliance.py   # Compliance tests
```

### 2. Performance Validation

```bash
# Run load test
python3 -c "
from mcp_performance_v2 import LoadTester
import asyncio

async def test():
    tester = LoadTester()
    results = await tester.run_load_test(num_requests=1000, concurrent_users=10)
    print(f'Throughput: {results[\"requests_per_second\"]:.0f} req/s')
    print(f'Success Rate: {results[\"success_count\"]/results[\"total_requests\"]*100:.1f}%')
    print(f'P95 Response: {results[\"p95_response_time\"]:.3f}s')

asyncio.run(test())
"
```

### 3. Agent Terminal Validation

```bash
# Check each agent terminal
for port in {8090..8098}; do
    echo "Testing port $port..."
    curl -s http://localhost:$port | grep -q "ttyd" && echo "✓ Terminal on $port is active" || echo "✗ Terminal on $port failed"
done
```

### 4. MCP Hook Validation

```bash
# Test Claude Code hooks
curl -X POST http://localhost:8099/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": 1
  }'
```

---

## Rollback Plan

### If Migration Fails

```bash
#!/bin/bash
# rollback.sh

# 1. Stop MCP v2 services
pkill -f "mcp_server_v2"
pkill -f "mcp_websocket"

# 2. Restore database
LATEST_BACKUP=$(ls -t /backup/mcp/mcp_state_*.db | head -1)
cp $LATEST_BACKUP /tmp/mcp_state.db

# 3. Start old services
python3 mcp_api_server_optimized.py &
python3 mcp_bridge.py &

# 4. Restart agent terminals
./restart_old_terminals.sh

echo "Rollback completed. System restored to previous state."
```

### Rollback Triggers

- Performance degradation > 50%
- Agent terminals not accessible
- Database corruption detected
- Critical errors in logs
- User-reported functionality loss

---

## Post-Migration Tasks

### 1. Monitor System Health

```bash
# Check system status
curl http://localhost:8099/api/mcp/status

# Monitor performance
curl http://localhost:8099/api/mcp/performance/metrics

# Check compliance
curl http://localhost:8099/api/mcp/compliance/report?framework=gdpr
```

### 2. Update Documentation

- Update API documentation
- Update agent terminal guides
- Update user manuals
- Update troubleshooting guides

### 3. Performance Tuning

```python
# Adjust cache settings
CACHE_TTL = 600  # Increase if hit rate < 80%
DB_POOL_SIZE = 10  # Increase for more concurrent connections

# Monitor and adjust
watch -n 5 'curl -s http://localhost:8099/api/mcp/performance/report | jq .'
```

### 4. Security Hardening

```bash
# Enable rate limiting
export RATE_LIMIT=100  # requests per minute

# Enable audit logging
export AUDIT_LOG_LEVEL=INFO

# Review security status
curl http://localhost:8099/api/mcp/security
```

---

## Troubleshooting Guide

### Common Issues and Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| Port conflict | "Address already in use" | `lsof -i :PORT` then `kill -9 PID` |
| Database locked | "database is locked" | Close SQLite connections, restart server |
| WebSocket fails | "Connection refused" | Check port 8100, restart WebSocket server |
| Agent terminal blank | No output in terminal | Restart tmux session and ttyd |
| High memory usage | >80% RAM usage | Increase cache TTL, reduce pool size |
| Slow responses | P95 > 1 second | Enable caching, check slow queries |

### Debug Commands

```bash
# Check server logs
tail -f /var/log/mcp/server.log

# Monitor WebSocket connections
wscat -c ws://localhost:8100

# Database query performance
sqlite3 /tmp/mcp_state.db "SELECT * FROM query_performance ORDER BY execution_time DESC LIMIT 10;"

# Agent status
for agent in backend-api database frontend-ui testing; do
    tmux capture-pane -t "claude-$agent" -p | tail -5
done
```

---

## Production Deployment

### 1. Use Production Configuration

```python
# config/production.py
DEBUG = False
CACHE_BACKEND = 'redis://localhost:6379'
DATABASE_URL = 'postgresql://user:pass@localhost/mcp_prod'
RATE_LIMIT = 1000
LOG_LEVEL = 'WARNING'
```

### 2. Deploy with Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8099 8100
CMD ["python", "mcp_server_v2_compliant.py"]
```

### 3. Use Process Manager

```bash
# Install PM2
npm install -g pm2

# Start services
pm2 start mcp_server_v2_compliant.py --name mcp-server
pm2 start mcp_websocket_handler.py --name mcp-websocket
pm2 save
pm2 startup
```

### 4. Configure Nginx

```nginx
# /etc/nginx/sites-available/mcp
server {
    listen 443 ssl http2;
    server_name mcp.yourdomain.com;

    ssl_certificate /etc/ssl/certs/mcp.crt;
    ssl_certificate_key /etc/ssl/private/mcp.key;

    location / {
        proxy_pass http://localhost:8099;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Request-ID $request_id;
    }

    location /ws {
        proxy_pass http://localhost:8100;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Monitoring & Alerting

### 1. Set Up Monitoring

```bash
# Install Prometheus node exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.5.0/node_exporter-1.5.0.linux-amd64.tar.gz
tar xvf node_exporter-1.5.0.linux-amd64.tar.gz
./node_exporter &

# Configure alerts
cat > /etc/prometheus/alerts.yml << EOF
groups:
  - name: mcp_alerts
    rules:
      - alert: HighResponseTime
        expr: mcp_response_time_p95 > 1
        for: 5m
        annotations:
          summary: "High P95 response time"

      - alert: LowCacheHitRate
        expr: mcp_cache_hit_rate < 0.7
        for: 10m
        annotations:
          summary: "Cache hit rate below 70%"
EOF
```

### 2. Dashboard Setup

Access monitoring dashboards:
- MCP Status: http://localhost:5173 → Dashboard tab
- Agent Terminals: http://localhost:8090-8098
- WebSocket Status: http://localhost:5173 → WebSocket tab
- Compliance: http://localhost:5173 → Compliance tab
- Performance: http://localhost:8099/api/mcp/performance/report

---

## Success Criteria

Migration is successful when:

✅ All agent terminals are accessible and functional
✅ MCP v2 server responds on port 8099
✅ WebSocket connections established on port 8100
✅ Frontend displays correct agent status
✅ All tests pass with >80% success rate
✅ Performance metrics meet or exceed baseline
✅ No critical errors in logs for 1 hour
✅ Agent terminal integration fully functional

---

## Support & Resources

- **Documentation**: `/docs/MCP_V2_API_REFERENCE.md`
- **Troubleshooting**: `/docs/TROUBLESHOOTING.md`
- **Support Channel**: #mcp-migration
- **Emergency Contact**: ops-team@company.com
- **Rollback Hotline**: +1-XXX-XXX-XXXX

---

## Appendix

### A. Environment Variables

```bash
# .env.production
MCP_SERVER_PORT=8099
MCP_WEBSOCKET_PORT=8100
MCP_CACHE_BACKEND=redis
MCP_DATABASE_URL=sqlite:///tmp/mcp_state.db
MCP_LOG_LEVEL=INFO
MCP_RATE_LIMIT=100
MCP_ENABLE_COMPLIANCE=true
MCP_ENABLE_PERFORMANCE=true
```

### B. Health Check Script

```bash
#!/bin/bash
# health_check.sh

echo "=== MCP v2 System Health Check ==="

# Check services
services=("mcp_server:8099" "websocket:8100" "frontend:5173")
for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    nc -zv localhost $port 2>/dev/null && echo "✓ $name is running" || echo "✗ $name is down"
done

# Check database
sqlite3 /tmp/mcp_state.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" && echo "✓ Database accessible" || echo "✗ Database error"

# Check agent terminals
for port in {8090..8098}; do
    curl -s http://localhost:$port > /dev/null && echo "✓ Terminal on $port active" || echo "✗ Terminal on $port inactive"
done

echo "=== Health Check Complete ==="
```

---

**Last Updated**: 2025-09-18
**Version**: 1.0.0
**Status**: READY FOR PRODUCTION