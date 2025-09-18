import React, { createContext, useContext, useReducer, useEffect, type ReactNode } from 'react';
import axios from 'axios';
import { config } from '../config';

// Configure axios defaults
// Remove baseURL to use Vite proxy
// axios.defaults.baseURL = config.API_URL;

// Add request/response interceptors for debugging
axios.interceptors.request.use(
  (request) => {
    console.log('Starting Request:', request.url, request);
    return request;
  },
  (error) => {
    console.error('Request Error:', error);
    return Promise.reject(error);
  }
);

axios.interceptors.response.use(
  (response) => {
    console.log('Response:', response.config.url, response.status);
    return response;
  },
  (error) => {
    console.error('Response Error:', error.config?.url, error.message);
    return Promise.reject(error);
  }
);

// Types
interface Agent {
  id: string;
  name: string;
  type: string;
  status: 'online' | 'offline' | 'busy';
  sessionId: string;
  lastActivity: string;
}

interface SystemHealth {
  status: string;
  message: string;
  components: Record<string, any>;
  summary: {
    healthy: number;
    degraded: number;
    unhealthy: number;
    total: number;
  };
}

interface QueueStatus {
  total: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  avgProcessingTime: number;
}

interface Log {
  id: string;
  timestamp: string;
  level: string;
  agent: string;
  message: string;
  details?: Record<string, any>;
}

interface Message {
  id: string;
  timestamp: string;
  from: string;
  to: string;
  type: string;
  status: string;
  subject: string;
  content: string;
  priority: string;
}

interface Task {
  id: string;
  timestamp: string;
  agent: string;
  command: string;
  status: string;
  priority: string;
  params?: Record<string, any>;
}

interface AppState {
  // Core Data
  agents: Agent[];
  systemHealth: SystemHealth | null;
  queueStatus: QueueStatus | null;
  logs: Log[];
  messages: Message[];
  tasks: Task[];

  // UI State
  activeView: 'workflow' | 'operations' | 'monitoring';
  selectedAgent: Agent | null;
  sidebarCollapsed: boolean;
  workflowMode: 'view' | 'edit'; // Per switchare tra visualizzazione e builder

  // Loading & Errors
  loading: boolean;
  error: string | null;
  notifications: Notification[];

  // WebSocket
  wsConnected: boolean;
  wsReconnectAttempts: number;
}

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
  timestamp: number;
  autoClose?: boolean;
}

// Action Types
type Action =
  | { type: 'SET_AGENTS'; payload: Agent[] }
  | { type: 'UPDATE_AGENT'; payload: Agent }
  | { type: 'SET_SYSTEM_HEALTH'; payload: SystemHealth }
  | { type: 'SET_QUEUE_STATUS'; payload: QueueStatus }
  | { type: 'SET_LOGS'; payload: Log[] }
  | { type: 'SET_MESSAGES'; payload: Message[] }
  | { type: 'SET_TASKS'; payload: Task[] }
  | { type: 'ADD_LOG'; payload: Log }
  | { type: 'ADD_MESSAGE'; payload: Message }
  | { type: 'ADD_TASK'; payload: Task }
  | { type: 'SET_ACTIVE_VIEW'; payload: AppState['activeView'] }
  | { type: 'SET_SELECTED_AGENT'; payload: Agent | null }
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'SET_WORKFLOW_MODE'; payload: 'view' | 'edit' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'ADD_NOTIFICATION'; payload: Notification }
  | { type: 'REMOVE_NOTIFICATION'; payload: string }
  | { type: 'SET_WS_CONNECTED'; payload: boolean }
  | { type: 'INCREMENT_WS_RECONNECT' }
  | { type: 'RESET_WS_RECONNECT' };

// Initial State
const initialState: AppState = {
  agents: [],
  systemHealth: null,
  queueStatus: null,
  logs: [],
  messages: [],
  tasks: [],
  activeView: 'workflow',
  selectedAgent: null,
  sidebarCollapsed: false,
  workflowMode: 'view',
  loading: false,
  error: null,
  notifications: [],
  wsConnected: false,
  wsReconnectAttempts: 0
};

