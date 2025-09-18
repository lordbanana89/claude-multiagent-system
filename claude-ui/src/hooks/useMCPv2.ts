import { useState, useEffect, useCallback } from 'react';

interface MCPv2Status {
  connected: boolean;
  protocol: string;
  version: string;
  capabilities: number;
  tools: number;
  resources: number;
  prompts: number;
}

export const useMCPv2 = () => {
  const [status, setStatus] = useState<MCPv2Status>({
    connected: false,
    protocol: '',
    version: '',
    capabilities: 0,
    tools: 0,
    resources: 0,
    prompts: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkMCPv2Status = useCallback(async () => {
    try {
      const mcpApiUrl = import.meta.env.VITE_MCP_API_URL || 'http://localhost:8099';
      const response = await fetch(`${mcpApiUrl}/api/mcp/status`);

      if (!response.ok) {
        throw new Error('MCP v2 server not responding');
      }

      const data = await response.json();

      // Check if it's MCP v2
      const isV2 = data.protocol === '2025-06-18' || data.version === '2.0';

      // Count capabilities
      const capabilityCount =
        (data.capabilities?.supports?.length || 0) +
        (Object.keys(data.capabilities?.features || {}).length || 0);

      setStatus({
        connected: isV2,
        protocol: data.protocol || '',
        version: data.version || '',
        capabilities: capabilityCount,
        tools: data.stats?.tools_available || 0,
        resources: data.stats?.resources_available || 0,
        prompts: data.stats?.prompts_available || 0,
      });

      setError(null);
    } catch (err) {
      console.error('MCP v2 check failed:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      setStatus(prev => ({ ...prev, connected: false }));
    } finally {
      setLoading(false);
    }
  }, []);

  // Check status on mount and periodically
  useEffect(() => {
    checkMCPv2Status();
    const interval = setInterval(checkMCPv2Status, 10000); // Check every 10 seconds
    return () => clearInterval(interval);
  }, [checkMCPv2Status]);

  return {
    mcpV2Status: status,
    mcpV2Loading: loading,
    mcpV2Error: error,
    refreshMCPv2: checkMCPv2Status,
  };
};

export default useMCPv2;