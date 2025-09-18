"""
Task Queue Package - Production-ready Dramatiq queue system with Redis
Replaces the experimental SQLite broker with professional Redis backend
"""

from .broker import broker, setup_broker
from .actors import (
    process_agent_command,
    broadcast_message,
    execute_task,
    notify_agent,
    handle_failed_task,
    check_actors_health
)
from .client import (
    QueueClient,
    send_agent_command,
    broadcast_to_all,
    quick_notify,
    get_default_client
)

__version__ = "1.0.0"

__all__ = [
    # Broker
    "broker",
    "setup_broker",
    # Actors
    "process_agent_command",
    "broadcast_message",
    "execute_task",
    "notify_agent",
    "handle_failed_task",
    "check_actors_health",
    # Client
    "QueueClient",
    "send_agent_command",
    "broadcast_to_all",
    "quick_notify",
    "get_default_client",
]