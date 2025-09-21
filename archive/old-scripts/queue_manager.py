#!/usr/bin/env python3
"""
Queue Manager Agent - Manages task queue for multi-agent system
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import time

class QueueManager:
    def __init__(self, db_path: str = "langgraph-test/shared_inbox.db"):
        self.db_path = db_path
        self.agent_name = "queue-manager"
        self.init_database()

    def init_database(self):
        """Initialize queue tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create task queue table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_queue (
                task_id TEXT PRIMARY KEY,
                priority INTEGER DEFAULT 5,
                assigned_to TEXT,
                created_by TEXT,
                task_type TEXT,
                description TEXT,
                payload TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3
            )
        ''')

        # Create queue metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS queue_metrics (
                metric_id TEXT PRIMARY KEY,
                timestamp TIMESTAMP,
                queue_length INTEGER,
                pending_tasks INTEGER,
                active_tasks INTEGER,
                completed_tasks INTEGER,
                failed_tasks INTEGER,
                avg_completion_time REAL
            )
        ''')

        conn.commit()
        conn.close()

    def add_task(self, task_type: str, description: str, assigned_to: str = None,
                 priority: int = 5, payload: Dict = None, created_by: str = "system") -> str:
        """Add a new task to the queue"""
        task_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO task_queue (
                task_id, priority, assigned_to, created_by, task_type,
                description, payload, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        ''', (
            task_id, priority, assigned_to, created_by, task_type,
            description, json.dumps(payload or {}), datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        self.log_activity("task_added", f"Added task: {description}", {
            "task_id": task_id,
            "type": task_type,
            "assigned_to": assigned_to
        })

        return task_id

    def get_next_task(self, agent_id: str = None) -> Optional[Dict]:
        """Get the next available task from the queue"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if agent_id:
            # Get tasks assigned to specific agent
            cursor.execute('''
                SELECT * FROM task_queue
                WHERE status = 'pending'
                AND (assigned_to = ? OR assigned_to IS NULL)
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            ''', (agent_id,))
        else:
            # Get any available task
            cursor.execute('''
                SELECT * FROM task_queue
                WHERE status = 'pending'
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            ''')

        row = cursor.fetchone()

        if row:
            task = self._row_to_dict(cursor, row)

            # Mark task as active
            cursor.execute('''
                UPDATE task_queue
                SET status = 'active', started_at = ?
                WHERE task_id = ?
            ''', (datetime.now().isoformat(), task['task_id']))

            conn.commit()
            conn.close()

            return task

        conn.close()
        return None

    def complete_task(self, task_id: str, result: Dict = None) -> bool:
        """Mark a task as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE task_queue
            SET status = 'completed', completed_at = ?
            WHERE task_id = ?
        ''', (datetime.now().isoformat(), task_id))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if success:
            self.log_activity("task_completed", f"Completed task: {task_id}", result or {})

        return success

    def fail_task(self, task_id: str, error: str) -> bool:
        """Mark a task as failed and handle retry logic"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get current retry count
        cursor.execute('''
            SELECT retry_count, max_retries FROM task_queue
            WHERE task_id = ?
        ''', (task_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return False

        retry_count, max_retries = row

        if retry_count < max_retries:
            # Retry the task
            cursor.execute('''
                UPDATE task_queue
                SET status = 'pending', retry_count = retry_count + 1
                WHERE task_id = ?
            ''', (task_id,))
            status = 'retrying'
        else:
            # Max retries reached, mark as failed
            cursor.execute('''
                UPDATE task_queue
                SET status = 'failed', completed_at = ?
                WHERE task_id = ?
            ''', (datetime.now().isoformat(), task_id))
            status = 'failed'

        conn.commit()
        conn.close()

        self.log_activity("task_failed", f"Task failed: {task_id}", {
            "error": error,
            "status": status,
            "retry_count": retry_count
        })

        return True

    def get_queue_status(self) -> Dict:
        """Get current queue status and metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Count tasks by status
        cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM task_queue
            GROUP BY status
        ''')

        status_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # Get queue length
        cursor.execute('SELECT COUNT(*) FROM task_queue WHERE status = "pending"')
        queue_length = cursor.fetchone()[0]

        # Calculate average completion time
        cursor.execute('''
            SELECT AVG(julianday(completed_at) - julianday(started_at)) * 86400
            FROM task_queue
            WHERE status = 'completed'
            AND completed_at IS NOT NULL
            AND started_at IS NOT NULL
        ''')
        avg_time = cursor.fetchone()[0] or 0

        conn.close()

        return {
            "queue_length": queue_length,
            "pending": status_counts.get('pending', 0),
            "active": status_counts.get('active', 0),
            "completed": status_counts.get('completed', 0),
            "failed": status_counts.get('failed', 0),
            "avg_completion_time": round(avg_time, 2)
        }

    def log_activity(self, category: str, activity: str, details: Dict = None):
        """Log activity to MCP system"""
        # This would integrate with the MCP logging system
        print(f"[{self.agent_name}] {category}: {activity}")
        if details:
            print(f"  Details: {json.dumps(details, indent=2)}")

    def _row_to_dict(self, cursor, row) -> Dict:
        """Convert a database row to a dictionary"""
        columns = [desc[0] for desc in cursor.description]
        task_dict = dict(zip(columns, row))

        # Parse JSON payload
        if task_dict.get('payload'):
            try:
                task_dict['payload'] = json.loads(task_dict['payload'])
            except json.JSONDecodeError:
                task_dict['payload'] = {}

        return task_dict

    def monitor_queue(self, interval: int = 10):
        """Monitor queue and record metrics periodically"""
        while True:
            status = self.get_queue_status()

            # Record metrics
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO queue_metrics (
                    metric_id, timestamp, queue_length, pending_tasks,
                    active_tasks, completed_tasks, failed_tasks, avg_completion_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(uuid.uuid4()),
                datetime.now().isoformat(),
                status['queue_length'],
                status['pending'],
                status['active'],
                status['completed'],
                status['failed'],
                status['avg_completion_time']
            ))

            conn.commit()
            conn.close()

            print(f"Queue Status: {json.dumps(status, indent=2)}")

            time.sleep(interval)


if __name__ == "__main__":
    # Initialize queue manager
    qm = QueueManager()

    # Add some sample tasks
    qm.add_task(
        task_type="api_development",
        description="Create user authentication endpoint",
        assigned_to="backend-api",
        priority=8,
        payload={"endpoint": "/api/auth/login", "method": "POST"}
    )

    qm.add_task(
        task_type="ui_development",
        description="Build login form component",
        assigned_to="frontend-ui",
        priority=7,
        payload={"component": "LoginForm", "framework": "React"}
    )

    qm.add_task(
        task_type="testing",
        description="Test authentication flow",
        assigned_to="testing",
        priority=6,
        payload={"test_suite": "auth_integration"}
    )

    # Get and display queue status
    status = qm.get_queue_status()
    print(f"\nInitial Queue Status:\n{json.dumps(status, indent=2)}")

    # Simulate processing a task
    task = qm.get_next_task("backend-api")
    if task:
        print(f"\nProcessing task: {task['description']}")
        # Simulate work
        time.sleep(1)
        qm.complete_task(task['task_id'], {"status": "success"})

    # Final status
    status = qm.get_queue_status()
    print(f"\nFinal Queue Status:\n{json.dumps(status, indent=2)}")