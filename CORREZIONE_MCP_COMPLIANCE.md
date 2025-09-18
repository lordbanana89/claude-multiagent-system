# 🚨 CORREZIONE URGENTE: MCP Compliance con SDK Ufficiale

## ❌ PROBLEMI IDENTIFICATI

### 1. **ARCHITETTURA COMPLETAMENTE SBAGLIATA**

#### ❌ ATTUALE (ERRATO):
```python
# mcp_server_v2_full.py
class MCPServerV2Full:
    def __init__(self):
        self.app = web.Application()  # ❌ aiohttp custom
```

#### ✅ CORRETTO (SDK MCP):
```python
from mcp import FastMCP
from mcp.server import Server

app = FastMCP("claude-multiagent")

@app.tool()
def heartbeat(agent: str) -> dict:
    """Agent heartbeat signal"""
    return {"status": "alive", "agent": agent}
```

### 2. **TOOL DEFINITION NON CONFORME**

#### ❌ ATTUALE (ERRATO):
```python
self.tools = {
    "heartbeat": {
        "name": "heartbeat",
        "description": "Agent heartbeat",
        "inputSchema": {...}  # Manca outputSchema!
    }
}
```

#### ✅ CORRETTO (SDK MCP):
```python
from mcp.types import Tool

Tool(
    name="heartbeat",
    description="Agent heartbeat signal",
    inputSchema={
        "type": "object",
        "properties": {
            "agent": {"type": "string"}
        },
        "required": ["agent"]
    },
    outputSchema={  # OBBLIGATORIO!
        "type": "object",
        "properties": {
            "status": {"type": "string"},
            "agent": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"}
        },
        "required": ["status", "agent", "timestamp"]
    },
    annotations={  # OBBLIGATORIO!
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
```

### 3. **ERROR HANDLING ERRATO**

#### ❌ ATTUALE (ERRATO):
```python
return {"error": "Tool not found"}  # ❌ Non standard
```

#### ✅ CORRETTO (SDK MCP):
```python
from mcp.types import McpError, ErrorCode

raise McpError(
    code=ErrorCode.METHOD_NOT_FOUND,  # Codici standard
    message=f"Tool not found: {tool_name}",
    data={"available_tools": list(self.tools.keys())}
)
```

## 📦 NUOVO SERVER MCP COMPLIANT

