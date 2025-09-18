#!/usr/bin/env python3
"""
MCP v2 Comprehensive Test Script
Tests all tools, resources, prompts, and capabilities
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List

# Configuration
SERVER_URL = "http://localhost:8099"
JSONRPC_URL = f"{SERVER_URL}/jsonrpc"
LEGACY_URL = f"{SERVER_URL}/api/mcp/status"

class MCPTester:
    def __init__(self):
        self.session_id = None
        self.test_results = []
        self.request_counter = 0

    def make_jsonrpc_request(self, method: str, params: Dict = None) -> Dict:
        """Make a JSON-RPC 2.0 request"""
        self.request_counter += 1
        request_id = str(uuid.uuid4())

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self.request_counter
        }

        if self.session_id:
            payload["params"]["session_id"] = self.session_id

        headers = {
            "Content-Type": "application/json",
            "X-Request-ID": request_id
        }

        try:
            response = requests.post(JSONRPC_URL, json=payload, headers=headers, timeout=5)
            data = response.json()

            if "error" in data:
                return {"success": False, "error": data["error"]}

            return {"success": True, "result": data.get("result", {})}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_initialize(self):
        """Test session initialization and capability negotiation"""
        print("\n🔧 Testing Initialize...")

        result = self.make_jsonrpc_request("initialize", {
            "clientInfo": {
                "name": "MCP Test Suite",
                "version": "1.0.0"
            },
            "capabilities": ["tools", "resources", "prompts"]
        })

        if result["success"]:
            self.session_id = result["result"].get("session_id")
            print(f"✅ Session initialized: {self.session_id}")
            print(f"   Protocol: {result['result'].get('protocol_version')}")
            print(f"   Tools: {result['result'].get('tools_count')}")
            print(f"   Resources: {result['result'].get('resources_count')}")
            print(f"   Prompts: {result['result'].get('prompts_count')}")
            self.test_results.append(("Initialize", True))
        else:
            print(f"❌ Initialize failed: {result['error']}")
            self.test_results.append(("Initialize", False))

    def test_list_tools(self):
        """Test listing all available tools"""
        print("\n🔧 Testing Tools List...")

        result = self.make_jsonrpc_request("tools/list")

        if result["success"]:
            tools = result["result"]
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools[:3]:  # Show first 3
                print(f"   - {tool['name']}: {tool['description']}")
            if len(tools) > 3:
                print(f"   ... and {len(tools) - 3} more")
            self.test_results.append(("List Tools", True))
            return tools
        else:
            print(f"❌ List tools failed: {result['error']}")
            self.test_results.append(("List Tools", False))
            return []

    def test_tool_execution(self):
        """Test executing each tool with dry_run"""
        print("\n🔧 Testing Tool Execution...")

        test_cases = [
            ("log_activity", {
                "agent": "test_agent",
                "activity": "Running MCP v2 tests",
                "category": "task",
                "status": "in_progress",
                "dry_run": True
            }),
            ("check_conflicts", {
                "agents": ["backend-api", "database"],
                "dry_run": True
            }),
            ("register_component", {
                "name": "test_component",
                "owner": "test_agent",
                "status": "active",
                "dry_run": True
            }),
            ("update_status", {
                "agent": "test_agent",
                "status": "active",
                "current_task": "Testing MCP v2",
                "dry_run": True
            }),
            ("heartbeat", {
                "agent": "test_agent",
                "dry_run": True
            }),
            ("request_collaboration", {
                "from_agent": "test_agent",
                "to_agent": "backend-api",
                "task": "Test collaboration",
                "priority": "low",
                "dry_run": True
            }),
            ("propose_decision", {
                "category": "testing",
                "question": "Should we deploy MCP v2?",
                "proposed_by": "test_agent",
                "dry_run": True
            }),
            ("find_component_owner", {
                "component": "test_component",
                "dry_run": True
            })
        ]

        for tool_name, params in test_cases:
            result = self.make_jsonrpc_request("tools/call", {
                "name": tool_name,
                "arguments": params
            })

            if result["success"]:
                print(f"✅ {tool_name}: Success (dry_run)")
            else:
                print(f"❌ {tool_name}: Failed - {result['error']}")

            self.test_results.append((f"Tool: {tool_name}", result["success"]))

    def test_list_resources(self):
        """Test listing all available resources"""
        print("\n📦 Testing Resources List...")

        result = self.make_jsonrpc_request("resources/list")

        if result["success"]:
            resources = result["result"]
            print(f"✅ Found {len(resources)} resources:")
            for resource in resources:
                print(f"   - {resource['uri']}: {resource['name']}")
            self.test_results.append(("List Resources", True))
            return resources
        else:
            print(f"❌ List resources failed: {result['error']}")
            self.test_results.append(("List Resources", False))
            return []

    def test_resource_access(self):
        """Test reading different resource types"""
        print("\n📦 Testing Resource Access...")

        test_uris = [
            "db://schema/complete",
            "api://swagger/spec",
            "config://agents/supervisor"
        ]

        for uri in test_uris:
            result = self.make_jsonrpc_request("resources/read", {"uri": uri})

            if result["success"]:
                content = result["result"].get("content")
                print(f"✅ {uri}: Retrieved successfully")
                if isinstance(content, dict):
                    print(f"   Content type: dict with {len(content)} keys")
                elif isinstance(content, str):
                    print(f"   Content type: string ({len(content)} chars)")
            else:
                print(f"❌ {uri}: Failed - {result['error']}")

            self.test_results.append((f"Resource: {uri}", result["success"]))

    def test_list_prompts(self):
        """Test listing all available prompts"""
        print("\n💬 Testing Prompts List...")

        result = self.make_jsonrpc_request("prompts/list")

        if result["success"]:
            prompts = result["result"]
            print(f"✅ Found {len(prompts)} prompts:")
            for prompt in prompts:
                print(f"   - {prompt['name']}: {prompt['description']}")
            self.test_results.append(("List Prompts", True))
            return prompts
        else:
            print(f"❌ List prompts failed: {result['error']}")
            self.test_results.append(("List Prompts", False))
            return []

    def test_prompt_execution(self):
        """Test executing prompts with different arguments"""
        print("\n💬 Testing Prompt Execution...")

        test_cases = [
            ("deploy_system", {
                "environment": "development",
                "version": "v2.0.0"
            }),
            ("run_tests", {
                "suite": "integration",
                "verbose": True
            }),
            ("analyze_performance", {
                "component": "mcp_server",
                "duration": "last_hour"
            })
        ]

        for prompt_name, arguments in test_cases:
            result = self.make_jsonrpc_request("prompts/execute", {
                "name": prompt_name,
                "arguments": arguments
            })

            if result["success"]:
                formatted = result["result"].get("result", "")
                print(f"✅ {prompt_name}: {formatted}")
            else:
                print(f"❌ {prompt_name}: Failed - {result['error']}")

            self.test_results.append((f"Prompt: {prompt_name}", result["success"]))

    def test_idempotency(self):
        """Test idempotency with same key"""
        print("\n🔄 Testing Idempotency...")

        idempotency_key = str(uuid.uuid4())
        headers = {
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key
        }

        # First request
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "log_activity",
                "arguments": {
                    "agent": "test_idempotency",
                    "activity": "Testing idempotency",
                    "category": "task",
                    "dry_run": True
                }
            },
            "id": 999
        }

        response1 = requests.post(JSONRPC_URL, json=payload, headers=headers)
        data1 = response1.json()

        # Second request with same idempotency key
        time.sleep(0.1)
        response2 = requests.post(JSONRPC_URL, json=payload, headers=headers)
        data2 = response2.json()

        if data1 == data2:
            print(f"✅ Idempotency working: Same response for same key")
            self.test_results.append(("Idempotency", True))
        else:
            print(f"❌ Idempotency failed: Different responses")
            self.test_results.append(("Idempotency", False))

    def test_legacy_compatibility(self):
        """Test legacy API endpoint compatibility"""
        print("\n🔧 Testing Legacy API Compatibility...")

        try:
            response = requests.get(LEGACY_URL, timeout=5)
            data = response.json()

            if data.get("status") == "operational":
                print(f"✅ Legacy endpoint working")
                print(f"   MCP Version: {data.get('mcp_version')}")
                print(f"   Tools: {data.get('system_stats', {}).get('tools_available')}")
                print(f"   Resources: {data.get('system_stats', {}).get('resources_available')}")
                self.test_results.append(("Legacy API", True))
            else:
                print(f"❌ Legacy endpoint returned non-operational status")
                self.test_results.append(("Legacy API", False))
        except Exception as e:
            print(f"❌ Legacy endpoint failed: {e}")
            self.test_results.append(("Legacy API", False))

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        passed = sum(1 for _, success in self.test_results if success)
        total = len(self.test_results)

        for test_name, success in self.test_results:
            status = "✅" if success else "❌"
            print(f"{status} {test_name}")

        print("\n" + "-"*60)
        print(f"Results: {passed}/{total} tests passed ({passed*100//total}%)")

        if passed == total:
            print("🎉 All tests passed! MCP v2 is working correctly.")
        else:
            print(f"⚠️  {total - passed} test(s) failed. Please check the logs.")

def main():
    print("="*60)
    print("MCP v2 COMPREHENSIVE TEST SUITE")
    print("="*60)
    print(f"Server: {SERVER_URL}")
    print(f"Time: {datetime.now().isoformat()}")

    tester = MCPTester()

    # Run all tests
    tester.test_initialize()
    tester.test_list_tools()
    tester.test_tool_execution()
    tester.test_list_resources()
    tester.test_resource_access()
    tester.test_list_prompts()
    tester.test_prompt_execution()
    tester.test_idempotency()
    tester.test_legacy_compatibility()

    # Print summary
    tester.print_summary()

if __name__ == "__main__":
    main()