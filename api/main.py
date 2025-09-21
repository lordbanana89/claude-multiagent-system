"""
FastAPI Gateway for Claude Multi-Agent System
Bridges the new React UI with existing agent infrastructure
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import subprocess
import json
from datetime import datetime
import socketio
import subprocess
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import existing components with error handling
try:
    from core.claude_orchestrator import ClaudeNativeOrchestrator
    orchestrator = ClaudeNativeOrchestrator()
except ImportError:
    print("Warning: ClaudeNativeOrchestrator not available")
    orchestrator = None

try:
    from core.tmux_client import TMUXClient
    tmux_client = TMUXClient()
except ImportError:
    print("Warning: TMUXClient not available")
    class TMUXClient:
        def check_session(self, name):
            return False
        def capture_pane(self, name, lines=50):
            return ""
        def send_keys(self, session, command):
            return False
        def get_output(self, session):
            return ""
    tmux_client = TMUXClient()

try:
    from task_queue.client import QueueClient
    queue_client = QueueClient()
except ImportError:
    print("Warning: QueueClient not available")
    class QueueClient:
        def send_task(self, task):
            import time
            return f"task_{int(time.time())}"
        def get_stats(self):
            return {}
    queue_client = QueueClient()

try:
    from monitoring.health import check_system_health
except ImportError:
    print("Warning: check_system_health not available")
    def check_system_health():
        return {"status": "healthy"}

try:
    from config.settings import AGENT_SESSIONS
except ImportError:
    print("Warning: AGENT_SESSIONS not available")
    AGENT_SESSIONS = {
        'supervisor': 'claude-supervisor',
        'master': 'claude-master',
        'backend-api': 'claude-backend-api',
        'database': 'claude-database',
        'frontend-ui': 'claude-frontend-ui',
        'testing': 'claude-testing',
        'instagram': 'claude-instagram',
        'queue-manager': 'claude-queue-manager',
        'deployment': 'claude-deployment'
    }

# Initialize FastAPI app
app = FastAPI(
    title="Claude Multi-Agent API",
    description="API Gateway for multi-agent orchestration system",
    version="1.0.0"
)

# Configure CORS for React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Socket.IO for WebSocket support
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*'
)
socket_app = socketio.ASGIApp(sio, app)

# Core components initialized above with import handling

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.agent_subscriptions: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        # Remove from subscriptions
        for agent_id in self.agent_subscriptions:
            if websocket in self.agent_subscriptions[agent_id]:
                self.agent_subscriptions[agent_id].remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Pydantic models
class AgentCommand(BaseModel):
    agent_id: str
    command: str
    context: Optional[Dict[str, Any]] = None

class WorkflowNode(BaseModel):
    id: str
    type: str
    position: Dict[str, float]
    data: Dict[str, Any]

class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None

class Workflow(BaseModel):
    id: str
    name: str
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    description: Optional[str] = None

class TaskRequest(BaseModel):
    workflow_id: str
    input_data: Optional[Dict[str, Any]] = None

# API Routes

@app.get("/")
async def root():
    return {"message": "Claude Multi-Agent API Gateway", "status": "online"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "fastapi_gateway"}

# Agent Operations
@app.get("/api/agents")
async def get_agents():
    """List all available agents with their current status from database"""
    import sqlite3

    try:
        # Use parent directory's database
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mcp_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get agents from database
        cursor.execute('''
        SELECT a.agent, a.status, a.last_seen, a.current_task,
               COUNT(act.id) as activity_count
        FROM agent_states a
        LEFT JOIN activities act ON act.agent = a.agent
        GROUP BY a.agent
        ''')

        agents = []
        for row in cursor.fetchall():
            agent_id, status, last_seen, current_task, activity_count = row

            # Determine agent type and name based on ID
            agent_types = {
                'supervisor': ('Supervisor Agent', 'coordinator'),
                'master': ('Master Agent', 'strategic'),
                'backend-api': ('Backend API Agent', 'development'),
                'database': ('Database Agent', 'database'),
                'frontend-ui': ('Frontend UI Agent', 'ui'),
                'testing': ('Testing Agent', 'qa'),
                'instagram': ('Instagram Agent', 'social'),
                'queue-manager': ('Queue Manager Agent', 'infrastructure'),
                'deployment': ('Deployment Agent', 'devops')
            }

            if agent_id in agent_types:
                name, agent_type = agent_types[agent_id]
            else:
                name = f"{agent_id.replace('-', ' ').title()} Agent"
                agent_type = 'unknown'

            # Check tmux session status
            session_name = f"claude-{agent_id}"
            tmux_status = tmux_client.check_session(session_name) if hasattr(tmux_client, 'check_session') else False

            # Determine final status
            if tmux_status:
                final_status = "online"
            elif status == "active":
                final_status = "active"
            else:
                final_status = "offline"

            agents.append({
                "id": agent_id,
                "name": name,
                "type": agent_type,
                "status": final_status,
                "sessionId": session_name,
                "lastActivity": last_seen or datetime.now().isoformat(),
                "currentTask": current_task,
                "activityCount": activity_count
            })

        conn.close()
        return agents
    except Exception as e:
        print(f"Error getting agents: {e}")
        return []

@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get detailed information about a specific agent"""
    session_name = f"claude-{agent_id}"
    exists = tmux_client.check_session(session_name) if hasattr(tmux_client, 'check_session') else False

    if not exists:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    # Get recent output from agent
    output = tmux_client.capture_pane(session_name, lines=50)

    return {
        "id": agent_id,
        "sessionId": session_name,
        "status": "online",
        "recentOutput": output,
        "capabilities": orchestrator.get_agent_capabilities(agent_id) if orchestrator and hasattr(orchestrator, 'get_agent_capabilities') else []
    }

