#!/usr/bin/env python3
"""
MCP API Server Optimized - REST API with reduced polling overhead
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import subprocess
import json
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

app = Flask(__name__)
CORS(app)

DB_PATH = "/tmp/mcp_state.db"
PROJECT_DIR = "/Users/erik/Desktop/claude-multiagent-system"

# Cache configuration
CACHE_TTL = 5  # seconds
STATUS_CACHE_TTL = 10  # longer TTL for status endpoint
cache = {}
cache_timestamps = {}

# Rate limiting
request_counts = defaultdict(int)
request_timestamps = defaultdict(lambda: datetime.now())
RATE_LIMIT = 10  # requests per second per endpoint

def get_db_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def cache_key(endpoint: str, params: Dict = None) -> str:
    """Generate cache key for endpoint and params"""
    if params:
        param_str = json.dumps(sorted(params.items()))
        return f"{endpoint}:{param_str}"
    return endpoint

def get_cached_or_fetch(key: str, fetch_func, ttl: int = CACHE_TTL):
    """Get from cache or fetch from source"""
    now = datetime.now()

    # Check if cached and not expired
    if key in cache and key in cache_timestamps:
        if (now - cache_timestamps[key]).seconds < ttl:
            return cache[key]

    # Fetch fresh data
    data = fetch_func()
    cache[key] = data
    cache_timestamps[key] = now
    return data

def rate_limit_check(endpoint: str) -> bool:
    """Check if request should be rate limited"""
    now = datetime.now()
    key = f"{request.remote_addr}:{endpoint}"

    # Reset counter if time window passed
    if (now - request_timestamps[key]).seconds >= 1:
        request_counts[key] = 0
        request_timestamps[key] = now

    request_counts[key] += 1
    return request_counts[key] > RATE_LIMIT

@app.route('/api/mcp/status', methods=['GET'])
def get_mcp_status():
    """Get complete MCP system status with caching"""
    if rate_limit_check('status'):
        return jsonify({'error': 'Rate limit exceeded'}), 429

    def fetch_status():
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Get recent activities (limit to 10 for performance)
            cursor.execute("""
                SELECT id, agent, timestamp, activity, category, status
                FROM activities
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            activities = [dict(row) for row in cursor.fetchall()]

            # Get agent states
            cursor.execute("""
                SELECT agent, last_seen, status, current_task
                FROM agent_states
                WHERE datetime(last_seen) > datetime('now', '-5 minutes')
                ORDER BY last_seen DESC
            """)
            agent_states = [dict(row) for row in cursor.fetchall()]

            # Get statistics (cached separately)
            stats = get_statistics(cursor)

            conn.close()

            # Check TMUX sessions (expensive, cache longer)
            tmux_sessions = get_tmux_sessions_cached()

            return {
                'activities': activities,
                'agent_states': agent_states,
                'stats': stats,
                'tmux_sessions': tmux_sessions,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {'error': str(e)}

    result = get_cached_or_fetch('status', fetch_status, STATUS_CACHE_TTL)
    return jsonify(result)

def get_statistics(cursor) -> Dict:
    """Get system statistics"""
    stats_key = 'statistics'

    def fetch_stats():
        cursor.execute("SELECT COUNT(*) as count FROM activities WHERE datetime(timestamp) > datetime('now', '-1 hour')")
        recent_activities = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM components")
        total_components = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM agent_states WHERE status = 'active'")
        active_agents = cursor.fetchone()['count']

        return {
            'recent_activities': recent_activities,
            'total_components': total_components,
            'active_agents': active_agents
        }

    return get_cached_or_fetch(stats_key, lambda: fetch_stats(), 30)

def get_tmux_sessions_cached() -> List[str]:
    """Get TMUX sessions with caching"""
    def fetch_sessions():
        try:
            result = subprocess.run(['tmux', 'list-sessions'],
                                 capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                sessions = result.stdout.strip().split('\n')
                return [s.split(':')[0] for s in sessions if 'claude-' in s.lower()]
        except:
            pass
        return []

    return get_cached_or_fetch('tmux_sessions', fetch_sessions, 30)

@app.route('/api/mcp/activities', methods=['GET'])
def get_activities():
    """Get recent activities with pagination"""
    if rate_limit_check('activities'):
        return jsonify({'error': 'Rate limit exceeded'}), 429

    try:
        limit = min(request.args.get('limit', 20, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        agent = request.args.get('agent', None)

        cache_params = {'limit': limit, 'offset': offset, 'agent': agent}
        key = cache_key('activities', cache_params)

        def fetch_activities():
            conn = get_db_connection()
            cursor = conn.cursor()

            if agent:
                cursor.execute("""
                    SELECT * FROM activities
                    WHERE agent = ?
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                """, (agent, limit, offset))
            else:
                cursor.execute("""
                    SELECT * FROM activities
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))

            activities = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return activities

        activities = get_cached_or_fetch(key, fetch_activities, 3)
        return jsonify(activities)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/start-terminal', methods=['POST'])
def start_terminal_service():
    """Start ttyd terminal service for an agent"""
    try:
        data = request.json
        agent_name = data.get('agent_name')

        if not agent_name:
            return jsonify({'error': 'agent_name required'}), 400

        # Normalize agent name
        if agent_name.startswith('claude-'):
            agent_name = agent_name[7:]
        agent_name = agent_name.lower().replace(' ', '-').replace('_', '-')

        # Port mapping
        port_map = {
            'master': 8090,
            'supervisor': 8091,
            'backend-api': 8092,
            'database': 8093,
            'frontend-ui': 8094,
            'testing': 8095,
            'instagram': 8096,
            'queue-manager': 8097,
            'deployment': 8098
        }

        if agent_name not in port_map:
            return jsonify({'error': f'Unknown agent: {agent_name}'}), 400

        port = port_map[agent_name]
        session_name = f'claude-{agent_name}'

        # First ensure TMUX session exists
        result = subprocess.run(['tmux', 'has-session', '-t', session_name],
                              capture_output=True)
        if result.returncode != 0:
            # Create session if it doesn't exist
            subprocess.run(['tmux', 'new-session', '-d', '-s', session_name])
            # Send welcome message
            welcome_msgs = {
                'instagram': "echo '📱 Instagram Agent Ready'",
                'queue-manager': "echo '📬 Queue Manager Agent Ready'",
                'deployment': "echo '🚀 Deployment Agent Ready'",
                'master': "echo '🎖️ Master Agent Ready'",
                'supervisor': "echo '👨‍💼 Supervisor Agent Ready'",
                'backend-api': "echo '🔧 Backend API Agent Ready'",
                'database': "echo '🗄️ Database Agent Ready'",
                'frontend-ui': "echo '🎨 Frontend UI Agent Ready'",
                'testing': "echo '🧪 Testing Agent Ready'"
            }
            if agent_name in welcome_msgs:
                subprocess.run(['tmux', 'send-keys', '-t', session_name,
                              welcome_msgs[agent_name], 'Enter'])

        # Kill any existing ttyd on this port
        subprocess.run(['pkill', '-f', f'ttyd.*{port}'], capture_output=True)
        time.sleep(0.5)

        # Start ttyd
        subprocess.Popen([
            'ttyd', '-p', str(port), '--writable',
            '-t', f'titleFixed={agent_name.replace("-", " ").title()} Agent',
            'tmux', 'attach', '-t', session_name
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return jsonify({
            'success': True,
            'message': f'Terminal service started for {agent_name} on port {port}',
            'port': port
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/health', methods=['GET'])
def health_check():
    """Lightweight health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/mcp/ws-config', methods=['GET'])
def get_websocket_config():
    """Get WebSocket configuration for real-time updates"""
    return jsonify({
        'ws_url': 'ws://localhost:8091/ws',
        'polling_fallback': True,
        'polling_interval': 10000,  # 10 seconds
        'reconnect_interval': 5000
    })

# Background cache cleanup
def cleanup_cache():
    """Clean expired cache entries"""
    while True:
        time.sleep(60)  # Run every minute
        now = datetime.now()
        expired_keys = [
            key for key, timestamp in cache_timestamps.items()
            if (now - timestamp).seconds > 300  # 5 minutes
        ]
        for key in expired_keys:
            del cache[key]
            del cache_timestamps[key]

# Start cache cleanup thread
cleanup_thread = threading.Thread(target=cleanup_cache, daemon=True)
cleanup_thread.start()

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)

    # Create database tables if not exist
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS activities
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      agent TEXT NOT NULL,
                      timestamp TEXT NOT NULL,
                      activity TEXT NOT NULL,
                      category TEXT,
                      status TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS components
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT NOT NULL,
                      type TEXT,
                      owner TEXT,
                      created_at TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS agent_states
                     (agent TEXT PRIMARY KEY,
                      last_seen TEXT,
                      status TEXT,
                      current_task TEXT)''')

    # Create indexes for performance
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_activities_timestamp
                     ON activities(timestamp DESC)''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_activities_agent
                     ON activities(agent, timestamp DESC)''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_agent_states_status
                     ON agent_states(status)''')

    conn.commit()
    conn.close()

    print("🚀 MCP API Server Optimized starting on http://localhost:8099")
    print("📊 Features: Caching, Rate Limiting, Optimized Queries")

    app.run(host='0.0.0.0', port=8099, debug=False)