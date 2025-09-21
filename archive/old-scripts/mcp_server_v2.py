#!/usr/bin/env python3
"""
MCP Server v2 - Full JSON-RPC 2.0 Implementation
Implements MCP protocol version 2025-06-18 with Tools, Resources, and Prompts
"""

import json
import sqlite3
import asyncio
import logging
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import uuid

from aiohttp import web
from jsonschema import validate, ValidationError
import aiohttp_cors

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DB_PATH = "/tmp/mcp_state.db"
PORT = 8099
IDEMPOTENCY_CACHE_HOURS = 24
REQUEST_TIMEOUT_SECONDS = 30
RATE_LIMIT_PER_MINUTE = 100

# MCP Protocol Version
MCP_VERSION = "2025-06-18"

class MCPServer:
    def __init__(self):
        self.db_path = DB_PATH
        self.idempotency_cache = {}  # {idempotency_key: {result, timestamp}}
        self.rate_limiter = {}  # {session_id: {count, reset_time}}
        self.capabilities = {
            "protocol_version": MCP_VERSION,
            "supports": ["tools", "resources", "prompts"],
            "features": {
                "idempotency": True,
                "dry_run": True,
                "streaming": False,
                "batch": False
            }
        }
        self.tools = {}
        self.resources = {}
        self.prompts = {}
        self._load_primitives()

    def _load_primitives(self):
        """Load Tools, Resources, and Prompts definitions"""
        # Define MCP Tools with JSON Schema
        self.tools = {
            "log_activity": {
                "name": "log_activity",
                "description": "Log an activity for an agent",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent": {"type": "string", "description": "Agent name"},
                        "activity": {"type": "string", "description": "Activity description"},
                        "category": {"type": "string", "enum": ["task", "communication", "decision", "error"]},
                        "status": {"type": "string", "enum": ["started", "in_progress", "completed", "failed"]},
                        "details": {"type": "object", "description": "Additional details"},
                        "dry_run": {"type": "boolean", "default": False}
                    },
                    "required": ["agent", "activity", "category"],
                    "additionalProperties": False
                }
            },
            "check_conflicts": {
                "name": "check_conflicts",
                "description": "Check for conflicts between agents",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agents": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 2
                        },
                        "dry_run": {"type": "boolean", "default": False}
                    },
                    "required": ["agents"],
                    "additionalProperties": False
                }
            },
            "register_component": {
                "name": "register_component",
                "description": "Register a new component ownership",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Component name"},
                        "owner": {"type": "string", "description": "Owner agent"},
                        "status": {"type": "string", "enum": ["active", "inactive", "deprecated"]},
                        "metadata": {"type": "object"},
                        "dry_run": {"type": "boolean", "default": False}
                    },
                    "required": ["name", "owner"],
                    "additionalProperties": False
                }
            },
            "update_status": {
                "name": "update_status",
                "description": "Update agent status",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent": {"type": "string"},
                        "status": {"type": "string", "enum": ["active", "idle", "busy", "offline"]},
                        "current_task": {"type": "string"},
                        "dry_run": {"type": "boolean", "default": False}
                    },
                    "required": ["agent", "status"],
                    "additionalProperties": False
                }
            },
            "heartbeat": {
                "name": "heartbeat",
                "description": "Send heartbeat signal from agent",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent": {"type": "string"},
                        "dry_run": {"type": "boolean", "default": False}
                    },
                    "required": ["agent"],
                    "additionalProperties": False
                }
            },
            "request_collaboration": {
                "name": "request_collaboration",
                "description": "Request collaboration from another agent",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "from_agent": {"type": "string"},
                        "to_agent": {"type": "string"},
                        "task": {"type": "string"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                        "dry_run": {"type": "boolean", "default": False}
                    },
                    "required": ["from_agent", "to_agent", "task"],
                    "additionalProperties": False
                }
            },
            "propose_decision": {
                "name": "propose_decision",
                "description": "Propose a decision for approval",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string"},
                        "question": {"type": "string"},
                        "proposed_by": {"type": "string"},
                        "metadata": {"type": "object"},
                        "dry_run": {"type": "boolean", "default": False}
                    },
                    "required": ["category", "question", "proposed_by"],
                    "additionalProperties": False
                }
            },
            "find_component_owner": {
                "name": "find_component_owner",
                "description": "Find the owner of a component",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "component": {"type": "string"},
                        "dry_run": {"type": "boolean", "default": False}
                    },
                    "required": ["component"],
                    "additionalProperties": False
                }
            }
        }

        # Define Resources with URI schemes
        self.resources = {
            "file://README.md": {
                "uri": "file://README.md",
                "name": "Project README",
                "type": "text/markdown",
                "description": "Main project documentation"
            },
            "db://schema/complete": {
                "uri": "db://schema/complete",
                "name": "Database Schema",
                "type": "application/json",
                "description": "Complete database schema definition"
            },
            "api://swagger/spec": {
                "uri": "api://swagger/spec",
                "name": "API Specification",
                "type": "application/json",
                "description": "OpenAPI specification for the MCP API"
            },
            "config://agents/supervisor": {
                "uri": "config://agents/supervisor",
                "name": "Supervisor Agent Config",
                "type": "application/json",
                "description": "Configuration for the supervisor agent"
            }
        }

        # Define Prompts
        self.prompts = {
            "deploy_system": {
                "name": "deploy_system",
                "description": "Deploy the multi-agent system",
                "arguments": [
                    {"name": "environment", "type": "string", "required": True},
                    {"name": "version", "type": "string", "required": False}
                ],
                "template": "Deploy multi-agent system to {environment} environment{version}"
            },
            "run_tests": {
                "name": "run_tests",
                "description": "Run system tests",
                "arguments": [
                    {"name": "suite", "type": "string", "required": True},
                    {"name": "verbose", "type": "boolean", "required": False}
                ],
                "template": "Run {suite} test suite{verbose}"
            },
            "analyze_performance": {
                "name": "analyze_performance",
                "description": "Analyze system performance",
                "arguments": [
                    {"name": "component", "type": "string", "required": True},
                    {"name": "duration", "type": "string", "required": False}
                ],
                "template": "Analyze performance of {component}{duration}"
            }
        }

    async def handle_jsonrpc(self, request):
        """Main JSON-RPC 2.0 request handler"""
        try:
            # Get request ID for tracing
            request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))

            # Parse JSON-RPC request
            data = await request.json()

            # Validate JSON-RPC structure
            if not isinstance(data, dict) or 'jsonrpc' not in data or data['jsonrpc'] != '2.0':
                return self._error_response(-32600, "Invalid Request", request_id)

            if 'method' not in data:
                return self._error_response(-32600, "Invalid Request - missing method", request_id)

            method = data.get('method')
            params = data.get('params', {})
            rpc_id = data.get('id')

            # Check idempotency
            idempotency_key = request.headers.get('Idempotency-Key')
            if idempotency_key:
                cached = self._check_idempotency(idempotency_key)
                if cached:
                    return web.json_response(cached)

            # Rate limiting
            session_id = params.get('session_id', request.remote)
            if not self._check_rate_limit(session_id):
                return self._error_response(-32000, "Rate limit exceeded", request_id)

            # Route to method handler
            result = await self._route_method(method, params, request_id)

            # Build response
            response = {
                "jsonrpc": "2.0",
                "result": result
            }
            if rpc_id is not None:
                response["id"] = rpc_id

            # Cache if idempotent
            if idempotency_key:
                self._cache_idempotent(idempotency_key, response)

            return web.json_response(response, headers={'X-Request-ID': request_id})

        except ValidationError as e:
            return self._error_response(-32602, f"Invalid params: {str(e)}", request_id)
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return self._error_response(-32603, "Internal error", request_id)

    async def _route_method(self, method: str, params: Dict, request_id: str) -> Any:
        """Route JSON-RPC method to handler"""
        handlers = {
            "initialize": self._handle_initialize,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resources_read,
            "prompts/list": self._handle_prompts_list,
            "prompts/execute": self._handle_prompts_execute,
            "capabilities": self._handle_capabilities
        }

        handler = handlers.get(method)
        if not handler:
            raise ValueError(f"Method not found: {method}")

        return await handler(params, request_id)

    async def _handle_initialize(self, params: Dict, request_id: str) -> Dict:
        """Handle initialize method for capability negotiation"""
        client_info = params.get('clientInfo', {})
        requested_capabilities = params.get('capabilities', [])

        # Negotiate capabilities
        negotiated = {
            "protocol_version": MCP_VERSION,
            "server_name": "MCP Multi-Agent System",
            "capabilities": self.capabilities,
            "tools_count": len(self.tools),
            "resources_count": len(self.resources),
            "prompts_count": len(self.prompts)
        }

        # Store session
        session_id = str(uuid.uuid4())
        self._store_session(session_id, client_info, negotiated)

        negotiated["session_id"] = session_id
        return negotiated

    async def _handle_tools_list(self, params: Dict, request_id: str) -> List[Dict]:
        """List available tools"""
        return list(self.tools.values())

    async def _handle_tools_call(self, params: Dict, request_id: str) -> Dict:
        """Execute a tool"""
        tool_name = params.get('name')
        tool_params = params.get('arguments', {})
        dry_run = tool_params.get('dry_run', False)

        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")

        # Validate parameters
        schema = self.tools[tool_name]['inputSchema']
        validate(tool_params, schema)

        # Execute tool (or simulate if dry_run)
        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "message": f"Would execute {tool_name} with params: {tool_params}"
            }

        # Actual tool execution
        result = await self._execute_tool(tool_name, tool_params)
        return result

    async def _handle_resources_list(self, params: Dict, request_id: str) -> List[Dict]:
        """List available resources"""
        return list(self.resources.values())

    async def _handle_resources_read(self, params: Dict, request_id: str) -> Dict:
        """Read a resource by URI"""
        uri = params.get('uri')

        if uri not in self.resources:
            raise ValueError(f"Resource not found: {uri}")

        # Check path protection for file:// URIs
        if uri.startswith('file://'):
            if not self._validate_file_path(uri):
                raise ValueError("Access denied: Path outside project directory")

        # Get resource content
        content = await self._read_resource(uri)
        return {
            "uri": uri,
            "content": content,
            "metadata": self.resources[uri]
        }

    async def _handle_prompts_list(self, params: Dict, request_id: str) -> List[Dict]:
        """List available prompts"""
        return list(self.prompts.values())

    async def _handle_prompts_execute(self, params: Dict, request_id: str) -> Dict:
        """Execute a prompt template"""
        prompt_name = params.get('name')
        arguments = params.get('arguments', {})

        if prompt_name not in self.prompts:
            raise ValueError(f"Prompt not found: {prompt_name}")

        prompt = self.prompts[prompt_name]

        # Validate required arguments
        for arg in prompt['arguments']:
            if arg['required'] and arg['name'] not in arguments:
                raise ValueError(f"Missing required argument: {arg['name']}")

        # Format template
        template = prompt['template']
        for key, value in arguments.items():
            template = template.replace(f"{{{key}}}", str(value))

        return {
            "prompt": prompt_name,
            "result": template,
            "executed_at": datetime.now().isoformat()
        }

    async def _handle_capabilities(self, params: Dict, request_id: str) -> Dict:
        """Return server capabilities"""
        return self.capabilities

    async def _execute_tool(self, tool_name: str, params: Dict) -> Dict:
        """Execute a specific tool"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            timestamp = datetime.now().isoformat()

            if tool_name == "log_activity":
                cursor.execute("""
                    INSERT INTO activities (agent, timestamp, activity, category, status, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    params['agent'],
                    timestamp,
                    params['activity'],
                    params['category'],
                    params.get('status', 'completed'),
                    json.dumps(params.get('details', {}))
                ))
                conn.commit()
                return {"success": True, "id": cursor.lastrowid}

            elif tool_name == "check_conflicts":
                # Check for conflicts between agents
                agents = params['agents']
                cursor.execute("""
                    SELECT * FROM conflicts
                    WHERE agents LIKE ? AND resolved = 0
                """, (f"%{json.dumps(agents)}%",))
                conflicts = cursor.fetchall()
                return {
                    "success": True,
                    "conflicts": len(conflicts) > 0,
                    "count": len(conflicts)
                }

            elif tool_name == "register_component":
                cursor.execute("""
                    INSERT OR REPLACE INTO components (name, owner, status, last_updated, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    params['name'],
                    params['owner'],
                    params.get('status', 'active'),
                    timestamp,
                    json.dumps(params.get('metadata', {}))
                ))
                conn.commit()
                return {"success": True, "component": params['name']}

            elif tool_name == "update_status":
                cursor.execute("""
                    INSERT OR REPLACE INTO agent_states (agent, last_seen, status, current_task)
                    VALUES (?, ?, ?, ?)
                """, (
                    params['agent'],
                    timestamp,
                    params['status'],
                    params.get('current_task', '')
                ))
                conn.commit()
                return {"success": True, "agent": params['agent']}

            elif tool_name == "heartbeat":
                cursor.execute("""
                    UPDATE agent_states
                    SET last_seen = ?
                    WHERE agent = ?
                """, (timestamp, params['agent']))
                conn.commit()
                return {"success": True, "timestamp": timestamp}

            elif tool_name == "request_collaboration":
                # Log collaboration request
                cursor.execute("""
                    INSERT INTO activities (agent, timestamp, activity, category, details)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    params['from_agent'],
                    timestamp,
                    f"Collaboration requested from {params['to_agent']}",
                    "communication",
                    json.dumps({
                        "to_agent": params['to_agent'],
                        "task": params['task'],
                        "priority": params.get('priority', 'medium')
                    })
                ))
                conn.commit()
                return {"success": True, "request_id": cursor.lastrowid}

            elif tool_name == "propose_decision":
                cursor.execute("""
                    INSERT INTO decisions (category, question, proposed_by, status, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    params['category'],
                    params['question'],
                    params['proposed_by'],
                    'pending',
                    timestamp,
                    json.dumps(params.get('metadata', {}))
                ))
                conn.commit()
                return {"success": True, "decision_id": cursor.lastrowid}

            elif tool_name == "find_component_owner":
                cursor.execute("""
                    SELECT owner, status FROM components WHERE name = ?
                """, (params['component'],))
                result = cursor.fetchone()
                if result:
                    return {
                        "success": True,
                        "found": True,
                        "owner": result[0],
                        "status": result[1]
                    }
                return {"success": True, "found": False}

            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}

        finally:
            conn.close()

    async def _read_resource(self, uri: str) -> Any:
        """Read resource content by URI"""
        if uri.startswith('file://'):
            # Read file content
            path = uri[7:]  # Remove file://
            project_path = Path("/Users/erik/Desktop/claude-multiagent-system")
            file_path = project_path / path

            if not file_path.exists():
                raise ValueError(f"File not found: {path}")

            with open(file_path, 'r') as f:
                return f.read()

        elif uri.startswith('db://'):
            # Read database content
            if uri == "db://schema/complete":
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
                schemas = cursor.fetchall()
                conn.close()
                return {"tables": [s[0] for s in schemas]}

        elif uri.startswith('api://'):
            # Return API documentation
            if uri == "api://swagger/spec":
                return {
                    "openapi": "3.0.0",
                    "info": {
                        "title": "MCP API",
                        "version": "2.0.0"
                    },
                    "paths": {}  # Would include full OpenAPI spec
                }

        elif uri.startswith('config://'):
            # Return configuration
            if uri == "config://agents/supervisor":
                return {
                    "name": "supervisor",
                    "role": "coordination",
                    "capabilities": ["task_delegation", "conflict_resolution"]
                }

        return None

    def _validate_file_path(self, uri: str) -> bool:
        """Validate file path is within project directory"""
        path = uri[7:]  # Remove file://
        project_path = Path("/Users/erik/Desktop/claude-multiagent-system")

        try:
            file_path = (project_path / path).resolve()
            # Check if path is within project directory
            if not str(file_path).startswith(str(project_path)):
                return False

            # Check blacklist
            blacklist = ['.git', '.env', 'id_rsa', '.ssh']
            for forbidden in blacklist:
                if forbidden in str(file_path):
                    return False

            return True
        except:
            return False

    def _check_idempotency(self, key: str) -> Optional[Dict]:
        """Check idempotency cache"""
        if key in self.idempotency_cache:
            cached = self.idempotency_cache[key]
            # Check if still valid (24 hours)
            if datetime.now() - cached['timestamp'] < timedelta(hours=IDEMPOTENCY_CACHE_HOURS):
                return cached['result']
            else:
                del self.idempotency_cache[key]
        return None

    def _cache_idempotent(self, key: str, result: Dict):
        """Cache idempotent result"""
        self.idempotency_cache[key] = {
            'result': result,
            'timestamp': datetime.now()
        }

    def _check_rate_limit(self, session_id: str) -> bool:
        """Check rate limit for session"""
        now = datetime.now()

        if session_id not in self.rate_limiter:
            self.rate_limiter[session_id] = {
                'count': 1,
                'reset_time': now + timedelta(minutes=1)
            }
            return True

        limiter = self.rate_limiter[session_id]

        # Reset if time window passed
        if now >= limiter['reset_time']:
            limiter['count'] = 1
            limiter['reset_time'] = now + timedelta(minutes=1)
            return True

        # Check limit
        limiter['count'] += 1
        return limiter['count'] <= RATE_LIMIT_PER_MINUTE

    def _store_session(self, session_id: str, client_info: Dict, capabilities: Dict):
        """Store session in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create capabilities table if needed
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS capabilities (
                session_id TEXT PRIMARY KEY,
                client_info TEXT,
                negotiated_capabilities TEXT,
                created_at INTEGER,
                last_used INTEGER
            )
        """)

        cursor.execute("""
            INSERT OR REPLACE INTO capabilities
            (session_id, client_info, negotiated_capabilities, created_at, last_used)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session_id,
            json.dumps(client_info),
            json.dumps(capabilities),
            int(time.time()),
            int(time.time())
        ))

        conn.commit()
        conn.close()

    def _error_response(self, code: int, message: str, request_id: str) -> web.Response:
        """Create JSON-RPC error response"""
        # Load error codes
        error_codes_path = Path("/Users/erik/Desktop/claude-multiagent-system/mcp_error_codes.json")
        if error_codes_path.exists():
            with open(error_codes_path) as f:
                error_codes = json.load(f)
                if str(code) in error_codes:
                    error_info = error_codes[str(code)]
                    message = error_info.get('message', message)

        response = {
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message,
                "data": {
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat()
                }
            },
            "id": None
        }

        return web.json_response(response, status=400, headers={'X-Request-ID': request_id})

    async def handle_legacy_status(self, request):
        """Handle legacy /api/mcp/status endpoint for backward compatibility"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get recent activities
            cursor.execute("""
                SELECT id, agent, timestamp, activity, category, status
                FROM activities
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            activities = [dict(zip(['id', 'agent', 'timestamp', 'activity', 'category', 'status'], row))
                         for row in cursor.fetchall()]

            # Get agent states
            cursor.execute("""
                SELECT agent, last_seen, status, current_task
                FROM agent_states
                WHERE datetime(last_seen) > datetime('now', '-5 minutes')
            """)
            agents = [dict(zip(['agent', 'last_seen', 'status', 'current_task'], row))
                     for row in cursor.fetchall()]

            # Get system stats
            cursor.execute("SELECT COUNT(*) FROM activities")
            total_activities = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT agent) FROM agent_states")
            active_agents = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM components")
            registered_components = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM decisions WHERE status='pending'")
            pending_decisions = cursor.fetchone()[0]

            conn.close()

            # Add MCP v2 information
            response = {
                "status": "operational",
                "mcp_version": MCP_VERSION,
                "capabilities": self.capabilities,
                "agents": agents,
                "activities": activities,
                "system_stats": {
                    "total_activities": total_activities,
                    "active_agents": active_agents,
                    "registered_components": registered_components,
                    "pending_decisions": pending_decisions,
                    "tools_available": len(self.tools),
                    "resources_available": len(self.resources),
                    "prompts_available": len(self.prompts)
                }
            }

            return web.json_response(response)

        except Exception as e:
            logger.error(f"Error in legacy status endpoint: {e}")
            return web.json_response({"error": str(e)}, status=500)

