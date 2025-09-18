import React from 'react';

interface MetricsPanelProps {
  systemHealth: any;
  agents: any[];
  detailed?: boolean;
}

const MetricsPanel: React.FC<MetricsPanelProps> = ({ systemHealth, agents, detailed = false }) => {
  const getMetricColor = (value: number, thresholds: { good: number; warning: number }) => {
    if (value >= thresholds.good) return 'text-green-400';
    if (value >= thresholds.warning) return 'text-yellow-400';
    return 'text-red-400';
  };

  const calculateSystemScore = () => {
    if (!systemHealth) return 0;
    let score = 0;
    if (systemHealth.status === 'healthy') score += 40;
    if (systemHealth.components?.redis?.status === 'healthy') score += 30;
    const onlineAgents = agents.filter(a => a.status === 'online').length;
    score += (onlineAgents / agents.length) * 30;
    return Math.round(score);
  };

  if (detailed) {
    // Full page metrics view
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* System Overview */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">System Overview</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Health Score</span>
              <span className={getMetricColor(calculateSystemScore(), { good: 80, warning: 60 })}>
                {calculateSystemScore()}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Uptime</span>
              <span className="text-white">{systemHealth?.uptime_human || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">API Latency</span>
              <span className="text-white">{systemHealth?.latency || 'N/A'}ms</span>
            </div>
          </div>
        </div>

        {/* Agent Metrics */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Agent Performance</h3>
          {agents.slice(0, 5).map(agent => (
            <div key={agent.id} className="mb-3">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-400">{agent.name}</span>
                <span className={`text-xs ${
                  agent.status === 'online' ? 'text-green-400' :
                  agent.status === 'busy' ? 'text-yellow-400' :
                  'text-gray-500'
                }`}>
                  {agent.status}
                </span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    agent.status === 'online' ? 'bg-green-500' :
                    agent.status === 'busy' ? 'bg-yellow-500' :
                    'bg-gray-500'
                  }`}
                  style={{ width: agent.status === 'online' ? '100%' : agent.status === 'busy' ? '60%' : '0%' }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Resource Usage */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Resource Usage</h3>
          <div className="space-y-4">
            {systemHealth?.components?.redis?.details && (
              <>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-400">Redis Memory</span>
                    <span className="text-white">
                      {systemHealth.components.redis.details.used_memory_human}
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="h-2 bg-blue-500 rounded-full" style={{ width: '45%' }} />
                  </div>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Connected Clients</span>
                  <span className="text-white text-sm">
                    {systemHealth.components.redis.details.connected_clients}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Commands/sec</span>
                  <span className="text-white text-sm">
                    {systemHealth.components.redis.details.instantaneous_ops_per_sec || 0}
                  </span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Compact panel view for workflow
  return (
    <div className="bg-gray-800/90 backdrop-blur rounded-lg p-4 m-4 min-w-[250px]">
      <h3 className="text-lg font-semibold text-white mb-3">System Metrics</h3>

      {systemHealth && (
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Status:</span>
            <span className={`font-medium ${
              systemHealth.status === 'healthy' ? 'text-green-400' : 'text-yellow-400'
            }`}>
              {systemHealth.status}
            </span>
          </div>

          <div className="flex justify-between">
            <span className="text-gray-400">Uptime:</span>
            <span className="text-white font-medium">
              {systemHealth.uptime_human || '0m'}
            </span>
          </div>

          <div className="flex justify-between">
            <span className="text-gray-400">Active Agents:</span>
            <span className="text-green-400 font-medium">
              {agents.filter(a => a.status === 'online').length}/{agents.length}
            </span>
          </div>

          <div className="flex justify-between">
            <span className="text-gray-400">System Score:</span>
            <span className={`font-bold ${
              getMetricColor(calculateSystemScore(), { good: 80, warning: 60 })
            }`}>
              {calculateSystemScore()}%
            </span>
          </div>

          {systemHealth.components?.redis?.status && (
            <div className="border-t border-gray-700 pt-2 mt-2">
              <div className="flex justify-between">
                <span className="text-gray-400">Redis:</span>
                <span className={`font-medium ${
                  systemHealth.components.redis.status === 'healthy' ? 'text-green-400' : 'text-red-400'
                }`}>
                  {systemHealth.components.redis.status}
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MetricsPanel;