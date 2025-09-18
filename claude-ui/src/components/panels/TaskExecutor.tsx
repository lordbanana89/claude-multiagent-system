import React, { useState } from 'react';
import axios from 'axios';
import { config } from '../../config';
import { getErrorMessage, logError } from '../../utils/error-handler';

interface TaskExecutorProps {
  agents: any[];
  selectedAgent: any;
  onSelectAgent: (agent: any) => void;
}

const TaskExecutor: React.FC<TaskExecutorProps> = ({ agents, selectedAgent, onSelectAgent }) => {
  const [taskInput, setTaskInput] = useState({ name: '', description: '', priority: 'normal' });
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<any>(null);

  const executeTask = async () => {
    if (!taskInput.name || !taskInput.description) {
      alert('Please provide task name and description');
      return;
    }

    setLoading(true);
    setResponse(null);

    try {
      const res = await axios.post(`${config.API_URL}/api/tasks/execute`, {
        name: taskInput.name,
        description: taskInput.description,
        agent_id: selectedAgent?.id,
        priority: taskInput.priority
      });

      setResponse(res.data);
      setTaskInput({ name: '', description: '', priority: 'normal' });
    } catch (err) {
      const errorMsg = getErrorMessage(err);
      logError('executeTask', err);
      setResponse({ error: errorMsg });
    } finally {
      setLoading(false);
    }
  };

  const delegateToAgent = async (agentId: string) => {
    setLoading(true);
    try {
      const res = await axios.post(`${config.API_URL}/api/agents/${agentId}/delegate`, {
        task: taskInput.description,
        priority: taskInput.priority
      });
      setResponse(res.data);
    } catch (err) {
      const errorMsg = getErrorMessage(err);
      setResponse({ error: errorMsg });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 border-b border-gray-700">
      <h2 className="text-lg font-semibold text-white mb-3">Execute Task</h2>

      {/* Agent Selector */}
      <div className="mb-3">
        <label className="text-xs text-gray-400 block mb-1">Target Agent</label>
        <select
          value={selectedAgent?.id || ''}
          onChange={(e) => {
            const agent = agents.find(a => a.id === e.target.value);
            onSelectAgent(agent);
          }}
          className="w-full px-3 py-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
        >
          <option value="">Auto-assign (Supervisor)</option>
          {agents.map(agent => (
            <option key={agent.id} value={agent.id}>
              {agent.name} ({agent.status})
            </option>
          ))}
        </select>
      </div>

      {/* Task Name */}
      <input
        type="text"
        placeholder="Task name"
        value={taskInput.name}
        onChange={(e) => setTaskInput({ ...taskInput, name: e.target.value })}
        className="w-full px-3 py-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none mb-2"
      />

      {/* Task Description */}
      <textarea
        placeholder="Task description"
        value={taskInput.description}
        onChange={(e) => setTaskInput({ ...taskInput, description: e.target.value })}
        className="w-full px-3 py-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none mb-2 h-20 resize-none"
      />

      {/* Priority Selector */}
      <div className="flex gap-2 mb-3">
        {['low', 'normal', 'high', 'critical'].map(priority => (
          <button
            key={priority}
            onClick={() => setTaskInput({ ...taskInput, priority })}
            className={`px-3 py-1 rounded text-xs capitalize ${
              taskInput.priority === priority
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {priority}
          </button>
        ))}
      </div>

      {/* Execute Button */}
      <button
        onClick={executeTask}
        disabled={loading}
        className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded transition-colors font-medium mb-2"
      >
        {loading ? '⏳ Executing...' : '🚀 Execute Task'}
      </button>

      {/* Quick Delegation Buttons */}
      {selectedAgent?.id === 'supervisor' && (
        <div className="mt-3">
          <p className="text-xs text-gray-400 mb-2">Quick Delegation:</p>
          <div className="grid grid-cols-2 gap-2">
            {agents.filter(a => a.id !== 'supervisor' && a.id !== 'master').map(agent => (
              <button
                key={agent.id}
                onClick={() => delegateToAgent(agent.id)}
                disabled={loading || !taskInput.description}
                className="px-2 py-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-xs text-white rounded"
              >
                → {agent.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Response Display */}
      {response && (
        <div className={`mt-3 p-2 rounded text-xs ${
          response.error ? 'bg-red-900/50 text-red-200' : 'bg-green-900/50 text-green-200'
        }`}>
          {response.error ? `❌ ${response.error}` : `✅ Task ID: ${response.task_id || response.id}`}
        </div>
      )}
    </div>
  );
};

export default TaskExecutor;