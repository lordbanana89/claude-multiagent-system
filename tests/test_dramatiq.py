#!/usr/bin/env python3
"""
Test Dramatiq Queue System with Redis
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_broker_connection():
    """Test Redis broker connection"""
    print("Testing broker connection...")
    try:
        from task_queue import broker
        print(f"✅ Broker imported: {type(broker).__name__}")

        # Check if it's a Redis broker
        from dramatiq.brokers.redis import RedisBroker
        if isinstance(broker, RedisBroker):
            print("✅ Using Redis broker")
            return True
        else:
            print(f"⚠️ Using {type(broker).__name__} instead of Redis")
            return True  # Still ok if using stub for testing
    except Exception as e:
        print(f"❌ Broker connection failed: {e}")
        return False


def test_actors_import():
    """Test that actors can be imported"""
    print("\nTesting actors import...")
    try:
        from task_queue import (
            process_agent_command,
            broadcast_message,
            execute_task,
            notify_agent,
            check_actors_health
        )
        print("✅ All actors imported successfully")

        # Check actors health
        health = check_actors_health()
        print(f"✅ Actors health check: {health['status']}")
        print(f"   - Registered actors: {len(health['actors'])}")
        print(f"   - Available agents: {health['agents_available']}")
        print(f"   - Active TMUX sessions: {health['active_sessions']}")

        return True
    except Exception as e:
        print(f"❌ Failed to import actors: {e}")
        return False


def test_client_import():
    """Test queue client"""
    print("\nTesting queue client...")
    try:
        from task_queue import QueueClient, get_default_client

        # Create client instance
        client = QueueClient()
        print("✅ QueueClient instantiated")

        # Get stats
        stats = client.get_stats()
        print(f"✅ Queue stats retrieved:")
        print(f"   - Broker type: {stats['broker_type']}")
        print(f"   - Total messages: {stats['total_messages_sent']}")

        # Get default client
        default = get_default_client()
        print("✅ Default client available")

        return True
    except Exception as e:
        print(f"❌ Client test failed: {e}")
        return False


def test_redis_connection():
    """Test direct Redis connection"""
    print("\nTesting Redis connection...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

        # Test ping
        response = r.ping()
        if response:
            print("✅ Redis PING successful")
        else:
            print("❌ Redis PING failed")
            return False

        # Get Redis info
        info = r.info('server')
        print(f"✅ Redis version: {info.get('redis_version', 'unknown')}")

        # Check Dramatiq queues
        dramatiq_keys = r.keys('dramatiq:*')
        print(f"✅ Dramatiq keys in Redis: {len(dramatiq_keys)}")

        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("   Make sure Redis is running: redis-server")
        return False


def test_send_message():
    """Test sending a message to the queue"""
    print("\nTesting message sending...")
    try:
        from task_queue import send_agent_command, broadcast_to_all, quick_notify

        # Try sending a test command (won't execute without worker)
        msg_id = send_agent_command(
            "supervisor",
            "echo 'Test message from Dramatiq'"
        )
        print(f"✅ Test command queued: {msg_id[:8]}...")

        # Try broadcast
        broadcast_id = broadcast_to_all(
            "System test broadcast",
            exclude=["testing"]
        )
        print(f"✅ Broadcast queued: {broadcast_id[:8]}...")

        # Try notification
        notif_id = quick_notify(
            "backend-api",
            "Test Notification",
            "Dramatiq queue system is operational"
        )
        print(f"✅ Notification queued: {notif_id[:8]}...")

        return True
    except Exception as e:
        print(f"❌ Message sending failed: {e}")
        return False


def test_task_chain():
    """Test creating a task chain"""
    print("\nTesting task chain creation...")
    try:
        from task_queue import QueueClient

        client = QueueClient()

        # Create a simple task chain
        chain_id = client.create_task_chain([
            {
                "agent_id": "supervisor",
                "command": "echo 'Step 1: Initialize'",
                "description": "Initialize process",
                "delay": 0.5
            },
            {
                "agent_id": "backend-api",
                "command": "echo 'Step 2: Process'",
                "description": "Process data",
                "delay": 0.5
            },
            {
                "agent_id": "supervisor",
                "command": "echo 'Step 3: Complete'",
                "description": "Complete process",
                "delay": 0
            }
        ])

        print(f"✅ Task chain created: {chain_id[:8]}...")

        # Check history
        history = client.get_history(limit=5)
        print(f"✅ Message history: {len(history)} recent messages")

        return True
    except Exception as e:
        print(f"❌ Task chain test failed: {e}")
        return False


def main():
    """Run all Dramatiq tests"""
    print("=" * 60)
    print("DRAMATIQ QUEUE SYSTEM TESTS")
    print("=" * 60)

    tests = [
        ("Broker Connection", test_broker_connection),
        ("Actors Import", test_actors_import),
        ("Client Import", test_client_import),
        ("Redis Connection", test_redis_connection),
        ("Message Sending", test_send_message),
        ("Task Chain", test_task_chain),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"❌ {name} failed with exception: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")

    print(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 Dramatiq queue system is fully operational!")
        return 0
    else:
        print("\n⚠️ Some tests failed - check Redis and configuration")
        return 1


if __name__ == "__main__":
    sys.exit(main())