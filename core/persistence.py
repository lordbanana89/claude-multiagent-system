"""
SQLite persistence layer for system state
"""

import sqlite3
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PersistenceManager:
    """Manages persistent storage of system state in SQLite"""

    def __init__(self, db_path: str = "data/system_state.db"):
        """Initialize persistence manager"""
        self.db_path = db_path

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()
        logger.info(f"PersistenceManager initialized with database: {db_path}")

    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    agent TEXT NOT NULL,
                    command TEXT,
                    params TEXT,
                    status TEXT,
                    priority INTEGER,
                    created_at REAL,
                    completed_at REAL,
                    result TEXT,
                    error TEXT
                )
            """)

            # Workflows table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    workflow_id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    definition TEXT,
                    created_at REAL
                )
            """)

            # Workflow executions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    execution_id TEXT PRIMARY KEY,
                    workflow_id TEXT,
                    status TEXT,
                    started_at REAL,
                    completed_at REAL,
                    context TEXT,
                    error TEXT,
                    FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
                )
            """)

            # Workflow steps table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_steps (
                    step_id TEXT,
                    execution_id TEXT,
                    name TEXT,
                    agent TEXT,
                    action TEXT,
                    status TEXT,
                    started_at REAL,
                    completed_at REAL,
                    result TEXT,
                    error TEXT,
                    PRIMARY KEY (step_id, execution_id),
                    FOREIGN KEY (execution_id) REFERENCES workflow_executions(execution_id)
                )
            """)

            # Agent status table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_status (
                    agent TEXT PRIMARY KEY,
                    status TEXT,
                    last_task_id TEXT,
                    last_heartbeat REAL,
                    details TEXT
                )
            """)

            # System events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    source TEXT,
                    timestamp REAL,
                    data TEXT
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(agent)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_executions_status ON workflow_executions(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON system_events(event_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON system_events(timestamp)")

            conn.commit()

    # Task persistence methods
    def save_task(self, task_id: str, agent: str, command: str, params: Dict = None,
                  priority: int = 1, status: str = "pending"):
        """Save or update a task"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO tasks
                (task_id, agent, command, params, status, priority, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (task_id, agent, command, json.dumps(params or {}), status, priority, time.time()))
            conn.commit()

    def update_task_status(self, task_id: str, status: str, result: Dict = None, error: str = None):
        """Update task status and result"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tasks
                SET status = ?, completed_at = ?, result = ?, error = ?
                WHERE task_id = ?
            """, (status, time.time() if status in ['completed', 'failed'] else None,
                  json.dumps(result) if result else None, error, task_id))
            conn.commit()

    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            if row:
                task = dict(row)
                if task['params']:
                    task['params'] = json.loads(task['params'])
                if task['result']:
                    task['result'] = json.loads(task['result'])
                return task
        return None

    def get_pending_tasks(self, agent: str = None) -> List[Dict]:
        """Get all pending tasks, optionally filtered by agent"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if agent:
                cursor.execute("""
                    SELECT * FROM tasks
                    WHERE status = 'pending' AND agent = ?
                    ORDER BY priority DESC, created_at ASC
                """, (agent,))
            else:
                cursor.execute("""
                    SELECT * FROM tasks
                    WHERE status = 'pending'
                    ORDER BY priority DESC, created_at ASC
                """)

            tasks = []
            for row in cursor.fetchall():
                task = dict(row)
                if task['params']:
                    task['params'] = json.loads(task['params'])
                tasks.append(task)
            return tasks

    # Workflow persistence methods
    def save_workflow(self, workflow_id: str, name: str, description: str, definition: Dict):
        """Save workflow definition"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO workflows
                (workflow_id, name, description, definition, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (workflow_id, name, description, json.dumps(definition), time.time()))
            conn.commit()

    def save_workflow_execution(self, execution_id: str, workflow_id: str, status: str = "running"):
        """Save workflow execution"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO workflow_executions
                (execution_id, workflow_id, status, started_at)
                VALUES (?, ?, ?, ?)
            """, (execution_id, workflow_id, status, time.time()))
            conn.commit()

    def update_workflow_execution(self, execution_id: str, status: str,
                                  context: Dict = None, error: str = None):
        """Update workflow execution status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE workflow_executions
                SET status = ?, completed_at = ?, context = ?, error = ?
                WHERE execution_id = ?
            """, (status, time.time() if status in ['completed', 'failed'] else None,
                  json.dumps(context) if context else None, error, execution_id))
            conn.commit()

    def save_workflow_step(self, step_id: str, execution_id: str, name: str,
                          agent: str, action: str, status: str = "pending"):
        """Save workflow step"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO workflow_steps
                (step_id, execution_id, name, agent, action, status, started_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (step_id, execution_id, name, agent, action, status,
                  time.time() if status == "running" else None))
            conn.commit()

    def update_workflow_step(self, step_id: str, execution_id: str, status: str,
                            result: Dict = None, error: str = None):
        """Update workflow step status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE workflow_steps
                SET status = ?, completed_at = ?, result = ?, error = ?
                WHERE step_id = ? AND execution_id = ?
            """, (status, time.time() if status in ['completed', 'failed'] else None,
                  json.dumps(result) if result else None, error, step_id, execution_id))
            conn.commit()

    # Agent status methods
    def update_agent_status(self, agent: str, status: str, details: Dict = None):
        """Update agent status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO agent_status
                (agent, status, last_heartbeat, details)
                VALUES (?, ?, ?, ?)
            """, (agent, status, time.time(), json.dumps(details or {})))
            conn.commit()

    def get_agent_status(self, agent: str) -> Optional[Dict]:
        """Get agent status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agent_status WHERE agent = ?", (agent,))
            row = cursor.fetchone()
            if row:
                status = dict(row)
                if status['details']:
                    status['details'] = json.loads(status['details'])
                return status
        return None

    # Event logging
    def log_event(self, event_type: str, source: str, data: Dict = None):
        """Log system event"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_events
                (event_type, source, timestamp, data)
                VALUES (?, ?, ?, ?)
            """, (event_type, source, time.time(), json.dumps(data or {})))
            conn.commit()

    def get_recent_events(self, limit: int = 100, event_type: str = None) -> List[Dict]:
        """Get recent system events"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if event_type:
                cursor.execute("""
                    SELECT * FROM system_events
                    WHERE event_type = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (event_type, limit))
            else:
                cursor.execute("""
                    SELECT * FROM system_events
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))

            events = []
            for row in cursor.fetchall():
                event = dict(row)
                if event['data']:
                    event['data'] = json.loads(event['data'])
                events.append(event)
            return events

    # Recovery methods
    def get_incomplete_executions(self) -> List[Dict]:
        """Get all incomplete workflow executions for recovery"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM workflow_executions
                WHERE status IN ('running', 'pending')
                ORDER BY started_at ASC
            """)

            executions = []
            for row in cursor.fetchall():
                execution = dict(row)
                if execution['context']:
                    execution['context'] = json.loads(execution['context'])
                executions.append(execution)
            return executions

    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data"""
        cutoff_time = time.time() - (days_to_keep * 24 * 3600)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Clean old completed tasks
            cursor.execute("""
                DELETE FROM tasks
                WHERE status IN ('completed', 'failed')
                AND completed_at < ?
            """, (cutoff_time,))

            # Clean old events
            cursor.execute("""
                DELETE FROM system_events
                WHERE timestamp < ?
            """, (cutoff_time,))

            conn.commit()

            # Vacuum database to reclaim space
            cursor.execute("VACUUM")

            logger.info(f"Cleaned up data older than {days_to_keep} days")

    def get_statistics(self) -> Dict:
        """Get system statistics from persistence"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            stats = {}

            # Task statistics
            cursor.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
            stats['tasks'] = dict(cursor.fetchall())

            # Workflow statistics
            cursor.execute("SELECT status, COUNT(*) FROM workflow_executions GROUP BY status")
            stats['workflows'] = dict(cursor.fetchall())

            # Agent statistics
            cursor.execute("SELECT status, COUNT(*) FROM agent_status GROUP BY status")
            stats['agents'] = dict(cursor.fetchall())

            # Recent events count
            cursor.execute("SELECT COUNT(*) FROM system_events WHERE timestamp > ?",
                          (time.time() - 3600,))  # Last hour
            stats['recent_events'] = cursor.fetchone()[0]

            return stats


# Singleton instance
_persistence_manager = None

def get_persistence_manager(db_path: str = "data/system_state.db") -> PersistenceManager:
    """Get or create persistence manager instance"""
    global _persistence_manager
    if _persistence_manager is None:
        _persistence_manager = PersistenceManager(db_path)
    return _persistence_manager