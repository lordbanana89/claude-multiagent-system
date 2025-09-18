#!/usr/bin/env python3
"""
Debug script to test message flow between components
"""

import sys
import os
import time
import json
import redis
import threading
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.message_bus import UnifiedMessageBus, Message, MessageType, MessagePriority
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_direct_redis():
    """Test Redis pub/sub directly"""
    print("\n=== Testing Direct Redis Pub/Sub ===")

    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

    # Test basic connectivity
    r.ping()
    print("✓ Redis connected")

    # Create pubsub
    pubsub = r.pubsub()

    # Track received messages
    received = []

    def message_handler(message):
        print(f"Received: {message}")
        received.append(message)

    # Subscribe to test channel
    pubsub.subscribe(**{'test-channel': message_handler})

    # Start listening in thread
    thread = pubsub.run_in_thread(sleep_time=0.001)

    # Publish test message
    r.publish('test-channel', json.dumps({"test": "message"}))
    print("✓ Published test message")

    # Wait for message
    time.sleep(1)

    # Check if received
    thread.stop()

    if received:
        print(f"✓ Received {len(received)} messages via Redis directly")
        return True
    else:
        print("✗ No messages received via Redis")
        return False

def test_message_bus_internals():
    """Test message bus internals"""
    print("\n=== Testing Message Bus Internals ===")

    from core.message_bus import UnifiedMessageBus
    import uuid

    bus = UnifiedMessageBus()

    # Track what we receive
    received_messages = []

    def callback(message):
        print(f"Callback received: {message.type.value if hasattr(message, 'type') else message}")
        received_messages.append(message)

    # Test 1: Direct channel subscription
    test_channel = "bus:tasks:backend-api"
    bus.subscribe(test_channel, callback)
    print(f"✓ Subscribed to {test_channel}")

    # Start the listener
    bus.start()
    time.sleep(1)

    # Test 2: Publish directly to Redis to see if listener picks it up
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

    test_message = {
        'id': str(uuid.uuid4()),
        'type': 'task',
        'source': 'test',
        'target': 'backend-api',
        'payload': {'test': 'data'},
        'priority': 1,
        'timestamp': time.time()
    }

    # Publish to exact channel
    r.publish(test_channel, json.dumps(test_message))
    print(f"✓ Published test message to {test_channel}")

    # Wait for processing
    time.sleep(2)

    if received_messages:
        print(f"✓ Message bus received {len(received_messages)} messages")
    else:
        print("✗ Message bus did not receive messages")

        # Debug: Check what channels are subscribed
        print("\nDebug - Subscribed patterns:", bus.subscribers.keys())

        # Try pattern subscription
        bus.subscribe("bus:tasks:*", callback)
        print("✓ Added pattern subscription")

        # Publish again
        r.publish(test_channel, json.dumps(test_message))
        time.sleep(2)

        if received_messages:
            print(f"✓ Pattern subscription worked: {len(received_messages)} messages")
        else:
            print("✗ Still no messages with pattern subscription")

    bus.stop()

    return len(received_messages) > 0

def test_agent_bridge_receiving():
    """Test if agent bridge receives messages"""
    print("\n=== Testing Agent Bridge Message Reception ===")

    from core.message_bus import get_message_bus
    from agents.agent_bridge import AgentBridge
    from core.tmux_client import TMUXClient

    # Ensure TMUX session exists
    tmux = TMUXClient()
    if not tmux.session_exists("claude-backend-api"):
        tmux.create_session("claude-backend-api")
        print("✓ Created TMUX session")

    # Create message bus
    bus = get_message_bus()
    if not bus.running:
        bus.start()
    print("✓ Message bus started")

    # Create and start agent bridge
    bridge = AgentBridge("backend-api")

    # Monkey-patch to track received messages
    original_handle = bridge._handle_task_message
    received_tasks = []

    def tracked_handle(message):
        print(f"Bridge received task: {message.id if hasattr(message, 'id') else message}")
        received_tasks.append(message)
        return original_handle(message)

    bridge._handle_task_message = tracked_handle

    bridge.start()
    print("✓ Agent bridge started")

    time.sleep(1)

    # Submit a task
    task_id = bus.publish_task(
        agent="backend-api",
        task={
            "command": "echo 'Test task'",
            "params": {},
            "timeout": 5
        }
    )
    print(f"✓ Published task: {task_id}")

    # Wait for reception
    time.sleep(3)

    if received_tasks:
        print(f"✓ Bridge received {len(received_tasks)} tasks")
    else:
        print("✗ Bridge did not receive any tasks")

        # Debug: Check Redis directly
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

        # Check if task is in queue
        queue_keys = r.keys("queue:*")
        print(f"\nDebug - Queue keys in Redis: {queue_keys}")

        for key in queue_keys:
            items = r.lrange(key, 0, -1)
            print(f"  {key}: {len(items)} items")
            if items:
                print(f"    Sample: {items[0][:100]}...")

    bridge.stop()

    return len(received_tasks) > 0

