#!/usr/bin/env python3
"""
MCP v2 Database Migration Script
Migrates existing database to MCP v2 schema while preserving data
"""

import sqlite3
import json
import logging
import sys
from datetime import datetime
import shutil
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPDatabaseMigration:
    def __init__(self, db_path: str = "/tmp/mcp_state.db"):
        self.db_path = db_path
        self.backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def backup_database(self):
        """Create backup before migration"""
        logger.info(f"Creating backup at {self.backup_path}")
        shutil.copy2(self.db_path, self.backup_path)
        logger.info("Backup completed")

    def migrate(self):
        """Run the migration"""
        try:
            # Create backup first
            self.backup_database()

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            logger.info("Starting database migration to MCP v2...")

            # Check existing tables
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table'
            """)
            existing_tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"Existing tables: {existing_tables}")

            # Create new MCP v2 tables if they don't exist
            self._create_mcp_v2_tables(cursor)

            # Migrate data from old tables
            self._migrate_existing_data(cursor, existing_tables)

            # Add indexes for performance
            self._create_indexes(cursor)

            # Verify migration
            if self._verify_migration(cursor):
                conn.commit()
                logger.info("✅ Migration completed successfully")
                return True
            else:
                conn.rollback()
                logger.error("❌ Migration verification failed")
                return False

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            logger.info(f"Restore from backup: {self.backup_path}")
            return False
        finally:
            conn.close()

    def _create_mcp_v2_tables(self, cursor):
        """Create all MCP v2 required tables"""

        # Core MCP tables
        tables = [
            # Note: capabilities table already exists with different schema
            # Create a new capabilities_v2 table for MCP v2 features
            """CREATE TABLE IF NOT EXISTS capabilities_v2 (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT,
                features TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",

            # Resources table
            """CREATE TABLE IF NOT EXISTS resources (
                id TEXT PRIMARY KEY,
                uri TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL,
                name TEXT,
                description TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",

            # Note: prompts table already exists with different schema,

            # Resource access log
            """CREATE TABLE IF NOT EXISTS resource_access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id TEXT,
                accessed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                accessed_by TEXT,
                action TEXT,
                metadata TEXT,
                FOREIGN KEY (resource_id) REFERENCES resources(id)
            )""",

            # Session management
            """CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                client_id TEXT,
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                ended_at TEXT,
                capabilities TEXT,
                metadata TEXT
            )""",

            # Tool execution log
            """CREATE TABLE IF NOT EXISTS tool_executions (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                tool_name TEXT,
                parameters TEXT,
                result TEXT,
                executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                execution_time REAL,
                success BOOLEAN,
                error_message TEXT,
                idempotency_key TEXT UNIQUE,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )""",

            # Note: audit_log table already exists with different schema
            # We'll update it with ALTER TABLE instead of CREATE,

            # Idempotency cache
            """CREATE TABLE IF NOT EXISTS idempotency_cache (
                key TEXT PRIMARY KEY,
                result TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT
            )"""
        ]

        for table_sql in tables:
            try:
                cursor.execute(table_sql)
                logger.info(f"✓ Created/verified table from: {table_sql.split('(')[0]}")
            except sqlite3.Error as e:
                logger.error(f"Failed to create table: {e}")
                raise

        # Handle existing audit_log table - add missing columns if needed
        try:
            # Check existing columns
            cursor.execute("PRAGMA table_info(audit_log)")
            existing_columns = [row[1] for row in cursor.fetchall()]

            # Add missing columns
            if 'event_type' not in existing_columns:
                cursor.execute("ALTER TABLE audit_log ADD COLUMN event_type TEXT")
                logger.info("✓ Added event_type column to audit_log")

            if 'level' not in existing_columns:
                cursor.execute("ALTER TABLE audit_log ADD COLUMN level TEXT DEFAULT 'INFO'")
                logger.info("✓ Added level column to audit_log")

        except sqlite3.Error as e:
            logger.warning(f"Could not update audit_log table: {e}")

    def _migrate_existing_data(self, cursor, existing_tables):
        """Migrate data from existing tables"""

        # Migrate agents to resources if agents table exists
        if 'agents' in existing_tables:
            logger.info("Migrating agents to resources...")
            cursor.execute("""
                INSERT OR IGNORE INTO resources (id, uri, type, name, description, metadata)
                SELECT
                    'resource_' || id,
                    'agent://' || id,
                    'agent',
                    name,
                    type || ' agent',
                    json_object('status', status, 'type', type)
                FROM agents
            """)
            logger.info(f"✓ Migrated {cursor.rowcount} agents")

        # Migrate activities to audit_log if exists
        if 'activities' in existing_tables:
            logger.info("Migrating activities to audit_log...")
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO audit_log
                    (timestamp, event_type, user_id, operation, details)
                    SELECT
                        timestamp,
                        'activity',
                        agent_id,
                        type,
                        json_object('description', description, 'metadata', metadata)
                    FROM activities
                """)
                logger.info(f"✓ Migrated {cursor.rowcount} activities")
            except sqlite3.Error as e:
                logger.warning(f"Could not migrate activities: {e}")

        # Update existing prompts table if needed
        try:
            cursor.execute("PRAGMA table_info(prompts)")
            columns = [row[1] for row in cursor.fetchall()]

            # Add missing columns to prompts
            if 'id' not in columns:
                # Add id column as text to existing prompts table
                cursor.execute("ALTER TABLE prompts ADD COLUMN id TEXT")
                # Generate ids for existing records
                cursor.execute("UPDATE prompts SET id = 'prompt_' || name WHERE id IS NULL")
                logger.info("✓ Added id column to prompts")

            if 'parameters' not in columns:
                cursor.execute("ALTER TABLE prompts ADD COLUMN parameters TEXT")
                logger.info("✓ Added parameters column to prompts")

            if 'created_at' not in columns:
                cursor.execute("ALTER TABLE prompts ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP")
                logger.info("✓ Added created_at column to prompts")

        except sqlite3.Error as e:
            logger.warning(f"Could not update prompts table: {e}")

        # Add default prompts if not exist
        try:
            default_prompts = [
                ("debug_agent", "Debug the {agent_name} agent", '{"agent_name": "string"}', "Debugging"),
                ("analyze_code", "Analyze the following code:\n{code}", '{"code": "string"}', "Analysis"),
                ("generate_test", "Generate tests for:\n{component}", '{"component": "string"}', "Testing")
            ]

            for name, template, params, category in default_prompts:
                cursor.execute("""
                    INSERT OR IGNORE INTO prompts (name, template, arguments, category)
                    VALUES (?, ?, ?, ?)
                """, (name, template, params, category))

            logger.info("✓ Added default prompts")
        except sqlite3.Error as e:
            logger.warning(f"Could not add default prompts: {e}")

        # Populate capabilities_v2
        cursor.execute("""
            INSERT OR IGNORE INTO capabilities_v2 (id, name, version, features)
            VALUES (?, ?, ?, ?)
        """, (
            "mcp_v2",
            "MCP v2 Server",
            "2025-06-18",
            json.dumps({
                "tools": True,
                "resources": True,
                "prompts": True,
                "idempotency": True,
                "dry_run": True,
                "websocket": True,
                "compliance": ["GDPR", "HIPAA", "SOC2", "PCI-DSS"]
            })
        ))
        logger.info("✓ Added MCP v2 capabilities")

    def _create_indexes(self, cursor):
        """Create performance indexes"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_resources_uri ON resources(uri)",
            "CREATE INDEX IF NOT EXISTS idx_resources_type ON resources(type)",
            "CREATE INDEX IF NOT EXISTS idx_access_log_uri ON resource_access_log(uri)",
            "CREATE INDEX IF NOT EXISTS idx_access_log_time ON resource_access_log(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_client ON sessions(client_id)",
            "CREATE INDEX IF NOT EXISTS idx_tools_session ON tool_executions(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_tools_name ON tool_executions(tool_name)",
            "CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_idempotency_expires ON idempotency_cache(expires_at)"
        ]

        created = 0
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                created += 1
            except sqlite3.Error as e:
                logger.warning(f"Could not create index: {e}")

        logger.info(f"✓ Created {created} indexes")

    def _verify_migration(self, cursor):
        """Verify migration was successful"""
        required_tables = [
            'capabilities_v2', 'resources', 'prompts', 'resource_access_log',
            'sessions', 'tool_executions', 'audit_log', 'idempotency_cache'
        ]

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]

        missing = set(required_tables) - set(existing_tables)
        if missing:
            logger.error(f"Missing tables: {missing}")
            return False

        # Check data integrity
        cursor.execute("SELECT COUNT(*) FROM resources")
        resource_count = cursor.fetchone()[0]
        logger.info(f"Resources: {resource_count}")

        cursor.execute("SELECT COUNT(*) FROM prompts")
        prompt_count = cursor.fetchone()[0]
        logger.info(f"Prompts: {prompt_count}")

        cursor.execute("SELECT COUNT(*) FROM capabilities_v2")
        capability_count = cursor.fetchone()[0]
        logger.info(f"Capabilities: {capability_count}")

        return capability_count > 0

    def rollback(self):
        """Rollback to backup"""
        if os.path.exists(self.backup_path):
            logger.info(f"Rolling back to {self.backup_path}")
            shutil.copy2(self.backup_path, self.db_path)
            logger.info("Rollback completed")
            return True
        else:
            logger.error("No backup found for rollback")
            return False

def main():
    """Main migration entry point"""
    print("""
    ╔══════════════════════════════════════╗
    ║   MCP v2 Database Migration Tool     ║
    ╚══════════════════════════════════════╝
    """)

    # Confirm migration
    response = input("This will migrate your database to MCP v2 schema. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled")
        sys.exit(0)

    # Run migration
    migrator = MCPDatabaseMigration()

    if migrator.migrate():
        print("\n✅ Migration successful!")
        print(f"Backup saved at: {migrator.backup_path}")
        print("\nNext steps:")
        print("1. Start MCP v2 server: python3 mcp_server_v2_compliant.py")
        print("2. Update agent configurations")
        print("3. Restart frontend: cd claude-ui && npm run dev")
    else:
        print("\n❌ Migration failed!")
        print("Would you like to rollback? (yes/no): ")
        if input().lower() == 'yes':
            if migrator.rollback():
                print("✅ Rollback successful")
            else:
                print("❌ Rollback failed - manual restoration required")
        sys.exit(1)

if __name__ == "__main__":
    main()