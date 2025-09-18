# Current MCP API Documentation

## Overview
The current MCP API Server runs on port 8099 and provides REST endpoints for monitoring and managing the multi-agent system. This documentation captures the state before MCP v2 migration.

## Endpoints

### 1. GET /api/mcp/status
**Purpose**: Get complete MCP system status with caching

**Response Format**:
```json
{
  "status": "operational",
  "agents": [
    {
      "agent": "supervisor",
      "last_seen": "2024-09-18T10:30:00",
      "status": "active",
      "current_task": "Coordinating inbox system"
    }
  ],
  "activities": [
    {
      "id": 1,
      "agent": "backend-api",
      "timestamp": "2024-09-18T10:30:00",
      "activity": "Processing request",
      "category": "task",
      "status": "completed"
    }
  ],
  "components": [
    {
      "name": "inbox_api",
      "owner": "backend-api",
      "status": "active",
      "last_updated": "2024-09-18T10:30:00"
    }
  ],
  "pending_decisions": [
    {
      "id": 1,
      "category": "architecture",
      "question": "Database schema design",
      "proposed_by": "database",
      "timestamp": "2024-09-18T10:30:00"
    }
  ],
  "recent_conflicts": [],
  "system_stats": {
    "total_activities": 100,
    "active_agents": 5,
    "registered_components": 10,
    "pending_decisions": 2
  }
}
```

**Cache**: 10 seconds TTL
**Rate Limit**: 10 requests per second

### 2. GET /api/mcp/activities
**Purpose**: Get detailed activity log with pagination and filtering

**Query Parameters**:
- `limit` (int): Number of activities to return (default: 50, max: 100)
- `offset` (int): Pagination offset (default: 0)
- `agent` (string): Filter by agent name
- `category` (string): Filter by activity category

**Response Format**:
```json
{
  "activities": [
    {
      "id": 1,
      "agent": "backend-api",
      "timestamp": "2024-09-18T10:30:00",
      "activity": "Processing API request",
      "category": "task",
      "status": "completed",
      "details": {}
    }
  ],
  "total": 1000,
  "limit": 50,
  "offset": 0,
  "has_more": true
}
```

**Cache**: 5 seconds TTL
**Rate Limit**: 10 requests per second

### 3. POST /api/mcp/start-terminal
**Purpose**: Start tmux terminal sessions for agents

**Request Body**:
```json
{
  "session": "supervisor",
  "split": true
}
```

**Supported Sessions**:
- supervisor
- backend-api
- database
- frontend-ui
- testing
- instagram
- queue-manager
- deployment
- master

**Response Format**:
```json
{
  "status": "success",
  "session": "supervisor",
  "message": "Terminal session started successfully"
}
```

**Error Response**:
```json
{
  "error": "Session already exists: supervisor"
}
```

### 4. GET /api/mcp/health
**Purpose**: Simple health check endpoint

**Response Format**:
```json
{
  "status": "healthy"
}
```

### 5. GET /api/mcp/ws-config
**Purpose**: Get WebSocket configuration for real-time updates

**Response Format**:
```json
{
  "ws_enabled": false,
  "ws_url": null,
  "polling_interval": 5000
}
```

## Database Tables

### activities
- id (INTEGER PRIMARY KEY)
- agent (TEXT)
- timestamp (TEXT)
- activity (TEXT)
- category (TEXT)
- status (TEXT)
- details (TEXT JSON)

### agent_states
- agent (TEXT PRIMARY KEY)
- last_seen (TEXT)
- status (TEXT)
- current_task (TEXT)
- metadata (TEXT JSON)

### components
- name (TEXT PRIMARY KEY)
- owner (TEXT)
- status (TEXT)
- last_updated (TEXT)
- metadata (TEXT JSON)

### conflicts
- id (INTEGER PRIMARY KEY)
- agents (TEXT JSON array)
- issue (TEXT)
- resolved (INTEGER)
- resolution (TEXT)
- timestamp (TEXT)

### decisions
- id (INTEGER PRIMARY KEY)
- category (TEXT)
- question (TEXT)
- proposed_by (TEXT)
- approved_by (TEXT JSON array)
- status (TEXT)
- timestamp (TEXT)
- metadata (TEXT JSON)

## Common Response Codes

- 200: Success
- 400: Bad Request (invalid parameters)
- 429: Rate Limit Exceeded
- 500: Internal Server Error

## Caching Strategy

- Status endpoint: 10 second TTL (frequently polled)
- Activities endpoint: 5 second TTL
- In-memory cache with timestamp-based expiration
- Cache key includes endpoint and parameters

## Rate Limiting

- 10 requests per second per endpoint per IP address
- Counter resets every second
- Returns 429 status code when exceeded

## Notes

1. All timestamps are in ISO 8601 format
2. Database uses SQLite at `/tmp/mcp_state.db`
3. No authentication currently implemented
4. CORS is enabled for all origins
5. No WebSocket support currently (polling only)
6. Pattern matching in `mcp_bridge.py` handles agent communication
7. No JSON-RPC protocol support
8. No MCP v2 primitives (Tools, Resources, Prompts)