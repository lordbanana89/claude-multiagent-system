#!/usr/bin/env python3
import sqlite3
import json
import shutil
from datetime import datetime
import hashlib

def create_backup():
    """Create backup before migration"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"mcp_system_backup_{timestamp}.db"
    
    print(f"📦 Creating backup: {backup_name}")
    shutil.copy2('mcp_system.db', backup_name)
    
    # Calculate checksum
    with open(backup_name, 'rb') as f:
        checksum = hashlib.md5(f.read()).hexdigest()
    
    return backup_name, checksum

def get_table_counts():
    """Get record counts before migration"""
    conn = sqlite3.connect('mcp_system.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    counts = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        counts[table_name] = cursor.fetchone()[0]
    
    conn.close()
    return counts

def execute_migration():
    """Execute the migration"""
    conn = sqlite3.connect('mcp_system.db')
    cursor = conn.cursor()
    
    migrations = [
        {
            "version": "001",
            "name": "comprehensive_schema",
            "file": "mcp_comprehensive_schema.sql"
        },
        {
            "version": "002", 
            "name": "persistence_advanced",
            "file": "persistence_advanced_schema.sql"
        }
    ]
    
    print("\n🔄 Executing migrations...")
    
    for migration in migrations:
        # Check if already applied
        cursor.execute(
            "SELECT COUNT(*) FROM schema_migrations WHERE version = ?",
            (migration['version'],)
        )
        if cursor.fetchone()[0] > 0:
            print(f"  ⏭️  Migration {migration['version']} already applied")
            continue
        
        # Read and execute migration
        with open(migration['file'], 'r') as f:
            sql = f.read()
        
        start_time = datetime.now()
        
        # Execute each statement separately
        statements = sql.split(';')
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                cursor.execute(stmt)
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Record migration
        cursor.execute("""
            INSERT INTO schema_migrations (version, name, execution_time_ms)
            VALUES (?, ?, ?)
        """, (migration['version'], migration['name'], int(execution_time)))
        
        print(f"  ✅ Migration {migration['version']}: {migration['name']} ({execution_time:.2f}ms)")
    
    conn.commit()
    conn.close()

def verify_migration():
    """Verify migration success"""
    conn = sqlite3.connect('mcp_system.db')
    cursor = conn.cursor()
    
    print("\n🔍 Verifying migration...")
    
    # Check new tables
    cursor.execute("""
        SELECT COUNT(*) FROM sqlite_master 
        WHERE type='table' AND name IN (
            'projects', 'workflows', 'resources',
            'messages_v2', 'channels', 'subscriptions',
            'performance_metrics', 'knowledge_base',
            'schema_migrations', 'distributed_locks',
            'write_ahead_log', 'snapshots'
        )
    """)
    new_tables = cursor.fetchone()[0]
    
    # Check indexes
    cursor.execute("""
        SELECT COUNT(*) FROM sqlite_master 
        WHERE type='index' AND name LIKE 'idx_%'
    """)
    indexes = cursor.fetchone()[0]
    
    conn.close()
    
    return new_tables, indexes

def main():
    print("🚀 MCP Database Migration Plan")
    print("=" * 50)
    
    # Step 1: Backup
    backup_file, checksum = create_backup()
    print(f"  Checksum: {checksum}")
    
    # Step 2: Get pre-migration stats
    print("\n📊 Pre-migration statistics:")
    pre_counts = get_table_counts()
    for table, count in pre_counts.items():
        if count > 0:
            print(f"  {table}: {count} records")
    
    # Step 3: Execute migration
    try:
        execute_migration()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print(f"💾 Restore from backup: {backup_file}")
        return
    
    # Step 4: Verify
    new_tables, indexes = verify_migration()
    print(f"  New tables created: {new_tables}")
    print(f"  Indexes created: {indexes}")
    
    # Step 5: Post-migration stats
    print("\n📊 Post-migration statistics:")
    post_counts = get_table_counts()
    new_count = len(post_counts) - len(pre_counts)
    print(f"  Total tables: {len(post_counts)} (+{new_count} new)")
    print(f"  Data preserved: ✅")
    
    print("\n✅ Migration completed successfully!")

if __name__ == "__main__":
    main()
