# 📚 API Reference

Complete API documentation for Claude Multi-Agent System.

## Table of Contents

- [Task Queue API](#task-queue-api)
- [Monitoring API](#monitoring-api)
- [TMUX Client API](#tmux-client-api)
- [Overmind Client API](#overmind-client-api)
- [Shared State API](#shared-state-api)

---

## Task Queue API

### QueueClient

High-level client for interacting with the Dramatiq queue system.

#### Initialization

```python
from task_queue import QueueClient

client = QueueClient()
```

#### Methods

##### send_command(agent_id, command, task_id=None, delay=None)

Send a command to a specific agent.

**Parameters:**
- `agent_id` (str): Target agent identifier
- `command` (str): Command to execute
- `task_id` (str, optional): Task ID for tracking
- `delay` (int, optional): Delay in milliseconds before processing

**Returns:**
- `str`: Message ID for tracking

**Example:**
```python
msg_id = client.send_command(
    "supervisor",
    "echo 'Deploy application'",
    task_id="deploy_123"
)
```

##### broadcast(message, exclude=None)

Broadcast a message to all agents.

**Parameters:**
- `message` (str): Message to broadcast
- `exclude` (list, optional): List of agent IDs to exclude

**Returns:**
- `str`: Message ID

**Example:**
```python
msg_id = client.broadcast(
    "System maintenance starting",
    exclude=["testing"]
)
```

##### create_task_chain(steps)

Create a chain of tasks to execute sequentially.

**Parameters:**
- `steps` (list): List of task step dictionaries

**Step Dictionary Format:**
```python
{
    "agent_id": str,          # Target agent
    "command": str,           # Command to execute
    "description": str,       # Step description
    "delay": int,            # Delay after step (seconds)
    "continue_on_failure": bool  # Continue if step fails
}
```

**Returns:**
- `str`: Task chain message ID

**Example:**
```python
chain_id = client.create_task_chain([
    {
        "agent_id": "backend-api",
        "command": "python deploy.py --stage",
        "description": "Deploy to staging",
        "delay": 5
    },
    {
        "agent_id": "testing",
        "command": "pytest tests/integration",
        "description": "Run integration tests",
        "delay": 2
    }
])
```

##### create_parallel_tasks(tasks)

Create parallel tasks for multiple agents.

**Parameters:**
- `tasks` (list): List of (agent_id, command) tuples

**Returns:**
- `list`: List of message IDs

**Example:**
```python
msg_ids = client.create_parallel_tasks([
    ("backend-api", "python migrate.py"),
    ("frontend-ui", "npm run build"),
    ("database", "pg_dump production > backup.sql")
])
```

##### get_stats()

Get queue statistics.

**Returns:**
- `dict`: Queue statistics

**Example:**
```python
stats = client.get_stats()
print(f"Total messages: {stats['total_messages_sent']}")
print(f"Messages by actor: {stats['messages_by_actor']}")
```

### Convenience Functions

#### send_agent_command(agent_id, command, task_id=None)

Quick function to send a command without creating a client.

```python
from task_queue import send_agent_command

msg_id = send_agent_command("supervisor", "echo 'Hello'")
```

#### broadcast_to_all(message, exclude=None)

Quick broadcast function.

```python
from task_queue import broadcast_to_all

broadcast_to_all("System update complete")
```

#### quick_notify(agent_id, title, message, type="info")

Send a quick notification.

```python
from task_queue import quick_notify

quick_notify(
    "backend-api",
    "Deployment Complete",
    "Version 2.0.1 deployed successfully",
    type="success"
)
```

---

## Monitoring API

### MetricsCollector

Centralized metrics collection and management.

#### Initialization

```python
from monitoring.metrics import MetricsCollector

collector = MetricsCollector()
```

#### Methods

##### record_agent_command(agent_id, command_type, status, duration)

Record an agent command execution.

**Parameters:**
- `agent_id` (str): Agent identifier
- `command_type` (str): Type of command
- `status` (str): Command status ("success", "failure")
- `duration` (float, optional): Execution duration in seconds

**Example:**
```python
collector.record_agent_command(
    "supervisor",
    "deploy",
    "success",
    duration=45.3
)
```

##### record_task_completion(task_type, agent_id, status, duration)

Record task completion.

**Parameters:**
- `task_type` (str): Type of task
- `agent_id` (str): Agent that completed the task
- `status` (str): Completion status
- `duration` (float, optional): Task duration in seconds

##### record_error(component, error_type, severity)

Record system error.

**Parameters:**
- `component` (str): Component where error occurred
- `error_type` (str): Type of error
- `severity` (str): Error severity ("warning", "error", "critical")

##### get_metrics()

Get metrics in Prometheus format.

**Returns:**
- `bytes`: Prometheus-formatted metrics

### HealthChecker

Comprehensive health checking system.

#### Methods

##### check_system_health()

Perform comprehensive system health check.

**Returns:**
- `dict`: Health status with component details

**Example:**
```python
from monitoring.health import check_system_health

health = check_system_health()
print(f"Status: {health['status']}")
print(f"Uptime: {health['uptime_human']}")

for component, details in health['components'].items():
    print(f"{component}: {details['status']}")
```

##### get_health_endpoint()

Get health status for HTTP endpoint.

**Returns:**
- `tuple`: (HTTP status code, health data)

**Example:**
```python
from monitoring.health import get_health_endpoint

status_code, health_data = get_health_endpoint()
# Returns 200 for healthy/degraded, 503 for unhealthy
```

---

## TMUX Client API

### TMUXClient

Centralized TMUX interaction with race condition prevention.

#### Methods

##### send_command(session, command, delay=None)

Send command to TMUX session with mandatory delay.

**Parameters:**
- `session` (str): TMUX session name
- `command` (str): Command to send
- `delay` (float, optional): Custom delay (default: 0.1s)

**Returns:**
- `bool`: Success status

**Example:**
```python
from core.tmux_client import TMUXClient

success = TMUXClient.send_command(
    "claude-supervisor",
    "python deploy.py"
)
```

##### send_keys(session, keys)

Send raw keys without Enter.

**Parameters:**
- `session` (str): TMUX session name
- `keys` (str): Keys to send (e.g., "C-c" for Ctrl+C)

**Returns:**
- `bool`: Success status

##### capture_pane(session, lines=None)

Capture output from TMUX pane.

**Parameters:**
- `session` (str): TMUX session name
- `lines` (int, optional): Number of recent lines to capture

**Returns:**
- `str`: Captured text or None

##### session_exists(session)

Check if TMUX session exists.

**Parameters:**
- `session` (str): Session name

**Returns:**
- `bool`: True if session exists

##### list_sessions()

List all TMUX sessions.

**Returns:**
- `list`: List of session dictionaries

##### create_session(name, command=None)

Create new TMUX session.

**Parameters:**
- `name` (str): Session name
- `command` (str, optional): Initial command to run

**Returns:**
- `bool`: Success status

---

## Overmind Client API

### OvermindClient

Client for Overmind process management.

#### Initialization

```python
from core.overmind_client import OvermindClient

client = OvermindClient()
```

#### Methods

##### start(procfile="Procfile", detached=True)

Start Overmind with specified Procfile.

**Parameters:**
- `procfile` (str): Path to Procfile
- `detached` (bool): Run in background

**Returns:**
- `bool`: Success status

##### get_processes()

Get all Overmind-managed processes with status.

**Returns:**
- `dict`: Process statuses

**Example:**
```python
processes = client.get_processes()
for name, info in processes.items():
    print(f"{name}: {info['status']}")
```

##### restart_process(name)

Restart specific process.

**Parameters:**
- `name` (str): Process name

**Returns:**
- `bool`: Success status

##### stop_process(name)

Stop specific process.

**Parameters:**
- `name` (str): Process name

**Returns:**
- `bool`: Success status

##### connect_to_process(name)

Connect to process terminal (interactive).

**Parameters:**
- `name` (str): Process name

##### kill_all()

Kill all Overmind processes.

**Returns:**
- `bool`: Success status

---

## Shared State API

### SharedStateManager

Manages shared state across agents.

#### Initialization

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "langgraph-test"))
from shared_state.manager import SharedStateManager

manager = SharedStateManager()
```

#### Methods

##### get_state()

Get current shared state.

**Returns:**
- `dict`: Current state

##### update_state(updates)

Update shared state.

**Parameters:**
- `updates` (dict): State updates to apply

**Returns:**
- `bool`: Success status

##### get_agent_status(agent_id)

Get specific agent status.

**Parameters:**
- `agent_id` (str): Agent identifier

**Returns:**
- `dict`: Agent status

##### update_agent_status(agent_id, status, **kwargs)

Update agent status.

**Parameters:**
- `agent_id` (str): Agent identifier
- `status` (str): New status
- `**kwargs`: Additional status fields

**Example:**
```python
manager.update_agent_status(
    "backend-api",
    "active",
    last_command="deploy",
    error_count=0
)
```

---

## Error Codes

### Queue System Errors

- `QUEUE_001`: Redis connection failed
- `QUEUE_002`: Message serialization error
- `QUEUE_003`: Actor not found
- `QUEUE_004`: Retry limit exceeded

### Agent Errors

- `AGENT_001`: Session not found
- `AGENT_002`: Command execution failed
- `AGENT_003`: Timeout exceeded
- `AGENT_004`: Invalid agent ID

### System Errors

- `SYS_001`: Configuration error
- `SYS_002`: Permission denied
- `SYS_003`: Resource exhausted
- `SYS_004`: Component unhealthy

---

## Rate Limits

### Queue Operations

- **send_command**: 1000 req/second per agent
- **broadcast**: 100 req/second
- **create_task_chain**: 100 req/second

### Monitoring

- **metrics collection**: Updated every 10 seconds
- **health checks**: Cached for 30 seconds

---

## WebSocket Events

### Event Types

```javascript
// Agent status update
{
    "type": "agent_status",
    "agent_id": "supervisor",
    "status": "active",
    "timestamp": 1234567890
}

// Task completion
{
    "type": "task_complete",
    "task_id": "task_123",
    "agent_id": "backend-api",
    "status": "success",
    "duration": 45.3
}

// System alert
{
    "type": "system_alert",
    "severity": "warning",
    "message": "High queue depth detected",
    "component": "queue"
}
```

### Subscribing to Events

```python
# Example WebSocket client
import websocket

def on_message(ws, message):
    data = json.loads(message)
    if data['type'] == 'agent_status':
        print(f"Agent {data['agent_id']} is {data['status']}")

ws = websocket.WebSocketApp(
    "ws://localhost:8501/ws",
    on_message=on_message
)
ws.run_forever()
```

---

## Best Practices

1. **Always use task IDs** for tracking long-running operations
2. **Set appropriate timeouts** for agent commands
3. **Handle retries** at the application level
4. **Monitor queue depth** to prevent overload
5. **Use health checks** before critical operations
6. **Implement circuit breakers** for failing agents
7. **Log all errors** with context for debugging

---

## Support

For API questions or issues:
- GitHub Issues: [Report an issue](https://github.com/yourusername/claude-multiagent-system/issues)
- Documentation: [Read more](https://github.com/yourusername/claude-multiagent-system/docs)