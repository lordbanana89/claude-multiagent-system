#!/usr/bin/env python3
"""
Phase 4: End-to-End Testing Suite
Comprehensive validation of deployed system
"""

import json
import time
import requests
import sqlite3
import subprocess
from datetime import datetime

class EndToEndTests:
    def __init__(self):
        self.mcp_url = "http://localhost:9999/jsonrpc"
        self.auth_url = "http://localhost:5002/api/auth/login"
        self.results = []

    def test_agent_workflow(self):
        """Test complete agent workflow"""
        print("\n[E2E] Testing Agent Workflow...")

        try:
            # 1. Send heartbeat
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "heartbeat",
                    "arguments": {"agent": "e2e_test"}
                },
                "id": 1
            }
            response = requests.post(self.mcp_url, json=payload, timeout=5)
            assert response.status_code == 200
            assert "result" in response.json()

            # 2. Update status
            payload["params"]["name"] = "update_status"
            payload["params"]["arguments"] = {
                "agent": "e2e_test",
                "status": "busy",
                "task": "E2E testing"
            }
            payload["id"] = 2
            response = requests.post(self.mcp_url, json=payload, timeout=5)
            assert response.status_code == 200

            # 3. Log activity
            payload["params"]["name"] = "log_activity"
            payload["params"]["arguments"] = {
                "agent": "e2e_test",
                "category": "test",
                "activity": "End-to-end test",
                "details": {"phase": 4}
            }
            payload["id"] = 3
            response = requests.post(self.mcp_url, json=payload, timeout=5)
            assert response.status_code == 200

            print("   ✅ Agent workflow test PASSED")
            return True

        except Exception as e:
            print(f"   ❌ Agent workflow test FAILED: {e}")
            return False

    def test_database_operations(self):
        """Test database CRUD operations"""
        print("\n[E2E] Testing Database Operations...")

        try:
            conn = sqlite3.connect("mcp_system.db")
            cursor = conn.cursor()

            # Read
            cursor.execute("SELECT COUNT(*) FROM agents")
            count = cursor.fetchone()[0]
            assert count > 0

            # Verify activity logs
            cursor.execute("SELECT COUNT(*) FROM activity_logs WHERE agent_id = 'e2e_test'")
            logs = cursor.fetchone()[0]
            assert logs > 0

            conn.close()
            print("   ✅ Database operations test PASSED")
            return True

        except Exception as e:
            print(f"   ❌ Database operations test FAILED: {e}")
            return False

    def test_message_flow(self):
        """Test inter-agent messaging"""
        print("\n[E2E] Testing Message Flow...")

        try:
            import uuid
            conn = sqlite3.connect("langgraph-test/shared_inbox.db")
            cursor = conn.cursor()

            # Send test message
            msg_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO messages (message_id, sender_id, recipient_id,
                                    message_type, subject, content, timestamp, status)
                VALUES (?, ?, ?, 'direct', ?, ?, ?, 'sent')
            ''', (msg_id, "e2e_test", "testing", "E2E Test Message",
                  "Phase 4 validation", datetime.now().isoformat()))
            conn.commit()

            # Verify message
            cursor.execute("SELECT * FROM messages WHERE message_id = ?", (msg_id,))
            message = cursor.fetchone()
            assert message is not None

            conn.close()
            print("   ✅ Message flow test PASSED")
            return True

        except Exception as e:
            print(f"   ❌ Message flow test FAILED: {e}")
            return False

    def test_auth_flow(self):
        """Test authentication flow"""
        print("\n[E2E] Testing Authentication Flow...")

        try:
            # Invalid credentials
            response = requests.post(self.auth_url,
                                    json={"username": "invalid", "password": "wrong"},
                                    timeout=5)
            assert response.status_code == 401

            # Missing fields
            response = requests.post(self.auth_url,
                                    json={"username": "test"},
                                    timeout=5)
            assert response.status_code == 400

            print("   ✅ Authentication flow test PASSED")
            return True

        except Exception as e:
            print(f"   ❌ Authentication flow test FAILED: {e}")
            return False

    def run_all(self):
        """Run all E2E tests"""
        print("="*50)
        print("PHASE 4: END-TO-END TESTING")
        print("="*50)

        results = {
            "Agent Workflow": self.test_agent_workflow(),
            "Database Operations": self.test_database_operations(),
            "Message Flow": self.test_message_flow(),
            "Authentication Flow": self.test_auth_flow()
        }

        passed = sum(1 for v in results.values() if v)
        total = len(results)

        print(f"\nE2E Results: {passed}/{total} tests passed")
        return results, passed == total

if __name__ == "__main__":
    tester = EndToEndTests()
    results, success = tester.run_all()
    print("\n✅ E2E Testing Complete" if success else "\n⚠️ Some E2E tests failed")