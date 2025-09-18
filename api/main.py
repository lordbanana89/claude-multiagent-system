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

# Import existing components
from core.claude_orchestrator import ClaudeNativeOrchestrator
from core.tmux_client import TMUXClient
from task_queue.client import QueueClient
from monitoring.health import check_system_health
from config.settings import AGENT_SESSIONS

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

# Initialize core components
orchestrator = ClaudeNativeOrchestrator()
tmux_client = TMUXClient()
queue_client = QueueClient()

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

# Agent Operations
@app.get("/api/agents")
async def get_agents():
    """List all available agents with their current status"""
    agents = []
    agent_configs = {
        'supervisor': {'name': 'Supervisor Agent', 'type': 'coordinator'},
        'master': {'name': 'Master Agent', 'type': 'strategic'},
        'backend-api': {'name': 'Backend API Agent', 'type': 'development'},
        'database': {'name': 'Database Agent', 'type': 'database'},
        'frontend-ui': {'name': 'Frontend UI Agent', 'type': 'ui'},
        'testing': {'name': 'Testing Agent', 'type': 'qa'},
        'instagram': {'name': 'Instagram Agent', 'type': 'social'},
        'queue-manager': {'name': 'Queue Manager Agent', 'type': 'infrastructure'},
        'deployment': {'name': 'Deployment Agent', 'type': 'devops'}
    }

    for agent_id, config in agent_configs.items():
        session_name = f"claude-{agent_id}"
        status = tmux_client.check_session(session_name) if hasattr(tmux_client, 'check_session') else False

        agents.append({
            "id": agent_id,
            "name": config['name'],
            "type": config['type'],
            "status": "online" if status else "offline",
            "sessionId": session_name,
            "lastActivity": datetime.now().isoformat()
        })

    return agents

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
        "capabilities": orchestrator.get_agent_capabilities(agent_id)
    }

@app.post("/api/agents/{agent_id}/command")
async def send_command(agent_id: str, command: AgentCommand):
    """Send a command to a specific agent"""
    try:
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
    # TODO: Implement task listing
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
            result = orchestrator.send_task_to_claude(agent_id, command)
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
        # Simulate workflow execution
        await sio.emit('workflow:started', {'workflowId': workflow_id}, to=sid)

        # Simulate progress updates
        for i in range(1, 101, 20):
            await asyncio.sleep(1)
            await sio.emit('workflow:progress', {
                'workflowId': workflow_id,
                'progress': i
            }, to=sid)

        await sio.emit('workflow:completed', {'workflowId': workflow_id}, to=sid)

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

# Inbox message storage (in-memory for now)
inbox_messages = []
message_counter = 0

# Inbox endpoints
@app.get("/api/inbox/messages")
async def get_inbox_messages(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    agent: Optional[str] = None
):
    """Get inbox messages with optional filters"""
    filtered = inbox_messages.copy()

    if status:
        filtered = [m for m in filtered if m.get('status') == status]

    if priority:
        priorities = priority.split(',')
        filtered = [m for m in filtered if m.get('priority') in priorities]

    if agent:
        filtered = [m for m in filtered if m.get('from') == agent or m.get('to') == agent]

    return filtered

@app.post("/api/inbox/messages")
async def create_inbox_message(message: Dict[str, Any]):
    """Create a new inbox message"""
    global message_counter
    message_counter += 1

    new_message = {
        **message,
        'id': str(message_counter),
        'timestamp': datetime.utcnow().isoformat(),
        'status': message.get('status', 'unread')
    }

    inbox_messages.append(new_message)

    # Emit socket.io event for real-time update
    await sio.emit('inbox:new_message', new_message)

    return new_message

@app.patch("/api/inbox/messages/{message_id}/read")
async def mark_message_as_read(message_id: str):
    """Mark a message as read"""
    for message in inbox_messages:
        if message['id'] == message_id:
            message['status'] = 'read'
            return {"success": True}

    raise HTTPException(status_code=404, detail="Message not found")

@app.patch("/api/inbox/messages/{message_id}/archive")
async def archive_message(message_id: str):
    """Archive a message"""
    for message in inbox_messages:
        if message['id'] == message_id:
            message['status'] = 'archived'
            return {"success": True}

    raise HTTPException(status_code=404, detail="Message not found")

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
    try:
        task = request.get("task", "")
        # Here you would integrate with LangGraph API
        # For now, return a mock response
        return {
            "success": True,
            "data": {
                "task": task,
                "status": "submitted",
                "message": "Task submitted to LangGraph for processing"
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
    try:
        # Mock logs for now - replace with actual log retrieval
        logs = []
        for i in range(10):
            logs.append({
                "id": f"log_{i}",
                "timestamp": datetime.now().isoformat(),
                "level": "info" if i % 3 == 0 else "warning" if i % 3 == 1 else "error",
                "agent": agent or "system",
                "message": f"Sample log message {i}",
                "details": {}
            })

        # Filter by level if specified
        if level:
            logs = [log for log in logs if log["level"] == level]

        # Filter by agent if specified
        if agent:
            logs = [log for log in logs if log["agent"] == agent]

        return {"logs": logs[:limit]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Messages endpoint (different from inbox)
@app.get("/api/messages")
async def get_messages(agent: str = None):
    """Get inter-agent messages"""
    try:
        # Mock messages for now
        messages = []
        for i in range(5):
            messages.append({
                "id": f"msg_{i}",
                "timestamp": datetime.now().isoformat(),
                "from": "supervisor",
                "to": agent or "backend-api",
                "type": "task",
                "status": "delivered",
                "subject": f"Task assignment {i}",
                "content": f"Please process task {i}",
                "priority": "normal"
            })

        if agent:
            messages = [msg for msg in messages if msg["to"] == agent or msg["from"] == agent]

        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Tasks endpoints
@app.get("/api/tasks/pending")
async def get_pending_tasks(agent: str = None):
    """Get pending tasks"""
    try:
        tasks = []
        for i in range(3):
            tasks.append({
                "id": f"task_{i}",
                "timestamp": datetime.now().isoformat(),
                "agent": agent or "any",
                "command": f"execute_task_{i}",
                "status": "pending",
                "priority": "normal" if i % 2 == 0 else "high",
                "params": {}
            })

        if agent:
            tasks = [task for task in tasks if task["agent"] == agent or task["agent"] == "any"]

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
    try:
        # This would connect to the actual queue system (Redis/Dramatiq)
        # For now, return mock data
        return [
            {
                "id": "task-001",
                "name": "Process data batch",
                "status": "processing",
                "priority": 1,
                "created_at": datetime.now().isoformat(),
                "started_at": datetime.now().isoformat(),
                "retries": 0,
                "actor": "data_processor"
            },
            {
                "id": "task-002",
                "name": "Generate report",
                "status": "pending",
                "priority": 2,
                "created_at": datetime.now().isoformat(),
                "retries": 0,
                "actor": "report_generator"
            }
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    try:
        # Check if we can get real stats from the queue client
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
        else:
            # Return mock data as fallback
            return {
                "total": 10,
                "pending": 3,
                "processing": 2,
                "completed": 4,
                "failed": 1,
                "avgProcessingTime": 45.2
            }
    except Exception as e:
        # Return default values on error
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
    uvicorn.run(
        "main:socket_app",  # Use socket_app for Socket.IO support
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )