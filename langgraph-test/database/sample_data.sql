-- =================================================================
-- INBOX DATABASE SAMPLE DATA
-- Test data for development and demonstration
-- =================================================================

-- =================================================================
-- SAMPLE USERS
-- Create test users with different profiles
-- =================================================================
INSERT INTO users (email, username, password_hash, first_name, last_name, display_name, timezone, language, email_verified, is_active) VALUES
('john.doe@example.com', 'johndoe', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/v5v5v5v5v', 'John', 'Doe', 'John D.', 'America/New_York', 'en', true, true),
('jane.smith@example.com', 'janesmith', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/v5v5v5v5v', 'Jane', 'Smith', 'Jane S.', 'Europe/London', 'en', true, true),
('mike.wilson@example.com', 'mikewilson', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/v5v5v5v5v', 'Mike', 'Wilson', 'Mike W.', 'America/Los_Angeles', 'en', true, true),
('sarah.johnson@example.com', 'sarahjohnson', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/v5v5v5v5v', 'Sarah', 'Johnson', 'Sarah J.', 'Asia/Tokyo', 'en', false, true),
('admin@example.com', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/v5v5v5v5v', 'Admin', 'User', 'Administrator', 'UTC', 'en', true, true);

-- =================================================================
-- CUSTOM FOLDERS
-- Add some custom folders (system folders created automatically by trigger)
-- =================================================================
INSERT INTO folders (user_id, name, folder_type, color, sort_order) VALUES
-- John Doe's custom folders
(1, 'Work', 'custom', '#FF5722', 10),
(1, 'Personal', 'custom', '#4CAF50', 11),
(1, 'Projects', 'custom', '#2196F3', 12),
-- Jane Smith's custom folders
(2, 'Clients', 'custom', '#9C27B0', 10),
(2, 'Marketing', 'custom', '#FF9800', 11),
-- Mike Wilson's custom folders
(3, 'Development', 'custom', '#607D8B', 10),
(3, 'Support', 'custom', '#795548', 11);

-- =================================================================
-- SAMPLE MESSAGES
-- Create realistic test messages with various statuses
-- =================================================================

-- Messages for John Doe (user_id: 1)
INSERT INTO messages (message_id, thread_id, sender_id, sender_email, owner_id, folder_id, subject, body_text, body_html, priority, is_read, is_starred, is_important, sent_at, received_at) VALUES
-- Inbox messages
('msg_001', 'thread_001', 2, 'jane.smith@example.com', 1, 1, 'Project Kickoff Meeting', 'Hi John,\n\nLet''s schedule the project kickoff meeting for next week. Are you available on Tuesday afternoon?\n\nBest regards,\nJane', '<p>Hi John,</p><p>Let''s schedule the project kickoff meeting for next week. Are you available on Tuesday afternoon?</p><p>Best regards,<br>Jane</p>', 'high', false, true, true, NOW() - INTERVAL '2 hours', NOW() - INTERVAL '2 hours'),

('msg_002', 'thread_002', 3, 'mike.wilson@example.com', 1, 1, 'Code Review Request', 'Hey John,\n\nCould you please review the authentication module? The PR is ready for review.\n\nThanks!\nMike', '<p>Hey John,</p><p>Could you please review the authentication module? The PR is ready for review.</p><p>Thanks!<br>Mike</p>', 'normal', true, false, false, NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day'),

('msg_003', 'thread_003', 4, 'sarah.johnson@example.com', 1, 1, 'Weekly Report', 'Hi John,\n\nAttached is the weekly progress report. Everything is on track for the current sprint.\n\nRegards,\nSarah', '<p>Hi John,</p><p>Attached is the weekly progress report. Everything is on track for the current sprint.</p><p>Regards,<br>Sarah</p>', 'normal', false, false, false, NOW() - INTERVAL '3 hours', NOW() - INTERVAL '3 hours'),

-- Work folder messages
('msg_004', 'thread_004', 5, 'admin@example.com', 1, 5, 'System Maintenance Notice', 'Dear Team,\n\nScheduled maintenance will occur this weekend. Please save your work before Friday 5 PM.\n\nIT Department', '<p>Dear Team,</p><p>Scheduled maintenance will occur this weekend. Please save your work before Friday 5 PM.</p><p>IT Department</p>', 'urgent', true, true, true, NOW() - INTERVAL '1 week', NOW() - INTERVAL '1 week'),

-- Draft message
('msg_005', null, 1, 'john.doe@example.com', 1, 3, 'Meeting Follow-up', 'Hi team,\n\nFollowing up on our meeting today...', '<p>Hi team,</p><p>Following up on our meeting today...</p>', 'normal', false, false, false, NULL, NOW() - INTERVAL '30 minutes');

-- Update the draft message
UPDATE messages SET is_draft = true WHERE message_id = 'msg_005';

-- Messages for Jane Smith (user_id: 2)
INSERT INTO messages (message_id, thread_id, sender_id, sender_email, owner_id, folder_id, subject, body_text, body_html, priority, is_read, is_starred, sent_at, received_at) VALUES
-- Inbox messages
('msg_006', 'thread_005', 1, 'john.doe@example.com', 2, 6, 'Re: Project Kickoff Meeting', 'Hi Jane,\n\nTuesday afternoon works for me. How about 2 PM?\n\nBest,\nJohn', '<p>Hi Jane,</p><p>Tuesday afternoon works for me. How about 2 PM?</p><p>Best,<br>John</p>', 'high', true, false, NOW() - INTERVAL '1 hour', NOW() - INTERVAL '1 hour'),

('msg_007', 'thread_006', 3, 'mike.wilson@example.com', 2, 6, 'Bug Report: Login Issue', 'Jane,\n\nUsers are reporting login issues. This needs immediate attention.\n\nDetails:\n- Error occurs on mobile devices\n- Started happening after yesterday''s deployment\n\nMike', '<p>Jane,</p><p>Users are reporting login issues. This needs immediate attention.</p><ul><li>Error occurs on mobile devices</li><li>Started happening after yesterday''s deployment</li></ul><p>Mike</p>', 'urgent', false, true, NOW() - INTERVAL '4 hours', NOW() - INTERVAL '4 hours');

-- Messages for Mike Wilson (user_id: 3)
INSERT INTO messages (message_id, thread_id, sender_id, sender_email, owner_id, folder_id, subject, body_text, body_html, priority, is_read, is_starred, sent_at, received_at) VALUES
-- Development folder messages
('msg_008', 'thread_007', 1, 'john.doe@example.com', 3, 15, 'Code Review Feedback', 'Mike,\n\nGreat work on the auth module! Just a few minor suggestions:\n\n1. Add input validation\n2. Improve error handling\n3. Add unit tests\n\nOtherwise looks good to merge.\n\nJohn', '<p>Mike,</p><p>Great work on the auth module! Just a few minor suggestions:</p><ol><li>Add input validation</li><li>Improve error handling</li><li>Add unit tests</li></ol><p>Otherwise looks good to merge.</p><p>John</p>', 'normal', true, false, NOW() - INTERVAL '6 hours', NOW() - INTERVAL '6 hours');

-- =================================================================
-- MESSAGE RECIPIENTS
-- Add recipients for the messages
-- =================================================================
INSERT INTO message_recipients (message_id, recipient_type, recipient_email, recipient_name, user_id) VALUES
-- msg_001 recipients
(1, 'to', 'john.doe@example.com', 'John Doe', 1),
-- msg_002 recipients
(2, 'to', 'john.doe@example.com', 'John Doe', 1),
(2, 'cc', 'jane.smith@example.com', 'Jane Smith', 2),
-- msg_003 recipients
(3, 'to', 'john.doe@example.com', 'John Doe', 1),
(3, 'cc', 'mike.wilson@example.com', 'Mike Wilson', 3),
-- msg_004 recipients (team-wide)
(4, 'to', 'team@example.com', 'Development Team', NULL),
-- msg_006 recipients
(6, 'to', 'jane.smith@example.com', 'Jane Smith', 2),
-- msg_007 recipients
(7, 'to', 'jane.smith@example.com', 'Jane Smith', 2),
(7, 'cc', 'john.doe@example.com', 'John Doe', 1),
-- msg_008 recipients
(8, 'to', 'mike.wilson@example.com', 'Mike Wilson', 3);

-- =================================================================
-- MESSAGE ATTACHMENTS
-- Add sample attachments
-- =================================================================
INSERT INTO message_attachments (message_id, filename, content_type, file_size, file_path, is_inline) VALUES
-- Weekly report attachment
(3, 'weekly_report.pdf', 'application/pdf', 2048576, '/attachments/2024/01/weekly_report.pdf', false),
(3, 'chart.png', 'image/png', 512000, '/attachments/2024/01/chart.png', true),
-- System maintenance attachment
(4, 'maintenance_schedule.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 1024000, '/attachments/2024/01/maintenance_schedule.xlsx', false);

-- =================================================================
-- MESSAGE TAGS
-- Add some sample tags
-- =================================================================
INSERT INTO message_tags (message_id, tag_name, tag_color) VALUES
-- Project-related tags
(1, 'urgent', '#F44336'),
(1, 'meeting', '#2196F3'),
(2, 'code-review', '#4CAF50'),
(3, 'reports', '#FF9800'),
(4, 'maintenance', '#9C27B0'),
(7, 'bug', '#F44336'),
(7, 'urgent', '#F44336'),
(8, 'development', '#607D8B');

-- =================================================================
-- MESSAGE HEADERS
-- Add some sample email headers
-- =================================================================
INSERT INTO message_headers (message_id, header_name, header_value) VALUES
-- Standard email headers
(1, 'Message-ID', '<001_jane_smith@example.com>'),
(1, 'References', '<thread_001@example.com>'),
(1, 'X-Priority', '1'),
(2, 'Message-ID', '<002_mike_wilson@example.com>'),
(2, 'User-Agent', 'Thunderbird 102.0'),
(3, 'Message-ID', '<003_sarah_johnson@example.com>'),
(3, 'X-Mailer', 'Outlook 16.0'),
(4, 'Message-ID', '<004_admin@example.com>'),
(4, 'X-Priority', '1'),
(4, 'Importance', 'high');

-- =================================================================
-- UPDATE FOLDER COUNTS
-- Manual update since triggers won't fire for existing data
-- =================================================================
UPDATE folders SET
    message_count = (
        SELECT COUNT(*) FROM messages
        WHERE messages.folder_id = folders.id AND is_deleted = false
    ),
    unread_count = (
        SELECT COUNT(*) FROM messages
        WHERE messages.folder_id = folders.id AND is_read = false AND is_deleted = false
    );

-- =================================================================
-- SAMPLE DATA COMPLETE
-- Database populated with realistic test data
-- =================================================================