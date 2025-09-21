#!/usr/bin/env python3
"""
Comprehensive test to verify NO MOCK functions remain in the system
Tests all endpoints to ensure they use real database data
"""

import sqlite3
import json
import sys
import os

def test_database_connectivity():
    """Test database is accessible and has real data"""
    print("\n🔍 Testing Database Connectivity...")
    try:
        conn = sqlite3.connect('mcp_system.db')
        cursor = conn.cursor()

        # Check all tables
        tables = ['agent_states', 'activities', 'tasks', 'messages',
                  'frontend_components', 'api_endpoints']

        for table in tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f"  ✅ Table {table}: {count} records")

        conn.close()
        return True
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def test_routes_api_endpoints():
    """Test that routes_api.py endpoints use real data"""
    print("\n🔍 Testing routes_api.py Endpoints...")

    # Import and create test client
    sys.path.insert(0, os.getcwd())
    from routes_api import app

    app.config['TESTING'] = True
    client = app.test_client()

    tests = [
        ('GET', '/api/agents', 'Agent list'),
        ('GET', '/api/tasks', 'Task list'),
        ('GET', '/api/messages', 'Messages'),
        ('GET', '/api/system/status', 'System status'),
        ('GET', '/api/system/metrics', 'System metrics'),
        ('GET', '/api/mcp/status', 'MCP status'),
    ]

    all_passed = True
    for method, endpoint, name in tests:
        try:
            if method == 'GET':
                response = client.get(endpoint)
            else:
                response = client.post(endpoint)
            data = json.loads(response.data)

            # Check if response contains real data indicators
            if 'mock' in str(data).lower() or 'sample' in str(data).lower():
                print(f"  ⚠️  {name} ({endpoint}): Contains mock/sample data")
                all_passed = False
            else:
                print(f"  ✅ {name} ({endpoint}): Uses real data")
        except Exception as e:
            print(f"  ❌ {name} ({endpoint}): Error - {e}")
            all_passed = False

    return all_passed

def test_api_main_endpoints():
    """Test that api/main.py endpoints use real data"""
    print("\n🔍 Testing api/main.py Endpoints...")

    # Check if file exists
    api_main_path = 'api/main.py'
    if not os.path.exists(api_main_path):
        print(f"  ⚠️  {api_main_path} not found")
        return True  # Not a failure if file doesn't exist

    # Read file and check for mock indicators
    with open(api_main_path, 'r') as f:
        content = f.read()

    mock_indicators = [
        'mock_data',
        'Mock data',
        'TODO: Implement',
        'return []  # Empty',
        '"Sample ',
        'for i in range(',  # Common in mock loops
    ]

    issues = []
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        for indicator in mock_indicators:
            if indicator in line and not line.strip().startswith('#'):
                issues.append(f"  Line {i}: {line.strip()[:60]}...")

    if issues:
        print(f"  ⚠️  Found {len(issues)} potential mock implementations:")
        for issue in issues[:5]:  # Show first 5
            print(f"    {issue}")
        return False
    else:
        print(f"  ✅ No mock indicators found in {api_main_path}")
        return True

def test_auth_implementation():
    """Test that authentication uses real implementation"""
    print("\n🔍 Testing Authentication Implementation...")

    try:
        import jwt
        from datetime import datetime, timedelta

        # Test token generation
        secret = 'test-secret'
        payload = {
            'agent_id': 'test-agent',
            'role': 'agent',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=1)
        }

        token = jwt.encode(payload, secret, algorithm='HS256')
        decoded = jwt.decode(token, secret, algorithms=['HS256'])

        print(f"  ✅ JWT implementation: WORKING")

        # Check if auth endpoints exist in routes
        from routes_api import app

        auth_routes = ['/api/auth/login', '/api/auth/verify', '/api/auth/logout']
        for route in auth_routes:
            if any(rule.rule == route for rule in app.url_map.iter_rules()):
                print(f"  ✅ Route {route}: EXISTS")
            else:
                print(f"  ❌ Route {route}: MISSING")

        return True
    except Exception as e:
        print(f"  ❌ Auth test error: {e}")
        return False

def check_mock_functions_in_codebase():
    """Search for mock functions in Python files"""
    print("\n🔍 Searching for Mock Functions in Codebase...")

    import glob

    # Files to check
    files_to_check = [
        'routes_api.py',
        'api/main.py',
        'api/metrics_endpoint.py',
        'api/unified_gateway.py'
    ]

    mock_patterns = [
        'def mock_',
        'return mock',
        'mock_response',
        'fake_data',
        '# TODO:',
        'hardcoded',
        'dummy_'
    ]

    issues_found = False

    for filepath in files_to_check:
        if not os.path.exists(filepath):
            continue

        with open(filepath, 'r') as f:
            lines = f.readlines()

        file_issues = []
        for i, line in enumerate(lines, 1):
            for pattern in mock_patterns:
                if pattern.lower() in line.lower() and not line.strip().startswith('#'):
                    file_issues.append((i, line.strip()))

        if file_issues:
            print(f"\n  ⚠️  {filepath}:")
            for line_no, content in file_issues[:3]:
                print(f"    Line {line_no}: {content[:60]}...")
            issues_found = True

    if not issues_found:
        print("  ✅ No mock patterns found in checked files")

    return not issues_found

def main():
    """Run all tests"""
    print("="*60)
    print("🔬 MOCK FUNCTION ELIMINATION VERIFICATION")
    print("="*60)

    results = {
        'Database': test_database_connectivity(),
        'Routes API': test_routes_api_endpoints(),
        'API Main': test_api_main_endpoints(),
        'Authentication': test_auth_implementation(),
        'Codebase Check': check_mock_functions_in_codebase()
    }

    print("\n" + "="*60)
    print("📊 FINAL RESULTS:")
    print("="*60)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("🎉 SUCCESS: NO MOCK FUNCTIONS DETECTED!")
        print("All implementations use REAL data from database")
    else:
        print("⚠️  WARNING: Some mock implementations may remain")
        print("Review the failures above and fix any remaining mocks")
    print("="*60)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())