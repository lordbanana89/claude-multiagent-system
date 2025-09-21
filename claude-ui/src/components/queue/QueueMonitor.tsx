import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { config } from '../../config';

const API_URL = config.API_URL;

interface QueueTask {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  priority: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error?: string;
  retries: number;
  actor: string;
}

interface QueueStats {
  total: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  avgProcessingTime: number;
}

const QueueMonitor: React.FC = () => {
  const [selectedTask, setSelectedTask] = useState<QueueTask | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const queryClient = useQueryClient();

  // Fetch queue tasks
  const { data: tasks = [], refetch: refetchTasks } = useQuery<QueueTask[]>({
    queryKey: ['queue-tasks'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/queue/tasks`);
      return response.data;
    },
    refetchInterval: autoRefresh ? 2000 : false,
  });

  // Fetch queue stats
  const { data: stats } = useQuery<QueueStats>({
    queryKey: ['queue-stats'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/queue/stats`);
      return response.data;
    },
    refetchInterval: autoRefresh ? 2000 : false,
  });

  // Retry task mutation
  const retryTaskMutation = useMutation({
    mutationFn: async (taskId: string) => {
      const response = await axios.post(`${API_URL}/api/queue/tasks/${taskId}/retry`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['queue-tasks'] });
      queryClient.invalidateQueries({ queryKey: ['queue-stats'] });
    },
  });

  // Cancel task mutation
  const cancelTaskMutation = useMutation({
    mutationFn: async (taskId: string) => {
      const response = await axios.delete(`${API_URL}/api/queue/tasks/${taskId}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['queue-tasks'] });
      queryClient.invalidateQueries({ queryKey: ['queue-stats'] });
    },
  });

  // Clear completed tasks mutation
  const clearCompletedMutation = useMutation({
    mutationFn: async () => {
      const response = await axios.post(`${API_URL}/api/queue/clear-completed`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['queue-tasks'] });
      queryClient.invalidateQueries({ queryKey: ['queue-stats'] });
    },
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
      case 'processing':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400';
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const calculateDuration = (start: string, end?: string) => {
    const startTime = new Date(start).getTime();
    const endTime = end ? new Date(end).getTime() : Date.now();
    const duration = endTime - startTime;
    const seconds = Math.floor(duration / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  return (
    <div className="p-6">
      {/* Header with Stats */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            📡 Queue Monitor
          </h2>
          <div className="flex items-center space-x-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Auto Refresh
              </span>
            </label>
            <button
              onClick={() => refetchTasks()}
              className="px-3 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
            >
              🔄 Refresh
            </button>
            <button
              onClick={() => clearCompletedMutation.mutate()}
              className="px-3 py-1 bg-gray-600 text-white rounded-md hover:bg-gray-700 text-sm"
            >
              🧹 Clear Completed
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-3 shadow">
              <div className="text-sm text-gray-600 dark:text-gray-400">Total</div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {stats.total}
              </div>
            </div>
            <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3 shadow">
              <div className="text-sm text-yellow-600 dark:text-yellow-400">Pending</div>
              <div className="text-2xl font-bold text-yellow-700 dark:text-yellow-300">
                {stats.pending}
              </div>
            </div>
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 shadow">
              <div className="text-sm text-blue-600 dark:text-blue-400">Processing</div>
              <div className="text-2xl font-bold text-blue-700 dark:text-blue-300">
                {stats.processing}
              </div>
            </div>
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 shadow">
              <div className="text-sm text-green-600 dark:text-green-400">Completed</div>
              <div className="text-2xl font-bold text-green-700 dark:text-green-300">
                {stats.completed}
              </div>
            </div>
            <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-3 shadow">
              <div className="text-sm text-red-600 dark:text-red-400">Failed</div>
              <div className="text-2xl font-bold text-red-700 dark:text-red-300">
                {stats.failed}
              </div>
            </div>
            <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-3 shadow">
              <div className="text-sm text-purple-600 dark:text-purple-400">Avg Time</div>
              <div className="text-2xl font-bold text-purple-700 dark:text-purple-300">
                {stats.avgProcessingTime ? stats.avgProcessingTime.toFixed(1) : '0.0'}s
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Task List and Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Task List */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
          <div className="px-6 py-3 bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Tasks
            </h3>
          </div>
          <div className="max-h-[600px] overflow-y-auto">
            {tasks.length === 0 ? (
              <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                No tasks in queue
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-700 sticky top-0">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Task
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Status
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Priority
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Duration
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-600">
                  {tasks.map(task => (
                    <tr
                      key={task.id}
                      onClick={() => setSelectedTask(task)}
                      className="hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                    >
                      <td className="px-4 py-3">
                        <div>
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {task.name}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {task.actor}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(
                            task.status
                          )}`}
                        >
                          {task.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-gray-900 dark:text-white">
                          {task.priority}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {task.started_at
                            ? calculateDuration(task.started_at, task.completed_at)
                            : '-'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex space-x-2">
                          {task.status === 'failed' && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                retryTaskMutation.mutate(task.id);
                              }}
                              className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                              title="Retry"
                            >
                              🔄
                            </button>
                          )}
                          {(task.status === 'pending' || task.status === 'processing') && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                cancelTaskMutation.mutate(task.id);
                              }}
                              className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                              title="Cancel"
                            >
                              ❌
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Task Details */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg">
          <div className="px-6 py-3 bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Task Details
            </h3>
          </div>
          <div className="p-6">
            {selectedTask ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    ID
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white font-mono">
                    {selectedTask.id}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Name
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">
                    {selectedTask.name}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Status
                  </label>
                  <p className="mt-1">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(
                        selectedTask.status
                      )}`}
                    >
                      {selectedTask.status}
                    </span>
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Created At
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">
                    {formatDate(selectedTask.created_at)}
                  </p>
                </div>
                {selectedTask.started_at && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Started At
                    </label>
                    <p className="mt-1 text-sm text-gray-900 dark:text-white">
                      {formatDate(selectedTask.started_at)}
                    </p>
                  </div>
                )}
                {selectedTask.completed_at && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Completed At
                    </label>
                    <p className="mt-1 text-sm text-gray-900 dark:text-white">
                      {formatDate(selectedTask.completed_at)}
                    </p>
                  </div>
                )}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Retries
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">
                    {selectedTask.retries}
                  </p>
                </div>
                {selectedTask.error && (
                  <div>
                    <label className="block text-sm font-medium text-red-700 dark:text-red-300">
                      Error
                    </label>
                    <p className="mt-1 text-sm text-red-600 dark:text-red-400 font-mono text-xs">
                      {selectedTask.error}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-center text-gray-500 dark:text-gray-400">
                Select a task to view details
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default QueueMonitor;