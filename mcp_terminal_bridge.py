#!/usr/bin/env python3
"""
MCP Terminal Bridge - Connects TMUX terminals to MCP system
"""

import asyncio
import json
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# MCP Tools available in terminals
MCP_TOOLS = {
    "init_agent": "Initialize an agent in the MCP system",
    "send_message": "Send a message to another agent",
    "read_inbox": "Read messages from inbox",
    "log_activity": "Log an activity to the MCP system",
    "status": "Update agent status",
    "heartbeat": "Send heartbeat signal",
    "check_agents": "Check status of all agents",
    "view_activities": "View recent activities"
}

def init_database():
    """Initialize MCP database if needed"""
    conn = sqlite3.connect('mcp_system.db')
    cursor = conn.cursor()

    # Ensure tables exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS agent_states (
        agent TEXT PRIMARY KEY,
        last_seen TEXT,
        status TEXT,
        current_task TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS activities (
        id TEXT PRIMARY KEY,
        agent TEXT,
        timestamp TEXT,
        activity TEXT,
        category TEXT,
        status TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_agent TEXT,
        to_agent TEXT,
        message TEXT,
        timestamp TEXT,
        read INTEGER DEFAULT 0
    )''')

    conn.commit()
    conn.close()

def execute_mcp_tool(tool_name, agent_name, args):
    """Execute an MCP tool for an agent"""
    conn = sqlite3.connect('mcp_system.db')
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()

    try:
        if tool_name == "init_agent":
            cursor.execute('''INSERT OR REPLACE INTO agent_states
                VALUES (?, ?, 'active', 'Initialized')''',
                (agent_name, timestamp))
            result = f"Agent {agent_name} initialized"

        elif tool_name == "status":
            status = args.get('status', 'active')
            task = args.get('task', '')
            cursor.execute('''UPDATE agent_states
                SET status = ?, current_task = ?, last_seen = ?
                WHERE agent = ?''',
                (status, task, timestamp, agent_name))
            result = f"Status updated: {status}"

        elif tool_name == "heartbeat":
            cursor.execute('''UPDATE agent_states
                SET last_seen = ? WHERE agent = ?''',
                (timestamp, agent_name))
            result = "Heartbeat sent"

        elif tool_name == "log_activity":
            activity_id = f"{agent_name}_{int(datetime.now().timestamp())}"
            activity = args.get('activity', '')
            category = args.get('category', 'general')
            cursor.execute('''INSERT INTO activities
                VALUES (?, ?, ?, ?, ?, 'completed')''',
                (activity_id, agent_name, timestamp, activity, category))
            result = f"Activity logged: {activity}"

        elif tool_name == "send_message":
            to_agent = args.get('to', '')
            message = args.get('message', '')
            cursor.execute('''INSERT INTO messages (from_agent, to_agent, message, timestamp)
                VALUES (?, ?, ?, ?)''',
                (agent_name, to_agent, message, timestamp))
            result = f"Message sent to {to_agent}"

        elif tool_name == "read_inbox":
            cursor.execute('''SELECT from_agent, message, timestamp
                FROM messages WHERE to_agent = ? AND read = 0
                ORDER BY timestamp DESC LIMIT 5''',
                (agent_name,))
            messages = cursor.fetchall()
            cursor.execute('''UPDATE messages SET read = 1
                WHERE to_agent = ?''', (agent_name,))
            result = json.dumps([{
                'from': m[0], 'message': m[1], 'timestamp': m[2]
            } for m in messages])

        elif tool_name == "check_agents":
            cursor.execute('''SELECT agent, status, current_task
                FROM agent_states ORDER BY agent''')
            agents = cursor.fetchall()
            result = json.dumps([{
                'agent': a[0], 'status': a[1], 'task': a[2]
            } for a in agents])

        elif tool_name == "view_activities":
            cursor.execute('''SELECT agent, activity, category, timestamp
                FROM activities ORDER BY timestamp DESC LIMIT 10''')
            activities = cursor.fetchall()
            result = json.dumps([{
                'agent': a[0], 'activity': a[1],
                'category': a[2], 'timestamp': a[3]
            } for a in activities])

        else:
            result = f"Unknown tool: {tool_name}"

        conn.commit()
        conn.close()
        return result

    except Exception as e:
        conn.close()
        return f"Error: {str(e)}"

def inject_mcp_functions(session_name):
    """Inject MCP functions into TMUX session"""
    agent_name = session_name.replace('claude-', '')

    # Create shell functions for MCP tools
    functions = []

    # Basic MCP functions
    functions.append(f'''
