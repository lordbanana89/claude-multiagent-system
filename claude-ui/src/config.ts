// Configuration file for the application
export const config = {
  // API Configuration
  API_URL: import.meta.env.VITE_API_URL || 'http://localhost:8888',
  WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8888',

  // WebSocket settings
  WS_RECONNECT_DELAY: 5000,
  WS_MAX_RECONNECT_ATTEMPTS: 10,
  RECONNECT_INTERVAL: 5000,
  MAX_RECONNECT_ATTEMPTS: 10,

  // Polling intervals
  POLL_INTERVAL: 10000,
  POLL_INTERVAL_WS_CONNECTED: 30000,

  // UI settings
  NOTIFICATION_AUTO_CLOSE_DELAY: 5000,
  MAX_NOTIFICATIONS: 10,

  // Development settings
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
};

// Terminal configuration
export function getTerminalUrl(agentId: string): string {
  const terminalPorts: Record<string, number> = {
    'master': 3001,
    'supervisor': 3002,
    'backend-api': 3003,
    'database': 3004,
    'frontend-ui': 3005,
    'testing': 3006,
    'instagram': 3007,
    'queue-manager': 3008,
    'deployment': 3009,
  };

  const port = terminalPorts[agentId] || 3001;
  return `http://localhost:${port}/terminal`;
}

export default config;