import React from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';

interface AgentData {
  id: string;
  name: string;
  type: string;
  status: 'online' | 'offline' | 'busy' | 'error';
  sessionId: string;
  lastActivity?: string;
  label?: string;
}

const AgentNode: React.FC<NodeProps<AgentData>> = ({ data, isConnectable }) => {
  const getStatusColor = () => {
    switch (data.status) {
      case 'online': return '#10b981';
      case 'busy': return '#f59e0b';
      case 'offline': return '#6b7280';
      case 'error': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getIcon = () => {
    switch (data.id) {
      case 'master': return '🎖️';
      case 'supervisor': return '👨‍💼';
      case 'backend-api': return '⚙️';
      case 'database': return '🗄️';
      case 'frontend-ui': return '🎨';
      case 'testing': return '🧪';
      case 'instagram': return '📷';
      case 'queue-manager': return '📋';
      case 'deployment': return '🚀';
      default: return '🤖';
    }
  };

  return (
    <div
      className="bg-gray-800 rounded-lg p-4 min-w-[200px] border-2 transition-all hover:shadow-xl relative"
      style={{ borderColor: getStatusColor() }}
    >
      <Handle
        type="target"
        position={Position.Top}
        id="top"
        isConnectable={isConnectable}
        className="w-3 h-3 bg-blue-500 border-2 border-gray-900"
      />

      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xl">{getIcon()}</span>
          <h3 className="font-bold text-white">{data.label || data.name}</h3>
        </div>
        <div
          className="w-3 h-3 rounded-full animate-pulse"
          style={{ backgroundColor: getStatusColor() }}
        />
      </div>

      <div className="text-xs text-gray-400 space-y-1">
        <div>Type: {data.type}</div>
        <div>Session: {data.sessionId}</div>
        <div className="flex justify-between mt-2">
          <span className={`px-2 py-1 rounded text-xs ${
            data.status === 'online' ? 'bg-green-900 text-green-300' :
            data.status === 'busy' ? 'bg-yellow-900 text-yellow-300' :
            data.status === 'error' ? 'bg-red-900 text-red-300' :
            'bg-gray-700 text-gray-400'
          }`}>
            {data.status}
          </span>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom"
        isConnectable={isConnectable}
        className="w-3 h-3 bg-blue-500 border-2 border-gray-900"
      />
    </div>
  );
};

export default AgentNode;