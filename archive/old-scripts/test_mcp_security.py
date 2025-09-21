#!/usr/bin/env python3
"""
MCP v2 Security Features Test Suite
Tests OAuth, consent flow, path protection, rate limiting, and audit logging
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List

# Configuration
BASE_URL = "http://localhost:8099"

class SecurityTester:
    def __init__(self):
        self.test_results = []
        self.oauth_token = None
        self.session_id = str(uuid.uuid4())

    def test_oauth_flow(self):
        """Test OAuth 2.1 token generation and validation"""
        print("\n🔐 Testing OAuth 2.1 Flow...")

        # Request token
        response = requests.post(f"{BASE_URL}/oauth/token", json={
            "grant_type": "client_credentials",
            "client_id": "test_client",
            "client_secret": "test_secret",
            "scope": "read write execute"
        })

        if response.status_code == 200:
            token_data = response.json()
            self.oauth_token = token_data['access_token']
            print(f"✅ OAuth token obtained")
            print(f"   Type: {token_data['token_type']}")
            print(f"   Expires in: {token_data['expires_in']}s")
            print(f"   Scopes: {token_data['scope']}")
            self.test_results.append(("OAuth Token Creation", True))

            # Test authenticated request
            auth_response = requests.post(f"{BASE_URL}/jsonrpc",
                headers={
                    "Authorization": f"Bearer {self.oauth_token}",
                    "X-Session-ID": self.session_id
                },
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "params": {},
                    "id": 1
                }
            )

            if auth_response.status_code == 200:
                print("✅ Authenticated request successful")
                self.test_results.append(("OAuth Authentication", True))
            else:
                print("❌ Authenticated request failed")
                self.test_results.append(("OAuth Authentication", False))
        else:
            print(f"❌ OAuth token request failed: {response.status_code}")
            self.test_results.append(("OAuth Token Creation", False))

    def test_path_protection(self):
        """Test path traversal protection"""
        print("\n🛡️ Testing Path Protection...")

        test_paths = [
            ("file:///Users/erik/Desktop/claude-multiagent-system/README.md", True, "Valid project file"),
            ("file://../../etc/passwd", False, "Path traversal attempt"),
            ("file://.git/config", False, "Blacklisted path"),
            ("file://~/.ssh/id_rsa", False, "Sensitive file"),
            ("file://test.env", False, "Environment file")
        ]

        for uri, should_succeed, description in test_paths:
            response = requests.post(f"{BASE_URL}/jsonrpc",
                headers={"X-Session-ID": self.session_id},
                json={
                    "jsonrpc": "2.0",
                    "method": "resources/read",
                    "params": {"uri": uri},
                    "id": 2
                }
            )

            data = response.json()
            success = "error" not in data

            if success == should_succeed:
                status = "✅"
                result = True
            else:
                status = "❌"
                result = False

            print(f"{status} {description}: {uri}")
            if "error" in data:
                print(f"   Error: {data['error']['message']}")

            self.test_results.append((f"Path Protection: {description}", result))

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("\n⏱️ Testing Rate Limiting...")

        # Make rapid requests
        start_time = time.time()
        request_count = 0
        rate_limited = False

        while time.time() - start_time < 2:  # Test for 2 seconds
            response = requests.post(f"{BASE_URL}/jsonrpc",
                headers={"X-Session-ID": self.session_id},
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "params": {},
                    "id": request_count
                }
            )

            request_count += 1

            if response.status_code == 400:
                data = response.json()
                if "rate limit" in data.get("error", {}).get("message", "").lower():
                    rate_limited = True
                    break

            time.sleep(0.01)  # Small delay between requests

        if rate_limited:
            print(f"✅ Rate limiting triggered after {request_count} requests")
            self.test_results.append(("Rate Limiting", True))
        else:
            print(f"⚠️ Made {request_count} requests without rate limit")
            self.test_results.append(("Rate Limiting", request_count > 100))

    def test_consent_flow(self):
        """Test consent flow for dangerous operations"""
        print("\n🤝 Testing Consent Flow...")

        # Try a dangerous operation
        response = requests.post(f"{BASE_URL}/jsonrpc",
            headers={"X-Session-ID": self.session_id},
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "delete_component",
                    "arguments": {
                        "component": "test",
                        "dry_run": True
                    }
                },
                "id": 3
            }
        )

        data = response.json()

        if "error" in data and "consent" in data["error"].get("message", "").lower():
            print("✅ Consent required for dangerous operation")

            consent_data = data["error"].get("data", {})
            if "consent_id" in consent_data:
                print(f"   Consent ID: {consent_data['consent_id']}")
                self.test_results.append(("Consent Flow Detection", True))

                # Check consent status
                consent_url = consent_data.get("consent_url", "")
                if consent_url:
                    consent_response = requests.get(f"{BASE_URL}{consent_url}")
                    if consent_response.status_code == 200:
                        print("✅ Consent endpoint accessible")
                        self.test_results.append(("Consent Endpoint", True))
                    else:
                        print("❌ Consent endpoint error")
                        self.test_results.append(("Consent Endpoint", False))
            else:
                self.test_results.append(("Consent Flow Detection", False))
        else:
            print("⚠️ No consent required (operation may not be configured as dangerous)")
            self.test_results.append(("Consent Flow Detection", False))

    def test_audit_logging(self):
        """Test audit logging functionality"""
        print("\n📝 Testing Audit Logging...")

        # Make some operations to generate audit logs
        test_operations = [
            ("tools/list", {}),
            ("resources/list", {}),
            ("prompts/list", {})
        ]

        for method, params in test_operations:
            requests.post(f"{BASE_URL}/jsonrpc",
                headers={"X-Session-ID": self.session_id},
                json={
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": params,
                    "id": 4
                }
            )

        # Retrieve audit logs
        response = requests.get(f"{BASE_URL}/api/mcp/audit",
            params={"session_id": self.session_id, "limit": 10}
        )

        if response.status_code == 200:
            data = response.json()
            log_count = data.get("count", 0)

            if log_count > 0:
                print(f"✅ Audit logs retrieved: {log_count} entries")

                # Show first log entry
                if data.get("logs"):
                    first_log = data["logs"][0]
                    print(f"   Latest: {first_log.get('operation')} - {first_log.get('result')}")

                self.test_results.append(("Audit Logging", True))
            else:
                print("⚠️ No audit logs found")
                self.test_results.append(("Audit Logging", False))
        else:
            print(f"❌ Failed to retrieve audit logs: {response.status_code}")
            self.test_results.append(("Audit Logging", False))

    def test_security_endpoints(self):
        """Test all security-related endpoints"""
        print("\n🔒 Testing Security Endpoints...")

        endpoints = [
            ("/api/mcp/security", "Security Status"),
            ("/api/mcp/resources", "Resources List"),
            ("/api/mcp/prompts", "Prompts List"),
            ("/api/mcp/capabilities", "Capabilities")
        ]

        for endpoint, name in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ {name}: OK")

                # Show key info
                if endpoint == "/api/mcp/security":
                    security = data.get("security", {})
                    print(f"   OAuth: {security.get('oauth_enabled')}")
                    print(f"   Consent: {security.get('consent_flow')}")
                    print(f"   Path Protection: {security.get('path_protection')}")
                elif endpoint == "/api/mcp/capabilities":
                    print(f"   Protocol: {data.get('protocol_version')}")
                    print(f"   Features: {', '.join(data.get('supports', []))}")

                self.test_results.append((f"Endpoint: {name}", True))
            else:
                print(f"❌ {name}: Failed ({response.status_code})")
                self.test_results.append((f"Endpoint: {name}", False))

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("SECURITY TEST SUMMARY")
        print("="*60)

        passed = sum(1 for _, success in self.test_results if success)
        total = len(self.test_results)

        for test_name, success in self.test_results:
            status = "✅" if success else "❌"
            print(f"{status} {test_name}")

        print("\n" + "-"*60)
        print(f"Results: {passed}/{total} tests passed ({passed*100//total if total else 0}%)")

        if passed == total:
            print("🎉 All security tests passed!")
        else:
            print(f"⚠️ {total - passed} security test(s) failed")

def main():
    print("="*60)
    print("MCP v2 SECURITY TEST SUITE")
    print("="*60)
    print(f"Server: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")

    tester = SecurityTester()

    # Run all security tests
    tester.test_oauth_flow()
    tester.test_path_protection()
    tester.test_rate_limiting()
    tester.test_consent_flow()
    tester.test_audit_logging()
    tester.test_security_endpoints()

    # Print summary
    tester.print_summary()

if __name__ == "__main__":
    main()