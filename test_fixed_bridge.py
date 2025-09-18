#!/usr/bin/env python3
"""Test the fixed agent bridge"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.agent_bridge_fixed import FixedAgentBridge, AgentTask
from core.message_bus import get_message_bus
from core.tmux_client import TMUXClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fixed_bridge():
    """Test the fixed bridge implementation"""
    print("\n=== TESTING FIXED AGENT BRIDGE ===\n")

    # Setup
    tmux = TMUXClient()
    bus = get_message_bus()

    # Clean start
    session = "claude-backend-api"
    if tmux.session_exists(session):
        tmux.kill_session(session)
    tmux.create_session(session)
    print(f"✓ Created session: {session}")

    # Start message bus
    if not bus.running:
        bus.start()
    print("✓ Message bus started")

    # Create and start fixed bridge
    bridge = FixedAgentBridge("backend-api")
    bridge.start()
    print("✓ Fixed bridge started")

    # Test 1: Simple echo command
    print("\nTest 1: Simple echo command")
    task1 = AgentTask(
        id="test-001",
        agent="backend-api",
        command="echo 'Hello from fixed bridge!'",
        params={},
        timeout=10
    )

    # Execute directly (not through message bus)
    bridge._execute_task(task1)

    # Check result
    status = bus.get_task_status(task1.id)
    if status and status['status'] == 'completed':
        print("✅ Task 1 completed successfully!")
        print(f"   Duration: {status.get('completed_at', 0) - status.get('created_at', 0):.2f}s")
    else:
        print(f"❌ Task 1 failed: {status}")

    time.sleep(1)

    # Test 2: Multi-line command
    print("\nTest 2: Multi-line output")
    task2 = AgentTask(
        id="test-002",
        agent="backend-api",
        command="for i in 1 2 3; do echo \"Line $i\"; done",
        params={},
        timeout=10
    )

    bridge._execute_task(task2)

    status = bus.get_task_status(task2.id)
    if status and status['status'] == 'completed':
        print("✅ Task 2 completed successfully!")
        result = status.get('result', {})
        if isinstance(result, str):
            import json
            try:
                result = json.loads(result)
            except:
                pass
        if isinstance(result, dict) and 'output' in result:
            output = result['output']
            if 'lines' in output:
                print(f"   Output lines: {len(output['lines'])}")
                for line in output['lines'][:3]:
                    print(f"     - {line}")
    else:
        print(f"❌ Task 2 failed: {status}")

    time.sleep(1)

    # Test 3: Command with error
    print("\nTest 3: Command that fails")
    task3 = AgentTask(
        id="test-003",
        agent="backend-api",
        command="this_command_does_not_exist",
        params={},
        timeout=5
    )

    bridge._execute_task(task3)

    status = bus.get_task_status(task3.id)
    if status:
        if status['status'] == 'failed':
            print("✅ Task 3 correctly detected as failed")
        else:
            print(f"❌ Task 3 should have failed but got: {status['status']}")
    else:
        print("❌ No status for task 3")

    # Cleanup
    bridge.stop()
    bus.stop()
    tmux.kill_session(session)
    print("\n✓ Cleanup complete")

def test_through_message_bus():
    """Test task execution through message bus"""
    print("\n=== TESTING THROUGH MESSAGE BUS ===\n")

    # Setup
    tmux = TMUXClient()
    bus = get_message_bus()

    # Clean sessions
    for agent in ["backend-api", "database", "supervisor"]:
        session = f"claude-{agent}"
        if tmux.session_exists(session):
            tmux.kill_session(session)
        tmux.create_session(session)
        print(f"✓ Created session: {session}")

    # Start message bus
    if not bus.running:
        bus.start()
    print("✓ Message bus started")

    # Start multiple bridges
    bridges = {}
    for agent in ["backend-api", "database", "supervisor"]:
        bridge = FixedAgentBridge(agent)
        bridge.start()
        bridges[agent] = bridge
        print(f"✓ Started bridge: {agent}")

    time.sleep(1)

    # Submit tasks through message bus
    print("\nSubmitting tasks through message bus...")
    task_ids = []

    for i, agent in enumerate(["backend-api", "database", "supervisor"]):
        task_id = bus.publish_task(
            agent=agent,
            task={
                "command": f"echo '{agent.upper()} executing task {i+1}'",
                "params": {},
                "timeout": 10
            }
        )
        task_ids.append((agent, task_id))
        print(f"  Submitted to {agent}: {task_id}")

    # Monitor completion
    print("\nMonitoring task completion...")
    max_wait = 15
    start_time = time.time()
    completed = []

    while time.time() - start_time < max_wait and len(completed) < len(task_ids):
        for agent, task_id in task_ids:
            if task_id not in completed:
                status = bus.get_task_status(task_id)
                if status and status['status'] == 'completed':
                    completed.append(task_id)
                    print(f"  ✅ {agent} task completed")
                elif status and status['status'] == 'failed':
                    completed.append(task_id)
                    print(f"  ❌ {agent} task failed")
        time.sleep(1)

    # Results
    print(f"\nResults: {len(completed)}/{len(task_ids)} tasks completed")
    if len(completed) == len(task_ids):
        print("✅ All tasks processed successfully!")
    else:
        print("❌ Some tasks did not complete")

    # Cleanup
    for bridge in bridges.values():
        bridge.stop()
    bus.stop()
    for agent in ["backend-api", "database", "supervisor"]:
        tmux.kill_session(f"claude-{agent}")

    print("\n✓ Cleanup complete")

def main():
    """Run all tests"""
    print("=" * 60)
    print("TESTING FIXED AGENT BRIDGE")
    print("=" * 60)

    test_fixed_bridge()
    test_through_message_bus()

    print("\n" + "=" * 60)
    print("TESTS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()