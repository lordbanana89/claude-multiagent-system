import { config } from '../config';

class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectInterval: number = config.RECONNECT_INTERVAL;
  private maxReconnectAttempts: number = config.MAX_RECONNECT_ATTEMPTS;
  private reconnectAttempts: number = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private pingInterval: NodeJS.Timeout | null = null;
  private url: string;
  private messageHandlers: ((message: any) => void)[] = [];
  private connectionHandlers: ((connected: boolean) => void)[] = [];

  constructor(url: string = config.WS_URL) {
    this.url = url;
  }

  // Add event listener methods
  on(event: 'message', handler: (message: any) => void): void;
  on(event: 'connect' | 'disconnect', handler: () => void): void;
  on(event: 'reconnect', handler: () => void): void;
  on(event: string, handler: (...args: any[]) => void): void {
    if (event === 'message') {
      this.messageHandlers.push(handler);
    } else if (event === 'connect' || event === 'disconnect' || event === 'reconnect') {
      // Store handlers for connection events
    }
  }

  off(event: 'message', handler: (message: any) => void): void;
  off(event: 'connect' | 'disconnect' | 'reconnect', handler: () => void): void;
  off(event: string, handler: (...args: any[]) => void): void {
    if (event === 'message') {
      this.messageHandlers = this.messageHandlers.filter(h => h !== handler);
    }
  }

  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.connectionHandlers.forEach(handler => handler(true));
        this.reconnectAttempts = 0;

        // Start ping interval to keep connection alive
        this.startPingInterval();
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          // Handle ping/pong
          if (message.type === 'pong') {
            return;
          }

          // Notify all message handlers
          this.messageHandlers.forEach(handler => handler(message));
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.connectionHandlers.forEach(handler => handler(false));

        // Clean up ping interval
        this.stopPingInterval();

        // Attempt to reconnect
        this.scheduleReconnect();
      };

    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.scheduleReconnect();
    }
  }

  private startPingInterval() {
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' });
      }
    }, 30000); // Ping every 30 seconds
  }

  private stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectInterval * this.reconnectAttempts, 30000);

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  // Send task execution request
  executeTask(task: { name: string; description: string; agentId?: string }) {
    this.send({
      type: 'execute_task',
      data: task
    });
  }

  // Send task assignment
  assignTask(taskId: string, agentId: string) {
    this.send({
      type: 'assign_task',
      data: {
        taskId,
        agentId
      }
    });
  }

  // Request full state sync
  requestSync() {
    // Don't try to sync if not connected
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.send({
        type: 'sync_request'
      });
    } else {
      console.log('WebSocket not ready, skipping sync request');
    }
  }

  disconnect() {
    this.stopPingInterval();

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.connectionHandlers.forEach(handler => handler(false));
  }

  getState(): 'connecting' | 'connected' | 'disconnected' {
    if (!this.ws) return 'disconnected';

    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      default:
        return 'disconnected';
    }
  }
}

// Create singleton instance
const wsManager = new WebSocketManager();

// Auto-connect on import
if (typeof window !== 'undefined') {
  wsManager.connect();

  // Handle page visibility changes
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      // Page is hidden, we might want to reduce activity
      console.log('Page hidden, maintaining minimal connection');
    } else {
      // Page is visible again, ensure connection
      if (wsManager.getState() === 'disconnected') {
        wsManager.connect();
      }
    }
  });

  // Clean up on page unload
  window.addEventListener('beforeunload', () => {
    wsManager.disconnect();
  });
}

export default wsManager;