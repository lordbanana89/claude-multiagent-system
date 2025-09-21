#!/usr/bin/env python3
"""
MCP Server optimized for Claude Desktop
Uses standard Server class with proper stdio handling
"""

import asyncio
import json
import sqlite3
import hashlib
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Configure logging to stderr to avoid stdio interference
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = "mcp_system.db"

def init_database():
    """Initialize database tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

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

    # Agent states
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_states (
            agent TEXT PRIMARY KEY,
            last_seen TEXT,
            status TEXT,
            current_task TEXT
        )
    """)

    # Activities
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

    # Messages
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

    conn.commit()
    conn.close()

def get_file_hash(file_path: str) -> Optional[str]:
    """Calculate file hash"""
    path = Path(file_path)
    if not path.exists():
        return None
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

class MCPServer:
    """MCP Server for Claude Multi-Agent System"""

    def __init__(self):
        self.server = Server("claude-multiagent-system")
        init_database()
        self.setup_handlers()

    def setup_handlers(self):
        """Setup all handlers"""

        @self.server.list_resources()
        async def handle_list_resources() -> list[types.Resource]:
            return [
                types.Resource(
                    uri="mcp://system/status",
                    name="System Status",
                    description="Current system status",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="mcp://frontend/components",
                    name="Frontend Components",
                    description="Tracked frontend components",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="mcp://agents/status",
                    name="Agent Status",
                    description="Status of all agents",
                    mimeType="application/json"
                )
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            if uri == "mcp://system/status":
                cursor.execute("SELECT COUNT(*) FROM agent_states WHERE status = 'active'")
                active = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM activities")
                activities = cursor.fetchone()[0]
                conn.close()
                return json.dumps({
                    "active_agents": active,
                    "total_activities": activities,
                    "database": DB_PATH
                })

            elif uri == "mcp://frontend/components":
                cursor.execute("SELECT * FROM frontend_components")
                components = []
                for row in cursor.fetchall():
                    components.append({
                        "name": row[0],
                        "file_path": row[1],
                        "status": row[5]
                    })
                conn.close()
                return json.dumps(components)

            elif uri == "mcp://agents/status":
                cursor.execute("SELECT * FROM agent_states")
                agents = []
                for row in cursor.fetchall():
                    agents.append({
                        "agent": row[0],
                        "status": row[2],
                        "last_seen": row[1]
                    })
                conn.close()
                return json.dumps(agents)

            else:
                conn.close()
                return json.dumps({"error": "Unknown resource"})

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return [
                # Frontend tracking
                types.Tool(
                    name="track_component",
                    description="Track a frontend component for changes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "file_path": {"type": "string"},
                            "config": {"type": "object"}
                        },
                        "required": ["name", "file_path"]
                    }
                ),
                types.Tool(
                    name="verify_component",
                    description="Check if a component has been modified",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"}
                        },
                        "required": ["name"]
                    }
                ),
                types.Tool(
                    name="list_components",
                    description="List all tracked components",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                # Agent coordination
                types.Tool(
                    name="init_agent",
                    description="Initialize an agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string"}
                        },
                        "required": ["agent"]
                    }
                ),
                types.Tool(
                    name="agent_heartbeat",
                    description="Send agent heartbeat",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string"}
                        },
                        "required": ["agent"]
                    }
                ),
                types.Tool(
                    name="log_activity",
                    description="Log an activity",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string"},
                            "activity": {"type": "string"},
                            "category": {"type": "string"}
                        },
                        "required": ["agent", "activity"]
                    }
                ),
                types.Tool(
                    name="send_message",
                    description="Send message between agents",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "from": {"type": "string"},
                            "to": {"type": "string"},
                            "message": {"type": "string"}
                        },
                        "required": ["from", "to", "message"]
                    }
                ),
                types.Tool(
                    name="read_messages",
                    description="Read messages for an agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string"}
                        },
                        "required": ["agent"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Any) -> list[types.TextContent]:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            result = {"status": "error", "message": "Unknown tool"}

            try:
                if name == "track_component":
                    file_hash = get_file_hash(arguments.get("file_path", ""))
                    cursor.execute("""
                        INSERT OR REPLACE INTO frontend_components
                        (name, file_path, file_hash, config, last_modified, status)
                        VALUES (?, ?, ?, ?, ?, 'tracked')
                    """, (
                        arguments["name"],
                        arguments["file_path"],
                        file_hash,
                        json.dumps(arguments.get("config", {})),
                        datetime.now().isoformat()
                    ))
                    conn.commit()
                    result = {
                        "status": "success",
                        "message": f"Component {arguments['name']} tracked",
                        "hash": file_hash
                    }

                elif name == "verify_component":
                    cursor.execute("""
                        SELECT file_path, file_hash FROM frontend_components
                        WHERE name = ?
                    """, (arguments["name"],))
                    row = cursor.fetchone()

                    if row:
                        current_hash = get_file_hash(row[0])
                        result = {
                            "status": "success",
                            "name": arguments["name"],
                            "modified": current_hash != row[1],
                            "stored_hash": row[1],
                            "current_hash": current_hash
                        }
                    else:
                        result = {
                            "status": "not_tracked",
                            "name": arguments["name"]
                        }

                elif name == "list_components":
                    cursor.execute("SELECT name, file_path, status FROM frontend_components")
                    components = []
                    for row in cursor.fetchall():
                        components.append({
                            "name": row[0],
                            "file_path": row[1],
                            "status": row[2]
                        })
                    result = {
                        "status": "success",
                        "components": components
                    }

                elif name == "init_agent":
                    cursor.execute("""
                        INSERT OR REPLACE INTO agent_states
                        (agent, last_seen, status, current_task)
                        VALUES (?, ?, 'active', 'initialized')
                    """, (arguments["agent"], datetime.now().isoformat()))
                    conn.commit()
                    result = {
                        "status": "success",
                        "agent": arguments["agent"]
                    }

                elif name == "agent_heartbeat":
                    cursor.execute("""
                        UPDATE agent_states
                        SET last_seen = ?
                        WHERE agent = ?
                    """, (datetime.now().isoformat(), arguments["agent"]))
                    conn.commit()
                    result = {
                        "status": "success",
                        "agent": arguments["agent"]
                    }

                elif name == "log_activity":
                    activity_id = f"{arguments['agent']}_{int(datetime.now().timestamp())}"
                    cursor.execute("""
                        INSERT INTO activities
                        (id, agent, timestamp, activity, category, status)
                        VALUES (?, ?, ?, ?, ?, 'completed')
                    """, (
                        activity_id,
                        arguments["agent"],
                        datetime.now().isoformat(),
                        arguments["activity"],
                        arguments.get("category", "general")
                    ))
                    conn.commit()
                    result = {
                        "status": "success",
                        "id": activity_id
                    }

                elif name == "send_message":
                    cursor.execute("""
                        INSERT INTO messages
                        (from_agent, to_agent, message, timestamp)
                        VALUES (?, ?, ?, ?)
                    """, (
                        arguments["from"],
                        arguments["to"],
                        arguments["message"],
                        datetime.now().isoformat()
                    ))
                    conn.commit()
                    result = {
                        "status": "success",
                        "from": arguments["from"],
                        "to": arguments["to"]
                    }

                elif name == "read_messages":
                    cursor.execute("""
                        SELECT from_agent, message, timestamp
                        FROM messages
                        WHERE to_agent = ? AND read = 0
                        ORDER BY timestamp DESC
                        LIMIT 10
                    """, (arguments["agent"],))

                    messages = []
                    for row in cursor.fetchall():
                        messages.append({
                            "from": row[0],
                            "message": row[1],
                            "timestamp": row[2]
                        })

                    cursor.execute("""
                        UPDATE messages SET read = 1
                        WHERE to_agent = ?
                    """, (arguments["agent"],))
                    conn.commit()

                    result = {
                        "status": "success",
                        "messages": messages
                    }

            except Exception as e:
                result = {
                    "status": "error",
                    "message": str(e)
                }
            finally:
                conn.close()

            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

    async def run(self):
        """Run the server with stdio"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="claude-multiagent-system",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities={}
                    )
                )
            )

async def main():
    """Main entry point"""
    logger.info("Starting MCP Server for Claude Desktop...")
    server = MCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())