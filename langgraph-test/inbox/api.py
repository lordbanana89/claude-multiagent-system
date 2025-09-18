"""
Inbox API Endpoints
RESTful API for inbox operations with authentication and validation
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import asdict
import json
import uuid
from functools import wraps

from flask import Flask, request, jsonify, g
from flask_cors import CORS
import jwt

from shared_state.models import AgentMessage, MessageType, MessagePriority, MessageStatus
from .storage import InboxStorage, InboxManager
from .routing import MessageRouter, RoutingRule, RoutingStrategy, FilterType


class InboxAPI:
    """RESTful API for inbox operations"""

    def __init__(self, storage: InboxStorage, router: MessageRouter, secret_key: str = None):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = secret_key or str(uuid.uuid4())

        CORS(self.app)  # Enable CORS for cross-origin requests

        self.storage = storage
        self.manager = InboxManager(storage)
        self.router = router

        self._setup_routes()
        self._setup_error_handlers()

    def _setup_routes(self):
        """Setup API routes"""

        # Health check
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            })

        # Authentication
        @self.app.route('/auth/token', methods=['POST'])
        def generate_token():
            """Generate authentication token for agent"""
            data = request.get_json()

            if not data or 'agent_id' not in data:
                return jsonify({'error': 'agent_id required'}), 400

            agent_id = data['agent_id']

            # In production, validate agent credentials here
            token = jwt.encode({
                'agent_id': agent_id,
                'exp': datetime.utcnow().timestamp() + 3600  # 1 hour expiry
            }, self.app.config['SECRET_KEY'], algorithm='HS256')

            return jsonify({'token': token, 'expires_in': 3600})

        # Message endpoints
        @self.app.route('/messages/send', methods=['POST'])
        @self._require_auth
        def send_message():
            """Send a direct message"""
            data = request.get_json()

            try:
                validation_error = self._validate_send_message(data)
                if validation_error:
                    return jsonify({'error': validation_error}), 400

                sender_id = g.agent_id
                recipient_id = data['recipient_id']
                content = data['content']
                subject = data.get('subject')
                priority = MessagePriority(data.get('priority', 2))
                message_type = MessageType(data.get('message_type', 'direct'))

                message = self.manager.send_message(
                    sender_id=sender_id,
                    recipient_id=recipient_id,
                    content=content,
                    subject=subject,
                    priority=priority,
                    message_type=message_type
                )

                return jsonify({
                    'success': True,
                    'message_id': message.message_id,
                    'sent_at': message.timestamp.isoformat()
                }), 201

            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/messages/broadcast', methods=['POST'])
        @self._require_auth
        def broadcast_message():
            """Send broadcast message"""
            data = request.get_json()

            try:
                validation_error = self._validate_broadcast_message(data)
                if validation_error:
                    return jsonify({'error': validation_error}), 400

                sender_id = g.agent_id
                content = data['content']
                recipients = data.get('recipients', [])
                subject = data.get('subject')
                priority = MessagePriority(data.get('priority', 2))

                # If no specific recipients, broadcast to all available agents
                if not recipients:
                    # In a real implementation, you'd get this from agent registry
                    recipients = data.get('all_agents', [])

                messages = self.manager.broadcast_message(
                    sender_id=sender_id,
                    content=content,
                    recipients=recipients,
                    subject=subject,
                    priority=priority
                )

                return jsonify({
                    'success': True,
                    'message_count': len(messages),
                    'message_ids': [msg.message_id for msg in messages],
                    'sent_at': datetime.now().isoformat()
                }), 201

            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/inbox', methods=['GET'])
        @self._require_auth
        def get_inbox():
            """Get agent's inbox"""
            try:
                agent_id = g.agent_id
                limit = int(request.args.get('limit', 50))
                unread_only = request.args.get('unread_only', 'false').lower() == 'true'

                inbox_data = self.manager.get_inbox(
                    agent_id=agent_id,
                    limit=limit,
                    unread_only=unread_only
                )

                # Convert messages to dict format
                messages_dict = []
                for msg in inbox_data['messages']:
                    msg_dict = msg.to_dict()
                    messages_dict.append(msg_dict)

                return jsonify({
                    'agent_id': inbox_data['agent_id'],
                    'messages': messages_dict,
                    'unread_count': inbox_data['unread_count'],
                    'total_count': inbox_data['total_count']
                })

            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/messages/<message_id>', methods=['GET'])
        @self._require_auth
        def get_message(message_id):
            """Get specific message"""
            try:
                message = self.storage.get_message_by_id(message_id)

                if not message:
                    return jsonify({'error': 'Message not found'}), 404

                # Check if agent has access to this message
                agent_id = g.agent_id
                if message.recipient_id != agent_id and message.sender_id != agent_id:
                    return jsonify({'error': 'Access denied'}), 403

                return jsonify(message.to_dict())

            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/messages/<message_id>/read', methods=['POST'])
        @self._require_auth
        def mark_message_read(message_id):
            """Mark message as read"""
            try:
                agent_id = g.agent_id
                success = self.manager.mark_as_read(message_id, agent_id)

                if success:
                    return jsonify({'success': True, 'read_at': datetime.now().isoformat()})
                else:
                    return jsonify({'error': 'Message not found or already read'}), 404

            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/messages/search', methods=['GET'])
        @self._require_auth
        def search_messages():
            """Search messages in inbox"""
            try:
                agent_id = g.agent_id
                query = request.args.get('q', '')
                limit = int(request.args.get('limit', 50))

                if not query:
                    return jsonify({'error': 'Search query required'}), 400

                messages = self.manager.search_inbox(agent_id, query, limit)

                messages_dict = [msg.to_dict() for msg in messages]

                return jsonify({
                    'query': query,
                    'results': messages_dict,
                    'count': len(messages_dict)
                })

            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/conversations/<other_agent_id>', methods=['GET'])
        @self._require_auth
        def get_conversation(other_agent_id):
            """Get conversation with another agent"""
            try:
                agent_id = g.agent_id
                limit = int(request.args.get('limit', 100))

                messages = self.manager.get_conversation(agent_id, other_agent_id, limit)

                messages_dict = [msg.to_dict() for msg in messages]

                return jsonify({
                    'agent1_id': agent_id,
                    'agent2_id': other_agent_id,
                    'messages': messages_dict,
                    'count': len(messages_dict)
                })

            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # Admin endpoints
        @self.app.route('/admin/stats', methods=['GET'])
        @self._require_auth
        def get_stats():
            """Get system statistics"""
            try:
                storage_stats = self.storage.get_storage_stats()
                routing_stats = self.router.get_routing_stats()

                return jsonify({
                    'storage': storage_stats,
                    'routing': routing_stats,
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/admin/cleanup', methods=['POST'])
        @self._require_auth
        def cleanup_messages():
            """Clean up old messages"""
            try:
                data = request.get_json() or {}
                days = int(data.get('days', 30))

                deleted_count = self.storage.cleanup_old_messages(days)

                return jsonify({
                    'success': True,
                    'deleted_count': deleted_count,
                    'cleanup_date': datetime.now().isoformat()
                })

            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # Routing configuration endpoints
        @self.app.route('/routing/rules', methods=['GET'])
        @self._require_auth
        def get_routing_rules():
            """Get routing rules"""
            try:
                rules = self.router.export_rules()
                return jsonify({'rules': rules})

            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/routing/rules', methods=['POST'])
        @self._require_auth
        def add_routing_rule():
            """Add new routing rule"""
            try:
                data = request.get_json()

                validation_error = self._validate_routing_rule(data)
                if validation_error:
                    return jsonify({'error': validation_error}), 400

                rule = RoutingRule(
                    rule_id=data.get('rule_id', str(uuid.uuid4())),
                    name=data['name'],
                    strategy=RoutingStrategy(data['strategy']),
                    filter_type=FilterType(data['filter_type']),
                    filter_value=data['filter_value'],
                    target_agents=data.get('target_agents'),
                    priority=data.get('priority', 0),
                    description=data.get('description')
                )

                self.router.add_routing_rule(rule)

                return jsonify({
                    'success': True,
                    'rule_id': rule.rule_id
                }), 201

            except Exception as e:
                return jsonify({'error': str(e)}), 500

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

    def _require_auth(self, f):
        """Authentication decorator"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization')

            if not token:
                return jsonify({'error': 'Authorization token required'}), 401

            if token.startswith('Bearer '):
                token = token[7:]

            try:
                payload = jwt.decode(
                    token,
                    self.app.config['SECRET_KEY'],
                    algorithms=['HS256']
                )
                g.agent_id = payload['agent_id']

            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid token'}), 401

            return f(*args, **kwargs)

        return decorated_function

    def _validate_send_message(self, data: Dict[str, Any]) -> Optional[str]:
        """Validate send message request"""
        if not data:
            return "Request body required"

        if 'recipient_id' not in data:
            return "recipient_id required"

        if 'content' not in data:
            return "content required"

        if not data['content'].strip():
            return "content cannot be empty"

        if len(data['content']) > 10000:
            return "content too long (max 10000 characters)"

        if 'priority' in data:
            try:
                MessagePriority(data['priority'])
            except ValueError:
                return "invalid priority value (1-4)"

        if 'message_type' in data:
            try:
                MessageType(data['message_type'])
            except ValueError:
                return "invalid message_type"

        return None

    def _validate_broadcast_message(self, data: Dict[str, Any]) -> Optional[str]:
        """Validate broadcast message request"""
        if not data:
            return "Request body required"

        if 'content' not in data:
            return "content required"

        if not data['content'].strip():
            return "content cannot be empty"

        if len(data['content']) > 10000:
            return "content too long (max 10000 characters)"

        if 'recipients' in data and not isinstance(data['recipients'], list):
            return "recipients must be a list"

        return None

    def _validate_routing_rule(self, data: Dict[str, Any]) -> Optional[str]:
        """Validate routing rule request"""
        if not data:
            return "Request body required"

        required_fields = ['name', 'strategy', 'filter_type', 'filter_value']
        for field in required_fields:
            if field not in data:
                return f"{field} required"

        try:
            RoutingStrategy(data['strategy'])
        except ValueError:
            return "invalid strategy"

        try:
            FilterType(data['filter_type'])
        except ValueError:
            return "invalid filter_type"

        return None

    def run(self, host='localhost', port=5000, debug=False):
        """Run the API server"""
        self.app.run(host=host, port=port, debug=debug)

    def get_app(self):
        """Get Flask app instance"""
        return self.app


# Helper functions for integration
def create_inbox_api(db_path: str = "inbox.db", secret_key: str = None) -> InboxAPI:
    """Create configured inbox API instance"""
    storage = InboxStorage(db_path)
    router = MessageRouter()

    # Add some default routing rules
    from .routing import RoutingRule, RoutingStrategy, FilterType

    # High priority messages get routed to multiple agents
    urgent_rule = RoutingRule(
        rule_id="urgent_broadcast",
        name="Urgent Message Broadcast",
        strategy=RoutingStrategy.PRIORITY,
        filter_type=FilterType.PRIORITY,
        filter_value=4,
        priority=100
    )
    router.add_routing_rule(urgent_rule)

    # System messages broadcast to all
    system_rule = RoutingRule(
        rule_id="system_broadcast",
        name="System Message Broadcast",
        strategy=RoutingStrategy.BROADCAST,
        filter_type=FilterType.MESSAGE_TYPE,
        filter_value=MessageType.SYSTEM,
        priority=90
    )
    router.add_routing_rule(system_rule)

    api = InboxAPI(storage, router, secret_key)
    return api


if __name__ == "__main__":
    # Example usage
    api = create_inbox_api()
    print("Starting Inbox API server...")
    api.run(debug=True)