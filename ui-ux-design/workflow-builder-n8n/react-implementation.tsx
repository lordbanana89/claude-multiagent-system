// Full React Implementation - Workflow Builder n8n Style
// Complete working example with drag-drop functionality

import React, { useState, useCallback, useRef, useMemo } from 'react';
import ReactFlow, {
  ReactFlowProvider,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  Panel,
  Node,
  Edge,
  Connection,
  useReactFlow,
  getIncomers,
  getOutgoers,
  getConnectedEdges,
} from 'reactflow';
import 'reactflow/dist/style.css';

// Custom node types
import AgentNode from './nodes/AgentNode';
import TriggerNode from './nodes/TriggerNode';
import ConditionNode from './nodes/ConditionNode';
import ActionNode from './nodes/ActionNode';
import TransformNode from './nodes/TransformNode';

// Stores
import { useWorkflowStore } from './stores/workflowStore';
import { useAgentStore } from './stores/agentStore';

// Types
interface WorkflowNode extends Node {
  data: {
    label: string;
    type: string;
    agentId?: string;
    task?: string;
    config?: Record<string, any>;
    status?: 'idle' | 'running' | 'success' | 'error';
    lastExecution?: Date;
  };
}

interface NodeTemplate {
  type: string;
  category: string;
  label: string;
  icon: string;
  description: string;
  defaultData: Record<string, any>;
}

// Node templates library
const NODE_TEMPLATES: NodeTemplate[] = [
  // Triggers
  {
    type: 'trigger',
    category: 'Triggers',
    label: 'Manual Trigger',
    icon: '▶️',
    description: 'Start workflow manually',
    defaultData: { triggerType: 'manual' }
  },
  {
    type: 'trigger',
    category: 'Triggers',
    label: 'Webhook',
    icon: '🔗',
    description: 'Trigger via HTTP webhook',
    defaultData: { triggerType: 'webhook', method: 'POST' }
  },
  {
    type: 'trigger',
    category: 'Triggers',
    label: 'Schedule',
    icon: '⏰',
    description: 'Run on schedule',
    defaultData: { triggerType: 'cron', schedule: '0 * * * *' }
  },

  // Agents
  {
    type: 'agent',
    category: 'Agents',
    label: 'Backend API',
    icon: '🔧',
    description: 'Backend API Agent',
    defaultData: { agentId: 'backend-api', agentType: 'backend' }
  },
  {
    type: 'agent',
    category: 'Agents',
    label: 'Database',
    icon: '🗄️',
    description: 'Database Agent',
    defaultData: { agentId: 'database', agentType: 'database' }
  },
  {
    type: 'agent',
    category: 'Agents',
    label: 'Frontend UI',
    icon: '🎨',
    description: 'Frontend UI Agent',
    defaultData: { agentId: 'frontend-ui', agentType: 'frontend' }
  },
  {
    type: 'agent',
    category: 'Agents',
    label: 'Testing',
    icon: '🧪',
    description: 'Testing Agent',
    defaultData: { agentId: 'testing', agentType: 'testing' }
  },

  // Logic
  {
    type: 'condition',
    category: 'Logic',
    label: 'IF Condition',
    icon: '❓',
    description: 'Conditional branching',
    defaultData: { condition: '', operator: 'equals' }
  },
  {
    type: 'condition',
    category: 'Logic',
    label: 'Switch',
    icon: '🔀',
    description: 'Multiple branches',
    defaultData: { cases: [] }
  },
  {
    type: 'transform',
    category: 'Logic',
    label: 'Loop',
    icon: '🔁',
    description: 'Iterate over items',
    defaultData: { loopType: 'foreach' }
  },

  // Actions
  {
    type: 'action',
    category: 'Actions',
    label: 'HTTP Request',
    icon: '🌐',
    description: 'Make HTTP request',
    defaultData: { method: 'GET', url: '' }
  },
  {
    type: 'action',
    category: 'Actions',
    label: 'Database Query',
    icon: '📊',
    description: 'Execute database query',
    defaultData: { query: '', database: '' }
  },
  {
    type: 'transform',
    category: 'Actions',
    label: 'Transform Data',
    icon: '🔄',
    description: 'Transform data structure',
    defaultData: { transformer: 'jsonpath', path: '' }
  },
];

// Node type components mapping
const nodeTypes = {
  trigger: TriggerNode,
  agent: AgentNode,
  condition: ConditionNode,
  action: ActionNode,
  transform: TransformNode,
};

