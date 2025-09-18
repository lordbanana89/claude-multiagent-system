import React, { useState, useCallback } from 'react';
import ReactFlow, {
  Controls,
  Background,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  ConnectionMode,
  Panel
} from 'reactflow';
import type { Node, Edge, Connection } from 'reactflow';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import 'reactflow/dist/style.css';

// Components
import AgentNode from '../nodes/AgentNode';
import NodePalette from './NodePalette';
import NodeConfig from './NodeConfig';
import ExecutionControl from './ExecutionControl';

const nodeTypes = {
  agent: AgentNode,
};

interface WorkflowViewProps {
  agents: any[];
  mode: 'view' | 'edit';
  onModeChange: (mode: 'view' | 'edit') => void;
}

const WorkflowView: React.FC<WorkflowViewProps> = ({ agents, mode, onModeChange }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);

  // Generate workflow nodes from agents
  React.useEffect(() => {
    const agentNodes: Node[] = agents.map((agent, index) => {
      let position = { x: 0, y: 0 };

      // Hierarchical positioning
      if (agent.id === 'master') {
        position = { x: 600, y: 50 };
      } else if (agent.id === 'supervisor') {
        position = { x: 600, y: 200 };
      } else {
        const angle = (Math.PI / (agents.length - 2)) * (index - 2);
        position = {
          x: 600 + Math.cos(angle) * 400,
          y: 450 + Math.sin(angle) * 150
        };
      }

      return {
        id: agent.id,
        type: 'agent',
        position,
        data: {
          ...agent,
          label: agent.name
        }
      };
    });

    // Create hierarchy edges
    const hierarchyEdges: Edge[] = [];
    const master = agents.find(a => a.id === 'master');
    const supervisor = agents.find(a => a.id === 'supervisor');

    if (master && supervisor) {
      hierarchyEdges.push({
        id: 'master-supervisor',
        source: 'master',
        target: 'supervisor',
        sourceHandle: 'bottom',
        targetHandle: 'top',
        animated: true,
        style: { stroke: '#60a5fa', strokeWidth: 2 },
        type: 'smoothstep'
      });
    }

    if (supervisor) {
      agents.filter(a => a.id !== 'master' && a.id !== 'supervisor').forEach(agent => {
        hierarchyEdges.push({
          id: `supervisor-${agent.id}`,
          source: 'supervisor',
          target: agent.id,
          sourceHandle: 'bottom',
          targetHandle: 'top',
          animated: false,
          style: { stroke: '#4b5563', strokeWidth: 1 },
          type: 'smoothstep'
        });
      });
    }

    setNodes(agentNodes);
    setEdges(hierarchyEdges);
  }, [agents, setNodes, setEdges]);

  // Handle edge connection
  const onConnect = useCallback((connection: Connection) => {
    setEdges((eds) => addEdge({
      ...connection,
      animated: true,
      style: { stroke: '#10b981' }
    }, eds));
  }, [setEdges]);

  // Handle node click
  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  // Handle node drop from palette
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      if (!type) return;

      // Get the bounding rect of the ReactFlow wrapper to calculate relative position
      const reactFlowBounds = (event.target as Element).closest('.react-flow')?.getBoundingClientRect();
      if (!reactFlowBounds) return;

      const position = {
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top
      };

      const newNode: Node = {
        id: `${type}_${Date.now()}`,
        type: type === 'agent' ? 'agent' : 'default',
        position,
        data: {
          label: `New ${type}`,
          type,
          config: {}
        }
      };

      setNodes((nds) => [...nds, newNode]);
    },
    [setNodes]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const handleExecute = () => {
    setIsExecuting(!isExecuting);
  };

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="h-full flex flex-col bg-gray-900">
        {/* Toolbar */}
        <div className="bg-gray-800 border-b border-gray-700 px-4 py-2 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h2 className="text-lg font-semibold text-white">
              Workflow {mode === 'edit' ? 'Builder' : 'Visualization'}
            </h2>

            {/* Mode Toggle */}
            <div className="flex bg-gray-700 rounded-lg p-1">
              <button
                onClick={() => onModeChange('view')}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  mode === 'view'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                📊 View
              </button>
              <button
                onClick={() => onModeChange('edit')}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  mode === 'edit'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                ✏️ Edit
              </button>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="flex items-center space-x-2">
            {mode === 'edit' && (
              <>
                <button
                  onClick={() => {
                    const workflow = { nodes, edges };
                    console.log('Save workflow:', workflow);
                    // TODO: Implement save
                  }}
                  className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-sm"
                >
                  💾 Save
                </button>
                <button
                  onClick={() => {
                    console.log('Load workflow');
                    // TODO: Implement load
                  }}
                  className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm"
                >
                  📁 Load
                </button>
              </>
            )}
            <button
              onClick={() => {
                setNodes([]);
                setEdges([]);
              }}
              className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm"
            >
              🗑️ Clear
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex">
          {/* Left Panel - Node Palette (Edit Mode Only) */}
          {mode === 'edit' && (
            <div className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
              <NodePalette />
            </div>
          )}

          {/* Center - ReactFlow Canvas */}
          <div className="flex-1 relative">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              onDrop={onDrop}
              onDragOver={onDragOver}
              nodeTypes={nodeTypes}
              connectionMode={ConnectionMode.Loose}
              fitView
              className="bg-gray-900"
              deleteKeyCode={mode === 'edit' ? ['Delete', 'Backspace'] : []}
            >
              <Background color="#1f2937" gap={20} />
              <Controls className="bg-gray-800 border-gray-700 text-white" />
              <MiniMap
                className="bg-gray-800 border-gray-700"
                nodeColor={(node) => {
                  const agent = agents.find(a => a.id === node.id);
                  return agent?.status === 'online' ? '#10b981' : '#6b7280';
                }}
              />

              {/* Status Panel */}
              <Panel position="top-left" className="bg-gray-800 p-3 rounded-lg border border-gray-700">
                <div className="text-sm text-white">
                  <div className="flex items-center space-x-4">
                    <span>Nodes: {nodes.length}</span>
                    <span>Edges: {edges.length}</span>
                    {mode === 'view' && (
                      <span className="flex items-center">
                        <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-1"></span>
                        Live
                      </span>
                    )}
                  </div>
                </div>
              </Panel>

              {/* Instructions Panel */}
              {mode === 'edit' && (
                <Panel position="bottom-left" className="bg-gray-800 p-3 rounded-lg border border-gray-700 max-w-sm">
                  <div className="text-xs text-gray-300">
                    <p>📌 Drag nodes from palette to canvas</p>
                    <p>🔗 Connect nodes by dragging from handles</p>
                    <p>🗑️ Select + Delete key to remove</p>
                    <p>⚙️ Click node to configure</p>
                  </div>
                </Panel>
              )}
            </ReactFlow>
          </div>

          {/* Right Panel - Node Configuration (Edit Mode Only) */}
          {mode === 'edit' && selectedNode && (
            <div className="w-80 bg-gray-800 border-l border-gray-700">
              <NodeConfig
                node={selectedNode}
                onUpdate={(updatedNode) => {
                  setNodes((nds) =>
                    nds.map((n) => (n.id === updatedNode.id ? updatedNode : n))
                  );
                }}
                onClose={() => setSelectedNode(null)}
              />
            </div>
          )}
        </div>

        {/* Bottom - Execution Control */}
        <ExecutionControl
          onExecute={handleExecute}
          isExecuting={isExecuting}
          nodes={nodes}
        />
      </div>
    </DndProvider>
  );
};

export default WorkflowView;