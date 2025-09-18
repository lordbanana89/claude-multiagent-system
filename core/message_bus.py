#!/usr/bin/env python3
"""
Central Message Bus for Multi-Agent System
Provides real event routing between all components
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
from collections import defaultdict
import queue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types in the system"""
    # Agent events
    AGENT_READY = "agent.ready"
    AGENT_BUSY = "agent.busy"
    AGENT_ERROR = "agent.error"
    AGENT_OFFLINE = "agent.offline"

    # Task events
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"

    # Message events
    MESSAGE_SENT = "message.sent"
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_ACKNOWLEDGED = "message.acknowledged"

    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"

    # Collaboration events
    COLLABORATION_REQUEST = "collaboration.request"
    COLLABORATION_ACCEPTED = "collaboration.accepted"
    COLLABORATION_REJECTED = "collaboration.rejected"
    COLLABORATION_COMPLETED = "collaboration.completed"


@dataclass
class Event:
    """Event data structure"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = EventType.SYSTEM_ERROR
    source: str = ""
    target: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MessageBus:
    """Central message bus for event routing"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.subscribers = defaultdict(list)
        self.event_queue = asyncio.Queue()
        self.sync_queue = queue.Queue()
        self.event_history = []
        self.max_history = 1000
        self.running = False
        self._event_loop = None
        self._thread = None

        logger.info("🚌 Message Bus initialized")

    def start(self):
        """Start the message bus"""
        if self.running:
            return

        self.running = True

        # Start async event loop in background thread
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()

        # Start sync processor
        threading.Thread(target=self._process_sync_events, daemon=True).start()

        logger.info("✅ Message Bus started")

    def stop(self):
        """Stop the message bus"""
        self.running = False
        if self._event_loop:
            self._event_loop.call_soon_threadsafe(self._event_loop.stop)
        logger.info("🛑 Message Bus stopped")

    def _run_event_loop(self):
        """Run async event loop in thread"""
        self._event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._event_loop)

        self._event_loop.run_until_complete(self._process_async_events())

    async def _process_async_events(self):
        """Process async events"""
        while self.running:
            try:
                # Get event with timeout
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )

                await self._dispatch_event(event)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing async event: {e}")

    def _process_sync_events(self):
        """Process sync events"""
        while self.running:
            try:
                event = self.sync_queue.get(timeout=1.0)
                self._dispatch_sync_event(event)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing sync event: {e}")

    def subscribe(self, event_type: EventType, handler: Callable,
                  filter_func: Optional[Callable] = None):
        """Subscribe to event type"""
        subscription = {
            'handler': handler,
            'filter': filter_func,
            'id': str(uuid.uuid4())
        }

        self.subscribers[event_type].append(subscription)
        logger.info(f"📮 Subscribed to {event_type.value}")

        return subscription['id']

    def unsubscribe(self, subscription_id: str):
        """Unsubscribe from events"""
        for event_type, subs in self.subscribers.items():
            self.subscribers[event_type] = [
                s for s in subs if s['id'] != subscription_id
            ]

    def publish(self, event: Event, sync: bool = False):
        """Publish an event"""
        # Add to history
        self._add_to_history(event)

        # Log event
        logger.debug(f"📤 Event: {event.type.value} from {event.source}")

        # Route to appropriate queue
        if sync:
            self.sync_queue.put(event)
        else:
            if self._event_loop and self.running:
                asyncio.run_coroutine_threadsafe(
                    self.event_queue.put(event),
                    self._event_loop
                )

    async def _dispatch_event(self, event: Event):
        """Dispatch event to async subscribers"""
        subscribers = self.subscribers.get(event.type, [])

        for sub in subscribers:
            try:
                # Apply filter if provided
                if sub['filter'] and not sub['filter'](event):
                    continue

                handler = sub['handler']

                # Call handler
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)

            except Exception as e:
                logger.error(f"Error in event handler: {e}")

    def _dispatch_sync_event(self, event: Event):
        """Dispatch event to sync subscribers"""
        subscribers = self.subscribers.get(event.type, [])

        for sub in subscribers:
            try:
                # Apply filter if provided
                if sub['filter'] and not sub['filter'](event):
                    continue

                handler = sub['handler']

                # Call handler synchronously
                if not asyncio.iscoroutinefunction(handler):
                    handler(event)
                else:
                    # Schedule async handler
                    if self._event_loop and self.running:
                        asyncio.run_coroutine_threadsafe(
                            handler(event),
                            self._event_loop
                        )

            except Exception as e:
                logger.error(f"Error in sync event handler: {e}")

    def _add_to_history(self, event: Event):
        """Add event to history"""
        self.event_history.append(event)

        # Trim history if needed
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]

    def get_history(self, event_type: Optional[EventType] = None,
                    source: Optional[str] = None,
                    since: Optional[float] = None) -> List[Event]:
        """Get event history with optional filters"""
        history = self.event_history

        if event_type:
            history = [e for e in history if e.type == event_type]

        if source:
            history = [e for e in history if e.source == source]

        if since:
            history = [e for e in history if e.timestamp >= since]

        return history

    def create_event(self, event_type: EventType, source: str,
                    payload: Dict[str, Any] = None,
                    target: Optional[str] = None,
                    correlation_id: Optional[str] = None) -> Event:
        """Helper to create and publish event"""
        event = Event(
            type=event_type,
            source=source,
            target=target,
            payload=payload or {},
            correlation_id=correlation_id
        )

        return event

    def request_reply(self, event: Event, timeout: float = 5.0) -> Optional[Event]:
        """Send event and wait for reply"""
        reply_queue = queue.Queue()
        correlation_id = event.correlation_id or event.id

        # Subscribe to replies
        def reply_handler(reply_event: Event):
            if reply_event.correlation_id == correlation_id:
                reply_queue.put(reply_event)

        sub_id = self.subscribe(EventType.MESSAGE_RECEIVED, reply_handler)

        try:
            # Publish request
            self.publish(event)

            # Wait for reply
            reply = reply_queue.get(timeout=timeout)
            return reply

        except queue.Empty:
            logger.warning(f"No reply received for {event.id}")
            return None

        finally:
            self.unsubscribe(sub_id)


# Global instance
_message_bus = MessageBus()


def get_message_bus() -> MessageBus:
    """Get message bus singleton"""
    return _message_bus


# Convenience functions
def publish_event(event_type: EventType, source: str, **kwargs):
    """Publish event convenience function"""
    bus = get_message_bus()
    event = bus.create_event(event_type, source, **kwargs)
    bus.publish(event)
    return event


def subscribe_to_event(event_type: EventType, handler: Callable, **kwargs):
    """Subscribe convenience function"""
    bus = get_message_bus()
    return bus.subscribe(event_type, handler, **kwargs)


# Example usage
if __name__ == "__main__":
    import time

    # Initialize bus
    bus = get_message_bus()
    bus.start()

    # Example subscriber
    def on_task_created(event: Event):
        print(f"📥 Task created: {event.payload}")

    # Subscribe
    bus.subscribe(EventType.TASK_CREATED, on_task_created)

    # Publish events
    for i in range(3):
        event = bus.create_event(
            EventType.TASK_CREATED,
            source="test",
            payload={"task_id": f"task_{i}", "description": f"Test task {i}"}
        )
        bus.publish(event)
        time.sleep(1)

    # Check history
    history = bus.get_history(EventType.TASK_CREATED)
    print(f"\n📜 History: {len(history)} events")

    # Cleanup
    time.sleep(2)
    bus.stop()