// Main Workflow Builder Component
export const WorkflowBuilder: React.FC = () => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState<WorkflowNode>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [showNodePalette, setShowNodePalette] = useState(true);
  const [showProperties, setShowProperties] = useState(true);
  const { project } = useReactFlow();

  // Handle connection between nodes
  const onConnect = useCallback(
    (params: Edge | Connection) => {
      setEdges((eds) => addEdge({
        ...params,
        type: 'smoothstep',
        animated: true,
        style: { stroke: '#2563eb', strokeWidth: 2 }
      }, eds));
    },
    [setEdges]
  );

  // Handle node selection
  const onNodeClick = useCallback((event: React.MouseEvent, node: WorkflowNode) => {
    setSelectedNode(node);
  }, []);

  // Handle drag over canvas
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Handle drop on canvas
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
      const templateData = event.dataTransfer.getData('application/reactflow');

      if (typeof templateData === 'undefined' || !templateData || !reactFlowBounds) {
        return;
      }

      const template = JSON.parse(templateData) as NodeTemplate;
      const position = project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      const newNode: WorkflowNode = {
        id: `${template.type}_${Date.now()}`,
        type: template.type,
        position,
        data: {
          label: template.label,
          type: template.type,
          ...template.defaultData,
          status: 'idle'
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [project, setNodes]
  );

  // Delete selected nodes and edges
  const deleteSelectedElements = useCallback(() => {
    setNodes((nds) => nds.filter((node) => !node.selected));
    setEdges((eds) => eds.filter((edge) => !edge.selected));
    setSelectedNode(null);
  }, [setNodes, setEdges]);

  // Execute workflow
  const executeWorkflow = useCallback(async () => {
    // Update all nodes to running state
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: { ...node.data, status: 'running' }
      }))
    );

    // Simulate execution
    for (const node of nodes) {
      await new Promise(resolve => setTimeout(resolve, 1000));

      setNodes((nds) =>
        nds.map((n) =>
          n.id === node.id
            ? { ...n, data: { ...n.data, status: 'success' } }
            : n
        )
      );
    }
  }, [nodes, setNodes]);

  return (
    <div className="workflow-builder-container" style={{ height: '100vh', display: 'flex' }}>
      {/* Node Palette Sidebar */}
      {showNodePalette && (
        <NodePalette templates={NODE_TEMPLATES} onClose={() => setShowNodePalette(false)} />
      )}

      {/* Main Canvas */}
      <div className="workflow-canvas-wrapper" style={{ flex: 1 }} ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onDragOver={onDragOver}
          onDrop={onDrop}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-left"
        >
          <Background variant="dots" gap={12} size={1} color="#e5e7eb" />
          <Controls />
          <MiniMap
            nodeColor={(node) => {
              switch (node.data?.status) {
                case 'running': return '#f59e0b';
                case 'success': return '#10b981';
                case 'error': return '#ef4444';
                default: return '#6b7280';
              }
            }}
          />

          {/* Top Toolbar */}
          <Panel position="top-center">
            <div className="workflow-toolbar">
              <button onClick={() => setShowNodePalette(!showNodePalette)}>
                📦 Nodes
              </button>
              <button onClick={executeWorkflow}>
                ▶️ Execute
              </button>
              <button onClick={() => console.log({ nodes, edges })}>
                💾 Save
              </button>
              <button onClick={deleteSelectedElements}>
                🗑️ Delete
              </button>
            </div>
          </Panel>
        </ReactFlow>
      </div>

      {/* Properties Panel */}
      {showProperties && selectedNode && (
        <PropertiesPanel
          node={selectedNode}
          onUpdate={(updates) => {
            setNodes((nds) =>
              nds.map((n) =>
                n.id === selectedNode.id
                  ? { ...n, data: { ...n.data, ...updates } }
                  : n
              )
            );
          }}
          onClose={() => setShowProperties(false)}
        />
      )}
    </div>
  );
};

