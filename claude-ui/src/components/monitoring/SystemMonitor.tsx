import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { config } from '../../config';

const API_URL = config.API_URL;

interface QueueStats {
  queued: number;
  processing: number;
  completed: number;
  failed: number;
  totalMessages: number;
  avgProcessingTime: number;
}

interface SystemHealth {
  status: string;
  uptime: number;
  cpu_usage: number;
  memory_usage: number;
  redis_connected: boolean;
  agents_online: number;
  agents_total: number;
}

const SystemMonitor: React.FC = () => {
  const [selectedTimeRange, setSelectedTimeRange] = useState('1h');
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch queue stats
  const { data: queueStats } = useQuery<QueueStats>({
    queryKey: ['queueStats'],
    queryFn: async () => {
      try {
        const response = await axios.get(`${API_URL}/api/queue/stats`);
        return response.data;
      } catch (error) {
        console.error('Failed to fetch queue stats:', error);
        // Return empty stats instead of mock data
        return {
          queued: 0,
          processing: 0,
          completed: 0,
          failed: 0,
          totalMessages: 0,
          avgProcessingTime: 0,
        };
      }
    },
    refetchInterval: autoRefresh ? 2000 : false,
  });

  // Fetch system health
  const { data: systemHealth } = useQuery<SystemHealth>({
    queryKey: ['systemHealth'],
    queryFn: async () => {
      try {
        const response = await axios.get(`${API_URL}/api/system/health`);
        return response.data;
      } catch (error) {
        console.error('Failed to fetch system health:', error);
        // Return empty health data instead of mock data
        return {
          status: 'unknown',
          uptime: 0,
          cpu_usage: 0,
          memory_usage: 0,
          redis_connected: false,
          agents_online: 0,
          agents_total: 0,
        };
      }
    },
    refetchInterval: autoRefresh ? 5000 : false,
  });

  // Fetch real performance data
  const { data: performanceData } = useQuery<{timestamp: number, value: number}[]>({
    queryKey: ['performanceData', selectedTimeRange],
    queryFn: async () => {
      try {
        const response = await axios.get(`${API_URL}/api/analytics/performance`, {
          params: { timeRange: selectedTimeRange }
        });
        return response.data.performance || [];
      } catch {
        return [];
      }
    },
    refetchInterval: autoRefresh ? 10000 : false,
  });

  const cpuData = performanceData?.map(d => ({ timestamp: d.timestamp, value: (d as any).cpu || 0 })) || [];
  const memoryData = performanceData?.map(d => ({ timestamp: d.timestamp, value: (d as any).memory || 0 })) || [];
  const queueData = performanceData?.map(d => ({ timestamp: d.timestamp, value: (d as any).queueSize || 0 })) || [];

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          System Monitor
        </h2>
        <div className="flex items-center space-x-4">
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(e.target.value)}
            className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md text-sm"
          >
            <option value="5m">Last 5 minutes</option>
            <option value="1h">Last 1 hour</option>
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
          </select>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-4 py-2 rounded-md font-medium transition-colors ${
              autoRefresh
                ? 'bg-green-600 text-white hover:bg-green-700'
                : 'bg-gray-300 text-gray-700 hover:bg-gray-400'
            }`}
          >
            {autoRefresh ? '🔄 Auto-refresh ON' : '⏸️ Auto-refresh OFF'}
          </button>
        </div>
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatusCard
          title="System Status"
          value={systemHealth?.status || 'Unknown'}
          icon="🟢"
          color="green"
          subtitle={`Uptime: ${formatUptime(systemHealth?.uptime || 0)}`}
        />
        <StatusCard
          title="CPU Usage"
          value={`${Math.round(systemHealth?.cpu_usage || 0)}%`}
          icon="💻"
          color="blue"
          trend={cpuData[cpuData.length - 1]?.value > cpuData[cpuData.length - 2]?.value ? 'up' : 'down'}
        />
        <StatusCard
          title="Memory Usage"
          value={`${Math.round(systemHealth?.memory_usage || 0)}%`}
          icon="🧠"
          color="purple"
          trend={memoryData[memoryData.length - 1]?.value > memoryData[memoryData.length - 2]?.value ? 'up' : 'down'}
        />
        <StatusCard
          title="Agents Online"
          value={`${systemHealth?.agents_online || 0}/${systemHealth?.agents_total || 0}`}
          icon="🤖"
          color="indigo"
          subtitle="Active agents"
        />
      </div>

      {/* Queue Statistics */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Queue Statistics
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <QueueStatCard
            label="Queued"
            value={queueStats?.queued || 0}
            color="yellow"
          />
          <QueueStatCard
            label="Processing"
            value={queueStats?.processing || 0}
            color="blue"
          />
          <QueueStatCard
            label="Completed"
            value={queueStats?.completed || 0}
            color="green"
          />
          <QueueStatCard
            label="Failed"
            value={queueStats?.failed || 0}
            color="red"
          />
        </div>
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">
              Total Messages: {queueStats?.totalMessages || 0}
            </span>
            <span className="text-gray-600 dark:text-gray-400">
              Avg Processing Time: {(queueStats?.avgProcessingTime || 0).toFixed(2)}s
            </span>
          </div>
        </div>
      </div>

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard
          title="CPU Usage"
          data={cpuData}
          color="#3b82f6"
        />
        <ChartCard
          title="Memory Usage"
          data={memoryData}
          color="#8b5cf6"
        />
      </div>

      {/* Queue Throughput Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Queue Throughput
        </h3>
        <SimpleLineChart data={queueData} color="#10b981" height={200} />
      </div>

      {/* System Logs Preview */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Recent System Events
        </h3>
        <SystemLogs autoRefresh={autoRefresh} />
      </div>
    </div>
  );
};

// Status Card Component
const StatusCard: React.FC<{
  title: string;
  value: string;
  icon: string;
  color: string;
  subtitle?: string;
  trend?: 'up' | 'down';
}> = ({ title, value, icon, color, subtitle, trend }) => {
  const colorClasses = {
    green: 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400',
    blue: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400',
    purple: 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400',
    indigo: 'bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400',
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color as keyof typeof colorClasses]}`}>
          <span className="text-2xl">{icon}</span>
        </div>
      </div>
      {trend && (
        <div className="mt-2">
          <span className={trend === 'up' ? 'text-red-500' : 'text-green-500'}>
            {trend === 'up' ? '↑' : '↓'}
          </span>
        </div>
      )}
    </div>
  );
};

