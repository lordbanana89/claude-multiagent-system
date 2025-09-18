"""
Advanced Messaging System Package
Enhanced messaging capabilities for the multi-agent system
"""

from .notifications import AgentNotificationSystem, NotificationConfig
from .classification import MessageClassifier, MessageCategory
from .workflow import AgentDecisionEngine, AgentConfig
from .interface import EnhancedTerminalInterface, MessageActionHandler
from .management import IntelligentInbox, MessageLifecycleManager

__all__ = [
    'AgentNotificationSystem',
    'NotificationConfig',
    'MessageClassifier',
    'MessageCategory',
    'AgentDecisionEngine',
    'AgentConfig',
    'EnhancedTerminalInterface',
    'MessageActionHandler',
    'IntelligentInbox',
    'MessageLifecycleManager'
]

__version__ = "1.0.0"