function mcp_init() {{
    echo "Initializing {agent_name} in MCP system..."
    python3 -c "
import sys
sys.path.insert(0, '/Users/erik/Desktop/claude-multiagent-system')
from mcp_terminal_bridge import execute_mcp_tool
result = execute_mcp_tool('init_agent', '{agent_name}', {{}})
print(result)
"
}}
''')

    functions.append(f'''
function mcp_status() {{
    local status=$1
    local task=$2
    python3 -c "
import sys
sys.path.insert(0, '/Users/erik/Desktop/claude-multiagent-system')
from mcp_terminal_bridge import execute_mcp_tool
result = execute_mcp_tool('status', '{agent_name}', {{'status': '$status', 'task': '$task'}})
print(result)
"
}}
''')

    functions.append(f'''
function mcp_heartbeat() {{
    python3 -c "
import sys
sys.path.insert(0, '/Users/erik/Desktop/claude-multiagent-system')
from mcp_terminal_bridge import execute_mcp_tool
result = execute_mcp_tool('heartbeat', '{agent_name}', {{}})
print(result)
"
}}
''')

    functions.append(f'''
function mcp_send() {{
    local to_agent=$1
    shift
    local message="$@"
    python3 -c "
import sys
sys.path.insert(0, '/Users/erik/Desktop/claude-multiagent-system')
from mcp_terminal_bridge import execute_mcp_tool
result = execute_mcp_tool('send_message', '{agent_name}', {{'to': '$to_agent', 'message': '$message'}})
print(result)
"
}}
''')

    functions.append(f'''
function mcp_inbox() {{
    python3 -c "
import sys, json
sys.path.insert(0, '/Users/erik/Desktop/claude-multiagent-system')
from mcp_terminal_bridge import execute_mcp_tool
result = execute_mcp_tool('read_inbox', '{agent_name}', {{}})
messages = json.loads(result)
for msg in messages:
    print(f'From {{msg[\\"from\\"]}}: {{msg[\\"message\\"]}}')
"
}}
''')

    functions.append(f'''
function mcp_log() {{
    local activity="$@"
    python3 -c "
import sys
sys.path.insert(0, '/Users/erik/Desktop/claude-multiagent-system')
from mcp_terminal_bridge import execute_mcp_tool
result = execute_mcp_tool('log_activity', '{agent_name}', {{'activity': '$activity', 'category': 'task'}})
print(result)
"
}}
''')

    # Send functions to TMUX session
    for func in functions:
        # Clean up the function string
        func_lines = func.strip().split('\n')
        for line in func_lines:
            if line.strip():
                cmd = f"tmux send-keys -t {session_name} '{line}' C-m"
                subprocess.run(cmd, shell=True, capture_output=True)

    # Initialize the agent
    subprocess.run(f"tmux send-keys -t {session_name} 'mcp_init' C-m",
                   shell=True, capture_output=True)

    # Show available commands
    help_text = f'''
echo "🤖 MCP Tools Available for {agent_name}:"
echo "  mcp_init         - Initialize agent in MCP"
echo "  mcp_status <status> <task> - Update status"
echo "  mcp_heartbeat    - Send heartbeat"
echo "  mcp_send <agent> <message> - Send message"
echo "  mcp_inbox        - Read inbox"
echo "  mcp_log <activity> - Log activity"
echo ""
echo "✅ MCP: Connected"
'''

    for line in help_text.strip().split('\n'):
        cmd = f"tmux send-keys -t {session_name} '{line}' C-m"
        subprocess.run(cmd, shell=True, capture_output=True)

def main():
    """Initialize MCP bridge for all agent terminals"""
    print("🚀 Starting MCP Terminal Bridge")

    # Initialize database
    init_database()

    # Get all TMUX sessions
    result = subprocess.run(['tmux', 'list-sessions', '-F', '#{session_name}'],
                           capture_output=True, text=True)

    if result.returncode == 0:
        sessions = [s for s in result.stdout.strip().split('\n')
                   if s.startswith('claude-')]

        print(f"Found {len(sessions)} agent sessions")

        for session in sessions:
            print(f"Injecting MCP tools into {session}...")
            inject_mcp_functions(session)

        print("✅ MCP Terminal Bridge initialized for all agents")

        # Keep the bridge running
        print("\nBridge is running. Press Ctrl+C to stop.")
        try:
            while True:
                asyncio.run(asyncio.sleep(1))
        except KeyboardInterrupt:
            print("\n👋 MCP Terminal Bridge stopped")
    else:
        print("❌ No TMUX sessions found")

if __name__ == "__main__":
    main()