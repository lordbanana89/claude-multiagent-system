import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';

export interface TransformNodeData {
  label: string;
  transformer?: string;
  path?: string;
  loopType?: string;
  status?: 'idle' | 'running' | 'success' | 'error';
}

const TransformNode = memo<NodeProps<TransformNodeData>>(({ data, selected }) => {
  const getTransformIcon = () => {
    if (data.loopType) return '🔁';
    return '🔄';
  };

  return (
    <div
      style={{
        background: 'white',
        border: `2px solid ${selected ? '#2563eb' : '#8b5cf6'}`,
        borderRadius: '8px',
        padding: '12px',
        minWidth: '160px',
        boxShadow: selected ? '0 4px 6px -1px rgba(0, 0, 0, 0.1)' : '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
        transition: 'all 0.2s'
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        style={{
          background: '#8b5cf6',
          width: '10px',
          height: '10px'
        }}
      />

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
        <span style={{ fontSize: '20px' }}>{getTransformIcon()}</span>
        <div>
          <div style={{ fontWeight: '600', fontSize: '14px' }}>{data.label}</div>
          {data.transformer && (
            <div style={{ fontSize: '11px', color: '#6b7280' }}>
              Type: {data.transformer}
            </div>
          )}
          {data.loopType && (
            <div style={{ fontSize: '11px', color: '#6b7280' }}>
              Loop: {data.loopType}
            </div>
          )}
        </div>
      </div>

      {data.path && (
        <div style={{
          fontSize: '11px',
          color: '#374151',
          background: '#f3e8ff',
          padding: '6px',
          borderRadius: '4px',
          fontFamily: 'monospace'
        }}>
          {data.path}
        </div>
      )}

      <Handle
        type="source"
        position={Position.Right}
        style={{
          background: '#8b5cf6',
          width: '10px',
          height: '10px'
        }}
      />
    </div>
  );
});

TransformNode.displayName = 'TransformNode';

export default TransformNode;