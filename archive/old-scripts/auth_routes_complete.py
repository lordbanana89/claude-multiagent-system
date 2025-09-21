#!/usr/bin/env python3
"""
Complete Authentication Routes Implementation
Full auth system with register, login, refresh, roles, and permissions
"""

from flask import Flask, jsonify, request, g
from flask_cors import CORS
import jwt
import bcrypt
import sqlite3
import uuid
from datetime import datetime, timedelta
from functools import wraps
import re

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['TOKEN_EXPIRY'] = 3600  # 1 hour
app.config['REFRESH_TOKEN_EXPIRY'] = 86400 * 7  # 7 days

# Database setup
def init_db():
    """Initialize authentication database"""
    conn = sqlite3.connect('auth.db', check_same_thread=False)
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            metadata TEXT
        )
    ''')

    # Sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            refresh_token TEXT UNIQUE,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Permissions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS permissions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            resource TEXT NOT NULL,
            action TEXT NOT NULL,
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            granted_by TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Audit log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT
        )
    ''')

    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Helper functions
def get_db():
    """Get database connection"""
    if 'db' not in g:
        g.db = sqlite3.connect('auth.db', check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hash):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hash.encode('utf-8'))

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain number"
    return True, "Valid"

def generate_tokens(user_id):
    """Generate access and refresh tokens"""
    now = datetime.utcnow()

    # Access token
    access_payload = {
        'user_id': user_id,
        'type': 'access',
        'iat': now,
        'exp': now + timedelta(seconds=app.config['TOKEN_EXPIRY'])
    }
    access_token = jwt.encode(access_payload, app.config['SECRET_KEY'], algorithm='HS256')

    # Refresh token
    refresh_payload = {
        'user_id': user_id,
        'type': 'refresh',
        'iat': now,
        'exp': now + timedelta(seconds=app.config['REFRESH_TOKEN_EXPIRY'])
    }
    refresh_token = jwt.encode(refresh_payload, app.config['SECRET_KEY'], algorithm='HS256')

    return access_token, refresh_token

def log_audit(user_id, action, details=None, ip=None):
    """Log audit event"""
    db = get_db()
    db.execute(
        'INSERT INTO audit_log (user_id, action, details, ip_address) VALUES (?, ?, ?, ?)',
        (user_id, action, details, ip)
    )
    db.commit()

# Authentication decorator
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'error': 'No token provided'}), 401

        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]

            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])

            if payload.get('type') != 'access':
                return jsonify({'error': 'Invalid token type'}), 401

            # Check if session exists
            db = get_db()
            session = db.execute(
                'SELECT * FROM sessions WHERE token = ? AND expires_at > ?',
                (token, datetime.utcnow())
            ).fetchone()

            if not session:
                return jsonify({'error': 'Invalid or expired session'}), 401

            # Get user
            user = db.execute(
                'SELECT * FROM users WHERE id = ? AND is_active = 1',
                (payload['user_id'],)
            ).fetchone()

            if not user:
                return jsonify({'error': 'User not found or inactive'}), 401

            g.current_user = dict(user)

        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(*args, **kwargs)

    return decorated