```python
# mcp_server_compliant.py

from mcp import FastMCP
from mcp.server import Server
from mcp.types import Tool, McpError, ErrorCode
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import uuid

# Initialize MCP app
app = FastMCP("claude-multiagent-system")

# Database connection
db = sqlite3.connect('mcp_system.db')

# Message bus (se esistente)
from core.message_bus import get_message_bus, Event, EventType
message_bus = get_message_bus()

# ===== TOOL IMPLEMENTATIONS =====

@app.tool()
def heartbeat(agent: str) -> Dict[str, Any]:
    """
    Agent heartbeat signal with full compliance.

    Args:
        agent: Agent identifier

    Returns:
        Heartbeat confirmation with timestamp
    """
    timestamp = datetime.now(timezone.utc)

    # Real database update
    cursor = db.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO agents (id, last_heartbeat, status, total_heartbeats)
        VALUES (?, ?, 'active', COALESCE((SELECT total_heartbeats FROM agents WHERE id = ?), 0) + 1)
    """, (agent, timestamp, agent))
    db.commit()

    # Publish to message bus
    message_bus.publish(Event(
        type=EventType.HEARTBEAT_RECEIVED,
        source=agent,
        payload={'timestamp': timestamp.isoformat()}
    ))

    # MCP-compliant response
    return {
        "status": "alive",
        "agent": agent,
        "timestamp": timestamp.isoformat(),
        "next_expected": (timestamp + timedelta(seconds=30)).isoformat(),
        "interval_seconds": 30,
        "_meta": {  # MCP metadata
            "processed_at": timestamp.isoformat(),
            "server_version": "2.0.0"
        }
    }

@app.tool()
def update_status(agent: str, status: str, current_task: str = None) -> Dict[str, Any]:
    """
    Update agent status with validation.

    Args:
        agent: Agent identifier
        status: New status (idle|busy|error|offline)
        current_task: Current task ID if busy

    Returns:
        Status update confirmation

    Raises:
        McpError: If status is invalid
    """
    valid_statuses = ['idle', 'busy', 'error', 'offline']

    if status not in valid_statuses:
        raise McpError(
            code=ErrorCode.INVALID_PARAMS,
            message=f"Invalid status: {status}",
            data={"valid_statuses": valid_statuses}
        )

    timestamp = datetime.now(timezone.utc)

    # Get previous status
    cursor = db.cursor()
    cursor.execute("SELECT status FROM agents WHERE id = ?", (agent,))
    result = cursor.fetchone()
    previous_status = result[0] if result else None

    # Update database
    cursor.execute("""
        UPDATE agents
        SET status = ?, current_task = ?, last_update = ?
        WHERE id = ?
    """, (status, current_task, timestamp, agent))

    # Log status change
    cursor.execute("""
        INSERT INTO agent_status_history (agent_id, status, task_id, timestamp)
        VALUES (?, ?, ?, ?)
    """, (agent, status, current_task, timestamp))

    db.commit()

    # Publish event
    message_bus.publish(Event(
        type=EventType.AGENT_STATUS_CHANGED,
        source=agent,
        payload={
            'status': status,
            'previous_status': previous_status,
            'task': current_task
        }
    ))

    return {
        "success": True,
        "agent": agent,
        "status": status,
        "previous_status": previous_status,
        "current_task": current_task,
        "timestamp": timestamp.isoformat()
    }

@app.tool()
def log_activity(agent: str, activity: str, category: str, details: Dict = None) -> Dict[str, Any]:
    """
    Log agent activity with structured data.

    Args:
        agent: Agent identifier
        activity: Activity description
        category: Activity category (task|error|info|warning)
        details: Additional structured details

    Returns:
        Activity log confirmation
    """
    activity_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc)

    # Save to database
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO activity_logs (id, agent, category, activity, details, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (activity_id, agent, category, activity, json.dumps(details or {}), timestamp))
    db.commit()

    # Critical error handling
    if category == 'error' and details and details.get('severity') == 'critical':
        # Trigger alert
        message_bus.publish(Event(
            type=EventType.CRITICAL_ERROR,
            source=agent,
            payload={
                'activity_id': activity_id,
                'error': activity,
                'details': details
            }
        ))

    return {
        "logged": True,
        "id": activity_id,
        "timestamp": timestamp.isoformat(),
        "indexed": True,
        "category": category
    }

@app.tool()
def check_conflicts(agents: list[str]) -> Dict[str, Any]:
    """
    Check for conflicts between agents.

    Args:
        agents: List of agent identifiers to check

    Returns:
        Conflict analysis result
    """
    cursor = db.cursor()

    # Find overlapping tasks
    placeholders = ','.join(['?' for _ in agents])
    cursor.execute(f"""
        SELECT t.component, GROUP_CONCAT(t.assigned_to) as agents
        FROM tasks t
        WHERE t.assigned_to IN ({placeholders})
        AND t.status = 'in_progress'
        GROUP BY t.component
        HAVING COUNT(DISTINCT t.assigned_to) > 1
    """, agents)

    conflicts = []
    for row in cursor.fetchall():
        conflicts.append({
            'type': 'component_conflict',
            'component': row[0],
            'agents': row[1].split(','),
            'severity': 'high'
        })

    return {
        "conflicts": conflicts,
        "agents_checked": agents,
        "has_conflicts": len(conflicts) > 0,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.tool()
def register_component(name: str, owner: str, type: str = "module", metadata: Dict = None) -> Dict[str, Any]:
    """
    Register a new component.

    Args:
        name: Component name
        owner: Owning agent identifier
        type: Component type
        metadata: Additional metadata

    Returns:
        Registration confirmation

    Raises:
        McpError: If component already exists
    """
    cursor = db.cursor()

    # Check uniqueness
    cursor.execute("SELECT id FROM components WHERE name = ?", (name,))
    if cursor.fetchone():
        raise McpError(
            code=ErrorCode.INVALID_REQUEST,
            message=f"Component already exists: {name}"
        )

    component_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc)

    # Register component
    cursor.execute("""
        INSERT INTO components (id, name, type, owner, created_at, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (component_id, name, type, owner, timestamp, json.dumps(metadata or {})))
    db.commit()

    return {
        "registered": True,
        "component_id": component_id,
        "name": name,
        "owner": owner,
        "type": type,
        "timestamp": timestamp.isoformat()
    }

@app.tool()
def request_collaboration(from_agent: str, to_agent: str, task: str, priority: str = "normal") -> Dict[str, Any]:
    """
    Request collaboration between agents.

    Args:
        from_agent: Requesting agent
        to_agent: Target agent
        task: Task description
        priority: Task priority (low|normal|high|critical)

    Returns:
        Collaboration request confirmation
    """
    request_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc)

    # Check target agent status
    cursor = db.cursor()
    cursor.execute("SELECT status FROM agents WHERE id = ?", (to_agent,))
    result = cursor.fetchone()

    if not result:
        raise McpError(
            code=ErrorCode.INVALID_REQUEST,
            message=f"Agent not found: {to_agent}"
        )

    target_status = result[0]

    # Create collaboration request
    cursor.execute("""
        INSERT INTO collaboration_requests (id, from_agent, to_agent, task, priority, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (request_id, from_agent, to_agent, task, priority,
          'accepted' if target_status == 'idle' else 'queued', timestamp))
    db.commit()

    # Publish event
    message_bus.publish(Event(
        type=EventType.COLLABORATION_REQUEST,
        source=from_agent,
        target=to_agent,
        payload={
            'request_id': request_id,
            'task': task,
            'priority': priority
        }
    ))

    return {
        "request_id": request_id,
        "status": 'accepted' if target_status == 'idle' else 'queued',
        "from": from_agent,
        "to": to_agent,
        "priority": priority,
        "timestamp": timestamp.isoformat()
    }

@app.tool()
def propose_decision(agent: str, decision: str, category: str, confidence: float, alternatives: list = None) -> Dict[str, Any]:
    """
    Propose a decision for voting.

    Args:
        agent: Proposing agent
        decision: Decision description
        category: Decision category
        confidence: Confidence level (0.0-1.0)
        alternatives: Alternative options

    Returns:
        Decision proposal confirmation
    """
    if not 0 <= confidence <= 1:
        raise McpError(
            code=ErrorCode.INVALID_PARAMS,
            message="Confidence must be between 0 and 1"
        )

    decision_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc)

    # Auto-approve high confidence low risk
    auto_approved = confidence >= 0.95 and category != 'critical'

    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO decisions (id, proposed_by, decision, category, confidence, alternatives, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (decision_id, agent, decision, category, confidence,
          json.dumps(alternatives or []),
          'auto_approved' if auto_approved else 'proposed',
          timestamp))
    db.commit()

    return {
        "decision_id": decision_id,
        "status": 'auto_approved' if auto_approved else 'proposed',
        "category": category,
        "confidence": confidence,
        "auto_approved": auto_approved,
        "timestamp": timestamp.isoformat()
    }

@app.tool()
def find_component_owner(component: str) -> Dict[str, Any]:
    """
    Find owner of a component.

    Args:
        component: Component name or ID

    Returns:
        Component ownership information
    """
    cursor = db.cursor()

    # Search by name or ID
    cursor.execute("""
        SELECT c.owner, c.type, c.status, a.status as agent_status
        FROM components c
        LEFT JOIN agents a ON c.owner = a.id
        WHERE c.name = ? OR c.id = ?
    """, (component, component))

    result = cursor.fetchone()

    if result:
        return {
            "component": component,
            "owner": result[0],
            "type": result[1],
            "component_status": result[2],
            "agent_status": result[3],
            "found": True
        }
    else:
        # Try pattern matching
        import re
        patterns = {
            r'.*\.(jsx?|tsx?)$': 'frontend-ui',
            r'.*\.(py|api)$': 'backend-api',
            r'.*\.(sql|db)$': 'database',
            r'.*test.*': 'testing'
        }

        for pattern, default_owner in patterns.items():
            if re.match(pattern, component):
                return {
                    "component": component,
                    "owner": default_owner,
                    "type": "inferred",
                    "found": False,
                    "inferred": True
                }

        return {
            "component": component,
            "owner": "supervisor",
            "type": "unknown",
            "found": False,
            "inferred": False
        }

# ===== RESOURCE HANDLERS =====

@app.resource("file://agents/{agent_id}/logs")
def read_agent_logs(agent_id: str) -> str:
    """Read agent logs"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT timestamp, category, activity, details
        FROM activity_logs
        WHERE agent = ?
        ORDER BY timestamp DESC
        LIMIT 100
    """, (agent_id,))

    logs = []
    for row in cursor.fetchall():
        logs.append({
            "timestamp": row[0],
            "category": row[1],
            "activity": row[2],
            "details": json.loads(row[3])
        })

    return json.dumps(logs, indent=2)

# ===== PROMPT TEMPLATES =====

@app.prompt("collaboration_request")
def collaboration_prompt(from_agent: str, to_agent: str, task: str) -> str:
    """Generate collaboration request prompt"""
    return f"""
    Agent {from_agent} is requesting collaboration from {to_agent}.

    Task: {task}

    Please respond with:
    - ACCEPT: I can help with this task
    - DEFER: I'm busy but can help later
    - REJECT: I cannot help with this task

    Provide reasoning for your response.
    """

# ===== SERVER INITIALIZATION =====

def initialize_database():
    """Create database schema"""
    cursor = db.cursor()

    # Agents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            status TEXT DEFAULT 'offline',
            last_heartbeat TIMESTAMP,
            last_update TIMESTAMP,
            current_task TEXT,
            total_heartbeats INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0
        )
    """)

    # Activity logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id TEXT PRIMARY KEY,
            agent TEXT,
            category TEXT,
            activity TEXT,
            details TEXT,
            timestamp TIMESTAMP
        )
    """)

    # Components
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS components (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE,
            type TEXT,
            owner TEXT,
            created_at TIMESTAMP,
            status TEXT DEFAULT 'active',
            metadata TEXT
        )
    """)

    # Tasks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            component TEXT,
            assigned_to TEXT,
            status TEXT,
            created_at TIMESTAMP
        )
    """)

    # Collaboration requests
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS collaboration_requests (
            id TEXT PRIMARY KEY,
            from_agent TEXT,
            to_agent TEXT,
            task TEXT,
            priority TEXT,
            status TEXT,
            created_at TIMESTAMP
        )
    """)

    # Decisions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id TEXT PRIMARY KEY,
            proposed_by TEXT,
            decision TEXT,
            category TEXT,
            confidence REAL,
            alternatives TEXT,
            status TEXT,
            created_at TIMESTAMP
        )
    """)

    # Agent status history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT,
            status TEXT,
            task_id TEXT,
            timestamp TIMESTAMP
        )
    """)

    db.commit()

# Initialize on startup
initialize_database()

# ===== RUN SERVER =====

if __name__ == "__main__":
    import uvicorn

    # Create ASGI app
    server = Server()
    app.register_server(server)

    # Run with uvicorn
    uvicorn.run(
        app.get_asgi_app(),
        host="0.0.0.0",
        port=8099,
        log_level="info"
    )
```

