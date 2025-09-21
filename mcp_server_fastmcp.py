#!/usr/bin/env python3
"""
MCP Server using FastMCP - Official SDK Implementation
Provides frontend state management and agent coordination
"""

import os
import sys
import sqlite3
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

# Configure logging to stderr to avoid stdio interference
logging.basicConfig(
    level=logging.WARNING,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)

# Initialize FastMCP server
mcp = FastMCP(name="claude-multiagent-system")

# Database path - use absolute path for Claude Desktop
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_system.db")

# ======================
# Database Initialization
# ======================

def init_database():
    """Initialize database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Agent states table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_states (
            agent TEXT PRIMARY KEY,
            last_seen TEXT,
            status TEXT,
            current_task TEXT
        )
    """)

    # Activities table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id TEXT PRIMARY KEY,
            agent TEXT,
            timestamp TEXT,
            activity TEXT,
            category TEXT,
            status TEXT DEFAULT 'completed'
        )
    """)

    # Messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_agent TEXT,
            to_agent TEXT,
            message TEXT,
            timestamp TEXT,
            read INTEGER DEFAULT 0
        )
    """)

    # Frontend components tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS frontend_components (
            name TEXT PRIMARY KEY,
            file_path TEXT,
            file_hash TEXT,
            config TEXT,
            last_modified TEXT,
            status TEXT DEFAULT 'unknown'
        )
    """)

    # API endpoints tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_endpoints (
            name TEXT PRIMARY KEY,
            url TEXT,
            method TEXT DEFAULT 'GET',
            expected_keys TEXT,
            last_verified TEXT,
            status TEXT DEFAULT 'unknown'
        )
    """)

    conn.commit()
    conn.close()

# Initialize database on import
init_database()

# ======================
# Helper Functions
# ======================

def get_file_hash(file_path: str) -> Optional[str]:
    """Calculate MD5 hash of a file"""
    path = Path(file_path)
    if not path.exists():
        return None
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

# ======================
# Data Classes
# ======================

@dataclass
class ComponentStatus:
    """Status of a frontend component"""
    name: str
    file_path: str
    status: str  # unchanged, modified, not_tracked
    stored_hash: Optional[str] = None
    current_hash: Optional[str] = None
    config: Optional[Dict] = None

@dataclass
class AgentStatus:
    """Status of an agent"""
    agent: str
    status: str
    last_seen: str
    current_task: Optional[str] = None

@dataclass
class Activity:
    """Agent activity record"""
    id: str
    agent: str
    timestamp: str
    activity: str
    category: str
    status: str = "completed"

# ======================
# Frontend Management Tools
# ======================

@mcp.tool()
def track_frontend_component(name: str, file_path: str, config: Optional[Dict[str, Any]] = None) -> Dict:
    """
    Track a frontend component for change detection.

    Args:
        name: Component name (must be unique)
        file_path: Absolute path to component file
        config: Optional configuration dict for the component

    Returns:
        Status dict with tracking result
    """
    file_hash = get_file_hash(file_path)
    if not file_hash:
        return {"status": "error", "message": f"File not found: {file_path}"}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO frontend_components
        (name, file_path, file_hash, config, last_modified, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, file_path, file_hash, json.dumps(config or {}),
          datetime.now().isoformat(), 'tracked'))

    conn.commit()
    conn.close()

    return {
        "status": "tracked",
        "name": name,
        "hash": file_hash,
        "message": f"Component {name} is now being tracked"
    }

@mcp.tool()
def verify_frontend_component(name: str) -> ComponentStatus:
    """
    Verify if a tracked component has been modified.

    Args:
        name: Component name to verify

    Returns:
        ComponentStatus with current state
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT file_path, file_hash, config
        FROM frontend_components WHERE name = ?
    """, (name,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return ComponentStatus(
            name=name,
            file_path="",
            status="not_tracked"
        )

    file_path, stored_hash, config_str = row
    current_hash = get_file_hash(file_path)

    return ComponentStatus(
        name=name,
        file_path=file_path,
        status="unchanged" if current_hash == stored_hash else "modified",
        stored_hash=stored_hash,
        current_hash=current_hash,
        config=json.loads(config_str) if config_str else None
    )

@mcp.tool()
def verify_all_frontend() -> List[ComponentStatus]:
    """
    Verify all tracked frontend components.

    Returns:
        List of ComponentStatus for all tracked components
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM frontend_components")
    components = cursor.fetchall()
    conn.close()

    results = []
    for (name,) in components:
        results.append(verify_frontend_component(name))

    return results

@mcp.tool()
def track_api_endpoint(name: str, url: str, method: str = "GET", expected_keys: Optional[List[str]] = None) -> Dict:
    """
    Track an API endpoint for monitoring.

    Args:
        name: Endpoint name
        url: Full URL of the endpoint
        method: HTTP method (default: GET)
        expected_keys: List of expected keys in response

    Returns:
        Status dict with tracking result
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO api_endpoints
        (name, url, method, expected_keys, last_verified, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, url, method, json.dumps(expected_keys or []),
          None, 'tracked'))

    conn.commit()
    conn.close()

    return {
        "status": "tracked",
        "name": name,
        "url": url,
        "method": method
    }

# ======================
# Agent Coordination Tools
# ======================

