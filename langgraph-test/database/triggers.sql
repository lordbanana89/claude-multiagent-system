-- =================================================================
-- INBOX DATABASE TRIGGERS
-- Data integrity and automatic maintenance triggers
-- =================================================================

-- =================================================================
-- TIMESTAMP UPDATE TRIGGER FUNCTION
-- Automatically update 'updated_at' timestamps
-- =================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply timestamp triggers to all tables with updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_folders_updated_at
    BEFORE UPDATE ON folders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_messages_updated_at
    BEFORE UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =================================================================
-- FOLDER COUNT MAINTENANCE TRIGGERS
-- Keep message_count and unread_count synchronized
-- =================================================================
CREATE OR REPLACE FUNCTION update_folder_counts()
RETURNS TRIGGER AS $$
BEGIN
    -- Handle INSERT operations
    IF TG_OP = 'INSERT' THEN
        UPDATE folders SET
            message_count = message_count + 1,
            unread_count = unread_count + (CASE WHEN NEW.is_read = false THEN 1 ELSE 0 END)
        WHERE id = NEW.folder_id;
        RETURN NEW;
    END IF;

    -- Handle UPDATE operations
    IF TG_OP = 'UPDATE' THEN
        -- Handle read status changes
        IF OLD.is_read != NEW.is_read THEN
            UPDATE folders SET
                unread_count = unread_count + (CASE WHEN NEW.is_read = false THEN 1 ELSE -1 END)
            WHERE id = NEW.folder_id;
        END IF;

        -- Handle folder moves
        IF OLD.folder_id != NEW.folder_id THEN
            -- Decrease counts in old folder
            UPDATE folders SET
                message_count = message_count - 1,
                unread_count = unread_count - (CASE WHEN OLD.is_read = false THEN 1 ELSE 0 END)
            WHERE id = OLD.folder_id;

            -- Increase counts in new folder
            UPDATE folders SET
                message_count = message_count + 1,
                unread_count = unread_count + (CASE WHEN NEW.is_read = false THEN 1 ELSE 0 END)
            WHERE id = NEW.folder_id;
        END IF;

        -- Handle soft delete changes
        IF OLD.is_deleted != NEW.is_deleted THEN
            IF NEW.is_deleted = true THEN
                -- Message being deleted (soft delete)
                UPDATE folders SET
                    message_count = message_count - 1,
                    unread_count = unread_count - (CASE WHEN NEW.is_read = false THEN 1 ELSE 0 END)
                WHERE id = NEW.folder_id;
            ELSE
                -- Message being restored
                UPDATE folders SET
                    message_count = message_count + 1,
                    unread_count = unread_count + (CASE WHEN NEW.is_read = false THEN 1 ELSE 0 END)
                WHERE id = NEW.folder_id;
            END IF;
        END IF;

        RETURN NEW;
    END IF;

    -- Handle DELETE operations (hard delete)
    IF TG_OP = 'DELETE' THEN
        UPDATE folders SET
            message_count = message_count - 1,
            unread_count = unread_count - (CASE WHEN OLD.is_read = false THEN 1 ELSE 0 END)
        WHERE id = OLD.folder_id;
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ language 'plpgsql';

-- Apply folder count trigger
CREATE TRIGGER trigger_update_folder_counts
    AFTER INSERT OR UPDATE OR DELETE ON messages
    FOR EACH ROW EXECUTE FUNCTION update_folder_counts();

-- =================================================================
-- ATTACHMENT COUNT MAINTENANCE TRIGGER
-- Keep attachment_count synchronized on messages table
-- =================================================================
CREATE OR REPLACE FUNCTION update_attachment_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE messages SET
            attachment_count = attachment_count + 1,
            has_attachments = true
        WHERE id = NEW.message_id;
        RETURN NEW;
    END IF;

    IF TG_OP = 'DELETE' THEN
        UPDATE messages SET
            attachment_count = attachment_count - 1,
            has_attachments = (attachment_count - 1) > 0
        WHERE id = OLD.message_id;
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ language 'plpgsql';

-- Apply attachment count trigger
CREATE TRIGGER trigger_update_attachment_count
    AFTER INSERT OR DELETE ON message_attachments
    FOR EACH ROW EXECUTE FUNCTION update_attachment_count();

-- =================================================================
-- SYSTEM FOLDERS CREATION TRIGGER
-- Automatically create system folders for new users
-- =================================================================
CREATE OR REPLACE FUNCTION create_system_folders()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO folders (user_id, name, folder_type, is_system, sort_order) VALUES
        (NEW.id, 'Inbox', 'inbox', true, 1),
        (NEW.id, 'Sent', 'sent', true, 2),
        (NEW.id, 'Drafts', 'drafts', true, 3),
        (NEW.id, 'Trash', 'trash', true, 4);
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply system folders trigger
CREATE TRIGGER trigger_create_system_folders
    AFTER INSERT ON users
    FOR EACH ROW EXECUTE FUNCTION create_system_folders();

