#!/usr/bin/env python3
"""Test MCP Bridge functionality"""

import json
import sys
import subprocess

def test_bridge():
    """Test the MCP bridge with sample data"""

    test_cases = [
        {
            "event": "notification",
            "data": {
                "content": "I'll use the log_activity tool to record starting the backend API implementation"
            }
        },
        {
            "event": "notification",
            "data": {
                "content": "Checking for conflicts with /api/users endpoint"
            }
        },
        {
            "event": "notification",
            "data": {
                "content": "Registering component: api:/api/users"
            }
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test['event']}")
        print(f"   Input: {test['data']['content'][:50]}...")

        # Run bridge with test data
        result = subprocess.run(
            ["python3", "/Users/erik/Desktop/claude-multiagent-system/mcp_bridge.py", test["event"]],
            input=json.dumps(test["data"]),
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            response = json.loads(result.stdout)
            if response.get("systemMessage"):
                print(f"   ✅ Result: {response['systemMessage']}")
            else:
                print(f"   ✅ Passed through (no MCP tool detected)")
        else:
            print(f"   ❌ Error: {result.stderr}")

if __name__ == "__main__":
    print("🌉 Testing MCP Bridge...")
    test_bridge()
