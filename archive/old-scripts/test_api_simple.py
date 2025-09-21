#!/usr/bin/env python3
"""Simple API test with actual endpoints"""

import subprocess
import time
import requests
import json

def start_api():
    """Start API in background"""
    print("Starting API Gateway...")
    process = subprocess.Popen(
        ["python3", "-m", "uvicorn", "api.unified_gateway:app", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)
    return process

def test_endpoints():
    """Test actual API endpoints"""
    base_url = "http://localhost:8000"

    # Test root
    print("\nTesting root endpoint...")
    try:
        resp = requests.get(f"{base_url}/")
        print(f"  / - Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"    Message: {data.get('message', '')[:50]}")
    except Exception as e:
        print(f"  Error: {e}")

    # Test agents list
    print("\nTesting agents endpoint...")
    try:
        resp = requests.get(f"{base_url}/agents")
        print(f"  /agents - Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"    Found {len(data.get('agents', []))} agents")
    except Exception as e:
        print(f"  Error: {e}")

    # Test system health
    print("\nTesting system health...")
    try:
        resp = requests.get(f"{base_url}/system/health")
        print(f"  /system/health - Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"    Status: {data.get('status')}")
            print(f"    Components: {list(data.get('components', {}).keys())}")
    except Exception as e:
        print(f"  Error: {e}")

    # Test task submission
    print("\nTesting task submission...")
    task_data = {
        "agent": "backend-api",
        "command": "echo 'Test task'",
        "params": {},
        "priority": "normal"
    }

    try:
        resp = requests.post(f"{base_url}/tasks/submit", json=task_data)
        print(f"  /tasks/submit - Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"    Task ID: {data.get('task_id', 'unknown')}")
    except Exception as e:
        print(f"  Error: {e}")

    # Test workflows
    print("\nTesting workflows...")
    try:
        resp = requests.get(f"{base_url}/workflows")
        print(f"  /workflows - Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"    Workflows: {len(data.get('workflows', []))}")
    except Exception as e:
        print(f"  Error: {e}")

def main():
    print("=" * 60)
    print("SIMPLE API TEST")
    print("=" * 60)

    # Start API
    api_process = start_api()

    try:
        # Run tests
        test_endpoints()

        print("\n" + "=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)

    finally:
        # Cleanup
        print("\nStopping API...")
        api_process.terminate()
        api_process.wait()
        print("API stopped")

if __name__ == "__main__":
    main()