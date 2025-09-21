# MCP Server V2 Documentation

## Overview
MCP Server V2 is a complete rewrite following the official Model Context Protocol Python SDK standards.
It provides persistent state management and verification tools specifically designed to help Claude maintain consistency when working with frontend code.

## Key Features

### 1. Frontend State Management
- **Track Components**: Monitor React components for changes
- **Verify Modifications**: Check if files have been modified since last tracked
- **Configuration Persistence**: Remember component configurations across sessions

### 2. Agent Coordination
- **Agent Lifecycle**: Initialize, heartbeat, status tracking
- **Inter-agent Communication**: Message passing between agents
- **Activity Logging**: Track all agent activities

### 3. API Testing
- **Endpoint Verification**: Test API endpoints directly
- **Response Validation**: Verify expected response structure

## Available Tools

### Frontend Management Tools

#### `track_frontend_component`
Track a frontend component for changes.
```json
{
  "name": "MultiTerminal",
  "file_path": "/path/to/component.tsx",
  "config": {
    "api_url": "http://localhost:5001",
    "polling_interval": 10000
  }
}
```

#### `verify_frontend_component`
Check if a component has been modified.
```json
{
  "name": "MultiTerminal"
}
```

#### `verify_all_frontend`
Verify all tracked frontend components at once.

#### `test_api_endpoint`
Test an API endpoint.
```json
{
  "url": "http://localhost:5001/api/mcp/status",
  "method": "GET"
}
```

### Agent Coordination Tools

#### `init_agent`
Initialize an agent in the system.
```json
{
  "agent": "supervisor"
}
```

#### `heartbeat`
Send heartbeat from an agent.
```json
{
  "agent": "supervisor"
}
```

#### `log_activity`
Log an agent activity.
```json
{
  "agent": "backend-api",
  "activity": "Created authentication endpoint",
  "category": "implementation"
}
```

#### `get_agent_status`
Get status of agents.
```json
{
  "agent": "backend-api"  // Optional, omit for all agents
}
```

#### `send_message`
Send message between agents.
```json
{
  "from_agent": "supervisor",
  "to_agent": "backend-api",
  "message": "Please implement login endpoint"
}
```

#### `read_inbox`
Read messages for an agent.
```json
{
  "agent": "backend-api"
}
```

## Resources

### `mcp://frontend/status`
Current status of all tracked frontend components.

### `mcp://agents/status`
Status of all agents in the system.

### `mcp://system/config`
Current system configuration.

## Database Schema

### `frontend_components`
- `name`: Component name (PRIMARY KEY)
- `file_path`: Path to component file
- `file_hash`: MD5 hash of file contents
- `config`: JSON configuration
- `last_modified`: Last modification timestamp
- `status`: Component status

### `api_endpoints`
- `name`: Endpoint name (PRIMARY KEY)
- `url`: Endpoint URL
- `method`: HTTP method
- `expected_structure`: Expected response structure
- `last_verified`: Last verification timestamp
- `status`: Endpoint status

### `config_snapshots`
- `id`: Snapshot ID
- `name`: Snapshot name
- `timestamp`: Creation time
- `components`: Component states
- `endpoints`: Endpoint states
- `is_working`: Whether this configuration works

## Installation

1. Install dependencies:
```bash
pip install mcp
```

2. Configure Claude Desktop:
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "claude-multiagent": {
      "command": "python3",
      "args": ["/path/to/mcp_server_v2.py"]
    }
  }
}
```

3. Run the server:
```bash
python3 mcp_server_v2.py
```

## Usage Example

When Claude needs to modify frontend code:

1. **Track the component first**:
   - Use `track_frontend_component` to record current state
   - This creates a baseline for detecting changes

2. **Make modifications**:
   - Edit the component as needed
   - MCP maintains awareness of what was changed

3. **Verify changes**:
   - Use `verify_frontend_component` to check modifications
   - Ensures changes are intentional and consistent

4. **Test the system**:
   - Use `test_api_endpoint` to verify API connections
   - Use `get_agent_status` to check system health

## Benefits

1. **Persistent Memory**: Claude remembers what was modified across sessions
2. **Change Detection**: Automatically detects when files have been modified
3. **Configuration Tracking**: Maintains component configurations
4. **Consistency Verification**: Ensures frontend and backend remain aligned
5. **Rollback Capability**: Can identify last known working configuration

## Troubleshooting

### Server not connecting
- Check Python path in configuration
- Ensure mcp package is installed
- Check logs in `/tmp/mcp_coordinator.log`

### Tools not working
- Verify database file `mcp_system.db` exists
- Check file permissions
- Ensure paths are absolute, not relative

### Frontend tracking issues
- Verify file paths are correct
- Check that files exist and are readable
- Ensure component names are unique

## Next Steps

1. **Snapshot System**: Implement configuration snapshots for rollback
2. **Dependency Tracking**: Track dependencies between components
3. **Auto-verification**: Automatic verification on file changes
4. **Integration Tests**: Automated testing of component interactions
5. **Visual Diff**: Show exact changes between versions