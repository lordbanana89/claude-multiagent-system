#!/usr/bin/env python3
"""
MCP Server Compliant - Implementazione corretta secondo SDK ufficiale
Usa FastMCP invece di aiohttp custom
"""

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import sqlite3
import json
import logging
import asyncio
from pathlib import Path

# Import our components
from core.database_manager import DatabaseManager
from core.message_bus import MessageBus, Event, EventType
from core.watchdog import AgentWatchdog

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server with correct name
mcp = FastMCP(name="claude-multiagent-system")

# Initialize components
db_manager = DatabaseManager()
message_bus = MessageBus()
watchdog = AgentWatchdog()

# Pydantic models for structured responses
class HeartbeatResponse(BaseModel):
    status: str
    agent: str
    timestamp: str
    next_expected: float
    db_updated: bool
    message: Optional[str] = None

class StatusUpdateResponse(BaseModel):
    success: bool
    agent: str
    status: str
    previous_status: Optional[str]
    task_assigned: Optional[str]
    timestamp: str

class ActivityLogResponse(BaseModel):
    logged: bool
    id: str
    timestamp: str
    indexed: bool

class ConflictCheckResponse(BaseModel):
    conflicts: List[Dict[str, Any]]
    agents_checked: List[str]
    components_analyzed: int
    resolution_needed: bool

class ComponentRegistrationResponse(BaseModel):
    registered: bool
    component_id: str
    name: str
    owner: str
    timestamp: str

class CollaborationRequestResponse(BaseModel):
    request_id: str
    status: str
    from_agent: str
    to_agent: str
    timestamp: str
    queue_position: Optional[int] = None

class DecisionProposalResponse(BaseModel):
    decision_id: str
    status: str
    category: str
    confidence: float
    timestamp: str
    auto_approved: bool

class ComponentOwnerResponse(BaseModel):
    component: str
    owner: str
    type: str
    status: str
    agent_available: bool

# Tool implementations with proper MCP decorators

