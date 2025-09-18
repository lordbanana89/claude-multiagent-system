"""
Unified Message Bus for Claude Multi-Agent System
Centralizes all inter-component communication through Redis
"""

import json
import time
import asyncio
import threading
import uuid
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import redis.asyncio as aioredis
import redis
from config.settings import REDIS_HOST, REDIS_PORT, REDIS_DB
import logging
from core.persistence import get_persistence_manager

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class MessageType(Enum):
    TASK = "task"
    RESULT = "result"
    EVENT = "event"
    COMMAND = "command"
    STATUS = "status"
    ERROR = "error"
    NOTIFICATION = "notification"


@dataclass
class Message:
    """Universal message format for all system communications"""
    id: str
    type: MessageType
    source: str
    target: Optional[str]
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: float = None
    correlation_id: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'type': self.type.value,
            'source': self.source,
            'target': self.target,
            'payload': self.payload,
            'priority': self.priority.value,
            'timestamp': self.timestamp,
            'correlation_id': self.correlation_id
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Message':
        return cls(
            id=data['id'],
            type=MessageType(data['type']),
            source=data['source'],
            target=data.get('target'),
            payload=data['payload'],
            priority=MessagePriority(data.get('priority', 1)),
            timestamp=data.get('timestamp', time.time()),
            correlation_id=data.get('correlation_id')
        )


