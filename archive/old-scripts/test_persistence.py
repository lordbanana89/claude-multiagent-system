#!/usr/bin/env python3
import sqlite3
import json
import uuid
from datetime import datetime

def test_persistence():
    conn = sqlite3.connect('mcp_system.db')
    cursor = conn.cursor()
    
    print("🧪 Testing MCP Persistence Operations")
    
    # Test 1: Create a state checkpoint
    state_id = str(uuid.uuid4())
    state_data = {
        "agent": "database",
        "status": "testing",
        "memory": {"last_task": "persistence_setup"},
        "timestamp": datetime.now().isoformat()
    }
    
    cursor.execute("""
        INSERT INTO mcp_states (state_id, agent_id, state_type, state_data, metadata)
        VALUES (?, ?, ?, ?, ?)
    """, (state_id, 'database', 'checkpoint', json.dumps(state_data), '{"test": true}'))
    
    print("✅ Test 1: State checkpoint created")
    
    # Test 2: Create a transaction
    trans_id = str(uuid.uuid4())
    operations = [
        {"action": "update_status", "params": {"status": "busy"}},
        {"action": "log_activity", "params": {"category": "test"}}
    ]
    
    cursor.execute("""
        INSERT INTO mcp_transactions (transaction_id, agent_id, transaction_type, operations)
        VALUES (?, ?, ?, ?)
    """, (trans_id, 'database', 'task', json.dumps(operations)))
    
    print("✅ Test 2: Transaction created")
    
    # Test 3: Create a session
    session_id = str(uuid.uuid4())
    session_token = str(uuid.uuid4())
    
    cursor.execute("""
        INSERT INTO mcp_sessions (session_id, agent_id, session_token, session_data)
        VALUES (?, ?, ?, ?)
    """, (session_id, 'database', session_token, '{"connected": true}'))
    
    print("✅ Test 3: Session created")
    
    # Test 4: Add cache entry
    cache_data = {"result": "test_value", "computed_at": datetime.now().isoformat()}
    
    cursor.execute("""
        INSERT OR REPLACE INTO mcp_cache (cache_key, cache_value, cache_type, agent_id)
        VALUES (?, ?, ?, ?)
    """, ('test_key_1', json.dumps(cache_data), 'computation', 'database'))
    
    print("✅ Test 4: Cache entry added")
    
    # Test 5: Event sourcing
    event_id = str(uuid.uuid4())
    event_data = {
        "before": {"status": "idle"},
        "after": {"status": "busy"},
        "reason": "testing"
    }
    
    cursor.execute("""
        INSERT INTO mcp_events (event_id, aggregate_id, aggregate_type, event_type, event_data, sequence_number, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (event_id, 'database', 'agent', 'status_changed', json.dumps(event_data), 1, 'database'))
    
    print("✅ Test 5: Event logged")
    
    # Test 6: Create checkpoint
    checkpoint_state = {
        "agents": ["database", "supervisor", "backend-api"],
        "active_tasks": 0,
        "system_status": "operational"
    }
    
    cursor.execute("""
        INSERT INTO mcp_checkpoints (checkpoint_name, checkpoint_type, system_state, created_by)
        VALUES (?, ?, ?, ?)
    """, (f'test_checkpoint_{datetime.now().strftime("%Y%m%d_%H%M%S")}', 'manual', json.dumps(checkpoint_state), 'database'))
    
    print("✅ Test 6: System checkpoint created")
    
    # Verify all operations
    cursor.execute("SELECT COUNT(*) FROM mcp_states")
    states = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM mcp_transactions")
    transactions = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM mcp_sessions")
    sessions = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM mcp_cache")
    cache_entries = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM mcp_events")
    events = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM mcp_checkpoints")
    checkpoints = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 Persistence Stats:")
    print(f"  States: {states}")
    print(f"  Transactions: {transactions}")
    print(f"  Sessions: {sessions}")
    print(f"  Cache entries: {cache_entries}")
    print(f"  Events: {events}")
    print(f"  Checkpoints: {checkpoints}")
    print(f"\n✅ All persistence operations successful!")

if __name__ == "__main__":
    test_persistence()
