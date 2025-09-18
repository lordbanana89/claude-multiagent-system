import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

interface Terminal {
  agentId: string;
  port: number;
  url: string;
  status: 'running' | 'stopped';
}

interface Agent {
  id: string;
  name: string;
  type: string;
  status: string;
  terminal?: Terminal;
}

const TerminalView: React.FC = () => {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [command, setCommand] = useState('');
  const [terminals, setTerminals] = useState<Map<string, Terminal>>(new Map());
  const queryClient = useQueryClient();
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Fetch agents
  const { data: agents = [] } = useQuery<Agent[]>({
    queryKey: ['agents'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/agents`);
      return response.data;
    },
    refetchInterval: 5000,
  });

  // Start terminal mutation
  const startTerminalMutation = useMutation({
    mutationFn: async (agentId: string) => {
      const response = await axios.post(`${API_URL}/api/agents/${agentId}/terminal/start`);
      return response.data;
    },
    onSuccess: (data, agentId) => {
      const terminal: Terminal = {
        agentId,
        port: data.port,
        url: data.url,
        status: 'running'
      };
      setTerminals(prev => new Map(prev).set(agentId, terminal));
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  // Stop terminal mutation
  const stopTerminalMutation = useMutation({
    mutationFn: async (agentId: string) => {
      await axios.post(`${API_URL}/api/agents/${agentId}/terminal/stop`);
    },
    onSuccess: (_, agentId) => {
      setTerminals(prev => {
        const next = new Map(prev);
        next.delete(agentId);
        return next;
      });
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  // Send command mutation
  const sendCommandMutation = useMutation({
    mutationFn: async ({ agentId, command }: { agentId: string; command: string }) => {
      const response = await axios.post(`${API_URL}/api/agents/${agentId}/command`, {
        command,
      });
      return response.data;
    },
    onSuccess: () => {
      setCommand('');
    },
  });

  const handleStartTerminal = (agentId: string) => {
    startTerminalMutation.mutate(agentId);
  };

  const handleStopTerminal = (agentId: string) => {
    stopTerminalMutation.mutate(agentId);
  };

  const handleSendCommand = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedAgent && command.trim()) {
      sendCommandMutation.mutate({ agentId: selectedAgent, command });
    }
  };

  const getTerminalUrl = (agentId: string) => {
    const terminal = terminals.get(agentId);
    if (terminal) {
      return terminal.url;
    }
    // Default ttyd port calculation
    const agentIndex = agents.findIndex(a => a.id === agentId);
    const port = 8090 + agentIndex;
    return `http://localhost:${port}`;
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex bg-gray-50 dark:bg-gray-900 rounded-lg overflow-hidden">
      {/* Left sidebar - Agent list */}
      <div className="w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
        <div className="p-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            🖥️ Agent Terminals
          </h2>

          <div className="space-y-3">
            {agents.map((agent) => {
              const terminal = terminals.get(agent.id);
              const isRunning = terminal?.status === 'running';

              return (
                <div
                  key={agent.id}
                  className={`p-3 rounded-lg border-2 transition-all cursor-pointer ${
                    selectedAgent === agent.id
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedAgent(agent.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">🤖</span>
                      <div>
                        <div className="font-semibold text-gray-900 dark:text-white">
                          {agent.name}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {agent.id}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          isRunning ? 'bg-green-500' : 'bg-gray-400'
                        }`}
                      />
                      {isRunning ? (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStopTerminal(agent.id);
                          }}
                          className="px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600"
                        >
                          Stop
                        </button>
                      ) : (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStartTerminal(agent.id);
                          }}
                          className="px-2 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600"
                        >
                          Start
                        </button>
                      )}
                    </div>
                  </div>

                  {isRunning && (
                    <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                      Port: {terminal.port}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Quick Actions */}
          <div className="mt-6 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Quick Actions
            </h3>
            <div className="space-y-2">
              <button
                onClick={() => agents.forEach(a => handleStartTerminal(a.id))}
                className="w-full px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm"
              >
                ▶️ Start All Terminals
              </button>
              <button
                onClick={() => agents.forEach(a => handleStopTerminal(a.id))}
                className="w-full px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm"
              >
                ⏹️ Stop All Terminals
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main content - Terminal display */}
      <div className="flex-1 flex flex-col bg-black">
        {selectedAgent ? (
          <>
            {/* Terminal header */}
            <div className="bg-gray-900 text-white p-3 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="text-green-400">●</span>
                <span className="font-mono text-sm">
                  {agents.find(a => a.id === selectedAgent)?.name} Terminal
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => {
                    if (iframeRef.current) {
                      iframeRef.current.src = getTerminalUrl(selectedAgent);
                    }
                  }}
                  className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                >
                  🔄 Refresh
                </button>
                <button
                  onClick={() => window.open(getTerminalUrl(selectedAgent), '_blank')}
                  className="px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700"
                >
                  🔗 Open External
                </button>
              </div>
            </div>

            {/* Terminal iframe */}
            {terminals.get(selectedAgent)?.status === 'running' ? (
              <iframe
                ref={iframeRef}
                src={getTerminalUrl(selectedAgent)}
                className="flex-1 w-full"
                title={`Terminal for ${selectedAgent}`}
              />
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                <div className="text-center">
                  <div className="text-6xl mb-4">📺</div>
                  <div className="text-xl">Terminal not running</div>
                  <button
                    onClick={() => handleStartTerminal(selectedAgent)}
                    className="mt-4 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    Start Terminal
                  </button>
                </div>
              </div>
            )}

            {/* Command input */}
            <form onSubmit={handleSendCommand} className="bg-gray-900 p-3">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  placeholder="Enter command..."
                  className="flex-1 px-3 py-2 bg-black text-green-400 font-mono rounded border border-gray-700 focus:border-green-500 focus:outline-none"
                />
                <button
                  type="submit"
                  disabled={!command.trim() || sendCommandMutation.isPending}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed"
                >
                  Send
                </button>
              </div>
            </form>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <div className="text-6xl mb-4">🖥️</div>
              <div className="text-xl">Select an agent to view its terminal</div>
            </div>
          </div>
        )}
      </div>

      {/* Right sidebar - Terminal stats */}
      <div className="w-64 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 p-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          📊 Terminal Stats
        </h3>

        <div className="space-y-4">
          <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="text-sm text-gray-600 dark:text-gray-400">Active Terminals</div>
            <div className="text-2xl font-bold text-green-600">{terminals.size}</div>
          </div>

          <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="text-sm text-gray-600 dark:text-gray-400">Total Agents</div>
            <div className="text-2xl font-bold text-blue-600">{agents.length}</div>
          </div>

          <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="text-sm text-gray-600 dark:text-gray-400">Commands Sent</div>
            <div className="text-2xl font-bold text-purple-600">0</div>
          </div>
        </div>

        {/* Recent commands */}
        <div className="mt-6">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
            Recent Commands
          </h4>
          <div className="space-y-2 text-xs">
            <div className="p-2 bg-gray-50 dark:bg-gray-700 rounded">
              <div className="font-mono text-gray-600 dark:text-gray-400">
                No commands sent yet
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TerminalView;