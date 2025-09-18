import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Agent {
  id: string;
  name: string;
  type: string;
  status: string;
  sessionId: string;
  lastActivity: string;
}

const SimpleDashboard: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('agents');

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [agentsRes, healthRes] = await Promise.all([
        axios.get('http://localhost:8000/api/agents'),
        axios.get('http://localhost:8000/api/system/health')
      ]);

      setAgents(agentsRes.data);
      setSystemHealth(healthRes.data);
      setLoading(false);
      setError(null);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to connect to API');
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'bg-green-500';
      case 'offline': return 'bg-gray-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-yellow-500';
    }
  };

  const getHealthColor = (healthy: boolean) => {
    return healthy ? 'text-green-500' : 'text-red-500';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">Claude Multi-Agent System</h1>
            <div className="flex items-center gap-4">
              {systemHealth && (
                <div className={`flex items-center gap-2 ${getHealthColor(systemHealth.overall_health)}`}>
                  <span className="text-sm">System:</span>
                  <span className="font-medium">
                    {systemHealth.overall_health ? 'Healthy' : 'Issues Detected'}
                  </span>
                </div>
              )}
              <button
                onClick={fetchData}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-900 border border-red-700 px-4 py-2">
          <p className="text-red-200">{error}</p>
        </div>
      )}

      {/* Tabs */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-4">
            {['agents', 'health', 'streamlit'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-3 px-4 capitalize ${
                  activeTab === tab
                    ? 'text-blue-400 border-b-2 border-blue-400'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Agents Tab */}
        {activeTab === 'agents' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((agent) => (
              <div
                key={agent.id}
                className="bg-gray-800 rounded-lg p-4 border border-gray-700"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-lg">{agent.name}</h3>
                    <p className="text-sm text-gray-400">{agent.type}</p>
                  </div>
                  <div className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)}`} />
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Status:</span>
                    <span className="capitalize">{agent.status}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Session:</span>
                    <span className="font-mono text-xs">{agent.sessionId}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Last Active:</span>
                    <span>{new Date(agent.lastActivity).toLocaleTimeString()}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Health Tab */}
        {activeTab === 'health' && systemHealth && (
          <div className="space-y-6">
            {/* Components Health */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h2 className="text-xl font-semibold mb-4">System Components</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(systemHealth.components).map(([key, value]: any) => (
                  <div key={key} className="flex items-center justify-between">
                    <span className="capitalize">{key.replace(/_/g, ' ')}:</span>
                    <span className={value.healthy ? 'text-green-500' : 'text-red-500'}>
                      {value.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Metrics */}
            {systemHealth.metrics && (
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h2 className="text-xl font-semibold mb-4">System Metrics</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {Object.entries(systemHealth.metrics).map(([key, value]: any) => (
                    <div key={key} className="text-center">
                      <p className="text-gray-400 text-sm capitalize">
                        {key.replace(/_/g, ' ')}
                      </p>
                      <p className="text-2xl font-bold mt-1">
                        {typeof value === 'number' ? value.toFixed(2) : value}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Streamlit Tab */}
        {activeTab === 'streamlit' && (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-xl font-semibold mb-4">Legacy Interface</h2>
            <p className="text-gray-400 mb-4">
              The Streamlit interface is running on port 8501
            </p>
            <a
              href="http://localhost:8501"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg"
            >
              Open Streamlit Interface →
            </a>
            <div className="mt-6 p-4 bg-gray-900 rounded">
              <p className="text-sm text-gray-400">
                Features available in Streamlit:
              </p>
              <ul className="mt-2 text-sm space-y-1 list-disc list-inside">
                <li>Task execution and monitoring</li>
                <li>Agent terminal access</li>
                <li>Queue management</li>
                <li>Real-time logs</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SimpleDashboard;