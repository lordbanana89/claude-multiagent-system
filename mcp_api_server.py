#!/usr/bin/env python3
"""
MCP API Server - Provides REST API for MCP data to frontend
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import subprocess
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

DB_PATH = "/tmp/mcp_state.db"
PROJECT_DIR = "/Users/erik/Desktop/claude-multiagent-system"

def get_db_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/mcp/status', methods=['GET'])
def get_mcp_status():
    """Get complete MCP system status"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get recent activities
        cursor.execute("""
            SELECT id, agent, timestamp, activity, category, status
            FROM activities
            ORDER BY timestamp DESC
            LIMIT 20
        """)
        activities = [dict(row) for row in cursor.fetchall()]

        # Get components
        cursor.execute("""
            SELECT id, name, type, owner, created_at
            FROM components
            ORDER BY created_at DESC
        """)
        components = [dict(row) for row in cursor.fetchall()]

        # Get agent states
        cursor.execute("""
            SELECT agent, last_seen, status, current_task
            FROM agent_states
            ORDER BY last_seen DESC
        """)
        agent_states = [dict(row) for row in cursor.fetchall()]

        # Get statistics
        cursor.execute("SELECT COUNT(*) as count FROM activities")
        total_activities = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM components")
        total_components = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM agent_states WHERE status = 'active'")
        active_agents = cursor.fetchone()['count']

        try:
            cursor.execute("SELECT COUNT(*) as count FROM conflicts WHERE resolved = 0")
            result = cursor.fetchone()
            conflicts_detected = result['count'] if result else 0
        except:
            conflicts_detected = 0

        conn.close()

        # Check if MCP server is running
        server_running = False
        try:
            result = subprocess.run(['pgrep', '-f', 'mcp_server_complete.py'],
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
                'conflicts_detected': conflicts_detected
            },
            'server_running': server_running,
            'tmux_sessions': tmux_sessions
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/activities', methods=['GET'])
def get_activities():
    """Get recent activities"""
    try:
        limit = request.args.get('limit', 50, type=int)
        agent = request.args.get('agent', None)

        conn = get_db_connection()
        cursor = conn.cursor()

        if agent:
            cursor.execute("""
                SELECT * FROM activities
                WHERE agent = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (agent, limit))
        else:
            cursor.execute("""
                SELECT * FROM activities
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

        activities = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify(activities)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/setup-agent', methods=['POST'])
def setup_agent():
    """Setup MCP configuration for an agent"""
    try:
        data = request.json
        agent_name = data.get('agent_name')
        mcp_config = data.get('mcp_config', {})

        if not agent_name:
            return jsonify({'error': 'agent_name required'}), 400

        # Normalize agent name
        if agent_name.startswith('claude-'):
            agent_name = agent_name[7:]
        agent_name = agent_name.lower().replace(' ', '-').replace('_', '-')

        session_name = f'claude-{agent_name}'

        # Check if session exists, create if not
        subprocess.run(['tmux', 'has-session', '-t', session_name],
                      capture_output=True)
        if subprocess.run(['tmux', 'has-session', '-t', session_name],
                         capture_output=True).returncode != 0:
            subprocess.run(['tmux', 'new-session', '-d', '-s', session_name])

        # First, exit Claude if it's running
        # Send /exit command to exit Claude properly
        subprocess.run(['tmux', 'send-keys', '-t', session_name, '/exit', 'Enter'], capture_output=True)
        time.sleep(1.0)  # Give Claude time to exit

        # Send Ctrl+C to ensure we're at shell prompt
        subprocess.run(['tmux', 'send-keys', '-t', session_name, 'C-c'], capture_output=True)
        time.sleep(0.2)

        # Clear the terminal
        subprocess.run(['tmux', 'send-keys', '-t', session_name, 'clear', 'Enter'])
        time.sleep(0.2)

        # Setup MCP environment variables and configuration
        setup_commands = [
            f"export CLAUDE_AGENT_NAME='{agent_name}'",
            f"export MCP_DB_PATH='{mcp_config.get('db_path', DB_PATH)}'",
            f"export CLAUDE_PROJECT_DIR='{mcp_config.get('project_dir', PROJECT_DIR)}'",
            "export MCP_ENABLED=true",
            "export MCP_BRIDGE_ENABLED=true",
            f"cd {PROJECT_DIR}"
        ]

        # Send each command with a small delay
        for cmd in setup_commands:
            subprocess.run(['tmux', 'send-keys', '-t', session_name, cmd, 'Enter'])
            time.sleep(0.1)

        # Display configuration info
        info_commands = [
            "echo '🔧 MCP Configuration Applied'",
            "echo 'Agent Name: '$CLAUDE_AGENT_NAME",
            "echo 'MCP Database: '$MCP_DB_PATH",
            "echo 'Project Directory: '$CLAUDE_PROJECT_DIR",
            "echo ''",
            "echo '✅ Ready! Starting Claude with MCP...'"
        ]

        for cmd in info_commands:
            subprocess.run(['tmux', 'send-keys', '-t', session_name, cmd, 'Enter'])
            time.sleep(0.1)

        # Auto-start Claude
        time.sleep(0.5)
        subprocess.run(['tmux', 'send-keys', '-t', session_name, 'claude', 'Enter'])

        # Log setup activity
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO activities (id, agent, timestamp, activity, category, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            f"setup_{agent_name}_{datetime.now().timestamp()}",
            'system',
            datetime.now().isoformat(),
            f"MCP setup completed for: {agent_name}",
            'configuration',
            'completed'
        ))

        # Update agent state
        cursor.execute("""
            INSERT OR REPLACE INTO agent_states (agent, last_seen, status, current_task)
            VALUES (?, ?, ?, ?)
        """, (
            agent_name,
            datetime.now().isoformat(),
            'configured',
            'MCP Environment Ready'
        ))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'MCP configuration applied for {agent_name}',
            'session': session_name
        })

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

        # Clean up agent name (remove 'claude-' prefix if present and normalize)
        if agent_name.startswith('claude-'):
            agent_name = agent_name[7:]

        # Normalize name: replace spaces with dashes, lowercase
        agent_name = agent_name.lower().replace(' ', '-').replace('_', '-')

        # Kill existing session if exists
        subprocess.run(['tmux', 'kill-session', '-t', f'claude-{agent_name}'],
                      capture_output=True)

        # Create new TMUX session
        session_name = f'claude-{agent_name}'
        subprocess.run(['tmux', 'new-session', '-d', '-s', session_name])

        # Set environment and start Claude
        commands = [
            f"export CLAUDE_AGENT_NAME='{agent_name}'",
            f"export MCP_DB_PATH='{DB_PATH}'",
            f"export CLAUDE_PROJECT_DIR='{PROJECT_DIR}'",
            f"cd {PROJECT_DIR}",
            "claude"
        ]

        for cmd in commands:
            subprocess.run(['tmux', 'send-keys', '-t', session_name, cmd, 'Enter'])

        # Start ttyd terminal for this agent
        port_map = {
            'backend-api': 8090,
            'database': 8091,
            'frontend-ui': 8092,
            'testing': 8093,
            'instagram': 8094,
            'supervisor': 8095,
            'master': 8096,
            'deployment': 8097,
            'queue-manager': 8098
        }

        if agent_name in port_map:
            port = port_map[agent_name]
            # Kill any existing ttyd on this port
            subprocess.run(['pkill', '-f', f'ttyd.*-p {port}'], capture_output=True)
            # Start new ttyd
            subprocess.Popen([
                'ttyd', '-p', str(port), '--writable',
                '-t', f'titleFixed={agent_name.title()} Agent',
                'tmux', 'attach', '-t', session_name
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Log activity
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO activities (id, agent, timestamp, activity, category, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            f"start_{agent_name}_{datetime.now().timestamp()}",
            'system',
            datetime.now().isoformat(),
            f"Started agent: {agent_name}",
            'info',
            'completed'
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
            # Log activity
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO activities (id, agent, timestamp, activity, category, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                f"stop_{agent_name}_{datetime.now().timestamp()}",
                'system',
                datetime.now().isoformat(),
                f"Stopped agent: {agent_name}",
                'info',
                'completed'
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
            SELECT * FROM agent_states
            ORDER BY last_seen DESC
        """)

        states = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify(states)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/conflicts', methods=['GET'])
def get_conflicts():
    """Get detected conflicts"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if conflicts table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conflicts'")
        if not cursor.fetchone():
            return jsonify([])  # No conflicts table yet

        cursor.execute("""
            SELECT * FROM conflicts
            WHERE resolved = 0
            ORDER BY detected_at DESC
        """)

        conflicts = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify(conflicts)

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
            INSERT OR REPLACE INTO agent_states (agent, last_seen, status, current_task)
            VALUES (?, ?, ?, ?)
        """, (
            agent_name,
            datetime.now().isoformat(),
            'active',
            data.get('current_task', '')
        ))

        conn.commit()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/terminals', methods=['GET'])
def get_terminal_status():
    """Get status of ttyd terminals"""
    try:
        port_map = {
            'backend-api': 8090,
            'database': 8091,
            'frontend-ui': 8092,
            'testing': 8093,
            'instagram': 8094,
            'supervisor': 8095,
            'master': 8096,
            'deployment': 8097,
            'queue-manager': 8098
        }

        terminal_status = {}
        for agent, port in port_map.items():
            # Check if ttyd is running on this port
            result = subprocess.run(['lsof', '-i', f':{port}'],
                                  capture_output=True, text=True)
            terminal_status[agent] = {
                'port': port,
                'running': bool(result.stdout and 'ttyd' in result.stdout),
                'url': f'http://localhost:{port}' if result.stdout else None
            }

        return jsonify(terminal_status)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 MCP API Server starting on http://localhost:5001")
    print(f"📊 Database: {DB_PATH}")
    print(f"📁 Project: {PROJECT_DIR}")
    print("")
    print("Endpoints:")
    print("  GET  /api/mcp/status       - Full system status")
    print("  GET  /api/mcp/activities   - Recent activities")
    print("  GET  /api/mcp/components   - Registered components")
    print("  GET  /api/mcp/agent-states - Agent states")
    print("  POST /api/mcp/start-agent  - Start an agent")
    print("  POST /api/mcp/stop-agent   - Stop an agent")
    print("  POST /api/mcp/heartbeat    - Send agent heartbeat")
    print("  GET  /api/mcp/terminals    - Terminal status")
    print("")

    app.run(host='0.0.0.0', port=5001, debug=True)