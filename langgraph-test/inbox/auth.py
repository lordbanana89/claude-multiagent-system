"""
Authentication and Authorization for Inbox System
Handles agent authentication, permissions, and access control
"""

from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import secrets
import jwt
from functools import wraps

from shared_state.models import AgentMessage, MessageType


class Permission(Enum):
    """System permissions"""
    READ_OWN_MESSAGES = "read_own_messages"
    SEND_MESSAGES = "send_messages"
    BROADCAST_MESSAGES = "broadcast_messages"
    READ_ALL_MESSAGES = "read_all_messages"  # Admin permission
    DELETE_MESSAGES = "delete_messages"
    MANAGE_ROUTING = "manage_routing"
    VIEW_STATS = "view_stats"
    ADMIN_CLEANUP = "admin_cleanup"


class Role(Enum):
    """User roles with predefined permissions"""
    AGENT = "agent"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"
    SYSTEM = "system"


@dataclass
class AgentCredentials:
    """Agent authentication credentials"""
    agent_id: str
    agent_name: str
    role: Role
    permissions: Set[Permission] = field(default_factory=set)
    api_key_hash: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default permissions based on role"""
        if not self.permissions:
            self.permissions = self._get_default_permissions()

    def _get_default_permissions(self) -> Set[Permission]:
        """Get default permissions for role"""
        role_permissions = {
            Role.AGENT: {
                Permission.READ_OWN_MESSAGES,
                Permission.SEND_MESSAGES
            },
            Role.SUPERVISOR: {
                Permission.READ_OWN_MESSAGES,
                Permission.SEND_MESSAGES,
                Permission.BROADCAST_MESSAGES,
                Permission.VIEW_STATS
            },
            Role.ADMIN: {
                Permission.READ_OWN_MESSAGES,
                Permission.SEND_MESSAGES,
                Permission.BROADCAST_MESSAGES,
                Permission.READ_ALL_MESSAGES,
                Permission.DELETE_MESSAGES,
                Permission.MANAGE_ROUTING,
                Permission.VIEW_STATS,
                Permission.ADMIN_CLEANUP
            },
            Role.SYSTEM: {perm for perm in Permission}  # All permissions
        }
        return role_permissions.get(self.role, set())

    def has_permission(self, permission: Permission) -> bool:
        """Check if agent has specific permission"""
        return self.active and permission in self.permissions

    def can_access_message(self, message: AgentMessage) -> bool:
        """Check if agent can access a specific message"""
        if not self.active:
            return False

        # System and admin can access all messages
        if self.has_permission(Permission.READ_ALL_MESSAGES):
            return True

        # Agents can access their own messages
        return (message.sender_id == self.agent_id or
                message.recipient_id == self.agent_id or
                (message.recipient_id is None and message.message_type == MessageType.BROADCAST))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'role': self.role.value,
            'permissions': [p.value for p in self.permissions],
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'active': self.active,
            'metadata': self.metadata
        }


class AuthenticationManager:
    """Manages agent authentication and authorization"""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.agents: Dict[str, AgentCredentials] = {}
        self.active_tokens: Dict[str, str] = {}  # token -> agent_id
        self.api_keys: Dict[str, str] = {}  # api_key -> agent_id

    def register_agent(self, agent_id: str, agent_name: str, role: Role = Role.AGENT,
                      permissions: Optional[Set[Permission]] = None) -> AgentCredentials:
        """Register a new agent"""
        if agent_id in self.agents:
            raise ValueError(f"Agent {agent_id} already registered")

        agent = AgentCredentials(
            agent_id=agent_id,
            agent_name=agent_name,
            role=role,
            permissions=permissions or set()
        )

        self.agents[agent_id] = agent
        return agent

    def generate_api_key(self, agent_id: str) -> str:
        """Generate API key for agent"""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")

        api_key = f"ak_{secrets.token_urlsafe(32)}"
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        self.agents[agent_id].api_key_hash = api_key_hash
        self.api_keys[api_key] = agent_id

        return api_key

    def authenticate_with_api_key(self, api_key: str) -> Optional[AgentCredentials]:
        """Authenticate agent with API key"""
        if api_key not in self.api_keys:
            return None

        agent_id = self.api_keys[api_key]
        agent = self.agents.get(agent_id)

        if agent and agent.active:
            # Verify API key hash
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            if agent.api_key_hash == api_key_hash:
                agent.last_login = datetime.now()
                return agent

        return None

    def generate_jwt_token(self, agent_id: str, expires_in: int = 3600) -> str:
        """Generate JWT token for agent"""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self.agents[agent_id]
        if not agent.active:
            raise ValueError(f"Agent {agent_id} is not active")

        payload = {
            'agent_id': agent_id,
            'role': agent.role.value,
            'permissions': [p.value for p in agent.permissions],
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(seconds=expires_in)
        }

        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        self.active_tokens[token] = agent_id

        agent.last_login = datetime.now()
        return token

    def verify_jwt_token(self, token: str) -> Optional[AgentCredentials]:
        """Verify JWT token and return agent credentials"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            agent_id = payload['agent_id']

            if token in self.active_tokens and self.active_tokens[token] == agent_id:
                agent = self.agents.get(agent_id)
                if agent and agent.active:
                    return agent

        except jwt.ExpiredSignatureError:
            # Remove expired token
            if token in self.active_tokens:
                del self.active_tokens[token]
        except jwt.InvalidTokenError:
            pass

        return None

    def revoke_token(self, token: str) -> bool:
        """Revoke a JWT token"""
        if token in self.active_tokens:
            del self.active_tokens[token]
            return True
        return False

    def revoke_api_key(self, agent_id: str) -> bool:
        """Revoke agent's API key"""
        if agent_id not in self.agents:
            return False

        agent = self.agents[agent_id]
        if agent.api_key_hash:
            # Find and remove API key
            for api_key, stored_agent_id in list(self.api_keys.items()):
                if stored_agent_id == agent_id:
                    del self.api_keys[api_key]
                    break

            agent.api_key_hash = None
            return True

        return False

    def deactivate_agent(self, agent_id: str) -> bool:
        """Deactivate an agent"""
        if agent_id in self.agents:
            self.agents[agent_id].active = False

            # Revoke all tokens for this agent
            tokens_to_revoke = [token for token, stored_agent_id in self.active_tokens.items()
                              if stored_agent_id == agent_id]
            for token in tokens_to_revoke:
                del self.active_tokens[token]

            # Revoke API key
            self.revoke_api_key(agent_id)
            return True

        return False

    def get_agent(self, agent_id: str) -> Optional[AgentCredentials]:
        """Get agent credentials"""
        return self.agents.get(agent_id)

    def list_agents(self, active_only: bool = True) -> List[AgentCredentials]:
        """List all agents"""
        agents = list(self.agents.values())
        if active_only:
            agents = [agent for agent in agents if agent.active]
        return agents

    def update_permissions(self, agent_id: str, permissions: Set[Permission]) -> bool:
        """Update agent permissions"""
        if agent_id in self.agents:
            self.agents[agent_id].permissions = permissions
            return True
        return False

    def cleanup_expired_tokens(self):
        """Remove expired tokens from active tokens"""
        expired_tokens = []

        for token in list(self.active_tokens.keys()):
            try:
                jwt.decode(token, self.secret_key, algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                expired_tokens.append(token)
            except jwt.InvalidTokenError:
                expired_tokens.append(token)

        for token in expired_tokens:
            del self.active_tokens[token]

        return len(expired_tokens)


def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This assumes Flask context with g.agent_credentials set
            from flask import g, jsonify

            if not hasattr(g, 'agent_credentials') or not g.agent_credentials:
                return jsonify({'error': 'Authentication required'}), 401

            if not g.agent_credentials.has_permission(permission):
                return jsonify({'error': f'Permission {permission.value} required'}), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator


def require_role(role: Role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import g, jsonify

            if not hasattr(g, 'agent_credentials') or not g.agent_credentials:
                return jsonify({'error': 'Authentication required'}), 401

            if g.agent_credentials.role != role:
                return jsonify({'error': f'Role {role.value} required'}), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator


def create_default_auth_manager(secret_key: str) -> AuthenticationManager:
    """Create authentication manager with default agents"""
    auth_manager = AuthenticationManager(secret_key)

    # Create default system agent
    system_agent = auth_manager.register_agent(
        agent_id="system",
        agent_name="System Agent",
        role=Role.SYSTEM
    )

    # Create default admin agent
    admin_agent = auth_manager.register_agent(
        agent_id="admin",
        agent_name="Administrator",
        role=Role.ADMIN
    )

    # Generate API keys
    system_api_key = auth_manager.generate_api_key("system")
    admin_api_key = auth_manager.generate_api_key("admin")

    print(f"System API Key: {system_api_key}")
    print(f"Admin API Key: {admin_api_key}")

    return auth_manager


if __name__ == "__main__":
    # Example usage
    auth_manager = create_default_auth_manager("test-secret-key")

    # Register test agent
    test_agent = auth_manager.register_agent(
        agent_id="test-agent",
        agent_name="Test Agent",
        role=Role.AGENT
    )

    # Generate token
    token = auth_manager.generate_jwt_token("test-agent")
    print(f"Test Agent Token: {token}")

    # Verify token
    verified_agent = auth_manager.verify_jwt_token(token)
    if verified_agent:
        print(f"Token verified for: {verified_agent.agent_name}")
        print(f"Permissions: {[p.value for p in verified_agent.permissions]}")