#!/usr/bin/env python3
"""
MCP Bridge v2 COMPLETE - Full Integration with MCP Server v2
Includes WebSocket, Retry Logic, and Auto-configuration
"""

import json
import sys
import re
import logging
import requests
import asyncio
import websockets
import threading
import time
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List
import os
import uuid
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mcp_bridge_v2.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MCPBridgeV2Complete:
    """Complete Bridge between Claude Code Hooks and MCP Server v2"""

    def __init__(self):
        # MCP Server configuration
        self.mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8099")
        self.mcp_ws_url = os.getenv("MCP_WS_URL", "ws://localhost:8100")
        self.jsonrpc_endpoint = f"{self.mcp_server_url}/jsonrpc"

        # Agent identification
        self.agent_name = os.getenv("CLAUDE_AGENT_NAME", self._detect_agent_from_context())
        self.session_id = None
        self.ws_connection = None
        self.ws_connected = False
        self.ws_thread = None

        # Project directory
        self.project_dir = os.getenv("CLAUDE_PROJECT_DIR", "/Users/erik/Desktop/claude-multiagent-system")

        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        self.retry_backoff = 2.0  # exponential backoff multiplier

        # Initialize session with MCP server
        self._initialize_mcp_session()

        # Start WebSocket connection in background
        self._start_websocket_thread()

        # Install Claude hooks if needed
        self._setup_claude_hooks()

        # Enhanced tool patterns for MCP v2
        self.tool_patterns = {
            'log_activity': [
                r"(?:I'll |I will |Let me )?(?:use|call|invoke) (?:the )?log_activity (?:tool|MCP tool)(?: to)? (.+)",
                r"log_activity[:\s]+(.+)",
                r"(?:logging|log) (?:the )?activity[:\s]+(.+)",
                r"(?:MCP:)?\s*(?:log|logging)[:\s]+(.+)",
                r"(?:announce|announcing)[:\s]+(.+)"
            ],
            'check_conflicts': [
                r"(?:check|checking) (?:for )?conflicts?(?: for)? (.+)",
                r"(?:use|call) check_conflicts(?: tool)?(?: for)? (.+)",
                r"(?:verify|verifying) (?:no )?conflicts?(?: with)? (.+)",
                r"(?:MCP:)?\s*conflict check[:\s]+(.+)"
            ],
            'register_component': [
                r"register(?:ing)? component[:\s]+(.+)",
                r"(?:use|call) register_component(?: tool)?[:\s]+(.+)",
                r"(?:creating|created) component[:\s]+(.+)",
                r"(?:MCP:)?\s*component registration[:\s]+(.+)"
            ],
            'update_status': [
                r"(?:update|updating) (?:my )?status(?: to)?[:\s]+(.+)",
                r"status update[:\s]+(.+)",
                r"(?:I'm|I am) now (.+)",
                r"(?:MCP:)?\s*status[:\s]+(.+)"
            ],
            'heartbeat': [
                r"(?:send|sending) heartbeat",
                r"(?:I'm|I am) (?:still )?(?:active|alive)",
                r"heartbeat",
                r"keep.?alive",
                r"(?:MCP:)?\s*heartbeat"
            ],
            'request_collaboration': [
                r"(?:request|requesting) (?:collaboration|help)(?: from)? (.+)",
                r"(?:need|needing) (?:help|assistance)(?: with)? (.+)",
                r"collaborate(?: on)? (.+)",
                r"(?:MCP:)?\s*collaboration request[:\s]+(.+)"
            ],
            'propose_decision': [
                r"(?:propose|proposing) (?:decision|choice)[:\s]+(.+)",
                r"(?:should we|we should) (.+)",
                r"(?:vote|voting) (?:on|for)[:\s]+(.+)",
                r"(?:MCP:)?\s*decision[:\s]+(.+)"
            ],
            'find_component_owner': [
                r"(?:who|what) (?:owns|created) (.+)",
                r"find (?:owner|creator) (?:of|for) (.+)",
                r"component owner[:\s]+(.+)",
                r"(?:MCP:)?\s*find owner[:\s]+(.+)"
            ]
        }

    def _detect_agent_from_context(self) -> str:
        """Detect agent name from terminal context"""
        # Try to detect from tmux session name
        try:
            import subprocess
            result = subprocess.run(["tmux", "display-message", "-p", "#S"],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                session = result.stdout.strip()
                if session.startswith("claude-"):
                    return session.replace("claude-", "")
        except:
            pass

        # Default to unknown
        return "unknown"

    def _setup_claude_hooks(self):
        """Setup Claude Code hooks automatically"""
        try:
            hooks_dir = Path.home() / ".claude" / "hooks"
            hooks_dir.mkdir(parents=True, exist_ok=True)

            # Create hook script
            hook_script = hooks_dir / "mcp_v2_hook.sh"
            hook_content = f'''#!/bin/bash
# MCP v2 Hook for Claude Code - Auto-installed

# Get the hook type from the first argument
HOOK_TYPE="$1"

# Set agent name from tmux session if available
if [ -n "$TMUX" ]; then
    export CLAUDE_AGENT_NAME=$(tmux display-message -p '#S' | sed 's/claude-//')
fi

# Set MCP server URLs
export MCP_SERVER_URL="{self.mcp_server_url}"
export MCP_WS_URL="{self.mcp_ws_url}"

# Call the bridge
python3 {self.project_dir}/mcp_bridge_v2_complete.py "$HOOK_TYPE"
'''
            hook_script.write_text(hook_content)
            os.chmod(hook_script, 0o755)

            # Create settings.toml if needed
            settings_file = hooks_dir / "settings.toml"
            if not settings_file.exists():
                settings_content = f'''[hooks]
notification = "{hook_script}"
message = "{hook_script}"
pre_tool_use = "{hook_script}"
post_tool_use = "{hook_script}"
'''
                settings_file.write_text(settings_content)

            logger.info(f"Claude hooks installed at {hooks_dir}")

        except Exception as e:
            logger.error(f"Failed to setup Claude hooks: {e}")

    def _initialize_mcp_session(self):
        """Initialize session with MCP Server v2 with retry logic"""
        for attempt in range(self.max_retries):
            try:
                # Call initialize method via JSON-RPC
                response = self._jsonrpc_call("initialize", {
                    "clientInfo": {
                        "name": f"claude-{self.agent_name}",
                        "version": "2.0.0"
                    },
                    "capabilities": ["tools", "resources", "prompts"]
                }, retry_on_fail=False)  # Don't retry the retry

                if response and not response.get("error"):
                    self.session_id = response.get("sessionId")
                    logger.info(f"MCP session initialized for agent '{self.agent_name}' with ID: {self.session_id}")

                    # Register agent
                    self._register_agent()
                    return
                else:
                    logger.error(f"Failed to initialize MCP session (attempt {attempt + 1}): {response}")

            except Exception as e:
                logger.error(f"Error initializing MCP session (attempt {attempt + 1}): {e}")

            if attempt < self.max_retries - 1:
                delay = self.retry_delay * (self.retry_backoff ** attempt)
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)

    def _register_agent(self):
        """Register this agent with MCP server"""
        try:
            response = self._jsonrpc_call("tools/call", {
                "name": "update_status",
                "arguments": {
                    "agent": self.agent_name,
                    "status": "active",
                    "current_task": "initialized"
                }
            })

            if response and not response.get("error"):
                logger.info(f"Agent '{self.agent_name}' registered with MCP server")

        except Exception as e:
            logger.error(f"Error registering agent: {e}")

    def _jsonrpc_call(self, method: str, params: Dict = None, retry_on_fail: bool = True) -> Dict:
        """Make JSON-RPC 2.0 call to MCP server with retry logic"""
        request_id = str(uuid.uuid4())

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": request_id
        }

        # Add session ID if available
        if self.session_id and params:
            params["session_id"] = self.session_id

        headers = {
            "Content-Type": "application/json",
            "X-Request-ID": request_id,
            "X-Agent-Name": self.agent_name
        }

        attempts = self.max_retries if retry_on_fail else 1

        for attempt in range(attempts):
            try:
                response = requests.post(self.jsonrpc_endpoint,
                                        json=payload,
                                        headers=headers,
                                        timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    if "error" in data:
                        logger.error(f"JSON-RPC error: {data['error']}")
                    return data
                else:
                    logger.error(f"HTTP error {response.status_code}: {response.text}")
                    error_result = {"error": f"HTTP {response.status_code}"}

            except requests.exceptions.Timeout:
                logger.error(f"Request timeout (attempt {attempt + 1})")
                error_result = {"error": "timeout"}

            except requests.exceptions.ConnectionError:
                logger.error(f"Connection error (attempt {attempt + 1})")
                error_result = {"error": "connection_failed"}

            except Exception as e:
                logger.error(f"Failed to call MCP server (attempt {attempt + 1}): {e}")
                error_result = {"error": str(e)}

            if attempt < attempts - 1:
                delay = self.retry_delay * (self.retry_backoff ** attempt)
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                return error_result

    def _start_websocket_thread(self):
        """Start WebSocket connection in a background thread"""
        def run_websocket():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._websocket_loop())

        self.ws_thread = threading.Thread(target=run_websocket)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        logger.info("WebSocket thread started")

    async def _websocket_loop(self):
        """WebSocket connection loop with auto-reconnect"""
        while True:
            try:
                await self._connect_websocket()
                # If connection closes, wait before reconnecting
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"WebSocket loop error: {e}")
                await asyncio.sleep(10)

    async def _connect_websocket(self):
        """Establish and maintain WebSocket connection"""
        try:
            logger.info(f"Connecting to WebSocket at {self.mcp_ws_url}")
            async with websockets.connect(self.mcp_ws_url) as websocket:
                self.ws_connection = websocket
                self.ws_connected = True

                # Send initial handshake
                await websocket.send(json.dumps({
                    "type": "handshake",
                    "agent": self.agent_name,
                    "session_id": self.session_id
                }))

                logger.info(f"WebSocket connected for agent '{self.agent_name}'")

                # Listen for messages
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=30)
                        await self._handle_websocket_message(message)
                    except asyncio.TimeoutError:
                        # Send ping to keep connection alive
                        await websocket.send(json.dumps({"type": "ping"}))
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("WebSocket connection closed")
                        break

        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
        finally:
            self.ws_connected = False
            self.ws_connection = None

    async def _handle_websocket_message(self, message: str):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "command":
                # Server is sending a command to execute
                logger.info(f"Received command from server: {data}")
                # Process the command
                tool = data.get("tool")
                params = data.get("params", {})
                if tool:
                    result = self.execute_mcp_tool(tool, params)
                    # Send result back via WebSocket
                    if self.ws_connection:
                        await self.ws_connection.send(json.dumps({
                            "type": "result",
                            "tool": tool,
                            "result": result
                        }))

            elif msg_type == "notification":
                logger.info(f"Received notification: {data.get('message')}")

            elif msg_type == "pong":
                logger.debug("Received pong")

        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

    def detect_mcp_intent(self, text: str) -> Tuple[Optional[str], Optional[Dict]]:
        """Detect if text contains intent to use MCP tool"""
        if not text:
            return None, None

        text = text.strip()

        # Check for explicit MCP commands
        if text.startswith("MCP:") or text.startswith("mcp:"):
            text = text[4:].strip()

            # Parse direct MCP command
            parts = text.split(None, 1)
            if parts:
                tool = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                if tool in self.tool_patterns:
                    params = self._extract_params(tool, None, args)
                    return tool, params

        # Check each tool's patterns
        for tool, patterns in self.tool_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    logger.info(f"Detected intent for tool '{tool}' from pattern: {pattern}")
                    params = self._extract_params(tool, match, text)
                    return tool, params

        return None, None

    def _extract_params(self, tool: str, match: Optional[re.Match], full_text: str) -> Dict:
        """Extract parameters for specific tool"""
        params = {}

        if tool == 'log_activity':
            activity = match.group(1) if match and match.groups() else full_text
            params.update({
                "agent": self.agent_name,
                "activity": activity.strip('" '),
                "category": self._categorize_activity(activity),
                "status": "in_progress"
            })

        elif tool == 'check_conflicts':
            agents = []
            if match and match.groups():
                # Extract agent names from the text
                agent_text = match.group(1)
                agents = re.findall(r'\b(?:master|supervisor|backend-api|database|frontend-ui|testing|queue-manager|deployment|instagram)\b',
                                   agent_text, re.IGNORECASE)
            params["agents"] = agents if len(agents) >= 2 else [self.agent_name, "master"]

        elif tool == 'register_component':
            component_info = match.group(1).strip('" ') if match and match.groups() else ""
            params.update({
                "name": component_info.split(':')[0] if ':' in component_info else component_info,
                "owner": self.agent_name,
                "status": "active"
            })

        elif tool == 'update_status':
            status_text = match.group(1).strip('" ') if match and match.groups() else "active"

            # Map status text to valid status
            if any(word in status_text.lower() for word in ['busy', 'working', 'processing']):
                status = 'busy'
            elif any(word in status_text.lower() for word in ['idle', 'waiting', 'ready']):
                status = 'idle'
            elif any(word in status_text.lower() for word in ['offline', 'stopped', 'done']):
                status = 'offline'
            else:
                status = 'active'

            params.update({
                "agent": self.agent_name,
                "status": status,
                "current_task": status_text
            })

        elif tool == 'heartbeat':
            # Only agent name needed
            params["agent"] = self.agent_name

        elif tool == 'request_collaboration':
            task = match.group(1).strip('" ') if match and match.groups() else ""
            params.update({
                "from_agent": self.agent_name,
                "to_agent": "supervisor",  # Default to supervisor
                "task": task,
                "priority": "medium"
            })

        elif tool == 'propose_decision':
            decision = match.group(1).strip('" ') if match and match.groups() else ""
            params.update({
                "category": "technical",
                "question": decision,
                "proposed_by": self.agent_name
            })

        elif tool == 'find_component_owner':
            component = match.group(1).strip('" ') if match and match.groups() else ""
            params["component"] = component

        return params

    def _categorize_activity(self, activity: str) -> str:
        """Categorize activity type for MCP v2"""
        activity_lower = activity.lower()

        if any(word in activity_lower for word in ['error', 'fail', 'issue', 'problem']):
            return 'error'
        elif any(word in activity_lower for word in ['complete', 'finish', 'done']):
            return 'task'
        elif any(word in activity_lower for word in ['communicate', 'message', 'send', 'receive']):
            return 'communication'
        elif any(word in activity_lower for word in ['decide', 'choose', 'select']):
            return 'decision'
        else:
            return 'task'

    def execute_mcp_tool(self, tool: str, params: Dict) -> Dict[str, Any]:
        """Execute MCP tool via JSON-RPC to MCP Server v2"""
        try:
            # Call the tool via MCP server with retry logic
            response = self._jsonrpc_call("tools/call", {
                "name": tool,
                "arguments": params
            })

            if response and "result" in response:
                result = response["result"]

                # Log to shared context for visibility
                with open('/tmp/mcp_shared_context.log', 'a') as f:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    f.write(f"[{timestamp}] {self.agent_name}: {tool} -> {result.get('message', 'Success')}\n")

                # Send via WebSocket if connected
                if self.ws_connected and self.ws_connection:
                    asyncio.run_coroutine_threadsafe(
                        self.ws_connection.send(json.dumps({
                            "type": "activity",
                            "agent": self.agent_name,
                            "tool": tool,
                            "result": result
                        })),
                        asyncio.get_event_loop()
                    )

                return {
                    "success": True,
                    "message": result.get("message", f"Tool '{tool}' executed successfully"),
                    "data": result
                }
            elif response and "error" in response:
                error = response["error"]
                return {
                    "success": False,
                    "message": f"MCP error: {error.get('message', 'Unknown error')}",
                    "error": error
                }
            else:
                return {
                    "success": False,
                    "message": f"Invalid response from MCP server"
                }

        except Exception as e:
            logger.error(f"Error executing tool '{tool}': {e}")
            return {
                "success": False,
                "message": str(e)
            }

    def process_hook_event(self, event_type: str, data: Dict) -> Dict[str, Any]:
        """Process hook event from Claude Code"""
        logger.info(f"Processing {event_type} event for agent '{self.agent_name}'")

        # Extract relevant text based on event type
        text = ""
        if event_type == "notification":
            text = data.get("content", "")
        elif event_type == "pre_tool_use":
            tool_data = data.get("tool", {})
            text = tool_data.get("input", "") or str(tool_data)
        elif event_type == "post_tool_use":
            tool_data = data.get("tool", {})
            text = tool_data.get("output", "") or str(tool_data)
        elif event_type == "message":
            text = data.get("content", "") or data.get("text", "")
        else:
            text = str(data)

        # Always send heartbeat to keep connection alive
        if event_type in ["notification", "message"]:
            self._send_heartbeat()

        # Detect MCP intent
        tool, params = self.detect_mcp_intent(text)

        if tool:
            logger.info(f"Executing MCP tool: {tool} with params: {params}")

            # Execute the tool via MCP server
            result = self.execute_mcp_tool(tool, params)

            if result.get("success"):
                # Return success with system message
                return {
                    "continue": True,
                    "systemMessage": f"✅ MCP v2: {result.get('message', 'Tool executed')}",
                    "suppressOutput": False,
                    "metadata": {
                        "mcp_tool": tool,
                        "mcp_result": result.get("data", {}),
                        "ws_connected": self.ws_connected
                    }
                }
            else:
                # Return error
                return {
                    "continue": True,
                    "systemMessage": f"❌ MCP v2 Error: {result.get('message', 'Unknown error')}",
                    "suppressOutput": False
                }

        # No MCP tool detected, continue normally
        return {"continue": True}

    def _send_heartbeat(self):
        """Send periodic heartbeat to MCP server"""
        try:
            # Send heartbeat in background
            response = self._jsonrpc_call("tools/call", {
                "name": "heartbeat",
                "arguments": {"agent": self.agent_name}
            }, retry_on_fail=False)  # Don't retry heartbeat

            if response and not response.get("error"):
                logger.debug(f"Heartbeat sent for agent '{self.agent_name}'")

        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")


def main():
    """Main entry point for hook processing"""
    try:
        # Get event type from command line
        event_type = sys.argv[1] if len(sys.argv) > 1 else "unknown"

        # Read hook data from stdin
        input_data = sys.stdin.read()
        if input_data:
            data = json.loads(input_data)
        else:
            data = {}

        logger.info(f"Hook triggered: {event_type}")
        logger.debug(f"Data: {json.dumps(data, indent=2)}")

        # Process with MCP Bridge v2 Complete
        bridge = MCPBridgeV2Complete()
        response = bridge.process_hook_event(event_type, data)

        # Output response as JSON
        print(json.dumps(response))
        sys.exit(0)

    except Exception as e:
        logger.error(f"Hook error: {e}")
        # Return error response
        print(json.dumps({
            "continue": True,
            "systemMessage": f"MCP Bridge v2 error: {str(e)}"
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()