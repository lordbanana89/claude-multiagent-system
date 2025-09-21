#!/usr/bin/env python3
"""End-to-end workflow test"""

import sys
import os
import time
import requests
import json
import subprocess
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.tmux_client import TMUXClient
from core.message_bus import get_message_bus
from agents.agent_bridge import AgentBridge

def setup_system():
    """Setup complete system for workflow test"""
    print("\n=== SETTING UP SYSTEM ===\n")

    tmux = TMUXClient()
    bus = get_message_bus()

    # Create TMUX sessions
    agents = ["backend-api", "database", "supervisor"]
    for agent in agents:
        session = f"claude-{agent}"
        if tmux.session_exists(session):
            tmux.kill_session(session)
        tmux.create_session(session)
        print(f"✓ Created session: {session}")

    # Start message bus
    if not bus.running:
        bus.start()
    print("✓ Message bus started")

    # Start agent bridges
    bridges = {}
    for agent in agents:
        bridge = AgentBridge(agent)
        bridge.start()
        bridges[agent] = bridge
        print(f"✓ Started bridge: {agent}")

    # Start API Gateway
    print("\nStarting API Gateway...")
    api_process = subprocess.Popen(
        ["python3", "-m", "uvicorn", "api.unified_gateway:app", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)

    # Verify API is running
    try:
        resp = requests.get("http://localhost:8000/health")
        if resp.status_code == 200:
            print("✓ API Gateway started")
    except:
        print("⚠️ API Gateway may not be fully ready")

    return tmux, bus, bridges, api_process

def test_simple_workflow():
    """Test a simple multi-step workflow"""
    print("\n=== TESTING SIMPLE WORKFLOW ===\n")

    # Define workflow
    workflow_def = {
        "name": "Simple Test Workflow",
        "description": "Test workflow with dependencies",
        "steps": [
            {
                "id": "step1",
                "name": "Initialize",
                "agent": "supervisor",
                "action": "echo 'Starting workflow'",
                "params": {}
            },
            {
                "id": "step2",
                "name": "Backend Processing",
                "agent": "backend-api",
                "action": "echo 'Processing data'",
                "params": {},
                "depends_on": ["step1"]
            },
            {
                "id": "step3",
                "name": "Database Operation",
                "agent": "database",
                "action": "echo 'Storing results'",
                "params": {},
                "depends_on": ["step2"]
            },
            {
                "id": "step4",
                "name": "Finalize",
                "agent": "supervisor",
                "action": "echo 'Workflow complete'",
                "params": {},
                "depends_on": ["step3"]
            }
        ]
    }

    # Define workflow via API
    print("1. Defining workflow...")
    resp = requests.post("http://localhost:8000/workflows/define", json=workflow_def)
    if resp.status_code == 200:
        workflow_id = resp.json().get("workflow_id")
        print(f"   ✓ Workflow defined: {workflow_id}")
    else:
        print(f"   ❌ Failed to define workflow: {resp.status_code}")
        return False

    # Execute workflow
    print("2. Executing workflow...")
    exec_data = {"workflow_id": workflow_id, "params": {}}
    resp = requests.post("http://localhost:8000/workflows/execute", json=exec_data)

    if resp.status_code == 200:
        execution_id = resp.json().get("execution_id")
        print(f"   ✓ Execution started: {execution_id}")
    else:
        print(f"   ❌ Failed to execute workflow: {resp.status_code}")
        return False

    # Monitor execution
    print("3. Monitoring execution...")
    max_wait = 30
    start_time = time.time()
    last_status = None

    while time.time() - start_time < max_wait:
        resp = requests.get(f"http://localhost:8000/workflows/executions/{execution_id}")

        if resp.status_code == 200:
            data = resp.json()
            status = data.get("status", "unknown")

            if status != last_status:
                print(f"   Status: {status}")
                last_status = status

                # Show step progress
                steps = data.get("steps", {})
                for step_id, step_status in steps.items():
                    if isinstance(step_status, dict):
                        step_state = step_status.get("status", "pending")
                        print(f"     - {step_id}: {step_state}")

            if status in ["completed", "failed"]:
                if status == "completed":
                    print("   ✓ Workflow completed successfully!")
                    return True
                else:
                    print(f"   ❌ Workflow failed: {data.get('error')}")
                    return False

        time.sleep(2)

    print("   ⚠️ Workflow timed out")
    return False

def test_parallel_workflow():
    """Test workflow with parallel execution"""
    print("\n=== TESTING PARALLEL WORKFLOW ===\n")

    workflow_def = {
        "name": "Parallel Test Workflow",
        "description": "Test parallel task execution",
        "steps": [
            {
                "id": "init",
                "name": "Initialize",
                "agent": "supervisor",
                "action": "echo 'Starting parallel tasks'",
                "params": {}
            },
            {
                "id": "parallel1",
                "name": "Backend Task",
                "agent": "backend-api",
                "action": "echo 'Backend processing' && sleep 2 && echo 'Backend done'",
                "params": {},
                "depends_on": ["init"]
            },
            {
                "id": "parallel2",
                "name": "Database Task",
                "agent": "database",
                "action": "echo 'Database processing' && sleep 2 && echo 'Database done'",
                "params": {},
                "depends_on": ["init"]
            },
            {
                "id": "combine",
                "name": "Combine Results",
                "agent": "supervisor",
                "action": "echo 'Combining results from parallel tasks'",
                "params": {},
                "depends_on": ["parallel1", "parallel2"]
            }
        ]
    }

    # Execute workflow
    print("1. Defining and executing parallel workflow...")
    resp = requests.post("http://localhost:8000/workflows/define", json=workflow_def)

    if resp.status_code != 200:
        print(f"   ❌ Failed to define workflow: {resp.status_code}")
        return False

    workflow_id = resp.json().get("workflow_id")

    exec_data = {"workflow_id": workflow_id, "params": {}}
    resp = requests.post("http://localhost:8000/workflows/execute", json=exec_data)

    if resp.status_code != 200:
        print(f"   ❌ Failed to execute workflow: {resp.status_code}")
        return False

    execution_id = resp.json().get("execution_id")
    print(f"   ✓ Parallel execution started: {execution_id}")

    # Monitor for parallel execution
    print("2. Monitoring parallel execution...")
    start_time = time.time()
    parallel_started = False

    while time.time() - start_time < 30:
        resp = requests.get(f"http://localhost:8000/workflows/executions/{execution_id}")

        if resp.status_code == 200:
            data = resp.json()
            steps = data.get("steps", {})

            # Check if parallel tasks are running simultaneously
            p1_status = steps.get("parallel1", {}).get("status")
            p2_status = steps.get("parallel2", {}).get("status")

            if p1_status == "running" and p2_status == "running" and not parallel_started:
                print("   ✓ Parallel tasks executing simultaneously!")
                parallel_started = True

            if data.get("status") == "completed":
                print("   ✓ Parallel workflow completed!")
                return True
            elif data.get("status") == "failed":
                print(f"   ❌ Parallel workflow failed")
                return False

        time.sleep(1)

    print("   ⚠️ Parallel workflow timed out")
    return False

def cleanup(tmux, bus, bridges, api_process):
    """Clean up all resources"""
    print("\n=== CLEANING UP ===\n")

    # Stop API
    if api_process:
        api_process.terminate()
        api_process.wait()
        print("✓ API Gateway stopped")

    # Stop bridges
    for bridge in bridges.values():
        bridge.stop()
    print("✓ Agent bridges stopped")

    # Stop message bus
    bus.stop()
    print("✓ Message bus stopped")

    # Kill TMUX sessions
    for agent in ["backend-api", "database", "supervisor"]:
        tmux.kill_session(f"claude-{agent}")
    print("✓ TMUX sessions cleaned up")

def main():
    print("=" * 60)
    print("END-TO-END WORKFLOW TEST")
    print("=" * 60)

    # Setup
    tmux, bus, bridges, api_process = setup_system()

    try:
        # Run tests
        results = []

        # Test 1: Simple sequential workflow
        success = test_simple_workflow()
        results.append(("Simple Workflow", success))

        # Test 2: Parallel workflow
        success = test_parallel_workflow()
        results.append(("Parallel Workflow", success))

        # Report results
        print("\n" + "=" * 60)
        print("WORKFLOW TEST RESULTS")
        print("=" * 60)

        for name, success in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{name:20} {status}")

        passed = sum(1 for _, s in results if s)
        total = len(results)

        print("-" * 60)
        print(f"Total: {passed}/{total} tests passed")

        if passed == total:
            print("\n🎉 All workflow tests passed!")
        else:
            print(f"\n⚠️ {total - passed} workflow tests failed")

    finally:
        cleanup(tmux, bus, bridges, api_process)

if __name__ == "__main__":
    main()