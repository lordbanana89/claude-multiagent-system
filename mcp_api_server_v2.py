#!/usr/bin/env python3
"""
MCP API Server V2 - Provides REST API for real MCP database
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import subprocess
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Use the actual MCP database
DB_PATH = "mcp_system.db"
INBOX_DB_PATH = "langgraph-test/shared_inbox.db"
PROJECT_DIR = "/Users/erik/Desktop/claude-multiagent-system"

def get_db_connection(db_path=DB_PATH):
    """Get SQLite database connection"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/mcp/status', methods=['GET'])
def get_mcp_status():
    """Get complete MCP system status from real database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get recent activities from activity_logs table
        cursor.execute("""
            SELECT
                id,
                agent_id as agent,
                timestamp,
                activity,
                category,
                CASE
                    WHEN category = 'error' THEN 'failed'
                    WHEN category = 'task' THEN 'in_progress'
                    ELSE 'completed'
                END as status
            FROM activity_logs
            ORDER BY timestamp DESC
            LIMIT 20
        """)
        activities = [dict(row) for row in cursor.fetchall()]

        # Get components from components table
        cursor.execute("""
            SELECT
                id,
                name,
                type,
                owner,
                created_at
            FROM components
            ORDER BY created_at DESC
        """)
        components = [dict(row) for row in cursor.fetchall()]

        # Get agent states from agents table
        cursor.execute("""
            SELECT
                id as agent,
                last_heartbeat as last_seen,
                status,
                current_task
            FROM agents
            ORDER BY last_heartbeat DESC
        """)
        agent_states = [dict(row) for row in cursor.fetchall()]

        # Get statistics
        cursor.execute("SELECT COUNT(*) as count FROM activity_logs")
        total_activities = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM components")
        total_components = cursor.fetchone()['count']

        # Count agents that were active in last 60 seconds
        one_minute_ago = (datetime.now() - timedelta(seconds=60)).isoformat()
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM agents
            WHERE last_heartbeat > ? AND status != 'offline'
        """, (one_minute_ago,))
        active_agents = cursor.fetchone()['count']

        # Check for any unresolved tasks
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM tasks
            WHERE status = 'pending' OR status = 'in_progress'
        """)
        pending_tasks = cursor.fetchone()['count']

        conn.close()

        # Check if MCP server is running
        server_running = False
        try:
            result = subprocess.run(['pgrep', '-f', 'mcp_server'],
                                 capture_output=True, text=True)
            server_running = bool(result.stdout.strip())
        except:
            pass

        # Get TMUX sessions
        tmux_sessions = []
        try:
            result = subprocess.run(['tmux', 'list-sessions'],
                                 capture_output=True, text=True)
            if result.returncode == 0:
                sessions = result.stdout.strip().split('\n')
                tmux_sessions = [s.split(':')[0] for s in sessions if 'claude-' in s.lower()]
        except:
            pass

        return jsonify({
            'activities': activities,
            'components': components,
            'agent_states': agent_states,
            'stats': {
                'total_activities': total_activities,
                'total_components': total_components,
                'active_agents': active_agents,
                'conflicts_detected': pending_tasks  # Using pending tasks as a proxy
            },
            'server_running': server_running,
            'tmux_sessions': tmux_sessions
        })

    except Exception as e:
        print(f"Error in get_mcp_status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/activities', methods=['GET'])
def get_activities():
    """Get recent activities from activity_logs"""
    try:
        limit = request.args.get('limit', 50, type=int)
        agent = request.args.get('agent', None)

        conn = get_db_connection()
        cursor = conn.cursor()

        if agent:
            cursor.execute("""
                SELECT
                    id,
                    agent_id as agent,
                    timestamp,
                    activity,
                    category,
                    details
                FROM activity_logs
                WHERE agent_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (agent, limit))
        else:
            cursor.execute("""
                SELECT
                    id,
                    agent_id as agent,
                    timestamp,
                    activity,
                    category,
                    details
                FROM activity_logs
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

        activities = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify(activities)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/messages', methods=['GET'])
def get_messages():
    """Get messages from shared inbox"""
    try:
        agent = request.args.get('agent', None)
        limit = request.args.get('limit', 20, type=int)

        conn = get_db_connection(INBOX_DB_PATH)
        cursor = conn.cursor()

        if agent:
            cursor.execute("""
                SELECT
                    message_id as id,
                    sender_id as sender,
                    recipient_id as recipient,
                    subject,
                    content,
                    timestamp,
                    status
                FROM messages
                WHERE recipient_id = ? OR sender_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (agent, agent, limit))
        else:
            cursor.execute("""
                SELECT
                    message_id as id,
                    sender_id as sender,
                    recipient_id as recipient,
                    subject,
                    content,
                    timestamp,
                    status
                FROM messages
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify(messages)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/start-agent', methods=['POST'])
def start_agent():
    """Start a Claude agent with MCP"""
    try:
        data = request.json
        agent_name = data.get('agent_name')

        if not agent_name:
            return jsonify({'error': 'agent_name required'}), 400

        # Clean up agent name
        if agent_name.startswith('claude-'):
            agent_name = agent_name[7:]

        agent_name = agent_name.lower().replace(' ', '-').replace('_', '-')

        # Kill existing session if exists
        subprocess.run(['tmux', 'kill-session', '-t', f'claude-{agent_name}'],
                      capture_output=True)

        # Create new TMUX session
        session_name = f'claude-{agent_name}'
        subprocess.run(['tmux', 'new-session', '-d', '-s', session_name])

        # Set environment and initialize agent
        commands = [
            f"cd {PROJECT_DIR}",
            f"source ./agent_tools.sh",
            f"export AGENT_NAME={agent_name}",
            f"export MCP_URL=http://localhost:9999",
            f"init_agent {agent_name}",
            f"echo 'Agent {agent_name} initialized and ready'"
        ]

        for cmd in commands:
            subprocess.run(['tmux', 'send-keys', '-t', session_name, cmd, 'Enter'])
            time.sleep(0.2)

        # Log activity
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update agent status
        cursor.execute("""
            INSERT OR REPLACE INTO agents (id, name, status, last_heartbeat, current_task)
            VALUES (?, ?, 'idle', ?, 'Starting up')
        """, (agent_name, agent_name, datetime.now().isoformat()))

        # Log activity
        cursor.execute("""
            INSERT INTO activity_logs (id, agent_id, category, activity, details)
            VALUES (?, ?, 'system', 'Agent started', ?)
        """, (
            f"start_{agent_name}_{datetime.now().timestamp()}",
            agent_name,
            json.dumps({'session': session_name})
        ))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': f'Agent {agent_name} started'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/stop-agent', methods=['POST'])
def stop_agent():
    """Stop a Claude agent"""
    try:
        data = request.json
        agent_name = data.get('agent_name')

        if not agent_name:
            return jsonify({'error': 'agent_name required'}), 400

        session_name = f'claude-{agent_name}'
        result = subprocess.run(['tmux', 'kill-session', '-t', session_name],
                               capture_output=True, text=True)

        if result.returncode == 0:
            # Update agent status in database
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE agents
                SET status = 'offline', updated_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), agent_name))

            # Log activity
            cursor.execute("""
                INSERT INTO activity_logs (id, agent_id, category, activity)
                VALUES (?, ?, 'system', 'Agent stopped')
            """, (
                f"stop_{agent_name}_{datetime.now().timestamp()}",
                agent_name
            ))

            conn.commit()
            conn.close()

            return jsonify({'success': True, 'message': f'Agent {agent_name} stopped'})
        else:
            return jsonify({'error': 'Failed to stop agent'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/components', methods=['GET'])
def get_components():
    """Get registered components"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM components
            ORDER BY created_at DESC
        """)

        components = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify(components)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/agent-states', methods=['GET'])
def get_agent_states():
    """Get current agent states"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                name,
                status,
                last_heartbeat,
                current_task,
                metadata
            FROM agents
            ORDER BY last_heartbeat DESC
        """)

        states = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify(states)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/tasks', methods=['GET'])
def get_tasks():
    """Get tasks from the system"""
    try:
        status_filter = request.args.get('status', None)

        conn = get_db_connection()
        cursor = conn.cursor()

        if status_filter:
            cursor.execute("""
                SELECT * FROM tasks
                WHERE status = ?
                ORDER BY created_at DESC
            """, (status_filter,))
        else:
            cursor.execute("""
                SELECT * FROM tasks
                ORDER BY created_at DESC
            """)

        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify(tasks)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/heartbeat', methods=['POST'])
def send_heartbeat():
    """Send heartbeat for an agent"""
    try:
        data = request.json
        agent_name = data.get('agent_name')

        if not agent_name:
            return jsonify({'error': 'agent_name required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE agents
            SET last_heartbeat = ?, status = 'idle', updated_at = ?
            WHERE id = ?
        """, (
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            agent_name
        ))

        # Also insert the agent if it doesn't exist
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO agents (id, name, status, last_heartbeat)
                VALUES (?, ?, 'idle', ?)
            """, (agent_name, agent_name, datetime.now().isoformat()))

        conn.commit()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': DB_PATH
    })

if __name__ == '__main__':
    print("🚀 MCP API Server V2 starting on http://localhost:5001")
    print(f"📊 Database: {DB_PATH}")
    print(f"📬 Inbox DB: {INBOX_DB_PATH}")
    print(f"📁 Project: {PROJECT_DIR}")
    print("")
    print("Endpoints:")
    print("  GET  /api/mcp/status       - Full system status")
    print("  GET  /api/mcp/activities   - Recent activities")
    print("  GET  /api/mcp/messages     - Inbox messages")
    print("  GET  /api/mcp/components   - Registered components")
    print("  GET  /api/mcp/agent-states - Agent states")
    print("  GET  /api/mcp/tasks        - System tasks")
    print("  POST /api/mcp/start-agent  - Start an agent")
    print("  POST /api/mcp/stop-agent   - Stop an agent")
    print("  POST /api/mcp/heartbeat    - Send agent heartbeat")
    print("  GET  /api/mcp/health       - Health check")
    print("")

    app.run(host='0.0.0.0', port=5001, debug=True)