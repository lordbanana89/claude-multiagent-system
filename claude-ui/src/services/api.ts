/**
 * Centralized API configuration for all frontend services
 * Maps endpoints to the correct backend services
 */

import axios from 'axios';

// Backend service URLs
const MAIN_API_URL = 'http://localhost:5001';  // routes_api.py
const GATEWAY_API_URL = 'http://localhost:8888';  // api/main.py

// Create axios instances for each service
export const mainApi = axios.create({
  baseURL: MAIN_API_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const gatewayApi = axios.create({
  baseURL: GATEWAY_API_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// API Endpoints mapping
export const API_ENDPOINTS = {
  // Main API (routes_api.py - port 5001)
  agents: {
    list: () => mainApi.get('/api/agents'),
    get: (id: string) => mainApi.get(`/api/agents/${id}`),
    command: (id: string, data: any) => mainApi.post(`/api/agents/${id}/command`, data)
  },

  tasks: {
    list: () => mainApi.get('/api/tasks'),
    get: (id: string) => mainApi.get(`/api/tasks/${id}`),
    create: (data: any) => mainApi.post('/api/tasks', data),
    update: (id: string, data: any) => mainApi.put(`/api/tasks/${id}`, data)
  },

  messages: {
    list: (params?: any) => mainApi.get('/api/messages', { params }),
    send: (data: any) => mainApi.post('/api/messages', data),
    markRead: (id: string) => mainApi.patch(`/api/messages/${id}/read`)
  },

  system: {
    status: () => mainApi.get('/api/system/status'),
    metrics: () => mainApi.get('/api/system/metrics')
  },

  mcp: {
    status: () => mainApi.get('/api/mcp/status'),
    startAgent: (data: any) => mainApi.post('/api/mcp/start-agent', data),
    stopAgent: (data: any) => mainApi.post('/api/mcp/stop-agent', data),
    activities: (limit = 50) => mainApi.get(`/api/mcp/activities?limit=${limit}`)
  },

  auth: {
    login: (data: any) => mainApi.post('/api/auth/login', data),
    verify: () => mainApi.get('/api/auth/verify'),
    logout: () => mainApi.post('/api/auth/logout')
  },

  // Gateway API (api/main.py - port 8888)
  health: () => gatewayApi.get('/api/system/health'),

  workflows: {
    list: () => gatewayApi.get('/api/workflows'),
    get: (id: string) => gatewayApi.get(`/api/workflows/${id}`),
    create: (data: any) => gatewayApi.post('/api/workflows', data),
    execute: (id: string, data: any) => gatewayApi.post(`/api/workflows/${id}/execute`, data)
  },

  queue: {
    tasks: () => gatewayApi.get('/api/queue/tasks'),
    stats: () => gatewayApi.get('/api/queue/stats'),
    retry: (taskId: string) => gatewayApi.post(`/api/queue/tasks/${taskId}/retry`),
    cancel: (taskId: string) => gatewayApi.delete(`/api/queue/tasks/${taskId}`),
    clearCompleted: () => gatewayApi.post('/api/queue/clear-completed')
  },

  inbox: {
    messages: (params?: any) => gatewayApi.get('/api/inbox/messages', { params }),
    create: (data: any) => gatewayApi.post('/api/inbox/messages', data),
    markRead: (id: string) => gatewayApi.patch(`/api/inbox/messages/${id}/read`),
    archive: (id: string) => gatewayApi.patch(`/api/inbox/messages/${id}/archive`)
  },

  terminal: {
    start: (agentId: string) => gatewayApi.post(`/api/agents/${agentId}/terminal/start`),
    stop: (agentId: string) => gatewayApi.post(`/api/agents/${agentId}/terminal/stop`),
    status: (agentId: string) => gatewayApi.get(`/api/agents/${agentId}/terminal/status`),
    command: (agentId: string, data: any) => gatewayApi.post(`/api/agents/${agentId}/terminal/command`, data),
    output: (agentId: string) => gatewayApi.get(`/api/agents/${agentId}/terminal/output`)
  },

  logs: (params?: any) => gatewayApi.get('/api/logs', { params }),

  documents: {
    list: () => gatewayApi.get('/api/documents'),
    update: (id: string, data: any) => gatewayApi.put(`/api/documents/${id}`, data),
    create: (data: any) => gatewayApi.post('/api/documents', data)
  },

  langgraph: {
    execute: (data: any) => gatewayApi.post('/api/langgraph/execute', data)
  }
};

// Add request interceptor for authentication
mainApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

gatewayApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor for error handling
const handleResponseError = (error: any) => {
  if (error.response?.status === 401) {
    // Handle unauthorized
    localStorage.removeItem('auth_token');
    window.location.href = '/login';
  }
  return Promise.reject(error);
};

mainApi.interceptors.response.use(
  (response) => response,
  handleResponseError
);

gatewayApi.interceptors.response.use(
  (response) => response,
  handleResponseError
);

// Export for direct use
export default API_ENDPOINTS;