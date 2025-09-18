import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

interface TaskResult {
  success: boolean;
  data?: any;
  error?: string;
  taskId?: string;
}

interface Agent {
  id: string;
  name: string;
  type: string;
  status: string;
}

const MissionControl: React.FC = () => {
  const [taskDescription, setTaskDescription] = useState('');
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [taskHistory, setTaskHistory] = useState<TaskResult[]>([]);
  const queryClient = useQueryClient();

  // Fetch available agents
  const { data: agents = [] } = useQuery<Agent[]>({
    queryKey: ['agents'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/agents`);
      return response.data;
    },
  });

  // Execute task mutation
  const executeTaskMutation = useMutation({
    mutationFn: async (task: { description: string; agents: string[] }) => {
      const response = await axios.post(`${API_URL}/api/tasks/execute`, task);
      return response.data;
    },
    onSuccess: (data) => {
      setTaskHistory([data, ...taskHistory]);
      setTaskDescription('');
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  // LangGraph execution mutation
  const executeLangGraphMutation = useMutation({
    mutationFn: async (task: string) => {
      const response = await axios.post(`${API_URL}/api/langgraph/execute`, {
        task: task,
      });
      return response.data;
    },
    onSuccess: (data) => {
      setTaskHistory([data, ...taskHistory]);
      setTaskDescription('');
    },
  });

  const handleExecuteTask = () => {
    if (taskDescription.trim()) {
      executeTaskMutation.mutate({
        description: taskDescription,
        agents: selectedAgents,
      });
    }
  };

  const handleExecuteLangGraph = () => {
    if (taskDescription.trim()) {
      executeLangGraphMutation.mutate(taskDescription);
    }
  };

  const toggleAgent = (agentId: string) => {
    setSelectedAgents(prev =>
      prev.includes(agentId)
        ? prev.filter(id => id !== agentId)
        : [...prev, agentId]
    );
  };

  return (
    <div className="p-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Task Input */}
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              📋 Mission Control
            </h2>

            {/* Task Description */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Task Description
              </label>
              <textarea
                value={taskDescription}
                onChange={(e) => setTaskDescription(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                rows={4}
                placeholder="Describe the task to coordinate across agents..."
              />
            </div>

            {/* Agent Selection */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Select Agents
              </label>
              <div className="grid grid-cols-2 gap-2">
                {agents.map(agent => (
                  <label
                    key={agent.id}
                    className={`flex items-center p-2 rounded-lg border cursor-pointer transition-colors ${
                      selectedAgents.includes(agent.id)
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedAgents.includes(agent.id)}
                      onChange={() => toggleAgent(agent.id)}
                      className="mr-2"
                    />
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {agent.name}
                    </span>
                    <span
                      className={`ml-auto w-2 h-2 rounded-full ${
                        agent.status === 'online' ? 'bg-green-500' : 'bg-gray-400'
                      }`}
                    />
                  </label>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-3">
              <button
                onClick={handleExecuteLangGraph}
                disabled={!taskDescription.trim() || executeLangGraphMutation.isPending}
                className="flex-1 bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {executeLangGraphMutation.isPending ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Executing...
                  </span>
                ) : (
                  '🚀 Execute via LangGraph'
                )}
              </button>
              <button
                onClick={handleExecuteTask}
                disabled={!taskDescription.trim() || selectedAgents.length === 0 || executeTaskMutation.isPending}
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {executeTaskMutation.isPending ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Executing...
                  </span>
                ) : (
                  '🎯 Execute Direct'
                )}
              </button>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              ⚡ Quick Actions
            </h3>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setTaskDescription('Check system status and health for all agents')}
                className="text-left p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
              >
                <span className="text-sm font-medium">🔍 System Check</span>
              </button>
              <button
                onClick={() => setTaskDescription('Generate daily activity report')}
                className="text-left p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
              >
                <span className="text-sm font-medium">📊 Daily Report</span>
              </button>
              <button
                onClick={() => setTaskDescription('Run automated tests suite')}
                className="text-left p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
              >
                <span className="text-sm font-medium">🧪 Run Tests</span>
              </button>
              <button
                onClick={() => setTaskDescription('Optimize database performance')}
                className="text-left p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
              >
                <span className="text-sm font-medium">⚙️ Optimize DB</span>
              </button>
            </div>
          </div>
        </div>

        {/* Right Column - Task History */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            📜 Task History
          </h3>
          <div className="space-y-3 max-h-[600px] overflow-y-auto">
            {taskHistory.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No tasks executed yet
              </div>
            ) : (
              taskHistory.map((task, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-lg border ${
                    task.success
                      ? 'border-green-200 bg-green-50 dark:bg-green-900/20'
                      : 'border-red-200 bg-red-50 dark:bg-red-900/20'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-1">
                        {task.success ? (
                          <span className="text-green-600 mr-2">✅</span>
                        ) : (
                          <span className="text-red-600 mr-2">❌</span>
                        )}
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          Task #{taskHistory.length - index}
                        </span>
                      </div>
                      {task.data && (
                        <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-x-auto">
                          {JSON.stringify(task.data, null, 2)}
                        </pre>
                      )}
                      {task.error && (
                        <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                          Error: {task.error}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MissionControl;