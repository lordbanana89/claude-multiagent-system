#!/usr/bin/env python3
"""
Test MCP server stdio communication
"""

import json
import subprocess
import time

def test_stdio_communication():
    """Test the MCP server handles stdio communication properly"""

    # Start the MCP server
    process = subprocess.Popen(
        ["python3", "mcp_server_fastmcp.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    tests = []

    try:
        # Test 1: Initialize
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            },
            "id": 1
        }

        process.stdin.write(json.dumps(request) + '\n')
        process.stdin.flush()
        response = process.stdout.readline()
        result = json.loads(response)

        tests.append({
            "test": "Initialize",
            "passed": result.get("result", {}).get("serverInfo", {}).get("name") == "claude-multiagent-system"
        })

        # Test 2: Send initialized notification
        notification = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        }

        process.stdin.write(json.dumps(notification) + '\n')
        process.stdin.flush()

        # Test 3: List tools
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        }

        process.stdin.write(json.dumps(request) + '\n')
        process.stdin.flush()
        response = process.stdout.readline()

        if not response:
            tests.append({
                "test": "List tools",
                "passed": False,
                "details": "No response received"
            })
        else:
            try:
                result = json.loads(response)
                tools_count = len(result.get("result", {}).get("tools", []))
                tests.append({
                    "test": "List tools",
                    "passed": tools_count > 0,
                    "details": f"Found {tools_count} tools"
                })
            except json.JSONDecodeError:
                tests.append({
                    "test": "List tools",
                    "passed": False,
                    "details": f"Invalid JSON response: {response[:100]}"
                })

        # Test 4: Call a tool
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "init_agent",
                "arguments": {"agent": "test-agent"}
            },
            "id": 3
        }

        process.stdin.write(json.dumps(request) + '\n')
        process.stdin.flush()
        response = process.stdout.readline()
        result = json.loads(response)

        tests.append({
            "test": "Call tool",
            "passed": "result" in result
        })

        # Test 5: List resources
        request = {
            "jsonrpc": "2.0",
            "method": "resources/list",
            "params": {},
            "id": 4
        }

        process.stdin.write(json.dumps(request) + '\n')
        process.stdin.flush()
        response = process.stdout.readline()
        result = json.loads(response)

        tests.append({
            "test": "List resources",
            "passed": len(result.get("result", {}).get("resources", [])) > 0
        })

        # Print results
        print("\n=== MCP STDIO Test Results ===\n")
        all_passed = True
        for test in tests:
            status = "✅" if test["passed"] else "❌"
            details = f" - {test.get('details', '')}" if 'details' in test else ""
            print(f"{status} {test['test']}{details}")
            if not test["passed"]:
                all_passed = False

        print(f"\nOverall: {'✅ All tests passed!' if all_passed else '❌ Some tests failed'}")

        if all_passed:
            print("\n✅ MCP server is ready for Claude Desktop!")
            print("Restart Claude Desktop to activate the connection.")

    finally:
        # Terminate the server
        process.terminate()
        process.wait(timeout=2)

if __name__ == "__main__":
    test_stdio_communication()