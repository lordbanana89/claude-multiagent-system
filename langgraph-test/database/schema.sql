-- =================================================================
-- INBOX DATABASE SCHEMA
-- Complete schema for multi-user inbox system
-- =================================================================

-- Drop existing tables if they exist (for development)
DROP TABLE IF EXISTS message_headers CASCADE;
DROP TABLE IF EXISTS message_tags CASCADE;
DROP TABLE IF EXISTS message_attachments CASCADE;
DROP TABLE IF EXISTS message_recipients CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS folders CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- =================================================================
-- USERS TABLE
-- Core user authentication and profile data
-- =================================================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(200),
    avatar_url VARCHAR(500),
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    email_verified BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =================================================================
-- FOLDERS TABLE
-- Hierarchical folder organization with system folder support
-- =================================================================
CREATE TABLE folders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES folders(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    folder_type VARCHAR(20) DEFAULT 'custom', -- 'inbox', 'sent', 'drafts', 'trash', 'custom'
    is_system BOOLEAN DEFAULT false, -- system folders cannot be deleted
    color VARCHAR(7), -- hex color for UI
    sort_order INTEGER DEFAULT 0,
    message_count INTEGER DEFAULT 0, -- denormalized for performance
    unread_count INTEGER DEFAULT 0, -- denormalized for performance
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Ensure unique folder names per user at same level
    UNIQUE(user_id, parent_id, name),
    -- Prevent cycles in hierarchy
    CHECK (id != parent_id)
);

-- =================================================================
-- MESSAGES TABLE
-- Core message storage with full metadata
-- =================================================================
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(255) UNIQUE NOT NULL, -- globally unique message identifier
    thread_id VARCHAR(255), -- for message threading

    -- User relationships
    sender_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    sender_email VARCHAR(255) NOT NULL, -- preserve email even if user deleted
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- message owner
    folder_id INTEGER NOT NULL REFERENCES folders(id) ON DELETE CASCADE,

    -- Message content
    subject VARCHAR(500) NOT NULL,
    body_text TEXT, -- plain text version
    body_html TEXT, -- HTML version
    snippet VARCHAR(255), -- preview text for listings

    -- Message metadata
    message_size INTEGER DEFAULT 0, -- in bytes
    has_attachments BOOLEAN DEFAULT false,
    attachment_count INTEGER DEFAULT 0,
    priority VARCHAR(10) DEFAULT 'normal', -- 'low', 'normal', 'high', 'urgent'

    -- Status flags
    is_read BOOLEAN DEFAULT false,
    is_starred BOOLEAN DEFAULT false,
    is_important BOOLEAN DEFAULT false,
    is_draft BOOLEAN DEFAULT false,
    is_deleted BOOLEAN DEFAULT false, -- soft delete

    -- Timestamps
    sent_at TIMESTAMP,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP -- for soft delete tracking
);

-- =================================================================
-- MESSAGE RECIPIENTS TABLE
-- Track To, CC, BCC recipients for each message
-- =================================================================
CREATE TABLE message_recipients (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    recipient_type VARCHAR(10) NOT NULL, -- 'to', 'cc', 'bcc'
    recipient_email VARCHAR(255) NOT NULL,
    recipient_name VARCHAR(255),
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL -- if recipient is system user
);

-- =================================================================
-- MESSAGE ATTACHMENTS TABLE
-- File attachment metadata and storage references
-- =================================================================
CREATE TABLE message_attachments (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100),
    file_size INTEGER NOT NULL,
    file_path VARCHAR(500), -- storage path
    is_inline BOOLEAN DEFAULT false,
    content_id VARCHAR(255), -- for inline attachments
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =================================================================
-- MESSAGE TAGS TABLE
-- Flexible labeling system for message organization
-- =================================================================
CREATE TABLE message_tags (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    tag_name VARCHAR(100) NOT NULL,
    tag_color VARCHAR(7), -- hex color
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(message_id, tag_name)
);

-- =================================================================
-- MESSAGE HEADERS TABLE
-- Store email headers for protocol compliance
-- =================================================================
CREATE TABLE message_headers (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    header_name VARCHAR(100) NOT NULL,
    header_value TEXT
);

-- =================================================================
-- SCHEMA COMPLETE
-- =================================================================