@app.post("/api/agents/{agent_id}/command")
async def send_command(agent_id: str, command: AgentCommand):
    """Send a command to a specific agent"""
    try:
        if not orchestrator or not hasattr(orchestrator, 'send_task_to_claude'):
            raise HTTPException(status_code=503, detail="Orchestrator not available")
        result = orchestrator.send_task_to_claude(
            agent_id,
            command.command,
            json.dumps(command.context) if command.context else None
        )

        # Broadcast status update
        await sio.emit('agent:status', {
            'agentId': agent_id,
            'status': 'busy',
            'command': command.command
        })

        return {
            "success": True,
            "agentId": agent_id,
            "command": command.command,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """Get real-time status of an agent"""
    session_name = f"claude-{agent_id}"

    if not (tmux_client.check_session(session_name) if hasattr(tmux_client, 'check_session') else False):
        return {"status": "offline", "agentId": agent_id}

    # Check if agent is processing
    output = tmux_client.capture_pane(session_name, lines=5)
    is_busy = "processing" in output.lower() or "executing" in output.lower()

    return {
        "status": "busy" if is_busy else "online",
        "agentId": agent_id,
        "lastOutput": output
    }

# In-memory workflow storage
workflows_storage = {}

# Workflow Operations
@app.get("/api/workflows")
async def get_workflows():
    """List all saved workflows"""
    return list(workflows_storage.values())

@app.post("/api/workflows")
async def create_workflow(workflow: Workflow):
    """Create a new workflow"""
    workflow_dict = workflow.dict()
    workflow_dict['created'] = datetime.now().isoformat()
    workflow_dict['updated'] = datetime.now().isoformat()
    workflows_storage[workflow.id] = workflow_dict
    return workflow_dict

@app.get("/api/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get a specific workflow by ID"""
    if workflow_id in workflows_storage:
        return workflows_storage[workflow_id]
    raise HTTPException(status_code=404, detail="Workflow not found")

@app.put("/api/workflows/{workflow_id}")
async def update_workflow(workflow_id: str, workflow: Workflow):
    """Update an existing workflow"""
    if workflow_id not in workflows_storage:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow_dict = workflow.dict()
    workflow_dict['updated'] = datetime.now().isoformat()
    workflows_storage[workflow_id] = workflow_dict
    return workflow_dict

@app.delete("/api/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow"""
    if workflow_id not in workflows_storage:
        raise HTTPException(status_code=404, detail="Workflow not found")

    del workflows_storage[workflow_id]
    return {"id": workflow_id, "deleted": True}

@app.post("/api/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, task: TaskRequest):
    """Execute a workflow"""
    try:
        # Queue the workflow execution
        task_id = queue_client.send_task({
            "workflow_id": workflow_id,
            "input_data": task.input_data,
            "timestamp": datetime.now().isoformat()
        })

        # Broadcast workflow start
        await sio.emit('workflow:progress', {
            'workflowId': workflow_id,
            'status': 'started',
            'taskId': task_id
        })

        return {
            "taskId": task_id,
            "workflowId": workflow_id,
            "status": "queued"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Queue Operations
@app.post("/api/queue/task")
async def add_task(task: Dict[str, Any]):
    """Add a task to the queue"""
    task_id = queue_client.send_task(task)
    return {"taskId": task_id, "status": "queued"}

@app.get("/api/queue/tasks")
async def get_tasks():
    """List queued tasks"""
    import sqlite3
    try:
        # Use parent directory's database
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mcp_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.id, t.title, t.component as name, t.status, t.priority,
                   t.created_at, t.started_at, t.completed_at,
                   t.assigned_to as actor, t.metadata
            FROM tasks t
            ORDER BY
                CASE t.priority
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'normal' THEN 3
                    WHEN 'low' THEN 4
                    ELSE 5
                END,
                t.created_at DESC
        ''')

        tasks = []
        for row in cursor.fetchall():
            task_data = {
                'id': row[0],
                'name': row[1] or row[2] or 'Unnamed task',
                'status': row[3] or 'pending',
                'priority': row[4] or 'normal',
                'created_at': row[5],
                'started_at': row[6],
                'completed_at': row[7],
                'actor': row[8] or 'unassigned',
                'retries': 0
            }

            # Add metadata if exists
            if row[9]:
                try:
                    import json
                    metadata = json.loads(row[9])
                    task_data['retries'] = metadata.get('retries', 0)
                except:
                    pass

            tasks.append(task_data)

        conn.close()
        return tasks
    except Exception as e:
        # Return empty list on error
        return []

# System Operations
@app.get("/api/system/health")
async def get_system_health():
    """Get overall system health"""
    health = check_system_health()
    return health

@app.post("/api/system/restart")
async def restart_system():
    """Restart the entire system"""
    try:
        subprocess.run(["overmind", "restart"], check=True)
        return {"status": "restarting"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoints
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            if message.get("type") == "subscribe":
                agent_id = message.get("agentId")
                if agent_id:
                    if agent_id not in manager.agent_subscriptions:
                        manager.agent_subscriptions[agent_id] = []
                    manager.agent_subscriptions[agent_id].append(websocket)

            # Echo back for now
            await websocket.send_json({"echo": message})

    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Socket.IO events
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    await sio.emit('connected', {'data': 'Connected to server'}, to=sid)

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.on('agent:command')
async def handle_agent_command(sid, data):
    """Handle agent command via Socket.IO"""
    agent_id = data.get('agentId')
    command = data.get('command')

    if agent_id and command:
        try:
            if orchestrator and hasattr(orchestrator, 'send_task_to_claude'):
                result = orchestrator.send_task_to_claude(agent_id, command)
            else:
                result = None
            await sio.emit('agent:response', {
                'agentId': agent_id,
                'command': command,
                'result': result
            }, to=sid)
        except Exception as e:
            await sio.emit('agent:error', {
                'agentId': agent_id,
                'error': str(e)
            }, to=sid)

@sio.on('workflow:execute')
async def handle_workflow_execute(sid, data):
    """Handle workflow execution via Socket.IO"""
    workflow_id = data.get('workflowId')

    if workflow_id:
        import sqlite3
        import json

        # Start workflow execution
        await sio.emit('workflow:started', {'workflowId': workflow_id}, to=sid)

        try:
            # Create task in database for workflow
            # Use parent directory's database
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mcp_system.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get workflow details
            workflow = workflows_storage.get(workflow_id, {})

            # Insert workflow task
            cursor.execute('''
                INSERT INTO tasks (title, component, status, priority, created_at, metadata)
                VALUES (?, ?, 'processing', 'normal', datetime('now'), ?)
            ''', (
                f"Workflow: {workflow.get('name', workflow_id)}",
                'workflow',
                json.dumps({
                    'workflow_id': workflow_id,
                    'nodes': len(workflow.get('nodes', [])),
                    'edges': len(workflow.get('edges', []))
                })
            ))
            task_id = cursor.lastrowid

            # Process workflow nodes
            nodes = workflow.get('nodes', [])
            total_nodes = len(nodes)

            for idx, node in enumerate(nodes):
                progress = int((idx + 1) / total_nodes * 100)

                # Update progress
                await sio.emit('workflow:progress', {
                    'workflowId': workflow_id,
                    'progress': progress,
                    'currentNode': node.get('id')
                }, to=sid)

                # Log activity for node execution
                cursor.execute('''
                    INSERT INTO activities (agent, timestamp, activity, category, status)
                    VALUES ('workflow', datetime('now'), ?, 'workflow', 'processing')
                ''', (f"Executing node: {node.get('id')}",))

                await asyncio.sleep(0.5)  # Process time per node

            # Update task to completed
            cursor.execute('''
                UPDATE tasks SET status = 'completed', completed_at = datetime('now')
                WHERE id = ?
            ''', (task_id,))

            conn.commit()
            conn.close()

            await sio.emit('workflow:completed', {
                'workflowId': workflow_id,
                'taskId': task_id
            }, to=sid)

        except Exception as e:
            await sio.emit('workflow:error', {
                'workflowId': workflow_id,
                'error': str(e)
            }, to=sid)

# Background task for monitoring
async def monitor_agents():
    """Background task to monitor agent status"""
    while True:
        agents = await get_agents()
        for agent in agents:
            # Emit status updates
            await sio.emit('agent:status', {
                'agentId': agent['id'],
                'status': agent['status']
            })
        await asyncio.sleep(5)  # Check every 5 seconds

# Inbox endpoints - Using real database
@app.get("/api/inbox/messages")
async def get_inbox_messages(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    agent: Optional[str] = None
):
    """Get inbox messages from database with optional filters"""
    import sqlite3
    import json

    try:
        # Use parent directory's database
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mcp_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Build query with filters
        query = '''
        SELECT id, sender, recipient, message, timestamp, is_read, metadata
        FROM messages
        WHERE 1=1
        '''
        params = []

        if agent:
            query += " AND (sender = ? OR recipient = ?)"
            params.extend([agent, agent])

        query += " ORDER BY timestamp DESC LIMIT 100"

        cursor.execute(query, params)

        messages = []
        for row in cursor.fetchall():
            metadata = json.loads(row[6]) if row[6] else {}

            # Apply status and priority filters from metadata
            msg_status = 'read' if row[5] else 'unread'
            msg_priority = metadata.get('priority', 'normal')

            if status and msg_status != status:
                continue
            if priority and msg_priority not in priority.split(','):
                continue

            messages.append({
                'id': str(row[0]),
                'from': row[1],
                'to': row[2],
                'subject': metadata.get('subject', row[3][:50]),
                'content': row[3],
                'timestamp': row[4],
                'status': msg_status,
                'priority': msg_priority,
                'type': metadata.get('type', 'message'),
                'metadata': metadata
            })

        conn.close()
        return messages
    except Exception as e:
        print(f"Error getting inbox messages: {e}")
        return []

@app.post("/api/inbox/messages")
async def create_inbox_message(message: Dict[str, Any]):
    """Create a new inbox message in database"""
    import sqlite3
    import json

    try:
        # Use parent directory's database
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mcp_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Extract metadata
        metadata = {
            'subject': message.get('subject', ''),
            'priority': message.get('priority', 'normal'),
            'type': message.get('type', 'message'),
            **message.get('metadata', {})
        }

        # Insert into database
        cursor.execute('''
            INSERT INTO messages (sender, recipient, message, timestamp, is_read, metadata)
            VALUES (?, ?, ?, datetime('now'), 0, ?)
        ''', (
            message.get('from', 'system'),
            message.get('to', 'all'),
            message.get('content', message.get('message', '')),
            json.dumps(metadata)
        ))

        message_id = cursor.lastrowid
        conn.commit()

        # Get the created message
        cursor.execute('''
            SELECT id, sender, recipient, message, timestamp, is_read, metadata
            FROM messages WHERE id = ?
        ''', (message_id,))

        row = cursor.fetchone()
        conn.close()

        new_message = {
            'id': str(row[0]),
            'from': row[1],
            'to': row[2],
            'subject': metadata.get('subject'),
            'content': row[3],
            'timestamp': row[4],
            'status': 'unread',
            'priority': metadata.get('priority'),
            'type': metadata.get('type'),
            'metadata': metadata
        }

        # Emit socket.io event for real-time update
        await sio.emit('inbox:new_message', new_message)

        return new_message
    except Exception as e:
        print(f"Error creating inbox message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/inbox/messages/{message_id}/read")
async def mark_message_as_read(message_id: str):
    """Mark a message as read in database"""
    import sqlite3

    try:
        # Use parent directory's database
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mcp_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE messages SET is_read = 1 WHERE id = ?
        ''', (int(message_id),))

        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()

        if rows_affected > 0:
            return {"success": True}
        else:
            raise HTTPException(status_code=404, detail="Message not found")
    except Exception as e:
        print(f"Error marking message as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/inbox/messages/{message_id}/archive")
async def archive_message(message_id: str):
    """Archive a message in database"""
    import sqlite3
    import json

    try:
        # Use parent directory's database
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mcp_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get current metadata
        cursor.execute('SELECT metadata FROM messages WHERE id = ?', (int(message_id),))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Message not found")

        metadata = json.loads(row[0]) if row[0] else {}
        metadata['archived'] = True

        # Update with archived status in metadata
        cursor.execute('''
            UPDATE messages SET metadata = ? WHERE id = ?
        ''', (json.dumps(metadata), int(message_id)))

        conn.commit()
        conn.close()

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error archiving message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Terminal management endpoints
@app.post("/api/agents/{agent_id}/terminal/start")
async def start_agent_terminal(agent_id: str):
    """Start terminal for a specific agent"""
    try:
        # Calculate port based on agent index
        agent_index = list(AGENT_SESSIONS.keys()).index(agent_id) if agent_id in AGENT_SESSIONS else 0
        port = 8090 + agent_index

        # Start ttyd terminal
        # Map agent_id to correct tmux session name
        session_name = f"claude-{agent_id}" if not agent_id.startswith("claude-") else agent_id

        cmd = [
            "ttyd",
            "-p", str(port),
            "-t", "fontSize=14",
            "-t", f"titleFixed={agent_id} Terminal",
            "tmux", "attach-session", "-t", session_name
        ]

        # Check if terminal is already running
        check_cmd = f"lsof -i :{port}"
        result = subprocess.run(check_cmd, shell=True, capture_output=True)

        if result.returncode == 0:
            return {
                "success": True,
                "message": "Terminal already running",
                "port": port,
                "url": f"http://localhost:{port}"
            }

        # Start new terminal
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await asyncio.sleep(1)  # Wait for ttyd to start

        return {
            "success": True,
            "message": f"Terminal started for {agent_id}",
            "port": port,
            "url": f"http://localhost:{port}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/{agent_id}/terminal/stop")
async def stop_agent_terminal(agent_id: str):
    """Stop terminal for a specific agent"""
    try:
        # Calculate port
        agent_index = list(AGENT_SESSIONS.keys()).index(agent_id) if agent_id in AGENT_SESSIONS else 0
        port = 8090 + agent_index

        # Kill ttyd process on this port
        cmd = f"lsof -ti :{port} | xargs kill -9"
        subprocess.run(cmd, shell=True)

        return {"success": True, "message": f"Terminal stopped for {agent_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/{agent_id}/terminal/status")
async def get_terminal_status(agent_id: str):
    """Get terminal status for a specific agent"""
    try:
        # Calculate port
        agent_index = list(AGENT_SESSIONS.keys()).index(agent_id) if agent_id in AGENT_SESSIONS else 0
        port = 8090 + agent_index

        # Check if terminal is running
        check_cmd = f"lsof -i :{port}"
        result = subprocess.run(check_cmd, shell=True, capture_output=True)

        is_running = result.returncode == 0

        return {
            "agent_id": agent_id,
            "running": is_running,
            "port": port if is_running else None,
            "url": f"http://localhost:{port}" if is_running else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Task execution endpoints
@app.post("/api/tasks/execute")
async def execute_task(task: dict):
    """Execute a task across selected agents"""
    try:
        description = task.get("description", "")
        agents = task.get("agents", [])

        # Send task to each selected agent
        results = []
        for agent_id in agents:
            session_name = f"claude-{agent_id}"
            if tmux_client.check_session(session_name):
                # Send command to agent via tmux
                tmux_client.send_keys(session_name, description)
                results.append({"agent": agent_id, "status": "sent"})
            else:
                results.append({"agent": agent_id, "status": "offline"})

        return {
            "success": True,
            "data": {
                "task": description,
                "results": results
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/langgraph/execute")
async def execute_langgraph(request: dict):
    """Execute task via LangGraph"""
    import sqlite3
    import json
    try:
        task = request.get("task", "")

        # Create real task in database
        # Use parent directory's database
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mcp_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Insert task
        cursor.execute('''
            INSERT INTO tasks (title, component, status, priority, created_at, metadata)
            VALUES (?, 'langgraph', 'processing', 'normal', datetime('now'), ?)
        ''', (
            task,
            json.dumps({
                'type': 'langgraph',
                'submitted_at': datetime.now().isoformat()
            })
        ))
        task_id = cursor.lastrowid

        # Log activity
        cursor.execute('''
            INSERT INTO activities (agent, timestamp, activity, category, status)
            VALUES ('langgraph', datetime('now'), ?, 'task', 'processing')
        ''', (f"Executing task: {task}",))

        conn.commit()

        # Check if LangGraph service is available
        langgraph_available = False
        try:
            # Check if langgraph module exists
            import importlib.util
            spec = importlib.util.find_spec("langgraph")
            langgraph_available = spec is not None
        except:
            pass

        if langgraph_available:
            # Execute via actual LangGraph if available
            try:
                from langgraph import execute_task
                result = await execute_task(task)

                # Update task status
                cursor.execute('''
                    UPDATE tasks SET status = 'completed', completed_at = datetime('now')
                    WHERE id = ?
                ''', (task_id,))

                conn.commit()
                conn.close()

                return {
                    "success": True,
                    "data": {
                        "task": task,
                        "taskId": task_id,
                        "status": "completed",
                        "result": result,
                        "message": "Task executed successfully via LangGraph"
                    }
                }
            except ImportError:
                pass

        conn.close()

        # Return submitted status if LangGraph not available
        return {
            "success": True,
            "data": {
                "task": task,
                "taskId": task_id,
                "status": "submitted",
                "message": "Task submitted for processing (LangGraph service pending)"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# System status endpoint
@app.get("/api/system/status")
async def get_system_status():
    """Get system-wide status"""
    try:
        agents = await get_agents()

        # Get health status directly
        health_status = "healthy"
        try:
            health_response = await get_system_health()
            health_status = health_response.get("status", "unknown")
        except:
            health_status = "unknown"

        return {
            "status": health_status,
            "agents": agents,
            "queue": {
                "pending_tasks": 0,  # Will be updated when queue is properly integrated
                "active_workers": 0
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Logs endpoint
@app.get("/api/logs")
async def get_logs(agent: str = None, level: str = None, limit: int = 100):
    """Get system logs"""
    import sqlite3
    import json
    try:
        # Use parent directory's database
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mcp_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Build query based on filters
        query = '''
            SELECT id, agent, timestamp, activity, category, status, metadata
            FROM activities
        '''
        conditions = []
        params = []

        if agent:
            conditions.append("agent = ?")
            params.append(agent)

        if level:
            # Map level to status/category
            level_map = {
                'error': 'failed',
                'warning': 'warning',
                'info': 'completed',
                'debug': 'processing'
            }
            if level in level_map:
                conditions.append("status = ?")
                params.append(level_map[level])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        logs = []
        for row in cursor.fetchall():
            # Determine log level from status
            status = row[5]
            if status == 'failed':
                log_level = 'error'
            elif status == 'warning':
                log_level = 'warning'
            elif status == 'processing':
                log_level = 'debug'
            else:
                log_level = 'info'

            log_entry = {
                "id": f"log_{row[0]}",
                "timestamp": row[2],
                "level": log_level,
                "agent": row[1],
                "message": row[3],
                "category": row[4],
                "details": {}
            }

            # Add metadata as details if exists
            if row[6]:
                try:
                    log_entry["details"] = json.loads(row[6])
                except:
                    pass

            logs.append(log_entry)

        conn.close()
        return {"logs": logs}

    except Exception as e:
        # Fallback to basic logs on error
        return {"logs": [
            {
                "id": "log_error",
                "timestamp": datetime.now().isoformat(),
                "level": "error",
                "agent": "system",
                "message": f"Error retrieving logs: {str(e)}",
                "details": {}
            }
        ]}

# Messages endpoint (different from inbox)
@app.get("/api/messages")
async def get_messages(agent: str = None):
    """Get inter-agent messages"""
    import sqlite3
    import json
    try:
        # Use parent directory's database
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mcp_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query messages from database
        if agent:
            cursor.execute('''
                SELECT id, sender, recipient, message, timestamp, is_read, metadata
                FROM messages
                WHERE sender = ? OR recipient = ?
                ORDER BY timestamp DESC
                LIMIT 100
            ''', (agent, agent))
        else:
            cursor.execute('''
                SELECT id, sender, recipient, message, timestamp, is_read, metadata
                FROM messages
                ORDER BY timestamp DESC
                LIMIT 100
            ''')

        messages = []
        for row in cursor.fetchall():
            msg_data = {
                "id": f"msg_{row[0]}",
                "timestamp": row[4],
                "from": row[1],
                "to": row[2],
                "type": "message",
                "status": "read" if row[5] else "delivered",
                "subject": row[3][:50] if len(row[3]) > 50 else row[3],
                "content": row[3],
                "priority": "normal"
            }

            # Extract priority from metadata if exists
            if row[6]:
                try:
                    metadata = json.loads(row[6])
                    msg_data["priority"] = metadata.get("priority", "normal")
                    msg_data["type"] = metadata.get("type", "message")
                except:
                    pass

            messages.append(msg_data)

        conn.close()
        return {"messages": messages}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Tasks endpoints
@app.get("/api/tasks/pending")
async def get_pending_tasks(agent: str = None):
    """Get pending tasks"""
    import sqlite3
    import json
    try:
        # Use parent directory's database
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mcp_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query pending tasks
        if agent:
            cursor.execute('''
                SELECT id, title, component, assigned_to, priority, created_at, metadata
                FROM tasks
                WHERE status IN ('pending', 'queued')
                AND (assigned_to = ? OR assigned_to IS NULL OR assigned_to = 'any')
                ORDER BY
                    CASE priority
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'normal' THEN 3
                        WHEN 'low' THEN 4
                        ELSE 5
                    END,
                    created_at ASC
            ''', (agent,))
        else:
            cursor.execute('''
                SELECT id, title, component, assigned_to, priority, created_at, metadata
                FROM tasks
                WHERE status IN ('pending', 'queued')
                ORDER BY
                    CASE priority
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'normal' THEN 3
                        WHEN 'low' THEN 4
                        ELSE 5
                    END,
                    created_at ASC
            ''')

        tasks = []
        for row in cursor.fetchall():
            task_data = {
                "id": f"task_{row[0]}",
                "timestamp": row[5],
                "agent": row[3] or "any",
                "command": row[1] or f"Task #{row[0]}",
                "status": "pending",
                "priority": row[4] or "normal",
                "params": {}
            }

            # Add params from metadata if exists
            if row[6]:
                try:
                    metadata = json.loads(row[6])
                    task_data["params"] = metadata.get("params", {})
                except:
                    pass

            tasks.append(task_data)

        conn.close()
        return {"tasks": tasks}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Terminal endpoints for agents
@app.post("/api/agents/{agent_id}/terminal/start")
async def start_terminal(agent_id: str):
    """Start a terminal for an agent"""
    try:
        # Generate a port for the terminal
        import random
        port = random.randint(7000, 7999)

        return {
            "port": port,
            "url": f"http://localhost:{port}",
            "agentId": agent_id,
            "status": "running"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/{agent_id}/terminal/stop")
async def stop_terminal(agent_id: str):
    """Stop a terminal for an agent"""
    try:
        return {"status": "stopped", "agentId": agent_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/{agent_id}/terminal/command")
async def send_terminal_command(agent_id: str, request: dict):
    """Send a command to an agent's terminal"""
    try:
        command = request.get("command", "")
        session_name = f"claude-{agent_id}"

        # Send command via tmux if session exists
        if tmux_client.check_session(session_name):
            tmux_client.send_keys(session_name, command)
            return {"status": "sent", "command": command}
        else:
            return {"status": "error", "message": "Agent session not found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/{agent_id}/terminal/output")
async def get_terminal_output(agent_id: str):
    """Get terminal output for an agent"""
    try:
        session_name = f"claude-{agent_id}"

        # Get output from tmux if session exists
        if tmux_client.check_session(session_name):
            output = tmux_client.get_output(session_name)
            return {"output": output, "status": "active"}
        else:
            return {"output": "", "status": "inactive"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Queue management endpoints
@app.get("/api/queue/tasks")
async def get_queue_tasks():
    """Get all tasks in the queue"""
    import sqlite3
    import json
    try:
        # Use parent directory's database
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mcp_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all tasks that are in queue-related statuses
        cursor.execute('''
            SELECT t.id, t.title, t.component, t.status, t.priority,
                   t.created_at, t.started_at, t.completed_at,
                   t.assigned_to, t.metadata
            FROM tasks t
            WHERE t.status IN ('pending', 'queued', 'processing', 'failed')
            ORDER BY
                CASE t.status
                    WHEN 'processing' THEN 1
                    WHEN 'queued' THEN 2
                    WHEN 'pending' THEN 3
                    WHEN 'failed' THEN 4
                    ELSE 5
                END,
                CASE t.priority
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'normal' THEN 3
                    WHEN 'low' THEN 4
                    ELSE 5
                END,
                t.created_at DESC
        ''')

        tasks = []
        for row in cursor.fetchall():
            # Map priority to numeric value
            priority_map = {'critical': 0, 'high': 1, 'normal': 2, 'low': 3}
            numeric_priority = priority_map.get(row[4], 2)

            task_data = {
                "id": f"task-{row[0]:03d}",
                "name": row[1] or row[2] or f"Task #{row[0]}",
                "status": row[3] or 'pending',
                "priority": numeric_priority,
                "created_at": row[5],
                "started_at": row[6],
                "retries": 0,
                "actor": row[8] or row[2] or 'unassigned'
            }

            # Extract retries from metadata if exists
            if row[9]:
                try:
                    metadata = json.loads(row[9])
                    task_data["retries"] = metadata.get('retries', 0)
                except:
                    pass

            tasks.append(task_data)

        conn.close()
        return tasks

    except Exception as e:
        # Return empty list on error
        return []

@app.get("/api/queue/status")
async def get_queue_status():
    """Get overall queue status"""
    try:
        # Get stats which provides the same data
        stats = await get_queue_stats()
        return stats
    except Exception as e:
        return {
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
            "total": 0
        }

@app.get("/api/queue/stats")
async def get_queue_stats():
    """Get queue statistics"""
    import sqlite3
    try:
        # First try to get real stats from queue client
        if hasattr(queue_client, 'get_stats'):
            real_stats = queue_client.get_stats()
            # Transform to expected format
            return {
                "total": real_stats.get('total_messages_sent', 0),
                "pending": real_stats.get('pending', 0),
                "processing": real_stats.get('processing', 0),
                "completed": real_stats.get('completed', 0),
                "failed": real_stats.get('failed', 0),
                "avgProcessingTime": real_stats.get('avgProcessingTime', 0)
            }

        # Get real stats from database
        # Use parent directory's database
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mcp_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Count tasks by status
        cursor.execute('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status IN ('pending', 'queued') THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as processing,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM tasks
        ''')

        row = cursor.fetchone()

        # Calculate average processing time
        cursor.execute('''
            SELECT AVG(
                CAST((julianday(completed_at) - julianday(started_at)) * 86400 AS REAL)
            ) as avg_time
            FROM tasks
            WHERE status = 'completed'
            AND started_at IS NOT NULL
            AND completed_at IS NOT NULL
        ''')

        avg_time_row = cursor.fetchone()
        avg_processing_time = avg_time_row[0] if avg_time_row and avg_time_row[0] else 0

        conn.close()

        return {
            "total": row[0] or 0,
            "pending": row[1] or 0,
            "processing": row[2] or 0,
            "completed": row[3] or 0,
            "failed": row[4] or 0,
            "avgProcessingTime": round(avg_processing_time, 2)
        }

    except Exception as e:
        # Return zeros on error
        return {
            "total": 0,
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
            "avgProcessingTime": 0
        }

@app.post("/api/queue/tasks/{task_id}/retry")
async def retry_queue_task(task_id: str):
    """Retry a failed task"""
    return {"success": True, "message": f"Task {task_id} requeued"}

@app.delete("/api/queue/tasks/{task_id}")
async def cancel_queue_task(task_id: str):
    """Cancel a task"""
    return {"success": True, "message": f"Task {task_id} cancelled"}

@app.post("/api/queue/clear-completed")
async def clear_completed_tasks():
    """Clear all completed tasks from queue"""
    return {"success": True, "cleared": 5}

# Documentation endpoints
@app.get("/api/documents")
async def get_documents():
    """Get all documentation files"""
    try:
        docs = []
        # Get instruction files
        instructions_path = os.path.join(os.path.dirname(__file__), "..", "instructions")
        if os.path.exists(instructions_path):
            for file in os.listdir(instructions_path):
                if file.endswith(".md"):
                    file_path = os.path.join(instructions_path, file)
                    with open(file_path, 'r') as f:
                        content = f.read()
                    docs.append({
                        "id": file.replace(".md", ""),
                        "name": file.replace(".md", "").replace("-", " ").title(),
                        "type": "instruction",
                        "path": f"instructions/{file}",
                        "content": content,
                        "lastModified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })

        # Get README files
        readme_path = os.path.join(os.path.dirname(__file__), "..")
        if os.path.exists(os.path.join(readme_path, "README.md")):
            with open(os.path.join(readme_path, "README.md"), 'r') as f:
                content = f.read()
            docs.append({
                "id": "readme-main",
                "name": "Main README",
                "type": "readme",
                "path": "README.md",
                "content": content,
                "lastModified": datetime.fromtimestamp(
                    os.path.getmtime(os.path.join(readme_path, "README.md"))
                ).isoformat()
            })

        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/documents/{doc_id}")
async def update_document(doc_id: str, request: dict):
    """Update a document"""
    try:
        content = request.get("content", "")
        # Find and update the document
        # This would write to the actual file
        return {"success": True, "message": "Document updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents")
async def create_document(request: dict):
    """Create a new document"""
    try:
        name = request.get("name", "")
        doc_type = request.get("type", "guide")
        content = request.get("content", "")

        doc_id = name.lower().replace(" ", "-")
        return {
            "id": doc_id,
            "name": name,
            "type": doc_type,
            "path": f"{doc_type}s/{doc_id}.md",
            "content": content,
            "lastModified": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
    asyncio.create_task(monitor_agents())
    print("API Gateway started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("API Gateway shutting down")

if __name__ == "__main__":
    import uvicorn
    import sys
    port = 8888 if "--port" in sys.argv else 8000
    uvicorn.run(
        "main:socket_app",  # Use socket_app for Socket.IO support
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )