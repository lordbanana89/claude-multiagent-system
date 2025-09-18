"""
Queue Client - High-level interface for interacting with Dramatiq queue
"""

import time
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import DEBUG
from task_queue import broker
from task_queue.actors import (
    process_agent_command,
    broadcast_message,
    execute_task,
    notify_agent
)

# Configure logging
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class QueueMessage:
    """Represents a message in the queue"""
    message_id: str
    actor_name: str
    args: tuple
    kwargs: dict
    options: dict
    timestamp: float
    status: str = "pending"


class QueueClient:
    """
    High-level client for interacting with the Dramatiq queue system
    Provides convenient methods for task submission and monitoring
    """

    def __init__(self, broker_instance=None):
        """
        Initialize queue client

        Args:
            broker_instance: Optional broker instance (defaults to global broker)
        """
        self.broker = broker_instance or broker
        self._message_history = []
        self._max_history = 100

    def send_command(self, agent_id: str, command: str, task_id: Optional[str] = None,
                    delay: Optional[int] = None) -> str:
        """
        Send a command to an agent via the queue

        Args:
            agent_id: Target agent ID
            command: Command to send
            task_id: Optional task ID for tracking
            delay: Optional delay in milliseconds before processing

        Returns:
            Message ID for tracking
        """
        logger.info(f"Queueing command for {agent_id}")

        # Build options
        options = {}
        if delay:
            options["delay"] = delay

        # Send to queue
        message = process_agent_command.send_with_options(
            args=(agent_id, command),
            kwargs={"task_id": task_id},
            **options
        )

        # Track message
        self._track_message(message, "process_agent_command", (agent_id, command))

        logger.debug(f"Command queued with message_id: {message.message_id}")
        return message.message_id

    def broadcast(self, message: str, exclude: Optional[List[str]] = None) -> str:
        """
        Broadcast a message to all agents

        Args:
            message: Message to broadcast
            exclude: List of agent IDs to exclude

        Returns:
            Message ID for tracking
        """
        logger.info("Queueing broadcast message")

        # Send to queue
        msg = broadcast_message.send(message, exclude=exclude)

        # Track message
        self._track_message(msg, "broadcast_message", (message,))

        logger.debug(f"Broadcast queued with message_id: {msg.message_id}")
        return msg.message_id

    def submit_task(self, task_definition: Dict[str, Any], priority: Optional[int] = None) -> str:
        """
        Submit a complex task for execution

        Args:
            task_definition: Task definition dictionary
            priority: Optional priority (higher = more important)

        Returns:
            Message ID for tracking
        """
        task_id = task_definition.get("task_id", f"task_{int(time.time() * 1000)}")
        logger.info(f"Queueing task: {task_id}")

        # Ensure task_id is in definition
        task_definition["task_id"] = task_id

        # Build options
        options = {}
        if priority:
            options["priority"] = priority

        # Send to queue
        message = execute_task.send_with_options(
            args=(task_definition,),
            **options
        )

        # Track message
        self._track_message(message, "execute_task", (task_definition,))

        logger.debug(f"Task queued with message_id: {message.message_id}")
        return message.message_id

    def notify(self, agent_id: str, notification: Dict[str, Any]) -> str:
        """
        Send a notification to an agent

        Args:
            agent_id: Target agent ID
            notification: Notification data

        Returns:
            Message ID for tracking
        """
        logger.info(f"Queueing notification for {agent_id}")

        # Send to queue
        message = notify_agent.send(agent_id, notification)

        # Track message
        self._track_message(message, "notify_agent", (agent_id, notification))

        logger.debug(f"Notification queued with message_id: {message.message_id}")
        return message.message_id

    def create_task_chain(self, steps: List[Dict[str, Any]]) -> str:
        """
        Create a chain of tasks to execute sequentially

        Args:
            steps: List of task steps, each containing:
                - agent_id: Target agent
                - command: Command to execute
                - description: Step description
                - delay: Delay after step (seconds)
                - continue_on_failure: Whether to continue if step fails

        Returns:
            Message ID for the task
        """
        task_definition = {
            "task_id": f"chain_{int(time.time() * 1000)}",
            "task_type": "chain",
            "steps": steps,
            "created_at": time.time()
        }

        return self.submit_task(task_definition)

    def create_parallel_tasks(self, tasks: List[Tuple[str, str]]) -> List[str]:
        """
        Create parallel tasks for multiple agents

        Args:
            tasks: List of (agent_id, command) tuples

        Returns:
            List of message IDs
        """
        message_ids = []

        for agent_id, command in tasks:
            msg_id = self.send_command(agent_id, command)
            message_ids.append(msg_id)

        logger.info(f"Created {len(message_ids)} parallel tasks")
        return message_ids

    def _track_message(self, message: Any, actor_name: str, args: tuple):
        """
        Track a message in history

        Args:
            message: Dramatiq message object
            actor_name: Name of the actor
            args: Arguments passed to actor
        """
        msg_record = QueueMessage(
            message_id=message.message_id,
            actor_name=actor_name,
            args=args,
            kwargs={},
            options=message.options,
            timestamp=time.time(),
            status="queued"
        )

        self._message_history.append(msg_record)

        # Trim history if too large
        if len(self._message_history) > self._max_history:
            self._message_history = self._message_history[-self._max_history:]

    def get_history(self, limit: int = 10) -> List[QueueMessage]:
        """
        Get recent message history

        Args:
            limit: Number of recent messages to return

        Returns:
            List of recent messages
        """
        return self._message_history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics

        Returns:
            Dictionary with queue stats
        """
        stats = {
            "total_messages_sent": len(self._message_history),
            "recent_messages": len(self._message_history),
            "broker_type": type(self.broker).__name__,
            "timestamp": time.time()
        }

        # Count by actor
        actor_counts = {}
        for msg in self._message_history:
            actor_counts[msg.actor_name] = actor_counts.get(msg.actor_name, 0) + 1

        stats["messages_by_actor"] = actor_counts

        # Get broker-specific stats if available
        if hasattr(self.broker, 'get_queue_lengths'):
            try:
                stats["queue_lengths"] = self.broker.get_queue_lengths()
            except:
                pass

        return stats

    def clear_history(self):
        """Clear message history"""
        self._message_history.clear()
        logger.info("Message history cleared")


# Convenience functions for quick usage
_default_client = None


def get_default_client() -> QueueClient:
    """Get or create default queue client"""
    global _default_client
    if _default_client is None:
        _default_client = QueueClient()
    return _default_client


def send_agent_command(agent_id: str, command: str, task_id: Optional[str] = None) -> str:
    """
    Quick function to send command to agent

    Args:
        agent_id: Target agent ID
        command: Command to send
        task_id: Optional task ID

    Returns:
        Message ID
    """
    client = get_default_client()
    return client.send_command(agent_id, command, task_id)


def broadcast_to_all(message: str, exclude: Optional[List[str]] = None) -> str:
    """
    Quick function to broadcast message

    Args:
        message: Message to broadcast
        exclude: Agents to exclude

    Returns:
        Message ID
    """
    client = get_default_client()
    return client.broadcast(message, exclude)


def quick_notify(agent_id: str, title: str, message: str, type: str = "info") -> str:
    """
    Quick function to send notification

    Args:
        agent_id: Target agent
        title: Notification title
        message: Notification message
        type: Notification type

    Returns:
        Message ID
    """
    client = get_default_client()
    notification = {
        "type": type,
        "title": title,
        "message": message,
        "priority": "medium"
    }
    return client.notify(agent_id, notification)


if __name__ == "__main__":
    # Test the queue client
    print("🧪 Testing Queue Client...")

    client = QueueClient()

    # Test getting stats
    stats = client.get_stats()
    print("\n📊 Queue Statistics:")
    print(f"  Broker type: {stats['broker_type']}")
    print(f"  Total messages: {stats['total_messages_sent']}")

    # Example: Create a task chain
    example_chain = [
        {
            "agent_id": "supervisor",
            "command": "echo 'Starting deployment process'",
            "description": "Initialize deployment",
            "delay": 1
        },
        {
            "agent_id": "backend-api",
            "command": "echo 'Deploying backend services'",
            "description": "Deploy backend",
            "delay": 2
        },
        {
            "agent_id": "frontend-ui",
            "command": "echo 'Building frontend'",
            "description": "Build frontend",
            "delay": 1
        },
        {
            "agent_id": "supervisor",
            "command": "echo 'Deployment complete'",
            "description": "Finalize",
            "delay": 0
        }
    ]

    print("\n📋 Example task chain created (not sent):")
    for i, step in enumerate(example_chain, 1):
        print(f"  Step {i}: {step['description']} -> {step['agent_id']}")

    print("\n✅ Queue Client ready!")