// Queue Stat Card Component
const QueueStatCard: React.FC<{
  label: string;
  value: number;
  color: string;
}> = ({ label, value, color }) => {
  const colorClasses = {
    yellow: 'text-yellow-600 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-900/20',
    blue: 'text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/20',
    green: 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/20',
    red: 'text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/20',
  };

  return (
    <div className={`rounded-lg p-4 ${colorClasses[color as keyof typeof colorClasses]}`}>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-sm">{label}</div>
    </div>
  );
};

// Simple Chart Components
const ChartCard: React.FC<{
  title: string;
  data: Array<{ timestamp: number; value: number }>;
  color: string;
}> = ({ title, data, color }) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
      <SimpleLineChart data={data} color={color} height={150} />
    </div>
  );
};

const SimpleLineChart: React.FC<{
  data: Array<{ timestamp: number; value: number }>;
  color: string;
  height: number;
}> = ({ data, color, height }) => {
  const maxValue = Math.max(...data.map(d => d.value)) || 1;
  const width = 200; // Fixed width for SVG viewport

  return (
    <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={height} className="overflow-visible">
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="2"
        points={data
          .map(
            (point, index) =>
              `${(index / (data.length - 1)) * width},${
                height - (point.value / maxValue) * height
              }`
          )
          .join(' ')}
      />
      {data.map((point, index) => (
        <circle
          key={index}
          cx={(index / (data.length - 1)) * width}
          cy={height - (point.value / maxValue) * height}
          r="3"
          fill={color}
        />
      ))}
    </svg>
  );
};

// System Logs Component - fetches real logs from database
const SystemLogs: React.FC<{ autoRefresh: boolean }> = ({ autoRefresh }) => {
  const { data: logs } = useQuery<Array<{
    level: string;
    message: string;
    timestamp: string;
  }>>({
    queryKey: ['systemLogs'],
    queryFn: async () => {
      try {
        const response = await axios.get(`${API_URL}/api/system/logs`, {
          params: { limit: 5 }
        });
        return response.data;
      } catch (error) {
        console.error('Failed to fetch system logs:', error);
        // Return empty array instead of mock data
        return [];
      }
    },
    refetchInterval: autoRefresh ? 5000 : false,
  });

  if (!logs || logs.length === 0) {
    return (
      <div className="text-gray-500 dark:text-gray-400 text-sm">
        No recent events
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {logs.map((log, index) => (
        <LogEntry
          key={index}
          level={log.level}
          message={log.message}
          timestamp={new Date(log.timestamp)}
        />
      ))}
    </div>
  );
};

// Log Entry Component
const LogEntry: React.FC<{
  level: string;
  message: string;
  timestamp: Date;
}> = ({ level, message, timestamp }) => {
  const levelColors = {
    info: 'text-blue-600 dark:text-blue-400',
    warning: 'text-yellow-600 dark:text-yellow-400',
    error: 'text-red-600 dark:text-red-400',
    success: 'text-green-600 dark:text-green-400',
  };

  const levelIcons = {
    info: 'ℹ️',
    warning: '⚠️',
    error: '❌',
    success: '✅',
  };

  return (
    <div className="flex items-start space-x-3 text-sm">
      <span>{levelIcons[level as keyof typeof levelIcons]}</span>
      <div className="flex-1">
        <span className={levelColors[level as keyof typeof levelColors]}>{message}</span>
        <span className="text-gray-400 dark:text-gray-500 ml-2">
          {timestamp.toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
};

export default SystemMonitor;