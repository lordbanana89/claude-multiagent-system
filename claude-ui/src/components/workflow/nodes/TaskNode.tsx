import React from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';

interface TaskNodeData {
  label: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  priority: number;
  agent?: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  error?: string;
  isSelected?: boolean;
}

const TaskNode: React.FC<NodeProps<TaskNodeData>> = ({ data }) => {
  const getStatusColor = () => {
    switch (data.status) {
      case 'pending': return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20';
      case 'running': return 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 animate-pulse';
      case 'completed': return 'border-green-500 bg-green-50 dark:bg-green-900/20';
      case 'failed': return 'border-red-500 bg-red-50 dark:bg-red-900/20';
      default: return 'border-gray-500 bg-gray-50 dark:bg-gray-900/20';
    }
  };

  const getStatusIcon = () => {
    switch (data.status) {
      case 'pending': return '⏳';
      case 'running': return '⚡';
      case 'completed': return '✅';
      case 'failed': return '❌';
      default: return '📋';
    }
  };

  const getPriorityBadge = () => {
    if (data.priority >= 8) return { icon: '🔴', label: 'High' };
    if (data.priority >= 5) return { icon: '🟡', label: 'Med' };
    return { icon: '🟢', label: 'Low' };
  };

  const priority = getPriorityBadge();

  return (
    <div
      className={`
        px-4 py-3 rounded-lg border-2 min-w-[200px] transition-all
        ${getStatusColor()}
        ${data.isSelected ? 'ring-2 ring-blue-500 ring-offset-2' : ''}
        hover:shadow-lg
      `}
    >
      <Handle type="target" position={Position.Top} className="w-3 h-3" />

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold text-gray-900 dark:text-white flex items-center">
            {getStatusIcon()} {data.name || data.label}
          </span>
          <span className="text-xs" title={priority.label}>
            {priority.icon}
          </span>
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className={`
            px-2 py-1 rounded-full font-medium
            ${data.status === 'pending' ? 'bg-yellow-200 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200' :
              data.status === 'running' ? 'bg-blue-200 text-blue-800 dark:bg-blue-800 dark:text-blue-200' :
              data.status === 'completed' ? 'bg-green-200 text-green-800 dark:bg-green-800 dark:text-green-200' :
              'bg-red-200 text-red-800 dark:bg-red-800 dark:text-red-200'}
          `}>
            {data.status}
          </span>

          {data.agent && (
            <span className="text-gray-600 dark:text-gray-400">
              → {data.agent}
            </span>
          )}
        </div>

        {data.error && (
          <div className="text-xs text-red-600 dark:text-red-400 mt-1 p-1 bg-red-100 dark:bg-red-900/30 rounded">
            {data.error}
          </div>
        )}

        {data.status === 'running' && data.startedAt && (
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Running for {Math.round((Date.now() - new Date(data.startedAt).getTime()) / 1000)}s
          </div>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
};

export default TaskNode;