#!/usr/bin/env python3
"""
Complete MCP Server Implementation for Claude Multi-Agent System
Production-ready server with full coordination capabilities
"""

import asyncio
import json
import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
import hashlib
import re

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mcp_coordinator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class AgentActivity:
    """Represents an agent activity"""
    id: str
    agent: str
    timestamp: str
    activity: str
    category: str
    metadata: Dict[str, Any]
    status: str = "completed"


@dataclass
class SharedComponent:
    """Represents a shared component in the system"""
    id: str
    name: str
    type: str  # api, database, frontend, test
    owner: str
    description: str
    dependencies: List[str]
    interfaces: Dict[str, Any]
    created_at: str
    updated_at: str
    version: int


@dataclass
class Decision:
    """Represents a coordinated decision"""
    id: str
    proposer: str
    decision: str
    options: List[str]
    votes: Dict[str, str]
    status: str  # pending, approved, rejected
    consensus_required: bool
    created_at: str
    resolved_at: Optional[str]


class PersistenceLayer:
    """SQLite persistence for MCP state"""

    def __init__(self, db_path: str = "/tmp/mcp_state.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.init_database()

    def init_database(self):
        """Initialize database schema"""
        cursor = self.conn.cursor()

        # Activities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id TEXT PRIMARY KEY,
                agent TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                activity TEXT NOT NULL,
                category TEXT NOT NULL,
                metadata TEXT,
                status TEXT DEFAULT 'completed'
            )
        """)

        # Components table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS components (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                owner TEXT NOT NULL,
                description TEXT,
                dependencies TEXT,
                interfaces TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                UNIQUE(name, type)
            )
        """)

        # Decisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY,
                proposer TEXT NOT NULL,
                decision TEXT NOT NULL,
                options TEXT,
                votes TEXT,
                status TEXT DEFAULT 'pending',
                consensus_required BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL,
                resolved_at TEXT
            )
        """)

        # Agent states table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_states (
                agent TEXT PRIMARY KEY,
                last_seen TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                current_task TEXT,
                capabilities TEXT,
                metadata TEXT
            )
        """)

        # Conflicts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflicts (
                id TEXT PRIMARY KEY,
                agent1 TEXT NOT NULL,
                agent2 TEXT NOT NULL,
                component TEXT NOT NULL,
                conflict_type TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                resolved BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL,
                resolved_at TEXT
            )
        """)

        self.conn.commit()

    def add_activity(self, activity: AgentActivity) -> bool:
        """Add an activity to the database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO activities (id, agent, timestamp, activity, category, metadata, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            activity.id,
            activity.agent,
            activity.timestamp,
            activity.activity,
            activity.category,
            json.dumps(activity.metadata),
            activity.status
        ))
        self.conn.commit()
        return True

    def get_recent_activities(self, limit: int = 50) -> List[AgentActivity]:
        """Get recent activities"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM activities
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        activities = []
        for row in cursor.fetchall():
            activities.append(AgentActivity(
                id=row['id'],
                agent=row['agent'],
                timestamp=row['timestamp'],
                activity=row['activity'],
                category=row['category'],
                metadata=json.loads(row['metadata'] or '{}'),
                status=row['status']
            ))
        return activities

    def register_component(self, component: SharedComponent) -> bool:
        """Register or update a component"""
        cursor = self.conn.cursor()

        # Check if component exists
        cursor.execute("""
            SELECT version FROM components
            WHERE name = ? AND type = ?
        """, (component.name, component.type))

        existing = cursor.fetchone()

        if existing:
            # Update existing component
            new_version = existing['version'] + 1
            cursor.execute("""
                UPDATE components
                SET description = ?, dependencies = ?, interfaces = ?,
                    updated_at = ?, version = ?, owner = ?
                WHERE name = ? AND type = ?
            """, (
                component.description,
                json.dumps(component.dependencies),
                json.dumps(component.interfaces),
                datetime.now().isoformat(),
                new_version,
                component.owner,
                component.name,
                component.type
            ))
        else:
            # Insert new component
            cursor.execute("""
                INSERT INTO components (id, name, type, owner, description,
                                      dependencies, interfaces, created_at, updated_at, version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                component.id,
                component.name,
                component.type,
                component.owner,
                component.description,
                json.dumps(component.dependencies),
                json.dumps(component.interfaces),
                component.created_at,
                component.updated_at,
                1
            ))

        self.conn.commit()
        return True

    def get_components(self, component_type: Optional[str] = None) -> List[SharedComponent]:
        """Get all components or by type"""
        cursor = self.conn.cursor()

        if component_type:
            cursor.execute("SELECT * FROM components WHERE type = ?", (component_type,))
        else:
            cursor.execute("SELECT * FROM components")

        components = []
        for row in cursor.fetchall():
            components.append(SharedComponent(
                id=row['id'],
                name=row['name'],
                type=row['type'],
                owner=row['owner'],
                description=row['description'],
                dependencies=json.loads(row['dependencies'] or '[]'),
                interfaces=json.loads(row['interfaces'] or '{}'),
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                version=row['version']
            ))
        return components


