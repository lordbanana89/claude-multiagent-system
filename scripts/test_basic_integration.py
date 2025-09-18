#!/usr/bin/env python3
"""
Basic integration test for core components
Tests individual pieces before full integration
"""

import sys
import os
import time
import redis
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_redis_connection():
    """Test Redis connectivity"""
    print("\n1. Testing Redis Connection...")
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        print("✓ Redis connected successfully")

        # Test pub/sub
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        assert value == 'test_value'
        r.delete('test_key')
        print("✓ Redis read/write working")
        return True
    except Exception as e:
        print(f"✗ Redis error: {e}")
        return False

def test_tmux_sessions():
    """Test TMUX session creation"""
    print("\n2. Testing TMUX Sessions...")
    try:
        from core.tmux_client import TMUXClient
        from config.settings import AGENT_SESSIONS

        client = TMUXClient()

        # Check/create one test session
        test_session = "claude-backend-api"
        if not client.session_exists(test_session):
            client.create_session(test_session)
            print(f"✓ Created session: {test_session}")
        else:
            print(f"✓ Session exists: {test_session}")

        # Send test command
        client.send_command(test_session, "echo 'Test message'")
        print("✓ Sent command to TMUX session")

        # Capture output
        time.sleep(1)
        output = client.capture_pane(test_session)
        if output:
            print(f"✓ Captured output from session (length: {len(output)})")

        return True
    except Exception as e:
        print(f"✗ TMUX error: {e}")
        return False

def test_message_bus():
    """Test message bus basic operations"""
    print("\n3. Testing Message Bus...")
    try:
        from core.message_bus import UnifiedMessageBus, MessagePriority

        bus = UnifiedMessageBus()

        # Test basic publishing
        task_id = bus.publish_task(
            agent="backend-api",
            task={"command": "test", "params": {}},
            priority=MessagePriority.NORMAL
        )
        print(f"✓ Published task: {task_id}")

        # Check task status
        status = bus.get_task_status(task_id)
        assert status is not None
        assert status['status'] == 'pending'
        print(f"✓ Task status retrieved: {status['status']}")

        # Update agent status
        bus.update_agent_status("backend-api", "ready", {"test": True})
        agent_status = bus.get_agent_status("backend-api")
        assert agent_status is not None
        print(f"✓ Agent status updated: {agent_status['status']}")

        return True
    except Exception as e:
        print(f"✗ Message bus error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_workflow():
    """Test workflow engine with simple workflow"""
    print("\n4. Testing Workflow Engine...")
    try:
        from core.workflow_engine import WorkflowEngine

        engine = WorkflowEngine()

        # Define simple workflow
        workflow_def = {
            "name": "Simple Test",
            "description": "Basic workflow test",
            "steps": [
                {
                    "id": "step1",
                    "name": "Echo Test",
                    "agent": "backend-api",
                    "action": "echo 'test'",
                    "params": {}
                }
            ]
        }

        workflow_id = engine.define_workflow(workflow_def)
        print(f"✓ Defined workflow: {workflow_id}")

        # Check workflow exists
        assert workflow_id in engine.workflows
        print(f"✓ Workflow stored correctly")

        return True
    except Exception as e:
        print(f"✗ Workflow engine error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_bridge_init():
    """Test agent bridge initialization"""
    print("\n5. Testing Agent Bridge...")
    try:
        from agents.agent_bridge import AgentBridge
        from core.tmux_client import TMUXClient

        # Ensure session exists
        client = TMUXClient()
        if not client.session_exists("claude-backend-api"):
            client.create_session("claude-backend-api")

        # Create bridge
        bridge = AgentBridge("backend-api")
        print("✓ Agent bridge created")

        # Start bridge
        bridge.start()
        print("✓ Agent bridge started")

        # Stop bridge
        time.sleep(1)
        bridge.stop()
        print("✓ Agent bridge stopped")

        return True
    except Exception as e:
        print(f"✗ Agent bridge error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all basic tests"""
    print("=" * 60)
    print("Basic Integration Tests")
    print("=" * 60)

    results = []

    # Run tests
    tests = [
        ("Redis Connection", test_redis_connection),
        ("TMUX Sessions", test_tmux_sessions),
        ("Message Bus", test_message_bus),
        ("Workflow Engine", test_simple_workflow),
        ("Agent Bridge", test_agent_bridge_init)
    ]

    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ {name} failed with exception: {e}")
            results.append((name, False))

    # Report results
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{name:20} {status}")

    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All basic tests passed! System components working.")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Check components above.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)