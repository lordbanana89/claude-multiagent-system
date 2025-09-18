#!/usr/bin/env python3
"""
MCP Client v2 - Claude Code Hook Integration
Bridges between Claude Code hooks and MCP Server v2 via JSON-RPC 2.0
"""

import sys
import json
import requests
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='/tmp/mcp_client_v2.log'
)
logger = logging.getLogger(__name__)

# Configuration
MCP_SERVER_URL = "http://localhost:8099/jsonrpc"
SESSION_CACHE_FILE = "/tmp/mcp_session.json"

class MCPClient:
    def __init__(self):
        self.server_url = MCP_SERVER_URL
        self.session_id = None
        self.capabilities = None
        self._load_session()

    def _load_session(self):
        """Load existing session from cache"""
        try:
            with open(SESSION_CACHE_FILE, 'r') as f:
                data = json.load(f)
                self.session_id = data.get('session_id')
                self.capabilities = data.get('capabilities')
        except:
            pass

    def _save_session(self):
        """Save session to cache"""
        try:
            with open(SESSION_CACHE_FILE, 'w') as f:
                json.dump({
                    'session_id': self.session_id,
                    'capabilities': self.capabilities
                }, f)
        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    def jsonrpc_call(self, method: str, params: Dict = None, idempotency_key: str = None) -> Dict:
        """Make JSON-RPC 2.0 call to MCP server"""
        request_id = str(uuid.uuid4())

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": request_id
        }

        headers = {
            "Content-Type": "application/json",
            "X-Request-ID": request_id
        }

        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        if self.session_id:
            payload["params"]["session_id"] = self.session_id

        try:
            response = requests.post(self.server_url, json=payload, headers=headers, timeout=30)
            data = response.json()

            if "error" in data:
                logger.error(f"JSON-RPC error: {data['error']}")
                return {"error": data["error"]}

            return data.get("result", {})

        except Exception as e:
            logger.error(f"Failed to call MCP server: {e}")
            return {"error": str(e)}

    def initialize_session(self, client_info: Dict = None) -> bool:
        """Initialize MCP session with capability negotiation"""
        result = self.jsonrpc_call("initialize", {
            "clientInfo": client_info or {
                "name": "Claude Code",
                "version": "1.0.0"
            },
            "capabilities": ["tools", "resources", "prompts"]
        })

        if "error" not in result:
            self.session_id = result.get("session_id")
            self.capabilities = result.get("capabilities")
            self._save_session()
            logger.info(f"Session initialized: {self.session_id}")
            return True

        return False

    def handle_hook(self, hook_type: str, hook_data: Dict) -> Dict:
        """Handle Claude Code hook events"""
        handlers = {
            "SessionStart": self._handle_session_start,
            "SessionEnd": self._handle_session_end,
            "PreToolUse": self._handle_pre_tool_use,
            "PostToolUse": self._handle_post_tool_use,
            "UserPromptSubmit": self._handle_user_prompt_submit,
            "Notification": self._handle_notification,
            "Stop": self._handle_stop,
            "SubagentStop": self._handle_subagent_stop,
            "PreCompact": self._handle_pre_compact
        }

        handler = handlers.get(hook_type)
        if handler:
            return handler(hook_data)

        return {
            "continue": True,
            "suppressOutput": False
        }

    def _handle_session_start(self, data: Dict) -> Dict:
        """Handle SessionStart hook - Initialize MCP connection"""
        logger.info("Handling SessionStart hook")

        # Initialize MCP session
        if self.initialize_session():
            # Get available tools
            tools = self.jsonrpc_call("tools/list")
            resources = self.jsonrpc_call("resources/list")
            prompts = self.jsonrpc_call("prompts/list")

            return {
                "continue": True,
                "systemMessage": f"MCP v2 Connected - {len(tools)} tools, {len(resources)} resources, {len(prompts)} prompts available",
                "suppressOutput": False
            }

        return {
            "continue": True,
            "systemMessage": "Failed to initialize MCP connection",
            "suppressOutput": False
        }

    def _handle_session_end(self, data: Dict) -> Dict:
        """Handle SessionEnd hook - Cleanup session"""
        logger.info("Handling SessionEnd hook")

        # Log session end activity
        if self.session_id:
            self.jsonrpc_call("tools/call", {
                "name": "log_activity",
                "arguments": {
                    "agent": "claude_code",
                    "activity": "Session ended",
                    "category": "communication",
                    "status": "completed",
                    "details": {"session_id": self.session_id}
                }
            })

        return {"continue": True}

    def _handle_pre_tool_use(self, data: Dict) -> Dict:
        """Handle PreToolUse hook - Validate and authorize tool use"""
        tool_name = data.get("tool", {}).get("name", "")
        tool_params = data.get("tool", {}).get("parameters", {})

        logger.info(f"Handling PreToolUse for tool: {tool_name}")

        # Check if it's an MCP tool
        if tool_name.startswith("mcp__"):
            actual_tool_name = tool_name[5:]  # Remove mcp__ prefix

            # Validate tool exists
            tools = self.jsonrpc_call("tools/list")
            tool_names = [t.get("name") for t in tools if isinstance(t, dict)]

            if actual_tool_name not in tool_names:
                return {
                    "continue": False,
                    "stopReason": f"Unknown MCP tool: {actual_tool_name}",
                    "suppressOutput": True
                }

            # Check for dangerous operations
            dangerous_keywords = ["delete", "drop", "remove", "destroy", "reset"]
            if any(keyword in actual_tool_name.lower() for keyword in dangerous_keywords):
                # Log security check
                self.jsonrpc_call("tools/call", {
                    "name": "log_activity",
                    "arguments": {
                        "agent": "claude_code",
                        "activity": f"Security check for tool: {actual_tool_name}",
                        "category": "decision",
                        "status": "completed"
                    }
                })

                return {
                    "continue": True,
                    "systemMessage": f"⚠️ Dangerous operation detected: {actual_tool_name}. Please confirm before proceeding.",
                    "suppressOutput": False
                }

        return {"continue": True}

    def _handle_post_tool_use(self, data: Dict) -> Dict:
        """Handle PostToolUse hook - Log tool results"""
        tool_name = data.get("tool", {}).get("name", "")
        tool_result = data.get("result", {})

        logger.info(f"Handling PostToolUse for tool: {tool_name}")

        # Log MCP tool usage
        if tool_name.startswith("mcp__"):
            actual_tool_name = tool_name[5:]

            self.jsonrpc_call("tools/call", {
                "name": "log_activity",
                "arguments": {
                    "agent": "claude_code",
                    "activity": f"Tool executed: {actual_tool_name}",
                    "category": "task",
                    "status": "completed" if not tool_result.get("error") else "failed",
                    "details": {
                        "tool": actual_tool_name,
                        "success": not bool(tool_result.get("error"))
                    }
                }
            }, idempotency_key=f"post_tool_{tool_name}_{datetime.now().isoformat()}")

        return {"continue": True}

    def _handle_user_prompt_submit(self, data: Dict) -> Dict:
        """Handle UserPromptSubmit hook - Suggest relevant prompts"""
        user_prompt = data.get("prompt", "")

        logger.info(f"Handling UserPromptSubmit: {user_prompt[:100]}...")

        # Get available prompts
        prompts = self.jsonrpc_call("prompts/list")

        # Simple keyword matching for suggestions
        suggestions = []
        keywords_map = {
            "deploy": "deploy_system",
            "test": "run_tests",
            "performance": "analyze_performance",
            "analyze": "analyze_performance"
        }

        for keyword, prompt_name in keywords_map.items():
            if keyword in user_prompt.lower():
                for prompt in prompts:
                    if prompt.get("name") == prompt_name:
                        suggestions.append(prompt)
                        break

        if suggestions:
            message = "💡 Suggested MCP prompts:\n"
            for s in suggestions:
                message += f"- {s['name']}: {s['description']}\n"

            return {
                "continue": True,
                "systemMessage": message,
                "suppressOutput": False
            }

        return {"continue": True}

    def _handle_notification(self, data: Dict) -> Dict:
        """Handle Notification hook"""
        notification_type = data.get("type", "")
        logger.info(f"Handling Notification: {notification_type}")

        # Log notification
        self.jsonrpc_call("tools/call", {
            "name": "log_activity",
            "arguments": {
                "agent": "claude_code",
                "activity": f"Notification: {notification_type}",
                "category": "communication",
                "status": "completed"
            }
        })

        return {"continue": True}

    def _handle_stop(self, data: Dict) -> Dict:
        """Handle Stop hook - User stopped generation"""
        logger.info("Handling Stop hook")

        self.jsonrpc_call("tools/call", {
            "name": "log_activity",
            "arguments": {
                "agent": "claude_code",
                "activity": "User stopped generation",
                "category": "communication",
                "status": "completed"
            }
        })

        return {"continue": True}

    def _handle_subagent_stop(self, data: Dict) -> Dict:
        """Handle SubagentStop hook"""
        subagent = data.get("subagent", "")
        logger.info(f"Handling SubagentStop for: {subagent}")

        self.jsonrpc_call("tools/call", {
            "name": "log_activity",
            "arguments": {
                "agent": "claude_code",
                "activity": f"Subagent stopped: {subagent}",
                "category": "communication",
                "status": "completed"
            }
        })

        return {"continue": True}

    def _handle_pre_compact(self, data: Dict) -> Dict:
        """Handle PreCompact hook - Save state before conversation compaction"""
        logger.info("Handling PreCompact hook")

        # Save important state
        self.jsonrpc_call("tools/call", {
            "name": "log_activity",
            "arguments": {
                "agent": "claude_code",
                "activity": "Conversation compaction starting",
                "category": "communication",
                "status": "started",
                "details": {
                    "session_id": self.session_id,
                    "message_count": data.get("message_count", 0)
                }
            }
        })

        return {
            "continue": True,
            "systemMessage": "📝 MCP state saved before compaction",
            "suppressOutput": False
        }

def main():
    """Main entry point for hook processing"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Usage: mcp_client_v2.py <hook_type>",
            "continue": False
        }))
        sys.exit(1)

    hook_type = sys.argv[1]

    # Read hook data from stdin
    try:
        hook_data = json.load(sys.stdin)
    except:
        hook_data = {}

    # Process hook
    client = MCPClient()

    # Special handling for different command types
    if hook_type == "init":
        # Direct initialization call
        result = client.handle_hook("SessionStart", {})
    elif hook_type == "validate-tool":
        result = client.handle_hook("PreToolUse", hook_data)
    elif hook_type == "process-result":
        result = client.handle_hook("PostToolUse", hook_data)
    elif hook_type == "suggest-prompts":
        result = client.handle_hook("UserPromptSubmit", hook_data)
    else:
        # Standard hook processing
        result = client.handle_hook(hook_type, hook_data)

    # Output result
    print(json.dumps(result))

if __name__ == "__main__":
    main()