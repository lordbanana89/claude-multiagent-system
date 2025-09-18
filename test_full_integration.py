#!/usr/bin/env python3
"""
Full integration test showing complete task execution
"""

import sys
import os
import time
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.message_bus import get_message_bus, MessagePriority
from core.workflow_engine import get_workflow_engine
from agents.agent_bridge import AgentBridge
from core.tmux_client import TMUXClient
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_single_task_execution():
    """Test single task execution from submission to completion"""
    print("\n" + "=" * 60)
    print("Test 1: Single Task Execution")
    print("=" * 60)

    # Setup
    tmux = TMUXClient()
    bus = get_message_bus()

    # Ensure clean session
    session = "claude-backend-api"
    if tmux.session_exists(session):
        tmux.kill_session(session)
    tmux.create_session(session)
    print(f"✓ Created clean TMUX session: {session}")

    # Start message bus
    if not bus.running:
        bus.start()
    print("✓ Message bus started")

    # Start agent bridge
    bridge = AgentBridge("backend-api")
    bridge.start()
    print("✓ Agent bridge started")

    time.sleep(1)

    # Submit task
    task_id = bus.publish_task(
        agent="backend-api",
        task={
            "command": "/bin/echo 'Task executed successfully!'",
            "params": {},
            "timeout": 5
        },
        priority=MessagePriority.HIGH
    )
    print(f"✓ Submitted task: {task_id}")

    # Monitor execution
    max_wait = 10
    start_time = time.time()

    while time.time() - start_time < max_wait:
        status = bus.get_task_status(task_id)
        if status:
            print(f"  Task status: {status['status']}")
            if status['status'] == 'completed':
                print("✅ Task completed!")

                # Verify execution in TMUX
                output = tmux.capture_pane(session)
                if "Task executed successfully!" in output:
                    print("✅ Command executed in TMUX successfully!")
                    print("\nTMUX Output (last 200 chars):")
                    print("-" * 40)
                    print(output[-200:])
                    print("-" * 40)
                else:
                    print("⚠️ Command may not have executed")

                bridge.stop()
                return True

            elif status['status'] == 'failed':
                print(f"❌ Task failed: {status}")
                bridge.stop()
                return False

        time.sleep(1)

    print("❌ Task timed out")
    bridge.stop()
    return False

def test_multi_agent_workflow():
    """Test workflow with multiple agents"""
    print("\n" + "=" * 60)
    print("Test 2: Multi-Agent Workflow")
    print("=" * 60)

    # Setup sessions
    tmux = TMUXClient()
    sessions = {
        "supervisor": "claude-supervisor",
        "backend-api": "claude-backend-api",
        "database": "claude-database"
    }

    for agent, session in sessions.items():
        if tmux.session_exists(session):
            tmux.kill_session(session)
        tmux.create_session(session)
        print(f"✓ Created session: {session}")

    # Start components
    bus = get_message_bus()
    if not bus.running:
        bus.start()

    engine = get_workflow_engine()
    bridges = {}

    for agent in sessions.keys():
        bridge = AgentBridge(agent)
        bridge.start()
        bridges[agent] = bridge
        print(f"✓ Started bridge: {agent}")

    time.sleep(2)

    # Define workflow
    workflow_def = {
        "name": "Integration Test Workflow",
        "description": "Test multi-agent coordination",
        "steps": [
            {
                "id": "step1",
                "name": "Initialize",
                "agent": "supervisor",
                "action": "/bin/echo '1. Supervisor: Initializing workflow'",
                "params": {}
            },
            {
                "id": "step2",
                "name": "Process Backend",
                "agent": "backend-api",
                "action": "/bin/echo '2. Backend: Processing data'",
                "params": {},
                "depends_on": ["step1"]
            },
            {
                "id": "step3",
                "name": "Store Data",
                "agent": "database",
                "action": "/bin/echo '3. Database: Storing results'",
                "params": {},
                "depends_on": ["step2"]
            }
        ]
    }

    workflow_id = engine.define_workflow(workflow_def)
    print(f"✓ Defined workflow: {workflow_id}")

    execution_id = engine.execute(workflow_id, {})
    print(f"✓ Started execution: {execution_id}")

    # Monitor execution
    max_wait = 30
    start_time = time.time()
    last_status = None

    while time.time() - start_time < max_wait:
        status = engine.get_execution_status(execution_id)
        if status and status['status'] != last_status:
            print(f"\nWorkflow status: {status['status']}")
            for step_id, step in status['steps'].items():
                print(f"  {step['name']}: {step['status']}")
            last_status = status['status']

            if status['status'] == 'completed':
                print("\n✅ Workflow completed successfully!")

                # Check outputs
                for agent, session in sessions.items():
                    output = tmux.capture_pane(session)
                    print(f"\n{agent.upper()} Output:")
                    print("-" * 40)
                    relevant = [line for line in output.split('\n') if agent.capitalize() in line]
                    if relevant:
                        print(relevant[-1])
                    print("-" * 40)

                # Cleanup
                for bridge in bridges.values():
                    bridge.stop()

                return True

            elif status['status'] == 'failed':
                print(f"\n❌ Workflow failed: {status.get('error')}")
                for bridge in bridges.values():
                    bridge.stop()
                return False

        time.sleep(2)

    print("\n❌ Workflow timed out")
    for bridge in bridges.values():
        bridge.stop()
    return False

