"""
Inbox Infrastructure Package
Core inbox functionality for agent messaging system
"""

from .storage import InboxStorage, InboxManager
from .routing import MessageRouter, RoutingRule, RoutingStrategy, FilterType
from .api import InboxAPI, create_inbox_api
from .auth import AuthenticationManager, AgentCredentials, Role, Permission
from .validation import MessageValidator, ValidationResult, ErrorHandler, RateLimiter

__all__ = [
    'InboxStorage',
    'InboxManager',
    'MessageRouter',
    'RoutingRule',
    'RoutingStrategy',
    'FilterType',
    'InboxAPI',
    'create_inbox_api',
    'AuthenticationManager',
    'AgentCredentials',
    'Role',
    'Permission',
    'MessageValidator',
    'ValidationResult',
    'ErrorHandler',
    'RateLimiter'
]

__version__ = "1.0.0"