class UnifiedMessageBus:
    """
    Central message bus for all system communications
    Handles task distribution, result aggregation, events, and notifications
    """

    def __init__(self):
        self.redis_client = redis.StrictRedis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )
        self.async_redis = None
        self.subscribers: Dict[str, Set[Callable]] = {}
        self.persistence = get_persistence_manager()
        self.running = False
        self._listener_thread = None

        # Channel patterns
        self.TASK_CHANNEL = "bus:tasks:{agent}"
        self.RESULT_CHANNEL = "bus:results:{task_id}"
        self.EVENT_CHANNEL = "bus:events:{event_type}"
        self.BROADCAST_CHANNEL = "bus:broadcast"
        self.STATUS_CHANNEL = "bus:status:{agent}"

        logger.info("UnifiedMessageBus initialized")

    async def initialize_async(self):
        """Initialize async Redis connection"""
        self.async_redis = await aioredis.create_redis_pool(
            f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
        )

    def start(self):
        """Start the message bus listener"""
        if not self.running:
            self.running = True
            self._listener_thread = threading.Thread(target=self._listener_loop)
            self._listener_thread.daemon = True
            self._listener_thread.start()
            logger.info("Message bus listener started")

    def stop(self):
        """Stop the message bus listener"""
        self.running = False
        if self._listener_thread:
            self._listener_thread.join(timeout=5)
        logger.info("Message bus listener stopped")

    def publish_task(self, agent: str, task: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """
        Publish a task to a specific agent
        Returns task_id for tracking
        """
        import uuid
        task_id = str(uuid.uuid4())

        message = Message(
            id=task_id,
            type=MessageType.TASK,
            source="orchestrator",
            target=agent,
            payload=task,
            priority=priority
        )

        channel = self.TASK_CHANNEL.format(agent=agent)

        # Publish to Redis for any external listeners
        self.redis_client.publish(channel, json.dumps(message.to_dict()))

        # Also directly notify internal subscribers
        self._process_message(channel, message)

        # Store task in queue for persistence
        queue_key = f"queue:{agent}:{priority.name.lower()}"
        self.redis_client.lpush(queue_key, json.dumps(message.to_dict()))

        # Set task status (only if it doesn't exist or is not already completed)
        existing_status = self.redis_client.hget(f"task:{task_id}", 'status')
        if not existing_status or existing_status == 'pending':
            self.redis_client.hset(f"task:{task_id}", mapping={
                'status': 'pending',
                'agent': agent,
                'created_at': time.time(),
                'priority': priority.value
            })

            # Persist to SQLite
            self.persistence.save_task(
                task_id=task_id,
                agent=agent,
                command=task.get('command', ''),
                params=task.get('params', {}),
                priority=priority.value,
                status='pending'
            )

        logger.info(f"Published task {task_id} to agent {agent} with priority {priority.name}")
        return task_id

    def publish_result(self, task_id: str, result: Dict[str, Any], success: bool = True):
        """Publish task execution result"""
        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.RESULT,
            source="agent",
            target=None,
            payload={
                'task_id': task_id,
                'result': result,
                'success': success
            },
            correlation_id=task_id
        )

        channel = self.RESULT_CHANNEL.format(task_id=task_id)
        self.redis_client.publish(channel, json.dumps(message.to_dict()))

        # Update task status
        status = 'completed' if success else 'failed'
        update_data = {
            'status': status,
            'completed_at': str(time.time()),
            'result': json.dumps(result)
        }

        # Debug: Check what's in Redis before update
        before = self.redis_client.hget(f"task:{task_id}", 'status')

        # Use hset to update multiple fields (hmset is deprecated)
        self.redis_client.hset(f"task:{task_id}", mapping=update_data)

        # Debug: Check what's in Redis after update
        after = self.redis_client.hget(f"task:{task_id}", 'status')

        # Persist to SQLite
        self.persistence.update_task_status(
            task_id=task_id,
            status=status,
            result=result if success else None,
            error=json.dumps(result) if not success else None
        )

        logger.info(f"Published result for task {task_id}: {status} (before={before}, after={after})")

    def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to all listeners"""
        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.EVENT,
            source="system",
            target=None,
            payload={
                'event_type': event_type,
                'data': data
            }
        )

        # Publish to specific event channel
        event_channel = self.EVENT_CHANNEL.format(event_type=event_type)
        self.redis_client.publish(event_channel, json.dumps(message.to_dict()))

        # Also publish to broadcast channel
        self.redis_client.publish(self.BROADCAST_CHANNEL, json.dumps(message.to_dict()))

        logger.info(f"Broadcast event: {event_type}")

    def send_command(self, agent: str, command: str, params: Dict[str, Any] = None):
        """Send a direct command to an agent"""
        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.COMMAND,
            source="system",
            target=agent,
            payload={
                'command': command,
                'params': params or {}
            }
        )

        channel = self.TASK_CHANNEL.format(agent=agent)
        self.redis_client.publish(channel, json.dumps(message.to_dict()))

        logger.info(f"Sent command '{command}' to agent {agent}")

    def update_agent_status(self, agent: str, status: str, details: Dict[str, Any] = None):
        """Update and broadcast agent status"""
        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.STATUS,
            source=agent,
            target=None,
            payload={
                'status': status,
                'details': details or {},
                'timestamp': time.time()
            }
        )

        channel = self.STATUS_CHANNEL.format(agent=agent)
        self.redis_client.publish(channel, json.dumps(message.to_dict()))

        # Store status
        self.redis_client.hset(f"agent:{agent}", mapping={
            'status': status,
            'last_update': time.time(),
            'details': json.dumps(details or {})
        })

        logger.debug(f"Updated status for agent {agent}: {status}")

    def subscribe(self, pattern: str, callback: Callable):
        """Subscribe to a message pattern"""
        if pattern not in self.subscribers:
            self.subscribers[pattern] = set()
        self.subscribers[pattern].add(callback)
        logger.info(f"Added subscriber for pattern: {pattern}")

    def unsubscribe(self, pattern: str, callback: Callable):
        """Unsubscribe from a message pattern"""
        if pattern in self.subscribers:
            self.subscribers[pattern].discard(callback)
            if not self.subscribers[pattern]:
                del self.subscribers[pattern]
        logger.info(f"Removed subscriber for pattern: {pattern}")

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a task"""
        task_data = self.redis_client.hgetall(f"task:{task_id}")
        if task_data:
            if 'result' in task_data:
                task_data['result'] = json.loads(task_data['result'])
            return task_data
        return None

    def get_agent_status(self, agent: str) -> Optional[Dict[str, Any]]:
        """Get current status of an agent"""
        agent_data = self.redis_client.hgetall(f"agent:{agent}")
        if agent_data:
            if 'details' in agent_data:
                agent_data['details'] = json.loads(agent_data['details'])
            return agent_data
        return None

    def get_pending_tasks(self, agent: str = None) -> List[Dict[str, Any]]:
        """Get all pending tasks, optionally filtered by agent"""
        pattern = f"task:*"
        tasks = []

        for key in self.redis_client.scan_iter(match=pattern):
            task_data = self.redis_client.hgetall(key)
            if task_data.get('status') == 'pending':
                if agent is None or task_data.get('agent') == agent:
                    task_id = key.split(':')[1]
                    task_data['id'] = task_id
                    tasks.append(task_data)

        # Sort by priority and timestamp
        tasks.sort(key=lambda x: (-int(x.get('priority', 0)), float(x.get('created_at', 0))))
        return tasks

    def _listener_loop(self):
        """Main listener loop for processing subscribed channels"""
        pubsub = self.redis_client.pubsub()

        # Subscribe to all patterns
        for pattern in self.subscribers.keys():
            pubsub.psubscribe(pattern)

        pubsub.psubscribe(self.BROADCAST_CHANNEL)

        while self.running:
            try:
                message = pubsub.get_message(timeout=1.0)
                if message and message['type'] in ['message', 'pmessage']:
                    data = message['data']
                    channel = message.get('pattern', message.get('channel'))
                    if isinstance(channel, bytes):
                        channel = channel.decode('utf-8')

                    if isinstance(data, str):
                        try:
                            msg_dict = json.loads(data)
                            msg = Message.from_dict(msg_dict)
                            self._process_message(channel, msg)
                        except json.JSONDecodeError:
                            logger.error(f"Failed to decode message: {data}")
                    elif isinstance(data, bytes):
                        try:
                            msg_dict = json.loads(data.decode('utf-8'))
                            msg = Message.from_dict(msg_dict)
                            self._process_message(channel, msg)
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            logger.error(f"Failed to decode message: {data}")
            except Exception as e:
                logger.error(f"Error in listener loop: {e}")
                time.sleep(1)

        pubsub.close()

    def _process_message(self, channel: str, message: Message):
        """Process incoming message and call appropriate callbacks"""
        # Match channel to patterns and call callbacks
        for pattern, callbacks in self.subscribers.items():
            if self._pattern_matches(channel, pattern):
                for callback in callbacks:
                    try:
                        callback(message)
                    except Exception as e:
                        logger.error(f"Error in callback for {pattern}: {e}")

    def _pattern_matches(self, channel: str, pattern: str) -> bool:
        """Check if channel matches subscription pattern"""
        # Simple pattern matching (can be enhanced)
        if '*' in pattern:
            pattern_parts = pattern.split('*')
            return channel.startswith(pattern_parts[0]) and channel.endswith(pattern_parts[-1])
        return channel == pattern

    async def wait_for_result(self, task_id: str, timeout: int = 300) -> Optional[Dict[str, Any]]:
        """Async wait for task result"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            if status and status['status'] in ['completed', 'failed']:
                return status
            await asyncio.sleep(0.5)

        return None


# Singleton instance
_message_bus = None

def get_message_bus() -> UnifiedMessageBus:
    """Get or create singleton message bus instance"""
    global _message_bus
    if _message_bus is None:
        _message_bus = UnifiedMessageBus()
        _message_bus.start()
    return _message_bus


import uuid  # Add this import at the top with other imports