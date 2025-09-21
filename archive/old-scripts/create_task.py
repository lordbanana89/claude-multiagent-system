#!/usr/bin/env python3
"""
Create a real task for agents to collaborate on
"""

import sqlite3
import uuid
from datetime import datetime

# Connect to database
db = sqlite3.connect('mcp_system.db')
cursor = db.cursor()

# Create a task
task_id = str(uuid.uuid4())
timestamp = datetime.now().isoformat()

cursor.execute("""
    INSERT INTO tasks (id, title, component, status, priority, created_at, metadata)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    task_id,
    "Fix MCP compliance issues and implement real-time communication",
    "mcp_server",
    "pending",
    10,  # High priority
    timestamp,
    '{"description": "Agents must collaborate to fix MCP server compliance and test real communication", "assigned_to": null}'
))

db.commit()
print(f"✅ Task created: {task_id}")
print("Title: Fix MCP compliance issues and implement real-time communication")
print("Priority: HIGH (10)")

# Also add to inbox for supervisor
inbox_db = sqlite3.connect('langgraph-test/shared_inbox.db')
cursor = inbox_db.cursor()

cursor.execute("""
    INSERT INTO messages (message_id, sender_id, recipient_id, message_type, priority, subject, content, timestamp, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    str(uuid.uuid4()),
    'system',
    'supervisor',
    'task_assignment',
    3,  # High priority
    'URGENT: Fix MCP Compliance',
    f'Task {task_id}: All agents must collaborate to fix MCP server compliance issues. Backend-API lead on server fixes, Frontend-UI on dashboard updates, Database on persistence, Testing on validation.',
    timestamp,
    'sent'
))

inbox_db.commit()
inbox_db.close()
db.close()

print("📬 Message sent to supervisor inbox")