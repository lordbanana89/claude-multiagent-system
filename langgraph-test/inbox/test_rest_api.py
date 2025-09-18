#!/usr/bin/env python3
"""
Test script for the authenticated REST API
"""

import requests
import json
from datetime import datetime


class APITester:
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        self.api_key = None

    def test_health(self):
        """Test health endpoint"""
        print("\n=== Testing Health Check ===")
        response = self.session.get(f"{self.base_url}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200

    def test_register(self, agent_id="test-agent-001", agent_name="Test Agent", role="agent"):
        """Test agent registration"""
        print(f"\n=== Registering Agent: {agent_id} ===")
        response = self.session.post(
            f"{self.base_url}/auth/register",
            json={
                "agent_id": agent_id,
                "agent_name": agent_name,
                "role": role
            }
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")

        if response.status_code == 201:
            self.api_key = data.get('api_key')
            print(f"API Key saved: {self.api_key}")

        return response.status_code == 201

    def test_login(self):
        """Test login with API key"""
        print("\n=== Testing Login ===")
        if not self.api_key:
            print("No API key available, skipping login test")
            return False

        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={"api_key": self.api_key}
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")

        if response.status_code == 200:
            self.token = data.get('token')
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
            print("Token saved and set in headers")

        return response.status_code == 200

    def test_get_me(self):
        """Test get current agent info"""
        print("\n=== Testing Get Current Agent ===")
        response = self.session.get(f"{self.base_url}/auth/me")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200

    def test_send_message(self, recipient_id="admin", content="Test message from API"):
        """Test sending a message"""
        print(f"\n=== Sending Message to {recipient_id} ===")
        response = self.session.post(
            f"{self.base_url}/messages/send",
            json={
                "recipient_id": recipient_id,
                "content": content,
                "subject": "Test Message",
                "priority": 2,
                "message_type": "direct"
            }
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")

        if response.status_code == 201:
            return data.get('message_id')
        return None

    def test_get_inbox(self):
        """Test getting inbox messages"""
        print("\n=== Getting Inbox ===")
        response = self.session.get(
            f"{self.base_url}/messages/inbox",
            params={"limit": 10, "unread_only": False}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200

    def test_mark_as_read(self, message_id):
        """Test marking message as read"""
        print(f"\n=== Marking Message {message_id} as Read ===")
        response = self.session.post(f"{self.base_url}/messages/{message_id}/read")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200

    def test_broadcast(self, content="Broadcast test message"):
        """Test broadcasting a message"""
        print("\n=== Testing Broadcast (requires permission) ===")
        response = self.session.post(
            f"{self.base_url}/messages/broadcast",
            json={
                "content": content,
                "subject": "Broadcast Test",
                "priority": 1
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code in [201, 403]  # 403 if no permission

    def test_admin_stats(self):
        """Test admin stats endpoint"""
        print("\n=== Testing Admin Stats (requires admin) ===")
        response = self.session.get(f"{self.base_url}/admin/stats")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code in [200, 403]  # 403 if not admin

    def test_refresh_token(self):
        """Test token refresh"""
        print("\n=== Testing Token Refresh ===")
        response = self.session.post(f"{self.base_url}/auth/refresh")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")

        if response.status_code == 200:
            self.token = data.get('token')
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
            print("New token saved and set in headers")

        return response.status_code == 200

    def test_logout(self):
        """Test logout"""
        print("\n=== Testing Logout ===")
        response = self.session.post(f"{self.base_url}/auth/logout")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n" + "="*50)
        print("Starting REST API Tests")
        print("="*50)

        results = {}

        # Test health check (no auth required)
        results['health'] = self.test_health()

        # Register a new agent
        results['register'] = self.test_register()

        # Login with API key
        results['login'] = self.test_login()

        # Test authenticated endpoints
        if self.token:
            results['get_me'] = self.test_get_me()

            # Send a message and get its ID
            message_id = self.test_send_message()
            results['send_message'] = message_id is not None

            # Get inbox
            results['get_inbox'] = self.test_get_inbox()

            # Mark message as read if we have one
            if message_id:
                results['mark_read'] = self.test_mark_as_read(message_id)

            # Test broadcast (might fail with permission error)
            results['broadcast'] = self.test_broadcast()

            # Test admin stats (might fail if not admin)
            results['admin_stats'] = self.test_admin_stats()

            # Test token refresh
            results['refresh_token'] = self.test_refresh_token()

            # Test logout
            results['logout'] = self.test_logout()

        # Print summary
        print("\n" + "="*50)
        print("Test Results Summary")
        print("="*50)
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name:20} {status}")

        total = len(results)
        passed = sum(1 for v in results.values() if v)
        print(f"\nTotal: {passed}/{total} tests passed")

        return passed == total


def test_admin_flow():
    """Test admin-specific functionality"""
    print("\n" + "="*50)
    print("Testing Admin Flow")
    print("="*50)

    tester = APITester()

    # Register admin agent
    print("\n=== Registering Admin Agent ===")
    tester.test_register("test-admin-001", "Test Admin", "admin")

    # Login as admin
    tester.test_login()

    if tester.token:
        # Test admin-specific endpoints
        print("\n=== Testing Admin Endpoints ===")

        # List all agents
        print("\n--- List Agents ---")
        response = tester.session.get(f"{tester.base_url}/admin/agents")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        # Get stats
        print("\n--- Get Stats ---")
        response = tester.session.get(f"{tester.base_url}/admin/stats")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        # Cleanup tokens
        print("\n--- Cleanup Tokens ---")
        response = tester.session.post(f"{tester.base_url}/admin/tokens/cleanup")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")


if __name__ == "__main__":
    # Run basic tests
    tester = APITester()
    success = tester.run_all_tests()

    # Run admin tests
    test_admin_flow()

    if success:
        print("\n✅ All basic tests passed!")
    else:
        print("\n❌ Some tests failed!")