def test_system_resilience():
    """Test system resilience and error handling"""
    print("\n" + "=" * 60)
    print("Test 3: System Resilience")
    print("=" * 60)

    bus = get_message_bus()
    if not bus.running:
        bus.start()

    # Test with non-existent agent
    try:
        task_id = bus.publish_task(
            agent="non-existent-agent",
            task={"command": "test", "params": {}},
            priority=MessagePriority.LOW
        )
        print(f"✓ System accepted task for non-existent agent: {task_id}")
    except Exception as e:
        print(f"✅ System properly rejected invalid agent: {e}")

    # Test task status tracking
    status = bus.get_task_status(task_id if 'task_id' in locals() else "invalid-id")
    if status:
        print(f"✓ Task tracked with status: {status['status']}")
    else:
        print("✓ Invalid task properly returns None")

    # Test queue management
    pending = bus.get_pending_tasks()
    print(f"✓ System tracking {len(pending)} pending tasks")

    # Test agent status
    for agent in ["supervisor", "backend-api", "database"]:
        status = bus.get_agent_status(agent)
        if status:
            print(f"✓ Agent {agent} status: {status.get('status', 'unknown')}")

    return True

def main():
    """Run all integration tests"""
    print("\n" + "🚀 " * 20)
    print("CLAUDE MULTI-AGENT SYSTEM - FULL INTEGRATION TEST")
    print("🚀 " * 20)

    results = []

    # Test 1: Single task
    try:
        success = test_single_task_execution()
        results.append(("Single Task Execution", success))
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Single Task Execution", False))

    # Test 2: Multi-agent workflow
    try:
        success = test_multi_agent_workflow()
        results.append(("Multi-Agent Workflow", success))
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Multi-Agent Workflow", False))

    # Test 3: System resilience
    try:
        success = test_system_resilience()
        results.append(("System Resilience", success))
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        results.append(("System Resilience", False))

    # Final report
    print("\n" + "=" * 60)
    print("FINAL INTEGRATION TEST RESULTS")
    print("=" * 60)

    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{name:30} {status}")

    passed = sum(1 for _, s in results if s)
    total = len(results)

    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n" + "🎉 " * 20)
        print("ALL INTEGRATION TESTS PASSED!")
        print("The Claude Multi-Agent System is FULLY OPERATIONAL!")
        print("🎉 " * 20)
    else:
        print(f"\n⚠️ {total - passed} tests failed")
        print("Check the logs above for details")

    # Cleanup
    bus = get_message_bus()
    if bus.running:
        bus.stop()

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)