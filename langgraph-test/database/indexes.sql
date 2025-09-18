-- =================================================================
-- INBOX DATABASE INDEXES
-- Optimized indexes for high-performance inbox operations
-- =================================================================

-- =================================================================
-- USERS TABLE INDEXES
-- Authentication and user lookup optimization
-- =================================================================
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_last_login ON users(last_login_at);
CREATE INDEX idx_users_email_verified ON users(email_verified);

-- =================================================================
-- FOLDERS TABLE INDEXES
-- Folder hierarchy and organization optimization
-- =================================================================
CREATE INDEX idx_folders_user ON folders(user_id);
CREATE INDEX idx_folders_parent ON folders(parent_id);
CREATE INDEX idx_folders_type ON folders(folder_type);
CREATE INDEX idx_folders_user_type ON folders(user_id, folder_type);
CREATE INDEX idx_folders_user_parent ON folders(user_id, parent_id);
CREATE INDEX idx_folders_system ON folders(is_system);

-- =================================================================
-- MESSAGES TABLE INDEXES
-- Critical for inbox performance and message operations
-- =================================================================

-- Primary message access patterns
CREATE INDEX idx_messages_owner_folder ON messages(owner_id, folder_id);
CREATE INDEX idx_messages_folder_received ON messages(folder_id, received_at DESC);
CREATE INDEX idx_messages_owner_received ON messages(owner_id, received_at DESC);

-- Message relationships
CREATE INDEX idx_messages_sender ON messages(sender_id);
CREATE INDEX idx_messages_thread ON messages(thread_id);
CREATE INDEX idx_messages_message_id ON messages(message_id);

-- Status-based queries (most common inbox operations)
CREATE INDEX idx_messages_unread ON messages(owner_id, is_read, received_at DESC);
CREATE INDEX idx_messages_starred ON messages(owner_id, is_starred, received_at DESC);
CREATE INDEX idx_messages_important ON messages(owner_id, is_important, received_at DESC);
CREATE INDEX idx_messages_drafts ON messages(owner_id, is_draft, updated_at DESC);

-- Soft delete support
CREATE INDEX idx_messages_deleted ON messages(is_deleted, deleted_at);
CREATE INDEX idx_messages_owner_not_deleted ON messages(owner_id, is_deleted, received_at DESC);

-- Full-text search indexes (PostgreSQL specific)
CREATE INDEX idx_messages_subject_search ON messages USING gin(to_tsvector('english', subject));
CREATE INDEX idx_messages_body_search ON messages USING gin(to_tsvector('english', body_text));

-- Combined search index for subject and body
CREATE INDEX idx_messages_content_search ON messages USING gin(
    to_tsvector('english', coalesce(subject, '') || ' ' || coalesce(body_text, ''))
);

-- Priority and size queries
CREATE INDEX idx_messages_priority ON messages(priority, received_at DESC);
CREATE INDEX idx_messages_size ON messages(message_size);
CREATE INDEX idx_messages_attachments ON messages(has_attachments, received_at DESC);

-- =================================================================
-- MESSAGE RECIPIENTS TABLE INDEXES
-- Recipient lookup and message composition
-- =================================================================
CREATE INDEX idx_recipients_message ON message_recipients(message_id);
CREATE INDEX idx_recipients_email ON message_recipients(recipient_email);
CREATE INDEX idx_recipients_type ON message_recipients(message_id, recipient_type);
CREATE INDEX idx_recipients_user ON message_recipients(user_id);

-- Combined index for efficient recipient queries
CREATE INDEX idx_recipients_email_type ON message_recipients(recipient_email, recipient_type);

-- =================================================================
-- MESSAGE ATTACHMENTS TABLE INDEXES
-- Attachment queries and file management
-- =================================================================
CREATE INDEX idx_attachments_message ON message_attachments(message_id);
CREATE INDEX idx_attachments_filename ON message_attachments(filename);
CREATE INDEX idx_attachments_content_type ON message_attachments(content_type);
CREATE INDEX idx_attachments_size ON message_attachments(file_size);
CREATE INDEX idx_attachments_inline ON message_attachments(is_inline);
CREATE INDEX idx_attachments_content_id ON message_attachments(content_id);

-- =================================================================
-- MESSAGE TAGS TABLE INDEXES
-- Tag-based organization and filtering
-- =================================================================
CREATE INDEX idx_tags_message ON message_tags(message_id);
CREATE INDEX idx_tags_name ON message_tags(tag_name);
CREATE INDEX idx_tags_color ON message_tags(tag_color);

-- Combined index for tag filtering
CREATE INDEX idx_tags_name_message ON message_tags(tag_name, message_id);

-- =================================================================
-- MESSAGE HEADERS TABLE INDEXES
-- Email header lookup and compliance
-- =================================================================
CREATE INDEX idx_headers_message ON message_headers(message_id);
CREATE INDEX idx_headers_name ON message_headers(header_name);
CREATE INDEX idx_headers_message_name ON message_headers(message_id, header_name);

-- =================================================================
-- COMPOSITE INDEXES FOR COMPLEX QUERIES
-- Advanced query optimization for common use cases
-- =================================================================

-- Inbox view: unread messages in specific folder
CREATE INDEX idx_inbox_view ON messages(owner_id, folder_id, is_read, is_deleted, received_at DESC);

-- Message search with status
CREATE INDEX idx_search_status ON messages(owner_id, is_deleted)
    INCLUDE (subject, sender_email, received_at, is_read, is_starred);

-- Thread view optimization
CREATE INDEX idx_thread_view ON messages(thread_id, sent_at ASC)
    WHERE thread_id IS NOT NULL;

-- Folder management queries
CREATE INDEX idx_folder_management ON messages(folder_id, is_deleted)
    INCLUDE (is_read, received_at);

-- =================================================================
-- PARTIAL INDEXES FOR SPECIFIC USE CASES
-- Space-efficient indexes for filtered queries
-- =================================================================

-- Only index non-deleted messages (most common case)
CREATE INDEX idx_messages_active ON messages(owner_id, received_at DESC)
    WHERE is_deleted = false;

-- Only index unread messages (smaller, faster)
CREATE INDEX idx_messages_unread_only ON messages(owner_id, folder_id, received_at DESC)
    WHERE is_read = false AND is_deleted = false;

-- Only index messages with attachments
CREATE INDEX idx_messages_with_attachments ON messages(owner_id, received_at DESC)
    WHERE has_attachments = true AND is_deleted = false;

-- Only index draft messages
CREATE INDEX idx_messages_drafts_only ON messages(owner_id, updated_at DESC)
    WHERE is_draft = true;

-- =================================================================
-- INDEXES COMPLETE
-- All indexes optimized for inbox performance
-- =================================================================