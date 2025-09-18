"""
REST API with Authentication for Inbox System
Complete authentication endpoints with JWT and API key support
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from functools import wraps
import uuid

from shared_state.models import AgentMessage, MessageType, MessagePriority, MessageStatus
from .storage import InboxStorage, InboxManager
from .routing import MessageRouter
from .auth import (
    AuthenticationManager,
    Permission,
    Role,
    create_default_auth_manager,
    require_permission,
    require_role
)


class AuthenticatedInboxAPI:
    """REST API with full authentication support"""

    def __init__(self, storage: InboxStorage, router: MessageRouter, secret_key: str = None):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = secret_key or str(uuid.uuid4())

        CORS(self.app)

        self.storage = storage
        self.manager = InboxManager(storage)
        self.router = router
        self.auth_manager = create_default_auth_manager(self.app.config['SECRET_KEY'])

        self._setup_middleware()
        self._setup_auth_routes()
        self._setup_message_routes()
        self._setup_admin_routes()
        self._setup_error_handlers()

    def _setup_middleware(self):
        """Setup authentication middleware"""

        @self.app.before_request
        def authenticate_request():
            """Authenticate each request"""
            # Skip authentication for certain endpoints
            exempt_endpoints = ['/health', '/auth/login', '/auth/register']
            if request.path in exempt_endpoints:
                return

            # Check for API key in header
            api_key = request.headers.get('X-API-Key')
            if api_key:
                agent = self.auth_manager.authenticate_with_api_key(api_key)
                if agent:
                    g.agent_credentials = agent
                    return

            # Check for JWT token in Authorization header
            auth_header = request.headers.get('Authorization')
            if auth_header:
                try:
                    token = auth_header.split(' ')[1]  # Bearer <token>
                    agent = self.auth_manager.verify_jwt_token(token)
                    if agent:
                        g.agent_credentials = agent
                        return
                except (IndexError, ValueError):
                    pass

            # No valid authentication found
            if not request.path.startswith('/health'):
                return jsonify({'error': 'Authentication required'}), 401

    def _setup_auth_routes(self):
        """Setup authentication endpoints"""

        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0'
            })

        @self.app.route('/auth/register', methods=['POST'])
        def register_agent():
            """Register a new agent"""
            data = request.get_json()

            if not data:
                return jsonify({'error': 'Request body required'}), 400

            required_fields = ['agent_id', 'agent_name']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'{field} is required'}), 400

            try:
                # Get role from request or default to AGENT
                role_str = data.get('role', 'agent')
                role = Role[role_str.upper()]

                # Register agent
                agent = self.auth_manager.register_agent(
                    agent_id=data['agent_id'],
                    agent_name=data['agent_name'],
                    role=role
                )

                # Generate API key
                api_key = self.auth_manager.generate_api_key(agent.agent_id)

                return jsonify({
                    'success': True,
                    'agent_id': agent.agent_id,
                    'agent_name': agent.agent_name,
                    'role': agent.role.value,
                    'api_key': api_key,
                    'permissions': [p.value for p in agent.permissions]
                }), 201

            except ValueError as e:
                return jsonify({'error': str(e)}), 400
            except Exception as e:
                return jsonify({'error': 'Registration failed', 'details': str(e)}), 500

        @self.app.route('/auth/login', methods=['POST'])
        def login():
            """Login with API key and get JWT token"""
            data = request.get_json()

            if not data or 'api_key' not in data:
                return jsonify({'error': 'api_key required'}), 400

            # Authenticate with API key
            agent = self.auth_manager.authenticate_with_api_key(data['api_key'])
            if not agent:
                return jsonify({'error': 'Invalid API key'}), 401

            # Generate JWT token
            try:
                token = self.auth_manager.generate_jwt_token(
                    agent.agent_id,
                    expires_in=data.get('expires_in', 3600)
                )

                return jsonify({
                    'success': True,
                    'token': token,
                    'agent_id': agent.agent_id,
                    'agent_name': agent.agent_name,
                    'role': agent.role.value,
                    'permissions': [p.value for p in agent.permissions],
                    'expires_in': data.get('expires_in', 3600)
                })

            except Exception as e:
                return jsonify({'error': 'Login failed', 'details': str(e)}), 500

        @self.app.route('/auth/logout', methods=['POST'])
        def logout():
            """Logout and revoke current token"""
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({'error': 'No token provided'}), 400

            try:
                token = auth_header.split(' ')[1]
                self.auth_manager.revoke_token(token)
                return jsonify({'success': True, 'message': 'Token revoked'})
            except (IndexError, ValueError):
                return jsonify({'error': 'Invalid token format'}), 400

        @self.app.route('/auth/refresh', methods=['POST'])
        def refresh_token():
            """Refresh JWT token"""
            if not hasattr(g, 'agent_credentials'):
                return jsonify({'error': 'Authentication required'}), 401

            try:
                # Revoke old token
                auth_header = request.headers.get('Authorization')
                if auth_header:
                    old_token = auth_header.split(' ')[1]
                    self.auth_manager.revoke_token(old_token)

                # Generate new token
                new_token = self.auth_manager.generate_jwt_token(
                    g.agent_credentials.agent_id,
                    expires_in=3600
                )

                return jsonify({
                    'success': True,
                    'token': new_token,
                    'expires_in': 3600
                })

            except Exception as e:
                return jsonify({'error': 'Token refresh failed', 'details': str(e)}), 500

        @self.app.route('/auth/me', methods=['GET'])
        def get_current_agent():
            """Get current agent information"""
            if not hasattr(g, 'agent_credentials'):
                return jsonify({'error': 'Authentication required'}), 401

            return jsonify(g.agent_credentials.to_dict())

    def _setup_message_routes(self):
        """Setup message-related endpoints"""

        @self.app.route('/messages/send', methods=['POST'])
        def send_message():
            """Send a message"""
            if not hasattr(g, 'agent_credentials'):
                return jsonify({'error': 'Authentication required'}), 401

            if not g.agent_credentials.has_permission(Permission.SEND_MESSAGES):
                return jsonify({'error': 'Permission denied'}), 403

            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body required'}), 400

            try:
                message = self.manager.send_message(
                    sender_id=g.agent_credentials.agent_id,
                    recipient_id=data.get('recipient_id'),
                    content=data.get('content', ''),
                    subject=data.get('subject'),
                    priority=MessagePriority(data.get('priority', 2)),
                    message_type=MessageType(data.get('message_type', 'direct'))
                )

                return jsonify({
                    'success': True,
                    'message_id': message.message_id,
                    'timestamp': message.timestamp.isoformat()
                }), 201

            except Exception as e:
                return jsonify({'error': 'Failed to send message', 'details': str(e)}), 500

        @self.app.route('/messages/broadcast', methods=['POST'])
        def broadcast_message():
            """Broadcast a message to all agents"""
            if not hasattr(g, 'agent_credentials'):
                return jsonify({'error': 'Authentication required'}), 401

            if not g.agent_credentials.has_permission(Permission.BROADCAST_MESSAGES):
                return jsonify({'error': 'Permission denied'}), 403

            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body required'}), 400

            try:
                message = self.manager.broadcast_message(
                    sender_id=g.agent_credentials.agent_id,
                    content=data.get('content', ''),
                    subject=data.get('subject'),
                    priority=MessagePriority(data.get('priority', 2))
                )

                return jsonify({
                    'success': True,
                    'message_id': message.message_id,
                    'timestamp': message.timestamp.isoformat()
                }), 201

            except Exception as e:
                return jsonify({'error': 'Failed to broadcast message', 'details': str(e)}), 500

        @self.app.route('/messages/inbox', methods=['GET'])
        def get_inbox():
            """Get agent's inbox messages"""
            if not hasattr(g, 'agent_credentials'):
                return jsonify({'error': 'Authentication required'}), 401

            if not g.agent_credentials.has_permission(Permission.READ_OWN_MESSAGES):
                return jsonify({'error': 'Permission denied'}), 403

            try:
                unread_only = request.args.get('unread_only', 'false').lower() == 'true'
                limit = min(int(request.args.get('limit', 100)), 1000)
                offset = int(request.args.get('offset', 0))

                messages = self.manager.get_messages(
                    agent_id=g.agent_credentials.agent_id,
                    unread_only=unread_only
                )[offset:offset+limit]

                return jsonify({
                    'success': True,
                    'messages': [self._message_to_dict(msg) for msg in messages],
                    'count': len(messages),
                    'offset': offset,
                    'limit': limit
                })

            except Exception as e:
                return jsonify({'error': 'Failed to retrieve messages', 'details': str(e)}), 500

        @self.app.route('/messages/<message_id>', methods=['GET'])
        def get_message(message_id):
            """Get a specific message"""
            if not hasattr(g, 'agent_credentials'):
                return jsonify({'error': 'Authentication required'}), 401

            try:
                message = self.storage.get_message(message_id)
                if not message:
                    return jsonify({'error': 'Message not found'}), 404

                # Check if agent can access this message
                if not g.agent_credentials.can_access_message(message):
                    return jsonify({'error': 'Access denied'}), 403

                return jsonify(self._message_to_dict(message))

            except Exception as e:
                return jsonify({'error': 'Failed to retrieve message', 'details': str(e)}), 500

        @self.app.route('/messages/<message_id>/read', methods=['POST'])
        def mark_as_read(message_id):
            """Mark message as read"""
            if not hasattr(g, 'agent_credentials'):
                return jsonify({'error': 'Authentication required'}), 401

            try:
                success = self.manager.mark_as_read(
                    agent_id=g.agent_credentials.agent_id,
                    message_id=message_id
                )

                if success:
                    return jsonify({'success': True})
                else:
                    return jsonify({'error': 'Failed to mark message as read'}), 400

            except Exception as e:
                return jsonify({'error': 'Operation failed', 'details': str(e)}), 500

        @self.app.route('/messages/<message_id>', methods=['DELETE'])
        def delete_message(message_id):
            """Delete a message"""
            if not hasattr(g, 'agent_credentials'):
                return jsonify({'error': 'Authentication required'}), 401

            if not g.agent_credentials.has_permission(Permission.DELETE_MESSAGES):
                return jsonify({'error': 'Permission denied'}), 403

            try:
                message = self.storage.get_message(message_id)
                if not message:
                    return jsonify({'error': 'Message not found'}), 404

                # Only allow deletion of own messages unless admin
                if not g.agent_credentials.has_permission(Permission.READ_ALL_MESSAGES):
                    if message.sender_id != g.agent_credentials.agent_id:
                        return jsonify({'error': 'Can only delete own messages'}), 403

                success = self.storage.delete_message(message_id)

                if success:
                    return jsonify({'success': True})
                else:
                    return jsonify({'error': 'Failed to delete message'}), 400

            except Exception as e:
                return jsonify({'error': 'Delete failed', 'details': str(e)}), 500

    def _setup_admin_routes(self):
        """Setup admin-only endpoints"""

        @self.app.route('/admin/agents', methods=['GET'])
        def list_agents():
            """List all registered agents"""
            if not hasattr(g, 'agent_credentials'):
                return jsonify({'error': 'Authentication required'}), 401

            if g.agent_credentials.role not in [Role.ADMIN, Role.SYSTEM]:
                return jsonify({'error': 'Admin access required'}), 403

            active_only = request.args.get('active_only', 'true').lower() == 'true'
            agents = self.auth_manager.list_agents(active_only=active_only)

            return jsonify({
                'success': True,
                'agents': [agent.to_dict() for agent in agents],
                'count': len(agents)
            })

        @self.app.route('/admin/agents/<agent_id>', methods=['PUT'])
        def update_agent(agent_id):
            """Update agent permissions or status"""
            if not hasattr(g, 'agent_credentials'):
                return jsonify({'error': 'Authentication required'}), 401

            if g.agent_credentials.role not in [Role.ADMIN, Role.SYSTEM]:
                return jsonify({'error': 'Admin access required'}), 403

            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body required'}), 400

            agent = self.auth_manager.get_agent(agent_id)
            if not agent:
                return jsonify({'error': 'Agent not found'}), 404

            try:
                # Update permissions if provided
                if 'permissions' in data:
                    permissions = set()
                    for perm_str in data['permissions']:
                        permissions.add(Permission[perm_str.upper()])
                    self.auth_manager.update_permissions(agent_id, permissions)

                # Update active status if provided
                if 'active' in data:
                    if data['active']:
                        agent.active = True
                    else:
                        self.auth_manager.deactivate_agent(agent_id)

                return jsonify({
                    'success': True,
                    'agent': self.auth_manager.get_agent(agent_id).to_dict()
                })

            except Exception as e:
                return jsonify({'error': 'Update failed', 'details': str(e)}), 500

        @self.app.route('/admin/agents/<agent_id>', methods=['DELETE'])
        def deactivate_agent(agent_id):
            """Deactivate an agent"""
            if not hasattr(g, 'agent_credentials'):
                return jsonify({'error': 'Authentication required'}), 401

            if g.agent_credentials.role not in [Role.ADMIN, Role.SYSTEM]:
                return jsonify({'error': 'Admin access required'}), 403

            success = self.auth_manager.deactivate_agent(agent_id)

            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Agent not found'}), 404

        @self.app.route('/admin/tokens/cleanup', methods=['POST'])
        def cleanup_tokens():
            """Cleanup expired tokens"""
            if not hasattr(g, 'agent_credentials'):
                return jsonify({'error': 'Authentication required'}), 401

            if not g.agent_credentials.has_permission(Permission.ADMIN_CLEANUP):
                return jsonify({'error': 'Permission denied'}), 403

            removed_count = self.auth_manager.cleanup_expired_tokens()

            return jsonify({
                'success': True,
                'removed_tokens': removed_count
            })

        @self.app.route('/admin/stats', methods=['GET'])
        def get_stats():
            """Get system statistics"""
            if not hasattr(g, 'agent_credentials'):
                return jsonify({'error': 'Authentication required'}), 401

            if not g.agent_credentials.has_permission(Permission.VIEW_STATS):
                return jsonify({'error': 'Permission denied'}), 403

            stats = self.manager.get_inbox_stats()
            stats['active_agents'] = len(self.auth_manager.list_agents(active_only=True))
            stats['active_tokens'] = len(self.auth_manager.active_tokens)

            return jsonify(stats)

    def _setup_error_handlers(self):
        """Setup error handlers"""

        @self.app.errorhandler(400)
        def bad_request(error):
            return jsonify({'error': 'Bad request'}), 400

        @self.app.errorhandler(401)
        def unauthorized(error):
            return jsonify({'error': 'Unauthorized'}), 401

        @self.app.errorhandler(403)
        def forbidden(error):
            return jsonify({'error': 'Forbidden'}), 403

        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Not found'}), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({'error': 'Internal server error'}), 500

    def _message_to_dict(self, message: AgentMessage) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            'message_id': message.message_id,
            'sender_id': message.sender_id,
            'recipient_id': message.recipient_id,
            'subject': message.subject,
            'content': message.content,
            'message_type': message.message_type.value,
            'priority': message.priority.value,
            'status': message.status.value,
            'timestamp': message.timestamp.isoformat(),
            'metadata': message.metadata
        }

    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the Flask application"""
        self.app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    # Example usage
    from .storage import InMemoryInboxStorage
    from .routing import MessageRouter

    # Create components
    storage = InMemoryInboxStorage()
    router = MessageRouter()

    # Create and run API
    api = AuthenticatedInboxAPI(storage, router, secret_key="your-secret-key-here")

    print("Starting Authenticated Inbox API on http://localhost:5000")
    print("Default endpoints:")
    print("  - POST /auth/register - Register new agent")
    print("  - POST /auth/login - Login with API key")
    print("  - GET /auth/me - Get current agent info")
    print("  - POST /messages/send - Send message")
    print("  - GET /messages/inbox - Get inbox messages")
    print("  - POST /messages/<id>/read - Mark message as read")
    print("  - GET /admin/stats - Get system stats (admin only)")

    api.run(debug=True)