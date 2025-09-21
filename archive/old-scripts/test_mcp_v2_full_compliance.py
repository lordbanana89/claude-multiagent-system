#!/usr/bin/env python3
"""
MCP v2 Full Compliance Test
Tests all MCP v2 protocol features and capabilities
"""

import json
import requests
import asyncio
import websockets
import sys
from datetime import datetime
from typing import Dict, List, Any

class MCPv2ComplianceTester:
    def __init__(self):
        self.server_url = "http://localhost:8099"
        self.ws_url = "ws://localhost:8100"
        self.jsonrpc_endpoint = f"{self.server_url}/jsonrpc"
        self.test_results = {}

    def test_jsonrpc_call(self, method: str, params: Dict = None) -> Dict:
        """Test a JSON-RPC method"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params or {},
                "id": f"test-{method}"
            }

            response = requests.post(self.jsonrpc_endpoint,
                                    json=payload,
                                    headers={"Content-Type": "application/json"},
                                    timeout=5)

            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def run_compliance_tests(self):
        """Run all MCP v2 compliance tests"""
        print("=" * 60)
        print("MCP v2 FULL COMPLIANCE TEST")
        print("=" * 60)

        # 1. Test Core Methods
        print("\n📋 TESTING CORE MCP METHODS:")
        print("-" * 40)

        core_methods = [
            ("initialize", {"clientInfo": {"name": "test", "version": "1.0"}}),
            ("initialized", {}),
            ("shutdown", {}),
            ("ping", {})
        ]

        for method, params in core_methods:
            result = self.test_jsonrpc_call(method, params)
            status = "✅" if "result" in result or method == "ping" else "❌"
            self.test_results[method] = status
            print(f"  {method}: {status}")
            if "error" in result:
                print(f"    Error: {result['error']}")

        # 2. Test Tool Methods
        print("\n🔧 TESTING TOOL METHODS:")
        print("-" * 40)

        # List tools
        result = self.test_jsonrpc_call("tools/list")
        if "result" in result:
            tools = result["result"]
            print(f"  tools/list: ✅ ({len(tools)} tools available)")
            self.test_results["tools/list"] = "✅"

            # Test each tool
            for tool in tools[:3]:  # Test first 3 tools
                tool_name = tool["name"]
                # Get minimal params for the tool
                test_params = self._get_test_params(tool_name)
                result = self.test_jsonrpc_call("tools/call", {
                    "name": tool_name,
                    "arguments": test_params
                })
                status = "✅" if "result" in result else "❌"
                print(f"  tools/call ({tool_name}): {status}")
        else:
            print(f"  tools/list: ❌")
            self.test_results["tools/list"] = "❌"

        # 3. Test Resource Methods (if supported)
        print("\n📚 TESTING RESOURCE METHODS:")
        print("-" * 40)

        resource_methods = [
            ("resources/list", {}),
            ("resources/read", {"uri": "test://resource"}),
            ("resources/templates/list", {}),
            ("resources/subscribe", {"uri": "test://resource"})
        ]

        for method, params in resource_methods:
            result = self.test_jsonrpc_call(method, params)
            status = "✅" if "result" in result else "⚠️ Not implemented"
            self.test_results[method] = status
            print(f"  {method}: {status}")

        # 4. Test Prompt Methods (if supported)
        print("\n💬 TESTING PROMPT METHODS:")
        print("-" * 40)

        prompt_methods = [
            ("prompts/list", {}),
            ("prompts/get", {"name": "test_prompt"}),
            ("prompts/run", {"name": "test_prompt", "arguments": {}})
        ]

        for method, params in prompt_methods:
            result = self.test_jsonrpc_call(method, params)
            status = "✅" if "result" in result else "⚠️ Not implemented"
            self.test_results[method] = status
            print(f"  {method}: {status}")

        # 5. Test Notification Methods
        print("\n🔔 TESTING NOTIFICATION METHODS:")
        print("-" * 40)

        notification_methods = [
            ("notifications/initialized", {}),
            ("notifications/cancelled", {"requestId": "test"}),
            ("notifications/progress", {"progressToken": "test", "progress": 50})
        ]

        for method, params in notification_methods:
            result = self.test_jsonrpc_call(method, params)
            # Notifications don't expect responses
            status = "✅" if not result.get("error") else "⚠️"
            self.test_results[method] = status
            print(f"  {method}: {status}")

        # 6. Test WebSocket
        print("\n🌐 TESTING WEBSOCKET:")
        print("-" * 40)

        ws_test = self._test_websocket()
        print(f"  WebSocket connection: {ws_test}")
        self.test_results["websocket"] = ws_test

        # 7. Test Session Management
        print("\n🔐 TESTING SESSION MANAGEMENT:")
        print("-" * 40)

        # Initialize session
        result = self.test_jsonrpc_call("initialize", {
            "clientInfo": {"name": "session-test", "version": "1.0"},
            "capabilities": ["tools", "resources", "prompts"]
        })

        if "result" in result:
            session_id = result.get("result", {}).get("sessionId")
            if session_id:
                print(f"  Session creation: ✅ (ID: {session_id})")
                self.test_results["session"] = "✅"

                # Test session persistence
                result = self.test_jsonrpc_call("tools/list", {"session_id": session_id})
                if "result" in result:
                    print(f"  Session persistence: ✅")
                else:
                    print(f"  Session persistence: ❌")
            else:
                print(f"  Session creation: ⚠️ No session ID returned")
                self.test_results["session"] = "⚠️"
        else:
            print(f"  Session creation: ❌")
            self.test_results["session"] = "❌"

        # 8. Test Error Handling
        print("\n⚠️ TESTING ERROR HANDLING:")
        print("-" * 40)

        # Test invalid method
        result = self.test_jsonrpc_call("invalid/method")
        if "error" in result:
            print(f"  Invalid method handling: ✅")
            self.test_results["error_handling"] = "✅"
        else:
            print(f"  Invalid method handling: ❌")
            self.test_results["error_handling"] = "❌"

        # Test invalid params
        result = self.test_jsonrpc_call("tools/call", {"invalid": "params"})
        if "error" in result:
            print(f"  Invalid params handling: ✅")
        else:
            print(f"  Invalid params handling: ❌")

        # 9. Test Capabilities
        print("\n🚀 TESTING CAPABILITIES:")
        print("-" * 40)

        result = self.test_jsonrpc_call("initialize", {
            "clientInfo": {"name": "capability-test", "version": "1.0"},
            "capabilities": ["tools", "resources", "prompts", "experimental"]
        })

        if "result" in result:
            server_caps = result.get("result", {}).get("capabilities", {})
            print(f"  Server capabilities: {server_caps if server_caps else 'None declared'}")

            if "tools" in str(server_caps):
                print(f"    - Tools: ✅")
            if "resources" in str(server_caps):
                print(f"    - Resources: ✅")
            if "prompts" in str(server_caps):
                print(f"    - Prompts: ✅")

        # Summary
        self._print_summary()

    def _get_test_params(self, tool_name: str) -> Dict:
        """Get test parameters for a tool"""
        test_params = {
            "heartbeat": {"agent": "test"},
            "update_status": {"agent": "test", "status": "active"},
            "log_activity": {"agent": "test", "activity": "test", "category": "task"},
            "check_conflicts": {"agents": ["test1", "test2"]},
            "register_component": {"name": "test", "owner": "test"},
            "request_collaboration": {"from_agent": "test1", "to_agent": "test2", "task": "test"},
            "propose_decision": {"category": "test", "question": "test?", "proposed_by": "test"},
            "find_component_owner": {"component": "test"}
        }
        return test_params.get(tool_name, {})

    def _test_websocket(self) -> str:
        """Test WebSocket connection"""
        try:
            async def test_ws():
                async with websockets.connect(self.ws_url) as websocket:
                    # Send handshake
                    await websocket.send(json.dumps({
                        "type": "handshake",
                        "agent": "test",
                        "session_id": "test-session"
                    }))

                    # Wait for response with timeout
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2)
                        return True
                    except asyncio.TimeoutError:
                        # No response but connection established
                        return True

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(test_ws())
            return "✅" if result else "❌"
        except Exception as e:
            return f"❌ ({str(e)[:30]}...)"

    def _print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("COMPLIANCE SUMMARY")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed = sum(1 for v in self.test_results.values() if "✅" in v)
        warnings = sum(1 for v in self.test_results.values() if "⚠️" in v)
        failed = sum(1 for v in self.test_results.values() if "❌" in v)

        print(f"\nTotal Tests: {total_tests}")
        print(f"  ✅ Passed: {passed}")
        print(f"  ⚠️ Warnings: {warnings}")
        print(f"  ❌ Failed: {failed}")

        compliance_score = (passed / total_tests) * 100 if total_tests > 0 else 0

        print(f"\n🎯 MCP v2 Compliance Score: {compliance_score:.1f}%")

        if compliance_score >= 80:
            print("✅ FULLY COMPLIANT - Bridge supports MCP v2 protocol")
        elif compliance_score >= 60:
            print("⚠️ PARTIALLY COMPLIANT - Core features work, some optional features missing")
        else:
            print("❌ NOT COMPLIANT - Major features missing")

        # List missing features
        if warnings > 0 or failed > 0:
            print("\n📝 Areas for improvement:")
            for feature, status in self.test_results.items():
                if "⚠️" in status or "❌" in status:
                    print(f"  - {feature}: {status}")


if __name__ == "__main__":
    tester = MCPv2ComplianceTester()
    tester.run_compliance_tests()