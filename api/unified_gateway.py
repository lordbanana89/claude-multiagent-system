"""
Unified API Gateway for Claude Multi-Agent System
Single point of access for all system operations
"""

from fastapi import FastAPI, WebSocket, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio
import json
import logging

from core.message_bus import get_message_bus, MessagePriority
from core.workflow_engine import get_workflow_engine
from agents.agent_bridge import get_bridge_manager
from config.settings import AGENT_SESSIONS
from core.auth_manager import AuthManager
from enum import Enum

# Simple UserRole enum
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

# Simple auth placeholder
async def get_current_user():
    """Placeholder auth - returns default user"""
    return {"username": "admin", "role": "admin"}

logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Claude Multi-Agent System API",
    description="Unified gateway for multi-agent orchestration",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
message_bus = get_message_bus()
workflow_engine = get_workflow_engine()
bridge_manager = get_bridge_manager()
auth_manager = AuthManager()

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        # Remove from all subscriptions
        for subscribers in self.subscriptions.values():
            if websocket in subscribers:
                subscribers.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, channel: str = None):
        if channel and channel in self.subscriptions:
            # Send to channel subscribers
            for connection in self.subscriptions[channel]:
                try:
                    await connection.send_text(message)
                except:
                    # Connection closed
                    self.subscriptions[channel].remove(connection)
        else:
            # Broadcast to all
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except:
                    # Connection closed
                    self.active_connections.remove(connection)

    def subscribe(self, websocket: WebSocket, channel: str):
        if channel not in self.subscriptions:
            self.subscriptions[channel] = []
        if websocket not in self.subscriptions[channel]:
            self.subscriptions[channel].append(websocket)

manager = ConnectionManager()


# Request/Response Models
class TaskRequest(BaseModel):
    agent: str
    command: str
    params: Dict[str, Any] = Field(default_factory=dict)
    priority: str = "normal"
    timeout: int = 300

class WorkflowRequest(BaseModel):
    workflow_id: Optional[str] = None
    workflow_definition: Optional[Dict[str, Any]] = None
    params: Dict[str, Any] = Field(default_factory=dict)

class AgentCommand(BaseModel):
    command: str
    params: Dict[str, Any] = Field(default_factory=dict)

class SystemStatus(BaseModel):
    status: str
    agents: Dict[str, Any]
    queue: Dict[str, Any]
    workflows: Dict[str, Any]
    timestamp: datetime


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Claude Multi-Agent System API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "tasks": "/tasks",
            "agents": "/agents",
            "workflows": "/workflows",
            "system": "/system",
            "websocket": "/ws"
        }
    }


