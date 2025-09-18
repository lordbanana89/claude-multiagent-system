import React, { useState, useEffect, useCallback } from 'react';
import { Play, Stop, RefreshCw, Database, Activity, Terminal, CheckCircle, XCircle, AlertCircle, Users, Layers, Clock, Zap } from 'lucide-react';

interface MCPActivity {
  id: string;
  agent: string;
  timestamp: string;
  activity: string;
  category: string;
  status: string;
}

interface MCPComponent {
  id: string;
  name: string;
  type: string;
  owner: string;
  created_at: string;
}

interface AgentState {
  agent: string;
  last_seen: string;
  status: string;
  current_task: string;
}

interface MCPStats {
  total_activities: number;
  total_components: number;
  active_agents: number;
  conflicts_detected: number;
}

const MCPDashboard: React.FC = () => {
  const [activities, setActivities] = useState<MCPActivity[]>([]);
  const [components, setComponents] = useState<MCPComponent[]>([]);
  const [agentStates, setAgentStates] = useState<AgentState[]>([]);
  const [stats, setStats] = useState<MCPStats>({
    total_activities: 0,
    total_components: 0,
    active_agents: 0,
    conflicts_detected: 0
  });
  const [serverStatus, setServerStatus] = useState<'checking' | 'running' | 'stopped'>('checking');
  const [tmuxSessions, setTmuxSessions] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch MCP data from SQLite via API
  const fetchMCPData = useCallback(async () => {
    try {
      const response = await fetch('/api/mcp/status');
      const data = await response.json();

      setActivities(data.activities || []);
      setComponents(data.components || []);
      setAgentStates(data.agent_states || []);
      setStats(data.stats || {
        total_activities: 0,
        total_components: 0,
        active_agents: 0,
        conflicts_detected: 0
      });
      setServerStatus(data.server_running ? 'running' : 'stopped');
      setTmuxSessions(data.tmux_sessions || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching MCP data:', error);
      // Use mock data for development
      setActivities([
        { id: '1', agent: 'backend-api', timestamp: new Date().toISOString(), activity: 'Creating /api/auth endpoint', category: 'implementation', status: 'completed' },
        { id: '2', agent: 'database', timestamp: new Date().toISOString(), activity: 'Designing auth schema', category: 'planning', status: 'completed' },
        { id: '3', agent: 'frontend-ui', timestamp: new Date().toISOString(), activity: 'Building login form', category: 'implementation', status: 'in_progress' }
      ]);
      setComponents([
        { id: '1', name: '/api/auth', type: 'api', owner: 'backend-api', created_at: new Date().toISOString() },
        { id: '2', name: 'users_table', type: 'database', owner: 'database', created_at: new Date().toISOString() }
      ]);
      setAgentStates([
        { agent: 'backend-api', last_seen: new Date().toISOString(), status: 'active', current_task: 'Implementing JWT tokens' },
        { agent: 'database', last_seen: new Date().toISOString(), status: 'active', current_task: 'Creating indexes' },
        { agent: 'frontend-ui', last_seen: new Date().toISOString(), status: 'active', current_task: 'Styling login form' }
      ]);
      setStats({
        total_activities: 42,
        total_components: 8,
        active_agents: 3,
        conflicts_detected: 0
      });
      setServerStatus('running');
      setTmuxSessions(['claude-backend-api', 'claude-database', 'claude-frontend-ui']);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMCPData();

    if (autoRefresh) {
      const interval = setInterval(fetchMCPData, 2000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, fetchMCPData]);

  const startAgent = async (agentName: string) => {
    try {
      const response = await fetch('/api/mcp/start-agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_name: agentName })
      });
      if (response.ok) {
        fetchMCPData();
      }
    } catch (error) {
      console.error('Error starting agent:', error);
    }
  };

  const stopAgent = async (agentName: string) => {
    try {
      const response = await fetch('/api/mcp/stop-agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_name: agentName })
      });
      if (response.ok) {
        fetchMCPData();
      }
    } catch (error) {
      console.error('Error stopping agent:', error);
    }
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      'implementation': 'bg-blue-500',
      'planning': 'bg-purple-500',
      'testing': 'bg-green-500',
      'error': 'bg-red-500',
      'info': 'bg-gray-500',
      'completion': 'bg-emerald-500'
    };
    return colors[category] || 'bg-gray-500';
  };

  const getAgentColor = (agent: string) => {
    const colors: Record<string, string> = {
      'backend-api': 'text-blue-400',
      'database': 'text-purple-400',
      'frontend-ui': 'text-green-400',
      'testing': 'text-yellow-400'
    };
    return colors[agent] || 'text-gray-400';
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl animate-pulse">Loading MCP System...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Database className="w-8 h-8 text-blue-400" />
              <h1 className="text-2xl font-bold">MCP Control Center</h1>
              <span className={`ml-4 px-3 py-1 rounded-full text-sm font-medium ${
                serverStatus === 'running' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
              }`}>
                {serverStatus === 'running' ? 'MCP Active' : 'MCP Inactive'}
              </span>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`px-4 py-2 rounded-lg text-sm flex items-center gap-2 ${
                  autoRefresh ? 'bg-green-600 hover:bg-green-700' : 'bg-gray-600 hover:bg-gray-700'
                }`}
              >
                <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
                {autoRefresh ? 'Auto Refresh ON' : 'Auto Refresh OFF'}
              </button>

              <button
                onClick={fetchMCPData}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh Now
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="bg-gray-850 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="grid grid-cols-4 gap-4">
            <div className="flex items-center gap-3">
              <Activity className="w-5 h-5 text-blue-400" />
              <div>
                <div className="text-2xl font-bold">{stats.total_activities}</div>
                <div className="text-xs text-gray-400">Total Activities</div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Layers className="w-5 h-5 text-purple-400" />
              <div>
                <div className="text-2xl font-bold">{stats.total_components}</div>
                <div className="text-xs text-gray-400">Components</div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Users className="w-5 h-5 text-green-400" />
              <div>
                <div className="text-2xl font-bold">{stats.active_agents}</div>
                <div className="text-xs text-gray-400">Active Agents</div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-400" />
              <div>
                <div className="text-2xl font-bold">{stats.conflicts_detected}</div>
                <div className="text-xs text-gray-400">Conflicts</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-3 gap-6">

          {/* Agent Control Panel */}
          <div className="col-span-1">
            <div className="bg-gray-800 rounded-lg p-4">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Terminal className="w-5 h-5" />
                Agent Control
              </h2>

              <div className="space-y-2">
                {['backend-api', 'database', 'frontend-ui', 'testing'].map(agent => {
                  const state = agentStates.find(a => a.agent === agent);
                  const isActive = state && state.status === 'active';
                  const session = `claude-${agent}`;
                  const hasSession = tmuxSessions.includes(session);

                  return (
                    <div key={agent} className="bg-gray-700 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className={`font-medium ${getAgentColor(agent)}`}>
                          {agent}
                        </span>
                        <span className={`px-2 py-1 rounded text-xs ${
                          isActive ? 'bg-green-900 text-green-300' : 'bg-gray-600 text-gray-400'
                        }`}>
                          {isActive ? 'Active' : 'Inactive'}
                        </span>
                      </div>

                      {state && state.current_task && (
                        <div className="text-xs text-gray-400 mb-2">
                          Task: {state.current_task}
                        </div>
                      )}

                      <div className="flex gap-2">
                        <button
                          onClick={() => startAgent(agent)}
                          disabled={hasSession}
                          className={`flex-1 px-2 py-1 rounded text-xs flex items-center justify-center gap-1 ${
                            hasSession
                              ? 'bg-gray-600 text-gray-500 cursor-not-allowed'
                              : 'bg-green-600 hover:bg-green-700 text-white'
                          }`}
                        >
                          <Play className="w-3 h-3" />
                          Start
                        </button>

                        <button
                          onClick={() => stopAgent(agent)}
                          disabled={!hasSession}
                          className={`flex-1 px-2 py-1 rounded text-xs flex items-center justify-center gap-1 ${
                            !hasSession
                              ? 'bg-gray-600 text-gray-500 cursor-not-allowed'
                              : 'bg-red-600 hover:bg-red-700 text-white'
                          }`}
                        >
                          <Stop className="w-3 h-3" />
                          Stop
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-700">
                <button className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm flex items-center justify-center gap-2">
                  <Zap className="w-4 h-4" />
                  Start All Agents with MCP
                </button>
              </div>
            </div>

            {/* Components */}
            <div className="bg-gray-800 rounded-lg p-4 mt-4">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Layers className="w-5 h-5" />
                Registered Components
              </h2>

              <div className="space-y-2">
                {components.slice(0, 5).map(component => (
                  <div key={component.id} className="bg-gray-700 rounded p-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-blue-400">
                        {component.name}
                      </span>
                      <span className="text-xs text-gray-400">
                        {component.type}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      Owner: <span className={getAgentColor(component.owner)}>{component.owner}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Activity Stream */}
          <div className="col-span-2">
            <div className="bg-gray-800 rounded-lg p-4">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Activity Stream
              </h2>

              <div className="space-y-2 max-h-[600px] overflow-y-auto">
                {activities.map((activity, index) => (
                  <div
                    key={activity.id}
                    className="bg-gray-700 rounded-lg p-3 hover:bg-gray-650 transition-colors"
                    style={{
                      animation: index === 0 && autoRefresh ? 'slideIn 0.3s ease-out' : 'none'
                    }}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className={`font-medium ${getAgentColor(activity.agent)}`}>
                          {activity.agent}
                        </span>
                        <span className={`px-2 py-0.5 rounded-full text-xs ${getCategoryColor(activity.category)}`}>
                          {activity.category}
                        </span>
                      </div>
                      <span className="text-xs text-gray-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatTimestamp(activity.timestamp)}
                      </span>
                    </div>

                    <div className="text-sm text-gray-300">
                      {activity.activity}
                    </div>

                    {activity.status !== 'completed' && (
                      <div className="flex items-center gap-1 mt-2">
                        {activity.status === 'in_progress' ? (
                          <>
                            <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
                            <span className="text-xs text-yellow-400">In Progress</span>
                          </>
                        ) : activity.status === 'failed' ? (
                          <>
                            <XCircle className="w-3 h-3 text-red-400" />
                            <span className="text-xs text-red-400">Failed</span>
                          </>
                        ) : (
                          <>
                            <CheckCircle className="w-3 h-3 text-green-400" />
                            <span className="text-xs text-green-400">Completed</span>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
};

export default MCPDashboard;