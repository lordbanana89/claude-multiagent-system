"""
🚨 EMERGENCY DRAMATIQ DATABASE LAYER
High-performance queue persistence with ACID compliance
"""

import sqlite3
import psycopg2
import psycopg2.pool
import json
import threading
import time
from contextlib import contextmanager
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import pickle
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageStatus(Enum):
    """Message processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD = "dead"


class Priority(Enum):
    """Message priority levels"""
    LOW = 0
    NORMAL = 10
    HIGH = 20
    URGENT = 30


@dataclass
class DramatiqMessage:
    """Dramatiq message structure for database storage"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    queue_name: str = "default"
    actor_name: str = ""
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    options: dict = field(default_factory=dict)

    # Timing and lifecycle
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Processing status
    status: MessageStatus = MessageStatus.PENDING
    priority: Priority = Priority.NORMAL

    # Retry mechanism
    retries: int = 0
    max_retries: int = 3
    retry_delay: int = 60  # seconds

    # Error handling
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None

    # Worker assignment
    worker_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage"""
        return {
            "message_id": self.message_id,
            "queue_name": self.queue_name,
            "actor_name": self.actor_name,
            "args": list(self.args),
            "kwargs": self.kwargs,
            "options": self.options,
            "created_at": self.created_at.isoformat(),
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value,
            "priority": self.priority.value,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "error_message": self.error_message,
            "error_traceback": self.error_traceback,
            "worker_id": self.worker_id
        }


class DramatiqDatabaseBackend:
    """🚨 HIGH-PERFORMANCE DRAMATIQ DATABASE BACKEND"""

    def __init__(self, db_type: str = "postgresql", connection_string: str = None):
        self.db_type = db_type
        self.connection_string = connection_string or self._get_default_connection()
        self._lock = threading.RLock()
        self._pool = None

        # Performance metrics
        self.metrics = {
            "messages_enqueued": 0,
            "messages_dequeued": 0,
            "messages_completed": 0,
            "messages_failed": 0,
            "queue_operations": 0
        }

        self._init_database()
        self._setup_connection_pool()

        logger.info(f"🚨 Emergency Dramatiq database backend initialized: {db_type}")

    def _get_default_connection(self) -> str:
        """Get default connection string based on database type"""
        if self.db_type == "postgresql":
            return "postgresql://postgres:password@localhost:5432/dramatiq_queue"
        else:
            return "dramatiq_queue.db"

    def _init_database(self):
        """🚨 EMERGENCY: Initialize optimized database schema"""
        if self.db_type == "postgresql":
            self._init_postgresql()
        else:
            self._init_sqlite()

    def _init_postgresql(self):
        """Initialize PostgreSQL with high-performance schema"""
        try:
            # Try to connect without database first
            import psycopg2
            base_conn = psycopg2.connect(
                host="localhost",
                port=5432,
                user="postgres",
                password="password",
                database="postgres"
            )
            base_conn.autocommit = True

            with base_conn.cursor() as cursor:
                # Create database if it doesn't exist
                cursor.execute("SELECT 1 FROM pg_database WHERE datname='dramatiq_queue'")
                if not cursor.fetchone():
                    cursor.execute("CREATE DATABASE dramatiq_queue")
                    logger.info("📊 Created dramatiq_queue database")

            base_conn.close()

            # Now connect to the actual database
            conn = psycopg2.connect(self.connection_string)
            with conn.cursor() as cursor:
                cursor.execute("""
                    -- 🚨 EMERGENCY DRAMATIQ QUEUE TABLES

                    CREATE TABLE IF NOT EXISTS dramatiq_messages (
                        message_id VARCHAR(36) PRIMARY KEY,
                        queue_name VARCHAR(100) NOT NULL,
                        actor_name VARCHAR(200) NOT NULL,
                        message_data JSONB NOT NULL,
                        args_data BYTEA,
                        kwargs_data BYTEA,

                        -- Timing columns with proper indexing
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        scheduled_at TIMESTAMP WITH TIME ZONE,
                        started_at TIMESTAMP WITH TIME ZONE,
                        completed_at TIMESTAMP WITH TIME ZONE,

                        -- Processing status
                        status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                        priority INTEGER DEFAULT 10 NOT NULL,

                        -- Retry mechanism
                        retries INTEGER DEFAULT 0,
                        max_retries INTEGER DEFAULT 3,
                        retry_delay INTEGER DEFAULT 60,
                        next_retry_at TIMESTAMP WITH TIME ZONE,

                        -- Error handling
                        error_message TEXT,
                        error_traceback TEXT,

                        -- Worker assignment
                        worker_id VARCHAR(100),
                        locked_until TIMESTAMP WITH TIME ZONE,

                        -- Metadata
                        options JSONB DEFAULT '{}',

                        -- Performance tracking
                        processing_time_ms INTEGER,
                        memory_usage_mb REAL
                    );

                    -- 🔥 CRITICAL PERFORMANCE INDEXES
                    CREATE INDEX IF NOT EXISTS idx_dramatiq_queue_status
                        ON dramatiq_messages(queue_name, status, priority DESC, created_at);

                    CREATE INDEX IF NOT EXISTS idx_dramatiq_scheduled
                        ON dramatiq_messages(scheduled_at) WHERE scheduled_at IS NOT NULL;

                    CREATE INDEX IF NOT EXISTS idx_dramatiq_retry
                        ON dramatiq_messages(next_retry_at) WHERE next_retry_at IS NOT NULL;

                    CREATE INDEX IF NOT EXISTS idx_dramatiq_worker
                        ON dramatiq_messages(worker_id, locked_until) WHERE worker_id IS NOT NULL;

                    CREATE INDEX IF NOT EXISTS idx_dramatiq_cleanup
                        ON dramatiq_messages(status, completed_at) WHERE status IN ('completed', 'failed', 'dead');

                    -- Queue statistics table for monitoring
                    CREATE TABLE IF NOT EXISTS dramatiq_queue_stats (
                        queue_name VARCHAR(100) PRIMARY KEY,
                        pending_count INTEGER DEFAULT 0,
                        processing_count INTEGER DEFAULT 0,
                        completed_count INTEGER DEFAULT 0,
                        failed_count INTEGER DEFAULT 0,
                        last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );

                    -- Worker health tracking
                    CREATE TABLE IF NOT EXISTS dramatiq_workers (
                        worker_id VARCHAR(100) PRIMARY KEY,
                        hostname VARCHAR(200),
                        pid INTEGER,
                        started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        status VARCHAR(20) DEFAULT 'active',
                        processed_count INTEGER DEFAULT 0,
                        failed_count INTEGER DEFAULT 0
                    );
                """)

                conn.commit()
                logger.info("🚨 PostgreSQL Dramatiq schema initialized with performance optimizations")

        except Exception as e:
            logger.warning(f"PostgreSQL not available, falling back to SQLite: {e}")
            self.db_type = "sqlite"
            self.connection_string = "dramatiq_emergency.db"
            self._init_sqlite()

    def _init_sqlite(self):
        """Initialize SQLite with WAL mode for high performance"""
        conn = sqlite3.connect(self.connection_string, timeout=30.0)

        # 🚨 EMERGENCY: Enable maximum performance settings
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=100000")  # 100MB cache
        conn.execute("PRAGMA temp_store=memory")
        conn.execute("PRAGMA mmap_size=1073741824")  # 1GB mmap
        conn.execute("PRAGMA page_size=32768")  # 32KB pages for better performance

        conn.executescript("""
            -- 🚨 EMERGENCY DRAMATIQ QUEUE TABLES (SQLite)

            CREATE TABLE IF NOT EXISTS dramatiq_messages (
                message_id TEXT PRIMARY KEY,
                queue_name TEXT NOT NULL,
                actor_name TEXT NOT NULL,
                message_data TEXT NOT NULL,
                args_data BLOB,
                kwargs_data BLOB,

                -- Timing columns
                created_at TEXT DEFAULT (datetime('now')),
                scheduled_at TEXT,
                started_at TEXT,
                completed_at TEXT,

                -- Processing status
                status TEXT DEFAULT 'pending' NOT NULL,
                priority INTEGER DEFAULT 10 NOT NULL,

                -- Retry mechanism
                retries INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                retry_delay INTEGER DEFAULT 60,
                next_retry_at TEXT,

                -- Error handling
                error_message TEXT,
                error_traceback TEXT,

                -- Worker assignment
                worker_id TEXT,
                locked_until TEXT,

                -- Metadata
                options TEXT DEFAULT '{}',

                -- Performance tracking
                processing_time_ms INTEGER,
                memory_usage_mb REAL
            );

            -- 🔥 CRITICAL PERFORMANCE INDEXES
            CREATE INDEX IF NOT EXISTS idx_dramatiq_queue_status
                ON dramatiq_messages(queue_name, status, priority DESC, created_at);

            CREATE INDEX IF NOT EXISTS idx_dramatiq_scheduled
                ON dramatiq_messages(scheduled_at) WHERE scheduled_at IS NOT NULL;

            CREATE INDEX IF NOT EXISTS idx_dramatiq_retry
                ON dramatiq_messages(next_retry_at) WHERE next_retry_at IS NOT NULL;

            CREATE INDEX IF NOT EXISTS idx_dramatiq_worker
                ON dramatiq_messages(worker_id, locked_until) WHERE worker_id IS NOT NULL;

            CREATE INDEX IF NOT EXISTS idx_dramatiq_cleanup
                ON dramatiq_messages(status, completed_at) WHERE status IN ('completed', 'failed', 'dead');

            -- Queue statistics
            CREATE TABLE IF NOT EXISTS dramatiq_queue_stats (
                queue_name TEXT PRIMARY KEY,
                pending_count INTEGER DEFAULT 0,
                processing_count INTEGER DEFAULT 0,
                completed_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                last_updated TEXT DEFAULT (datetime('now'))
            );

            -- Worker health tracking
            CREATE TABLE IF NOT EXISTS dramatiq_workers (
                worker_id TEXT PRIMARY KEY,
                hostname TEXT,
                pid INTEGER,
                started_at TEXT DEFAULT (datetime('now')),
                last_heartbeat TEXT DEFAULT (datetime('now')),
                status TEXT DEFAULT 'active',
                processed_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0
            );
        """)

        conn.commit()
        conn.close()
        logger.info("🚨 SQLite Dramatiq schema initialized with WAL mode")

    def _setup_connection_pool(self):
        """🚨 EMERGENCY: Setup high-performance connection pool"""
        if self.db_type == "postgresql":
            try:
                self._pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=5,      # Minimum connections
                    maxconn=50,     # Maximum connections for high throughput
                    dsn=self.connection_string
                )
                logger.info("🔥 PostgreSQL connection pool initialized (5-50 connections)")
            except Exception as e:
                logger.error(f"Failed to create PostgreSQL pool: {e}")
                self._pool = None

    @contextmanager
    def _get_connection(self):
        """Get database connection with proper pooling"""
        if self.db_type == "postgresql" and self._pool:
            conn = self._pool.getconn()
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                self._pool.putconn(conn)
        else:
            # SQLite fallback
            conn = sqlite3.connect(self.connection_string, timeout=30.0)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def enqueue_message(self, message: DramatiqMessage) -> bool:
        """🚨 EMERGENCY: High-performance message enqueuing"""
        with self._lock, self._get_connection() as conn:
            try:
                cursor = conn.cursor()

                # Serialize args and kwargs
                args_data = pickle.dumps(message.args) if message.args else None
                kwargs_data = pickle.dumps(message.kwargs) if message.kwargs else None

                if self.db_type == "postgresql":
                    cursor.execute("""
                        INSERT INTO dramatiq_messages (
                            message_id, queue_name, actor_name, message_data,
                            args_data, kwargs_data, created_at, scheduled_at,
                            status, priority, max_retries, options
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        message.message_id, message.queue_name, message.actor_name,
                        json.dumps(message.to_dict()), args_data, kwargs_data,
                        message.created_at, message.scheduled_at,
                        message.status.value, message.priority.value,
                        message.max_retries, json.dumps(message.options)
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO dramatiq_messages (
                            message_id, queue_name, actor_name, message_data,
                            args_data, kwargs_data, created_at, scheduled_at,
                            status, priority, max_retries, options
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        message.message_id, message.queue_name, message.actor_name,
                        json.dumps(message.to_dict()), args_data, kwargs_data,
                        message.created_at.isoformat(),
                        message.scheduled_at.isoformat() if message.scheduled_at else None,
                        message.status.value, message.priority.value,
                        message.max_retries, json.dumps(message.options)
                    ))

                # Update queue statistics
                self._update_queue_stats(conn, message.queue_name, "pending", 1)

                self.metrics["messages_enqueued"] += 1
                self.metrics["queue_operations"] += 1

                logger.info(f"🚨 Message enqueued: {message.message_id} -> {message.queue_name}")
                return True

            except Exception as e:
                logger.error(f"Failed to enqueue message {message.message_id}: {e}")
                return False

    def dequeue_message(self, queue_name: str, worker_id: str,
                       timeout: int = 30) -> Optional[DramatiqMessage]:
        """🚨 EMERGENCY: High-performance atomic message dequeuing with worker locking"""
        with self._lock, self._get_connection() as conn:
            try:
                cursor = conn.cursor()

                # Lock timeout for worker assignment
                lock_until = (datetime.utcnow() + timedelta(seconds=timeout)).isoformat()

                if self.db_type == "postgresql":
                    # Atomic dequeue with row locking
                    cursor.execute("""
                        UPDATE dramatiq_messages
                        SET status = 'processing',
                            worker_id = %s,
                            locked_until = %s,
                            started_at = NOW()
                        WHERE message_id = (
                            SELECT message_id FROM dramatiq_messages
                            WHERE queue_name = %s
                            AND status = 'pending'
                            AND (scheduled_at IS NULL OR scheduled_at <= NOW())
                            ORDER BY priority DESC, created_at ASC
                            FOR UPDATE SKIP LOCKED
                            LIMIT 1
                        )
                        RETURNING *
                    """, (worker_id, lock_until, queue_name))

                    row = cursor.fetchone()
                else:
                    # SQLite version (less efficient but functional)
                    cursor.execute("""
                        SELECT * FROM dramatiq_messages
                        WHERE queue_name = ?
                        AND status = 'pending'
                        AND (scheduled_at IS NULL OR scheduled_at <= datetime('now'))
                        ORDER BY priority DESC, created_at ASC
                        LIMIT 1
                    """, (queue_name,))

                    row = cursor.fetchone()
                    if row:
                        cursor.execute("""
                            UPDATE dramatiq_messages
                            SET status = 'processing',
                                worker_id = ?,
                                locked_until = ?,
                                started_at = datetime('now')
                            WHERE message_id = ?
                        """, (worker_id, lock_until, row['message_id']))

                if row:
                    # Update statistics
                    self._update_queue_stats(conn, queue_name, "pending", -1)
                    self._update_queue_stats(conn, queue_name, "processing", 1)

                    # Convert row to message
                    message_data = json.loads(row['message_data'])
                    message = DramatiqMessage(**{
                        k: v for k, v in message_data.items()
                        if k not in ['status', 'priority', 'created_at', 'scheduled_at', 'started_at', 'completed_at']
                    })

                    # Restore enums and dates
                    message.status = MessageStatus(row['status'])
                    message.priority = Priority(row['priority'])

                    # Deserialize args and kwargs
                    if row['args_data']:
                        message.args = pickle.loads(row['args_data'])
                    if row['kwargs_data']:
                        message.kwargs = pickle.loads(row['kwargs_data'])

                    self.metrics["messages_dequeued"] += 1
                    logger.info(f"🔥 Message dequeued: {message.message_id} by {worker_id}")
                    return message

                return None

            except Exception as e:
                logger.error(f"Failed to dequeue from {queue_name}: {e}")
                return None

    def complete_message(self, message_id: str, worker_id: str,
                        processing_time_ms: int = None) -> bool:
        """🚨 EMERGENCY: Mark message as completed with performance tracking"""
        with self._lock, self._get_connection() as conn:
            try:
                cursor = conn.cursor()

                if self.db_type == "postgresql":
                    cursor.execute("""
                        UPDATE dramatiq_messages
                        SET status = 'completed',
                            completed_at = NOW(),
                            processing_time_ms = %s
                        WHERE message_id = %s AND worker_id = %s
                        RETURNING queue_name
                    """, (processing_time_ms, message_id, worker_id))

                    result = cursor.fetchone()
                    queue_name = result['queue_name'] if result else None
                else:
                    cursor.execute("""
                        UPDATE dramatiq_messages
                        SET status = 'completed',
                            completed_at = datetime('now'),
                            processing_time_ms = ?
                        WHERE message_id = ? AND worker_id = ?
                    """, (processing_time_ms, message_id, worker_id))

                    cursor.execute("SELECT queue_name FROM dramatiq_messages WHERE message_id = ?",
                                 (message_id,))
                    row = cursor.fetchone()
                    queue_name = row['queue_name'] if row else None

                if queue_name:
                    self._update_queue_stats(conn, queue_name, "processing", -1)
                    self._update_queue_stats(conn, queue_name, "completed", 1)
                    self.metrics["messages_completed"] += 1

                    logger.info(f"✅ Message completed: {message_id}")
                    return True

                return False

            except Exception as e:
                logger.error(f"Failed to complete message {message_id}: {e}")
                return False

    def fail_message(self, message_id: str, worker_id: str, error_message: str,
                    error_traceback: str = None) -> bool:
        """🚨 EMERGENCY: Handle message failure with retry logic"""
        with self._lock, self._get_connection() as conn:
            try:
                cursor = conn.cursor()

                # Get current message state
                cursor.execute("""
                    SELECT retries, max_retries, retry_delay, queue_name
                    FROM dramatiq_messages
                    WHERE message_id = ? AND worker_id = ?
                """, (message_id, worker_id))

                row = cursor.fetchone()
                if not row:
                    return False

                retries = row['retries'] if self.db_type == "postgresql" else row[0]
                max_retries = row['max_retries'] if self.db_type == "postgresql" else row[1]
                retry_delay = row['retry_delay'] if self.db_type == "postgresql" else row[2]
                queue_name = row['queue_name'] if self.db_type == "postgresql" else row[3]

                if retries < max_retries:
                    # Schedule retry
                    next_retry = datetime.utcnow() + timedelta(seconds=retry_delay * (retries + 1))

                    if self.db_type == "postgresql":
                        cursor.execute("""
                            UPDATE dramatiq_messages
                            SET status = 'retrying',
                                retries = retries + 1,
                                next_retry_at = %s,
                                error_message = %s,
                                error_traceback = %s,
                                worker_id = NULL,
                                locked_until = NULL
                            WHERE message_id = %s
                        """, (next_retry, error_message, error_traceback, message_id))
                    else:
                        cursor.execute("""
                            UPDATE dramatiq_messages
                            SET status = 'retrying',
                                retries = retries + 1,
                                next_retry_at = ?,
                                error_message = ?,
                                error_traceback = ?,
                                worker_id = NULL,
                                locked_until = NULL
                            WHERE message_id = ?
                        """, (next_retry.isoformat(), error_message, error_traceback, message_id))

                    logger.warning(f"🔄 Message retry scheduled: {message_id} (attempt {retries + 1}/{max_retries})")
                else:
                    # Mark as dead
                    if self.db_type == "postgresql":
                        cursor.execute("""
                            UPDATE dramatiq_messages
                            SET status = 'dead',
                                completed_at = NOW(),
                                error_message = %s,
                                error_traceback = %s
                            WHERE message_id = %s
                        """, (error_message, error_traceback, message_id))
                    else:
                        cursor.execute("""
                            UPDATE dramatiq_messages
                            SET status = 'dead',
                                completed_at = datetime('now'),
                                error_message = ?,
                                error_traceback = ?
                            WHERE message_id = ?
                        """, (error_message, error_traceback, message_id))

                    logger.error(f"💀 Message marked as dead: {message_id}")

                # Update statistics
                self._update_queue_stats(conn, queue_name, "processing", -1)
                self._update_queue_stats(conn, queue_name, "failed", 1)
                self.metrics["messages_failed"] += 1

                return True

            except Exception as e:
                logger.error(f"Failed to fail message {message_id}: {e}")
                return False

    def _update_queue_stats(self, conn, queue_name: str, status: str, delta: int):
        """Update queue statistics atomically"""
        cursor = conn.cursor()

        if self.db_type == "postgresql":
            cursor.execute("""
                INSERT INTO dramatiq_queue_stats (queue_name, {}_count, last_updated)
                VALUES (%s, %s, NOW())
                ON CONFLICT (queue_name) DO UPDATE SET
                {}_count = dramatiq_queue_stats.{}_count + %s,
                last_updated = NOW()
            """.format(status, status, status), (queue_name, delta, delta))
        else:
            cursor.execute("""
                INSERT OR IGNORE INTO dramatiq_queue_stats (queue_name) VALUES (?)
            """, (queue_name,))

            cursor.execute(f"""
                UPDATE dramatiq_queue_stats
                SET {status}_count = {status}_count + ?,
                    last_updated = datetime('now')
                WHERE queue_name = ?
            """, (delta, queue_name))

    def get_queue_stats(self, queue_name: str = None) -> Dict[str, Any]:
        """🚨 EMERGENCY: Get real-time queue health statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if queue_name:
                cursor.execute("""
                    SELECT * FROM dramatiq_queue_stats WHERE queue_name = ?
                """, (queue_name,))
                row = cursor.fetchone()

                if row:
                    if self.db_type == "postgresql":
                        return dict(row)
                    else:
                        return {
                            "queue_name": row[0],
                            "pending_count": row[1],
                            "processing_count": row[2],
                            "completed_count": row[3],
                            "failed_count": row[4],
                            "last_updated": row[5]
                        }
                return {}
            else:
                # Get all queue stats
                cursor.execute("SELECT * FROM dramatiq_queue_stats")
                return [dict(row) if self.db_type == "postgresql" else {
                    "queue_name": row[0],
                    "pending_count": row[1],
                    "processing_count": row[2],
                    "completed_count": row[3],
                    "failed_count": row[4],
                    "last_updated": row[5]
                } for row in cursor.fetchall()]

    def get_system_health(self) -> Dict[str, Any]:
        """🚨 EMERGENCY: Get complete system health metrics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get queue summary
            cursor.execute("""
                SELECT
                    SUM(pending_count) as total_pending,
                    SUM(processing_count) as total_processing,
                    SUM(completed_count) as total_completed,
                    SUM(failed_count) as total_failed
                FROM dramatiq_queue_stats
            """)

            row = cursor.fetchone()
            queue_totals = {
                "total_pending": (row[0] if self.db_type == "postgresql" else row[0]) or 0,
                "total_processing": (row[1] if self.db_type == "postgresql" else row[1]) or 0,
                "total_completed": (row[2] if self.db_type == "postgresql" else row[2]) or 0,
                "total_failed": (row[3] if self.db_type == "postgresql" else row[3]) or 0
            }

            # Get worker health
            cursor.execute("""
                SELECT COUNT(*) as active_workers
                FROM dramatiq_workers
                WHERE status = 'active'
            """)

            worker_count = cursor.fetchone()[0]

            return {
                "database_type": self.db_type,
                "connection_pool_active": self._pool is not None,
                "queue_totals": queue_totals,
                "active_workers": worker_count,
                "performance_metrics": self.metrics,
                "timestamp": datetime.utcnow().isoformat()
            }


