#!/usr/bin/env python3
"""
Authentication API with JWT token generation
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import jwt
import datetime
import uuid

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'

# In-memory user store (in production use a database)
users = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'user': {'password': 'user123', 'role': 'user'},
    'backend-api': {'password': 'agent123', 'role': 'agent'},
    'frontend-ui': {'password': 'agent123', 'role': 'agent'},
    'database': {'password': 'agent123', 'role': 'agent'},
    'testing': {'password': 'agent123', 'role': 'agent'},
    'supervisor': {'password': 'supervisor123', 'role': 'supervisor'}
}

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login endpoint with JWT token generation"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    # Verify credentials
    if username not in users or users[username]['password'] != password:
        return jsonify({'error': 'Invalid credentials'}), 401

    # Generate JWT token
    token_payload = {
        'user_id': str(uuid.uuid4()),
        'username': username,
        'role': users[username]['role'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        'iat': datetime.datetime.utcnow()
    }

    token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({
        'success': True,
        'token': token,
        'username': username,
        'role': users[username]['role'],
        'expires_in': 86400  # 24 hours in seconds
    }), 200

@app.route('/api/auth/verify', methods=['GET'])
def verify():
    """Verify JWT token"""
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return jsonify({'error': 'No authorization header'}), 401

    try:
        # Extract token from "Bearer <token>" format
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header

        # Decode and verify token
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])

        return jsonify({
            'valid': True,
            'username': payload.get('username'),
            'role': payload.get('role'),
            'user_id': payload.get('user_id')
        }), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout endpoint (in production, invalidate token in database)"""
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200

if __name__ == '__main__':
    print("Starting Authentication API on http://localhost:5002")
    print("Endpoints:")
    print("  POST /api/auth/login - Login with username/password")
    print("  GET /api/auth/verify - Verify JWT token")
    print("  POST /api/auth/logout - Logout")
    print("\nTest credentials:")
    print("  admin/admin123 (admin role)")
    print("  user/user123 (user role)")
    print("  backend-api/agent123 (agent role)")
    app.run(host='0.0.0.0', port=5002, debug=True)