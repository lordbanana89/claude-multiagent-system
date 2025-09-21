#!/usr/bin/env python3
"""
Quick status check for multi-agent system
"""
import sqlite3
from datetime import datetime
import json
import os

INBOX_DB = "/Users/erik/Desktop/claude-multiagent-system/langgraph-test/shared_inbox.db"
STATE_FILE = "/Users/erik/Desktop/claude-multiagent-system/supervisor_state.json"

def check_status():
    print("\n=== MULTI-AGENT SYSTEM STATUS ===\n")

    # Check supervisor state
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            print(f"Current Phase: {state.get('current_phase', 'unknown')}")
            print(f"Tasks Sent: {state.get('statistics', {}).get('tasks_sent', 0)}")
            print(f"Tasks Completed: {state.get('statistics', {}).get('tasks_completed', 0)}")
            print(f"Last Update: {state.get('last_save', 'unknown')}")
    else:
        print("Supervisor state not found")

    print("\nAgent Status:")
    print("-" * 40)

    # Connect to database
    conn = sqlite3.connect(INBOX_DB)
    cursor = conn.cursor()

    # Get agent status
    agents = [
        "master", "backend-api", "database", "frontend-ui",
        "testing", "instagram", "queue-manager", "deployment"
    ]

    for agent in agents:
        # Get task counts
        cursor.execute('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
            FROM inbox
            WHERE agent = ?
        ''', (agent,))

        total, completed, pending = cursor.fetchone()

        # Check heartbeat
        cursor.execute('''
            SELECT last_seen, status
            FROM heartbeat
            WHERE agent = ?
        ''', (agent,))

        heartbeat_result = cursor.fetchone()
        is_active = False

        if heartbeat_result:
            last_seen, status = heartbeat_result
            if last_seen:
                try:
                    dt = datetime.strptime(last_seen, "%Y-%m-%d %H:%M:%S.%f")
                    is_active = (datetime.now() - dt).seconds < 60
                except:
                    pass

        status_icon = "✓" if is_active else "✗"
        print(f"{status_icon} {agent:<15} Tasks: {completed}/{total} (pending: {pending})")

    # Recent activity
    print("\nRecent Activity:")
    print("-" * 40)

    cursor.execute('''
        SELECT agent, task, status,
               CASE
                   WHEN completed_at IS NOT NULL THEN completed_at
                   ELSE created_at
               END as timestamp
        FROM inbox
        ORDER BY timestamp DESC
        LIMIT 5
    ''')

    for agent, task, status, timestamp in cursor.fetchall():
        status_icon = "✓" if status == "completed" else "⧗"
        if timestamp:
            try:
                dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
                time_str = dt.strftime("%H:%M:%S")
            except:
                time_str = timestamp[:8]
        else:
            time_str = "unknown"

        print(f"{time_str} [{status_icon}] {agent}: {task[:30]}")

    conn.close()

    # Check running processes
    print("\nRunning Processes:")
    print("-" * 40)

    # Check supervisor daemon
    result = os.popen("ps aux | grep supervisor_daemon | grep -v grep").read()
    if result:
        print("✓ Supervisor daemon is running")
    else:
        print("✗ Supervisor daemon is NOT running")

    # Check agent responders
    result = os.popen("ps aux | grep agent_responder | grep -v grep | wc -l").read().strip()
    print(f"✓ {result} agent responders running")

    print("\n" + "=" * 40 + "\n")

if __name__ == "__main__":
    check_status()