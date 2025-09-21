#!/usr/bin/env python3
"""
Test MCP Compliant Server - Verifica compatibilità con SDK ufficiale
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Test imports to verify SDK compatibility
try:
    from mcp.server.fastmcp import FastMCP
    from pydantic import BaseModel
    print("✅ MCP SDK imports successful")
except ImportError as e:
    print(f"❌ MCP SDK not installed or incompatible: {e}")
    print("Install with: pip install mcp")
    exit(1)

class MCPComplianceTest:
    """Test compliance con SDK ufficiale MCP"""

    def __init__(self):
        self.passed = []
        self.failed = []

    def test_tool_decorators(self):
        """Verifica che i tool usino decoratori corretti"""
        print("\n📍 Test 1: Tool Decorators")

        try:
            from mcp_server_compliant import mcp

            # Verifica che mcp sia FastMCP instance
            assert isinstance(mcp, FastMCP), "Server must be FastMCP instance"
            print("  ✅ Server is FastMCP instance")

            # Verifica che i tool siano registrati
            tools = [
                'heartbeat', 'update_status', 'log_activity',
                'check_conflicts', 'register_component',
                'request_collaboration', 'propose_decision',
                'find_component_owner'
            ]

            # FastMCP registra i tool internamente
            # Possiamo verificare provando ad accedere ai metodi
            import mcp_server_compliant as server

            for tool_name in tools:
                assert hasattr(server, tool_name), f"Tool {tool_name} not found"
                print(f"  ✅ Tool '{tool_name}' properly defined")

            self.passed.append("Tool Decorators")
            return True

        except AssertionError as e:
            print(f"  ❌ {e}")
            self.failed.append("Tool Decorators")
            return False
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
            self.failed.append("Tool Decorators")
            return False

    def test_pydantic_models(self):
        """Verifica modelli Pydantic per response"""
        print("\n📍 Test 2: Pydantic Response Models")

        try:
            from mcp_server_compliant import (
                HeartbeatResponse,
                StatusUpdateResponse,
                ActivityLogResponse,
                ConflictCheckResponse,
                ComponentRegistrationResponse,
                CollaborationRequestResponse,
                DecisionProposalResponse,
                ComponentOwnerResponse
            )

            # Test HeartbeatResponse
            response = HeartbeatResponse(
                status='alive',
                agent='test-agent',
                timestamp=datetime.now().isoformat(),
                next_expected=123456789.0,
                db_updated=True
            )
            assert response.status == 'alive'
            print("  ✅ HeartbeatResponse model valid")

            # Test StatusUpdateResponse
            status = StatusUpdateResponse(
                success=True,
                agent='test-agent',
                status='busy',
                previous_status='idle',
                task_assigned='test-task',
                timestamp=datetime.now().isoformat()
            )
            assert status.success == True
            print("  ✅ StatusUpdateResponse model valid")

            # Verifica serialization
            json_data = response.model_dump_json()
            assert json_data
            print("  ✅ Models serialize to JSON properly")

            self.passed.append("Pydantic Models")
            return True

        except Exception as e:
            print(f"  ❌ Model validation failed: {e}")
            self.failed.append("Pydantic Models")
            return False

    def test_type_hints(self):
        """Verifica type hints nei tool"""
        print("\n📍 Test 3: Type Hints")

        try:
            import inspect
            import mcp_server_compliant as server

            # Controlla heartbeat function signature
            sig = inspect.signature(server.heartbeat)
            params = sig.parameters

            assert 'agent' in params, "Missing 'agent' parameter"
            assert params['agent'].annotation == str, "Agent should be str"
            print("  ✅ Heartbeat has correct type hints")

            # Controlla return type
            return_annotation = sig.return_annotation
            assert return_annotation.__name__ == 'HeartbeatResponse'
            print("  ✅ Return type properly annotated")

            self.passed.append("Type Hints")
            return True

        except Exception as e:
            print(f"  ❌ Type hint validation failed: {e}")
            self.failed.append("Type Hints")
            return False

    def test_context_parameter(self):
        """Verifica Context parameter opzionale"""
        print("\n📍 Test 4: Context Parameter")

        try:
            import inspect
            import mcp_server_compliant as server

            sig = inspect.signature(server.heartbeat)
            params = sig.parameters

            assert 'ctx' in params, "Missing Context parameter"
            print("  ✅ Context parameter present")

            # Verifica che sia del tipo corretto
            ctx_annotation = params['ctx'].annotation
            assert 'Context' in str(ctx_annotation)
            print("  ✅ Context has correct type")

            self.passed.append("Context Parameter")
            return True

        except Exception as e:
            print(f"  ❌ Context parameter validation failed: {e}")
            self.failed.append("Context Parameter")
            return False

    def test_async_functions(self):
        """Verifica che i tool siano async"""
        print("\n📍 Test 5: Async Functions")

        try:
            import inspect
            import mcp_server_compliant as server

            tools = [
                'heartbeat', 'update_status', 'log_activity',
                'check_conflicts', 'register_component',
                'request_collaboration', 'propose_decision',
                'find_component_owner'
            ]

            for tool_name in tools:
                func = getattr(server, tool_name)
                assert inspect.iscoroutinefunction(func), f"{tool_name} is not async"
                print(f"  ✅ {tool_name} is async function")

            self.passed.append("Async Functions")
            return True

        except Exception as e:
            print(f"  ❌ Async validation failed: {e}")
            self.failed.append("Async Functions")
            return False

    def test_docstrings(self):
        """Verifica che i tool abbiano docstring"""
        print("\n📍 Test 6: Docstrings")

        try:
            import mcp_server_compliant as server

            tools = ['heartbeat', 'update_status', 'log_activity']

            for tool_name in tools:
                func = getattr(server, tool_name)
                assert func.__doc__, f"{tool_name} missing docstring"
                assert len(func.__doc__) > 20, f"{tool_name} docstring too short"
                print(f"  ✅ {tool_name} has proper docstring")

            self.passed.append("Docstrings")
            return True

        except Exception as e:
            print(f"  ❌ Docstring validation failed: {e}")
            self.failed.append("Docstrings")
            return False

    def test_server_lifecycle(self):
        """Verifica lifecycle handlers"""
        print("\n📍 Test 7: Server Lifecycle")

        try:
            import mcp_server_compliant as server

            # Verifica on_start handler
            assert hasattr(server, 'on_start'), "Missing on_start handler"
            print("  ✅ on_server_start handler defined")

            # Verifica on_stop handler
            assert hasattr(server, 'on_stop'), "Missing on_stop handler"
            print("  ✅ on_server_stop handler defined")

            self.passed.append("Server Lifecycle")
            return True

        except Exception as e:
            print(f"  ❌ Lifecycle validation failed: {e}")
            self.failed.append("Server Lifecycle")
            return False

    def test_database_integration(self):
        """Verifica integrazione database"""
        print("\n📍 Test 8: Database Integration")

        try:
            from core.database_manager import DatabaseManager

            # Test instantiation
            db = DatabaseManager()
            print("  ✅ DatabaseManager instantiates correctly")

            # Verifica metodi richiesti
            required_methods = [
                'update_heartbeat',
                'update_agent_status',
                'log_activity',
                'check_conflicts',
                'register_component',
                'request_collaboration',
                'propose_decision',
                'find_component_owner'
            ]

            for method in required_methods:
                assert hasattr(db, method), f"Missing method: {method}"

            print("  ✅ All required database methods present")

            self.passed.append("Database Integration")
            return True

        except Exception as e:
            print(f"  ❌ Database integration failed: {e}")
            self.failed.append("Database Integration")
            return False

    def run_all_tests(self):
        """Esegui tutti i test di compliance"""
        print("=" * 60)
        print("🧪 MCP SDK COMPLIANCE TEST")
        print("=" * 60)

        tests = [
            self.test_tool_decorators,
            self.test_pydantic_models,
            self.test_type_hints,
            self.test_context_parameter,
            self.test_async_functions,
            self.test_docstrings,
            self.test_server_lifecycle,
            self.test_database_integration
        ]

        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"  ❌ Test crashed: {e}")
                self.failed.append(test.__name__)

        print("\n" + "=" * 60)
        print(f"📊 RESULTS: {len(self.passed)} passed, {len(self.failed)} failed")

        if self.failed:
            print("\n❌ Failed tests:")
            for test_name in self.failed:
                print(f"  - {test_name}")
        else:
            print("\n🎉 All compliance tests passed!")

        print("\n📋 COMPLIANCE SUMMARY:")
        compliance_score = (len(self.passed) / len(tests)) * 100
        print(f"  Compliance Score: {compliance_score:.1f}%")

        if compliance_score == 100:
            print("  Status: ✅ FULLY COMPLIANT with MCP SDK")
        elif compliance_score >= 80:
            print("  Status: 🟡 MOSTLY COMPLIANT (minor issues)")
        elif compliance_score >= 50:
            print("  Status: 🟠 PARTIALLY COMPLIANT (needs work)")
        else:
            print("  Status: 🔴 NOT COMPLIANT (major issues)")

        return compliance_score == 100

def main():
    """Run compliance test"""
    tester = MCPComplianceTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)

if __name__ == "__main__":
    main()