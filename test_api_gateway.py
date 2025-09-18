#!/usr/bin/env python3
"""Test API Gateway with real requests"""

import sys
import os
import time
import requests
import json
import subprocess
import threading
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.tmux_client import TMUXClient
from core.message_bus import get_message_bus
from agents.agent_bridge import AgentBridge

def start_api_server():
    """Start the API server in background"""
    print("Starting API Gateway...")

    # Start in a subprocess
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.unified_gateway:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for server to start
    time.sleep(3)

    # Check if it's running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✓ API Gateway started successfully")
            return process
    except:
        pass

    print("❌ Failed to start API Gateway")
    process.terminate()
    return None

def setup_system():
    """Setup the system components"""
    print("\nSetting up system components...")

    # Create TMUX sessions
    tmux = TMUXClient()
    for agent in ["backend-api", "database", "supervisor"]:
        session = f"claude-{agent}"
        if tmux.session_exists(session):
            tmux.kill_session(session)
        tmux.create_session(session)
        print(f"✓ Created session: {session}")

    # Start message bus
    bus = get_message_bus()
    if not bus.running:
        bus.start()
    print("✓ Message bus started")

    # Start agent bridges
    bridges = {}
    for agent in ["backend-api", "database", "supervisor"]:
        bridge = AgentBridge(agent)
        bridge.start()
        bridges[agent] = bridge
        print(f"✓ Started bridge: {agent}")

    return tmux, bus, bridges

def test_health_endpoint():
    """Test the health check endpoint"""
    print("\n=== Testing Health Endpoint ===")

    try:
        response = requests.get("http://localhost:8000/api/system/health")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✓ Health check passed")
            print(f"  Status: {data.get('status')}")
            print(f"  Components: {list(data.get('components', {}).keys())}")
            return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")

    return False

def test_list_agents():
    """Test listing agents"""
    print("\n=== Testing List Agents ===")

    try:
        response = requests.get("http://localhost:8000/api/agents")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            agents = data.get('agents', [])
            print(f"✓ Found {len(agents)} agents")
            for agent in agents[:3]:
                print(f"  - {agent['name']}: {agent.get('status', {}).get('status', 'unknown')}")
            return True
    except Exception as e:
        print(f"❌ List agents failed: {e}")

    return False

def test_submit_task():
    """Test submitting a task"""
    print("\n=== Testing Task Submission ===")

    task_data = {
        "agent": "backend-api",
        "command": "echo 'API Gateway test task'",
        "params": {},
        "priority": "high",
        "timeout": 10
    }

    try:
        print(f"Submitting task to {task_data['agent']}...")
        response = requests.post("http://localhost:8000/api/tasks/execute", json=task_data)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            print(f"✓ Task submitted: {task_id}")

            # Wait and check status
            time.sleep(3)

            # For now, check via queue status
            status_response = requests.get("http://localhost:8000/api/queue/tasks")
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"  Task status: {status.get('status')}")

                if status.get('status') == 'completed':
                    print("✓ Task completed successfully!")
                    return True
                else:
                    print(f"⚠️ Task status: {status}")

    except Exception as e:
        print(f"❌ Task submission failed: {e}")

    return False

def test_workflow_execution():
    """Test workflow execution via API"""
    print("\n=== Testing Workflow Execution ===")

    workflow = {
        "workflow_definition": {
            "name": "API Test Workflow",
            "description": "Test workflow via API",
            "steps": [
                {
                    "id": "step1",
                    "name": "Echo Start",
                    "agent": "supervisor",
                    "action": "echo 'Workflow started'",
                    "params": {}
                },
                {
                    "id": "step2",
                    "name": "Process",
                    "agent": "backend-api",
                    "action": "echo 'Processing'",
                    "params": {},
                    "depends_on": ["step1"]
                }
            ]
        },
        "params": {}
    }

    try:
        print("Submitting workflow...")
        # First create workflow then execute
        response = requests.post("http://localhost:8000/api/workflows", json=workflow['workflow_definition'])
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            execution_id = data.get('execution_id')
            print(f"✓ Workflow started: {execution_id}")

            # Monitor execution
            for i in range(10):
                time.sleep(2)
                # Check workflow status
                status_response = requests.get(f"http://localhost:8000/api/workflows/{execution_id}")

                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f"  Workflow status: {status.get('status')}")

                    if status.get('status') in ['completed', 'failed']:
                        if status.get('status') == 'completed':
                            print("✓ Workflow completed successfully!")
                            return True
                        break

    except Exception as e:
        print(f"❌ Workflow execution failed: {e}")

    return False

def test_system_status():
    """Test system status endpoint"""
    print("\n=== Testing System Status ===")

    try:
        response = requests.get("http://localhost:8000/api/system/health")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✓ System status retrieved")
            print(f"  Status: {data.get('status')}")
            print(f"  Agents: {len(data.get('agents', {}))}")
            print(f"  Queue pending: {data.get('queue', {}).get('pending_tasks', 0)}")
            print(f"  Workflows: {data.get('workflows', {}).get('defined', 0)} defined")
            return True

    except Exception as e:
        print(f"❌ System status failed: {e}")

    return False

def main():
    """Run all API Gateway tests"""
    print("=" * 60)
    print("API GATEWAY INTEGRATION TEST")
    print("=" * 60)

    # Setup system
    tmux, bus, bridges = setup_system()

    # Start API server
    api_process = start_api_server()
    if not api_process:
        print("Cannot proceed without API Gateway")
        return

    try:
        # Run tests
        results = []

        tests = [
            ("Health Check", test_health_endpoint),
            ("List Agents", test_list_agents),
            ("Submit Task", test_submit_task),
            ("Workflow Execution", test_workflow_execution),
            ("System Status", test_system_status)
        ]

        for name, test_func in tests:
            success = test_func()
            results.append((name, success))
            time.sleep(1)

        # Report results
        print("\n" + "=" * 60)
        print("API GATEWAY TEST RESULTS")
        print("=" * 60)

        for name, success in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{name:20} {status}")

        passed = sum(1 for _, s in results if s)
        total = len(results)

        print("-" * 60)
        print(f"Total: {passed}/{total} tests passed")

        if passed == total:
            print("\n🎉 All API Gateway tests passed!")
        else:
            print(f"\n⚠️ {total - passed} tests failed")

    finally:
        # Cleanup
        print("\nCleaning up...")

        # Stop API server
        if api_process:
            api_process.terminate()
            api_process.wait()
            print("✓ API Gateway stopped")

        # Stop bridges
        for bridge in bridges.values():
            bridge.stop()

        # Stop message bus
        bus.stop()

        # Kill TMUX sessions
        for agent in ["backend-api", "database", "supervisor"]:
            tmux.kill_session(f"claude-{agent}")

        print("✓ Cleanup complete")

if __name__ == "__main__":
    main()