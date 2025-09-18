import React, { useState, useMemo } from 'react';
import './InboxApp.css';

const InboxApp = () => {
  const [selectedFolder, setSelectedFolder] = useState('inbox');
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isComposing, setIsComposing] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Mock data - in real app would come from API
  const folders = [
    { id: 'inbox', name: 'Inbox', count: 12, icon: '📥' },
    { id: 'sent', name: 'Sent', count: 8, icon: '📤' },
    { id: 'drafts', name: 'Drafts', count: 3, icon: '📝' },
    { id: 'archive', name: 'Archive', count: 45, icon: '🗃️' },
    { id: 'spam', name: 'Spam', count: 2, icon: '🚫' },
    { id: 'trash', name: 'Trash', count: 5, icon: '🗑️' }
  ];

  const messages = [
    {
      id: 1,
      from: 'Backend API Agent',
      subject: 'System Status Update',
      preview: 'All systems running normally. Database optimizations completed successfully...',
      date: '2025-09-17',
      time: '09:15',
      read: false,
      important: true,
      folder: 'inbox'
    },
    {
      id: 2,
      from: 'Database Agent',
      subject: 'Query Performance Report',
      preview: 'Monthly performance metrics show 15% improvement in response times...',
      date: '2025-09-17',
      time: '08:30',
      read: true,
      important: false,
      folder: 'inbox'
    },
    {
      id: 3,
      from: 'Security Agent',
      subject: 'Security Scan Results',
      preview: 'Weekly security scan completed. No vulnerabilities found...',
      date: '2025-09-16',
      time: '18:45',
      read: true,
      important: false,
      folder: 'inbox'
    },
    {
      id: 4,
      from: 'Testing Agent',
      subject: 'Test Suite Results',
      preview: 'All 127 tests passed successfully. Coverage: 94.2%...',
      date: '2025-09-16',
      time: '16:20',
      read: false,
      important: false,
      folder: 'inbox'
    },
    {
      id: 5,
      from: 'DevOps Agent',
      subject: 'Deployment Successful',
      preview: 'Version 2.1.4 deployed to production. All services healthy...',
      date: '2025-09-16',
      time: '14:10',
      read: true,
      important: true,
      folder: 'sent'
    }
  ];

  const filteredMessages = useMemo(() => {
    return messages.filter(msg => {
      const matchesFolder = msg.folder === selectedFolder;
      const matchesSearch = searchQuery === '' ||
        msg.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
        msg.from.toLowerCase().includes(searchQuery.toLowerCase()) ||
        msg.preview.toLowerCase().includes(searchQuery.toLowerCase());

      return matchesFolder && matchesSearch;
    });
  }, [selectedFolder, searchQuery]);

  return (
    <div className="inbox-app">
      {/* Mobile overlay */}
      {sidebarOpen && <div className="mobile-overlay" onClick={() => setSidebarOpen(false)} />}

      {/* Sidebar */}
      <aside className={`inbox-sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2>📧 Inbox</h2>
          <button
            className="compose-btn"
            onClick={() => setIsComposing(true)}
            aria-label="Compose new message"
          >
            ✏️ Compose
          </button>
        </div>

        <nav className="folders-nav">
          <ul>
            {folders.map(folder => (
              <li key={folder.id}>
                <button
                  className={`folder-btn ${selectedFolder === folder.id ? 'active' : ''}`}
                  onClick={() => {
                    setSelectedFolder(folder.id);
                    setSidebarOpen(false);
                  }}
                >
                  <span className="folder-icon">{folder.icon}</span>
                  <span className="folder-name">{folder.name}</span>
                  {folder.count > 0 && (
                    <span className="folder-count">{folder.count}</span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      {/* Main content */}
      <main className="inbox-main">
        {/* Header */}
        <header className="inbox-header">
          <button
            className="mobile-menu-btn"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open sidebar"
          >
            ☰
          </button>

          <div className="search-container">
            <input
              type="search"
              placeholder="Search messages..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
            <span className="search-icon">🔍</span>
          </div>

          <div className="header-actions">
            <button className="refresh-btn" aria-label="Refresh">🔄</button>
            <button className="settings-btn" aria-label="Settings">⚙️</button>
          </div>
        </header>

        {/* Message list */}
        <div className="message-list-container">
          {filteredMessages.length === 0 ? (
            <div className="empty-state">
              <p>No messages found</p>
              {searchQuery && (
                <button onClick={() => setSearchQuery('')}>Clear search</button>
              )}
            </div>
          ) : (
            <div className="message-list">
              {filteredMessages.map(message => (
                <div
                  key={message.id}
                  className={`message-item ${!message.read ? 'unread' : ''} ${selectedMessage?.id === message.id ? 'selected' : ''}`}
                  onClick={() => setSelectedMessage(message)}
                >
                  <div className="message-status">
                    {!message.read && <span className="unread-dot" />}
                    {message.important && <span className="important-star">⭐</span>}
                  </div>

                  <div className="message-content">
                    <div className="message-header">
                      <span className="message-from">{message.from}</span>
                      <span className="message-date">{message.time}</span>
                    </div>
                    <div className="message-subject">{message.subject}</div>
                    <div className="message-preview">{message.preview}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Message view */}
      {selectedMessage && (
        <section className="message-view">
          <header className="message-view-header">
            <button
              className="close-message-btn"
              onClick={() => setSelectedMessage(null)}
              aria-label="Close message"
            >
              ✕
            </button>
            <div className="message-actions">
              <button aria-label="Reply">↩️</button>
              <button aria-label="Forward">➡️</button>
              <button aria-label="Archive">🗃️</button>
              <button aria-label="Delete">🗑️</button>
            </div>
          </header>

          <div className="message-details">
            <h3>{selectedMessage.subject}</h3>
            <div className="message-meta">
              <span>From: {selectedMessage.from}</span>
              <span>Date: {selectedMessage.date} at {selectedMessage.time}</span>
            </div>
            <div className="message-body">
              <p>{selectedMessage.preview}</p>
              <p>This is the full message content. In a real application, this would contain the complete message body with proper formatting, attachments, and other rich content.</p>
            </div>
          </div>
        </section>
      )}

      {/* Compose modal */}
      {isComposing && (
        <div className="compose-modal-overlay">
          <div className="compose-modal">
            <header className="compose-header">
              <h3>New Message</h3>
              <button
                className="close-compose-btn"
                onClick={() => setIsComposing(false)}
                aria-label="Close compose"
              >
                ✕
              </button>
            </header>

            <form className="compose-form">
              <input
                type="email"
                placeholder="To..."
                className="compose-input"
                required
              />
              <input
                type="text"
                placeholder="Subject..."
                className="compose-input"
              />
              <textarea
                placeholder="Write your message..."
                className="compose-textarea"
                rows="10"
                required
              />

              <div className="compose-actions">
                <button type="submit" className="send-btn">Send</button>
                <button type="button" className="draft-btn">Save Draft</button>
                <button
                  type="button"
                  className="cancel-btn"
                  onClick={() => setIsComposing(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default InboxApp;