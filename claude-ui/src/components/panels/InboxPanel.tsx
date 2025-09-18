import React, { useState, useEffect } from 'react';
import axios from 'axios';
import type { Message } from '../../context/AppContext';
import { config } from '../../config';

interface InboxPanelProps {
  messages: Message[];
  agents: any[];
  selectedAgent: any;
  setMessages?: (messages: Message[]) => void;
}

// Simple error logging function
const logError = (context: string, error: any) => {
  console.error(`[${context}] Error:`, error);
};

const InboxPanel: React.FC<InboxPanelProps> = ({ messages, agents, selectedAgent }) => {
  const [filter, setFilter] = useState('all');
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const [composing, setComposing] = useState(false);
  const [newMessage, setNewMessage] = useState({
    to: '',
    subject: '',
    content: '',
    priority: 'normal' as const
  });
  const [loading, setLoading] = useState(false);

  // Fetch messages
  const fetchMessages = async () => {
    try {
      const params: any = {};
      if (filter !== 'all') {
        params.status = filter;
      }
      if (selectedAgent) {
        params.agent = selectedAgent.id;
      }

      const response = await axios.get(`${config.API_URL}/api/inbox/messages`, { params });
      if (setMessages) {
        setMessages(response.data);
      }
    } catch (err) {
      logError('fetchMessages', err);
    }
  };

  useEffect(() => {
    fetchMessages();
    const interval = setInterval(fetchMessages, 5000);
    return () => clearInterval(interval);
  }, [filter, selectedAgent]);

  // Mark message as read
  const markAsRead = async (messageId: string) => {
    try {
      await axios.patch(`${config.API_URL}/api/inbox/messages/${messageId}/read`);
      fetchMessages();
    } catch (err) {
      logError('markAsRead', err);
    }
  };

  // Archive message
  const archiveMessage = async (messageId: string) => {
    try {
      await axios.patch(`${config.API_URL}/api/inbox/messages/${messageId}/archive`);
      setSelectedMessage(null);
      fetchMessages();
    } catch (err) {
      logError('archiveMessage', err);
    }
  };

  // Send message
  const sendMessage = async () => {
    if (!newMessage.to || !newMessage.subject || !newMessage.content) {
      alert('Please fill all fields');
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${config.API_URL}/api/inbox/messages`, {
        from: selectedAgent?.id || 'system',
        to: newMessage.to,
        subject: newMessage.subject,
        content: newMessage.content,
        priority: newMessage.priority
      });

      setNewMessage({ to: '', subject: '', content: '', priority: 'normal' });
      setComposing(false);
      fetchMessages();
    } catch (err) {
      logError('sendMessage', err);
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'text-red-500 bg-red-900/20';
      case 'high': return 'text-orange-500 bg-orange-900/20';
      case 'normal': return 'text-blue-500 bg-blue-900/20';
      case 'low': return 'text-gray-500 bg-gray-900/20';
      default: return 'text-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'unread': return '📨';
      case 'read': return '📧';
      case 'archived': return '📦';
      default: return '📧';
    }
  };

  return (
    <div className="h-full flex bg-gray-900">
      {/* Message List */}
      <div className="w-1/3 bg-gray-800 border-r border-gray-700 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-white">Inbox</h2>
            <button
              onClick={() => setComposing(true)}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm text-white"
            >
              ✉️ Compose
            </button>
          </div>

          {/* Filters */}
          <div className="flex gap-2">
            {['all', 'unread', 'read', 'archived'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1 rounded text-xs capitalize ${
                  filter === f
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Message List */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              No messages
            </div>
          ) : (
            messages.map(message => (
              <div
                key={message.id}
                onClick={() => {
                  setSelectedMessage(message);
                  if (message.status === 'unread') {
                    markAsRead(message.id);
                  }
                }}
                className={`p-3 border-b border-gray-700 cursor-pointer hover:bg-gray-700 ${
                  selectedMessage?.id === message.id ? 'bg-gray-700' : ''
                } ${message.status === 'unread' ? 'bg-gray-750' : ''}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm">{getStatusIcon(message.status)}</span>
                      <span className="text-white font-medium text-sm truncate">
                        {message.from} → {message.to}
                      </span>
                    </div>
                    <div className="text-white text-sm font-medium truncate">
                      {message.subject}
                    </div>
                    <div className="text-gray-400 text-xs truncate">
                      {message.content}
                    </div>
                  </div>
                  <div className="flex flex-col items-end ml-2">
                    <span className={`text-xs px-2 py-1 rounded ${getPriorityColor(message.priority)}`}>
                      {message.priority}
                    </span>
                    <span className="text-xs text-gray-500 mt-1">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Message Content or Compose */}
      <div className="flex-1 flex flex-col">
        {composing ? (
          /* Compose Form */
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-white">New Message</h3>
              <button
                onClick={() => setComposing(false)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">To</label>
                <select
                  value={newMessage.to}
                  onChange={(e) => setNewMessage({ ...newMessage, to: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                >
                  <option value="">Select recipient...</option>
                  {agents.map(agent => (
                    <option key={agent.id} value={agent.id}>
                      {agent.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Subject</label>
                <input
                  type="text"
                  value={newMessage.subject}
                  onChange={(e) => setNewMessage({ ...newMessage, subject: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                  placeholder="Enter subject..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Priority</label>
                <div className="flex gap-2">
                  {['low', 'normal', 'high', 'critical'].map(p => (
                    <button
                      key={p}
                      onClick={() => setNewMessage({ ...newMessage, priority: p as any })}
                      className={`px-3 py-1 rounded text-sm capitalize ${
                        newMessage.priority === p
                          ? getPriorityColor(p).replace('text-', 'bg-').replace('-500', '-600') + ' text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Message</label>
                <textarea
                  value={newMessage.content}
                  onChange={(e) => setNewMessage({ ...newMessage, content: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none h-40 resize-none"
                  placeholder="Type your message..."
                />
              </div>

              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setComposing(false)}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded"
                >
                  Cancel
                </button>
                <button
                  onClick={sendMessage}
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded"
                >
                  {loading ? 'Sending...' : 'Send Message'}
                </button>
              </div>
            </div>
          </div>
        ) : selectedMessage ? (
          /* Message Detail */
          <div className="flex-1 flex flex-col">
            <div className="p-6 border-b border-gray-700">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">
                    {selectedMessage.subject}
                  </h3>
                  <div className="flex items-center gap-4 text-sm text-gray-400">
                    <span>From: {selectedMessage.from}</span>
                    <span>To: {selectedMessage.to}</span>
                    <span className={`px-2 py-1 rounded ${getPriorityColor(selectedMessage.priority)}`}>
                      {selectedMessage.priority}
                    </span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => archiveMessage(selectedMessage.id)}
                    className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm text-white"
                  >
                    📦 Archive
                  </button>
                  <button
                    onClick={() => setSelectedMessage(null)}
                    className="text-gray-400 hover:text-white"
                  >
                    ✕
                  </button>
                </div>
              </div>
            </div>

            <div className="flex-1 p-6 overflow-y-auto">
              <div className="text-gray-300 whitespace-pre-wrap">
                {selectedMessage.content}
              </div>
            </div>

            <div className="p-4 border-t border-gray-700 text-xs text-gray-500">
              Received: {new Date(selectedMessage.timestamp).toLocaleString()}
            </div>
          </div>
        ) : (
          /* Empty State */
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <p className="text-gray-400 mb-2">Select a message to read</p>
              <p className="text-gray-500 text-sm">or compose a new message</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default InboxPanel;