#!/usr/bin/env python3
"""Debug workflow execution to find where it's failing"""

import sys
import os
import time
import threading
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.tmux_client import TMUXClient
from core.message_bus import get_message_bus
from core.workflow_engine import get_workflow_engine
from agents.agent_bridge import AgentBridge
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

def monitor_messages(bus):
    """Monitor all message bus activity"""
    print("\n=== MESSAGE BUS MONITOR STARTED ===\n")

    def log_message(message):
        print(f"[MESSAGE] Type: {message.type}, ID: {message.id}, Target: {message.metadata.get('target_agent', 'N/A')}")
        print(f"          Payload: {message.payload}")

    # Subscribe to all channels
    bus.subscribe("bus:tasks:*", log_message)
    bus.subscribe("bus:results:*", log_message)
    bus.subscribe("bus:events:*", log_message)

def test_workflow_debug():
    """Test workflow with detailed debugging"""
    print("\n=== WORKFLOW DEBUG TEST ===\n")

    # Setup
    tmux = TMUXClient()
    bus = get_message_bus()
    engine = get_workflow_engine()

    # Clean sessions
    for agent in ["backend-api", "supervisor"]:
        session = f"claude-{agent}"
        if tmux.session_exists(session):
            tmux.kill_session(session)
        tmux.create_session(session)
        print(f"✓ Created session: {session}")

    # Start message bus
    if not bus.running:
        bus.start()
    print("✓ Message bus started")

    # Start monitoring in background
    monitor_thread = threading.Thread(target=monitor_messages, args=(bus,))
    monitor_thread.daemon = True
    monitor_thread.start()

    # Start agent bridges
    bridges = {}
    for agent in ["backend-api", "supervisor"]:
        bridge = AgentBridge(agent)
        bridge.start()
        bridges[agent] = bridge
        print(f"✓ Started bridge: {agent}")

    time.sleep(1)

    # Define simple workflow
    workflow = {
        "name": "Debug Workflow",
        "description": "Simple workflow for debugging",
        "steps": [
            {
                "id": "step1",
                "name": "Test Step",
                "agent": "backend-api",
                "action": "echo 'Test message'",
                "params": {}
            }
        ]
    }

    print("\n1. Defining workflow...")
    workflow_id = engine.define_workflow(workflow)
    print(f"   Workflow ID: {workflow_id}")

    print("\n2. Executing workflow...")
    execution_id = engine.execute(workflow_id)
    print(f"   Execution ID: {execution_id}")

    print("\n3. Waiting for completion...")
    max_wait = 20
    start_time = time.time()

    while time.time() - start_time < max_wait:
        status = engine.get_execution_status(execution_id)
        if status:
            print(f"   Status: {status.get('status')}")

            # Show step details
            for step_id, step_data in status.get('steps', {}).items():
                print(f"     Step {step_id}: {step_data.get('status', 'unknown')}")

            if status.get('status') in ['completed', 'failed']:
                break

        time.sleep(2)

    # Check final result
    final_status = engine.get_execution_status(execution_id)
    if final_status:
        print(f"\nFinal Status: {final_status.get('status')}")
        print(f"Steps: {final_status.get('steps')}")

    # Check agent output directly
    print("\n4. Checking agent output...")
    output = tmux.capture_pane("claude-backend-api")
    print("Backend API output:")
    print(output[-500:] if len(output) > 500 else output)

    # Cleanup
    for bridge in bridges.values():
        bridge.stop()
    bus.stop()
    for agent in ["backend-api", "supervisor"]:
        tmux.kill_session(f"claude-{agent}")

    print("\n✓ Debug test complete")

if __name__ == "__main__":
    test_workflow_debug()