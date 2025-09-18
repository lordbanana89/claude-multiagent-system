import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

interface Message {
  id: string;
  from: string;
  to: string;
  subject: string;
  content: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  status: 'unread' | 'read' | 'archived';
  timestamp: string;
  type: 'task' | 'notification' | 'error' | 'success';
  metadata?: Record<string, any>;
}

interface Agent {
  id: string;
  name: string;
  type: string;
}

const InboxSystem: React.FC = () => {
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const [filter, setFilter] = useState<'all' | 'unread' | 'high-priority'>('all');
  const [selectedAgent, setSelectedAgent] = useState<string>('all');
  const [composeOpen, setComposeOpen] = useState(false);
  const queryClient = useQueryClient();

  // Fetch messages
  const { data: messages = [], isLoading: messagesLoading } = useQuery<Message[]>({
    queryKey: ['messages', filter, selectedAgent],
    queryFn: async () => {
      try {
        const params: any = {};
        if (filter === 'unread') params.status = 'unread';
        if (filter === 'high-priority') params.priority = 'high,urgent';
        if (selectedAgent !== 'all') params.agent = selectedAgent;

        const response = await axios.get(`${API_URL}/api/inbox/messages`, { params });
        return response.data;
      } catch {
        // Return mock data if API fails
        return generateMockMessages();
      }
    },
    refetchInterval: 5000,
  });

  // Fetch agents
  const { data: agents = [] } = useQuery<Agent[]>({
    queryKey: ['agents'],
    queryFn: async () => {
      try {
        const response = await axios.get(`${API_URL}/api/agents`);
        return response.data;
      } catch {
        return [];
      }
    },
  });

  // Mark as read mutation
  const markAsReadMutation = useMutation({
    mutationFn: async (messageId: string) => {
      await axios.patch(`${API_URL}/api/inbox/messages/${messageId}/read`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages'] });
    },
  });

  // Archive message mutation
  const archiveMutation = useMutation({
    mutationFn: async (messageId: string) => {
      await axios.patch(`${API_URL}/api/inbox/messages/${messageId}/archive`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages'] });
      setSelectedMessage(null);
    },
  });

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: async (message: Partial<Message>) => {
      await axios.post(`${API_URL}/api/inbox/messages`, message);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages'] });
      setComposeOpen(false);
    },
  });

  const handleMessageClick = (message: Message) => {
    setSelectedMessage(message);
    if (message.status === 'unread') {
      markAsReadMutation.mutate(message.id);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'text-red-600 dark:text-red-400';
      case 'high':
        return 'text-orange-600 dark:text-orange-400';
      case 'normal':
        return 'text-blue-600 dark:text-blue-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'task':
        return '📋';
      case 'notification':
        return '🔔';
      case 'error':
        return '❌';
      case 'success':
        return '✅';
      default:
        return '📧';
    }
  };

  const unreadCount = messages.filter(m => m.status === 'unread').length;
  const highPriorityCount = messages.filter(m => m.priority === 'high' || m.priority === 'urgent').length;

  return (
    <div className="h-[calc(100vh-8rem)] flex bg-gray-50 dark:bg-gray-900 rounded-lg overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 p-4">
        <button
          onClick={() => setComposeOpen(true)}
          className="w-full mb-6 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium"
        >
          ✉️ Compose Message
        </button>

        <div className="space-y-2 mb-6">
          <button
            onClick={() => setFilter('all')}
            className={`w-full text-left px-3 py-2 rounded ${
              filter === 'all' ? 'bg-gray-100 dark:bg-gray-700' : ''
            }`}
          >
            📥 All Messages
            <span className="float-right text-sm text-gray-500">{messages.length}</span>
          </button>
          <button
            onClick={() => setFilter('unread')}
            className={`w-full text-left px-3 py-2 rounded ${
              filter === 'unread' ? 'bg-gray-100 dark:bg-gray-700' : ''
            }`}
          >
            🔵 Unread
            <span className="float-right text-sm text-gray-500">{unreadCount}</span>
          </button>
          <button
            onClick={() => setFilter('high-priority')}
            className={`w-full text-left px-3 py-2 rounded ${
              filter === 'high-priority' ? 'bg-gray-100 dark:bg-gray-700' : ''
            }`}
          >
            ⚡ High Priority
            <span className="float-right text-sm text-gray-500">{highPriorityCount}</span>
          </button>
        </div>

        <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
          <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2">
            Filter by Agent
          </h3>
          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md text-sm"
          >
            <option value="all">All Agents</option>
            {agents.map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Message List */}
      <div className="flex-1 flex">
        <div className="w-96 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
          {messagesLoading ? (
            <div className="p-4 text-center text-gray-500">Loading messages...</div>
          ) : messages.length === 0 ? (
            <div className="p-4 text-center text-gray-500">No messages</div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {messages.map((message) => (
                <div
                  key={message.id}
                  onClick={() => handleMessageClick(message)}
                  className={`p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 ${
                    selectedMessage?.id === message.id ? 'bg-gray-50 dark:bg-gray-700' : ''
                  } ${message.status === 'unread' ? 'font-semibold' : ''}`}
                >
                  <div className="flex items-start justify-between mb-1">
                    <div className="flex items-center space-x-2">
                      <span>{getTypeIcon(message.type)}</span>
                      <span className="text-sm text-gray-900 dark:text-white">
                        {message.from}
                      </span>
                    </div>
                    <span className={`text-xs ${getPriorityColor(message.priority)}`}>
                      {message.priority}
                    </span>
                  </div>
                  <div className="text-sm text-gray-900 dark:text-white mb-1">
                    {message.subject}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {message.content}
                  </div>
                  <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                    {new Date(message.timestamp).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Message Detail */}
        <div className="flex-1 bg-white dark:bg-gray-800 p-6">
          {selectedMessage ? (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  {selectedMessage.subject}
                </h2>
                <div className="flex space-x-2">
                  <button
                    onClick={() => archiveMutation.mutate(selectedMessage.id)}
                    className="px-3 py-1 bg-gray-200 dark:bg-gray-700 rounded hover:bg-gray-300 dark:hover:bg-gray-600"
                  >
                    📁 Archive
                  </button>
                  <button className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">
                    ↩️ Reply
                  </button>
                </div>
              </div>

              <div className="mb-4 pb-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between text-sm">
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">From: </span>
                    <span className="text-gray-900 dark:text-white">{selectedMessage.from}</span>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className={`${getPriorityColor(selectedMessage.priority)} font-medium`}>
                      {selectedMessage.priority.toUpperCase()}
                    </span>
                    <span className="text-gray-500">
                      {new Date(selectedMessage.timestamp).toLocaleString()}
                    </span>
                  </div>
                </div>
                <div className="mt-1">
                  <span className="text-gray-600 dark:text-gray-400 text-sm">To: </span>
                  <span className="text-gray-900 dark:text-white text-sm">{selectedMessage.to}</span>
                </div>
              </div>

              <div className="prose dark:prose-invert max-w-none">
                <p className="whitespace-pre-wrap">{selectedMessage.content}</p>
              </div>

              {selectedMessage.metadata && (
                <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2">
                    Metadata
                  </h3>
                  <pre className="text-xs text-gray-600 dark:text-gray-300">
                    {JSON.stringify(selectedMessage.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              Select a message to view details
            </div>
          )}
        </div>
      </div>

      {/* Compose Modal */}
      {composeOpen && (
        <ComposeModal
          agents={agents}
          onSend={(message) => sendMessageMutation.mutate(message)}
          onClose={() => setComposeOpen(false)}
        />
      )}
    </div>
  );
};

// Compose Modal Component
const ComposeModal: React.FC<{
  agents: Agent[];
  onSend: (message: Partial<Message>) => void;
  onClose: () => void;
}> = ({ agents, onSend, onClose }) => {
  const [message, setMessage] = useState<Partial<Message>>({
    to: '',
    subject: '',
    content: '',
    priority: 'normal',
    type: 'task',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSend({
      ...message,
      from: 'UI',
      timestamp: new Date().toISOString(),
      status: 'unread',
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-2xl mx-4">
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Compose Message
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                To
              </label>
              <select
                value={message.to}
                onChange={(e) => setMessage({ ...message, to: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700"
                required
              >
                <option value="">Select recipient</option>
                {agents.map((agent) => (
                  <option key={agent.id} value={agent.id}>
                    {agent.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex space-x-4">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Type
                </label>
                <select
                  value={message.type}
                  onChange={(e) => setMessage({ ...message, type: e.target.value as any })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700"
                >
                  <option value="task">Task</option>
                  <option value="notification">Notification</option>
                  <option value="error">Error</option>
                  <option value="success">Success</option>
                </select>
              </div>

              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Priority
                </label>
                <select
                  value={message.priority}
                  onChange={(e) => setMessage({ ...message, priority: e.target.value as any })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700"
                >
                  <option value="low">Low</option>
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Subject
              </label>
              <input
                type="text"
                value={message.subject}
                onChange={(e) => setMessage({ ...message, subject: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Message
              </label>
              <textarea
                value={message.content}
                onChange={(e) => setMessage({ ...message, content: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700"
                rows={6}
                required
              />
            </div>
          </div>

          <div className="flex justify-end space-x-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Send Message
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Generate mock messages for testing
const generateMockMessages = (): Message[] => {
  return [
    {
      id: '1',
      from: 'Supervisor',
      to: 'Backend API',
      subject: 'Implement Authentication Endpoints',
      content: 'Please implement the following authentication endpoints:\n- POST /api/auth/login\n- POST /api/auth/logout\n- POST /api/auth/refresh\n\nUse JWT tokens and ensure proper security measures are in place.',
      priority: 'high',
      status: 'unread',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      type: 'task',
      metadata: { deadline: '2025-09-20', assignee: 'backend-api' }
    },
    {
      id: '2',
      from: 'Testing Agent',
      to: 'Frontend UI',
      subject: 'Test Results: Component Tests Failed',
      content: '3 component tests failed in the latest test run:\n- UserProfile.test.tsx\n- Navigation.test.tsx\n- DataTable.test.tsx\n\nPlease review and fix the failing tests.',
      priority: 'urgent',
      status: 'unread',
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      type: 'error',
      metadata: { testRun: 'TR-2025-001', failedTests: 3 }
    },
    {
      id: '3',
      from: 'Database Agent',
      to: 'Supervisor',
      subject: 'Database Migration Completed',
      content: 'Successfully completed database migration v2.1.0.\n\nChanges applied:\n- Added user_preferences table\n- Updated indexes on products table\n- Added foreign key constraints',
      priority: 'normal',
      status: 'read',
      timestamp: new Date(Date.now() - 10800000).toISOString(),
      type: 'success',
      metadata: { version: '2.1.0', duration: '45s' }
    },
    {
      id: '4',
      from: 'Master Agent',
      to: 'All Agents',
      subject: 'System Maintenance Scheduled',
      content: 'System maintenance is scheduled for this weekend.\n\nDate: September 21, 2025\nTime: 2:00 AM - 6:00 AM EST\n\nAll services will be temporarily unavailable during this window.',
      priority: 'high',
      status: 'read',
      timestamp: new Date(Date.now() - 86400000).toISOString(),
      type: 'notification',
      metadata: { broadcast: true, maintenanceWindow: '4 hours' }
    },
    {
      id: '5',
      from: 'Queue Manager',
      to: 'Supervisor',
      subject: 'Queue Processing Alert',
      content: 'Queue backlog detected. Current queue size: 1,234 messages.\n\nAverage processing time has increased to 3.5 seconds per message.',
      priority: 'high',
      status: 'unread',
      timestamp: new Date(Date.now() - 1800000).toISOString(),
      type: 'notification',
      metadata: { queueSize: 1234, avgProcessingTime: 3.5 }
    }
  ];
};

export default InboxSystem;