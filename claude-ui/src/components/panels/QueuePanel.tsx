import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { config } from '../../config';
import { getErrorMessage, logError } from '../../utils/error-handler';

interface QueueTask {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  priority: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  retries: number;
  actor?: string;
  error?: string;
}

interface QueueStats {
  total: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  avgProcessingTime: number;
}

interface QueuePanelProps {
  tasks?: QueueTask[];
  queueStatus?: any;
  agents: any[];
}

const QueuePanel: React.FC<QueuePanelProps> = ({ agents }) => {
  const [tasks, setTasks] = useState<QueueTask[]>([]);
  const [stats, setStats] = useState<QueueStats>({
    total: 0,
    pending: 0,
    processing: 0,
    completed: 0,
    failed: 0,
    avgProcessingTime: 0
  });
  const [selectedTask, setSelectedTask] = useState<QueueTask | null>(null);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(false);

  // Fetch queue data
  const fetchQueueData = async () => {
    try {
      const [tasksRes, statsRes] = await Promise.all([
        axios.get(`${config.API_URL}/api/queue/tasks`),
        axios.get(`${config.API_URL}/api/queue/stats`)
      ]);

      setTasks(tasksRes.data);
      setStats(statsRes.data);
    } catch (err) {
      logError('fetchQueueData', err);
    }
  };

  useEffect(() => {
    fetchQueueData();
    const interval = setInterval(fetchQueueData, 3000);
    return () => clearInterval(interval);
  }, []);

  // Retry task
  const retryTask = async (taskId: string) => {
    setLoading(true);
    try {
      await axios.post(`${config.API_URL}/api/queue/tasks/${taskId}/retry`);
      fetchQueueData();
    } catch (err) {
      logError('retryTask', err);
    } finally {
      setLoading(false);
    }
  };

  // Cancel task
  const cancelTask = async (taskId: string) => {
    setLoading(true);
    try {
      await axios.delete(`${config.API_URL}/api/queue/tasks/${taskId}`);
      setSelectedTask(null);
      fetchQueueData();
    } catch (err) {
      logError('cancelTask', err);
    } finally {
      setLoading(false);
    }
  };

  // Clear completed tasks
  const clearCompleted = async () => {
    setLoading(true);
    try {
      await axios.post(`${config.API_URL}/api/queue/clear-completed`);
      fetchQueueData();
    } catch (err) {
      logError('clearCompleted', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'text-yellow-400 bg-yellow-900/20';
      case 'processing': return 'text-blue-400 bg-blue-900/20';
      case 'completed': return 'text-green-400 bg-green-900/20';
      case 'failed': return 'text-red-400 bg-red-900/20';
      default: return 'text-gray-400 bg-gray-900/20';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return '⏳';
      case 'processing': return '🔄';
      case 'completed': return '✅';
      case 'failed': return '❌';
      default: return '❓';
    }
  };

  const filteredTasks = filter === 'all'
    ? tasks
    : tasks.filter(t => t.status === filter);

  return (
    <div className="h-full flex bg-gray-900">
      {/* Queue Stats & Controls */}
      <div className="w-80 bg-gray-800 border-r border-gray-700 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-700">
          <h2 className="text-lg font-semibold text-white mb-3">Queue Manager</h2>

          {/* Stats Overview */}
          <div className="grid grid-cols-2 gap-2 mb-3">
            <div className="bg-gray-700 rounded p-2">
              <div className="text-xs text-gray-400">Total Tasks</div>
              <div className="text-xl font-bold text-white">{stats.total}</div>
            </div>
            <div className="bg-gray-700 rounded p-2">
              <div className="text-xs text-gray-400">Avg Time</div>
              <div className="text-xl font-bold text-white">{stats.avgProcessingTime.toFixed(1)}s</div>
            </div>
          </div>

          {/* Status Breakdown */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-yellow-400">⏳ Pending</span>
              <span className="text-white font-medium">{stats.pending}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-blue-400">🔄 Processing</span>
              <span className="text-white font-medium">{stats.processing}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-green-400">✅ Completed</span>
              <span className="text-white font-medium">{stats.completed}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-red-400">❌ Failed</span>
              <span className="text-white font-medium">{stats.failed}</span>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mt-3">
            <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
              <div className="flex h-full">
                {stats.total > 0 && (
                  <>
                    <div
                      className="bg-green-500"
                      style={{ width: `${(stats.completed / stats.total) * 100}%` }}
                    />
                    <div
                      className="bg-blue-500"
                      style={{ width: `${(stats.processing / stats.total) * 100}%` }}
                    />
                    <div
                      className="bg-yellow-500"
                      style={{ width: `${(stats.pending / stats.total) * 100}%` }}
                    />
                    <div
                      className="bg-red-500"
                      style={{ width: `${(stats.failed / stats.total) * 100}%` }}
                    />
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Filter Buttons */}
        <div className="p-3 border-b border-gray-700">
          <div className="grid grid-cols-2 gap-2">
            {['all', 'pending', 'processing', 'completed', 'failed'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-2 py-1 rounded text-xs capitalize ${
                  filter === f
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="p-3 space-y-2">
          <button
            onClick={fetchQueueData}
            className="w-full px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm"
          >
            🔄 Refresh Queue
          </button>
          <button
            onClick={clearCompleted}
            disabled={loading || stats.completed === 0}
            className="w-full px-3 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white rounded text-sm"
          >
            🗑️ Clear Completed ({stats.completed})
          </button>
        </div>

        {/* Active Agents */}
        <div className="flex-1 p-3 overflow-y-auto">
          <h3 className="text-sm font-semibold text-white mb-2">Active Workers</h3>
          <div className="space-y-1">
            {agents.filter(a => a.status === 'online').map(agent => (
              <div key={agent.id} className="p-2 bg-gray-700 rounded text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-white">{agent.name}</span>
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Task List */}
      <div className="w-96 bg-gray-800 border-r border-gray-700 flex flex-col">
        <div className="p-3 border-b border-gray-700">
          <h3 className="text-sm font-semibold text-white">
            Tasks ({filteredTasks.length})
          </h3>
        </div>

        <div className="flex-1 overflow-y-auto">
          {filteredTasks.length === 0 ? (
            <div className="p-4 text-center text-gray-500 text-sm">
              No tasks in queue
            </div>
          ) : (
            filteredTasks.map(task => (
              <div
                key={task.id}
                onClick={() => setSelectedTask(task)}
                className={`p-3 border-b border-gray-700 cursor-pointer hover:bg-gray-700 ${
                  selectedTask?.id === task.id ? 'bg-gray-700' : ''
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm">{getStatusIcon(task.status)}</span>
                      <span className="text-white font-medium text-sm truncate">
                        {task.name}
                      </span>
                    </div>
                    {task.actor && (
                      <div className="text-xs text-gray-400">
                        Actor: {task.actor}
                      </div>
                    )}
                    <div className="text-xs text-gray-500">
                      Created: {new Date(task.created_at).toLocaleTimeString()}
                    </div>
                  </div>
                  <div className="flex flex-col items-end ml-2">
                    <span className={`text-xs px-2 py-1 rounded ${getStatusColor(task.status)}`}>
                      {task.status}
                    </span>
                    {task.retries > 0 && (
                      <span className="text-xs text-yellow-400 mt-1">
                        Retries: {task.retries}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Task Detail */}
      <div className="flex-1 flex flex-col">
        {selectedTask ? (
          <div className="flex-1 flex flex-col">
            <div className="p-6 border-b border-gray-700">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">
                    {selectedTask.name}
                  </h3>
                  <div className="flex items-center gap-4 text-sm">
                    <span className={`px-2 py-1 rounded ${getStatusColor(selectedTask.status)}`}>
                      {getStatusIcon(selectedTask.status)} {selectedTask.status}
                    </span>
                    <span className="text-gray-400">ID: {selectedTask.id}</span>
                    <span className="text-gray-400">Priority: {selectedTask.priority}</span>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedTask(null)}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="flex-1 p-6 space-y-4 overflow-y-auto">
              {/* Timeline */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-white mb-3">Timeline</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Created</span>
                    <span className="text-white">
                      {new Date(selectedTask.created_at).toLocaleString()}
                    </span>
                  </div>
                  {selectedTask.started_at && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Started</span>
                      <span className="text-white">
                        {new Date(selectedTask.started_at).toLocaleString()}
                      </span>
                    </div>
                  )}
                  {selectedTask.completed_at && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Completed</span>
                      <span className="text-white">
                        {new Date(selectedTask.completed_at).toLocaleString()}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Actor Info */}
              {selectedTask.actor && (
                <div className="bg-gray-800 rounded-lg p-4">
                  <h4 className="text-sm font-semibold text-white mb-3">Actor</h4>
                  <div className="text-sm text-gray-300">{selectedTask.actor}</div>
                </div>
              )}

              {/* Error Info */}
              {selectedTask.error && (
                <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
                  <h4 className="text-sm font-semibold text-red-400 mb-2">Error</h4>
                  <div className="text-sm text-red-300 font-mono">
                    {selectedTask.error}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3">
                {selectedTask.status === 'failed' && (
                  <button
                    onClick={() => retryTask(selectedTask.id)}
                    disabled={loading}
                    className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-600 text-white rounded text-sm"
                  >
                    🔄 Retry Task
                  </button>
                )}
                {(selectedTask.status === 'pending' || selectedTask.status === 'processing') && (
                  <button
                    onClick={() => cancelTask(selectedTask.id)}
                    disabled={loading}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white rounded text-sm"
                  >
                    ❌ Cancel Task
                  </button>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <p className="text-gray-400 mb-2">Select a task to view details</p>
              <p className="text-gray-500 text-sm">
                Queue is processing {stats.processing} task{stats.processing !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default QueuePanel;