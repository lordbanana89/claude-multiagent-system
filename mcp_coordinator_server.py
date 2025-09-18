#!/usr/bin/env python3
"""
MCP Server for Claude Multi-Agent Coordination
Provides shared context and coordination tools for Claude CLI agents
"""

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
from datetime import datetime
import json
import os
from typing import Dict, List, Any

class SharedContextServer:
    """MCP Server that maintains shared context between Claude agents"""

    def __init__(self):
        self.server = Server("claude-coordinator")
        self.shared_state = {
            "agents": {},
            "activities": [],
            "decisions": {},
            "conflicts": [],
            "project_structure": {
                "backend": {},
                "database": {},
                "frontend": {},
                "testing": {}
            }
        }

        # Setup handlers
        self.setup_handlers()

    def setup_handlers(self):
        """Setup MCP protocol handlers"""

        @self.server.list_resources()
        async def handle_list_resources() -> list[types.Resource]:
            """List available resources"""
            return [
                types.Resource(
                    uri="context://shared/state",
                    name="System State",
                    description="Complete shared state of the multi-agent system",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="context://shared/activities",
                    name="Agent Activities",
                    description="Recent activities from all agents",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="context://shared/decisions",
                    name="System Decisions",
                    description="Key decisions made by agents",
                    mimeType="application/json"
                )
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read a specific resource"""
            if uri == "context://shared/state":
                return json.dumps(self.shared_state, indent=2)
            elif uri == "context://shared/activities":
                return json.dumps(self.shared_state["activities"][-20:], indent=2)
            elif uri == "context://shared/decisions":
                return json.dumps(self.shared_state["decisions"], indent=2)
            else:
                raise ValueError(f"Unknown resource: {uri}")

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools"""
            return [
                types.Tool(
                    name="log_activity",
                    description="Log an agent activity to shared context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string"},
                            "activity": {"type": "string"},
                            "category": {
                                "type": "string",
                                "enum": ["decision", "action", "question", "completion", "error"]
                            }
                        },
                        "required": ["agent", "activity"]
                    }
                ),
                types.Tool(
                    name="check_conflicts",
                    description="Check if a planned action conflicts with other agents' work",
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
                types.Tool(
                    name="register_component",
                    description="Register a component being worked on",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string"},
                            "component_type": {"type": "string"},
                            "component_name": {"type": "string"},
                            "details": {"type": "object"}
                        },
                        "required": ["agent", "component_type", "component_name"]
                    }
                ),
                types.Tool(
                    name="get_agent_status",
                    description="Get status of all agents",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                types.Tool(
                    name="coordinate_decision",
                    description="Coordinate a decision across agents",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string"},
                            "decision": {"type": "string"},
                            "options": {"type": "array", "items": {"type": "string"}},
                            "requires_consensus": {"type": "boolean"}
                        },
                        "required": ["agent", "decision"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str,
            arguments: dict | None
        ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Handle tool calls"""

            if name == "log_activity":
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "agent": arguments["agent"],
                    "activity": arguments["activity"],
                    "category": arguments.get("category", "action")
                }
                self.shared_state["activities"].append(entry)

                # Log to file for persistence
                self.log_to_file(entry)

                return [types.TextContent(
                    type="text",
                    text=f"✅ Activity logged: {entry['agent']} - {entry['activity']}"
                )]

            elif name == "check_conflicts":
                conflicts = self.check_for_conflicts(
                    arguments["agent"],
                    arguments["planned_action"],
                    arguments.get("component", "")
                )

                response = {
                    "has_conflicts": len(conflicts) > 0,
                    "conflicts": conflicts,
                    "recommendation": self.get_conflict_recommendation(conflicts)
                }

                return [types.TextContent(
                    type="text",
                    text=json.dumps(response, indent=2)
                )]

            elif name == "register_component":
                component_type = arguments["component_type"]
                if component_type in self.shared_state["project_structure"]:
                    self.shared_state["project_structure"][component_type][arguments["component_name"]] = {
                        "owner": arguments["agent"],
                        "details": arguments.get("details", {}),
                        "created_at": datetime.now().isoformat()
                    }

                return [types.TextContent(
                    type="text",
                    text=f"✅ Component registered: {component_type}/{arguments['component_name']}"
                )]

            elif name == "get_agent_status":
                # Analyze recent activities to determine agent status
                status = self.analyze_agent_status()

                return [types.TextContent(
                    type="text",
                    text=json.dumps(status, indent=2)
                )]

            elif name == "coordinate_decision":
                decision_id = f"decision_{datetime.now().timestamp()}"
                self.shared_state["decisions"][decision_id] = {
                    "agent": arguments["agent"],
                    "decision": arguments["decision"],
                    "options": arguments.get("options", []),
                    "requires_consensus": arguments.get("requires_consensus", False),
                    "timestamp": datetime.now().isoformat(),
                    "status": "pending" if arguments.get("requires_consensus") else "approved"
                }

                return [types.TextContent(
                    type="text",
                    text=f"✅ Decision recorded: {decision_id}\nStatus: {self.shared_state['decisions'][decision_id]['status']}"
                )]

            else:
                raise ValueError(f"Unknown tool: {name}")

    def check_for_conflicts(self, agent: str, planned_action: str, component: str) -> List[Dict]:
        """Check for conflicts with other agents' work"""
        conflicts = []

        # Check recent activities for conflicts
        for activity in self.shared_state["activities"][-20:]:
            if activity["agent"] != agent:
                if self.is_conflicting(planned_action, activity["activity"]):
                    conflicts.append({
                        "agent": activity["agent"],
                        "activity": activity["activity"],
                        "timestamp": activity["timestamp"],
                        "severity": "high" if "database" in planned_action.lower() else "medium"
                    })

        return conflicts

    def is_conflicting(self, action1: str, action2: str) -> bool:
        """Detect if two actions conflict"""
        # Key conflict patterns
        conflict_patterns = [
            ("database schema", "database migration"),
            ("api endpoint", "api route"),
            ("authentication", "user model"),
            ("table", "schema"),
            ("/api/", "/api/"),  # Same API endpoint
            ("CREATE TABLE", "ALTER TABLE"),  # Database conflicts
        ]

        action1_lower = action1.lower()
        action2_lower = action2.lower()

        for pattern1, pattern2 in conflict_patterns:
            if pattern1 in action1_lower and pattern2 in action2_lower:
                return True

        return False

    def get_conflict_recommendation(self, conflicts: List[Dict]) -> str:
        """Get recommendation based on conflicts"""
        if not conflicts:
            return "No conflicts detected. Safe to proceed."

        if any(c["severity"] == "high" for c in conflicts):
            return "HIGH PRIORITY: Coordinate with other agents before proceeding. Database/schema conflicts detected."

        return "MEDIUM PRIORITY: Check with other agents to ensure compatibility."

    def analyze_agent_status(self) -> Dict[str, Any]:
        """Analyze and return current status of all agents"""
        status = {}

        # Count activities per agent
        for activity in self.shared_state["activities"][-50:]:
            agent = activity["agent"]
            if agent not in status:
                status[agent] = {
                    "last_activity": activity["timestamp"],
                    "activity_count": 0,
                    "recent_actions": []
                }

            status[agent]["activity_count"] += 1
            status[agent]["last_activity"] = activity["timestamp"]
            if len(status[agent]["recent_actions"]) < 3:
                status[agent]["recent_actions"].append(activity["activity"][:50])

        return status

    def log_to_file(self, entry: Dict):
        """Log to file for persistence"""
        log_file = "/tmp/mcp_shared_context.log"
        try:
            with open(log_file, 'a') as f:
                f.write(f"[{entry['timestamp']}] {entry['agent']}: {entry['activity']}\n")
        except Exception as e:
            print(f"Error logging to file: {e}")

    async def run(self):
        """Run the MCP server"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="claude-coordinator",
                    server_version="1.0.0",
                    capabilities={}
                )
            )


if __name__ == "__main__":
    import asyncio

    server = SharedContextServer()
    asyncio.run(server.run())