-- MCP Persistence Tables Schema
-- Core persistence infrastructure for MCP system

-- State persistence table for agent states
CREATE TABLE IF NOT EXISTS mcp_states (
    state_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    agent_id TEXT NOT NULL,
    state_type TEXT NOT NULL, -- 'checkpoint', 'snapshot', 'backup'
    state_data TEXT NOT NULL, -- JSON serialized state
    version INTEGER DEFAULT 1,
    parent_state_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    FOREIGN KEY (agent_id) REFERENCES agents(id),
    FOREIGN KEY (parent_state_id) REFERENCES mcp_states(state_id)
);

-- Transactions table for atomic operations
CREATE TABLE IF NOT EXISTS mcp_transactions (
    transaction_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    agent_id TEXT NOT NULL,
    transaction_type TEXT NOT NULL, -- 'task', 'message', 'state_change'
    status TEXT DEFAULT 'pending', -- 'pending', 'committed', 'rolled_back'
    operations TEXT NOT NULL, -- JSON array of operations
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- Rollback history for transaction recovery
CREATE TABLE IF NOT EXISTS mcp_rollback_history (
    rollback_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    transaction_id TEXT NOT NULL,
    rollback_reason TEXT,
    original_state TEXT, -- JSON of state before transaction
    restored_state TEXT, -- JSON of state after rollback
    rollback_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES mcp_transactions(transaction_id)
);

-- Data versioning for tracking changes
CREATE TABLE IF NOT EXISTS mcp_data_versions (
    version_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    change_type TEXT NOT NULL, -- 'insert', 'update', 'delete'
    old_data TEXT, -- JSON of previous data
    new_data TEXT, -- JSON of new data
    changed_by TEXT NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_metadata TEXT
);

-- Session management for persistent connections
CREATE TABLE IF NOT EXISTS mcp_sessions (
    session_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    agent_id TEXT NOT NULL,
    session_token TEXT UNIQUE,
    session_data TEXT, -- JSON session state
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    status TEXT DEFAULT 'active', -- 'active', 'expired', 'terminated'
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- Cache table for frequently accessed data
CREATE TABLE IF NOT EXISTS mcp_cache (
    cache_key TEXT PRIMARY KEY,
    cache_value TEXT NOT NULL,
    cache_type TEXT NOT NULL, -- 'query', 'computation', 'resource'
    agent_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);

-- Event sourcing table for replay capability
CREATE TABLE IF NOT EXISTS mcp_events (
    event_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    aggregate_id TEXT NOT NULL, -- ID of the entity being modified
    aggregate_type TEXT NOT NULL, -- 'agent', 'task', 'message', etc.
    event_type TEXT NOT NULL,
    event_data TEXT NOT NULL, -- JSON event payload
    event_metadata TEXT,
    sequence_number INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT NOT NULL
);

-- Checkpoints for recovery points
CREATE TABLE IF NOT EXISTS mcp_checkpoints (
    checkpoint_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    checkpoint_name TEXT UNIQUE NOT NULL,
    checkpoint_type TEXT NOT NULL, -- 'manual', 'auto', 'scheduled'
    system_state TEXT NOT NULL, -- JSON snapshot of entire system
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    description TEXT,
    is_valid BOOLEAN DEFAULT 1
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_mcp_states_agent ON mcp_states(agent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_mcp_transactions_agent ON mcp_transactions(agent_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_mcp_sessions_agent ON mcp_sessions(agent_id, status);
CREATE INDEX IF NOT EXISTS idx_mcp_cache_expires ON mcp_cache(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_mcp_events_aggregate ON mcp_events(aggregate_id, sequence_number);
CREATE INDEX IF NOT EXISTS idx_mcp_data_versions_record ON mcp_data_versions(table_name, record_id, version_number);

-- Triggers for automatic timestamping and cleanup
CREATE TRIGGER IF NOT EXISTS update_session_activity
AFTER UPDATE ON mcp_sessions
BEGIN
    UPDATE mcp_sessions SET last_activity = CURRENT_TIMESTAMP 
    WHERE session_id = NEW.session_id;
END;

CREATE TRIGGER IF NOT EXISTS cleanup_expired_cache
AFTER INSERT ON mcp_cache
BEGIN
    DELETE FROM mcp_cache 
    WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP;
END;