# 🚨 EMERGENCY TESTING AND VALIDATION
def emergency_test_database():
    """🚨 EMERGENCY: Test database functionality immediately"""
    print("🚨 EMERGENCY DRAMATIQ DATABASE TEST STARTING...")

    try:
        # Initialize database
        db = DramatiqDatabaseBackend(db_type="sqlite")

        # Test message creation and enqueuing
        test_message = DramatiqMessage(
            queue_name="emergency_queue",
            actor_name="emergency_task",
            args=("test_arg",),
            kwargs={"test_key": "test_value"},
            priority=Priority.URGENT
        )

        # Enqueue message
        enqueue_result = db.enqueue_message(test_message)
        print(f"✅ Message enqueued: {enqueue_result}")

        # Dequeue message
        dequeued = db.dequeue_message("emergency_queue", "test_worker_1")
        print(f"✅ Message dequeued: {dequeued is not None}")

        if dequeued:
            # Complete message
            complete_result = db.complete_message(dequeued.message_id, "test_worker_1", 1500)
            print(f"✅ Message completed: {complete_result}")

        # Get system health
        health = db.get_system_health()
        print(f"🏥 System health: {health}")

        print("🎉 EMERGENCY DATABASE TEST COMPLETED SUCCESSFULLY!")
        return True

    except Exception as e:
        print(f"❌ EMERGENCY TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    emergency_test_database()