def create_app():
    """Create aiohttp application"""
    server = MCPServer()
    app = web.Application()

    # Configure CORS
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })

    # JSON-RPC endpoint
    rpc_route = app.router.add_post('/jsonrpc', server.handle_jsonrpc)
    cors.add(rpc_route)

    # Legacy endpoints for backward compatibility
    legacy_status = app.router.add_get('/api/mcp/status', server.handle_legacy_status)
    cors.add(legacy_status)

    # Health check
    async def health_check(request):
        return web.json_response({"status": "healthy", "version": MCP_VERSION})

    health_route = app.router.add_get('/api/mcp/health', health_check)
    cors.add(health_route)

    return app

async def init_database():
    """Initialize database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create new MCP v2 tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            uri TEXT PRIMARY KEY,
            name TEXT,
            type TEXT,
            description TEXT,
            last_accessed INTEGER,
            access_count INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            name TEXT PRIMARY KEY,
            description TEXT,
            category TEXT,
            arguments TEXT,
            template TEXT,
            usage_count INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resource_access_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uri TEXT,
            session_id TEXT,
            timestamp INTEGER,
            success BOOLEAN,
            error_message TEXT
        )
    """)

    # Add indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON activities(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_agent ON activities(agent)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_resource_access_timestamp ON resource_access_log(timestamp)")

    conn.commit()
    conn.close()
    logger.info("Database initialized with MCP v2 tables")

async def main():
    """Main entry point"""
    # Initialize database
    await init_database()

    # Create and run app
    app = create_app()

    logger.info(f"Starting MCP Server v2 on port {PORT}")
    logger.info(f"Protocol version: {MCP_VERSION}")
    logger.info(f"JSON-RPC endpoint: http://localhost:{PORT}/jsonrpc")
    logger.info(f"Legacy status: http://localhost:{PORT}/api/mcp/status")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', PORT)
    await site.start()

    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down MCP Server v2")

if __name__ == '__main__':
    asyncio.run(main())