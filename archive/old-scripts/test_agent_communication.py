#!/usr/bin/env python3
"""
Test Real Agent Communication
Simula una comunicazione reale tra agenti tramite MCP
"""

import json
import requests
import time
from datetime import datetime

MCP_URL = "http://localhost:8099/jsonrpc"

def call_mcp_tool(tool_name, arguments):
    """Chiama un tool MCP"""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": 1
    }

    response = requests.post(MCP_URL, json=payload)
    if response.status_code == 200:
        return response.json().get('result', {})
    return None

def simulate_agent_workflow():
    """Simula un workflow completo tra agenti"""

    print("=" * 60)
    print("🚀 STARTING AGENT COMMUNICATION TEST")
    print("=" * 60)

    # 1. Frontend-UI inizia un task
    print("\n1️⃣ FRONTEND-UI: Richiedo componente login")
    result = call_mcp_tool("log_activity", {
        "agent": "frontend-ui",
        "category": "task",
        "activity": "Need login component",
        "details": {"component": "LoginForm", "type": "React"}
    })
    print(f"   ✅ Activity logged: {result.get('id')}")

    # 2. Frontend-UI cambia stato a busy
    print("\n2️⃣ FRONTEND-UI: Cambio stato a busy")
    result = call_mcp_tool("update_status", {
        "agent": "frontend-ui",
        "status": "busy",
        "task": "login-form-creation"
    })
    print(f"   ✅ Status updated: {result.get('status')}")

    time.sleep(1)

    # 3. Backend-API riceve richiesta
    print("\n3️⃣ BACKEND-API: Ricevo richiesta per API login")
    result = call_mcp_tool("heartbeat", {
        "agent": "backend-api"
    })
    print(f"   ✅ Heartbeat: {result.get('status')}")

    result = call_mcp_tool("update_status", {
        "agent": "backend-api",
        "status": "busy",
        "task": "login-api-development"
    })
    print(f"   ✅ Status: busy on login API")

    # 4. Database agent interviene
    print("\n4️⃣ DATABASE: Creo schema users")
    result = call_mcp_tool("log_activity", {
        "agent": "database",
        "category": "task",
        "activity": "Creating users table",
        "details": {
            "schema": "users",
            "fields": ["id", "email", "password_hash", "created_at"]
        }
    })
    print(f"   ✅ Schema created: {result.get('id')}")

    time.sleep(1)

    # 5. Backend completa API
    print("\n5️⃣ BACKEND-API: API login completata")
    result = call_mcp_tool("log_activity", {
        "agent": "backend-api",
        "category": "task",
        "activity": "Login API completed",
        "details": {
            "endpoints": ["/api/login", "/api/logout", "/api/refresh"],
            "status": "ready"
        }
    })
    print(f"   ✅ API ready: {result.get('id')}")

    result = call_mcp_tool("update_status", {
        "agent": "backend-api",
        "status": "idle"
    })
    print(f"   ✅ Status: idle")

    # 6. Frontend completa form
    print("\n6️⃣ FRONTEND-UI: Login form completato")
    result = call_mcp_tool("log_activity", {
        "agent": "frontend-ui",
        "category": "task",
        "activity": "Login form completed",
        "details": {
            "component": "LoginForm.tsx",
            "integrated_with": "backend-api"
        }
    })
    print(f"   ✅ Form completed: {result.get('id')}")

    result = call_mcp_tool("update_status", {
        "agent": "frontend-ui",
        "status": "idle"
    })

    time.sleep(1)

    # 7. Testing agent testa tutto
    print("\n7️⃣ TESTING: Inizio test integrazione")
    result = call_mcp_tool("update_status", {
        "agent": "testing",
        "status": "busy",
        "task": "login-integration-test"
    })
    print(f"   ✅ Testing started")

    result = call_mcp_tool("log_activity", {
        "agent": "testing",
        "category": "task",
        "activity": "Integration test passed",
        "details": {
            "tests_run": 15,
            "passed": 15,
            "failed": 0,
            "coverage": "92%"
        }
    })
    print(f"   ✅ All tests passed!")

    # 8. Supervisor approva
    print("\n8️⃣ SUPERVISOR: Approvo deployment")
    result = call_mcp_tool("log_activity", {
        "agent": "supervisor",
        "category": "task",
        "activity": "Login feature approved for deployment",
        "details": {
            "feature": "login-system",
            "approved_by": "supervisor",
            "ready_for": "production"
        }
    })
    print(f"   ✅ Approved: {result.get('id')}")

    print("\n" + "=" * 60)
    print("✅ WORKFLOW COMPLETATO CON SUCCESSO!")
    print("=" * 60)

    # Mostra statistiche finali
    print("\n📊 VERIFICA DATABASE:")

    import sqlite3

    # Check MCP database
    db = sqlite3.connect('mcp_system.db')
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM activity_logs")
    activities = cursor.fetchone()[0]
    print(f"   Activity logs: {activities}")

    cursor.execute("SELECT id, status FROM agents WHERE status='active'")
    active_agents = cursor.fetchall()
    print(f"   Active agents: {len(active_agents)}")
    for agent in active_agents:
        print(f"      - {agent[0]}: {agent[1]}")

    db.close()

    # Check inbox
    inbox_db = sqlite3.connect('langgraph-test/shared_inbox.db')
    cursor = inbox_db.cursor()

    cursor.execute("SELECT COUNT(*) FROM messages WHERE date(timestamp) = date('now')")
    today_messages = cursor.fetchone()[0]
    print(f"   Messages today: {today_messages}")

    cursor.execute("""
        SELECT sender_id, subject
        FROM messages
        WHERE date(timestamp) = date('now')
        ORDER BY timestamp DESC
        LIMIT 5
    """)
    recent = cursor.fetchall()
    print("   Recent messages:")
    for msg in recent:
        print(f"      - {msg[0]}: {msg[1]}")

    inbox_db.close()

if __name__ == "__main__":
    simulate_agent_workflow()