// Node Palette Component
const NodePalette: React.FC<{
  templates: NodeTemplate[];
  onClose: () => void;
}> = ({ templates, onClose }) => {
  const onDragStart = (event: React.DragEvent, template: NodeTemplate) => {
    event.dataTransfer.setData('application/reactflow', JSON.stringify(template));
    event.dataTransfer.effectAllowed = 'move';
  };

  // Group templates by category
  const groupedTemplates = useMemo(() => {
    const groups: Record<string, NodeTemplate[]> = {};
    templates.forEach(template => {
      if (!groups[template.category]) {
        groups[template.category] = [];
      }
      groups[template.category].push(template);
    });
    return groups;
  }, [templates]);

  return (
    <div className="node-palette" style={{
      width: '250px',
      background: 'white',
      borderRight: '1px solid #e5e7eb',
      padding: '1rem',
      overflowY: 'auto'
    }}>
      <div className="palette-header" style={{
        display: 'flex',
        justifyContent: 'space-between',
        marginBottom: '1rem'
      }}>
        <h3>Node Library</h3>
        <button onClick={onClose}>✕</button>
      </div>

      {Object.entries(groupedTemplates).map(([category, categoryTemplates]) => (
        <div key={category} className="node-category" style={{ marginBottom: '1.5rem' }}>
          <h4 style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem' }}>
            {category}
          </h4>
          <div className="node-list">
            {categoryTemplates.map((template) => (
              <div
                key={`${template.type}-${template.label}`}
                className="node-template"
                draggable
                onDragStart={(e) => onDragStart(e, template)}
                style={{
                  padding: '0.5rem',
                  marginBottom: '0.5rem',
                  background: '#f9fafb',
                  borderRadius: '0.375rem',
                  cursor: 'move',
                  border: '1px solid #e5e7eb',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = '#f3f4f6';
                  e.currentTarget.style.borderColor = '#2563eb';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = '#f9fafb';
                  e.currentTarget.style.borderColor = '#e5e7eb';
                }}
              >
                <span style={{ fontSize: '1.25rem' }}>{template.icon}</span>
                <div>
                  <div style={{ fontWeight: '500' }}>{template.label}</div>
                  <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                    {template.description}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

// Properties Panel Component
const PropertiesPanel: React.FC<{
  node: WorkflowNode;
  onUpdate: (updates: Partial<WorkflowNode['data']>) => void;
  onClose: () => void;
}> = ({ node, onUpdate, onClose }) => {
  return (
    <div className="properties-panel" style={{
      width: '300px',
      background: 'white',
      borderLeft: '1px solid #e5e7eb',
      padding: '1rem',
      overflowY: 'auto'
    }}>
      <div className="panel-header" style={{
        display: 'flex',
        justifyContent: 'space-between',
        marginBottom: '1rem'
      }}>
        <h3>Node Properties</h3>
        <button onClick={onClose}>✕</button>
      </div>

      <div className="properties-content">
        <div className="property-group" style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.875rem' }}>
            Node ID
          </label>
          <input
            type="text"
            value={node.id}
            disabled
            style={{
              width: '100%',
              padding: '0.5rem',
              border: '1px solid #e5e7eb',
              borderRadius: '0.375rem',
              background: '#f9fafb'
            }}
          />
        </div>

        <div className="property-group" style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.875rem' }}>
            Label
          </label>
          <input
            type="text"
            value={node.data.label}
            onChange={(e) => onUpdate({ label: e.target.value })}
            style={{
              width: '100%',
              padding: '0.5rem',
              border: '1px solid #e5e7eb',
              borderRadius: '0.375rem'
            }}
          />
        </div>

        {node.data.type === 'agent' && (
          <>
            <div className="property-group" style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.875rem' }}>
                Agent
              </label>
              <select
                value={node.data.agentId}
                onChange={(e) => onUpdate({ agentId: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #e5e7eb',
                  borderRadius: '0.375rem'
                }}
              >
                <option value="backend-api">Backend API</option>
                <option value="database">Database</option>
                <option value="frontend-ui">Frontend UI</option>
                <option value="testing">Testing</option>
              </select>
            </div>

            <div className="property-group" style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.875rem' }}>
                Task
              </label>
              <textarea
                value={node.data.task || ''}
                onChange={(e) => onUpdate({ task: e.target.value })}
                rows={3}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #e5e7eb',
                  borderRadius: '0.375rem',
                  resize: 'vertical'
                }}
                placeholder="Enter task description..."
              />
            </div>
          </>
        )}

        {node.data.type === 'condition' && (
          <div className="property-group" style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.875rem' }}>
              Condition
            </label>
            <input
              type="text"
              value={node.data.config?.condition || ''}
              onChange={(e) => onUpdate({
                config: { ...node.data.config, condition: e.target.value }
              })}
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #e5e7eb',
                borderRadius: '0.375rem'
              }}
              placeholder="e.g., result.status === 'success'"
            />
          </div>
        )}

        <div className="property-group" style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.875rem' }}>
            Status
          </label>
          <div style={{
            padding: '0.5rem',
            background: '#f9fafb',
            borderRadius: '0.375rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: node.data.status === 'success' ? '#10b981' :
                         node.data.status === 'error' ? '#ef4444' :
                         node.data.status === 'running' ? '#f59e0b' : '#6b7280'
            }} />
            <span style={{ textTransform: 'capitalize' }}>
              {node.data.status || 'idle'}
            </span>
          </div>
        </div>

        {node.data.lastExecution && (
          <div className="property-group">
            <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.875rem' }}>
              Last Execution
            </label>
            <div style={{
              padding: '0.5rem',
              background: '#f9fafb',
              borderRadius: '0.375rem',
              fontSize: '0.875rem'
            }}>
              {new Date(node.data.lastExecution).toLocaleString()}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Wrapper with ReactFlowProvider
export const WorkflowBuilderApp: React.FC = () => {
  return (
    <ReactFlowProvider>
      <WorkflowBuilder />
    </ReactFlowProvider>
  );
};

export default WorkflowBuilderApp;