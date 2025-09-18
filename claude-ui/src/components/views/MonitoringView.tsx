import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import MetricsPanel from '../panels/MetricsPanel';
import LogsPanel from '../panels/LogsPanel';
import PerformanceChart from '../charts/PerformanceChart';

type MonitoringTab = 'metrics' | 'performance' | 'logs' | 'health';

const MonitoringView: React.FC = () => {
  const { state } = useApp();
  const [activeTab, setActiveTab] = useState<MonitoringTab>('metrics');
  const [selectedAgent, setSelectedAgent] = useState(state.selectedAgent);
  const [timeRange, setTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('1h');

  const tabs = [
    { id: 'metrics' as const, label: 'Metrics', icon: '📊' },
    { id: 'performance' as const, label: 'Performance', icon: '📈' },
    { id: 'logs' as const, label: 'Logs', icon: '📜' },
    { id: 'health' as const, label: 'System Health', icon: '🏥' },
  ];

  const renderHealthStatus = () => {
    if (!state.systemHealth) return null;

    return (
      <div className="p-6 space-y-6">
        {/* Overall Status */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">System Health Overview</h3>

          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-700 rounded p-4">
              <div className="text-xs text-gray-400 mb-1">Status</div>
              <div className={`text-2xl font-bold ${
                state.systemHealth.status === 'healthy' ? 'text-green-400' :
                state.systemHealth.status === 'degraded' ? 'text-yellow-400' :
                'text-red-400'
              }`}>
                {state.systemHealth.status?.toUpperCase()}
              </div>
            </div>
            <div className="bg-gray-700 rounded p-4">
              <div className="text-xs text-gray-400 mb-1">Healthy</div>
              <div className="text-2xl font-bold text-green-400">
                {state.systemHealth.summary?.healthy || 0}
              </div>
            </div>
            <div className="bg-gray-700 rounded p-4">
              <div className="text-xs text-gray-400 mb-1">Degraded</div>
              <div className="text-2xl font-bold text-yellow-400">
                {state.systemHealth.summary?.degraded || 0}
              </div>
            </div>
            <div className="bg-gray-700 rounded p-4">
              <div className="text-xs text-gray-400 mb-1">Unhealthy</div>
              <div className="text-2xl font-bold text-red-400">
                {state.systemHealth.summary?.unhealthy || 0}
              </div>
            </div>
          </div>

          {/* Components Status */}
          <div className="space-y-3">
            {Object.entries(state.systemHealth.components || {}).map(([key, component]: [string, any]) => (
              <div key={key} className="bg-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium text-white capitalize">{component.name}</span>
                    <p className="text-sm text-gray-400 mt-1">{component.message}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    component.status === 'healthy' ? 'bg-green-900 text-green-300' :
                    component.status === 'degraded' ? 'bg-yellow-900 text-yellow-300' :
                    'bg-red-900 text-red-300'
                  }`}>
                    {component.status}
                  </span>
                </div>

                {component.details && (
                  <div className="mt-3 pt-3 border-t border-gray-600 text-xs text-gray-400">
                    <pre className="font-mono">{JSON.stringify(component.details, null, 2)}</pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Tab Navigation with Time Range Selector */}
      <div className="bg-gray-800 border-b border-gray-700 px-4 flex items-center justify-between">
        <nav className="flex space-x-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-3 px-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'text-blue-400 border-blue-400'
                  : 'text-gray-400 border-transparent hover:text-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Time Range Selector */}
        {(activeTab === 'metrics' || activeTab === 'performance') && (
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-400">Time Range:</span>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as any)}
              className="px-3 py-1 bg-gray-700 text-white rounded text-sm border border-gray-600"
            >
              <option value="1h">Last 1 Hour</option>
              <option value="6h">Last 6 Hours</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
            </select>
          </div>
        )}
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto">
        {activeTab === 'metrics' && (
          <div className="p-6">
            <MetricsPanel
              systemHealth={state.systemHealth}
              agents={state.agents}
              detailed={true}
            />
          </div>
        )}

        {activeTab === 'performance' && (
          <div className="p-6">
            <PerformanceChart
              agentId={selectedAgent?.id}
              timeRange={timeRange}
            />
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="flex h-full">
            {/* Agent Selector Sidebar */}
            <aside className="w-64 bg-gray-800 border-r border-gray-700 p-4">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                Filter by Agent
              </h3>
              <div className="space-y-2">
                <button
                  onClick={() => setSelectedAgent(null)}
                  className={`w-full p-2 rounded text-left text-sm transition-colors ${
                    !selectedAgent
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  All Agents
                </button>
                {state.agents.map((agent) => (
                  <button
                    key={agent.id}
                    onClick={() => setSelectedAgent(agent)}
                    className={`w-full p-2 rounded text-left text-sm transition-colors ${
                      selectedAgent?.id === agent.id
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {agent.name}
                  </button>
                ))}
              </div>
            </aside>

            {/* Logs Panel */}
            <div className="flex-1">
              <LogsPanel
                logs={state.logs}
                selectedAgent={selectedAgent}
                agents={state.agents}
              />
            </div>
          </div>
        )}

        {activeTab === 'health' && renderHealthStatus()}
      </div>
    </div>
  );
};

export default MonitoringView;