def role_required(role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        @auth_required
        def decorated(*args, **kwargs):
            if g.current_user.get('role') != role:
                return jsonify({'error': f'Role {role} required'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

# ===== AUTHENTICATION ROUTES =====

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.json

    # Validate input
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400

    username = data['username']
    password = data['password']
    email = data.get('email')

    # Validate email if provided
    if email and not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400

    # Validate password strength
    valid, message = validate_password(password)
    if not valid:
        return jsonify({'error': message}), 400

    # Check if user exists
    db = get_db()
    existing = db.execute(
        'SELECT id FROM users WHERE username = ? OR (email = ? AND email IS NOT NULL)',
        (username, email)
    ).fetchone()

    if existing:
        return jsonify({'error': 'User already exists'}), 409

    # Create user
    user_id = str(uuid.uuid4())
    password_hash = hash_password(password)

    db.execute(
        'INSERT INTO users (id, username, email, password_hash, role) VALUES (?, ?, ?, ?, ?)',
        (user_id, username, email, password_hash, data.get('role', 'user'))
    )
    db.commit()

    log_audit(user_id, 'register', f'User {username} registered', request.remote_addr)

    return jsonify({
        'success': True,
        'user_id': user_id,
        'username': username,
        'message': 'User registered successfully'
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    data = request.json

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400

    username = data['username']
    password = data['password']

    # Get user
    db = get_db()
    user = db.execute(
        'SELECT * FROM users WHERE (username = ? OR email = ?) AND is_active = 1',
        (username, username)
    ).fetchone()

    if not user or not verify_password(password, user['password_hash']):
        log_audit(None, 'login_failed', f'Failed login for {username}', request.remote_addr)
        return jsonify({'error': 'Invalid credentials'}), 401

    # Generate tokens
    access_token, refresh_token = generate_tokens(user['id'])

    # Create session
    session_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(seconds=app.config['TOKEN_EXPIRY'])

    db.execute(
        '''INSERT INTO sessions (id, user_id, token, refresh_token, expires_at, ip_address, user_agent)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (session_id, user['id'], access_token, refresh_token, expires_at,
         request.remote_addr, request.headers.get('User-Agent'))
    )

    # Update last login
    db.execute('UPDATE users SET last_login = ? WHERE id = ?', (datetime.utcnow(), user['id']))
    db.commit()

    log_audit(user['id'], 'login', 'Successful login', request.remote_addr)

    return jsonify({
        'success': True,
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': app.config['TOKEN_EXPIRY'],
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role']
        }
    }), 200

@app.route('/api/auth/refresh', methods=['POST'])
def refresh():
    """Refresh access token"""
    data = request.json

    if not data or not data.get('refresh_token'):
        return jsonify({'error': 'Refresh token required'}), 400

    refresh_token = data['refresh_token']

    try:
        payload = jwt.decode(refresh_token, app.config['SECRET_KEY'], algorithms=['HS256'])

        if payload.get('type') != 'refresh':
            return jsonify({'error': 'Invalid token type'}), 401

        # Check session
        db = get_db()
        session = db.execute(
            'SELECT * FROM sessions WHERE refresh_token = ?',
            (refresh_token,)
        ).fetchone()

        if not session:
            return jsonify({'error': 'Invalid refresh token'}), 401

        # Generate new access token
        access_token, _ = generate_tokens(payload['user_id'])
        expires_at = datetime.utcnow() + timedelta(seconds=app.config['TOKEN_EXPIRY'])

        # Update session
        db.execute(
            'UPDATE sessions SET token = ?, expires_at = ? WHERE id = ?',
            (access_token, expires_at, session['id'])
        )
        db.commit()

        log_audit(payload['user_id'], 'token_refresh', None, request.remote_addr)

        return jsonify({
            'success': True,
            'access_token': access_token,
            'expires_in': app.config['TOKEN_EXPIRY']
        }), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Refresh token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid refresh token'}), 401

@app.route('/api/auth/logout', methods=['POST'])
@auth_required
def logout():
    """Logout user"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')

    # Delete session
    db = get_db()
    db.execute('DELETE FROM sessions WHERE token = ?', (token,))
    db.commit()

    log_audit(g.current_user['id'], 'logout', None, request.remote_addr)

    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200

@app.route('/api/auth/verify', methods=['GET'])
@auth_required
def verify():
    """Verify current token"""
    return jsonify({
        'valid': True,
        'user': {
            'id': g.current_user['id'],
            'username': g.current_user['username'],
            'role': g.current_user['role']
        }
    }), 200

@app.route('/api/auth/change-password', methods=['POST'])
@auth_required
def change_password():
    """Change user password"""
    data = request.json

    if not data or not data.get('current_password') or not data.get('new_password'):
        return jsonify({'error': 'Current and new password required'}), 400

    # Verify current password
    db = get_db()
    user = db.execute(
        'SELECT password_hash FROM users WHERE id = ?',
        (g.current_user['id'],)
    ).fetchone()

    if not verify_password(data['current_password'], user['password_hash']):
        return jsonify({'error': 'Current password incorrect'}), 401

    # Validate new password
    valid, message = validate_password(data['new_password'])
    if not valid:
        return jsonify({'error': message}), 400

    # Update password
    new_hash = hash_password(data['new_password'])
    db.execute(
        'UPDATE users SET password_hash = ? WHERE id = ?',
        (new_hash, g.current_user['id'])
    )

    # Invalidate all sessions
    db.execute('DELETE FROM sessions WHERE user_id = ?', (g.current_user['id'],))
    db.commit()

    log_audit(g.current_user['id'], 'password_change', None, request.remote_addr)

    return jsonify({
        'success': True,
        'message': 'Password changed successfully. Please login again.'
    }), 200

@app.route('/api/auth/profile', methods=['GET'])
@auth_required
def get_profile():
    """Get user profile"""
    return jsonify({
        'user': {
            'id': g.current_user['id'],
            'username': g.current_user['username'],
            'email': g.current_user['email'],
            'role': g.current_user['role'],
            'created_at': g.current_user['created_at'],
            'last_login': g.current_user['last_login']
        }
    }), 200

@app.route('/api/auth/sessions', methods=['GET'])
@auth_required
def get_sessions():
    """Get user's active sessions"""
    db = get_db()
    sessions = db.execute(
        'SELECT id, created_at, expires_at, ip_address, user_agent FROM sessions WHERE user_id = ?',
        (g.current_user['id'],)
    ).fetchall()

    return jsonify({
        'sessions': [dict(s) for s in sessions]
    }), 200

@app.route('/api/auth/sessions/<session_id>', methods=['DELETE'])
@auth_required
def revoke_session(session_id):
    """Revoke specific session"""
    db = get_db()
    result = db.execute(
        'DELETE FROM sessions WHERE id = ? AND user_id = ?',
        (session_id, g.current_user['id'])
    )
    db.commit()

    if result.rowcount == 0:
        return jsonify({'error': 'Session not found'}), 404

    log_audit(g.current_user['id'], 'session_revoked', f'Session {session_id} revoked', request.remote_addr)

    return jsonify({'success': True, 'message': 'Session revoked'}), 200

# ===== ADMIN ROUTES =====

@app.route('/api/auth/admin/users', methods=['GET'])
@role_required('admin')
def admin_get_users():
    """Get all users (admin only)"""
    db = get_db()
    users = db.execute(
        'SELECT id, username, email, role, created_at, last_login, is_active FROM users'
    ).fetchall()

    return jsonify({
        'users': [dict(u) for u in users]
    }), 200

@app.route('/api/auth/admin/users/<user_id>/activate', methods=['POST'])
@role_required('admin')
def admin_activate_user(user_id):
    """Activate/deactivate user (admin only)"""
    data = request.json
    active = data.get('active', True)

    db = get_db()
    db.execute('UPDATE users SET is_active = ? WHERE id = ?', (active, user_id))
    db.commit()

    log_audit(g.current_user['id'], 'admin_user_activate',
              f'User {user_id} {"activated" if active else "deactivated"}',
              request.remote_addr)

    return jsonify({'success': True}), 200

@app.route('/api/auth/admin/users/<user_id>/role', methods=['PUT'])
@role_required('admin')
def admin_change_role(user_id):
    """Change user role (admin only)"""
    data = request.json

    if not data or not data.get('role'):
        return jsonify({'error': 'Role required'}), 400

    db = get_db()
    db.execute('UPDATE users SET role = ? WHERE id = ?', (data['role'], user_id))
    db.commit()

    log_audit(g.current_user['id'], 'admin_role_change',
              f'User {user_id} role changed to {data["role"]}',
              request.remote_addr)

    return jsonify({'success': True}), 200

# Health check
@app.route('/api/auth/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'auth_routes'}), 200

# Error handlers
@app.errorhandler(401)
def unauthorized(e):
    return jsonify({'error': 'Unauthorized'}), 401

@app.errorhandler(403)
def forbidden(e):
    return jsonify({'error': 'Forbidden'}), 403

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

@app.teardown_appcontext
def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    print("Starting Complete Auth Routes on http://localhost:5004")
    print("\nAuth Endpoints:")
    print("  POST /api/auth/register         - Register new user")
    print("  POST /api/auth/login            - Login")
    print("  POST /api/auth/refresh          - Refresh token")
    print("  POST /api/auth/logout           - Logout")
    print("  GET  /api/auth/verify           - Verify token")
    print("  POST /api/auth/change-password  - Change password")
    print("  GET  /api/auth/profile          - Get profile")
    print("  GET  /api/auth/sessions         - Get sessions")
    print("  DELETE /api/auth/sessions/:id   - Revoke session")
    print("\nAdmin Endpoints:")
    print("  GET  /api/auth/admin/users      - List all users")
    print("  POST /api/auth/admin/users/:id/activate - Activate/deactivate user")
    print("  PUT  /api/auth/admin/users/:id/role     - Change user role")

    app.run(host='0.0.0.0', port=5004, debug=True)