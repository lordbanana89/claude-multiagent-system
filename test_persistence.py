#!/usr/bin/env python3
"""Test SQLite persistence functionality"""

import sys
import os
import time
import sqlite3
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.persistence import get_persistence_manager
from core.tmux_client import TMUXClient
from core.message_bus import get_message_bus
from agents.agent_bridge import AgentBridge

def test_persistence():
    """Test persistence layer"""
    print("\n=== TESTING PERSISTENCE ===\n")

    # Get persistence manager
    pm = get_persistence_manager("data/test_persistence.db")

    # Test 1: Save and retrieve task
    print("1. Testing task persistence...")
    task_id = "test-task-001"
    pm.save_task(
        task_id=task_id,
        agent="backend-api",
        command="echo 'Test task'",
        params={"param1": "value1"},
        priority=2,
        status="pending"
    )

    task = pm.get_task(task_id)
    if task and task['task_id'] == task_id:
        print("   ✓ Task saved and retrieved")
    else:
        print("   ❌ Task persistence failed")

    # Test 2: Update task status
    print("2. Testing task status update...")
    pm.update_task_status(
        task_id=task_id,
        status="completed",
        result={"output": "Success"}
    )

    task = pm.get_task(task_id)
    if task and task['status'] == 'completed':
        print("   ✓ Task status updated")
    else:
        print("   ❌ Task status update failed")

    # Test 3: Save workflow
    print("3. Testing workflow persistence...")
    workflow_id = "test-wf-001"
    pm.save_workflow(
        workflow_id=workflow_id,
        name="Test Workflow",
        description="Test workflow for persistence",
        definition={"steps": [{"id": "s1", "action": "test"}]}
    )
    print("   ✓ Workflow saved")

    # Test 4: Save execution
    print("4. Testing execution persistence...")
    execution_id = "test-exec-001"
    pm.save_workflow_execution(
        execution_id=execution_id,
        workflow_id=workflow_id,
        status="running"
    )

    pm.save_workflow_step(
        step_id="s1",
        execution_id=execution_id,
        name="Step 1",
        agent="backend-api",
        action="echo 'Step 1'",
        status="pending"
    )
    print("   ✓ Execution and step saved")

    # Test 5: Update execution
    print("5. Testing execution update...")
    pm.update_workflow_step(
        step_id="s1",
        execution_id=execution_id,
        status="completed",
        result={"output": "Step 1 complete"}
    )

    pm.update_workflow_execution(
        execution_id=execution_id,
        status="completed",
        context={"final": "result"}
    )
    print("   ✓ Execution updated")

    # Test 6: Agent status
    print("6. Testing agent status...")
    pm.update_agent_status(
        agent="backend-api",
        status="ready",
        details={"tasks_completed": 5}
    )

    agent_status = pm.get_agent_status("backend-api")
    if agent_status and agent_status['status'] == 'ready':
        print("   ✓ Agent status saved")
    else:
        print("   ❌ Agent status failed")

    # Test 7: Event logging
    print("7. Testing event logging...")
    pm.log_event(
        event_type="task_completed",
        source="test",
        data={"task_id": task_id}
    )

    events = pm.get_recent_events(limit=5)
    if events and len(events) > 0:
        print("   ✓ Events logged")
    else:
        print("   ❌ Event logging failed")

    # Test 8: Statistics
    print("8. Testing statistics...")
    stats = pm.get_statistics()
    print(f"   Tasks: {stats.get('tasks', {})}")
    print(f"   Workflows: {stats.get('workflows', {})}")
    print(f"   Agents: {stats.get('agents', {})}")
    print("   ✓ Statistics retrieved")

    print("\n✓ Persistence tests complete")

def test_integration():
    """Test persistence integration with message bus"""
    print("\n=== TESTING PERSISTENCE INTEGRATION ===\n")

    # Setup
    tmux = TMUXClient()
    bus = get_message_bus()

    # Create session
    session = "claude-backend-api"
    if tmux.session_exists(session):
        tmux.kill_session(session)
    tmux.create_session(session)

    # Start message bus
    if not bus.running:
        bus.start()

    # Start agent bridge
    bridge = AgentBridge("backend-api")
    bridge.start()

    time.sleep(1)

    print("1. Publishing task...")
    task_id = bus.publish_task(
        agent="backend-api",
        task={"command": "echo 'Persistence test'", "params": {}}
    )
    print(f"   Task ID: {task_id}")

    # Wait for completion
    print("2. Waiting for task completion...")
    time.sleep(3)

    # Check if task was persisted
    print("3. Checking persistence...")
    pm = bus.persistence

    persisted_task = pm.get_task(task_id)
    if persisted_task:
        print(f"   ✓ Task found in SQLite: {persisted_task['status']}")
    else:
        print("   ❌ Task not found in SQLite")

    # Check statistics
    stats = pm.get_statistics()
    print(f"4. Statistics: {stats.get('tasks', {})}")

    # Cleanup
    bridge.stop()
    bus.stop()
    tmux.kill_session(session)

    print("\n✓ Integration test complete")

def main():
    print("=" * 60)
    print("PERSISTENCE TEST")
    print("=" * 60)

    test_persistence()
    test_integration()

    print("\n" + "=" * 60)
    print("ALL PERSISTENCE TESTS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()