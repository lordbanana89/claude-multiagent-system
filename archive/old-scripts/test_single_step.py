#!/usr/bin/env python3
"""Test single step at a time"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.tmux_client import TMUXClient
from core.message_bus import get_message_bus
from core.workflow_engine import get_workflow_engine
from agents.agent_bridge import AgentBridge

def test_two_steps():
    """Test workflow with two dependent steps"""
    print("\n=== TWO STEP WORKFLOW TEST ===\n")

    # Setup
    tmux = TMUXClient()
    bus = get_message_bus()
    engine = get_workflow_engine()

    # Create sessions
    for agent in ["backend-api", "supervisor"]:
        session = f"claude-{agent}"
        if tmux.session_exists(session):
            tmux.kill_session(session)
        tmux.create_session(session)

    # Start message bus
    if not bus.running:
        bus.start()

    # Start bridges
    bridges = {}
    for agent in ["backend-api", "supervisor"]:
        bridge = AgentBridge(agent)
        bridge.start()
        bridges[agent] = bridge

    time.sleep(1)

    # Define workflow with 2 steps
    workflow = {
        "name": "Two Step Test",
        "description": "Test with dependencies",
        "steps": [
            {
                "id": "step1",
                "name": "First Step",
                "agent": "supervisor",
                "action": "echo 'Step 1 complete'",
                "params": {}
            },
            {
                "id": "step2",
                "name": "Second Step",
                "agent": "backend-api",
                "action": "echo 'Step 2 complete'",
                "params": {},
                "depends_on": ["step1"]
            }
        ]
    }

    workflow_id = engine.define_workflow(workflow)
    print(f"Workflow defined: {workflow_id}")

    execution_id = engine.execute(workflow_id)
    print(f"Execution started: {execution_id}\n")

    # Monitor execution
    for i in range(20):
        status = engine.get_execution_status(execution_id)
        w_status = status.get('status', 'unknown')
        steps = status.get('steps', {})

        print(f"[{i:2}] Workflow: {w_status}")
        for step_id in ['step1', 'step2']:
            if step_id in steps:
                step_status = steps[step_id].get('status', 'unknown')
                print(f"     {step_id}: {step_status}")

        if w_status in ['completed', 'failed']:
            print(f"\n✓ Workflow {w_status}!")
            break

        time.sleep(1)

    # Show output from both agents
    print("\nAgent outputs:")
    print("Supervisor:")
    output = tmux.capture_pane("claude-supervisor")
    for line in output.strip().split('\n')[-5:]:
        print(f"  {line}")

    print("\nBackend API:")
    output = tmux.capture_pane("claude-backend-api")
    for line in output.strip().split('\n')[-5:]:
        print(f"  {line}")

    # Cleanup
    for bridge in bridges.values():
        bridge.stop()
    bus.stop()
    for agent in ["backend-api", "supervisor"]:
        tmux.kill_session(f"claude-{agent}")

    print("\n✓ Test complete")

if __name__ == "__main__":
    test_two_steps()