@mcp.tool()
def init_agent(agent: str) -> AgentStatus:
    """
    Initialize an agent in the system.

    Args:
        agent: Agent name

    Returns:
        AgentStatus with initialization result
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    timestamp = datetime.now().isoformat()
    cursor.execute("""
        INSERT OR REPLACE INTO agent_states
        (agent, last_seen, status, current_task)
        VALUES (?, ?, 'active', 'initialized')
    """, (agent, timestamp))

    conn.commit()
    conn.close()

    return AgentStatus(
        agent=agent,
        status="active",
        last_seen=timestamp,
        current_task="initialized"
    )

@mcp.tool()
def heartbeat(agent: str) -> Dict:
    """
    Send heartbeat for an agent.

    Args:
        agent: Agent name

    Returns:
        Dict with heartbeat status
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    timestamp = datetime.now().isoformat()
    cursor.execute("""
        UPDATE agent_states
        SET last_seen = ?
        WHERE agent = ?
    """, (timestamp, agent))

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    return {
        "status": "success" if affected > 0 else "agent_not_found",
        "agent": agent,
        "timestamp": timestamp
    }

@mcp.tool()
def log_activity(agent: str, activity: str, category: str = "general") -> Activity:
    """
    Log an agent activity.

    Args:
        agent: Agent name
        activity: Activity description
        category: Activity category (default: general)

    Returns:
        Activity record
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    activity_id = f"{agent}_{int(datetime.now().timestamp())}"
    timestamp = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO activities
        (id, agent, timestamp, activity, category, status)
        VALUES (?, ?, ?, ?, ?, 'completed')
    """, (activity_id, agent, timestamp, activity, category))

    conn.commit()
    conn.close()

    return Activity(
        id=activity_id,
        agent=agent,
        timestamp=timestamp,
        activity=activity,
        category=category,
        status="completed"
    )

@mcp.tool()
def get_agent_status(agent: Optional[str] = None) -> List[AgentStatus]:
    """
    Get status of agent(s).

    Args:
        agent: Optional agent name (if None, returns all agents)

    Returns:
        List of AgentStatus
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if agent:
        cursor.execute("""
            SELECT agent, status, last_seen, current_task
            FROM agent_states WHERE agent = ?
        """, (agent,))
    else:
        cursor.execute("""
            SELECT agent, status, last_seen, current_task
            FROM agent_states ORDER BY agent
        """)

    rows = cursor.fetchall()
    conn.close()

    return [
        AgentStatus(
            agent=row[0],
            status=row[1],
            last_seen=row[2],
            current_task=row[3]
        )
        for row in rows
    ]

@mcp.tool()
def send_message(from_agent: str, to_agent: str, message: str) -> Dict:
    """
    Send message between agents.

    Args:
        from_agent: Sender agent
        to_agent: Recipient agent
        message: Message content

    Returns:
        Dict with send status
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    timestamp = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO messages (from_agent, to_agent, message, timestamp)
        VALUES (?, ?, ?, ?)
    """, (from_agent, to_agent, message, timestamp))

    message_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "status": "sent",
        "message_id": message_id,
        "from": from_agent,
        "to": to_agent,
        "timestamp": timestamp
    }

@mcp.tool()
def read_inbox(agent: str, mark_as_read: bool = True) -> List[Dict]:
    """
    Read messages for an agent.

    Args:
        agent: Agent name
        mark_as_read: Whether to mark messages as read (default: True)

    Returns:
        List of messages
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, from_agent, message, timestamp
        FROM messages
        WHERE to_agent = ? AND read = 0
        ORDER BY timestamp DESC
        LIMIT 10
    """, (agent,))

    messages = []
    for row in cursor.fetchall():
        messages.append({
            "id": row[0],
            "from": row[1],
            "message": row[2],
            "timestamp": row[3]
        })

    if mark_as_read and messages:
        message_ids = [msg["id"] for msg in messages]
        placeholders = ','.join('?' * len(message_ids))
        cursor.execute(f"""
            UPDATE messages SET read = 1
            WHERE id IN ({placeholders})
        """, message_ids)

    conn.commit()
    conn.close()

    return messages

@mcp.tool()
def get_recent_activities(limit: int = 10) -> List[Activity]:
    """
    Get recent activities from all agents.

    Args:
        limit: Maximum number of activities to return (default: 10)

    Returns:
        List of recent activities
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, agent, timestamp, activity, category, status
        FROM activities
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))

    activities = []
    for row in cursor.fetchall():
        activities.append(Activity(
            id=row[0],
            agent=row[1],
            timestamp=row[2],
            activity=row[3],
            category=row[4],
            status=row[5]
        ))

    conn.close()
    return activities

# ======================
# Resources
# ======================

@mcp.resource("mcp://frontend/status")
def get_frontend_status() -> str:
    """Get current status of all frontend components"""
    components = verify_all_frontend()
    return json.dumps([{
        "name": c.name,
        "status": c.status,
        "file_path": c.file_path
    } for c in components], indent=2)

@mcp.resource("mcp://agents/status")
def get_all_agents_status() -> str:
    """Get status of all agents in the system"""
    agents = get_agent_status()
    return json.dumps([{
        "agent": a.agent,
        "status": a.status,
        "last_seen": a.last_seen,
        "current_task": a.current_task
    } for a in agents], indent=2)

@mcp.resource("mcp://system/config")
def get_system_config() -> str:
    """Get current system configuration"""
    return json.dumps({
        "database": DB_PATH,
        "agents": [
            "supervisor", "master", "backend-api", "database",
            "frontend-ui", "testing", "queue-manager",
            "instagram", "deployment"
        ],
        "api": {
            "main": "http://localhost:5001",
            "health": "http://localhost:5002",
            "auth": "http://localhost:5003"
        },
        "frontend": {
            "url": "http://localhost:5173",
            "polling_interval": 10000
        }
    }, indent=2)

# ======================
# Main Entry Point
# ======================

if __name__ == "__main__":
    import asyncio

    # Run with stdio mode for Claude Desktop
    asyncio.run(mcp.run_stdio_async())