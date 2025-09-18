import React, { useState, useEffect, useCallback } from 'react';
// Terminal controls removed - using TMUX sessions instead
import { Database, Activity, CheckCircle, XCircle, RefreshCw, Zap, AlertCircle, Settings, Play, Power } from 'lucide-react';
import mcpCache from '../../services/mcpCache';
import './terminal-fix.css';

interface Agent {
  id: string;
  name: string;
  status: string;
  mcpEnabled?: boolean;
  lastActivity?: string;
  activitiesCount?: number;
}

interface MCPAgentStatus {
  connected: boolean;
  lastHeartbeat?: string;
  activitiesCount: number;
  currentTask?: string;
  syncStatus: 'connected' | 'syncing' | 'disconnected';
}

interface MultiTerminalProps {
  agents: Agent[];
}

interface MCPStatus {
  serverRunning: boolean;
  totalActivities: number;
  activeAgents: number;
  lastUpdate: string;
}

type LayoutMode = '1x1' | '2x1' | '2x2' | '3x3';

const MultiTerminal: React.FC<MultiTerminalProps> = ({ agents }) => {
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [layoutMode, setLayoutMode] = useState<LayoutMode>('2x2');
  const [fullscreenAgent, setFullscreenAgent] = useState<string | null>(null);
  const [mcpStatus, setMcpStatus] = useState<MCPStatus | null>(null);
  const [mcpActivities, setMcpActivities] = useState<any[]>([]);
  const [showMcpPanel, setShowMcpPanel] = useState(false);
  const [loading, setLoading] = useState(false);
  const [tmuxSessions, setTmuxSessions] = useState<string[]>([]);
  const [agentStates, setAgentStates] = useState<any[]>([]);
  const [terminalPorts, setTerminalPorts] = useState<{[key: string]: number}>({});
  const [agentMCPStatus, setAgentMCPStatus] = useState<{[key: string]: MCPAgentStatus}>({});

  // Terminal port mapping - comprehensive for all agents
  const TERMINAL_PORT_MAP: {[key: string]: number} = {
    'backend-api': 8090,
    'backend api agent': 8090,
    'backend-api-agent': 8090,
    'database': 8091,
    'database agent': 8091,
    'database-agent': 8091,
    'frontend-ui': 8092,
    'frontend ui agent': 8092,
    'frontend-ui-agent': 8092,
    'testing': 8093,
    'testing agent': 8093,
    'testing-agent': 8093,
    'instagram': 8094,
    'instagram agent': 8094,
    'instagram-agent': 8094,
    'supervisor': 8095,
    'supervisor agent': 8095,
    'supervisor-agent': 8095,
    'master': 8096,
    'master agent': 8096,
    'master-agent': 8096,
    'deployment': 8097,
    'deployment agent': 8097,
    'deployment-agent': 8097,
    'queue-manager': 8098,
    'queue manager agent': 8098,
    'queue-manager-agent': 8098
  };

  // Get terminal port for agent - more flexible matching
  const getTerminalPort = (agentName: string): number | null => {
    // Check if we have a dynamic port assignment
    if (terminalPorts[agentName]) {
      return terminalPorts[agentName];
    }

    // Try multiple normalized versions
    const normalizations = [
      agentName.toLowerCase(),
      agentName.toLowerCase().replace(/ agent$/i, ''),
      agentName.toLowerCase().replace(/ /g, '-'),
      agentName.toLowerCase().replace(/_/g, '-'),
      agentName.toLowerCase().replace(/ /g, '-').replace(/_/g, '-')
    ];

    for (const normalized of normalizations) {
      if (TERMINAL_PORT_MAP[normalized]) {
        return TERMINAL_PORT_MAP[normalized];
      }
    }

    return null;
  };

  // Get max agents based on layout
  const getMaxAgents = (layout: LayoutMode): number => {
    switch (layout) {
      case '1x1': return 1;
      case '2x1': return 2;
      case '2x2': return 4;
      case '3x3': return 9;
      default: return 4;
    }
  };

  // Get grid class based on layout
  const getGridClass = (layout: LayoutMode): string => {
    switch (layout) {
      case '1x1': return 'grid-cols-1 grid-rows-1';
      case '2x1': return 'grid-cols-2 grid-rows-1';
      case '2x2': return 'grid-cols-2 grid-rows-2';
      case '3x3': return 'grid-cols-3 grid-rows-3';
      default: return 'grid-cols-2 grid-rows-2';
    }
  };

  const toggleAgentSelection = (agentId: string) => {
    const maxAgents = getMaxAgents(layoutMode);

    if (selectedAgents.includes(agentId)) {
      setSelectedAgents(selectedAgents.filter(id => id !== agentId));
    } else if (selectedAgents.length < maxAgents) {
      setSelectedAgents([...selectedAgents, agentId]);
    } else {
      // Replace the oldest selection
      setSelectedAgents([...selectedAgents.slice(1), agentId]);
    }
  };

  const clearSelection = () => {
    setSelectedAgents([]);
  };

  const selectAll = () => {
    const maxAgents = getMaxAgents(layoutMode);
    setSelectedAgents(agents.slice(0, maxAgents).map(a => a.id));
  };

  const toggleFullscreen = (agentId: string) => {
    setFullscreenAgent(fullscreenAgent === agentId ? null : agentId);
  };

  // Check which ttyd terminals are running
  const checkTerminalPorts = useCallback(async () => {
    // Disabled terminal port checking to prevent ERR_INSUFFICIENT_RESOURCES
    // The terminals are known to be on ports 8090-8098
    // We'll use the static port map instead of checking availability
    setTerminalPorts(TERMINAL_PORT_MAP);
    return;

    /* Original code - disabled due to too many requests
    const activePorts: {[key: string]: number} = {};
    for (const [name, port] of Object.entries(TERMINAL_PORT_MAP)) {
      try {
        const response = await fetch(`http://localhost:${port}/`, {
          method: 'HEAD',
          mode: 'no-cors'
        });
        activePorts[name] = port;
      } catch {
        // Terminal not available on this port
      }
    }
    setTerminalPorts(activePorts);
    */
  }, []);

  // Calculate MCP status for each agent
  const calculateAgentMCPStatus = useCallback((agentName: string): MCPAgentStatus => {
    const normalizedName = agentName.toLowerCase().replace(/ agent$/i, '').replace(/ /g, '-');

    // Find agent state - check multiple formats
    const agentState = agentStates.find(s => {
      const stateAgentName = s.agent?.toLowerCase() || '';
      return stateAgentName === normalizedName ||
             stateAgentName === agentName.toLowerCase() ||
             stateAgentName.includes(normalizedName) ||
             normalizedName.includes(stateAgentName);
    });

    // Count activities for this agent
    const agentActivities = mcpActivities.filter(a =>
      a.agent && (a.agent.toLowerCase() === normalizedName ||
                  a.agent.toLowerCase() === agentName.toLowerCase() ||
                  a.agent.toLowerCase().includes(normalizedName))
    );

    // For now, consider connected if we have the agent state and server is running
    // Since we're using static mock data from the server
    const isConnected = agentState && agentState.connected !== false;

    // Determine sync status based on agent state
    let syncStatus: 'connected' | 'syncing' | 'disconnected' = 'disconnected';
    if (isConnected) {
      syncStatus = agentState.status === 'active' ? 'connected' : 'syncing';
    } else if (mcpStatus?.serverRunning) {
      syncStatus = 'syncing';
    }

    return {
      connected: isConnected || false,
      lastHeartbeat: agentState?.lastActivity || agentState?.last_seen || new Date().toISOString(),
      activitiesCount: agentActivities.length,
      currentTask: agentState?.current_task || agentState?.currentTask,
      syncStatus
    };
  }, [agentStates, mcpActivities, mcpStatus]);

  // Fetch agent states from MCP
  const fetchAgentStates = useCallback(async () => {
    try {
      const mcpApiUrl = import.meta.env.VITE_MCP_API_URL || 'http://localhost:8099';
      const response = await fetch(`${mcpApiUrl}/api/mcp/agent-states`);
      if (response.ok) {
        const states = await response.json();
        // Convert object to array if needed
        if (!Array.isArray(states)) {
          const statesArray = Object.entries(states).map(([key, value]: [string, any]) => ({
            agent: key,
            ...value
          }));
          setAgentStates(statesArray);
        } else {
          setAgentStates(states);
        }
      }
    } catch (error) {
      console.error('Failed to fetch agent states:', error);
    }
  }, []);

  // Fetch activities from MCP
  const fetchActivities = useCallback(async () => {
    try {
      const mcpApiUrl = import.meta.env.VITE_MCP_API_URL || 'http://localhost:8099';
      const response = await fetch(`${mcpApiUrl}/api/mcp/activities?limit=50`);
      if (response.ok) {
        const data = await response.json();
        setMcpActivities(data.activities || data || []);
      }
    } catch (error) {
      console.error('Failed to fetch activities:', error);
    }
  }, []);

  // Fetch MCP status with caching
  const fetchMCPStatus = useCallback(async () => {
    try {
      setLoading(true);
      const mcpApiUrl = import.meta.env.VITE_MCP_API_URL || 'http://localhost:8099';

      // Use cache service to prevent duplicate requests
      const data = await mcpCache.fetch('mcp-status', async () => {
        const response = await fetch(`${mcpApiUrl}/api/mcp/status`);
        if (!response.ok) throw new Error('Failed to fetch status');
        return response.json();
      }, 5000); // 5 second cache

      if (data) {
        setMcpStatus({
          serverRunning: data.status === 'operational',
          totalActivities: data.stats?.activities_total || 0,
          activeAgents: data.stats?.agents_online || 0,
          lastUpdate: new Date().toISOString()
        });
        setMcpActivities(data.activities || []);
        setTmuxSessions(data.tmux_sessions || []);
        setAgentStates(data.agent_states || []);

        // Update MCP status for each agent
        const newAgentMCPStatus: {[key: string]: MCPAgentStatus} = {};
        agents.forEach(agent => {
          newAgentMCPStatus[agent.name] = calculateAgentMCPStatus(agent.name);
        });
        setAgentMCPStatus(newAgentMCPStatus);
      }
    } catch (error) {
      console.error('Failed to fetch MCP status:', error);
    } finally {
      setLoading(false);
    }
  }, [agents, calculateAgentMCPStatus]);

  // Setup agent with proper MCP configuration
  const setupAgentMCP = async (agentName: string) => {
    try {
      // Setup MCP environment for the agent
      const mcpApiUrl = import.meta.env.VITE_MCP_API_URL || 'http://localhost:8099';
      const response = await fetch(`${mcpApiUrl}/api/mcp/setup-agent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_name: agentName,
          setup_mcp: true,
          mcp_config: {
            db_path: '/tmp/mcp_state.db',
            project_dir: '/Users/erik/Desktop/claude-multiagent-system',
            enable_hooks: true,
            enable_bridge: true
          }
        })
      });

      if (response.ok) {
        console.log(`MCP setup completed for ${agentName}`);
        // Refresh status after setup
        setTimeout(() => {
          fetchMCPStatus();
          checkTerminalPorts();
        }, 1000);
      }
    } catch (error) {
      console.error('Failed to setup MCP:', error);
    }
  };

  // Start terminal ttyd service manually
  const startTerminalService = async (agentName: string) => {
    try {
      const mcpApiUrl = import.meta.env.VITE_MCP_API_URL || 'http://localhost:8099';
      const response = await fetch(`${mcpApiUrl}/api/mcp/start-terminal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_name: agentName })
      });

      if (response.ok) {
        console.log(`Terminal service started for ${agentName}`);
        // Wait a bit then check port availability
        setTimeout(() => {
          checkTerminalPorts();
        }, 2000);
      } else {
        console.error('Failed to start terminal service');
      }
    } catch (error) {
      console.error('Failed to start terminal service:', error);
    }
  };

  // Start agent with MCP
  const startAgentWithMCP = async (agentName: string) => {
    try {
      // First setup MCP
      await setupAgentMCP(agentName);

      // Then start the agent
      const mcpApiUrl = import.meta.env.VITE_MCP_API_URL || 'http://localhost:8099';
      const response = await fetch(`${mcpApiUrl}/api/mcp/start-agent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_name: agentName })
      });
      if (response.ok) {
        fetchMCPStatus();
        console.log(`Agent ${agentName} started with MCP enabled`);
      }
    } catch (error) {
      console.error('Failed to start agent:', error);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchMCPStatus();
    fetchAgentStates();
    fetchActivities();
    checkTerminalPorts();

    // Set up polling interval
    const interval = setInterval(() => {
      fetchMCPStatus();
      fetchAgentStates();
      fetchActivities();
      checkTerminalPorts();
    }, 10000); // Reduced frequency to avoid rate limiting

    return () => clearInterval(interval);
  }, [fetchMCPStatus, fetchAgentStates, fetchActivities, checkTerminalPorts]); // Dependencies

  if (fullscreenAgent) {
    const agent = agents.find(a => a.id === fullscreenAgent);
    if (!agent) return null;

    return (
      <div className="h-full flex flex-col bg-gray-900">
        <div className="bg-gray-800 border-b border-gray-700 p-3 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">
            {agent.name} - Fullscreen Terminal
          </h3>
          <button
            onClick={() => toggleFullscreen(agent.id)}
            className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm"
          >
            ❌ Exit Fullscreen
          </button>
        </div>
        <div className="flex-1">
          {getTerminalPort(agent.name) ? (
            <iframe
              src={`http://localhost:${getTerminalPort(agent.name)}`}
              className="w-full h-full"
              style={{ border: 'none' }}
              title={`${agent.name} Terminal - Fullscreen`}
            />
          ) : (
            <div className="w-full h-full bg-black p-6 font-mono text-green-400">
              <div className="text-xl mb-4">TMUX Session: claude-{agent.name}</div>
              <div className="text-yellow-400">Terminal not available</div>
              <div className="mt-4 text-white">Start ttyd for this agent:</div>
              <div className="mt-2 bg-gray-900 p-3 rounded text-sm">
                ttyd -p {TERMINAL_PORT_MAP[agent.name] || 8099} --writable tmux attach -t claude-{agent.name}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex bg-gray-900">
      {/* Sidebar */}
      <div className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
        {/* MCP Status Bar */}
        <div className="bg-gray-900 border-b border-gray-700 p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-blue-400" />
              <span className="text-sm font-medium text-white">MCP Status</span>
            </div>
            <button
              onClick={() => setShowMcpPanel(!showMcpPanel)}
              className="text-gray-400 hover:text-white"
            >
              <AlertCircle className="w-4 h-4" />
            </button>
          </div>
          {mcpStatus ? (
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">Server:</span>
                <span className={mcpStatus.serverRunning ? 'text-green-400' : 'text-red-400'}>
                  {mcpStatus.serverRunning ? 'Running' : 'Stopped'}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">Activities:</span>
                <span className="text-blue-400">{mcpStatus.totalActivities}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">Active:</span>
                <span className="text-green-400">{mcpStatus.activeAgents} agents</span>
              </div>
            </div>
          ) : (
            <div className="text-xs text-gray-500">Loading...</div>
          )}
          <button
            onClick={fetchMCPStatus}
            className="w-full mt-2 px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs flex items-center justify-center gap-1"
          >
            <RefreshCw className="w-3 h-3" />
            Refresh MCP
          </button>
        </div>

        <div className="p-4 border-b border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-3">Multi-Terminal</h3>

          {/* Layout Selector */}
          <div className="mb-3">
            <label className="text-xs text-gray-400 block mb-1">Layout</label>
            <select
              value={layoutMode}
              onChange={(e) => setLayoutMode(e.target.value as LayoutMode)}
              className="w-full px-2 py-1 bg-gray-700 text-white rounded text-sm border border-gray-600"
            >
              <option value="1x1">1×1 (Single)</option>
              <option value="2x1">2×1 (Horizontal)</option>
              <option value="2x2">2×2 (Grid)</option>
              <option value="3x3">3×3 (Large Grid)</option>
            </select>
          </div>

          {/* Quick Actions */}
          <div className="flex gap-2">
            <button
              onClick={selectAll}
              className="flex-1 px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs"
            >
              Select All
            </button>
            <button
              onClick={clearSelection}
              className="flex-1 px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded text-xs"
            >
              Clear
            </button>
          </div>
        </div>

        {/* Agent List */}
        <div className="flex-1 overflow-y-auto p-3">
          <p className="text-xs text-gray-400 mb-2">
            Select up to {getMaxAgents(layoutMode)} agents
          </p>
          <div className="space-y-1">
            {agents.map(agent => {
              const isSelected = selectedAgents.includes(agent.id);
              const canSelect = isSelected || selectedAgents.length < getMaxAgents(layoutMode);

              return (
                <button
                  key={agent.id}
                  onClick={() => toggleAgentSelection(agent.id)}
                  disabled={!canSelect}
                  className={`w-full p-2 rounded text-left text-sm transition-colors ${
                    isSelected
                      ? 'bg-blue-600 text-white'
                      : canSelect
                      ? 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      : 'bg-gray-700 text-gray-500 cursor-not-allowed opacity-50'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span>{agent.name}</span>
                      <div className="flex items-center gap-1">
                        {agent.mcpEnabled && (
                          <Database className="w-3 h-3 text-blue-400" title="MCP Enabled" />
                        )}
                        <span className={`w-2 h-2 rounded-full ${
                          agent.status === 'online' ? 'bg-green-500' :
                          agent.status === 'busy' ? 'bg-yellow-500' :
                          'bg-gray-500'
                        }`}></span>
                      </div>
                    </div>
                    {agent.lastActivity && (
                      <div className="text-xs text-gray-500 mt-1 truncate">
                        {agent.lastActivity}
                      </div>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Status */}
        <div className="p-3 border-t border-gray-700 text-xs text-gray-400">
          Selected: {selectedAgents.length}/{getMaxAgents(layoutMode)}
        </div>
      </div>

      {/* Terminal Grid */}
      <div className="flex-1 p-4">
        {selectedAgents.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <p className="text-gray-400 mb-2">No terminals selected</p>
              <p className="text-gray-500 text-sm">Select agents from the sidebar</p>
            </div>
          </div>
        ) : (
          <div className={`grid ${getGridClass(layoutMode)} gap-4 h-full`}>
            {selectedAgents.map(agentId => {
              const agent = agents.find(a => a.id === agentId);
              if (!agent) return null;

              return (
                <div
                  key={agentId}
                  className="bg-gray-800 rounded-lg overflow-hidden flex flex-col"
                >
                  {/* Terminal Header */}
                  <div className="bg-gray-700 p-2 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-white">
                        {agent.name}
                      </span>
                      {/* MCP Connection Status Badge */}
                      {(() => {
                        const mcpState = agentMCPStatus[agent.name];
                        if (!mcpState) return null;

                        return (
                          <div className="flex items-center gap-2">
                            <span className={`px-2 py-0.5 text-white text-xs rounded flex items-center gap-1 ${
                              mcpState.syncStatus === 'connected' ? 'bg-green-600' :
                              mcpState.syncStatus === 'syncing' ? 'bg-yellow-600' :
                              'bg-red-600'
                            }`}>
                              <Database className="w-3 h-3" />
                              MCP: {mcpState.syncStatus === 'connected' ? 'Connected' :
                                    mcpState.syncStatus === 'syncing' ? 'Syncing' : 'Disconnected'}
                            </span>
                            {mcpState.activitiesCount > 0 && (
                              <span className="text-xs text-gray-400">
                                {mcpState.activitiesCount} activities
                              </span>
                            )}
                          </div>
                        );
                      })()}
                    </div>
                    <div className="flex items-center space-x-1">
                      <button
                        onClick={() => startTerminalService(agent.name)}
                        className="p-1 hover:bg-gray-600 rounded text-green-400 hover:text-green-300"
                        title="Start Terminal Service"
                      >
                        <Power className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setupAgentMCP(agent.name)}
                        className="p-1 hover:bg-gray-600 rounded text-blue-400 hover:text-blue-300"
                        title="Setup MCP Configuration"
                      >
                        <Settings className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => startAgentWithMCP(agent.name)}
                        className="p-1 hover:bg-gray-600 rounded text-yellow-400 hover:text-yellow-300"
                        title="Start Agent with MCP"
                      >
                        <Zap className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => toggleFullscreen(agentId)}
                        className="p-1 hover:bg-gray-600 rounded text-gray-400 hover:text-white"
                        title="Fullscreen"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M4 8V4m0 0h4M4 4l5 5m11-5h-4m4 0v4m0-4l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5h-4m4 0v-4" />
                        </svg>
                      </button>
                      <button
                        onClick={() => toggleAgentSelection(agentId)}
                        className="p-1 hover:bg-gray-600 rounded text-gray-400 hover:text-white"
                        title="Remove"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>

                  {/* Terminal Content - Always show iframe for known ports */}
                  <div className="flex-1 relative bg-black overflow-hidden">
                    {(() => {
                      const port = getTerminalPort(agent.name);
                      const mcpState = agentMCPStatus[agent.name];

                      // Always try to show iframe if we have a port mapping
                      if (port) {
                        return (
                          <>
                            <iframe
                              key={`terminal-${agent.name}-${port}`}
                              src={`http://localhost:${port}`}
                              className="w-full h-full"
                              style={{ border: 'none', background: '#000' }}
                              title={`${agent.name} Terminal`}
                              referrerPolicy="no-referrer"
                              allow="fullscreen"
                              onLoad={() => {
                                console.log(`Terminal loaded: ${agent.name} on port ${port}`);
                              }}
                              onError={(e) => {
                                console.log(`Terminal reconnecting: ${agent.name}`);
                              }}
                            />
                            {/* MCP Status Overlay */}
                            {mcpState && (
                              <div className="absolute top-2 right-2 bg-black bg-opacity-75 rounded-lg p-2 text-xs">
                                <div className={`flex items-center gap-1 mb-1 ${
                                  mcpState.syncStatus === 'connected' ? 'text-green-400' :
                                  mcpState.syncStatus === 'syncing' ? 'text-yellow-400' :
                                  'text-red-400'
                                }`}>
                                  <div className={`w-2 h-2 rounded-full ${
                                    mcpState.syncStatus === 'connected' ? 'bg-green-400 animate-pulse' :
                                    mcpState.syncStatus === 'syncing' ? 'bg-yellow-400 animate-pulse' :
                                    'bg-red-400'
                                  }`} />
                                  MCP {mcpState.syncStatus}
                                </div>
                                {mcpState.lastHeartbeat && (
                                  <div className="text-gray-400">
                                    Last: {new Date(mcpState.lastHeartbeat).toLocaleTimeString()}
                                  </div>
                                )}
                                {mcpState.currentTask && (
                                  <div className="text-blue-400 mt-1 truncate max-w-xs">
                                    Task: {mcpState.currentTask}
                                  </div>
                                )}
                              </div>
                            )}
                          </>
                        );
                      }
                      // No port mapping available
                      return (
                        <div className="p-4 font-mono text-xs text-green-400">
                          <div className="mb-2 text-gray-400">
                            {`# Agent: ${agent.name}`}
                          </div>
                          <div className="mb-2">
                            <span className="text-yellow-400">⚠ No terminal port configured</span>
                            <br />
                            <span className="text-gray-500">This agent doesn't have a terminal port assigned</span>
                          </div>
                        </div>
                      );
                    })()}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* MCP Activity Panel (Overlay) */}
      {showMcpPanel && (
        <div className="absolute top-0 right-0 w-96 h-full bg-gray-800 border-l border-gray-700 shadow-xl z-50">
          <div className="p-4 border-b border-gray-700 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-400" />
              MCP Activities
            </h3>
            <button
              onClick={() => setShowMcpPanel(false)}
              className="text-gray-400 hover:text-white"
            >
              <XCircle className="w-5 h-5" />
            </button>
          </div>
          <div className="p-4 overflow-y-auto h-full">
            {mcpActivities.length > 0 ? (
              <div className="space-y-2">
                {mcpActivities.map((activity, index) => (
                  <div key={index} className="bg-gray-700 rounded p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-blue-400">
                        {activity.agent}
                      </span>
                      <span className="text-xs text-gray-400">
                        {new Date(activity.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="text-sm text-gray-300">
                      {activity.activity}
                    </div>
                    <div className="mt-1">
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        activity.category === 'implementation' ? 'bg-blue-900 text-blue-300' :
                        activity.category === 'planning' ? 'bg-purple-900 text-purple-300' :
                        activity.category === 'testing' ? 'bg-green-900 text-green-300' :
                        'bg-gray-600 text-gray-300'
                      }`}>
                        {activity.category}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-gray-400">
                No recent activities
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MultiTerminal;