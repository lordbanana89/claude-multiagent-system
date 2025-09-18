import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';

export interface TriggerNodeData {
  label: string;
  triggerType?: string;
  schedule?: string;
  method?: string;
  status?: 'idle' | 'running' | 'success' | 'error';
}

const TriggerNode = memo<NodeProps<TriggerNodeData>>(({ data, selected }) => {
  const triggerIcons = {
    manual: '▶️',
    webhook: '🔗',
    cron: '⏰',
    event: '📡',
    default: '⚡'
  };

  return (
    <div
      style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        border: `2px solid ${selected ? '#2563eb' : 'transparent'}`,
        borderRadius: '8px',
        padding: '12px',
        minWidth: '160px',
        color: 'white',
        boxShadow: selected ? '0 4px 6px -1px rgba(0, 0, 0, 0.1)' : '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
        transition: 'all 0.2s'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '20px' }}>
          {triggerIcons[data.triggerType || 'default']}
        </span>
        <div>
          <div style={{ fontWeight: '600', fontSize: '14px' }}>{data.label}</div>
          {data.triggerType && (
            <div style={{ fontSize: '11px', opacity: 0.9 }}>
              {data.triggerType === 'cron' && data.schedule
                ? `Schedule: ${data.schedule}`
                : data.triggerType === 'webhook' && data.method
                ? `Method: ${data.method}`
                : data.triggerType}
            </div>
          )}
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Right}
        style={{
          background: '#fff',
          border: '2px solid #667eea',
          width: '12px',
          height: '12px'
        }}
      />
    </div>
  );
});

TriggerNode.displayName = 'TriggerNode';

export default TriggerNode;