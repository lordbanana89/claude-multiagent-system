import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export interface ConditionNodeData {
  label: string;
  condition?: string;
  operator?: string;
  cases?: string[];
  status?: 'idle' | 'running' | 'success' | 'error';
}

const ConditionNode = memo<NodeProps<ConditionNodeData>>(({ data, selected }) => {
  return (
    <div
      style={{
        background: 'white',
        border: `2px solid ${selected ? '#2563eb' : '#fbbf24'}`,
        borderRadius: '12px',
        padding: '12px',
        minWidth: '160px',
        boxShadow: selected ? '0 4px 6px -1px rgba(0, 0, 0, 0.1)' : '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
        transition: 'all 0.2s',
        position: 'relative'
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        style={{
          background: '#fbbf24',
          width: '10px',
          height: '10px'
        }}
      />

      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        marginBottom: data.condition ? '8px' : '0'
      }}>
        <span style={{ fontSize: '20px' }}>❓</span>
        <div>
          <div style={{ fontWeight: '600', fontSize: '14px' }}>{data.label}</div>
          {data.operator && (
            <div style={{ fontSize: '11px', color: '#6b7280' }}>
              Operator: {data.operator}
            </div>
          )}
        </div>
      </div>

      {data.condition && (
        <div style={{
          fontSize: '11px',
          color: '#374151',
          background: '#fef3c7',
          padding: '6px',
          borderRadius: '4px',
          fontFamily: 'monospace'
        }}>
          {data.condition}
        </div>
      )}

      {/* True output */}
      <Handle
        type="source"
        position={Position.Right}
        id="true"
        style={{
          background: '#10b981',
          width: '10px',
          height: '10px',
          top: '30%'
        }}
      />
      <div style={{
        position: 'absolute',
        right: '-25px',
        top: 'calc(30% - 8px)',
        fontSize: '10px',
        color: '#10b981',
        fontWeight: 'bold'
      }}>
        T
      </div>

      {/* False output */}
      <Handle
        type="source"
        position={Position.Right}
        id="false"
        style={{
          background: '#ef4444',
          width: '10px',
          height: '10px',
          top: '70%'
        }}
      />
      <div style={{
        position: 'absolute',
        right: '-25px',
        top: 'calc(70% - 8px)',
        fontSize: '10px',
        color: '#ef4444',
        fontWeight: 'bold'
      }}>
        F
      </div>
    </div>
  );
});

ConditionNode.displayName = 'ConditionNode';

export default ConditionNode;