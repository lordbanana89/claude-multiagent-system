"""
Inbox Storage Layer - Database Integration for Message Storage
Provides persistent storage for agent messages with SQLite backend
"""

import sqlite3
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import asdict
from pathlib import Path
import threading
from contextlib import contextmanager

from shared_state.models import AgentMessage, MessageType, MessagePriority, MessageStatus


class InboxStorage:
    """Persistent storage layer for agent inbox messages"""

    def __init__(self, db_path: str = "inbox.db"):
        self.db_path = db_path
        self._lock = threading.RLock()
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
            conn.row_factory = sqlite3.Row

            # Enable optimizations
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=memory")

            conn.executescript("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    sender_id TEXT NOT NULL,
                    recipient_id TEXT,
                    message_type TEXT NOT NULL DEFAULT 'direct',
                    priority INTEGER NOT NULL DEFAULT 2,
                    subject TEXT,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'sent',
                    read_at TEXT,
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS agent_inboxes (
                    agent_id TEXT PRIMARY KEY,
                    unread_count INTEGER DEFAULT 0,
                    last_checked TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages(recipient_id);
                CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
                CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);
                CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(message_type);
            """)

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Error initializing database: {e}")
            raise

    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic cleanup and proper locking"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=memory")
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB
            conn.commit()

            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    def store_message(self, message: AgentMessage) -> bool:
        """Store a message in the database"""
        with self._lock, self._get_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO messages (
                        message_id, sender_id, recipient_id, message_type, priority,
                        subject, content, timestamp, status, read_at, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    message.message_id,
                    message.sender_id,
                    message.recipient_id,
                    message.message_type.value,
                    message.priority.value,
                    message.subject,
                    message.content,
                    message.timestamp.isoformat(),
                    message.status.value,
                    message.read_at.isoformat() if message.read_at else None,
                    json.dumps(message.metadata)
                ))

                # Update recipient's unread count if message is unread
                if message.recipient_id and message.status != MessageStatus.READ:
                    self._update_unread_count(message.recipient_id, 1, conn)

                return True

            except sqlite3.IntegrityError:
                # Message already exists
                return False

    def get_messages_for_agent(self, agent_id: str, limit: int = 100,
                             offset: int = 0, unread_only: bool = False) -> List[AgentMessage]:
        """Get messages for a specific agent"""
        with self._get_connection() as conn:
            where_clause = "WHERE recipient_id = ? OR (recipient_id IS NULL AND sender_id != ?)"
            params = [agent_id, agent_id]

            if unread_only:
                where_clause += " AND status != 'read'"

            query = f"""
                SELECT * FROM messages
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

            rows = conn.execute(query, params).fetchall()
            return [self._row_to_message(row) for row in rows]

    def get_message_by_id(self, message_id: str) -> Optional[AgentMessage]:
        """Get a specific message by ID"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM messages WHERE message_id = ?",
                (message_id,)
            ).fetchone()

            return self._row_to_message(row) if row else None

    def mark_message_read(self, message_id: str, reader_id: str) -> bool:
        """Mark a message as read"""
        with self._lock, self._get_connection() as conn:
            # Get current message status
            row = conn.execute(
                "SELECT status, recipient_id FROM messages WHERE message_id = ?",
                (message_id,)
            ).fetchone()

            if not row:
                return False

            current_status, recipient_id = row['status'], row['recipient_id']

            # Update message status
            conn.execute("""
                UPDATE messages
                SET status = 'read', read_at = ?,
                    metadata = json_set(metadata, '$.read_by', ?)
                WHERE message_id = ?
            """, (datetime.now().isoformat(), reader_id, message_id))

            # Update unread count if message was unread
            if current_status != 'read' and recipient_id:
                self._update_unread_count(recipient_id, -1, conn)

            return conn.total_changes > 0

    def get_conversation(self, agent1_id: str, agent2_id: str, limit: int = 100) -> List[AgentMessage]:
        """Get conversation between two agents"""
        with self._get_connection() as conn:
            query = """
                SELECT * FROM messages
                WHERE (sender_id = ? AND recipient_id = ?)
                   OR (sender_id = ? AND recipient_id = ?)
                ORDER BY timestamp ASC
                LIMIT ?
            """

            rows = conn.execute(query, (agent1_id, agent2_id, agent2_id, agent1_id, limit)).fetchall()
            return [self._row_to_message(row) for row in rows]

    def get_unread_count(self, agent_id: str) -> int:
        """Get unread message count for agent"""
        with self._get_connection() as conn:
            # Ensure agent inbox exists
            self._ensure_agent_inbox(agent_id, conn)

            row = conn.execute(
                "SELECT unread_count FROM agent_inboxes WHERE agent_id = ?",
                (agent_id,)
            ).fetchone()

            return row['unread_count'] if row else 0

    def search_messages(self, agent_id: str, query: str, limit: int = 50) -> List[AgentMessage]:
        """Search messages by content"""
        with self._get_connection() as conn:
            search_query = """
                SELECT * FROM messages
                WHERE (recipient_id = ? OR (recipient_id IS NULL AND sender_id != ?))
                  AND (content LIKE ? OR subject LIKE ?)
                ORDER BY timestamp DESC
                LIMIT ?
            """

            search_term = f"%{query}%"
            rows = conn.execute(
                search_query,
                (agent_id, agent_id, search_term, search_term, limit)
            ).fetchall()

            return [self._row_to_message(row) for row in rows]

    def delete_message(self, message_id: str) -> bool:
        """Delete a message"""
        with self._lock, self._get_connection() as conn:
            # Get message info before deletion
            row = conn.execute(
                "SELECT status, recipient_id FROM messages WHERE message_id = ?",
                (message_id,)
            ).fetchone()

            if not row:
                return False

            status, recipient_id = row['status'], row['recipient_id']

            # Delete message
            conn.execute("DELETE FROM messages WHERE message_id = ?", (message_id,))

            # Update unread count if message was unread
            if status != 'read' and recipient_id:
                self._update_unread_count(recipient_id, -1, conn)

            return conn.total_changes > 0

    def cleanup_old_messages(self, days: int = 30) -> int:
        """Clean up messages older than specified days"""
        with self._lock, self._get_connection() as conn:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)

            # Get messages to be deleted for unread count updates
            rows = conn.execute("""
                SELECT recipient_id, status FROM messages
                WHERE timestamp < ? AND status != 'read'
            """, (cutoff_date.isoformat(),)).fetchall()

            # Update unread counts
            unread_by_agent = {}
            for row in rows:
                if row['recipient_id']:
                    unread_by_agent[row['recipient_id']] = unread_by_agent.get(row['recipient_id'], 0) + 1

            for agent_id, count in unread_by_agent.items():
                self._update_unread_count(agent_id, -count, conn)

            # Delete old messages
            result = conn.execute(
                "DELETE FROM messages WHERE timestamp < ?",
                (cutoff_date.isoformat(),)
            )

            return result.rowcount

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        with self._get_connection() as conn:
            stats = {}

            # Total messages
            row = conn.execute("SELECT COUNT(*) as count FROM messages").fetchone()
            stats['total_messages'] = row['count']

            # Unread messages
            row = conn.execute("SELECT COUNT(*) as count FROM messages WHERE status != 'read'").fetchone()
            stats['unread_messages'] = row['count']

            # Messages by type
            rows = conn.execute("""
                SELECT message_type, COUNT(*) as count
                FROM messages
                GROUP BY message_type
            """).fetchall()
            stats['messages_by_type'] = {row['message_type']: row['count'] for row in rows}

            # Active agents
            row = conn.execute("SELECT COUNT(*) as count FROM agent_inboxes").fetchone()
            stats['active_agents'] = row['count']

            # Database size
            stats['db_size_bytes'] = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0

            return stats

    def _ensure_agent_inbox(self, agent_id: str, conn=None):
        """Ensure agent inbox record exists"""
        if conn is None:
            with self._get_connection() as connection:
                connection.execute("""
                    INSERT OR IGNORE INTO agent_inboxes (agent_id, last_checked)
                    VALUES (?, ?)
                """, (agent_id, datetime.now().isoformat()))
        else:
            conn.execute("""
                INSERT OR IGNORE INTO agent_inboxes (agent_id, last_checked)
                VALUES (?, ?)
            """, (agent_id, datetime.now().isoformat()))

    def _update_unread_count(self, agent_id: str, delta: int, conn=None):
        """Update unread count for an agent"""
        if conn is None:
            with self._get_connection() as connection:
                self._ensure_agent_inbox(agent_id, connection)
                connection.execute("""
                    UPDATE agent_inboxes
                    SET unread_count = MAX(0, unread_count + ?),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE agent_id = ?
                """, (delta, agent_id))
        else:
            self._ensure_agent_inbox(agent_id, conn)
            conn.execute("""
                UPDATE agent_inboxes
                SET unread_count = MAX(0, unread_count + ?),
                    updated_at = CURRENT_TIMESTAMP
                WHERE agent_id = ?
            """, (delta, agent_id))

    def _row_to_message(self, row: sqlite3.Row) -> AgentMessage:
        """Convert database row to AgentMessage"""
        message = AgentMessage()
        message.message_id = row['message_id']
        message.sender_id = row['sender_id']
        message.recipient_id = row['recipient_id']
        message.message_type = MessageType(row['message_type'])
        message.priority = MessagePriority(row['priority'])
        message.subject = row['subject']
        message.content = row['content']
        message.timestamp = datetime.fromisoformat(row['timestamp'])
        message.status = MessageStatus(row['status'])
        message.read_at = datetime.fromisoformat(row['read_at']) if row['read_at'] else None
        message.metadata = json.loads(row['metadata'] or '{}')

        return message


class InboxManager:
    """High-level inbox management with storage integration"""

    def __init__(self, storage: InboxStorage):
        self.storage = storage

    def send_message(self, sender_id: str, recipient_id: str, content: str,
                    subject: Optional[str] = None, priority: MessagePriority = MessagePriority.NORMAL,
                    message_type: MessageType = MessageType.DIRECT) -> AgentMessage:
        """Send a message and store it"""
        message = AgentMessage(
            sender_id=sender_id,
            recipient_id=recipient_id,
            content=content,
            subject=subject,
            priority=priority,
            message_type=message_type
        )

        if self.storage.store_message(message):
            return message
        else:
            raise ValueError(f"Failed to store message {message.message_id}")

    def broadcast_message(self, sender_id: str, content: str, recipients: List[str],
                         subject: Optional[str] = None, priority: MessagePriority = MessagePriority.NORMAL) -> List[AgentMessage]:
        """Send broadcast message to multiple recipients"""
        messages = []

        for recipient_id in recipients:
            if recipient_id != sender_id:  # Don't send to self
                message = AgentMessage(
                    sender_id=sender_id,
                    recipient_id=recipient_id,
                    content=content,
                    subject=subject,
                    priority=priority,
                    message_type=MessageType.BROADCAST
                )

                if self.storage.store_message(message):
                    messages.append(message)

        return messages

    def get_inbox(self, agent_id: str, limit: int = 50, unread_only: bool = False) -> Dict[str, Any]:
        """Get agent's inbox with metadata"""
        messages = self.storage.get_messages_for_agent(agent_id, limit=limit, unread_only=unread_only)
        unread_count = self.storage.get_unread_count(agent_id)

        return {
            'agent_id': agent_id,
            'messages': messages,
            'unread_count': unread_count,
            'total_count': len(messages)
        }

    def mark_as_read(self, message_id: str, reader_id: str) -> bool:
        """Mark message as read"""
        return self.storage.mark_message_read(message_id, reader_id)

    def search_inbox(self, agent_id: str, query: str, limit: int = 50) -> List[AgentMessage]:
        """Search agent's inbox"""
        return self.storage.search_messages(agent_id, query, limit)

    def get_conversation(self, agent1_id: str, agent2_id: str, limit: int = 100) -> List[AgentMessage]:
        """Get conversation between two agents"""
        return self.storage.get_conversation(agent1_id, agent2_id, limit)