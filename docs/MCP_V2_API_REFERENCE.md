# MCP v2 API Reference

## Table of Contents
1. [JSON-RPC 2.0 Methods](#json-rpc-20-methods)
2. [REST API Endpoints](#rest-api-endpoints)
3. [OAuth 2.1 Authentication](#oauth-21-authentication)
4. [WebSocket Events](#websocket-events)
5. [Error Codes](#error-codes)
6. [Examples](#examples)

## JSON-RPC 2.0 Methods

### Base URL
```
POST http://localhost:8099/jsonrpc
```

### initialize
Initialize a new MCP session with capability negotiation.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "clientInfo": {
      "name": "Your Client",
      "version": "1.0.0"
    },
    "capabilities": ["tools", "resources", "prompts"]
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocol_version": "2025-06-18",
    "session_id": "uuid",
    "capabilities": {
      "protocol_version": "2025-06-18",
      "supports": ["tools", "resources", "prompts"],
      "features": {
        "idempotency": true,
        "dry_run": true,
        "streaming": false,
        "batch": false
      }
    },
    "tools_count": 8,
    "resources_count": 4,
    "prompts_count": 3
  },
  "id": 1
}
```

### tools/list
List all available tools with their schemas.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "params": {},
  "id": 2
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": [
    {
      "name": "log_activity",
      "description": "Log an activity for an agent",
      "inputSchema": {
        "type": "object",
        "properties": {
          "agent": {"type": "string"},
          "activity": {"type": "string"},
          "category": {"type": "string", "enum": ["task", "communication", "decision", "error"]},
          "status": {"type": "string", "enum": ["started", "in_progress", "completed", "failed"]},
          "dry_run": {"type": "boolean", "default": false}
        },
        "required": ["agent", "activity", "category"]
      }
    }
  ],
  "id": 2
}
```

### tools/call
Execute a tool with the specified arguments.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "log_activity",
    "arguments": {
      "agent": "backend-api",
      "activity": "Processing request",
      "category": "task",
      "status": "completed",
      "dry_run": false
    }
  },
  "id": 3
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "id": 123,
    "message": "Activity logged successfully"
  },
  "id": 3
}
```

### resources/list
List all available resources.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "resources/list",
  "params": {},
  "id": 4
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": [
    {
      "uri": "file://README.md",
      "name": "Project README",
      "type": "text/markdown",
      "description": "Main project documentation"
    },
    {
      "uri": "db://schema/complete",
      "name": "Database Schema",
      "type": "application/json",
      "description": "Complete database schema definition"
    }
  ],
  "id": 4
}
```

### resources/read
Read the content of a specific resource.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "resources/read",
  "params": {
    "uri": "db://schema/complete"
  },
  "id": 5
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "uri": "db://schema/complete",
    "content": {
      "tables": ["activities", "agent_states", "components", "conflicts", "decisions"]
    },
    "metadata": {
      "uri": "db://schema/complete",
      "name": "Database Schema",
      "type": "application/json"
    }
  },
  "id": 5
}
```

### prompts/list
List all available prompt templates.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "prompts/list",
  "params": {},
  "id": 6
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": [
    {
      "name": "deploy_system",
      "description": "Deploy the multi-agent system",
      "arguments": [
        {"name": "environment", "type": "string", "required": true},
        {"name": "version", "type": "string", "required": false}
      ],
      "template": "Deploy multi-agent system to {environment} environment{version}"
    }
  ],
  "id": 6
}
```

### prompts/execute
Execute a prompt template with arguments.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "prompts/execute",
  "params": {
    "name": "deploy_system",
    "arguments": {
      "environment": "production",
      "version": "v2.0.0"
    }
  },
  "id": 7
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "prompt": "deploy_system",
    "result": "Deploy multi-agent system to production environmentv2.0.0",
    "executed_at": "2025-09-18T10:00:00Z"
  },
  "id": 7
}
```

## REST API Endpoints

### GET /api/mcp/status
Get the complete MCP system status.

**Response:**
```json
{
  "status": "operational",
  "mcp_version": "2025-06-18",
  "capabilities": {
    "protocol_version": "2025-06-18",
    "supports": ["tools", "resources", "prompts"],
    "features": {
      "idempotency": true,
      "dry_run": true,
      "streaming": false,
      "batch": false
    }
  },
  "agents": [],
  "activities": [],
  "system_stats": {
    "total_activities": 100,
    "active_agents": 5,
    "tools_available": 8,
    "resources_available": 4,
    "prompts_available": 3
  }
}
```

### GET /api/mcp/health
Simple health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "2025-06-18"
}
```

