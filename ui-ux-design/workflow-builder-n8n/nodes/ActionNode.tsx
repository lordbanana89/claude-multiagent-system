import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export interface ActionNodeData {
  label: string;
  method?: string;
  url?: string;
  query?: string;
  database?: string;
  status?: 'idle' | 'running' | 'success' | 'error';
}

const ActionNode = memo<NodeProps<ActionNodeData>>(({ data, selected }) => {
  const statusColors = {
    idle: '#6b7280',
    running: '#f59e0b',
    success: '#10b981',
    error: '#ef4444'
  };

  const getActionIcon = () => {
    if (data.method) return '🌐';
    if (data.query) return '📊';
    return '⚡';
  };

  return (
    <div
      style={{
        background: 'white',
        border: `2px solid ${selected ? '#2563eb' : '#10b981'}`,
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
          background: '#10b981',
          width: '10px',
          height: '10px'
        }}
      />

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
        <span style={{ fontSize: '20px' }}>{getActionIcon()}</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: '600', fontSize: '14px' }}>{data.label}</div>
          {data.method && (
            <div style={{ fontSize: '11px', color: '#6b7280' }}>
              {data.method} {data.url ? `to ${data.url.substring(0, 30)}...` : ''}
            </div>
          )}
          {data.database && (
            <div style={{ fontSize: '11px', color: '#6b7280' }}>
              Database: {data.database}
            </div>
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

      {data.query && (
        <div style={{
          fontSize: '11px',
          color: '#374151',
          background: '#f0fdf4',
          padding: '6px',
          borderRadius: '4px',
          fontFamily: 'monospace',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis'
        }}>
          {data.query}
        </div>
      )}

      <Handle
        type="source"
        position={Position.Right}
        style={{
          background: '#10b981',
          width: '10px',
          height: '10px'
        }}
      />
    </div>
  );
});

ActionNode.displayName = 'ActionNode';

export default ActionNode;