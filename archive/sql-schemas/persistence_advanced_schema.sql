-- =====================================================
-- ADVANCED PERSISTENCE SCHEMA FOR MCP
-- =====================================================
-- Enhanced persistence layer with migration support
-- =====================================================

-- Migration tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
    migration_id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checksum TEXT,
    execution_time_ms INTEGER,
    rollback_sql TEXT -- Store rollback commands
);

-- Distributed lock table for coordination
CREATE TABLE IF NOT EXISTS distributed_locks (
    lock_name TEXT PRIMARY KEY,
    lock_owner TEXT NOT NULL,
    lock_token TEXT UNIQUE NOT NULL,
    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    lock_data TEXT -- JSON context data
);

-- Write-ahead log for durability
CREATE TABLE IF NOT EXISTS write_ahead_log (
    wal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    operation_type TEXT NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    table_name TEXT NOT NULL,
    record_data TEXT NOT NULL, -- JSON of the operation
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied BOOLEAN DEFAULT 0,
    applied_at TIMESTAMP
);

-- Snapshot management for point-in-time recovery
CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    snapshot_name TEXT UNIQUE,
    snapshot_type TEXT NOT NULL, -- 'full', 'incremental', 'differential'
    base_snapshot_id TEXT, -- For incremental/differential
    tables_included TEXT, -- JSON array of table names
    total_records INTEGER,
    compressed_size INTEGER,
    snapshot_data BLOB, -- Compressed snapshot data
    checksum TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    FOREIGN KEY (base_snapshot_id) REFERENCES snapshots(snapshot_id)
);

-- Replication log for multi-database sync
CREATE TABLE IF NOT EXISTS replication_log (
    replication_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_db TEXT NOT NULL,
    target_db TEXT NOT NULL,
    operation TEXT NOT NULL, -- JSON operation details
    status TEXT DEFAULT 'pending', -- 'pending', 'synced', 'failed'
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP,
    error_message TEXT
);

-- Conflict resolution tracking
CREATE TABLE IF NOT EXISTS conflict_resolutions (
    conflict_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    conflict_type TEXT NOT NULL, -- 'update-update', 'delete-update', 'insert-insert'
    local_version TEXT, -- JSON local data
    remote_version TEXT, -- JSON remote data
    resolution_strategy TEXT, -- 'local_wins', 'remote_wins', 'merge', 'manual'
    resolved_version TEXT, -- JSON final data
    resolved_by TEXT,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data integrity checksums
CREATE TABLE IF NOT EXISTS data_integrity (
    integrity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_count INTEGER NOT NULL,
    data_checksum TEXT NOT NULL,
    metadata_checksum TEXT,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_valid BOOLEAN DEFAULT 1,
    UNIQUE(table_name, calculated_at)
);

-- Backup metadata
CREATE TABLE IF NOT EXISTS backup_metadata (
    backup_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    backup_name TEXT NOT NULL,
    backup_type TEXT NOT NULL, -- 'full', 'incremental', 'differential'
    backup_location TEXT NOT NULL,
    size_bytes INTEGER,
    tables_backed_up TEXT, -- JSON array
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    status TEXT DEFAULT 'in_progress', -- 'in_progress', 'completed', 'failed'
    error_message TEXT,
    retention_days INTEGER DEFAULT 30,
    created_by TEXT
);

-- Archive management for old data
CREATE TABLE IF NOT EXISTS archive_management (
    archive_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    source_table TEXT NOT NULL,
    archive_table TEXT NOT NULL,
    criteria TEXT NOT NULL, -- JSON archival criteria
    records_archived INTEGER,
    archive_location TEXT,
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    can_restore BOOLEAN DEFAULT 1,
    expires_at TIMESTAMP
);

-- Change data capture for tracking modifications
CREATE TABLE IF NOT EXISTS change_data_capture (
    cdc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    primary_key TEXT NOT NULL,
    old_values TEXT, -- JSON old row data
    new_values TEXT, -- JSON new row data
    changed_columns TEXT, -- JSON array of changed column names
    change_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    captured_by TEXT,
    transaction_id TEXT
);

-- Partition management for large tables
CREATE TABLE IF NOT EXISTS partition_metadata (
    partition_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    base_table TEXT NOT NULL,
    partition_table TEXT NOT NULL,
    partition_key TEXT NOT NULL,
    partition_value TEXT NOT NULL,
    row_count INTEGER,
    size_bytes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- Query cache for performance
CREATE TABLE IF NOT EXISTS query_cache (
    cache_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    query_hash TEXT UNIQUE NOT NULL,
    query_text TEXT NOT NULL,
    result_data TEXT, -- JSON cached result
    result_count INTEGER,
    execution_time_ms INTEGER,
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    last_hit TIMESTAMP
);

-- Index management and statistics
CREATE TABLE IF NOT EXISTS index_statistics (
    index_name TEXT PRIMARY KEY,
    table_name TEXT NOT NULL,
    column_names TEXT NOT NULL, -- JSON array
    index_type TEXT, -- 'btree', 'hash', 'gin', 'gist'
    size_bytes INTEGER,
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- Create performance indexes
CREATE INDEX IF NOT EXISTS idx_wal_transaction ON write_ahead_log(transaction_id, sequence_number);
CREATE INDEX IF NOT EXISTS idx_replication_status ON replication_log(status, created_at);
CREATE INDEX IF NOT EXISTS idx_cdc_table ON change_data_capture(table_name, change_timestamp);
CREATE INDEX IF NOT EXISTS idx_query_cache_hash ON query_cache(query_hash);
CREATE INDEX IF NOT EXISTS idx_backup_status ON backup_metadata(status, created_by);

-- Triggers for automatic maintenance
CREATE TRIGGER IF NOT EXISTS auto_expire_locks
AFTER INSERT ON distributed_locks
BEGIN
    DELETE FROM distributed_locks WHERE expires_at < CURRENT_TIMESTAMP;
END;

CREATE TRIGGER IF NOT EXISTS track_query_hits
AFTER UPDATE ON query_cache
BEGIN
    UPDATE query_cache 
    SET hit_count = hit_count + 1, last_hit = CURRENT_TIMESTAMP 
    WHERE cache_id = NEW.cache_id;
END;

