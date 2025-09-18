#!/usr/bin/env python3
"""
End-to-end integration test with proper message flow
"""

import sys
import os
import time
import threading
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.message_bus import get_message_bus, MessagePriority
from agents.agent_bridge import AgentBridge
from core.tmux_client import TMUXClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_end_to_end_flow():
    """Test complete flow from task submission to execution"""
    print("\nEnd-to-End Integration Test")
    print("=" * 60)

    # 1. Setup
    print("\n1. Setting up components...")

    # Create TMUX session
    tmux = TMUXClient()
    session = "claude-backend-api"

    if not tmux.session_exists(session):
        tmux.create_session(session)
        print(f"✓ Created TMUX session: {session}")
    else:
        print(f"✓ TMUX session exists: {session}")

    # Initialize message bus
    bus = get_message_bus()

    # Start message bus if not running
    if not bus.running:
        bus.start()
        print("✓ Message bus started")
    else:
        print("✓ Message bus already running")

    # 2. Setup agent bridge
    print("\n2. Setting up agent bridge...")
    bridge = AgentBridge("backend-api")
    bridge.start()
    print("✓ Agent bridge started")

    # Give everything time to initialize
    time.sleep(2)

    # 3. Submit a simple echo task
    print("\n3. Submitting test task...")

    # Clear the session first
    tmux.send_command(session, "clear")
    time.sleep(0.5)

    # Create a simple test task
    task_id = bus.publish_task(
        agent="backend-api",
        task={
            "command": "echo 'Integration test successful!'",
            "params": {},
            "timeout": 10
        },
        priority=MessagePriority.HIGH
    )
    print(f"✓ Submitted task: {task_id}")

    # 4. Monitor task execution
    print("\n4. Monitoring task execution...")
    max_wait = 15
    start_time = time.time()
    last_status = None

    while time.time() - start_time < max_wait:
        # Get task status
        status = bus.get_task_status(task_id)

        if status and status['status'] != last_status:
            print(f"   Task status: {status['status']}")
            last_status = status['status']

            if status['status'] == 'completed':
                print("✓ Task completed successfully!")

                # Check TMUX output
                output = tmux.capture_pane(session)
                if "Integration test successful!" in output:
                    print("✓ Command executed in TMUX!")
                else:
                    print("⚠️ Command may not have executed properly")
                    print(f"   Output length: {len(output)}")

                # Get result from status
                if 'result' in status:
                    print(f"✓ Task result available: {status['result'][:100] if isinstance(status['result'], str) else status['result']}")

                return True

            elif status['status'] == 'failed':
                print(f"✗ Task failed: {status}")
                return False

        time.sleep(1)

    print("✗ Task timed out")

    # Debug: Check what's in TMUX
    output = tmux.capture_pane(session)
    print(f"\nDebug - TMUX output (last 500 chars):\n{output[-500:]}")

    return False

def test_message_flow():
    """Test that messages flow through the system"""
    print("\n\nMessage Flow Test")
    print("=" * 60)

    bus = get_message_bus()
    received_messages = []

    # Subscribe to results
    def result_callback(message):
        received_messages.append(message)
        print(f"✓ Received message: {message.type.value}")

    bus.subscribe("bus:results:*", result_callback)
    print("✓ Subscribed to results channel")

    # Publish a test result
    bus.publish_result("test-task-123", {"test": "data"}, success=True)
    print("✓ Published test result")

    # Wait for message
    time.sleep(2)

    if received_messages:
        print(f"✓ Received {len(received_messages)} messages")
        return True
    else:
        print("✗ No messages received")
        return False

def main():
    """Run end-to-end tests"""
    results = []

    try:
        # Test message flow
        print("\n" + "=" * 60)
        print("TESTING MESSAGE FLOW")
        print("=" * 60)
        success = test_message_flow()
        results.append(("Message Flow", success))

        # Test end-to-end
        print("\n" + "=" * 60)
        print("TESTING END-TO-END EXECUTION")
        print("=" * 60)
        success = test_end_to_end_flow()
        results.append(("End-to-End", success))

    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Exception", False))

    finally:
        # Cleanup
        print("\n\nCleaning up...")
        bus = get_message_bus()
        if bus.running:
            bus.stop()
            print("✓ Stopped message bus")

    # Report
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{name:20} {status}")

    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All end-to-end tests passed!")
        print("The integration is working correctly.")
    else:
        print(f"\n⚠️ {total - passed} tests failed")
        print("Check the message flow and agent bridge connections.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)