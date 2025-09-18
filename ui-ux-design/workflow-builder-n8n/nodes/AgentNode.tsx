import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export interface AgentNodeData {
  label: string;
  agentId?: string;
  agentType?: string;
  task?: string;
  status?: 'idle' | 'running' | 'success' | 'error';
}

const AgentNode = memo<NodeProps<AgentNodeData>>(({ data, selected }) => {
  const statusColors = {
    idle: '#6b7280',
    running: '#f59e0b',
    success: '#10b981',
    error: '#ef4444'
  };

  const agentIcons = {
    backend: '🔧',
    database: '🗄️',
    frontend: '🎨',
    testing: '🧪',
    default: '🤖'
  };

  return (
    <div
      style={{
        background: 'white',
        border: `2px solid ${selected ? '#2563eb' : '#e5e7eb'}`,
        borderRadius: '8px',
        padding: '12px',
        minWidth: '180px',
        boxShadow: selected ? '0 4px 6px -1px rgba(0, 0, 0, 0.1)' : '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
        transition: 'all 0.2s'
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        style={{
          background: '#2563eb',
          width: '10px',
          height: '10px'
        }}
      />

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
        <span style={{ fontSize: '20px' }}>
          {agentIcons[data.agentType || 'default']}
        </span>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: '600', fontSize: '14px' }}>{data.label}</div>
          {data.agentId && (
            <div style={{ fontSize: '12px', color: '#6b7280' }}>{data.agentId}</div>
          )}
        </div>
        <div
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: statusColors[data.status || 'idle']
          }}
        />
      </div>

      {data.task && (
        <div style={{
          fontSize: '12px',
          color: '#374151',
          background: '#f9fafb',
          padding: '6px',
          borderRadius: '4px',
          marginTop: '8px'
        }}>
          {data.task}
        </div>
      )}

      <Handle
        type="source"
        position={Position.Right}
        style={{
          background: '#2563eb',
          width: '10px',
          height: '10px'
        }}
      />
    </div>
  );
});

AgentNode.displayName = 'AgentNode';

export default AgentNode;