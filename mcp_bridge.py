#!/usr/bin/env python3
"""
MCP Bridge for Claude Code Hooks
Intercepts Claude's commands and translates to MCP operations
"""

import json
import sys
import re
import sqlite3
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
import os

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mcp_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MCPBridge:
    """Bridge between Claude Code Hooks and MCP Server"""

    def __init__(self):
        self.db_path = os.getenv("MCP_DB_PATH", "/tmp/mcp_state.db")
        self.project_dir = os.getenv("CLAUDE_PROJECT_DIR", "/Users/erik/Desktop/claude-multiagent-system")

        # MCP tool patterns - what Claude might say to trigger each tool
        self.tool_patterns = {
            'log_activity': [
                r"(?:I'll |I will |Let me )?(?:use|call|invoke) (?:the )?log_activity (?:tool|MCP tool)(?: to)? (.+)",
                r"log_activity[:\s]+(.+)",
                r"(?:logging|log) (?:the )?activity[:\s]+(.+)",
                r"(?:announce|announcing)[:\s]+(.+)"
            ],
            'check_conflicts': [
                r"(?:check|checking) (?:for )?conflicts?(?: for)? (.+)",
                r"(?:use|call) check_conflicts(?: tool)?(?: for)? (.+)",
                r"(?:verify|verifying) (?:no )?conflicts?(?: with)? (.+)"
            ],
            'register_component': [
                r"register(?:ing)? component[:\s]+(.+)",
                r"(?:use|call) register_component(?: tool)?[:\s]+(.+)",
                r"(?:creating|created) component[:\s]+(.+)"
            ],
            'update_status': [
                r"(?:update|updating) (?:my )?status(?: to)?[:\s]+(.+)",
                r"status update[:\s]+(.+)",
                r"(?:I'm|I am) now (.+)"
            ],
            'heartbeat': [
                r"(?:send|sending) heartbeat",
                r"(?:I'm|I am) (?:still )?(?:active|alive)",
                r"heartbeat",
                r"keep.?alive"
            ],
            'request_collaboration': [
                r"(?:request|requesting) (?:collaboration|help)(?: from)? (.+)",
                r"(?:need|needing) (?:help|assistance)(?: with)? (.+)",
                r"collaborate(?: on)? (.+)"
            ],
            'propose_decision': [
                r"(?:propose|proposing) (?:decision|choice)[:\s]+(.+)",
                r"(?:should we|we should) (.+)",
                r"(?:vote|voting) (?:on|for)[:\s]+(.+)"
            ],
            'find_component_owner': [
                r"(?:who|what) (?:owns|created) (.+)",
                r"find (?:owner|creator) (?:of|for) (.+)",
                r"component owner[:\s]+(.+)"
            ]
        }

        # Ensure database exists
        self._init_database()

    def _init_database(self):
        """Initialize database if needed"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            if 'activities' not in tables:
                logger.warning("Database tables not found, creating...")
                # Create minimal tables if they don't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS activities (
                        id TEXT PRIMARY KEY,
                        agent TEXT,
                        timestamp TEXT,
                        activity TEXT,
                        category TEXT,
                        metadata TEXT,
                        status TEXT
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS components (
                        id TEXT PRIMARY KEY,
                        name TEXT,
                        type TEXT,
                        owner TEXT,
                        description TEXT,
                        dependencies TEXT,
                        interfaces TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        version INTEGER DEFAULT 1
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS agent_states (
                        agent TEXT PRIMARY KEY,
                        last_seen TEXT,
                        status TEXT,
                        current_task TEXT
                    )
                """)

                conn.commit()

            conn.close()
        except Exception as e:
            logger.error(f"Database init error: {e}")

    def detect_mcp_intent(self, text: str) -> Tuple[Optional[str], Optional[Dict]]:
        """Detect if text contains intent to use MCP tool"""
        if not text:
            return None, None

        text = text.strip()

        # Check each tool's patterns
        for tool, patterns in self.tool_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    logger.info(f"Detected intent for tool '{tool}' from pattern: {pattern}")

                    # Extract parameters based on tool
                    params = self._extract_params(tool, match, text)
                    return tool, params

        return None, None

    def _extract_params(self, tool: str, match: re.Match, full_text: str) -> Dict:
        """Extract parameters for specific tool"""
        params = {}

        # Extract agent name from context
        agent_name = self._detect_agent_name(full_text)
        params['agent'] = agent_name

        if tool == 'log_activity':
            activity = match.group(1) if match.groups() else full_text
            params['activity'] = activity.strip('" ')
            params['category'] = self._categorize_activity(activity)

        elif tool == 'check_conflicts':
            params['planned_action'] = match.group(1).strip('" ') if match.groups() else ""

        elif tool == 'register_component':
            component_info = match.group(1).strip('" ') if match.groups() else ""
            # Try to parse component type and name
            if ':' in component_info:
                parts = component_info.split(':', 1)
                params['type'] = parts[0].strip()
                params['name'] = parts[1].strip()
            else:
                params['name'] = component_info
                params['type'] = 'unknown'

        elif tool == 'update_status':
            status = match.group(1).strip('" ') if match.groups() else "working"
            params['status'] = status

        elif tool == 'heartbeat':
            # No additional params needed
            pass

        elif tool == 'request_collaboration':
            params['task'] = match.group(1).strip('" ') if match.groups() else ""
            params['priority'] = 'medium'

        elif tool == 'propose_decision':
            params['decision'] = match.group(1).strip('" ') if match.groups() else ""

        elif tool == 'find_component_owner':
            params['component_name'] = match.group(1).strip('" ') if match.groups() else ""

        return params

    def _detect_agent_name(self, text: str) -> str:
        """Detect agent name from context"""
        # Look for patterns like "I am the backend-api agent"
        patterns = [
            r"I am the (\w+[-\w]*) agent",
            r"Agent[:\s]+(\w+[-\w]*)",
            r"Role[:\s]+(\w+[-\w]*)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        # Check environment or default
        return os.getenv("CLAUDE_AGENT_NAME", "unknown")

    def _categorize_activity(self, activity: str) -> str:
        """Categorize activity type"""
        activity_lower = activity.lower()

        if any(word in activity_lower for word in ['plan', 'design', 'think', 'consider']):
            return 'planning'
        elif any(word in activity_lower for word in ['create', 'build', 'implement', 'code']):
            return 'implementation'
        elif any(word in activity_lower for word in ['test', 'verify', 'check', 'validate']):
            return 'testing'
        elif any(word in activity_lower for word in ['complete', 'finish', 'done']):
            return 'completion'
        elif any(word in activity_lower for word in ['error', 'fail', 'issue', 'problem']):
            return 'error'
        else:
            return 'info'

    def execute_mcp_tool(self, tool: str, params: Dict) -> Dict[str, Any]:
        """Execute MCP tool by directly interacting with database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if tool == 'log_activity':
                activity_id = hashlib.md5(f"{params.get('agent', 'unknown')}{datetime.now().isoformat()}".encode()).hexdigest()

                cursor.execute("""
                    INSERT INTO activities (id, agent, timestamp, activity, category, metadata, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    activity_id,
                    params.get('agent', 'unknown'),
                    datetime.now().isoformat(),
                    params.get('activity', ''),
                    params.get('category', 'info'),
                    json.dumps(params.get('metadata', {})),
                    'completed'
                ))
                conn.commit()

                # Also log to shared context file
                with open('/tmp/mcp_shared_context.log', 'a') as f:
                    f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {params.get('agent', 'unknown')}: {params.get('activity', '')}\n")

                return {"success": True, "message": "Activity logged successfully"}

            elif tool == 'check_conflicts':
                action = params.get('planned_action', '')

                # Check for conflicts in recent activities
                cursor.execute("""
                    SELECT agent, activity, timestamp FROM activities
                    WHERE agent != ? AND activity LIKE ?
                    ORDER BY timestamp DESC LIMIT 5
                """, (params.get('agent', 'unknown'), f"%{action.split()[0] if action else ''}%"))

                conflicts = cursor.fetchall()

                if conflicts:
                    return {
                        "success": True,
                        "conflicts": [{"agent": c[0], "activity": c[1]} for c in conflicts],
                        "message": f"Found {len(conflicts)} potential conflicts"
                    }
                else:
                    return {"success": True, "conflicts": [], "message": "No conflicts detected"}

            elif tool == 'register_component':
                component_id = hashlib.md5(f"{params.get('name', '')}{params.get('type', '')}".encode()).hexdigest()
                now = datetime.now().isoformat()

                cursor.execute("""
                    INSERT OR REPLACE INTO components
                    (id, name, type, owner, description, dependencies, interfaces, created_at, updated_at, version)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    component_id,
                    params.get('name', ''),
                    params.get('type', 'unknown'),
                    params.get('agent', 'unknown'),
                    params.get('description', ''),
                    json.dumps(params.get('dependencies', [])),
                    json.dumps(params.get('interfaces', {})),
                    now,
                    now,
                    1
                ))
                conn.commit()

                return {"success": True, "message": f"Component '{params.get('name')}' registered"}

            elif tool == 'update_status':
                cursor.execute("""
                    INSERT OR REPLACE INTO agent_states (agent, last_seen, status, current_task)
                    VALUES (?, ?, ?, ?)
                """, (
                    params.get('agent', 'unknown'),
                    datetime.now().isoformat(),
                    params.get('status', 'active'),
                    params.get('current_task', '')
                ))
                conn.commit()

                return {"success": True, "message": f"Status updated to '{params.get('status')}'"}

            elif tool == 'heartbeat':
                cursor.execute("""
                    INSERT OR REPLACE INTO agent_states (agent, last_seen, status, current_task)
                    VALUES (?, ?, ?, ?)
                """, (
                    params.get('agent', 'unknown'),
                    datetime.now().isoformat(),
                    'active',
                    ''
                ))
                conn.commit()

                return {"success": True, "message": "Heartbeat recorded"}

            elif tool == 'find_component_owner':
                cursor.execute("""
                    SELECT owner, type FROM components
                    WHERE name = ?
                """, (params.get('component_name', ''),))

                result = cursor.fetchone()
                if result:
                    return {
                        "success": True,
                        "owner": result[0],
                        "type": result[1],
                        "message": f"Component owned by {result[0]}"
                    }
                else:
                    return {"success": True, "owner": None, "message": "Component not found"}

            else:
                conn.close()
                return {"success": False, "message": f"Tool '{tool}' not implemented yet"}

            conn.close()

        except Exception as e:
            logger.error(f"Error executing tool '{tool}': {e}")
            return {"success": False, "message": str(e)}

    def process_hook_event(self, event_type: str, data: Dict) -> Dict[str, Any]:
        """Process hook event from Claude Code"""
        logger.info(f"Processing {event_type} event")

        # Extract relevant text based on event type
        text = ""
        if event_type == "notification":
            text = data.get("content", "")
        elif event_type == "pre_tool_use":
            text = data.get("tool", {}).get("input", "")
        elif event_type == "post_tool_use":
            text = data.get("tool", {}).get("output", "")
        else:
            text = str(data)

        # Detect MCP intent
        tool, params = self.detect_mcp_intent(text)

        if tool:
            logger.info(f"Executing MCP tool: {tool} with params: {params}")

            # Execute the tool
            result = self.execute_mcp_tool(tool, params)

            if result.get("success"):
                # Return success with system message
                return {
                    "continue": True,
                    "systemMessage": f"✅ MCP: {result.get('message', 'Tool executed')}",
                    "suppressOutput": False
                }
            else:
                # Return error
                return {
                    "continue": True,
                    "systemMessage": f"❌ MCP Error: {result.get('message', 'Unknown error')}",
                    "suppressOutput": False
                }

        # No MCP tool detected, continue normally
        return {"continue": True}


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

        # Process with bridge
        bridge = MCPBridge()
        response = bridge.process_hook_event(event_type, data)

        # Output response as JSON
        print(json.dumps(response))
        sys.exit(0)

    except Exception as e:
        logger.error(f"Hook error: {e}")
        # Return error response
        print(json.dumps({
            "continue": True,
            "systemMessage": f"Bridge error: {str(e)}"
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()