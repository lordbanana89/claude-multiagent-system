// MCP v2 Client Service
// Complete JSON-RPC 2.0 implementation with WebSocket support

import type {
  MCPRequest,
  MCPResponse,
  MCPServerStatus,
  MCPTool,
  MCPResource,
  MCPPrompt,
  MCPActivity,
  MCPAgentState,
  MCPToolExecution,
  MCPToolResult,
  MCPWebSocketMessage,
  MCPErrorCode,
} from './mcpTypes';

class MCPClient {
  private baseUrl: string;
  private wsUrl: string;
  private ws: WebSocket | null = null;
  private requestId: number = 1;
  private pendingRequests: Map<number | string, (response: MCPResponse) => void> = new Map();
  private wsListeners: Map<string, Set<(data: any) => void>> = new Map();
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 10;
  private reconnectTimeout: NodeJS.Timeout | null = null;

  constructor() {
    this.baseUrl = import.meta.env.VITE_MCP_API_URL || 'http://localhost:8099';
    this.wsUrl = import.meta.env.VITE_MCP_WS_URL || 'ws://localhost:8100';
    this.connectWebSocket();
  }

  // Core JSON-RPC method
  private async jsonRpcCall<T = any>(method: string, params?: any): Promise<T> {
    const request: MCPRequest = {
      jsonrpc: '2.0',
      method,
      params: params || {},
      id: this.requestId++,
    };

    const response = await fetch(`${this.baseUrl}/jsonrpc`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: MCPResponse<T> = await response.json();

    if (data.error) {
      throw new Error(`MCP Error: ${data.error.message} (${data.error.code})`);
    }

    return data.result as T;
  }

  // WebSocket Connection Management
  private connectWebSocket() {
    try {
      this.ws = new WebSocket(this.wsUrl);

      this.ws.onopen = () => {
        console.log('MCP WebSocket connected');
        this.reconnectAttempts = 0;
        this.emit('connection', { connected: true });
      };

      this.ws.onmessage = (event) => {
        try {
          const message: MCPWebSocketMessage = JSON.parse(event.data);
          this.handleWebSocketMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.emit('error', error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.emit('connection', { connected: false });
        this.attemptReconnect();
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      this.attemptReconnect();
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);

    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimeout = setTimeout(() => {
      this.connectWebSocket();
    }, delay);
  }

  private handleWebSocketMessage(message: MCPWebSocketMessage) {
    this.emit(message.type, message.data);
    this.emit('message', message);
  }

  // Event Emitter Pattern
  private emit(event: string, data: any) {
    const listeners = this.wsListeners.get(event);
    if (listeners) {
      listeners.forEach(listener => listener(data));
    }
  }

  public on(event: string, callback: (data: any) => void) {
    if (!this.wsListeners.has(event)) {
      this.wsListeners.set(event, new Set());
    }
    this.wsListeners.get(event)!.add(callback);

    // Return unsubscribe function
    return () => {
      const listeners = this.wsListeners.get(event);
      if (listeners) {
        listeners.delete(callback);
      }
    };
  }

  // Public API Methods

  async getStatus(): Promise<MCPServerStatus> {
    const response = await fetch(`${this.baseUrl}/api/mcp/status`);
    if (!response.ok) {
      throw new Error('Failed to fetch MCP status');
    }
    return response.json();
  }

  async initialize(clientInfo?: any): Promise<any> {
    return this.jsonRpcCall('initialize', { clientInfo });
  }

  async listTools(): Promise<MCPTool[]> {
    return this.jsonRpcCall('tools/list');
  }

  async callTool(execution: MCPToolExecution): Promise<MCPToolResult> {
    return this.jsonRpcCall('tools/call', execution);
  }

  async listResources(): Promise<MCPResource[]> {
    return this.jsonRpcCall('resources/list');
  }

  async readResource(uri: string): Promise<any> {
    return this.jsonRpcCall('resources/read', { uri });
  }

  async listPrompts(): Promise<MCPPrompt[]> {
    return this.jsonRpcCall('prompts/list');
  }

  async executePrompt(name: string, args?: Record<string, any>): Promise<string> {
    return this.jsonRpcCall('prompts/execute', { name, arguments: args });
  }

  async getActivities(limit: number = 100, offset: number = 0): Promise<MCPActivity[]> {
    const response = await fetch(
      `${this.baseUrl}/api/mcp/activities?limit=${limit}&offset=${offset}`
    );
    if (!response.ok) {
      throw new Error('Failed to fetch activities');
    }
    const data = await response.json();
    // Handle both formats: { activities: [] } or direct array
    return data.activities || data || [];
  }

  async getAgentStates(): Promise<MCPAgentState[]> {
    const response = await fetch(`${this.baseUrl}/api/mcp/agent-states`);
    if (!response.ok) {
      throw new Error('Failed to fetch agent states');
    }
    const data = await response.json();
    // Convert object to array if needed
    if (Array.isArray(data)) {
      return data;
    } else if (typeof data === 'object') {
      // Convert object format to array format
      return Object.entries(data).map(([agentId, state]: [string, any]) => ({
        agent_id: agentId,
        ...state
      }));
    }
    return [];
  }

  async updateAgentState(agentId: string, state: Partial<MCPAgentState>): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/mcp/agent-states/${agentId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(state),
    });

    if (!response.ok) {
      throw new Error('Failed to update agent state');
    }
  }

  // Batch Operations
  async batchCall(methods: Array<{ method: string; params?: any }>): Promise<any[]> {
    const requests = methods.map((m, i) => ({
      jsonrpc: '2.0' as const,
      method: m.method,
      params: m.params || {},
      id: `batch-${i}`,
    }));

    const response = await fetch(`${this.baseUrl}/jsonrpc`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requests),
    });

    if (!response.ok) {
      throw new Error(`Batch call failed: ${response.status}`);
    }

    const responses: MCPResponse[] = await response.json();
    return responses.map(r => {
      if (r.error) {
        throw new Error(`Method failed: ${r.error.message}`);
      }
      return r.result;
    });
  }

  // Utility Methods
  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.wsListeners.clear();
    this.pendingRequests.clear();
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
let mcpClientInstance: MCPClient | null = null;

export const getMCPClient = (): MCPClient => {
  if (!mcpClientInstance) {
    mcpClientInstance = new MCPClient();
  }
  return mcpClientInstance;
};

export default MCPClient;