-- =================================================================
-- MESSAGE SOFT DELETE TRIGGER
-- Set deleted_at timestamp when is_deleted is set to true
-- =================================================================
CREATE OR REPLACE FUNCTION handle_message_soft_delete()
RETURNS TRIGGER AS $$
BEGIN
    -- When marking as deleted, set deleted_at
    IF OLD.is_deleted = false AND NEW.is_deleted = true THEN
        NEW.deleted_at = CURRENT_TIMESTAMP;
    END IF;

    -- When restoring from deleted, clear deleted_at
    IF OLD.is_deleted = true AND NEW.is_deleted = false THEN
        NEW.deleted_at = NULL;
    END IF;

    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply soft delete trigger
CREATE TRIGGER trigger_handle_message_soft_delete
    BEFORE UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION handle_message_soft_delete();

-- =================================================================
-- MESSAGE SNIPPET GENERATION TRIGGER
-- Automatically generate preview snippet from body text
-- =================================================================
CREATE OR REPLACE FUNCTION generate_message_snippet()
RETURNS TRIGGER AS $$
BEGIN
    -- Generate snippet from body_text if not provided
    IF NEW.snippet IS NULL OR NEW.snippet = '' THEN
        IF NEW.body_text IS NOT NULL THEN
            NEW.snippet = LEFT(REGEXP_REPLACE(NEW.body_text, '\s+', ' ', 'g'), 255);
        ELSIF NEW.body_html IS NOT NULL THEN
            -- Simple HTML strip for snippet (basic implementation)
            NEW.snippet = LEFT(REGEXP_REPLACE(
                REGEXP_REPLACE(NEW.body_html, '<[^>]*>', '', 'g'),
                '\s+', ' ', 'g'
            ), 255);
        END IF;
    END IF;

    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply snippet generation trigger
CREATE TRIGGER trigger_generate_message_snippet
    BEFORE INSERT OR UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION generate_message_snippet();

-- =================================================================
-- FOLDER HIERARCHY VALIDATION TRIGGER
-- Prevent circular references in folder hierarchy
-- =================================================================
CREATE OR REPLACE FUNCTION validate_folder_hierarchy()
RETURNS TRIGGER AS $$
DECLARE
    current_parent_id INTEGER;
    depth INTEGER := 0;
    max_depth INTEGER := 10; -- Prevent infinite loops
BEGIN
    -- Skip validation if parent_id is NULL (root folder)
    IF NEW.parent_id IS NULL THEN
        RETURN NEW;
    END IF;

    -- Check for immediate self-reference (already prevented by CHECK constraint)
    IF NEW.id = NEW.parent_id THEN
        RAISE EXCEPTION 'Folder cannot be its own parent';
    END IF;

    -- Walk up the hierarchy to check for cycles
    current_parent_id := NEW.parent_id;

    WHILE current_parent_id IS NOT NULL AND depth < max_depth LOOP
        -- If we find the current folder in the parent chain, it's a cycle
        IF current_parent_id = NEW.id THEN
            RAISE EXCEPTION 'Circular reference detected in folder hierarchy';
        END IF;

        -- Move up one level
        SELECT parent_id INTO current_parent_id
        FROM folders
        WHERE id = current_parent_id;

        depth := depth + 1;
    END LOOP;

    -- Check if we hit max depth (potential infinite loop)
    IF depth >= max_depth THEN
        RAISE EXCEPTION 'Folder hierarchy too deep (max % levels)', max_depth;
    END IF;

    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply hierarchy validation trigger
CREATE TRIGGER trigger_validate_folder_hierarchy
    BEFORE INSERT OR UPDATE ON folders
    FOR EACH ROW EXECUTE FUNCTION validate_folder_hierarchy();

-- =================================================================
-- PREVENT SYSTEM FOLDER DELETION TRIGGER
-- Protect system folders from being deleted
-- =================================================================
CREATE OR REPLACE FUNCTION prevent_system_folder_deletion()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.is_system = true THEN
        RAISE EXCEPTION 'Cannot delete system folder: %', OLD.name;
    END IF;
    RETURN OLD;
END;
$$ language 'plpgsql';

-- Apply system folder protection trigger
CREATE TRIGGER trigger_prevent_system_folder_deletion
    BEFORE DELETE ON folders
    FOR EACH ROW EXECUTE FUNCTION prevent_system_folder_deletion();

-- =================================================================
-- MESSAGE SIZE CALCULATION TRIGGER
-- Calculate message size from content
-- =================================================================
CREATE OR REPLACE FUNCTION calculate_message_size()
RETURNS TRIGGER AS $$
BEGIN
    NEW.message_size = COALESCE(LENGTH(NEW.subject), 0) +
                      COALESCE(LENGTH(NEW.body_text), 0) +
                      COALESCE(LENGTH(NEW.body_html), 0);
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply message size calculation trigger
CREATE TRIGGER trigger_calculate_message_size
    BEFORE INSERT OR UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION calculate_message_size();

-- =================================================================
-- TRIGGERS COMPLETE
-- All data integrity and maintenance triggers implemented
-- =================================================================