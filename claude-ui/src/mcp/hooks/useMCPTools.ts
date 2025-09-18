// Hook for MCP Tools Management
import { useState, useEffect, useCallback } from 'react';
import { getMCPClient } from '../services/mcpClient';
import type { MCPTool, MCPToolExecution, MCPToolResult } from '../services/mcpTypes';

export const useMCPTools = () => {
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [executing, setExecuting] = useState(false);
  const client = getMCPClient();

  // Load available tools
  const loadTools = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const toolsList = await client.listTools();
      setTools(toolsList);
    } catch (err) {
      console.error('Failed to load MCP tools:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [client]);

  // Execute a tool
  const executeTool = useCallback(
    async (execution: MCPToolExecution): Promise<MCPToolResult | null> => {
      try {
        setExecuting(true);
        setError(null);
        const result = await client.callTool(execution);
        return result;
      } catch (err) {
        console.error('Failed to execute tool:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
        return null;
      } finally {
        setExecuting(false);
      }
    },
    [client]
  );

  // Dry run a tool (preview without execution)
  const dryRunTool = useCallback(
    async (execution: MCPToolExecution): Promise<MCPToolResult | null> => {
      return executeTool({ ...execution, dry_run: true });
    },
    [executeTool]
  );

  // Find tool by name
  const findTool = useCallback(
    (name: string): MCPTool | undefined => {
      return tools.find(t => t.name === name);
    },
    [tools]
  );

  // Group tools by category
  const toolsByCategory = useCallback((): Record<string, MCPTool[]> => {
    return tools.reduce((acc, tool) => {
      const category = tool.category || 'uncategorized';
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(tool);
      return acc;
    }, {} as Record<string, MCPTool[]>);
  }, [tools]);

  // Load tools on mount
  useEffect(() => {
    loadTools();
  }, [loadTools]);

  return {
    tools,
    loading,
    error,
    executing,
    executeTool,
    dryRunTool,
    findTool,
    toolsByCategory,
    refresh: loadTools,
  };
};

export default useMCPTools;