#!/usr/bin/env python3
"""
Authentication API Test Suite
Tests for login, registration, and auth validation endpoints
"""

import json
import requests
import unittest
import time
import sys
import os
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestAuthenticationAPI(unittest.TestCase):
    """Test suite for authentication API endpoints"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.base_url = "http://localhost:5002"
        cls.login_endpoint = f"{cls.base_url}/api/auth/login"
        cls.register_endpoint = f"{cls.base_url}/api/auth/register"
        cls.headers = {"Content-Type": "application/json"}

    def test_01_login_missing_credentials(self):
        """Test login with missing credentials"""
        print("\n[TEST] Testing login with missing credentials...")

        # Test missing password
        data = {"username": "testuser"}
        response = requests.post(self.login_endpoint, json=data)

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "Username and password required")

        print("✅ Missing password test passed")

        # Test missing username
        data = {"password": "testpass"}
        response = requests.post(self.login_endpoint, json=data)

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

        print("✅ Missing username test passed")

    def test_02_login_empty_credentials(self):
        """Test login with empty credentials"""
        print("\n[TEST] Testing login with empty credentials...")

        data = {"username": "", "password": ""}
        response = requests.post(self.login_endpoint, json=data)

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "Username and password required")

        print("✅ Empty credentials test passed")

    def test_03_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        print("\n[TEST] Testing login with invalid credentials...")

        data = {"username": "invaliduser", "password": "wrongpass"}
        response = requests.post(self.login_endpoint, json=data)

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "Invalid credentials")

        print("✅ Invalid credentials test passed")

    def test_04_login_sql_injection(self):
        """Test SQL injection prevention"""
        print("\n[TEST] Testing SQL injection prevention...")

        # Common SQL injection attempts
        injections = [
            {"username": "' OR '1'='1", "password": "password"},
            {"username": "admin'--", "password": "password"},
            {"username": "'; DROP TABLE users;--", "password": "password"},
            {"username": "admin", "password": "' OR '1'='1"}
        ]

        for data in injections:
            response = requests.post(self.login_endpoint, json=data)

            # Should return invalid credentials, not SQL error
            self.assertIn(response.status_code, [400, 401])
            self.assertIn("error", response.json())

        print("✅ SQL injection prevention test passed")

    def test_05_login_xss_prevention(self):
        """Test XSS prevention"""
        print("\n[TEST] Testing XSS prevention...")

        data = {
            "username": "<script>alert('XSS')</script>",
            "password": "<img src=x onerror=alert('XSS')>"
        }
        response = requests.post(self.login_endpoint, json=data)

        # Should handle safely without executing scripts
        self.assertIn(response.status_code, [400, 401])

        # Response should not contain unescaped script tags
        response_text = response.text
        self.assertNotIn("<script>", response_text)

        print("✅ XSS prevention test passed")

    def test_06_login_rate_limiting(self):
        """Test rate limiting"""
        print("\n[TEST] Testing rate limiting...")

        data = {"username": "testuser", "password": "wrongpass"}

        # Send multiple rapid requests
        responses = []
        for i in range(20):
            response = requests.post(self.login_endpoint, json=data)
            responses.append(response.status_code)

        # Check if rate limiting is applied (optional based on implementation)
        # This is informational - not all APIs implement rate limiting
        if 429 in responses:
            print("✅ Rate limiting detected (429 Too Many Requests)")
        else:
            print("⚠️ No rate limiting detected (consider implementing)")

    def test_07_login_special_characters(self):
        """Test handling of special characters"""
        print("\n[TEST] Testing special characters handling...")

        special_chars = [
            {"username": "user@example.com", "password": "p@$$w0rd!"},
            {"username": "user_name-123", "password": "pass#word$"},
            {"username": "用户名", "password": "密码"},  # Unicode
            {"username": "user👤", "password": "pass🔒"}  # Emojis
        ]

        for data in special_chars:
            response = requests.post(self.login_endpoint, json=data)

            # Should handle gracefully
            self.assertIn(response.status_code, [400, 401])
            self.assertIsInstance(response.json(), dict)

        print("✅ Special characters test passed")

    def test_08_login_large_payload(self):
        """Test handling of large payloads"""
        print("\n[TEST] Testing large payload handling...")

        # Create a large string (1MB)
        large_string = "a" * (1024 * 1024)
        data = {"username": large_string, "password": "password"}

        try:
            response = requests.post(self.login_endpoint, json=data, timeout=5)
            # Should reject or handle gracefully
            self.assertIn(response.status_code, [400, 401, 413, 431])
        except requests.exceptions.Timeout:
            print("⚠️ Request timed out (consider payload size limits)")
        except Exception as e:
            print(f"⚠️ Large payload handling: {e}")

        print("✅ Large payload test completed")

    def test_09_content_type_validation(self):
        """Test content type validation"""
        print("\n[TEST] Testing content type validation...")

        data = {"username": "testuser", "password": "testpass"}

        # Test with wrong content type
        headers = {"Content-Type": "text/plain"}
        response = requests.post(self.login_endpoint, data=json.dumps(data), headers=headers)

        # Should either process or return appropriate error
        self.assertIn(response.status_code, [400, 401, 415])

        print("✅ Content type validation test passed")

    def test_10_registration_endpoint(self):
        """Test registration endpoint availability"""
        print("\n[TEST] Testing registration endpoint...")

        data = {
            "username": "newuser",
            "password": "newpass123",
            "email": "newuser@example.com"
        }

        try:
            response = requests.post(self.register_endpoint, json=data, timeout=5)

            if response.status_code == 404:
                print("⚠️ Registration endpoint not implemented yet")
            else:
                print(f"✅ Registration endpoint responded with status {response.status_code}")

        except requests.exceptions.ConnectionError:
            print("⚠️ Registration endpoint not available")
        except Exception as e:
            print(f"⚠️ Registration endpoint error: {e}")

def run_tests():
    """Run all authentication tests"""
    print("=" * 60)
    print("AUTHENTICATION API TEST SUITE")
    print("=" * 60)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAuthenticationAPI)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return test results
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)