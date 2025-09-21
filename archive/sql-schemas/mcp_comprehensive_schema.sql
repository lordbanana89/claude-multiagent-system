-- =====================================================
-- MCP COMPREHENSIVE DATABASE SCHEMA
-- =====================================================
-- Complete table design for Multi-Agent Coordination Platform
-- Created by: Database Agent
-- Date: 2025-01-19
-- =====================================================

-- =====================================================
-- SECTION 1: CORE BUSINESS DOMAIN TABLES
-- =====================================================

-- Projects table for managing multi-agent projects
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    project_name TEXT NOT NULL,
    description TEXT,
    project_type TEXT NOT NULL, -- 'development', 'research', 'automation', 'integration'
    status TEXT DEFAULT 'planning', -- 'planning', 'active', 'paused', 'completed', 'archived'
    priority INTEGER DEFAULT 5, -- 1-10 scale
    owner_agent_id TEXT,
    team_agents TEXT, -- JSON array of agent IDs
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    deadline TIMESTAMP,
    budget REAL,
    resources TEXT, -- JSON object of required resources
    metadata TEXT, -- JSON additional data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_agent_id) REFERENCES agents(id)
);

-- Workflows for complex multi-step processes
CREATE TABLE IF NOT EXISTS workflows (
    workflow_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    workflow_name TEXT NOT NULL,
    project_id TEXT,
    workflow_type TEXT NOT NULL, -- 'sequential', 'parallel', 'conditional', 'loop'
    definition TEXT NOT NULL, -- JSON workflow definition
    current_step INTEGER DEFAULT 0,
    total_steps INTEGER,
    status TEXT DEFAULT 'draft', -- 'draft', 'running', 'paused', 'completed', 'failed'
    error_handling TEXT, -- JSON error handling rules
    retry_policy TEXT, -- JSON retry configuration
    created_by TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (created_by) REFERENCES agents(id)
);

-- Workflow steps for granular control
CREATE TABLE IF NOT EXISTS workflow_steps (
    step_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    workflow_id TEXT NOT NULL,
    step_number INTEGER NOT NULL,
    step_name TEXT NOT NULL,
    step_type TEXT NOT NULL, -- 'task', 'decision', 'parallel', 'wait'
    assigned_agent_id TEXT,
    input_data TEXT, -- JSON input parameters
    output_data TEXT, -- JSON output results
    conditions TEXT, -- JSON conditions for execution
    status TEXT DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'skipped'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id),
    FOREIGN KEY (assigned_agent_id) REFERENCES agents(id)
);

-- Resources management
CREATE TABLE IF NOT EXISTS resources (
    resource_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    resource_name TEXT NOT NULL,
    resource_type TEXT NOT NULL, -- 'compute', 'storage', 'api', 'database', 'service'
    resource_status TEXT DEFAULT 'available', -- 'available', 'in_use', 'maintenance', 'unavailable'
    capacity REAL,
    current_usage REAL,
    owner_agent_id TEXT,
    access_policy TEXT, -- JSON access rules
    cost_per_unit REAL,
    metadata TEXT, -- JSON additional properties
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Resource allocations tracking
CREATE TABLE IF NOT EXISTS resource_allocations (
    allocation_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    resource_id TEXT NOT NULL,
    allocated_to TEXT NOT NULL, -- agent_id or project_id
    allocation_type TEXT NOT NULL, -- 'agent', 'project', 'task'
    quantity REAL NOT NULL,
    priority INTEGER DEFAULT 5,
    allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    released_at TIMESTAMP,
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
);

-- =====================================================
-- SECTION 2: COMMUNICATION & COORDINATION TABLES
-- =====================================================

-- Enhanced messages table with threading and priority
CREATE TABLE IF NOT EXISTS messages_v2 (
    message_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    thread_id TEXT,
    parent_message_id TEXT,
    sender_id TEXT NOT NULL,
    recipient_id TEXT, -- NULL for broadcasts
    recipient_group TEXT, -- For group messages
    message_type TEXT NOT NULL, -- 'direct', 'broadcast', 'request', 'response', 'notification'
    priority INTEGER DEFAULT 5, -- 1-10 scale
    subject TEXT,
    content TEXT NOT NULL,
    attachments TEXT, -- JSON array of attachment references
    encryption_type TEXT, -- 'none', 'aes256', 'rsa'
    delivery_status TEXT DEFAULT 'pending', -- 'pending', 'sent', 'delivered', 'read', 'failed'
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES agents(id),
    FOREIGN KEY (parent_message_id) REFERENCES messages_v2(message_id)
);

-- Channels for organized communication
CREATE TABLE IF NOT EXISTS channels (
    channel_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    channel_name TEXT UNIQUE NOT NULL,
    channel_type TEXT NOT NULL, -- 'public', 'private', 'direct', 'system'
    description TEXT,
    owner_agent_id TEXT,
    members TEXT, -- JSON array of agent IDs
    permissions TEXT, -- JSON permission rules
    is_archived BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMP,
    FOREIGN KEY (owner_agent_id) REFERENCES agents(id)
);

-- Subscriptions for event-driven communication
CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    subscriber_id TEXT NOT NULL,
    subscription_type TEXT NOT NULL, -- 'channel', 'topic', 'agent', 'event'
    target_id TEXT NOT NULL, -- channel_id, topic, agent_id, or event_type
    filters TEXT, -- JSON filter criteria
    delivery_method TEXT DEFAULT 'push', -- 'push', 'pull', 'webhook'
    webhook_url TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (subscriber_id) REFERENCES agents(id)
);

