import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { format } from 'date-fns';

interface PerformanceData {
  timestamp: string;
  cpu: number;
  memory: number;
  latency: number;
  requests: number;
  errors: number;
}

interface ChartProps {
  agentId?: string;
  timeRange?: '1h' | '6h' | '24h' | '7d';
}

const PerformanceChart: React.FC<ChartProps> = ({
  agentId = 'all',
  timeRange = '1h'
}) => {
  const [data, setData] = useState<PerformanceData[]>([]);
  const [loading, setLoading] = useState(true);
  const [chartType, setChartType] = useState<'line' | 'area' | 'bar'>('line');
  const [metrics, setMetrics] = useState({
    avgCpu: 0,
    avgMemory: 0,
    avgLatency: 0,
    totalRequests: 0,
    errorRate: 0
  });

  // Generate mock data for demonstration
  const generateMockData = (): PerformanceData[] => {
    const points = timeRange === '1h' ? 12 : timeRange === '6h' ? 36 : timeRange === '24h' ? 48 : 84;
    const now = Date.now();
    const interval = timeRange === '1h' ? 5 * 60 * 1000 : // 5 minutes
                     timeRange === '6h' ? 10 * 60 * 1000 : // 10 minutes
                     timeRange === '24h' ? 30 * 60 * 1000 : // 30 minutes
                     2 * 60 * 60 * 1000; // 2 hours

    return Array.from({ length: points }, (_, i) => {
      const timestamp = new Date(now - (points - i) * interval);
      return {
        timestamp: timestamp.toISOString(),
        cpu: Math.random() * 30 + 40 + Math.sin(i / 5) * 20,
        memory: Math.random() * 20 + 60 + Math.cos(i / 7) * 15,
        latency: Math.random() * 50 + 100 + Math.sin(i / 3) * 30,
        requests: Math.floor(Math.random() * 100 + 50),
        errors: Math.floor(Math.random() * 5)
      };
    });
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // In production, this would fetch from the API
        // const response = await axios.get(`${config.API_URL}/api/analytics/performance`, {
        //   params: { agentId, timeRange }
        // });
        // setData(response.data);

        // For now, use mock data
        const mockData = generateMockData();
        setData(mockData);

        // Calculate metrics
        const avgCpu = mockData.reduce((sum, d) => sum + d.cpu, 0) / mockData.length;
        const avgMemory = mockData.reduce((sum, d) => sum + d.memory, 0) / mockData.length;
        const avgLatency = mockData.reduce((sum, d) => sum + d.latency, 0) / mockData.length;
        const totalRequests = mockData.reduce((sum, d) => sum + d.requests, 0);
        const totalErrors = mockData.reduce((sum, d) => sum + d.errors, 0);

        setMetrics({
          avgCpu: Math.round(avgCpu),
          avgMemory: Math.round(avgMemory),
          avgLatency: Math.round(avgLatency),
          totalRequests,
          errorRate: totalRequests > 0 ? (totalErrors / totalRequests) * 100 : 0
        });
      } catch (error) {
        console.error('Failed to fetch performance data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [agentId, timeRange]);

  const formatXAxis = (tickItem: string) => {
    const date = new Date(tickItem);
    if (timeRange === '1h' || timeRange === '6h') {
      return format(date, 'HH:mm');
    } else if (timeRange === '24h') {
      return format(date, 'HH:mm');
    } else {
      return format(date, 'MMM dd');
    }
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-800 p-3 rounded shadow-lg border border-gray-700">
          <p className="text-white text-sm font-medium">
            {format(new Date(label), 'MMM dd, HH:mm')}
          </p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value.toFixed(1)}
              {entry.name.includes('CPU') || entry.name.includes('Memory') ? '%' : ''}
              {entry.name.includes('Latency') ? 'ms' : ''}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  if (loading) {
    return (
      <div className="h-96 flex items-center justify-center">
        <div className="text-gray-400">Loading performance data...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Metrics Summary */}
      <div className="grid grid-cols-5 gap-4">
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="text-xs text-gray-400 mb-1">Avg CPU</div>
          <div className="text-2xl font-bold text-blue-400">{metrics.avgCpu}%</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="text-xs text-gray-400 mb-1">Avg Memory</div>
          <div className="text-2xl font-bold text-green-400">{metrics.avgMemory}%</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="text-xs text-gray-400 mb-1">Avg Latency</div>
          <div className="text-2xl font-bold text-yellow-400">{metrics.avgLatency}ms</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="text-xs text-gray-400 mb-1">Total Requests</div>
          <div className="text-2xl font-bold text-purple-400">{metrics.totalRequests}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="text-xs text-gray-400 mb-1">Error Rate</div>
          <div className="text-2xl font-bold text-red-400">{metrics.errorRate.toFixed(2)}%</div>
        </div>
      </div>

      {/* Chart Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-400">Chart Type:</span>
          {(['line', 'area', 'bar'] as const).map(type => (
            <button
              key={type}
              onClick={() => setChartType(type)}
              className={`px-3 py-1 rounded text-sm capitalize ${
                chartType === type
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Main Charts */}
      <div className="grid grid-cols-2 gap-6">
        {/* CPU & Memory Chart */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-white mb-4">CPU & Memory Usage</h3>
          <ResponsiveContainer width="100%" height={250}>
            {chartType === 'line' ? (
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={formatXAxis}
                  stroke="#9ca3af"
                  tick={{ fontSize: 12 }}
                />
                <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="cpu"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={false}
                  name="CPU %"
                />
                <Line
                  type="monotone"
                  dataKey="memory"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={false}
                  name="Memory %"
                />
              </LineChart>
            ) : chartType === 'area' ? (
              <AreaChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={formatXAxis}
                  stroke="#9ca3af"
                  tick={{ fontSize: 12 }}
                />
                <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="cpu"
                  stackId="1"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.6}
                  name="CPU %"
                />
                <Area
                  type="monotone"
                  dataKey="memory"
                  stackId="1"
                  stroke="#10b981"
                  fill="#10b981"
                  fillOpacity={0.6}
                  name="Memory %"
                />
              </AreaChart>
            ) : (
              <BarChart data={data.slice(-10)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={formatXAxis}
                  stroke="#9ca3af"
                  tick={{ fontSize: 12 }}
                />
                <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar dataKey="cpu" fill="#3b82f6" name="CPU %" />
                <Bar dataKey="memory" fill="#10b981" name="Memory %" />
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>

        {/* Latency Chart */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-white mb-4">Response Latency</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={formatXAxis}
                stroke="#9ca3af"
                tick={{ fontSize: 12 }}
              />
              <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Line
                type="monotone"
                dataKey="latency"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={false}
                name="Latency (ms)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Requests & Errors Chart */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-white mb-4">Requests & Errors</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={data.slice(-20)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={formatXAxis}
                stroke="#9ca3af"
                tick={{ fontSize: 12 }}
              />
              <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Bar dataKey="requests" fill="#8b5cf6" name="Requests" />
              <Bar dataKey="errors" fill="#ef4444" name="Errors" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Error Rate Pie Chart */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-white mb-4">Success vs Error Rate</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={[
                  { name: 'Success', value: 100 - metrics.errorRate },
                  { name: 'Errors', value: metrics.errorRate }
                ]}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                <Cell fill="#10b981" />
                <Cell fill="#ef4444" />
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default PerformanceChart;