@app.get("/health")
async def health_check():
    """System health check"""
    try:
        # Check all components
        agents_status = {}
        for agent_name in AGENT_SESSIONS.keys():
            status = message_bus.get_agent_status(agent_name)
            agents_status[agent_name] = status if status else {"status": "unknown"}

        return {
            "status": "healthy",
            "components": {
                "message_bus": "operational",
                "workflow_engine": "operational",
                "agents": agents_status
            },
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


# Task Management

@app.post("/tasks/submit")
async def submit_task(
    request: TaskRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Submit a task to an agent"""
    try:
        # Check agent exists
        if request.agent not in AGENT_SESSIONS:
            raise HTTPException(status_code=400, detail=f"Unknown agent: {request.agent}")

        # Map priority
        priority_map = {
            "low": MessagePriority.LOW,
            "normal": MessagePriority.NORMAL,
            "high": MessagePriority.HIGH,
            "urgent": MessagePriority.URGENT
        }
        priority = priority_map.get(request.priority.lower(), MessagePriority.NORMAL)

        # Submit task
        task_id = message_bus.publish_task(
            agent=request.agent,
            task={
                "command": request.command,
                "params": request.params,
                "timeout": request.timeout,
                "submitted_by": current_user["username"]
            },
            priority=priority
        )

        # Broadcast event
        await manager.broadcast(json.dumps({
            "event": "task_submitted",
            "task_id": task_id,
            "agent": request.agent
        }), channel="tasks")

        return {
            "task_id": task_id,
            "status": "submitted",
            "agent": request.agent
        }

    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a specific task"""
    status = message_bus.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status


@app.get("/tasks/pending")
async def get_pending_tasks(agent: Optional[str] = None):
    """Get all pending tasks"""
    try:
        tasks = message_bus.get_pending_tasks(agent)
        return {"count": len(tasks), "tasks": tasks}
    except Exception as e:
        # Return empty list if there's an error
        logger.warning(f"Error getting pending tasks: {e}")
        return {"count": 0, "tasks": []}


# Agent Management

@app.get("/agents")
async def list_agents():
    """List all available agents"""
    agents = []
    for agent_name, session_name in AGENT_SESSIONS.items():
        status = message_bus.get_agent_status(agent_name)
        agents.append({
            "name": agent_name,
            "session": session_name,
            "status": status if status else {"status": "unknown"}
        })
    return {"agents": agents}


@app.get("/agents/{agent_name}")
async def get_agent_status(agent_name: str):
    """Get detailed status of specific agent"""
    if agent_name not in AGENT_SESSIONS:
        raise HTTPException(status_code=404, detail="Agent not found")

    status = message_bus.get_agent_status(agent_name)
    bridge = bridge_manager.get_bridge(agent_name)

    return {
        "name": agent_name,
        "session": AGENT_SESSIONS[agent_name],
        "status": status if status else {"status": "unknown"},
        "bridge_active": bridge is not None
    }


@app.post("/agents/{agent_name}/command")
async def send_agent_command(
    agent_name: str,
    command: AgentCommand,
    current_user: dict = Depends(get_current_user)
):
    """Send direct command to agent"""
    if agent_name not in AGENT_SESSIONS:
        raise HTTPException(status_code=404, detail="Agent not found")

    message_bus.send_command(agent_name, command.command, command.params)
    return {"status": "sent", "agent": agent_name, "command": command.command}


@app.post("/agents/{agent_name}/restart")
async def restart_agent(
    agent_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Restart an agent bridge"""
    if current_user["role"] not in [UserRole.ADMIN, UserRole.DEVELOPER]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    if agent_name not in AGENT_SESSIONS:
        raise HTTPException(status_code=404, detail="Agent not found")

    bridge_manager.restart_bridge(agent_name)
    return {"status": "restarted", "agent": agent_name}


# Logs Management

@app.get("/logs")
async def get_logs(
    agent: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get system logs"""
    import sqlite3
    import json

    try:
        conn = sqlite3.connect('../mcp_system.db')
        cursor = conn.cursor()

        # Build query with filters
        query = '''
            SELECT id, agent, timestamp, activity as message, category, status
            FROM activities
            WHERE 1=1
        '''
        params = []

        if agent:
            query += ' AND agent = ?'
            params.append(agent)

        # Map level to status
        if level:
            if level.upper() == 'ERROR':
                query += ' AND status = ?'
                params.append('failed')
            elif level.upper() == 'WARNING':
                query += ' AND status = ?'
                params.append('warning')
            elif level.upper() == 'INFO':
                query += ' AND status = ?'
                params.append('completed')

        # Add ordering and limits
        query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        cursor.execute(query, params)
        activities = cursor.fetchall()

        # Format logs
        logs = []
        for activity in activities:
            act_id, agent_name, timestamp, message, category, status = activity

            # Determine log level from status
            if status == 'failed':
                log_level = 'ERROR'
            elif status == 'warning':
                log_level = 'WARNING'
            elif status == 'completed':
                log_level = 'INFO'
            else:
                log_level = 'DEBUG'

            logs.append({
                "id": act_id,
                "timestamp": timestamp,
                "level": log_level,
                "agent": agent_name,
                "message": message or f"{agent_name}: {category}",
                "details": {"category": category, "status": status}
            })

        # Get total count
        count_query = 'SELECT COUNT(*) FROM activities WHERE 1=1'
        count_params = []

        if agent:
            count_query += ' AND agent = ?'
            count_params.append(agent)

        if level and level.upper() in ['ERROR', 'WARNING', 'INFO']:
            status_map = {'ERROR': 'failed', 'WARNING': 'warning', 'INFO': 'completed'}
            count_query += ' AND status = ?'
            count_params.append(status_map[level.upper()])

        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()[0]

        conn.close()

        return {
            "logs": logs,
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return {"logs": [], "total": 0, "limit": limit, "offset": offset}


@app.get("/messages")
async def get_messages(
    agent: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get system messages"""
    import sqlite3
    import json

    try:
        conn = sqlite3.connect('../mcp_system.db')
        cursor = conn.cursor()

        # Build query with filters
        query = '''
            SELECT id, from_agent, to_agent, message, timestamp, read
            FROM messages
            WHERE 1=1
        '''
        params = []

        if agent:
            query += ' AND (from_agent = ? OR to_agent = ?)'
            params.extend([agent, agent])

        # Map status to read state
        if status:
            if status == 'pending':
                query += ' AND read = 0'
            elif status == 'processed':
                query += ' AND read = 1'

        # Add ordering and limits
        query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        cursor.execute(query, params)
        messages_data = cursor.fetchall()

        # Format messages
        messages = []
        for msg in messages_data:
            msg_id, from_agent, to_agent, content, timestamp, is_read = msg

            # Determine type and priority from content
            msg_type = 'task' if 'task' in content.lower() else 'status'
            priority = 'high' if '[HIGH PRIORITY]' in content else 'normal'

            # Extract subject from content (first line or first 50 chars)
            subject = content.split('\n')[0][:50]
            if len(subject) < len(content.split('\n')[0]):
                subject += '...'

            # Determine status
            if is_read == 0:
                msg_status = 'pending'
            else:
                msg_status = 'processed'

            messages.append({
                "id": msg_id,
                "timestamp": timestamp,
                "from": from_agent,
                "to": to_agent,
                "type": msg_type,
                "status": msg_status,
                "subject": subject,
                "content": content,
                "priority": priority
            })

        # Get total count
        count_query = 'SELECT COUNT(*) FROM messages WHERE 1=1'
        count_params = []

        if agent:
            count_query += ' AND (from_agent = ? OR to_agent = ?)'
            count_params.extend([agent, agent])

        if status:
            if status == 'pending':
                count_query += ' AND read = 0'
            elif status == 'processed':
                count_query += ' AND read = 1'

        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()[0]

        conn.close()

        return {
            "messages": messages,
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        return {"messages": [], "total": 0, "limit": limit, "offset": offset}


# Workflow Management

@app.post("/workflows/define")
async def define_workflow(
    definition: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Define a new workflow"""
    try:
        workflow_id = workflow_engine.define_workflow(definition)
        return {"workflow_id": workflow_id, "status": "defined"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/workflows/execute")
async def execute_workflow(
    request: WorkflowRequest,
    current_user: dict = Depends(get_current_user)
):
    """Execute a workflow"""
    try:
        if request.workflow_definition:
            # Define and execute new workflow
            workflow_id = workflow_engine.define_workflow(request.workflow_definition)
        elif request.workflow_id:
            workflow_id = request.workflow_id
        else:
            raise HTTPException(status_code=400, detail="Either workflow_id or workflow_definition required")

        execution_id = workflow_engine.execute(workflow_id, request.params)

        # Broadcast event
        await manager.broadcast(json.dumps({
            "event": "workflow_started",
            "execution_id": execution_id,
            "workflow_id": workflow_id
        }), channel="workflows")

        return {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "status": "started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflows/executions/{execution_id}")
async def get_workflow_execution(execution_id: str):
    """Get workflow execution status"""
    status = workflow_engine.get_execution_status(execution_id)
    if not status:
        raise HTTPException(status_code=404, detail="Execution not found")
    return status


@app.post("/workflows/executions/{execution_id}/cancel")
async def cancel_workflow(
    execution_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a running workflow"""
    success = workflow_engine.cancel_execution(execution_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel workflow")
    return {"status": "cancelled", "execution_id": execution_id}


# System Management

@app.get("/system/status")
async def get_system_status():
    """Get overall system status"""
    agents_status = {}
    for agent_name in AGENT_SESSIONS.keys():
        status = message_bus.get_agent_status(agent_name)
        agents_status[agent_name] = status if status else {"status": "unknown"}

    pending_tasks = message_bus.get_pending_tasks()

    return SystemStatus(
        status="operational",
        agents=agents_status,
        queue={
            "pending_tasks": len(pending_tasks),
            "message_bus": "active"
        },
        workflows={
            "defined": len(workflow_engine.workflows),
            "executions": len(workflow_engine.executions)
        },
        timestamp=datetime.now()
    )


@app.post("/system/initialize")
async def initialize_system(current_user: dict = Depends(get_current_user)):
    """Initialize all system components"""
    if current_user["role"] != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Start all agent bridges
        bridge_manager.start_all()

        # Initialize message bus if not running
        if not message_bus.running:
            message_bus.start()

        return {
            "status": "initialized",
            "components": {
                "message_bus": "started",
                "bridges": len(bridge_manager.bridges),
                "workflow_engine": "ready"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket Endpoint

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await manager.connect(websocket)

    # Subscribe to events
    def event_callback(message):
        asyncio.create_task(manager.send_personal_message(
            json.dumps(message.to_dict()),
            websocket
        ))

    message_bus.subscribe("bus:events:*", event_callback)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle subscription requests
            if message.get("action") == "subscribe":
                channel = message.get("channel")
                if channel:
                    manager.subscribe(websocket, channel)
                    await manager.send_personal_message(
                        json.dumps({"status": "subscribed", "channel": channel}),
                        websocket
                    )

            # Handle other actions
            elif message.get("action") == "ping":
                await manager.send_personal_message(
                    json.dumps({"action": "pong", "timestamp": datetime.now().isoformat()}),
                    websocket
                )

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)
        message_bus.unsubscribe("bus:events:*", event_callback)


# Event streaming callbacks to broadcast to WebSocket clients
async def broadcast_task_events():
    """Background task to broadcast task events"""
    def task_callback(message):
        asyncio.create_task(manager.broadcast(
            json.dumps(message.to_dict()),
            channel="tasks"
        ))

    message_bus.subscribe("bus:results:*", task_callback)


async def broadcast_workflow_events():
    """Background task to broadcast workflow events"""
    def workflow_callback(message):
        asyncio.create_task(manager.broadcast(
            json.dumps(message.to_dict()),
            channel="workflows"
        ))

    message_bus.subscribe("bus:events:workflow_*", workflow_callback)


# Startup and shutdown events

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    logger.info("Starting Claude Multi-Agent System API Gateway")

    # Start message bus
    message_bus.start()

    # Start broadcasting background tasks
    asyncio.create_task(broadcast_task_events())
    asyncio.create_task(broadcast_workflow_events())

    logger.info("API Gateway started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down API Gateway")

    # Stop message bus
    message_bus.stop()

    # Stop all agent bridges
    bridge_manager.stop_all()

    logger.info("API Gateway shut down complete")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")