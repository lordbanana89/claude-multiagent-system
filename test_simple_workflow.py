#!/usr/bin/env python3
"""Test simplest possible workflow execution"""

import sys
import os
import time
import redis
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.tmux_client import TMUXClient
from core.message_bus import get_message_bus
from core.workflow_engine import get_workflow_engine
from agents.agent_bridge import AgentBridge

def test_direct():
    """Test workflow execution with direct monitoring"""
    print("\n=== DIRECT WORKFLOW TEST ===\n")

    # Setup
    tmux = TMUXClient()
    bus = get_message_bus()
    engine = get_workflow_engine()
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)

    # Create session
    session = "claude-backend-api"
    if tmux.session_exists(session):
        tmux.kill_session(session)
    tmux.create_session(session)
    print(f"✓ Created session: {session}")

    # Start message bus
    if not bus.running:
        bus.start()
    print("✓ Message bus started")

    # Start agent bridge
    bridge = AgentBridge("backend-api")
    bridge.start()
    print("✓ Started bridge: backend-api")

    time.sleep(1)

    # Define and execute simple workflow
    workflow = {
        "name": "Test",
        "description": "Test",
        "steps": [{
            "id": "s1",
            "name": "Step 1",
            "agent": "backend-api",
            "action": "echo 'Hello World'",
            "params": {}
        }]
    }

    workflow_id = engine.define_workflow(workflow)
    print(f"\n1. Workflow defined: {workflow_id}")

    execution_id = engine.execute(workflow_id)
    print(f"2. Execution started: {execution_id}")

    # Monitor both workflow status AND task status directly in Redis
    print("\n3. Monitoring...")
    for i in range(15):
        # Get workflow status
        w_status = engine.get_execution_status(execution_id)
        step_status = w_status.get('steps', {}).get('s1', {}).get('status', 'unknown')

        # Find the task ID from Redis
        task_keys = r.keys("task:*")
        task_statuses = []
        for key in task_keys:
            task_data = r.hgetall(key)
            task_id = key.split(":")[-1]
            task_statuses.append(f"{task_id[:8]}:{task_data.get('status', 'unknown')}")

        print(f"   [{i}] Workflow step: {step_status}, Redis tasks: {task_statuses}")

        if w_status.get('status') in ['completed', 'failed']:
            print(f"\nFinal workflow status: {w_status.get('status')}")
            break

        time.sleep(1)

    # Check agent output
    print("\n4. Agent output:")
    output = tmux.capture_pane(session)
    lines = output.strip().split('\n')[-10:]
    for line in lines:
        print(f"   {line}")

    # Cleanup
    bridge.stop()
    bus.stop()
    tmux.kill_session(session)

    print("\n✓ Test complete")

if __name__ == "__main__":
    test_direct()