### GET /api/mcp/resources
List all available resources.

**Response:**
```json
{
  "resources": [
    {
      "uri": "file://README.md",
      "name": "Project README",
      "type": "text/markdown",
      "description": "Main project documentation"
    }
  ]
}
```

### GET /api/mcp/prompts
List all available prompts.

**Response:**
```json
{
  "prompts": [
    {
      "name": "deploy_system",
      "description": "Deploy the multi-agent system",
      "arguments": [
        {"name": "environment", "type": "string", "required": true}
      ],
      "template": "Deploy multi-agent system to {environment} environment"
    }
  ]
}
```

### GET /api/mcp/capabilities
Get current session capabilities.

**Response:**
```json
{
  "protocol_version": "2025-06-18",
  "supports": ["tools", "resources", "prompts"],
  "features": {
    "idempotency": true,
    "dry_run": true,
    "streaming": false,
    "batch": false
  }
}
```

### GET /api/mcp/security
Get security status and policies.

**Response:**
```json
{
  "security": {
    "oauth_enabled": true,
    "consent_flow": true,
    "path_protection": true,
    "rate_limiting": true,
    "audit_logging": true,
    "dangerous_operations": ["delete", "drop", "remove", "destroy"]
  },
  "policies": {
    "token_expiry_hours": 24,
    "consent_expiry_minutes": 30,
    "rate_limit_per_minute": 100,
    "path_blacklist": [".git", ".env", "id_rsa", ".ssh"]
  }
}
```

### GET /api/mcp/audit
Retrieve audit logs.

**Query Parameters:**
- `session_id` (optional): Filter by session
- `limit` (optional): Number of logs to return (default: 100)

**Response:**
```json
{
  "logs": [
    {
      "id": 1,
      "timestamp": 1758202578,
      "session_id": "uuid",
      "operation": "tools/call",
      "resource": "log_activity",
      "result": "success",
      "ip_address": "127.0.0.1",
      "request_id": "uuid"
    }
  ],
  "count": 1,
  "limit": 100
}
```

## OAuth 2.1 Authentication

### POST /oauth/token
Request an access token.

**Request:**
```json
{
  "grant_type": "client_credentials",
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "scope": "read write execute"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "scope": "read write execute",
  "refresh_token": "optional_refresh_token"
}
```

### Using the Token
Include the token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

## WebSocket Events

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8099/ws');
```

### Event Types

#### tool_executed
Fired when a tool is executed.
```json
{
  "event": "tool_executed",
  "data": {
    "tool": "log_activity",
    "result": "success",
    "timestamp": "2025-09-18T10:00:00Z"
  }
}
```

#### resource_updated
Fired when a resource is updated.
```json
{
  "event": "resource_updated",
  "data": {
    "uri": "file://README.md",
    "action": "modified",
    "timestamp": "2025-09-18T10:00:00Z"
  }
}
```

#### prompt_used
Fired when a prompt is executed.
```json
{
  "event": "prompt_used",
  "data": {
    "prompt": "deploy_system",
    "arguments": {"environment": "production"},
    "timestamp": "2025-09-18T10:00:00Z"
  }
}
```

## Error Codes

### JSON-RPC Error Codes
- `-32700`: Parse error
- `-32600`: Invalid Request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error
- `-32000`: Server error
- `-32001`: Unauthorized
- `-32002`: Rate limit exceeded
- `-32003`: Consent required
- `-32004`: Access denied

### HTTP Status Codes
- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `429`: Too Many Requests
- `500`: Internal Server Error

## Examples

### Python Client Example
```python
import requests
import json

# Initialize session
def initialize_mcp():
    response = requests.post('http://localhost:8099/jsonrpc', json={
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "clientInfo": {"name": "Python Client", "version": "1.0"},
            "capabilities": ["tools", "resources", "prompts"]
        },
        "id": 1
    })
    return response.json()

