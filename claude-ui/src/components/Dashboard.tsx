import React, { useState, useEffect } from 'react';
import { Activity, Users, Zap, AlertCircle, CheckCircle } from 'lucide-react';
import integrationService from '../services/integration';

interface SystemStats {
  totalAgents: number;
  activeAgents: number;
  totalTasks: number;
  completedTasks: number;
  systemUptime: string;
  messagesRouted: number;
}

const Dashboard: React.FC = () => {
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [stats, setStats] = useState<SystemStats>({
    totalAgents: 9,
    activeAgents: 0,
    totalTasks: 0,
    completedTasks: 0,
    systemUptime: '0h 0m',
    messagesRouted: 0
  });

  useEffect(() => {
    const loadHealth = async () => {
      const health = await integrationService.getSystemHealth();
      setSystemHealth(health);

      // Update stats based on health
      const activeCount = Object.values(health.agents || {}).filter(Boolean).length;
      setStats(prev => ({
        ...prev,
        activeAgents: activeCount
      }));
    };

    loadHealth();
    const interval = setInterval(loadHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  const getServiceStatus = (isActive: boolean) => {
    return isActive ? (
      <CheckCircle className="w-5 h-5 text-green-500" />
    ) : (
      <AlertCircle className="w-5 h-5 text-red-500" />
    );
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">System Overview</h1>
        <p className="text-gray-400">Claude Squad Multi-Agent System</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <Users className="w-8 h-8 text-blue-500" />
            <span className="text-2xl font-bold text-white">
              {stats.activeAgents}/{stats.totalAgents}
            </span>
          </div>
          <h3 className="text-sm font-medium text-gray-400">Active Agents</h3>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <Activity className="w-8 h-8 text-green-500" />
            <span className="text-2xl font-bold text-white">
              {stats.completedTasks}/{stats.totalTasks}
            </span>
          </div>
          <h3 className="text-sm font-medium text-gray-400">Tasks Completed</h3>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <Zap className="w-8 h-8 text-yellow-500" />
            <span className="text-2xl font-bold text-white">
              {stats.messagesRouted}
            </span>
          </div>
          <h3 className="text-sm font-medium text-gray-400">Messages Routed</h3>
        </div>
      </div>

      {/* System Health */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">System Health</h2>

        {systemHealth && (
          <div className="space-y-4">
            {/* Core Services */}
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-2">Core Services</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="flex items-center space-x-2">
                  {getServiceStatus(systemHealth.database)}
                  <span className="text-sm text-white">Database</span>
                </div>
                <div className="flex items-center space-x-2">
                  {getServiceStatus(systemHealth.redis)}
                  <span className="text-sm text-white">Redis</span>
                </div>
                <div className="flex items-center space-x-2">
                  {getServiceStatus(systemHealth.api)}
                  <span className="text-sm text-white">API Gateway</span>
                </div>
                <div className="flex items-center space-x-2">
                  {getServiceStatus(systemHealth.frontend)}
                  <span className="text-sm text-white">Frontend</span>
                </div>
              </div>
            </div>

            {/* Agents Status */}
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-2">Agent Status</h3>
              <div className="grid grid-cols-3 md:grid-cols-5 gap-4">
                {Object.entries(systemHealth.agents || {}).map(([agent, isActive]) => (
                  <div key={agent} className="flex items-center space-x-2">
                    {getServiceStatus(isActive as boolean)}
                    <span className="text-sm text-white capitalize">{agent}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Quick Actions</h2>
        <div className="flex space-x-4">
          <button
            onClick={() => integrationService.syncAll()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Sync All Components
          </button>
          <button
            onClick={() => integrationService.autoFixServices()}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            Auto-Fix Issues
          </button>
          <button
            onClick={() => integrationService.broadcast('System check', 'high')}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            Broadcast Test
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;