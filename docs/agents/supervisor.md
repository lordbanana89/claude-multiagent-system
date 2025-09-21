# Supervisor Agent

## Role and Responsibilities

The Supervisor Agent serves as the tactical coordinator for the multi-agent system, managing task delegation and workflow orchestration across all specialized agents.

### Primary Functions
- Task decomposition and delegation
- Workflow coordination and monitoring
- Resource allocation and prioritization
- Inter-agent communication facilitation
- Progress tracking and reporting

## Capabilities

### Task Management
- Receives complex, multi-domain tasks
- Breaks down tasks into specialized subtasks
- Assigns tasks to appropriate agents based on expertise
- Monitors task progress and dependencies
- Ensures task completion and quality

### Coordination Patterns
- **Sequential Processing**: Tasks executed in order
- **Parallel Processing**: Multiple agents work simultaneously
- **Pipeline Processing**: Output from one agent feeds another
- **Consensus Building**: Multiple agents collaborate on decisions

## Interaction Protocol

### Command Interface

```bash
# Direct task delegation
python3 supervisor_agent.py delegate "<task_description>" <agent_name>

# Quick task assignment
python3 quick_task.py "<task_description>" <agent_name>

# Complete current task
python3 complete_task.py "<completion_message>"

# Status check
python3 supervisor_agent.py status
```

### Message Format

```json
{
  "type": "task_delegation",
  "from": "supervisor",
  "to": "backend-api",
  "task": {
    "id": "task_123",
    "description": "Implement user authentication API",
    "priority": "high",
    "dependencies": ["database_schema"],
    "deadline": "2025-01-20T10:00:00Z"
  }
}
```

## Agent Network

The Supervisor coordinates with:

| Agent | Delegation Criteria | Common Tasks |
|-------|-------------------|--------------|
| Backend API | Server-side logic, APIs | REST endpoints, business logic |
| Database | Data persistence | Schema design, optimization |
| Frontend UI | User interfaces | React components, UX design |
| Testing | Quality assurance | Unit tests, integration tests |
| Queue Manager | Async processing | Task queuing, scheduling |
| Instagram | Social media | Content automation, APIs |
| Deployment | Production ops | CI/CD, monitoring |

## Workflow Examples

### Example 1: Full-Stack Feature

```
User Request: "Add user profile feature"
↓
Supervisor Analysis:
1. Database schema needed
2. API endpoints required
3. Frontend UI components
4. Tests for all layers
↓
Task Delegation:
- database: Create profile schema
- backend-api: Implement CRUD API
- frontend-ui: Build profile components
- testing: Write test suite
```

### Example 2: Bug Fix Coordination

```
Bug Report: "Login failing for mobile users"
↓
Supervisor Analysis:
1. Investigate frontend issue
2. Check API responses
3. Verify database queries
↓
Task Delegation:
- frontend-ui: Debug mobile viewport
- backend-api: Check auth endpoints
- testing: Add mobile test cases
```

## Configuration

### Environment Variables

```bash
SUPERVISOR_PORT=8089
SUPERVISOR_SESSION=claude-supervisor
MAX_CONCURRENT_TASKS=5
TASK_TIMEOUT=3600
AUTO_DELEGATE=true
```

### Priority Levels

1. **Critical**: System failures, security issues
2. **High**: User-facing features, production bugs
3. **Medium**: Enhancements, optimizations
4. **Low**: Documentation, refactoring

## Monitoring

### Metrics Tracked
- Tasks delegated per hour
- Average task completion time
- Agent utilization rates
- Task success/failure rates
- Queue depth and wait times

### Health Checks

```python
# Check supervisor status
curl http://localhost:8089/health

# Get active tasks
curl http://localhost:8089/tasks/active

# View delegation history
curl http://localhost:8089/history
```

## Best Practices

1. **Clear Task Definition**: Provide specific, measurable objectives
2. **Appropriate Delegation**: Match tasks to agent expertise
3. **Dependency Management**: Ensure prerequisites are met
4. **Progress Monitoring**: Regular status checks
5. **Failure Handling**: Have contingency plans

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Tasks not delegating | Agent offline | Check TMUX sessions |
| Slow response | Queue overload | Increase worker capacity |
| Failed tasks | Missing dependencies | Verify prerequisites |
| Communication errors | MCP server down | Restart MCP service |

### Debug Commands

```bash
# View supervisor logs
tmux attach -t claude-supervisor

# Check task queue
sqlite3 mcp_system.db "SELECT * FROM tasks WHERE status='pending';"

# Reset supervisor state
tmux send-keys -t claude-supervisor "reset_state()" Enter
```