# Execute a tool
def execute_tool(tool_name, arguments):
    response = requests.post('http://localhost:8099/jsonrpc', json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": 2
    })
    return response.json()

# Example usage
session = initialize_mcp()
print(f"Session ID: {session['result']['session_id']}")

result = execute_tool("log_activity", {
    "agent": "python_client",
    "activity": "Testing MCP",
    "category": "task",
    "status": "completed"
})
print(f"Tool result: {result['result']}")
```

### JavaScript Client Example
```javascript
// Initialize MCP session
async function initializeMCP() {
  const response = await fetch('http://localhost:8099/jsonrpc', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'initialize',
      params: {
        clientInfo: { name: 'JS Client', version: '1.0' },
        capabilities: ['tools', 'resources', 'prompts']
      },
      id: 1
    })
  });
  return response.json();
}

// Execute a tool
async function executeTool(toolName, args) {
  const response = await fetch('http://localhost:8099/jsonrpc', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'tools/call',
      params: { name: toolName, arguments: args },
      id: 2
    })
  });
  return response.json();
}

// Example usage
initializeMCP().then(session => {
  console.log('Session ID:', session.result.session_id);

  return executeTool('log_activity', {
    agent: 'js_client',
    activity: 'Testing MCP',
    category: 'task',
    status: 'completed'
  });
}).then(result => {
  console.log('Tool result:', result.result);
});
```

### cURL Examples
```bash
# Initialize session
curl -X POST http://localhost:8099/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "clientInfo": {"name": "curl", "version": "1.0"},
      "capabilities": ["tools", "resources", "prompts"]
    },
    "id": 1
  }'

# List tools
curl -X POST http://localhost:8099/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2}'

# Execute tool with dry_run
curl -X POST http://localhost:8099/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "log_activity",
      "arguments": {
        "agent": "test",
        "activity": "Test activity",
        "category": "task",
        "dry_run": true
      }
    },
    "id": 3
  }'

# Get OAuth token
curl -X POST http://localhost:8099/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "client_credentials",
    "client_id": "test_client",
    "client_secret": "test_secret",
    "scope": "read write execute"
  }'

# Use token in request
curl -X POST http://localhost:8099/jsonrpc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 4}'
```

### Idempotency Example
```bash
# Make request with idempotency key
curl -X POST http://localhost:8099/jsonrpc \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: unique-key-123" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "log_activity",
      "arguments": {
        "agent": "test",
        "activity": "Idempotent operation",
        "category": "task"
      }
    },
    "id": 5
  }'

# Repeat with same key - returns cached result
curl -X POST http://localhost:8099/jsonrpc \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: unique-key-123" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "log_activity",
      "arguments": {
        "agent": "test",
        "activity": "Different operation",
        "category": "task"
      }
    },
    "id": 6
  }'
```

## Rate Limiting

Requests are limited to 100 per minute per session/IP. When rate limit is exceeded:

**Response:**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32002,
    "message": "Rate limit exceeded",
    "data": {
      "retry_after": 30,
      "limit": 100,
      "remaining": 0,
      "reset": 1758202678
    }
  },
  "id": null
}
```

## Path Protection

File resources are protected against:
- Path traversal (../)
- Access outside project directory
- Blacklisted patterns (.git, .env, keys, etc.)

**Blocked Request Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "resources/read",
  "params": {
    "uri": "file://../../etc/passwd"
  },
  "id": 7
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32004,
    "message": "Access denied: Path outside project directory",
    "data": {
      "uri": "file://../../etc/passwd",
      "reason": "path_traversal_attempt"
    }
  },
  "id": 7
}
```

## Consent Flow

Dangerous operations require explicit consent:

**Request triggering consent:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "delete_all_data",
    "arguments": {}
  },
  "id": 8
}
```

**Response requiring consent:**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32003,
    "message": "Consent required for delete_all_data",
    "data": {
      "consent_id": "consent-uuid",
      "consent_url": "/api/mcp/consent/consent-uuid",
      "operation": "delete_all_data",
      "expires_at": "2025-09-18T10:30:00Z"
    }
  },
  "id": 8
}
```

**Grant consent:**
```bash
curl -X POST http://localhost:8099/api/mcp/consent/consent-uuid \
  -H "Content-Type: application/json" \
  -d '{"decision": "approved", "reason": "User authorized"}'
```