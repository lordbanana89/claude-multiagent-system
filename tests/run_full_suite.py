#!/usr/bin/env python3
"""
Master Test Suite Runner
Executes all system tests and generates comprehensive report
"""

import sys
import os
import unittest
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestSuiteRunner:
    """Master test suite runner"""

    def __init__(self):
        self.results = []
        self.start_time = None
        self.end_time = None

    def run_shell_tests(self):
        """Run shell-based MCP tool tests"""
        print("\n" + "="*60)
        print("RUNNING MCP TOOLS SHELL TESTS")
        print("="*60)

        test_results = {
            "suite": "MCP Tools Shell Tests",
            "tests": [],
            "passed": 0,
            "failed": 0
        }

        # Test 1: Agent initialization
        print("\n[TEST] Agent initialization...")
        cmd = "source ../agent_tools.sh && init_agent test_runner 2>&1"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable='/bin/bash')
        if "Agent initialized" in result.stdout:
            print("✅ Agent initialization passed")
            test_results["passed"] += 1
            test_results["tests"].append({"name": "Agent initialization", "status": "PASS"})
        else:
            print("❌ Agent initialization failed")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "Agent initialization", "status": "FAIL"})

        # Test 2: Heartbeat
        print("\n[TEST] Heartbeat functionality...")
        cmd = "source ../agent_tools.sh && export AGENT_NAME=test_runner && heartbeat 2>&1"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable='/bin/bash')
        if "Heartbeat" in result.stdout and "alive" in result.stdout:
            print("✅ Heartbeat test passed")
            test_results["passed"] += 1
            test_results["tests"].append({"name": "Heartbeat", "status": "PASS"})
        else:
            print("❌ Heartbeat test failed")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "Heartbeat", "status": "FAIL"})

        # Test 3: Status update
        print("\n[TEST] Status update...")
        cmd = 'source ../agent_tools.sh && status test_runner "busy" "Running tests" 2>&1'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable='/bin/bash')
        if "Status updated" in result.stdout:
            print("✅ Status update passed")
            test_results["passed"] += 1
            test_results["tests"].append({"name": "Status update", "status": "PASS"})
        else:
            print("❌ Status update failed")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "Status update", "status": "FAIL"})

        # Test 4: Activity logging
        print("\n[TEST] Activity logging...")
        cmd = '''source ../agent_tools.sh && log_activity test_runner "test" "Running regression tests" '{"suite":"full"}' 2>&1'''
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable='/bin/bash')
        if "Activity logged" in result.stdout:
            print("✅ Activity logging passed")
            test_results["passed"] += 1
            test_results["tests"].append({"name": "Activity logging", "status": "PASS"})
        else:
            print("❌ Activity logging failed")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "Activity logging", "status": "FAIL"})

        # Test 5: Message sending
        print("\n[TEST] Message sending...")
        cmd = 'source ../agent_tools.sh && send_message test_runner supervisor "Regression tests in progress" 2>&1'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable='/bin/bash')
        if "Message sent" in result.stdout:
            print("✅ Message sending passed")
            test_results["passed"] += 1
            test_results["tests"].append({"name": "Message sending", "status": "PASS"})
        else:
            print("❌ Message sending failed")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "Message sending", "status": "FAIL"})

        # Test 6: Agent status check
        print("\n[TEST] Agent status check...")
        cmd = "source ../agent_tools.sh && check_agents 2>&1"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable='/bin/bash')
        if "AGENT STATUS" in result.stdout:
            print("✅ Agent status check passed")
            test_results["passed"] += 1
            test_results["tests"].append({"name": "Agent status check", "status": "PASS"})
        else:
            print("❌ Agent status check failed")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "Agent status check", "status": "FAIL"})

        # Test 7: View activities
        print("\n[TEST] View activities...")
        cmd = "source ../agent_tools.sh && view_activities 2>&1"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable='/bin/bash')
        if "RECENT ACTIVITIES" in result.stdout:
            print("✅ View activities passed")
            test_results["passed"] += 1
            test_results["tests"].append({"name": "View activities", "status": "PASS"})
        else:
            print("❌ View activities failed")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "View activities", "status": "FAIL"})

        self.results.append(test_results)
        return test_results

    def run_auth_api_tests(self):
        """Run authentication API tests"""
        print("\n" + "="*60)
        print("RUNNING AUTHENTICATION API TESTS")
        print("="*60)

        test_results = {
            "suite": "Authentication API Tests",
            "tests": [],
            "passed": 0,
            "failed": 0
        }

        import requests

        # Test 1: Login endpoint availability
        print("\n[TEST] Login endpoint availability...")
        try:
            response = requests.get("http://localhost:5002/api/auth/login", timeout=5)
            print("✅ Login endpoint is reachable")
            test_results["passed"] += 1
            test_results["tests"].append({"name": "Login endpoint availability", "status": "PASS"})
        except:
            print("❌ Login endpoint not reachable")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "Login endpoint availability", "status": "FAIL"})

        # Test 2: Invalid credentials
        print("\n[TEST] Invalid credentials handling...")
        try:
            response = requests.post("http://localhost:5002/api/auth/login",
                                    json={"username": "invalid", "password": "wrong"},
                                    timeout=5)
            if response.status_code == 401 and "Invalid credentials" in response.text:
                print("✅ Invalid credentials handled correctly")
                test_results["passed"] += 1
                test_results["tests"].append({"name": "Invalid credentials", "status": "PASS"})
            else:
                print("❌ Invalid credentials not handled properly")
                test_results["failed"] += 1
                test_results["tests"].append({"name": "Invalid credentials", "status": "FAIL"})
        except:
            print("❌ Error testing invalid credentials")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "Invalid credentials", "status": "FAIL"})

        # Test 3: Missing fields validation
        print("\n[TEST] Missing fields validation...")
        try:
            response = requests.post("http://localhost:5002/api/auth/login",
                                    json={"username": "test"},
                                    timeout=5)
            if response.status_code == 400 and "required" in response.text.lower():
                print("✅ Missing fields validation works")
                test_results["passed"] += 1
                test_results["tests"].append({"name": "Missing fields validation", "status": "PASS"})
            else:
                print("❌ Missing fields validation failed")
                test_results["failed"] += 1
                test_results["tests"].append({"name": "Missing fields validation", "status": "FAIL"})
        except:
            print("❌ Error testing missing fields")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "Missing fields validation", "status": "FAIL"})

        self.results.append(test_results)
        return test_results

    def run_integration_tests(self):
        """Run integration tests"""
        print("\n" + "="*60)
        print("RUNNING INTEGRATION TESTS")
        print("="*60)

        test_results = {
            "suite": "Integration Tests",
            "tests": [],
            "passed": 0,
            "failed": 0
        }

        # Test 1: Database connectivity
        print("\n[TEST] Database connectivity...")
        import sqlite3
        try:
            conn = sqlite3.connect("../mcp_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM agents")
            count = cursor.fetchone()[0]
            conn.close()
            print(f"✅ Database connected, {count} agents found")
            test_results["passed"] += 1
            test_results["tests"].append({"name": "Database connectivity", "status": "PASS"})
        except:
            print("❌ Database connectivity failed")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "Database connectivity", "status": "FAIL"})

        # Test 2: MCP server availability
        print("\n[TEST] MCP server availability...")
        try:
            import requests
            response = requests.post("http://localhost:9999/jsonrpc",
                                    json={"jsonrpc": "2.0", "method": "ping", "id": 1},
                                    timeout=5)
            print("✅ MCP server is responding")
            test_results["passed"] += 1
            test_results["tests"].append({"name": "MCP server availability", "status": "PASS"})
        except:
            print("❌ MCP server not available")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "MCP server availability", "status": "FAIL"})

        # Test 3: Inter-agent communication
        print("\n[TEST] Inter-agent communication...")
        cmd = 'source ../agent_tools.sh && send_message test_runner testing "Integration test message" 2>&1'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable='/bin/bash')
        if "Message sent" in result.stdout:
            print("✅ Inter-agent communication working")
            test_results["passed"] += 1
            test_results["tests"].append({"name": "Inter-agent communication", "status": "PASS"})
        else:
            print("❌ Inter-agent communication failed")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "Inter-agent communication", "status": "FAIL"})

        self.results.append(test_results)
        return test_results

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("TEST EXECUTION SUMMARY")
        print("="*60)

        total_passed = sum(r["passed"] for r in self.results)
        total_failed = sum(r["failed"] for r in self.results)
        total_tests = total_passed + total_failed

        print(f"\nExecution Time: {self.end_time - self.start_time:.2f} seconds")
        print(f"Total Tests Run: {total_tests}")
        print(f"Passed: {total_passed} ({(total_passed/total_tests*100):.1f}%)")
        print(f"Failed: {total_failed} ({(total_failed/total_tests*100):.1f}%)")

        print("\nDetailed Results by Suite:")
        print("-" * 40)
        for result in self.results:
            print(f"\n{result['suite']}:")
            print(f"  Passed: {result['passed']}")
            print(f"  Failed: {result['failed']}")

            if result['failed'] > 0:
                print("  Failed tests:")
                for test in result['tests']:
                    if test['status'] == 'FAIL':
                        print(f"    - {test['name']}")

        # Write JSON report
        report = {
            "timestamp": datetime.now().isoformat(),
            "execution_time": f"{self.end_time - self.start_time:.2f}s",
            "summary": {
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "pass_rate": f"{(total_passed/total_tests*100):.1f}%"
            },
            "suites": self.results
        }

        with open("test_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print("\n✅ Full report saved to test_report.json")

        return total_failed == 0

    def run_all(self):
        """Run all test suites"""
        self.start_time = time.time()

        print("\n" + "="*60)
        print("STARTING FULL REGRESSION TEST SUITE")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        # Run all test suites
        self.run_shell_tests()
        self.run_auth_api_tests()
        self.run_integration_tests()

        self.end_time = time.time()

        # Generate report
        success = self.generate_report()

        if success:
            print("\n🎉 ALL TESTS PASSED! 🎉")
        else:
            print("\n⚠️ SOME TESTS FAILED - Review report for details")

        return success

if __name__ == "__main__":
    runner = TestSuiteRunner()
    success = runner.run_all()
    sys.exit(0 if success else 1)