// Reducer
function appReducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_AGENTS':
      return { ...state, agents: action.payload };

    case 'UPDATE_AGENT':
      return {
        ...state,
        agents: state.agents.map(a =>
          a.id === action.payload.id ? action.payload : a
        )
      };

    case 'SET_SYSTEM_HEALTH':
      return { ...state, systemHealth: action.payload };

    case 'SET_QUEUE_STATUS':
      return { ...state, queueStatus: action.payload };

    case 'SET_LOGS':
      return { ...state, logs: action.payload };

    case 'SET_MESSAGES':
      return { ...state, messages: action.payload };

    case 'SET_TASKS':
      return { ...state, tasks: action.payload };

    case 'ADD_LOG':
      return { ...state, logs: [action.payload, ...state.logs.slice(0, 99)] }; // Keep last 100 logs

    case 'ADD_MESSAGE':
      return { ...state, messages: [action.payload, ...state.messages.slice(0, 49)] }; // Keep last 50 messages

    case 'ADD_TASK':
      return { ...state, tasks: [action.payload, ...state.tasks.slice(0, 99)] }; // Keep last 100 tasks

    case 'SET_ACTIVE_VIEW':
      return { ...state, activeView: action.payload };

    case 'SET_SELECTED_AGENT':
      return { ...state, selectedAgent: action.payload };

    case 'TOGGLE_SIDEBAR':
      return { ...state, sidebarCollapsed: !state.sidebarCollapsed };

    case 'SET_WORKFLOW_MODE':
      return { ...state, workflowMode: action.payload };

    case 'SET_LOADING':
      return { ...state, loading: action.payload };

    case 'SET_ERROR':
      return { ...state, error: action.payload };

    case 'ADD_NOTIFICATION':
      return {
        ...state,
        notifications: [...state.notifications, action.payload]
      };

    case 'REMOVE_NOTIFICATION':
      return {
        ...state,
        notifications: state.notifications.filter(n => n.id !== action.payload)
      };

    case 'SET_WS_CONNECTED':
      return { ...state, wsConnected: action.payload };

    case 'INCREMENT_WS_RECONNECT':
      return { ...state, wsReconnectAttempts: state.wsReconnectAttempts + 1 };

    case 'RESET_WS_RECONNECT':
      return { ...state, wsReconnectAttempts: 0 };

    default:
      return state;
  }
}

// Context
interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<Action>;

  // Helper methods
  fetchAgents: () => Promise<void>;
  fetchSystemHealth: () => Promise<void>;
  fetchQueueStatus: () => Promise<void>;
  fetchLogs: (agent?: string) => Promise<void>;
  fetchMessages: (agent?: string) => Promise<void>;
  fetchTasks: (agent?: string) => Promise<void>;
  refreshAll: () => Promise<void>;

  // Notification helpers
  notify: (type: Notification['type'], message: string, autoClose?: boolean) => void;
  clearNotifications: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// Provider Component
interface AppProviderProps {
  children: ReactNode;
}

