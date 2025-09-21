#!/usr/bin/env python3
"""
Test suite for MCP (Model Context Protocol) tools
Tests all agent tools and database operations
"""

import json
import sqlite3
import subprocess
import time
import unittest
from datetime import datetime
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestMCPTools(unittest.TestCase):
    """Test suite for MCP agent tools"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.mcp_url = "http://localhost:9999/jsonrpc"
        cls.test_agent = "test_agent"
        cls.db_path = "mcp_system.db"
        cls.inbox_db = "langgraph-test/shared_inbox.db"

    def test_01_heartbeat(self):
        """Test agent heartbeat functionality"""
        print("\n[TEST] Testing heartbeat...")

        # Send heartbeat via curl
        cmd = f'''curl -s -X POST {self.mcp_url} -H "Content-Type: application/json" -d '{{"jsonrpc":"2.0","method":"tools/call","params":{{"name":"heartbeat","arguments":{{"agent":"{self.test_agent}"}}}},"id":1}}' '''

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        response = json.loads(result.stdout)

        # Check response
        self.assertIn("result", response)
        self.assertEqual(response["result"]["status"], "alive")
        print("✅ Heartbeat test passed")

    def test_02_status_update(self):
        """Test status update functionality"""
        print("\n[TEST] Testing status update...")

        statuses = ["idle", "busy", "error"]
        for status in statuses:
            cmd = f'''curl -s -X POST {self.mcp_url} -H "Content-Type: application/json" -d '{{"jsonrpc":"2.0","method":"tools/call","params":{{"name":"update_status","arguments":{{"agent":"{self.test_agent}","status":"{status}","task":"Testing status {status}"}}}},"id":1}}' '''

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            response = json.loads(result.stdout)

            self.assertIn("result", response)
            self.assertEqual(response["result"]["status"], "updated")

        print("✅ Status update test passed")

    def test_03_activity_logging(self):
        """Test activity logging"""
        print("\n[TEST] Testing activity logging...")

        activities = [
            ("test", "Running unit tests", '{"test_type":"unit","status":"running"}'),
            ("error", "Test error occurred", '{"error_code":500,"message":"test error"}'),
            ("success", "Test completed", '{"tests_passed":10,"tests_failed":0}')
        ]

        for category, activity, details in activities:
            cmd = f'''curl -s -X POST {self.mcp_url} -H "Content-Type: application/json" -d '{{"jsonrpc":"2.0","method":"tools/call","params":{{"name":"log_activity","arguments":{{"agent":"{self.test_agent}","category":"{category}","activity":"{activity}","details":{details}}}}},"id":1}}' '''

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            response = json.loads(result.stdout)

            self.assertIn("result", response)
            self.assertEqual(response["result"]["status"], "logged")

        print("✅ Activity logging test passed")

    def test_04_database_operations(self):
        """Test direct database operations"""
        print("\n[TEST] Testing database operations...")

        # Test agents table
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if test agent exists
        cursor.execute("SELECT * FROM agents WHERE id = ?", (self.test_agent,))
        agent = cursor.fetchone()
        self.assertIsNotNone(agent, "Test agent should exist in database")

        # Check activity logs
        cursor.execute("SELECT COUNT(*) FROM activity_logs WHERE agent_id = ?", (self.test_agent,))
        count = cursor.fetchone()[0]
        self.assertGreater(count, 0, "Should have activity logs")

        conn.close()
        print("✅ Database operations test passed")

    def test_05_message_system(self):
        """Test inter-agent messaging"""
        print("\n[TEST] Testing message system...")

        # Create test message
        import uuid
        message_id = str(uuid.uuid4())
        sender = self.test_agent
        recipient = "supervisor"
        message = "Test message from unit tests"

        conn = sqlite3.connect(self.inbox_db)
        cursor = conn.cursor()

        # Insert test message
        cursor.execute('''
            INSERT INTO messages (message_id, sender_id, recipient_id, message_type, subject, content, timestamp, status)
            VALUES (?, ?, ?, 'direct', ?, ?, ?, 'sent')
        ''', (message_id, sender, recipient, message, message, datetime.now().isoformat()))

        conn.commit()

        # Verify message was inserted
        cursor.execute("SELECT * FROM messages WHERE message_id = ?", (message_id,))
        msg = cursor.fetchone()
        self.assertIsNotNone(msg, "Message should be in database")

        conn.close()
        print("✅ Message system test passed")

    def test_06_agent_health_check(self):
        """Test agent health monitoring"""
        print("\n[TEST] Testing agent health check...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check agent health
        cursor.execute('''
            SELECT id, status,
                   CASE
                       WHEN last_heartbeat > datetime('now', '-60 seconds') THEN 'Active'
                       ELSE 'Inactive'
                   END as health
            FROM agents
            WHERE id = ?
        ''', (self.test_agent,))

        result = cursor.fetchone()
        self.assertIsNotNone(result, "Agent health data should exist")

        conn.close()
        print("✅ Agent health check test passed")

    def test_07_concurrent_operations(self):
        """Test concurrent agent operations"""
        print("\n[TEST] Testing concurrent operations...")

        import concurrent.futures
        import random

        def send_heartbeat(agent_id):
            cmd = f'''curl -s -X POST {self.mcp_url} -H "Content-Type: application/json" -d '{{"jsonrpc":"2.0","method":"tools/call","params":{{"name":"heartbeat","arguments":{{"agent":"test_{agent_id}"}}}},"id":1}}' '''
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return json.loads(result.stdout)

        # Send multiple concurrent heartbeats
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(send_heartbeat, i) for i in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed
        for result in results:
            self.assertIn("result", result)
            self.assertEqual(result["result"]["status"], "alive")

        print("✅ Concurrent operations test passed")

    def test_08_error_handling(self):
        """Test error handling"""
        print("\n[TEST] Testing error handling...")

        # Test with invalid JSON
        cmd = f'''curl -s -X POST {self.mcp_url} -H "Content-Type: application/json" -d 'invalid json' '''
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        # Should return error response
        if result.stdout:
            response = json.loads(result.stdout)
            self.assertIn("error", response)

        # Test with missing required fields
        cmd = f'''curl -s -X POST {self.mcp_url} -H "Content-Type: application/json" -d '{{"jsonrpc":"2.0","method":"tools/call","params":{{"name":"update_status","arguments":{{}}}},"id":1}}' '''
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.stdout:
            response = json.loads(result.stdout)
            self.assertIn("error", response)

        print("✅ Error handling test passed")

def run_tests():
    """Run all MCP tool tests"""
    print("=" * 60)
    print("MCP TOOLS TEST SUITE")
    print("=" * 60)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMCPTools)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return test results
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)