class ConflictDetector:
    """Advanced conflict detection system"""

    def __init__(self, persistence: PersistenceLayer):
        self.persistence = persistence

        # Define conflict patterns
        self.conflict_patterns = [
            # API conflicts
            (r"/api/(\w+)", r"/api/\1", "api_endpoint", "high"),
            # Database conflicts
            (r"CREATE TABLE (\w+)", r"ALTER TABLE \1", "schema", "high"),
            (r"ALTER TABLE (\w+)", r"DROP TABLE \1", "schema", "critical"),
            # Component conflicts
            (r"(\w+)Controller", r"\1Service", "dependency", "medium"),
            # File conflicts
            (r"editing (.*\.py)", r"deleting \1", "file", "critical"),
        ]

    def check_conflicts(
        self,
        agent: str,
        planned_action: str,
        component: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Check for conflicts with other agents' work"""
        conflicts = []

        # Get recent activities from other agents
        recent_activities = self.persistence.get_recent_activities(100)

        for activity in recent_activities:
            if activity.agent == agent:
                continue  # Skip own activities

            # Check pattern-based conflicts
            for pattern1, pattern2, conflict_type, severity in self.conflict_patterns:
                if (re.search(pattern1, planned_action, re.IGNORECASE) and
                    re.search(pattern2, activity.activity, re.IGNORECASE)):
                    conflicts.append({
                        "agent": activity.agent,
                        "activity": activity.activity,
                        "type": conflict_type,
                        "severity": severity,
                        "timestamp": activity.timestamp
                    })

            # Check component-based conflicts
            if component:
                components = self.persistence.get_components()
                for comp in components:
                    if comp.name == component and comp.owner != agent:
                        conflicts.append({
                            "agent": comp.owner,
                            "activity": f"Owns component {comp.name}",
                            "type": "ownership",
                            "severity": "high",
                            "timestamp": comp.updated_at
                        })

        return conflicts

    def suggest_resolution(self, conflicts: List[Dict]) -> str:
        """Suggest resolution for conflicts"""
        if not conflicts:
            return "No conflicts detected. Safe to proceed."

        critical = [c for c in conflicts if c['severity'] == 'critical']
        high = [c for c in conflicts if c['severity'] == 'high']

        if critical:
            return f"CRITICAL: {len(critical)} critical conflicts. Must coordinate with {', '.join(set(c['agent'] for c in critical))} immediately."

        if high:
            return f"HIGH: {len(high)} high-priority conflicts. Coordinate with {', '.join(set(c['agent'] for c in high))} before proceeding."

        return "MEDIUM: Minor conflicts detected. Review and proceed with caution."


class CoordinatorServer:
    """Complete MCP Server for Multi-Agent Coordination"""

    def __init__(self):
        self.server = Server("claude-multi-agent-coordinator")
        self.persistence = PersistenceLayer()
        self.conflict_detector = ConflictDetector(self.persistence)
        self.active_agents: Set[str] = set()
        self.last_heartbeat: Dict[str, float] = {}

        # Initialize server
        self.setup_handlers()
        logger.info("MCP Coordinator Server initialized")

    def setup_handlers(self):
        """Setup all MCP protocol handlers"""

        @self.server.list_resources()
        async def handle_list_resources() -> list[types.Resource]:
            """List available resources"""
            return [
                types.Resource(
                    uri="context://system/state",
                    name="Complete System State",
                    description="Full state of the multi-agent system",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="context://system/activities",
                    name="Recent Activities",
                    description="Recent activities from all agents",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="context://system/components",
                    name="System Components",
                    description="All registered components in the system",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="context://system/decisions",
                    name="Pending Decisions",
                    description="Decisions requiring coordination",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="context://system/agents",
                    name="Active Agents",
                    description="Currently active agents and their status",
                    mimeType="application/json"
                )
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read a specific resource"""
            if uri == "context://system/state":
                return self._get_system_state()
            elif uri == "context://system/activities":
                return self._get_recent_activities()
            elif uri == "context://system/components":
                return self._get_components()
            elif uri == "context://system/decisions":
                return self._get_pending_decisions()
            elif uri == "context://system/agents":
                return self._get_active_agents()
            else:
                raise ValueError(f"Unknown resource: {uri}")

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List all available coordination tools"""
            return [
                # Activity tracking
                types.Tool(
                    name="log_activity",
                    description="Log an agent activity to shared context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string", "description": "Agent name"},
                            "activity": {"type": "string", "description": "Description of activity"},
                            "category": {
                                "type": "string",
                                "enum": ["planning", "implementation", "testing", "completion", "error"],
                                "description": "Category of activity"
                            },
                            "metadata": {"type": "object", "description": "Additional metadata"}
                        },
                        "required": ["agent", "activity"]
                    }
                ),

                # Conflict detection
                types.Tool(
                    name="check_conflicts",
                    description="Check if planned action conflicts with other agents",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string"},
                            "planned_action": {"type": "string"},
                            "component": {"type": "string"}
                        },
                        "required": ["agent", "planned_action"]
                    }
                ),

                # Component registration
                types.Tool(
                    name="register_component",
                    description="Register a component being worked on",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string"},
                            "name": {"type": "string"},
                            "type": {
                                "type": "string",
                                "enum": ["api", "database", "frontend", "service", "test"]
                            },
                            "description": {"type": "string"},
                            "dependencies": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "interfaces": {"type": "object"}
                        },
                        "required": ["agent", "name", "type"]
                    }
                ),

                # Agent coordination
                types.Tool(
                    name="request_collaboration",
                    description="Request collaboration from other agents",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "requesting_agent": {"type": "string"},
                            "target_agents": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "task": {"type": "string"},
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high", "critical"]
                            }
                        },
                        "required": ["requesting_agent", "task"]
                    }
                ),

                # Decision coordination
                types.Tool(
                    name="propose_decision",
                    description="Propose a decision requiring coordination",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string"},
                            "decision": {"type": "string"},
                            "options": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "requires_consensus": {"type": "boolean"}
                        },
                        "required": ["agent", "decision"]
                    }
                ),

                # Status updates
                types.Tool(
                    name="update_status",
                    description="Update agent status",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string"},
                            "status": {
                                "type": "string",
                                "enum": ["idle", "working", "blocked", "completed"]
                            },
                            "current_task": {"type": "string"}
                        },
                        "required": ["agent", "status"]
                    }
                ),

                # Query tools
                types.Tool(
                    name="get_agent_responsibilities",
                    description="Get responsibilities for specific agents",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string"}
                        }
                    }
                ),

                types.Tool(
                    name="find_component_owner",
                    description="Find which agent owns a component",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "component_name": {"type": "string"},
                            "component_type": {"type": "string"}
                        },
                        "required": ["component_name"]
                    }
                ),

                # Synchronization
                types.Tool(
                    name="request_sync",
                    description="Request synchronization point with other agents",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string"},
                            "sync_point": {"type": "string"},
                            "wait_for": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["agent", "sync_point"]
                    }
                ),

                # Heartbeat
                types.Tool(
                    name="heartbeat",
                    description="Send heartbeat to indicate agent is active",
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
        async def handle_call_tool(
            name: str,
            arguments: dict | None
        ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Handle tool calls from agents"""

            try:
                if name == "log_activity":
                    return await self._handle_log_activity(arguments)

                elif name == "check_conflicts":
                    return await self._handle_check_conflicts(arguments)

                elif name == "register_component":
                    return await self._handle_register_component(arguments)

                elif name == "request_collaboration":
                    return await self._handle_request_collaboration(arguments)

                elif name == "propose_decision":
                    return await self._handle_propose_decision(arguments)

                elif name == "update_status":
                    return await self._handle_update_status(arguments)

                elif name == "get_agent_responsibilities":
                    return await self._handle_get_responsibilities(arguments)

                elif name == "find_component_owner":
                    return await self._handle_find_owner(arguments)

                elif name == "request_sync":
                    return await self._handle_request_sync(arguments)

                elif name == "heartbeat":
                    return await self._handle_heartbeat(arguments)

                else:
                    raise ValueError(f"Unknown tool: {name}")

            except Exception as e:
                logger.error(f"Error handling tool {name}: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"❌ Error: {str(e)}"
                )]

    async def _handle_log_activity(self, args: Dict) -> list[types.TextContent]:
        """Handle activity logging"""
        activity = AgentActivity(
            id=hashlib.md5(f"{args['agent']}{time.time()}".encode()).hexdigest(),
            agent=args["agent"],
            timestamp=datetime.now().isoformat(),
            activity=args["activity"],
            category=args.get("category", "implementation"),
            metadata=args.get("metadata", {}),
            status="completed"
        )

        self.persistence.add_activity(activity)

        # Log to file for external monitoring
        with open("/tmp/mcp_shared_context.log", "a") as f:
            f.write(f"[{activity.timestamp}] {activity.agent}: {activity.activity}\n")

        logger.info(f"Activity logged: {activity.agent} - {activity.activity}")

        return [types.TextContent(
            type="text",
            text=f"✅ Activity logged successfully"
        )]

    async def _handle_check_conflicts(self, args: Dict) -> list[types.TextContent]:
        """Handle conflict checking"""
        conflicts = self.conflict_detector.check_conflicts(
            args["agent"],
            args["planned_action"],
            args.get("component")
        )

        resolution = self.conflict_detector.suggest_resolution(conflicts)

        response = {
            "has_conflicts": len(conflicts) > 0,
            "conflict_count": len(conflicts),
            "conflicts": conflicts,
            "recommendation": resolution
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(response, indent=2)
        )]

    async def _handle_register_component(self, args: Dict) -> list[types.TextContent]:
        """Handle component registration"""
        component = SharedComponent(
            id=hashlib.md5(f"{args['name']}{args['type']}".encode()).hexdigest(),
            name=args["name"],
            type=args["type"],
            owner=args["agent"],
            description=args.get("description", ""),
            dependencies=args.get("dependencies", []),
            interfaces=args.get("interfaces", {}),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            version=1
        )

        self.persistence.register_component(component)

        return [types.TextContent(
            type="text",
            text=f"✅ Component '{component.name}' registered as {component.type}"
        )]

    async def _handle_request_collaboration(self, args: Dict) -> list[types.TextContent]:
        """Handle collaboration requests"""
        # Log the collaboration request
        activity = AgentActivity(
            id=hashlib.md5(f"collab{time.time()}".encode()).hexdigest(),
            agent=args["requesting_agent"],
            timestamp=datetime.now().isoformat(),
            activity=f"Requesting collaboration: {args['task']}",
            category="planning",
            metadata={
                "target_agents": args.get("target_agents", ["all"]),
                "priority": args.get("priority", "medium")
            },
            status="pending"
        )

        self.persistence.add_activity(activity)

        # Notify target agents (in a real implementation, this would trigger notifications)
        targets = args.get("target_agents", ["all agents"])

        return [types.TextContent(
            type="text",
            text=f"✅ Collaboration request sent to {', '.join(targets)}\nTask: {args['task']}\nPriority: {args.get('priority', 'medium')}"
        )]

    async def _handle_propose_decision(self, args: Dict) -> list[types.TextContent]:
        """Handle decision proposals"""
        decision_content = f"{args['decision']}{time.time()}"
        decision_id = f"decision_{hashlib.md5(decision_content.encode()).hexdigest()[:8]}"

        # Store decision in database
        cursor = self.persistence.conn.cursor()
        cursor.execute("""
            INSERT INTO decisions (id, proposer, decision, options, votes, status,
                                  consensus_required, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            decision_id,
            args["agent"],
            args["decision"],
            json.dumps(args.get("options", [])),
            json.dumps({}),
            "pending",
            args.get("requires_consensus", False),
            datetime.now().isoformat()
        ))
        self.persistence.conn.commit()

        return [types.TextContent(
            type="text",
            text=f"✅ Decision proposed: {decision_id}\nDecision: {args['decision']}\nStatus: Pending"
        )]

    async def _handle_update_status(self, args: Dict) -> list[types.TextContent]:
        """Handle status updates"""
        cursor = self.persistence.conn.cursor()

        # Update or insert agent status
        cursor.execute("""
            INSERT OR REPLACE INTO agent_states (agent, last_seen, status, current_task)
            VALUES (?, ?, ?, ?)
        """, (
            args["agent"],
            datetime.now().isoformat(),
            args["status"],
            args.get("current_task", "")
        ))
        self.persistence.conn.commit()

        self.active_agents.add(args["agent"])
        self.last_heartbeat[args["agent"]] = time.time()

        return [types.TextContent(
            type="text",
            text=f"✅ Status updated: {args['agent']} is now {args['status']}"
        )]

    async def _handle_get_responsibilities(self, args: Dict) -> list[types.TextContent]:
        """Get agent responsibilities"""
        responsibilities = {
            "backend-api": ["API endpoints", "Business logic", "Authentication", "Data validation"],
            "database": ["Schema design", "Migrations", "Query optimization", "Data integrity"],
            "frontend-ui": ["User interface", "User experience", "Client-side logic", "Styling"],
            "testing": ["Unit tests", "Integration tests", "E2E tests", "Test coverage"],
            "supervisor": ["Coordination", "Task assignment", "Conflict resolution", "Progress tracking"]
        }

        agent = args.get("agent", "all")
        if agent == "all":
            return [types.TextContent(
                type="text",
                text=json.dumps(responsibilities, indent=2)
            )]
        else:
            return [types.TextContent(
                type="text",
                text=json.dumps({agent: responsibilities.get(agent, [])}, indent=2)
            )]

    async def _handle_find_owner(self, args: Dict) -> list[types.TextContent]:
        """Find component owner"""
        components = self.persistence.get_components()

        for component in components:
            if component.name == args["component_name"]:
                if not args.get("component_type") or component.type == args.get("component_type"):
                    return [types.TextContent(
                        type="text",
                        text=f"Component '{component.name}' (type: {component.type}) is owned by {component.owner}"
                    )]

        return [types.TextContent(
            type="text",
            text=f"Component '{args['component_name']}' not found in registry"
        )]

    async def _handle_request_sync(self, args: Dict) -> list[types.TextContent]:
        """Handle synchronization requests"""
        sync_activity = AgentActivity(
            id=hashlib.md5(f"sync{time.time()}".encode()).hexdigest(),
            agent=args["agent"],
            timestamp=datetime.now().isoformat(),
            activity=f"Requesting sync point: {args['sync_point']}",
            category="planning",
            metadata={
                "sync_point": args["sync_point"],
                "waiting_for": args.get("wait_for", [])
            },
            status="pending"
        )

        self.persistence.add_activity(sync_activity)

        return [types.TextContent(
            type="text",
            text=f"✅ Sync point created: {args['sync_point']}\nWaiting for: {', '.join(args.get('wait_for', ['all agents']))}"
        )]

    async def _handle_heartbeat(self, args: Dict) -> list[types.TextContent]:
        """Handle agent heartbeat"""
        agent = args["agent"]
        self.active_agents.add(agent)
        self.last_heartbeat[agent] = time.time()

        return [types.TextContent(
            type="text",
            text=f"❤️ Heartbeat received from {agent}"
        )]

    def _get_system_state(self) -> str:
        """Get complete system state"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "active_agents": list(self.active_agents),
            "total_activities": len(self.persistence.get_recent_activities(1000)),
            "components": len(self.persistence.get_components()),
            "recent_activities": [
                {
                    "agent": a.agent,
                    "activity": a.activity,
                    "timestamp": a.timestamp
                } for a in self.persistence.get_recent_activities(10)
            ]
        }
        return json.dumps(state, indent=2)

    def _get_recent_activities(self) -> str:
        """Get recent activities"""
        activities = self.persistence.get_recent_activities(50)
        return json.dumps([asdict(a) for a in activities], indent=2)

    def _get_components(self) -> str:
        """Get all components"""
        components = self.persistence.get_components()
        return json.dumps([asdict(c) for c in components], indent=2)

    def _get_pending_decisions(self) -> str:
        """Get pending decisions"""
        cursor = self.persistence.conn.cursor()
        cursor.execute("""
            SELECT * FROM decisions WHERE status = 'pending'
        """)

        decisions = []
        for row in cursor.fetchall():
            decisions.append({
                "id": row['id'],
                "proposer": row['proposer'],
                "decision": row['decision'],
                "options": json.loads(row['options'] or '[]'),
                "created_at": row['created_at']
            })

        return json.dumps(decisions, indent=2)

    def _get_active_agents(self) -> str:
        """Get active agents and their status"""
        cursor = self.persistence.conn.cursor()
        cursor.execute("""
            SELECT * FROM agent_states
            ORDER BY last_seen DESC
        """)

        agents = []
        now = time.time()

        for row in cursor.fetchall():
            agent = row['agent']
            last_heartbeat = self.last_heartbeat.get(agent, 0)
            is_active = (now - last_heartbeat) < 60  # Active if heartbeat within 60 seconds

            agents.append({
                "agent": agent,
                "status": row['status'],
                "current_task": row['current_task'],
                "last_seen": row['last_seen'],
                "is_active": is_active
            })

        return json.dumps(agents, indent=2)

    async def run(self):
        """Run the MCP server"""
        logger.info("Starting MCP Coordinator Server...")

        # Start background tasks
        asyncio.create_task(self._cleanup_inactive_agents())

        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="claude-multi-agent-coordinator",
                    server_version="2.0.0",
                    capabilities={}
                )
            )

    async def _cleanup_inactive_agents(self):
        """Background task to cleanup inactive agents"""
        while True:
            await asyncio.sleep(30)  # Check every 30 seconds

            now = time.time()
            inactive = []

            for agent, last_seen in self.last_heartbeat.items():
                if now - last_seen > 300:  # 5 minutes timeout
                    inactive.append(agent)

            for agent in inactive:
                self.active_agents.discard(agent)
                del self.last_heartbeat[agent]
                logger.info(f"Removed inactive agent: {agent}")


def main():
    """Main entry point"""
    server = CoordinatorServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()