export function AppProvider({ children }: AppProviderProps) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Helper: Add notification
  const notify = (type: Notification['type'], message: string, autoClose = true) => {
    const notification: Notification = {
      id: `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      message,
      timestamp: Date.now(),
      autoClose
    };

    dispatch({ type: 'ADD_NOTIFICATION', payload: notification });

    if (autoClose) {
      setTimeout(() => {
        dispatch({ type: 'REMOVE_NOTIFICATION', payload: notification.id });
      }, 5000);
    }
  };

  // Clear all notifications
  const clearNotifications = () => {
    state.notifications.forEach(n => {
      dispatch({ type: 'REMOVE_NOTIFICATION', payload: n.id });
    });
  };

  // Fetch agents
  const fetchAgents = async () => {
    try {
      console.log('Fetching agents...');
      const response = await axios.get('/api/agents', { timeout: 15000 });
      console.log('Agents response:', response.data);
      // Transform the API response to match our Agent interface
      const agentsData = response.data || [];
      const transformedAgents: Agent[] = agentsData.map((agent: any) => ({
        id: agent.id,
        name: agent.name,
        type: agent.type,
        status: agent.status === 'online' ? 'online' :
                agent.status === 'busy' ? 'busy' : 'offline',
        sessionId: agent.sessionId || '',
        lastActivity: agent.lastActivity || new Date().toISOString()
      }));
      dispatch({ type: 'SET_AGENTS', payload: transformedAgents });
      console.log('Agents fetch complete');
    } catch (error: any) {
      console.error('Failed to fetch agents:', error);
      notify('error', 'Failed to fetch agents');
      dispatch({ type: 'SET_AGENTS', payload: [] });
    }
  };

  // Fetch system health
  const fetchSystemHealth = async () => {
    try {
      console.log('Fetching system health...');
      const response = await axios.get('/api/system/health', { timeout: 15000 });
      // Transform the API response to match our SystemHealth interface
      const healthData = {
        status: response.data.status === 'healthy' ? 'healthy' : 'degraded',
        message: response.data.status === 'healthy' ? 'All systems operational' : 'Some issues detected',
        components: response.data.components,
        summary: {
          healthy: 0,
          degraded: 0,
          unhealthy: 0,
          total: 0
        }
      };

      // Calculate summary from agents
      if (response.data.components?.agents) {
        const agents = Object.values(response.data.components.agents) as any[];
        healthData.summary.total = agents.length;
        agents.forEach((agent: any) => {
          if (agent.status === 'ready') healthData.summary.healthy++;
          else if (agent.status === 'stopped') healthData.summary.unhealthy++;
          else healthData.summary.degraded++;
        });
      }

      dispatch({ type: 'SET_SYSTEM_HEALTH', payload: healthData });
      console.log('System health fetch complete');
    } catch (error: any) {
      console.error('Failed to fetch system health:', error);
      notify('error', 'Failed to fetch system health');
    }
  };

  // Fetch queue status
  const fetchQueueStatus = async () => {
    try {
      console.log('Fetching queue status...');
      const response = await axios.get('/api/system/status', { timeout: 15000 });
      // Transform the API response to match our QueueStatus interface
      const queueData = {
        total: response.data.queue?.pending_tasks || 0,
        pending: response.data.queue?.pending_tasks || 0,
        processing: 0, // Not provided by current API
        completed: 0,  // Not provided by current API
        failed: 0,     // Not provided by current API
        avgProcessingTime: 0 // Not provided by current API
      };
      dispatch({ type: 'SET_QUEUE_STATUS', payload: queueData });
      console.log('Queue status fetch complete');
    } catch (error: any) {
      console.error('Failed to fetch queue status:', error);
      notify('error', 'Failed to fetch queue status');
    }
  };

  // Fetch logs
  const fetchLogs = async (agent?: string) => {
    try {
      console.log('Fetching logs...');
      const params = agent ? `?agent=${agent}` : '';
      const response = await axios.get(`/api/logs${params}`, { timeout: 15000 });
      dispatch({ type: 'SET_LOGS', payload: response.data.logs || [] });
      console.log('Logs fetch complete');
    } catch (error: any) {
      console.error('Failed to fetch logs:', error);
      notify('error', 'Failed to fetch logs');
    }
  };

  // Fetch messages
  const fetchMessages = async (agent?: string) => {
    try {
      console.log('Fetching messages...');
      const params = agent ? `?agent=${agent}` : '';
      const response = await axios.get(`/api/messages${params}`, { timeout: 15000 });
      dispatch({ type: 'SET_MESSAGES', payload: response.data.messages || [] });
      console.log('Messages fetch complete');
    } catch (error: any) {
      console.error('Failed to fetch messages:', error);
      notify('error', 'Failed to fetch messages');
    }
  };

  // Fetch tasks
  const fetchTasks = async (agent?: string) => {
    try {
      console.log('Fetching tasks...');
      const params = agent ? `?agent=${agent}` : '';
      const response = await axios.get(`/api/tasks/pending${params}`, { timeout: 15000 });
      // Transform the API response to match our Task interface
      const tasks = response.data.tasks || [];
      dispatch({ type: 'SET_TASKS', payload: tasks });
      console.log('Tasks fetch complete');
    } catch (error: any) {
      console.error('Failed to fetch tasks:', error);
      // Set empty array if there's an error
      dispatch({ type: 'SET_TASKS', payload: [] });
      // Don't throw the error, just log it
    }
  };

  // Refresh all data
  const refreshAll = async () => {
    console.log('Starting refreshAll...');
    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      // Use Promise.allSettled to handle individual errors without blocking
      const results = await Promise.allSettled([
        fetchAgents(),
        fetchSystemHealth(),
        fetchQueueStatus(),
        fetchLogs(),
        fetchMessages(),
        fetchTasks()
      ]);

      // Log any failures for debugging
      let hasErrors = false;
      results.forEach((result, index) => {
        if (result.status === 'rejected') {
          hasErrors = true;
          const names = ['agents', 'health', 'queue', 'logs', 'messages', 'tasks'];
          console.warn(`Failed to fetch ${names[index]}:`, result.reason?.message || result.reason);
        }
      });

      // Only set error if all requests failed
      const allFailed = results.every(r => r.status === 'rejected');
      if (allFailed) {
        dispatch({ type: 'SET_ERROR', payload: 'Unable to connect to API' });
      } else {
        dispatch({ type: 'SET_ERROR', payload: null });
      }
    } catch (error: any) {
      console.error('RefreshAll unexpected error:', error);
      dispatch({ type: 'SET_ERROR', payload: error.message });
    } finally {
      console.log('RefreshAll complete');
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  // WebSocket message handler
  useEffect(() => {
    // WebSocket handlers are commented out for now
    // TODO: Implement WebSocket integration when backend is ready
  }, [state.wsReconnectAttempts]);

  // Initial data fetch and polling
  useEffect(() => {
    // Initial fetch after a small delay to ensure everything is mounted
    const initialTimer = setTimeout(() => {
      refreshAll();
    }, 100);

    // Set up polling with a fixed interval
    const pollInterval = 30000; // Poll every 30 seconds
    const interval = setInterval(refreshAll, pollInterval);

    return () => {
      clearTimeout(initialTimer);
      clearInterval(interval);
    };
  }, []); // Only run once on mount

  const contextValue: AppContextType = {
    state,
    dispatch,
    fetchAgents,
    fetchSystemHealth,
    fetchQueueStatus,
    fetchLogs,
    fetchMessages,
    fetchTasks,
    refreshAll,
    notify,
    clearNotifications
  };

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
}

// Custom hook
export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
}

// Export types
export type { Agent, SystemHealth, QueueStatus, Log, Message, Task, Notification, AppState };