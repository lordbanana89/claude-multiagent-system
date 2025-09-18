// MCP Tool Executor Component - Execute MCP tools with UI
import React, { useState, useEffect } from 'react';
import { useMCPTools } from '../hooks/useMCPTools';
import type { MCPTool, MCPToolExecution } from '../services/mcpTypes';

const ToolExecutor: React.FC = () => {
  const { tools, loading, error, executing, executeTool, dryRunTool, toolsByCategory } = useMCPTools();
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);
  const [params, setParams] = useState<Record<string, any>>({});
  const [result, setResult] = useState<any>(null);
  const [executionError, setExecutionError] = useState<string | null>(null);
  const [isDryRun, setIsDryRun] = useState(true);

  // Group tools by category
  const categories = toolsByCategory();

  // Reset params when tool changes
  useEffect(() => {
    setParams({});
    setResult(null);
    setExecutionError(null);
  }, [selectedTool]);

  const handleExecute = async () => {
    if (!selectedTool) return;

    setResult(null);
    setExecutionError(null);

    const execution: MCPToolExecution = {
      tool: selectedTool.name,
      params,
      dry_run: isDryRun,
    };

    try {
      const res = isDryRun
        ? await dryRunTool(execution)
        : await executeTool(execution);

      if (res) {
        setResult(res);
        if (!res.success) {
          setExecutionError(res.error || 'Tool execution failed');
        }
      }
    } catch (err) {
      setExecutionError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const renderParamInput = (paramName: string, paramSchema: any) => {
    const type = paramSchema?.type || 'string';

    switch (type) {
      case 'boolean':
        return (
          <input
            type="checkbox"
            checked={params[paramName] || false}
            onChange={(e) => setParams({ ...params, [paramName]: e.target.checked })}
            className="mt-1"
          />
        );

      case 'number':
      case 'integer':
        return (
          <input
            type="number"
            value={params[paramName] || ''}
            onChange={(e) => setParams({ ...params, [paramName]: Number(e.target.value) })}
            className="w-full px-3 py-1 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
            placeholder={paramSchema.description}
          />
        );

      case 'object':
        return (
          <textarea
            value={params[paramName] ? JSON.stringify(params[paramName], null, 2) : ''}
            onChange={(e) => {
              try {
                setParams({ ...params, [paramName]: JSON.parse(e.target.value) });
              } catch {
                // Invalid JSON, don't update
              }
            }}
            className="w-full px-3 py-1 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none font-mono text-sm"
            rows={4}
            placeholder="Enter JSON object"
          />
        );

      default:
        return (
          <input
            type="text"
            value={params[paramName] || ''}
            onChange={(e) => setParams({ ...params, [paramName]: e.target.value })}
            className="w-full px-3 py-1 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
            placeholder={paramSchema.description}
          />
        );
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400">Loading MCP tools...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-red-400">Error loading tools: {error}</div>
      </div>
    );
  }

  return (
    <div className="h-full flex gap-4">
      {/* Tool Selector */}
      <div className="w-1/3 bg-gray-800 border border-gray-700 rounded-lg p-4 overflow-y-auto">
        <h3 className="text-white font-semibold mb-3">Available Tools</h3>

        {Object.entries(categories).map(([category, categoryTools]) => (
          <div key={category} className="mb-4">
            <h4 className="text-gray-400 text-sm font-semibold mb-2 uppercase">
              {category}
            </h4>
            <div className="space-y-1">
              {categoryTools.map((tool) => (
                <button
                  key={tool.name}
                  onClick={() => setSelectedTool(tool)}
                  className={`w-full text-left px-3 py-2 rounded transition-colors ${
                    selectedTool?.name === tool.name
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  <div className="font-medium">{tool.name}</div>
                  {tool.description && (
                    <div className="text-xs opacity-75 mt-1">{tool.description}</div>
                  )}
                  {tool.dangerous && (
                    <span className="inline-block mt-1 px-2 py-0.5 bg-red-900/50 text-red-300 text-xs rounded">
                      Dangerous
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Tool Configuration & Execution */}
      <div className="flex-1 bg-gray-800 border border-gray-700 rounded-lg p-4 overflow-y-auto">
        {selectedTool ? (
          <div>
            <h3 className="text-white font-semibold mb-3">
              Execute: {selectedTool.name}
            </h3>

            {selectedTool.description && (
              <p className="text-gray-400 text-sm mb-4">{selectedTool.description}</p>
            )}

            {/* Parameters */}
            {selectedTool.inputSchema?.properties && (
              <div className="mb-4">
                <h4 className="text-gray-300 font-medium mb-2">Parameters</h4>
                <div className="space-y-3">
                  {Object.entries(selectedTool.inputSchema.properties).map(([paramName, paramSchema]: [string, any]) => (
                    <div key={paramName}>
                      <label className="block text-gray-400 text-sm mb-1">
                        {paramName}
                        {selectedTool.inputSchema?.required?.includes(paramName) && (
                          <span className="text-red-400 ml-1">*</span>
                        )}
                      </label>
                      {renderParamInput(paramName, paramSchema)}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Execution Controls */}
            <div className="flex items-center gap-3 mb-4">
              <button
                onClick={handleExecute}
                disabled={executing}
                className={`px-4 py-2 rounded font-medium transition-colors ${
                  executing
                    ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                    : isDryRun
                    ? 'bg-yellow-600 hover:bg-yellow-700 text-white'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                {executing ? 'Executing...' : isDryRun ? 'Dry Run' : 'Execute'}
              </button>

              <label className="flex items-center text-gray-400 text-sm">
                <input
                  type="checkbox"
                  checked={isDryRun}
                  onChange={(e) => setIsDryRun(e.target.checked)}
                  className="mr-2"
                />
                Dry Run Mode
              </label>
            </div>

            {/* Result Display */}
            {(result || executionError) && (
              <div className="mt-4 border-t border-gray-700 pt-4">
                <h4 className="text-gray-300 font-medium mb-2">Result</h4>

                {executionError && (
                  <div className="bg-red-900/20 border border-red-700 rounded p-3 mb-3">
                    <div className="text-red-400 text-sm">{executionError}</div>
                  </div>
                )}

                {result && (
                  <div className={`border rounded p-3 ${
                    result.success
                      ? 'bg-green-900/20 border-green-700'
                      : 'bg-yellow-900/20 border-yellow-700'
                  }`}>
                    <div className="text-gray-300 font-mono text-sm whitespace-pre-wrap">
                      {typeof result.result === 'object'
                        ? JSON.stringify(result.result, null, 2)
                        : result.result}
                    </div>

                    {result.execution_time && (
                      <div className="mt-2 text-xs text-gray-500">
                        Execution time: {result.execution_time}ms
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            Select a tool to execute
          </div>
        )}
      </div>
    </div>
  );
};

export default ToolExecutor;