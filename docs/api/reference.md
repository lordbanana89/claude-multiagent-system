# API Reference

## Base URLs

- **Health API**: `http://localhost:5001`
- **Auth API**: `http://localhost:5002`
- **Routes API**: `http://localhost:5003`
- **Complete Auth**: `http://localhost:5004`
- **MCP Server**: `http://localhost:9999`

## Authentication

All API endpoints require JWT authentication except health checks.

### Get Token

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  }
}
```

### Use Token

```http
Authorization: Bearer <token>
```

## Core Endpoints

### System Health

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime": 3600,
  "services": {
    "database": "connected",
    "redis": "connected",
    "mcp": "active"
  }
}
```

### Agent Management

#### List Agents

```http
GET /api/agents
```

**Response:**
```json
{
  "agents": [
    {
      "id": "supervisor",
      "name": "Supervisor Agent",
      "status": "active",
      "port": 8089,
      "session": "claude-supervisor",
      "last_heartbeat": "2025-01-19T10:00:00Z"
    }
  ]
}
```

#### Get Agent Status

```http
GET /api/agents/{agent_id}/status
```

**Response:**
```json
{
  "id": "backend-api",
  "status": "active",
  "current_task": "Implementing user API",
  "cpu_usage": 15.2,
  "memory_usage": 256,
  "tasks_completed": 42
}
```

#### Send Message to Agent

```http
POST /api/agents/{agent_id}/message
Content-Type: application/json

{
  "message": "Status report",
  "priority": "normal",
  "require_response": true
}
```

**Response:**
```json
{
  "message_id": "msg_123",
  "status": "delivered",
  "response": "Currently working on authentication module"
}
```

### Task Management

#### Create Task

```http
POST /api/tasks
Content-Type: application/json

{
  "title": "Implement user profile",
  "description": "Create user profile management system",
  "assigned_to": "backend-api",
  "priority": "high",
  "due_date": "2025-01-25T00:00:00Z"
}
```

**Response:**
```json
{
  "task_id": "task_456",
  "status": "created",
  "assigned_to": "backend-api",
  "created_at": "2025-01-19T10:00:00Z"
}
```

#### Get Task Status

```http
GET /api/tasks/{task_id}
```

**Response:**
```json
{
  "id": "task_456",
  "title": "Implement user profile",
  "status": "in_progress",
  "progress": 60,
  "assigned_to": "backend-api",
  "subtasks": [
    {
      "id": "sub_1",
      "title": "Database schema",
      "status": "completed"
    }
  ]
}
```

#### Update Task

```http
PATCH /api/tasks/{task_id}
Content-Type: application/json

{
  "status": "completed",
  "completion_notes": "All tests passing"
}
```

### Message Queue

#### Send Message

```http
POST /api/messages
Content-Type: application/json

{
  "from": "supervisor",
  "to": "backend-api",
  "type": "task",
  "content": "Please implement login endpoint",
  "priority": 2
}
```

#### Get Messages

```http
GET /api/messages?agent={agent_id}&status=unread
```

**Response:**
```json
{
  "messages": [
    {
      "id": "msg_789",
      "from": "supervisor",
      "to": "backend-api",
      "content": "Task assigned",
      "timestamp": "2025-01-19T10:00:00Z",
      "read": false
    }
  ]
}
```

### Activity Logs

#### Get Activity Stream

```http
GET /api/activities?limit=50
```

**Response:**
```json
{
  "activities": [
    {
      "id": 1234,
      "agent": "backend-api",
      "action": "task_completed",
      "details": "User API implementation complete",
      "timestamp": "2025-01-19T10:00:00Z"
    }
  ]
}
```

### System Components

#### List Components

```http
GET /api/components
```

**Response:**
```json
{
  "components": [
    {
      "id": "comp_123",
      "name": "UserProfile",
      "type": "React Component",
      "created_by": "frontend-ui",
      "created_at": "2025-01-19T09:00:00Z"
    }
  ]
}
```

## WebSocket Endpoints

### Real-time Updates

```javascript
const ws = new WebSocket('ws://localhost:9999/ws');

ws.on('message', (data) => {
  const update = JSON.parse(data);
  console.log('Update:', update);
});

// Subscribe to agent updates
ws.send(JSON.stringify({
  action: 'subscribe',
  channel: 'agents'
}));
```

### Event Types

```json
{
  "type": "agent_status_change",
  "agent_id": "backend-api",
  "old_status": "idle",
  "new_status": "busy",
  "timestamp": "2025-01-19T10:00:00Z"
}
```

## Error Responses

### Standard Error Format

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Agent not found",
    "details": {
      "agent_id": "unknown-agent"
    }
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| UNAUTHORIZED | 401 | Missing or invalid token |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| VALIDATION_ERROR | 400 | Invalid request data |
| RATE_LIMITED | 429 | Too many requests |
| SERVER_ERROR | 500 | Internal server error |

## Rate Limiting

- **Default**: 100 requests per minute per IP
- **Authenticated**: 1000 requests per minute per user
- **Headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

## Pagination

```http
GET /api/tasks?page=2&limit=20
```

**Response Headers:**
```
X-Total-Count: 150
X-Page-Count: 8
Link: <http://localhost:5003/api/tasks?page=3>; rel="next"
```