-- Coordination protocols
CREATE TABLE IF NOT EXISTS coordination_protocols (
    protocol_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    protocol_name TEXT NOT NULL,
    protocol_type TEXT NOT NULL, -- 'consensus', 'voting', 'auction', 'negotiation'
    participants TEXT NOT NULL, -- JSON array of agent IDs
    rules TEXT NOT NULL, -- JSON protocol rules
    state TEXT, -- JSON current protocol state
    timeout_seconds INTEGER,
    status TEXT DEFAULT 'pending', -- 'pending', 'active', 'completed', 'failed', 'timeout'
    result TEXT, -- JSON protocol result
    initiated_by TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (initiated_by) REFERENCES agents(id)
);

-- =====================================================
-- SECTION 3: MONITORING & ANALYTICS TABLES
-- =====================================================

-- Performance metrics
CREATE TABLE IF NOT EXISTS performance_metrics (
    metric_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    agent_id TEXT,
    metric_type TEXT NOT NULL, -- 'cpu', 'memory', 'disk', 'network', 'custom'
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    unit TEXT, -- 'percent', 'bytes', 'seconds', etc.
    tags TEXT, -- JSON tags for filtering
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- System logs with structured data
CREATE TABLE IF NOT EXISTS system_logs (
    log_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    log_level TEXT NOT NULL, -- 'debug', 'info', 'warning', 'error', 'critical'
    source TEXT NOT NULL, -- agent_id or system component
    category TEXT,
    message TEXT NOT NULL,
    context TEXT, -- JSON structured context
    stack_trace TEXT,
    correlation_id TEXT, -- For tracking related logs
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit trail for compliance
CREATE TABLE IF NOT EXISTS audit_trail (
    audit_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    old_value TEXT, -- JSON previous state
    new_value TEXT, -- JSON new state
    reason TEXT,
    ip_address TEXT,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (actor_id) REFERENCES agents(id)
);

-- Analytics aggregations
CREATE TABLE IF NOT EXISTS analytics_summary (
    summary_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    period_type TEXT NOT NULL, -- 'hour', 'day', 'week', 'month'
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    metrics TEXT NOT NULL, -- JSON aggregated metrics
    dimensions TEXT, -- JSON dimensions for grouping
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- SECTION 4: KNOWLEDGE & LEARNING TABLES
-- =====================================================

-- Knowledge base for shared learning
CREATE TABLE IF NOT EXISTS knowledge_base (
    knowledge_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    topic TEXT NOT NULL,
    category TEXT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    content_type TEXT, -- 'text', 'code', 'config', 'procedure'
    tags TEXT, -- JSON array of tags
    source_agent_id TEXT,
    confidence_score REAL, -- 0-1 confidence level
    validation_status TEXT DEFAULT 'pending', -- 'pending', 'validated', 'rejected'
    validated_by TEXT,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_agent_id) REFERENCES agents(id),
    FOREIGN KEY (validated_by) REFERENCES agents(id)
);

-- Learning patterns
CREATE TABLE IF NOT EXISTS learning_patterns (
    pattern_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    pattern_type TEXT NOT NULL, -- 'success', 'failure', 'optimization'
    context TEXT NOT NULL, -- JSON context where pattern applies
    pattern_data TEXT NOT NULL, -- JSON pattern details
    frequency INTEGER DEFAULT 1,
    success_rate REAL,
    discovered_by TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_applied TIMESTAMP,
    FOREIGN KEY (discovered_by) REFERENCES agents(id)
);

-- =====================================================
-- SECTION 5: SECURITY & ACCESS CONTROL TABLES
-- =====================================================

-- Roles for RBAC
CREATE TABLE IF NOT EXISTS roles (
    role_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    role_name TEXT UNIQUE NOT NULL,
    description TEXT,
    permissions TEXT NOT NULL, -- JSON array of permissions
    parent_role_id TEXT, -- For role hierarchy
    is_system_role BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_role_id) REFERENCES roles(role_id)
);

-- Agent roles mapping
CREATE TABLE IF NOT EXISTS agent_roles (
    agent_id TEXT NOT NULL,
    role_id TEXT NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by TEXT,
    expires_at TIMESTAMP,
    PRIMARY KEY (agent_id, role_id),
    FOREIGN KEY (agent_id) REFERENCES agents(id),
    FOREIGN KEY (role_id) REFERENCES roles(role_id),
    FOREIGN KEY (granted_by) REFERENCES agents(id)
);

-- Access tokens for authentication
CREATE TABLE IF NOT EXISTS access_tokens (
    token_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    agent_id TEXT NOT NULL,
    token_hash TEXT NOT NULL, -- Hashed token value
    token_type TEXT NOT NULL, -- 'bearer', 'api_key', 'refresh'
    scope TEXT, -- JSON array of scopes
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    last_used TIMESTAMP,
    revoked_at TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Core indexes
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status, priority);
CREATE INDEX IF NOT EXISTS idx_workflows_project ON workflows(project_id, status);
CREATE INDEX IF NOT EXISTS idx_workflow_steps_workflow ON workflow_steps(workflow_id, step_number);
CREATE INDEX IF NOT EXISTS idx_resources_type_status ON resources(resource_type, resource_status);

-- Communication indexes
CREATE INDEX IF NOT EXISTS idx_messages_v2_thread ON messages_v2(thread_id, created_at);
CREATE INDEX IF NOT EXISTS idx_messages_v2_recipient ON messages_v2(recipient_id, priority DESC, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_subscriptions_subscriber ON subscriptions(subscriber_id, is_active);

-- Monitoring indexes
CREATE INDEX IF NOT EXISTS idx_performance_metrics_agent ON performance_metrics(agent_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(log_level, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_trail_actor ON audit_trail(actor_id, timestamp DESC);

-- Knowledge indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_base_topic ON knowledge_base(topic, validation_status);
CREATE INDEX IF NOT EXISTS idx_learning_patterns_type ON learning_patterns(pattern_type, success_rate DESC);

