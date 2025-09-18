import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import axios from 'axios';
import AgentCard from './AgentCard';
import CommandPanel from './CommandPanel';

const API_URL = 'http://localhost:8000';

interface Agent {
  id: string;
  name: string;
  type: string;
  status: 'online' | 'offline' | 'busy' | 'error';
  sessionId: string;
  lastActivity: string;
}

const AgentDashboard: React.FC = () => {
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [commandHistory, setCommandHistory] = useState<Array<{
    agentId: string;
    command: string;
    timestamp: string;
    status: 'sent' | 'completed' | 'error';
  }>>([]);

  // Fetch agents
  const { data: agents = [], isLoading, error, refetch } = useQuery<Agent[]>({
    queryKey: ['agents'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/agents`);
      return response.data;
    },
    refetchInterval: 3000, // Refresh every 3 seconds
  });

  // Send command mutation
  const sendCommandMutation = useMutation({
    mutationFn: async ({ agentId, command }: { agentId: string; command: string }) => {
      const response = await axios.post(`${API_URL}/api/agents/${agentId}/command`, {
        agent_id: agentId,
        command: command,
      });
      return response.data;
    },
    onSuccess: (data, variables) => {
      setCommandHistory(prev => [{
        agentId: variables.agentId,
        command: variables.command,
        timestamp: new Date().toISOString(),
        status: 'sent'
      }, ...prev].slice(0, 20)); // Keep last 20 commands
      refetch();
    },
    onError: (error, variables) => {
      setCommandHistory(prev => [{
        agentId: variables.agentId,
        command: variables.command,
        timestamp: new Date().toISOString(),
        status: 'error'
      }, ...prev].slice(0, 20));
      console.error('Failed to send command:', error);
    },
  });

  const handleSendCommand = (command: string) => {
    if (selectedAgent && command.trim()) {
      sendCommandMutation.mutate({
        agentId: selectedAgent.id,
        command: command.trim(),
      });
    }
  };

  const getAgentsByType = (type: string) => {
    return agents.filter(agent => agent.type === type);
  };

  const agentTypes = [
    { type: 'coordinator', label: 'Coordination', color: 'purple' },
    { type: 'strategic', label: 'Strategic', color: 'red' },
    { type: 'development', label: 'Development', color: 'blue' },
    { type: 'database', label: 'Database', color: 'green' },
    { type: 'ui', label: 'UI/UX', color: 'yellow' },
    { type: 'qa', label: 'Testing', color: 'cyan' },
    { type: 'social', label: 'Social', color: 'pink' },
    { type: 'infrastructure', label: 'Infrastructure', color: 'indigo' },
    { type: 'devops', label: 'DevOps', color: 'gray' },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
        <strong>Error:</strong> Failed to load agents. Please check if the API is running.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Agent Grid */}
      <div className="lg:col-span-2">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Agent Status Dashboard
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 mb-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {agents.length}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Total</div>
            </div>
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {agents.filter(a => a.status === 'online').length}
              </div>
              <div className="text-sm text-green-600 dark:text-green-400">Online</div>
            </div>
            <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                {agents.filter(a => a.status === 'busy').length}
              </div>
              <div className="text-sm text-yellow-600 dark:text-yellow-400">Busy</div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-900/20 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-gray-600 dark:text-gray-400">
                {agents.filter(a => a.status === 'offline').length}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Offline</div>
            </div>
          </div>
        </div>

        {/* Agent Categories */}
        {agentTypes.map(({ type, label }) => {
          const typeAgents = getAgentsByType(type);
          if (typeAgents.length === 0) return null;

          return (
            <div key={type} className="mb-6">
              <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-3">
                {label} Agents
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {typeAgents.map(agent => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    isSelected={selectedAgent?.id === agent.id}
                    onClick={() => setSelectedAgent(agent)}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Command Panel */}
      <div className="lg:col-span-1">
        <CommandPanel
          selectedAgent={selectedAgent}
          onSendCommand={handleSendCommand}
          isLoading={sendCommandMutation.isPending}
          commandHistory={commandHistory}
        />
      </div>
    </div>
  );
};

export default AgentDashboard;