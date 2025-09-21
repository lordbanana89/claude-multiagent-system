#!/usr/bin/env python3
"""
MCP Server V2 - Following Official Python SDK Standards
Includes frontend state management and verification tools
"""

import asyncio
import json
import logging
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FrontendStateManager:
    """Manages frontend configuration state"""

    def __init__(self, db_path: str = "mcp_system.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize database with frontend tracking tables"""
        conn = sqlite3.connect(self.db_path)
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

        # API endpoints tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_endpoints (
                name TEXT PRIMARY KEY,
                url TEXT,
                method TEXT DEFAULT 'GET',
                expected_structure TEXT,
                last_verified TEXT,
                status TEXT DEFAULT 'unknown'
            )
        """)

        # Configuration snapshots
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                timestamp TEXT,
                components TEXT,
                endpoints TEXT,
                is_working INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()

    def get_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate hash of a file"""
        path = Path(file_path)
        if not path.exists():
            return None
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def track_component(self, name: str, file_path: str, config: Dict) -> Dict:
        """Track a frontend component"""
        file_hash = self.get_file_hash(file_path)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO frontend_components
            (name, file_path, file_hash, config, last_modified, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, file_path, file_hash, json.dumps(config),
              datetime.now().isoformat(), 'tracked'))

        conn.commit()
        conn.close()

        return {"status": "tracked", "hash": file_hash}

    def verify_component(self, name: str) -> Dict:
        """Verify if component has changed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT file_path, file_hash, config
            FROM frontend_components WHERE name = ?
        """, (name,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return {"status": "not_tracked", "name": name}

        file_path, stored_hash, config = row
        current_hash = self.get_file_hash(file_path)

        return {
            "status": "unchanged" if current_hash == stored_hash else "modified",
            "stored_hash": stored_hash,
            "current_hash": current_hash,
            "config": json.loads(config) if config else {}
        }

    def verify_all_components(self) -> List[Dict]:
        """Verify all tracked components"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM frontend_components")
        components = cursor.fetchall()
        conn.close()

        results = []
        for (name,) in components:
            results.append(self.verify_component(name))

        return results

class MCPServerV2:
    """MCP Server following official SDK standards"""

    def __init__(self):
        self.server = Server("claude-multiagent-mcp")
        self.frontend_manager = FrontendStateManager()
        self.setup_handlers()
        logger.info("MCP Server V2 initialized")

    def setup_handlers(self):
        """Setup MCP protocol handlers following SDK patterns"""

        # Resources handler
        @self.server.list_resources()
        async def handle_list_resources() -> list[types.Resource]:
            return [
                types.Resource(
                    uri="mcp://frontend/status",
                    name="Frontend Status",
                    description="Current status of frontend components",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="mcp://agents/status",
                    name="Agent Status",
                    description="Status of all agents in the system",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="mcp://system/config",
                    name="System Configuration",
                    description="Current system configuration",
                    mimeType="application/json"
                )
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            if uri == "mcp://frontend/status":
                return json.dumps(self.frontend_manager.verify_all_components())
            elif uri == "mcp://agents/status":
                return json.dumps(self.get_agent_status())
            elif uri == "mcp://system/config":
                return json.dumps(self.get_system_config())
            else:
                raise ValueError(f"Unknown resource: {uri}")

        # Tools handler
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return [
                # Frontend management tools
                types.Tool(
                    name="track_frontend_component",
                    description="Track a frontend component for changes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Component name"},
                            "file_path": {"type": "string", "description": "Path to component file"},
                            "config": {"type": "object", "description": "Component configuration"}
                        },
                        "required": ["name", "file_path"]
                    }
                ),
                types.Tool(
                    name="verify_frontend_component",
                    description="Check if a frontend component has been modified",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Component name to verify"}
                        },
                        "required": ["name"]
                    }
                ),
                types.Tool(
                    name="verify_all_frontend",
                    description="Verify all tracked frontend components",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                types.Tool(
                    name="test_api_endpoint",
                    description="Test an API endpoint",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "API endpoint URL"},
                            "method": {"type": "string", "description": "HTTP method", "default": "GET"}
                        },
                        "required": ["url"]
                    }
                ),
                # Agent coordination tools
                types.Tool(
                    name="init_agent",
                    description="Initialize an agent in the system",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string", "description": "Agent name"}
                        },
                        "required": ["agent"]
                    }
                ),
                types.Tool(
                    name="heartbeat",
                    description="Send heartbeat from an agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string", "description": "Agent name"}
                        },
                        "required": ["agent"]
                    }
                ),
                types.Tool(
                    name="log_activity",
                    description="Log an agent activity",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string", "description": "Agent name"},
                            "activity": {"type": "string", "description": "Activity description"},
                            "category": {"type": "string", "description": "Activity category"}
                        },
                        "required": ["agent", "activity"]
                    }
                ),
                types.Tool(
                    name="get_agent_status",
                    description="Get status of a specific agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string", "description": "Agent name"}
                        },
                        "required": ["agent"]
                    }
                ),
                types.Tool(
                    name="send_message",
                    description="Send message between agents",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "from_agent": {"type": "string", "description": "Sender agent"},
                            "to_agent": {"type": "string", "description": "Recipient agent"},
                            "message": {"type": "string", "description": "Message content"}
                        },
                        "required": ["from_agent", "to_agent", "message"]
                    }
                ),
                types.Tool(
                    name="read_inbox",
                    description="Read messages for an agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string", "description": "Agent name"}
                        },
                        "required": ["agent"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Any) -> list[types.TextContent]:
            try:
                result = await self.execute_tool(name, arguments)
                return [types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)})
                )]

    async def execute_tool(self, name: str, arguments: Dict) -> Dict:
        """Execute a tool with given arguments"""

        # Frontend tools
        if name == "track_frontend_component":
            return self.frontend_manager.track_component(
                arguments["name"],
                arguments["file_path"],
                arguments.get("config", {})
            )

        elif name == "verify_frontend_component":
            return self.frontend_manager.verify_component(arguments["name"])

        elif name == "verify_all_frontend":
            return {"components": self.frontend_manager.verify_all_components()}

        elif name == "test_api_endpoint":
            return await self.test_api_endpoint(
                arguments["url"],
                arguments.get("method", "GET")
            )

        # Agent tools
        elif name == "init_agent":
            return self.init_agent(arguments["agent"])

        elif name == "heartbeat":
            return self.heartbeat(arguments["agent"])

        elif name == "log_activity":
            return self.log_activity(
                arguments["agent"],
                arguments["activity"],
                arguments.get("category", "general")
            )

        elif name == "get_agent_status":
            return self.get_agent_status(arguments.get("agent"))

        elif name == "send_message":
            return self.send_message(
                arguments["from_agent"],
                arguments["to_agent"],
                arguments["message"]
            )

        elif name == "read_inbox":
            return self.read_inbox(arguments["agent"])

        else:
            raise ValueError(f"Unknown tool: {name}")

    async def test_api_endpoint(self, url: str, method: str) -> Dict:
        """Test an API endpoint"""
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url) as response:
                    data = await response.json()
                    return {
                        "status": "success",
                        "status_code": response.status,
                        "data_sample": str(data)[:200]
                    }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def init_agent(self, agent: str) -> Dict:
        """Initialize an agent"""
        conn = sqlite3.connect("mcp_system.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO agent_states
            (agent, last_seen, status, current_task)
            VALUES (?, ?, 'active', 'initialized')
        """, (agent, datetime.now().isoformat()))

        conn.commit()
        conn.close()

        return {"status": "initialized", "agent": agent}

    def heartbeat(self, agent: str) -> Dict:
        """Update agent heartbeat"""
        conn = sqlite3.connect("mcp_system.db")
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE agent_states
            SET last_seen = ?
            WHERE agent = ?
        """, (datetime.now().isoformat(), agent))

        conn.commit()
        conn.close()

        return {"status": "heartbeat_received", "agent": agent}

    def log_activity(self, agent: str, activity: str, category: str) -> Dict:
        """Log an agent activity"""
        conn = sqlite3.connect("mcp_system.db")
        cursor = conn.cursor()

        activity_id = f"{agent}_{int(datetime.now().timestamp())}"

        cursor.execute("""
            INSERT INTO activities
            (id, agent, timestamp, activity, category, status)
            VALUES (?, ?, ?, ?, ?, 'completed')
        """, (activity_id, agent, datetime.now().isoformat(), activity, category))

        conn.commit()
        conn.close()

        return {"status": "logged", "id": activity_id}

    def get_agent_status(self, agent: Optional[str] = None) -> Dict:
        """Get agent status"""
        conn = sqlite3.connect("mcp_system.db")
        cursor = conn.cursor()

        if agent:
            cursor.execute("""
                SELECT agent, status, last_seen, current_task
                FROM agent_states WHERE agent = ?
            """, (agent,))
            row = cursor.fetchone()
            if row:
                result = {
                    "agent": row[0],
                    "status": row[1],
                    "last_seen": row[2],
                    "current_task": row[3]
                }
            else:
                result = {"error": f"Agent {agent} not found"}
        else:
            cursor.execute("""
                SELECT agent, status, last_seen, current_task
                FROM agent_states
            """)
            rows = cursor.fetchall()
            result = {
                "agents": [
                    {
                        "agent": row[0],
                        "status": row[1],
                        "last_seen": row[2],
                        "current_task": row[3]
                    }
                    for row in rows
                ]
            }

        conn.close()
        return result

    def send_message(self, from_agent: str, to_agent: str, message: str) -> Dict:
        """Send message between agents"""
        conn = sqlite3.connect("mcp_system.db")
        cursor = conn.cursor()

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

        cursor.execute("""
            INSERT INTO messages (from_agent, to_agent, message, timestamp)
            VALUES (?, ?, ?, ?)
        """, (from_agent, to_agent, message, datetime.now().isoformat()))

        conn.commit()
        conn.close()

        return {"status": "sent", "from": from_agent, "to": to_agent}

    def read_inbox(self, agent: str) -> Dict:
        """Read messages for an agent"""
        conn = sqlite3.connect("mcp_system.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT from_agent, message, timestamp
            FROM messages
            WHERE to_agent = ? AND read = 0
            ORDER BY timestamp DESC
            LIMIT 10
        """, (agent,))

        messages = cursor.fetchall()

        cursor.execute("""
            UPDATE messages SET read = 1
            WHERE to_agent = ?
        """, (agent,))

        conn.commit()
        conn.close()

        return {
            "messages": [
                {
                    "from": msg[0],
                    "message": msg[1],
                    "timestamp": msg[2]
                }
                for msg in messages
            ]
        }

    def get_system_config(self) -> Dict:
        """Get current system configuration"""
        return {
            "frontend": {
                "api_url": "http://localhost:5001",
                "polling_interval": 10000
            },
            "agents": [
                "supervisor", "master", "backend-api", "database",
                "frontend-ui", "testing", "queue-manager",
                "instagram", "deployment"
            ],
            "database": "mcp_system.db"
        }

    async def run(self):
        """Run the MCP server"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="claude-multiagent-mcp",
                    server_version="2.0.0",
                    capabilities={
                        "resources": {},
                        "tools": {},
                        "prompts": {}
                    }
                )
            )

async def main():
    """Main entry point"""
    server = MCPServerV2()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())