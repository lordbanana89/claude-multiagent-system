// Enhanced MCP Status Card Component
import React, { useState, useEffect } from 'react';
import { getMCPClient } from '../services/mcpClient';
import type { MCPServerStatus } from '../services/mcpTypes';

const MCPStatusCard: React.FC = () => {
  const [status, setStatus] = useState<MCPServerStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadStatus = async () => {
      try {
        setLoading(true);
        const client = getMCPClient();
        const serverStatus = await client.getStatus();
        setStatus(serverStatus);
        setError(null);
      } catch (err) {
        console.error('Failed to load MCP status:', err);
        setError(err instanceof Error ? err.message : 'Failed to connect');
        setStatus(null);
      } finally {
        setLoading(false);
      }
    };

    loadStatus();
    const interval = setInterval(loadStatus, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  if (loading && !status) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-700 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
        <h3 className="text-red-400 font-semibold mb-2 flex items-center">
          <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
          MCP v2 Offline
        </h3>
        <p className="text-red-300 text-sm">{error}</p>
      </div>
    );
  }

  if (!status) return null;

  const statusColor = status.status === 'operational' ? 'green' : status.status === 'degraded' ? 'yellow' : 'red';
  const statusBg = {
    green: 'bg-green-900/20 border-green-700',
    yellow: 'bg-yellow-900/20 border-yellow-700',
    red: 'bg-red-900/20 border-red-700',
  }[statusColor];

  return (
    <div className={`border rounded-lg p-4 transition-all duration-200 ${statusBg}`}>
      <div
        className="cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <h3 className={`text-${statusColor}-400 font-semibold mb-2 flex items-center justify-between`}>
          <span className="flex items-center">
            <span className={`w-2 h-2 bg-${statusColor}-500 rounded-full mr-2 animate-pulse`}></span>
            MCP v2 {status.status.charAt(0).toUpperCase() + status.status.slice(1)}
          </span>
          <span className="text-xs">
            {expanded ? '▼' : '▶'}
          </span>
        </h3>

        <div className="space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Protocol:</span>
            <span className="text-gray-200 font-mono">{status.protocol}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Version:</span>
            <span className="text-gray-200">{status.version}</span>
          </div>
        </div>
      </div>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-gray-700 space-y-2 text-sm animate-fadeIn">
          <h4 className="text-gray-300 font-semibold mb-2">Capabilities</h4>
          <div className="grid grid-cols-2 gap-2">
            <div className="flex items-center">
              <span className={`w-2 h-2 rounded-full mr-2 ${
                status.capabilities.features.idempotency ? 'bg-green-500' : 'bg-gray-500'
              }`}></span>
              <span className="text-gray-400">Idempotency</span>
            </div>
            <div className="flex items-center">
              <span className={`w-2 h-2 rounded-full mr-2 ${
                status.capabilities.features.dry_run ? 'bg-green-500' : 'bg-gray-500'
              }`}></span>
              <span className="text-gray-400">Dry Run</span>
            </div>
            <div className="flex items-center">
              <span className={`w-2 h-2 rounded-full mr-2 ${
                status.capabilities.features.streaming ? 'bg-green-500' : 'bg-gray-500'
              }`}></span>
              <span className="text-gray-400">Streaming</span>
            </div>
            <div className="flex items-center">
              <span className={`w-2 h-2 rounded-full mr-2 ${
                status.capabilities.features.batch_requests ? 'bg-green-500' : 'bg-gray-500'
              }`}></span>
              <span className="text-gray-400">Batch</span>
            </div>
          </div>

          <h4 className="text-gray-300 font-semibold mt-3 mb-2">Statistics</h4>
          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="text-gray-400">Tools Available:</span>
              <span className="text-blue-400 font-semibold">{status.stats?.tools_available || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Resources:</span>
              <span className="text-purple-400 font-semibold">{status.stats?.resources_available || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Prompts:</span>
              <span className="text-pink-400 font-semibold">{status.stats?.prompts_available || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Activities:</span>
              <span className="text-yellow-400 font-semibold">{status.stats?.activities_total || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Agents Online:</span>
              <span className="text-green-400 font-semibold">
                {status.stats?.agents_online || 0}
              </span>
            </div>
          </div>

          <h4 className="text-gray-300 font-semibold mt-3 mb-2">Transports</h4>
          <div className="flex gap-2">
            {status.transports.map(transport => (
              <span
                key={transport}
                className="px-2 py-1 bg-gray-700/50 text-gray-300 rounded text-xs"
              >
                {transport.toUpperCase()}
              </span>
            ))}
          </div>

          {status.websocket_clients > 0 && (
            <div className="mt-2 flex justify-between">
              <span className="text-gray-400 text-xs">WebSocket Clients:</span>
              <span className="text-gray-200 text-xs">{status.websocket_clients}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MCPStatusCard;