@mcp.tool()
async def heartbeat(
    agent: str,
    ctx: Context[ServerSession, None]
) -> HeartbeatResponse:
    """
    Register heartbeat from an agent to indicate it's alive.
    Updates database, publishes event, resets watchdog, and tracks metrics.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        # Log the heartbeat reception
        await ctx.info(f"Received heartbeat from agent: {agent}")

        # 1. Update database
        db_result = db_manager.update_heartbeat(agent, timestamp)

        # 2. Publish event to message bus
        if message_bus.running:
            event = Event(
                type=EventType.HEARTBEAT_RECEIVED,
                source=agent,
                payload={
                    'agent': agent,
                    'timestamp': timestamp,
                    'status': 'alive'
                }
            )
            message_bus.publish(event, sync=True)

        # 3. Reset watchdog timer
        watchdog.reset_timeout(agent)

        # 4. Calculate next expected heartbeat (30 seconds)
        next_expected = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).timestamp() + 30

        await ctx.info(f"Heartbeat processed for {agent}, next expected at {next_expected}")

        return HeartbeatResponse(
            status='alive',
            agent=agent,
            timestamp=timestamp,
            next_expected=next_expected,
            db_updated=True,
            message=f"Heartbeat recorded successfully for {agent}"
        )

    except Exception as e:
        logger.error(f"Heartbeat processing failed for {agent}: {e}")
        await ctx.error(f"Failed to process heartbeat: {str(e)}")

        return HeartbeatResponse(
            status='error',
            agent=agent,
            timestamp=timestamp,
            next_expected=0,
            db_updated=False,
            message=f"Error processing heartbeat: {str(e)}"
        )

@mcp.tool()
async def update_status(
    agent: str,
    status: str,
    task: Optional[str] = None,
    ctx: Context[ServerSession, None] = None
) -> StatusUpdateResponse:
    """
    Update agent status (idle, busy, error, offline).
    Tracks status history and manages task assignments.
    """
    valid_statuses = ['idle', 'busy', 'error', 'offline']

    if status not in valid_statuses:
        raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

    try:
        if ctx:
            await ctx.info(f"Updating status for {agent} to {status}")

        # Update in database
        result = db_manager.update_agent_status(agent, status, task)

        # Publish status change event
        if message_bus.running:
            event = Event(
                type=EventType.AGENT_STATUS_CHANGED,
                source=agent,
                payload={
                    'agent': agent,
                    'status': status,
                    'previous_status': result['previous_status'],
                    'task': task
                }
            )
            message_bus.publish(event, sync=True)

        # If error status, might trigger alerts
        if status == 'error' and ctx:
            await ctx.warning(f"Agent {agent} reported error status")

        return StatusUpdateResponse(**result)

    except Exception as e:
        logger.error(f"Status update failed for {agent}: {e}")
        raise

@mcp.tool()
async def log_activity(
    agent: str,
    category: str,
    activity: str,
    details: Dict[str, Any] = None,
    ctx: Context[ServerSession, None] = None
) -> ActivityLogResponse:
    """
    Log agent activity for audit and monitoring.
    Categories: task, error, info, warning, debug.
    """
    try:
        if ctx:
            await ctx.info(f"Logging {category} activity for {agent}: {activity}")

        # Log to database
        result = db_manager.log_activity(
            agent=agent,
            category=category,
            activity=activity,
            details=details or {}
        )

        # Publish activity event
        if message_bus.running:
            event = Event(
                type=EventType.ACTIVITY_LOGGED,
                source=agent,
                payload={
                    'category': category,
                    'activity': activity,
                    'details': details
                }
            )
            message_bus.publish(event, sync=True)

        # Stream to dashboard if it's an important activity
        if category in ['error', 'warning'] and ctx:
            await ctx.warning(f"{agent}: {activity}")

        return ActivityLogResponse(**result)

    except Exception as e:
        logger.error(f"Activity logging failed: {e}")
        raise

@mcp.tool()
async def check_conflicts(
    agents: List[str],
    ctx: Context[ServerSession, None] = None
) -> ConflictCheckResponse:
    """
    Check for conflicts between multiple agents.
    Detects if agents are working on the same components.
    """
    try:
        if ctx:
            await ctx.info(f"Checking conflicts between agents: {agents}")

        # Query database for conflicts
        result = db_manager.check_conflicts(agents)

        # If conflicts found, publish alert
        if result['conflicts'] and message_bus.running:
            event = Event(
                type=EventType.CONFLICT_DETECTED,
                source='conflict_checker',
                payload={
                    'conflicts': result['conflicts'],
                    'agents': agents
                }
            )
            message_bus.publish(event, sync=True)

            if ctx:
                await ctx.warning(f"Found {len(result['conflicts'])} conflicts")

        return ConflictCheckResponse(**result)

    except Exception as e:
        logger.error(f"Conflict check failed: {e}")
        raise

@mcp.tool()
async def register_component(
    name: str,
    type: str,
    owner: str,
    metadata: Optional[Dict[str, Any]] = None,
    ctx: Context[ServerSession, None] = None
) -> ComponentRegistrationResponse:
    """
    Register a new component created by an agent.
    Types: module, service, database, interface, config.
    """
    try:
        if ctx:
            await ctx.info(f"Registering component {name} owned by {owner}")

        # Register in database
        result = db_manager.register_component(
            name=name,
            type=type,
            owner=owner,
            metadata=metadata or {}
        )

        # Publish component creation event
        if message_bus.running:
            event = Event(
                type=EventType.COMPONENT_CREATED,
                source=owner,
                payload={
                    'component_id': result['component_id'],
                    'name': name,
                    'type': type,
                    'owner': owner
                }
            )
            message_bus.publish(event, sync=True)

        if ctx:
            await ctx.info(f"Component {name} registered successfully")

        return ComponentRegistrationResponse(**result)

    except ValueError as e:
        if ctx:
            await ctx.error(f"Component registration failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Component registration failed: {e}")
        raise

@mcp.tool()
async def request_collaboration(
    from_agent: str,
    to_agent: str,
    task: str,
    priority: int = 5,
    metadata: Optional[Dict[str, Any]] = None,
    ctx: Context[ServerSession, None] = None
) -> CollaborationRequestResponse:
    """
    Request collaboration between agents.
    Priority: 1 (lowest) to 10 (highest).
    """
    try:
        if ctx:
            await ctx.info(f"Creating collaboration request from {from_agent} to {to_agent}")

        # Create collaboration request
        result = db_manager.request_collaboration(
            from_agent=from_agent,
            to_agent=to_agent,
            task=task,
            priority=priority,
            metadata=metadata
        )

        # Publish collaboration request event
        if message_bus.running:
            event = Event(
                type=EventType.COLLABORATION_REQUEST,
                source=from_agent,
                target=to_agent,
                payload={
                    'request_id': result['request_id'],
                    'task': task,
                    'priority': priority,
                    'status': result['status']
                }
            )
            message_bus.publish(event, sync=True)

        if ctx:
            status_msg = f"Collaboration request {result['status']}"
            if result['status'] == 'queued':
                await ctx.info(f"{status_msg} (position in queue: {result.get('queue_position', 'unknown')})")
            else:
                await ctx.info(status_msg)

        return CollaborationRequestResponse(**result)

    except Exception as e:
        logger.error(f"Collaboration request failed: {e}")
        raise

@mcp.tool()
async def propose_decision(
    agent: str,
    decision: str,
    category: str,
    confidence: float,
    alternatives: Optional[List[str]] = None,
    ctx: Context[ServerSession, None] = None
) -> DecisionProposalResponse:
    """
    Propose a decision that may require consensus.
    Categories: architecture, deployment, security, performance.
    Confidence: 0.0 to 1.0 (auto-approved if >= 0.95).
    """
    if not 0 <= confidence <= 1:
        raise ValueError("Confidence must be between 0 and 1")

    try:
        if ctx:
            await ctx.info(f"Agent {agent} proposing {category} decision with confidence {confidence}")

        # Propose decision
        result = db_manager.propose_decision(
            agent=agent,
            decision=decision,
            category=category,
            confidence=confidence,
            alternatives=alternatives or []
        )

        # Publish decision proposal event
        if message_bus.running:
            event = Event(
                type=EventType.DECISION_PROPOSED,
                source=agent,
                payload={
                    'decision_id': result['decision_id'],
                    'decision': decision,
                    'category': category,
                    'confidence': confidence,
                    'status': result['status']
                }
            )
            message_bus.publish(event, sync=True)

        if ctx:
            if result['status'] == 'auto_approved':
                await ctx.info(f"Decision auto-approved due to high confidence ({confidence})")
            else:
                await ctx.info(f"Decision pending votes from other agents")

        # Add auto_approved field
        result['auto_approved'] = result['status'] == 'auto_approved'

        return DecisionProposalResponse(**result)

    except Exception as e:
        logger.error(f"Decision proposal failed: {e}")
        raise

@mcp.tool()
async def find_component_owner(
    component: str,
    ctx: Context[ServerSession, None] = None
) -> ComponentOwnerResponse:
    """
    Find which agent owns a specific component.
    Uses database lookup with pattern matching fallback.
    """
    try:
        if ctx:
            await ctx.info(f"Finding owner for component: {component}")

        # Query database
        result = db_manager.find_component_owner(component)

        if ctx:
            if result['type'] == 'inferred':
                await ctx.info(f"Owner inferred from pattern matching: {result['owner']}")
            else:
                await ctx.info(f"Owner found in database: {result['owner']}")

        return ComponentOwnerResponse(**result)

    except Exception as e:
        logger.error(f"Component owner lookup failed: {e}")
        raise

# Server lifecycle handlers

@mcp.on_server_start()
async def on_start():
    """Initialize components when server starts"""
    logger.info("MCP Server starting...")

    # Start message bus
    if not message_bus.running:
        message_bus.start()

    # Start watchdog
    watchdog.start()

    logger.info("MCP Server ready")

@mcp.on_server_stop()
async def on_stop():
    """Cleanup when server stops"""
    logger.info("MCP Server stopping...")

    # Stop watchdog
    watchdog.stop()

    # Stop message bus
    if message_bus.running:
        message_bus.stop()

    # Close database
    db_manager.close()

    logger.info("MCP Server stopped")

# Main entry point
if __name__ == "__main__":
    import uvicorn

    # Run with uvicorn (FastMCP uses FastAPI internally)
    uvicorn.run(
        "mcp_server_compliant:mcp",
        host="0.0.0.0",
        port=8099,
        log_level="info",
        reload=True
    )