def test_fixed_message_flow():
    """Test with fixed message flow"""
    print("\n=== Testing Fixed Message Flow ===")

    # Clear any existing Redis data
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.flushdb()
    print("✓ Cleared Redis")

    from core.message_bus import UnifiedMessageBus
    import uuid

    # Create new bus instance
    bus = UnifiedMessageBus()

    # Fix: Ensure listener subscribes to actual Redis channels
    received = []

    def test_callback(message):
        print(f"Received in callback: {message}")
        received.append(message)

    # Subscribe before starting
    channel = "bus:tasks:backend-api"
    bus.subscribe(channel, test_callback)

    # Start listener
    bus.start()
    time.sleep(1)

    print(f"✓ Bus started with subscription to {channel}")

    # Publish task using bus method (which also publishes to Redis)
    task_id = bus.publish_task(
        agent="backend-api",
        task={"command": "test", "params": {}},
        priority=MessagePriority.HIGH
    )

    print(f"✓ Published task {task_id}")

    # Also publish directly to Redis channel to test
    test_msg = {
        'id': str(uuid.uuid4()),
        'type': 'task',
        'source': 'test',
        'target': 'backend-api',
        'payload': {'direct': True},
        'priority': 2,
        'timestamp': time.time()
    }

    r = bus.redis_client
    r.publish(channel, json.dumps(test_msg))
    print(f"✓ Published direct message to {channel}")

    # Wait for messages
    time.sleep(2)

    bus.stop()

    if received:
        print(f"✅ Success! Received {len(received)} messages")
        for msg in received:
            print(f"  - Type: {msg.type.value if hasattr(msg, 'type') else 'unknown'}")
    else:
        print("❌ Failed - No messages received")

        # Debug pubsub
        print("\nDebug - Checking Redis pubsub...")
        ps = r.pubsub()
        ps.subscribe(channel)

        # Publish test
        r.publish(channel, "test")

        # Try to get message
        msg = ps.get_message(timeout=1)
        print(f"Subscription confirmation: {msg}")

        msg = ps.get_message(timeout=1)
        print(f"Test message: {msg}")

        ps.close()

    return len(received) > 0

def main():
    """Run all message flow tests"""
    print("=" * 60)
    print("Message Flow Debugging")
    print("=" * 60)

    results = []

    # Test 1: Direct Redis
    try:
        success = test_direct_redis()
        results.append(("Direct Redis Pub/Sub", success))
    except Exception as e:
        print(f"✗ Direct Redis test failed: {e}")
        results.append(("Direct Redis Pub/Sub", False))

    # Test 2: Message Bus internals
    try:
        success = test_message_bus_internals()
        results.append(("Message Bus Internals", success))
    except Exception as e:
        print(f"✗ Message Bus test failed: {e}")
        results.append(("Message Bus Internals", False))

    # Test 3: Agent Bridge
    try:
        success = test_agent_bridge_receiving()
        results.append(("Agent Bridge Reception", success))
    except Exception as e:
        print(f"✗ Agent Bridge test failed: {e}")
        results.append(("Agent Bridge Reception", False))

    # Test 4: Fixed flow
    try:
        success = test_fixed_message_flow()
        results.append(("Fixed Message Flow", success))
    except Exception as e:
        print(f"✗ Fixed flow test failed: {e}")
        results.append(("Fixed Message Flow", False))

    # Report
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)

    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{name:30} {status}")

    passed = sum(1 for _, s in results if s)
    print("-" * 60)
    print(f"Total: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\n🎉 All message flow tests passed!")
    else:
        print(f"\n⚠️ {len(results) - passed} tests failed - check message routing")

if __name__ == "__main__":
    main()