#!/usr/bin/env python3
"""
Routes API - Complete routing system for the multiagent application
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import jwt
from functools import wraps
import os

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'error': 'Token missing'}), 401

        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]

            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            request.user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(*args, **kwargs)

    return decorated

# ===== PUBLIC ROUTES =====

@app.route('/', methods=['GET'])
def home():
    """Home route - API information"""
    return jsonify({
        'name': 'Claude Multiagent System API',
        'version': '1.0.0',
        'endpoints': {
            'auth': '/api/auth/*',
            'agents': '/api/agents/*',
            'tasks': '/api/tasks/*',
            'messages': '/api/messages/*',
            'system': '/api/system/*',
            'dashboard': '/dashboard'
        }
    })

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok', 'service': 'routes_api'})

# ===== AUTHENTICATION ROUTES =====

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login endpoint - proxy to auth service"""
    # This would proxy to http://localhost:5002/api/auth/login
    import requests
    try:
        response = requests.post('http://localhost:5002/api/auth/login', json=request.json)
        return response.json(), response.status_code
    except:
        return jsonify({'error': 'Auth service unavailable'}), 503

@app.route('/api/auth/verify', methods=['GET'])
@token_required
def verify():
    """Verify token"""
    return jsonify({
        'valid': True,
        'user': request.user
    })

@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout():
    """Logout endpoint"""
    # In production, invalidate token in database
    return jsonify({'success': True, 'message': 'Logged out'})

# ===== AGENT ROUTES =====

@app.route('/api/agents', methods=['GET'])
@token_required
def get_agents():
    """Get all agents status"""
    agents = [
        {'id': 'backend-api', 'status': 'active', 'role': 'backend'},
        {'id': 'frontend-ui', 'status': 'active', 'role': 'frontend'},
        {'id': 'database', 'status': 'idle', 'role': 'database'},
        {'id': 'testing', 'status': 'active', 'role': 'testing'},
        {'id': 'supervisor', 'status': 'active', 'role': 'supervisor'},
    ]
    return jsonify({'agents': agents})

@app.route('/api/agents/<agent_id>', methods=['GET'])
@token_required
def get_agent(agent_id):
    """Get specific agent details"""
    # Mock data - would connect to real database
    agent_data = {
        'id': agent_id,
        'status': 'active',
        'last_heartbeat': '2025-09-18T22:30:00Z',
        'current_task': None,
        'metrics': {
            'tasks_completed': 15,
            'uptime': '2h 15m',
            'cpu_usage': '12%',
            'memory_usage': '256MB'
        }
    }
    return jsonify(agent_data)

@app.route('/api/agents/<agent_id>/heartbeat', methods=['POST'])
@token_required
def agent_heartbeat(agent_id):
    """Agent heartbeat endpoint"""
    # Forward to MCP server
    import requests
    try:
        response = requests.post('http://localhost:9999/jsonrpc', json={
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'params': {
                'name': 'heartbeat',
                'arguments': {'agent': agent_id}
            },
            'id': 1
        })
        return response.json(), response.status_code
    except:
        return jsonify({'error': 'MCP service unavailable'}), 503

# ===== TASK ROUTES =====

@app.route('/api/tasks', methods=['GET'])
@token_required
def get_tasks():
    """Get all tasks"""
    tasks = [
        {
            'id': 'task-001',
            'title': 'Implement authentication',
            'status': 'completed',
            'assigned_to': 'backend-api',
            'created_at': '2025-09-18T20:00:00Z'
        },
        {
            'id': 'task-002',
            'title': 'Create integration tests',
            'status': 'in_progress',
            'assigned_to': 'testing',
            'created_at': '2025-09-18T21:00:00Z'
        }
    ]
    return jsonify({'tasks': tasks})

@app.route('/api/tasks', methods=['POST'])
@token_required
def create_task():
    """Create new task"""
    data = request.json

    if not data or 'title' not in data:
        return jsonify({'error': 'Title required'}), 400

    # Create task logic here
    new_task = {
        'id': f'task-{os.urandom(4).hex()}',
        'title': data['title'],
        'description': data.get('description', ''),
        'assigned_to': data.get('assigned_to'),
        'status': 'pending',
        'created_by': request.user.get('username')
    }

    return jsonify(new_task), 201

