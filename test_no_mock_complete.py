#!/usr/bin/env python3
"""
Test completo per verificare che il sistema funzioni senza mock
Testa sia backend che frontend per assicurare dati reali
"""

import requests
import json
import sqlite3
import time
import sys

def test_database_data():
    """Verifica che ci siano dati reali nel database"""
    print("\n🗄️  Testing Database Data...")

    conn = sqlite3.connect('mcp_system.db')
    cursor = conn.cursor()

    tables = {
        'agent_states': 'SELECT COUNT(*) FROM agent_states',
        'activities': 'SELECT COUNT(*) FROM activities',
        'tasks': 'SELECT COUNT(*) FROM tasks',
        'messages': 'SELECT COUNT(*) FROM messages'
    }

    all_good = True
    for table, query in tables.items():
        cursor.execute(query)
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"  ✅ {table}: {count} records")
        else:
            print(f"  ⚠️  {table}: EMPTY")
            all_good = False

    conn.close()
    return all_good

def test_main_api():
    """Test Main API endpoints (port 5001)"""
    print("\n🔌 Testing Main API (port 5001)...")

    base_url = "http://localhost:5001"
    endpoints = [
        ("/api/agents", "Agents"),
        ("/api/tasks", "Tasks"),
        ("/api/messages", "Messages"),
        ("/api/system/status", "System Status"),
        ("/api/system/metrics", "System Metrics"),
        ("/api/mcp/status", "MCP Status")
    ]

    all_good = True
    for endpoint, name in endpoints:
        try:
            response = requests.get(base_url + endpoint, timeout=2)

            if response.status_code == 200:
                data = response.json()

                # Check for mock indicators
                data_str = str(data).lower()
                has_mock = 'mock' in data_str or 'sample' in data_str or 'dummy' in data_str

                if has_mock:
                    print(f"  ⚠️  {name}: Contains mock data")
                    all_good = False
                elif isinstance(data, list) and len(data) == 0:
                    print(f"  ⚠️  {name}: Empty response")
                elif isinstance(data, dict) and not data:
                    print(f"  ⚠️  {name}: Empty dict")
                else:
                    print(f"  ✅ {name}: Real data")
            elif response.status_code == 401:
                print(f"  🔐 {name}: Requires auth")
            else:
                print(f"  ❌ {name}: Status {response.status_code}")
                all_good = False

        except requests.exceptions.Timeout:
            print(f"  ❌ {name}: Timeout")
            all_good = False
        except requests.exceptions.ConnectionError:
            print(f"  ❌ {name}: Connection failed")
            all_good = False
        except Exception as e:
            print(f"  ❌ {name}: {str(e)[:30]}")
            all_good = False

    return all_good

def test_gateway_api():
    """Test Gateway API endpoints (port 8888)"""
    print("\n🌉 Testing Gateway API (port 8888)...")

    base_url = "http://localhost:8888"
    endpoints = [
        ("/api/system/health", "Health"),
        ("/api/queue/tasks", "Queue Tasks"),
        ("/api/queue/stats", "Queue Stats"),
        ("/api/inbox/messages", "Inbox Messages"),
        ("/api/logs", "Logs"),
        ("/api/workflows", "Workflows")
    ]

    all_good = True
    for endpoint, name in endpoints:
        try:
            response = requests.get(base_url + endpoint, timeout=2)

            if response.status_code == 200:
                data = response.json()

                # Check for mock indicators
                data_str = str(data).lower()
                has_mock = 'mock' in data_str or 'sample' in data_str or 'dummy' in data_str

                if has_mock:
                    print(f"  ⚠️  {name}: Contains mock data")
                    all_good = False
                else:
                    print(f"  ✅ {name}: Real data")
            else:
                print(f"  ❌ {name}: Status {response.status_code}")
                all_good = False

        except Exception as e:
            print(f"  ❌ {name}: {str(e)[:30]}")
            all_good = False

    return all_good

def test_inbox_functionality():
    """Test inbox CRUD operations"""
    print("\n📬 Testing Inbox Functionality...")

    base_url = "http://localhost:8888"

    # 1. Create a message
    new_message = {
        "from": "test-agent",
        "to": "supervisor",
        "subject": "Test Message",
        "content": "This is a real test message",
        "priority": "normal",
        "type": "notification"
    }

    try:
        response = requests.post(
            f"{base_url}/api/inbox/messages",
            json=new_message,
            timeout=2
        )

        if response.status_code == 200:
            created = response.json()
            message_id = created.get('id')
            print(f"  ✅ Create message: ID {message_id}")

            # 2. Read messages
            response = requests.get(f"{base_url}/api/inbox/messages", timeout=2)
            if response.status_code == 200:
                messages = response.json()
                print(f"  ✅ Read messages: {len(messages)} total")

                # 3. Mark as read
                if message_id:
                    response = requests.patch(
                        f"{base_url}/api/inbox/messages/{message_id}/read",
                        timeout=2
                    )
                    if response.status_code == 200:
                        print(f"  ✅ Mark as read: Success")
                    else:
                        print(f"  ❌ Mark as read: Failed")
            else:
                print(f"  ❌ Read messages: Failed")
        else:
            print(f"  ❌ Create message: Failed")

    except Exception as e:
        print(f"  ❌ Inbox test failed: {e}")
        return False

    return True

def test_frontend_endpoints():
    """Verify frontend can access all required endpoints"""
    print("\n🎨 Testing Frontend Requirements...")

    critical_endpoints = [
        ("http://localhost:5001/api/mcp/status", "MCP Status"),
        ("http://localhost:5001/api/agents", "Agents List"),
        ("http://localhost:8888/api/inbox/messages", "Inbox"),
        ("http://localhost:8888/api/queue/tasks", "Queue")
    ]

    all_good = True
    for url, name in critical_endpoints:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code in [200, 401]:  # 401 is ok, just needs auth
                print(f"  ✅ {name}: Accessible")
            else:
                print(f"  ❌ {name}: Not accessible")
                all_good = False
        except:
            print(f"  ❌ {name}: Failed to connect")
            all_good = False

    return all_good

def main():
    print("="*60)
    print("🧪 COMPLETE NO-MOCK SYSTEM TEST")
    print("="*60)

    results = {
        "Database": test_database_data(),
        "Main API": test_main_api(),
        "Gateway API": test_gateway_api(),
        "Inbox": test_inbox_functionality(),
        "Frontend Ready": test_frontend_endpoints()
    }

    print("\n" + "="*60)
    print("📊 FINAL RESULTS:")
    print("="*60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")

    all_passed = all(results.values())

    print("\n" + "="*60)
    if all_passed:
        print("🎉 SUCCESS: System is running WITHOUT mock data!")
        print("All endpoints return real data from database.")
    else:
        print("⚠️  Some components still need real implementation")
    print("="*60)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())