## 🔧 MODIFICHE RICHIESTE

### 1. **Installare SDK MCP**
```bash
pip install mcp
```

### 2. **Sostituire il server**
- Eliminare `mcp_server_v2_full.py`
- Usare `mcp_server_compliant.py`

### 3. **Aggiornare tutti i client**
```python
# Invece di chiamate JSON-RPC custom
response = await mcp_client.call_tool(
    "heartbeat",
    {"agent": "backend-api"}
)
```

### 4. **Validazione Schema**
Tutti i tool DEVONO avere:
- `inputSchema` completo
- `outputSchema` completo
- `annotations` per hints
- Error handling con `McpError`

## ⚠️ IMPATTO

**Senza queste correzioni**:
- ❌ Non compatibile con client MCP standard
- ❌ Non interoperabile con altri sistemi MCP
- ❌ Validazione schema non funziona
- ❌ Error handling non standard

**Con le correzioni**:
- ✅ Full compliance MCP 2024-11-05
- ✅ Interoperabile con qualsiasi client MCP
- ✅ Type safety e validation automatica
- ✅ Error handling standard

## 📊 TEMPO STIMATO

- **Riscrittura server**: 8 ore
- **Migrazione tool**: 6 ore
- **Testing compliance**: 4 ore
- **Update client**: 4 ore

**TOTALE: 22 ore** per full compliance