@app.route('/api/tasks/<task_id>', methods=['GET'])
@token_required
def get_task(task_id):
    """Get specific task"""
    # Mock task data
    task = {
        'id': task_id,
        'title': 'Sample task',
        'description': 'Task description',
        'status': 'in_progress',
        'assigned_to': 'backend-api',
        'created_at': '2025-09-18T20:00:00Z',
        'updated_at': '2025-09-18T21:00:00Z'
    }
    return jsonify(task)

@app.route('/api/tasks/<task_id>', methods=['PUT'])
@token_required
def update_task(task_id):
    """Update task"""
    data = request.json

    # Update task logic here
    updated_task = {
        'id': task_id,
        'status': data.get('status', 'in_progress'),
        'updated_at': '2025-09-18T22:00:00Z'
    }

    return jsonify(updated_task)

# ===== MESSAGE ROUTES =====

@app.route('/api/messages', methods=['GET'])
@token_required
def get_messages():
    """Get messages for current user"""
    # Would query database for user's messages
    messages = [
        {
            'id': 'msg-001',
            'from': 'supervisor',
            'to': request.user.get('username'),
            'subject': 'Task assigned',
            'content': 'Please implement the auth endpoint',
            'timestamp': '2025-09-18T20:00:00Z'
        }
    ]
    return jsonify({'messages': messages})

@app.route('/api/messages', methods=['POST'])
@token_required
def send_message():
    """Send message"""
    data = request.json

    if not data or 'to' not in data or 'content' not in data:
        return jsonify({'error': 'Recipient and content required'}), 400

    # Send message logic here
    new_message = {
        'id': f'msg-{os.urandom(4).hex()}',
        'from': request.user.get('username'),
        'to': data['to'],
        'subject': data.get('subject', ''),
        'content': data['content'],
        'timestamp': '2025-09-18T22:00:00Z'
    }

    return jsonify(new_message), 201

# ===== SYSTEM ROUTES =====

@app.route('/api/system/status', methods=['GET'])
@token_required
def system_status():
    """Get system status"""
    return jsonify({
        'status': 'operational',
        'services': {
            'auth': 'online',
            'mcp': 'online',
            'database': 'online',
            'messaging': 'online'
        },
        'uptime': '2h 30m',
        'version': '1.0.0'
    })

@app.route('/api/system/metrics', methods=['GET'])
@token_required
def system_metrics():
    """Get system metrics"""
    return jsonify({
        'cpu_usage': '25%',
        'memory_usage': '1.2GB',
        'disk_usage': '15GB',
        'active_agents': 5,
        'total_tasks': 42,
        'messages_sent': 150
    })

# ===== DASHBOARD ROUTE =====

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Serve dashboard HTML"""
    # Would serve the dashboard HTML file
    return jsonify({
        'message': 'Dashboard would be served here',
        'url': '/Users/erik/Desktop/claude-multiagent-system/test_integration.html'
    })

# ===== STATIC FILES =====

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    return send_from_directory(static_dir, filename)

# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized'}), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Forbidden'}), 403

if __name__ == '__main__':
    print("Starting Routes API on http://localhost:5003")
    print("\nAvailable routes:")
    print("  GET  /                     - API info")
    print("  GET  /api/health           - Health check")
    print("  POST /api/auth/login       - Login")
    print("  GET  /api/auth/verify      - Verify token")
    print("  GET  /api/agents           - List agents")
    print("  GET  /api/agents/:id       - Agent details")
    print("  POST /api/agents/:id/heartbeat - Agent heartbeat")
    print("  GET  /api/tasks            - List tasks")
    print("  POST /api/tasks            - Create task")
    print("  GET  /api/tasks/:id        - Task details")
    print("  PUT  /api/tasks/:id        - Update task")
    print("  GET  /api/messages         - List messages")
    print("  POST /api/messages         - Send message")
    print("  GET  /api/system/status    - System status")
    print("  GET  /api/system/metrics   - System metrics")
    print("  GET  /dashboard            - Dashboard")

    app.run(host='0.0.0.0', port=5003, debug=True)