// MCP v2 TypeScript Type Definitions
// Protocol: 2025-06-18

export interface MCPRequest {
  jsonrpc: '2.0';
  method: string;
  params?: any;
  id: number | string;
}

export interface MCPResponse<T = any> {
  jsonrpc: '2.0';
  result?: T;
  error?: MCPError;
  id: number | string;
}

export interface MCPError {
  code: number;
  message: string;
  data?: any;
}

export interface MCPCapabilities {
  protocol_version: string;
  supports: string[];
  features: {
    idempotency: boolean;
    dry_run: boolean;
    streaming: boolean;
    batch_requests: boolean;
  };
}

export interface MCPTool {
  name: string;
  description: string;
  inputSchema?: any;
  outputSchema?: any;
  category?: string;
  dangerous?: boolean;
}

export interface MCPResource {
  uri: string;
  name: string;
  description?: string;
  mimeType?: string;
  schema?: string;
  metadata?: Record<string, any>;
}

export interface MCPPrompt {
  name: string;
  description?: string;
  arguments?: Array<{
    name: string;
    description?: string;
    required?: boolean;
    default?: any;
  }>;
  template: string;
}

export interface MCPActivity {
  id: string;
  timestamp: string;
  agent: string;
  action: string;
  category?: string;
  type?: string;
  details?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface MCPAgentState {
  agent_id: string;
  status: 'online' | 'offline' | 'busy' | 'error';
  current_task?: string;
  last_activity?: string;
  capabilities?: string[];
  metadata?: Record<string, any>;
}

export interface MCPServerStatus {
  status: 'operational' | 'degraded' | 'offline';
  version: string;
  protocol: string;
  transports: string[];
  websocket_clients: number;
  capabilities: MCPCapabilities;
  stats: {
    tools_available: number;
    resources_available: number;
    prompts_available: number;
    activities_total: number;
    agents_online: number;
  };
}

export interface MCPToolExecution {
  tool: string;
  params: any;
  dry_run?: boolean;
  idempotency_key?: string;
}

export interface MCPToolResult {
  success: boolean;
  result?: any;
  error?: string;
  execution_time?: number;
  metadata?: Record<string, any>;
}

export interface MCPBatchRequest {
  requests: MCPRequest[];
  parallel?: boolean;
}

export interface MCPBatchResponse {
  responses: MCPResponse[];
  execution_time?: number;
}

// WebSocket Message Types
export interface MCPWebSocketMessage {
  type: 'activity' | 'state_change' | 'notification' | 'error';
  data: any;
  timestamp: string;
}

// Error Codes
export enum MCPErrorCode {
  PARSE_ERROR = -32700,
  INVALID_REQUEST = -32600,
  METHOD_NOT_FOUND = -32601,
  INVALID_PARAMS = -32602,
  INTERNAL_ERROR = -32603,
  // Custom MCP errors
  TOOL_NOT_FOUND = -32000,
  RESOURCE_NOT_FOUND = -32001,
  PROMPT_NOT_FOUND = -32002,
  UNAUTHORIZED = -32003,
  RATE_LIMITED = -32004,
  VALIDATION_ERROR = -32005,
}