// Application Configuration
export const config = {
  // API Configuration
  API_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',

  // MCP Configuration
  MCP_API_URL: import.meta.env.VITE_MCP_API_URL || 'http://localhost:8099',
  MCP_WEBSOCKET_URL: import.meta.env.VITE_MCP_WS_URL || 'ws://localhost:8089/ws',

  // Inbox Configuration
  INBOX_API_URL: import.meta.env.VITE_INBOX_API_URL || 'http://localhost:8098',
  INBOX_WEBSOCKET_URL: import.meta.env.VITE_INBOX_WS_URL || 'ws://localhost:8098/ws',

  // Terminal Port Mapping (corrected for actual ttyd services)
  TERMINAL_PORTS: {
    'backend-api': 8090,
    'database': 8091,
    'frontend-ui': 8092,
    'testing': 8093,
    'instagram': 8094,
    'supervisor': 8095,
    'master': 8096,
    'deployment': 8098,
    'queue-manager': 8097,
  } as const,

  // Terminal Configuration
  TERMINAL_BASE_URL: 'http://localhost',

  // Feature Flags
  FEATURES: {
    WEBSOCKET: import.meta.env.VITE_ENABLE_WEBSOCKET !== 'false',
    TERMINALS: import.meta.env.VITE_ENABLE_TERMINALS !== 'false',
  },

  // System Configuration
  REFRESH_INTERVAL: 5000, // ms
  MAX_RECONNECT_ATTEMPTS: 10,
  RECONNECT_INTERVAL: 5000, // ms

  // UI Configuration
  MAX_NOTIFICATIONS: 10,
  NOTIFICATION_TIMEOUT: 5000, // ms

  // Agent Configuration
  AGENT_TYPES: {
    master: { name: 'Master Agent', icon: '🎖️', color: '#f59e0b' },
    supervisor: { name: 'Supervisor', icon: '👨‍💼', color: '#3b82f6' },
    'backend-api': { name: 'Backend API', icon: '⚙️', color: '#10b981' },
    database: { name: 'Database', icon: '🗄️', color: '#8b5cf6' },
    'frontend-ui': { name: 'Frontend UI', icon: '🎨', color: '#ec4899' },
    testing: { name: 'Testing', icon: '🧪', color: '#06b6d4' },
    instagram: { name: 'Instagram', icon: '📷', color: '#f43f5e' },
    'queue-manager': { name: 'Queue Manager', icon: '📋', color: '#84cc16' },
    deployment: { name: 'Deployment', icon: '🚀', color: '#eab308' },
  } as const,

  // Task Status Configuration
  TASK_STATUS: {
    pending: { label: 'Pending', color: '#fbbf24', bgColor: '#fef3c7' },
    processing: { label: 'Processing', color: '#3b82f6', bgColor: '#dbeafe' },
    completed: { label: 'Completed', color: '#10b981', bgColor: '#d1fae5' },
    failed: { label: 'Failed', color: '#ef4444', bgColor: '#fee2e2' },
  } as const,
};

// Type exports
export type AgentId = keyof typeof config.AGENT_TYPES;
export type TaskStatus = keyof typeof config.TASK_STATUS;

// Helper functions
export const getTerminalUrl = (agentId: AgentId): string => {
  const port = config.TERMINAL_PORTS[agentId];
  return port ? `${config.TERMINAL_BASE_URL}:${port}` : '';
};

export const getAgentConfig = (agentId: string) => {
  return config.AGENT_TYPES[agentId as AgentId] || {
    name: agentId,
    icon: '🤖',
    color: '#6b7280',
  };
};

export const getTaskStatusConfig = (status: string) => {
  return config.TASK_STATUS[status as TaskStatus] || {
    label: status,
    color: '#6b7280',
    bgColor: '#f3f4f6',
  };
};