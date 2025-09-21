import React, { useState, useCallback, useRef } from 'react';
import ReactFlow, {
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  Panel,
  ReactFlowProvider,
  useReactFlow,
} from 'reactflow';
import type { Node, Edge, Connection } from 'reactflow';
import 'reactflow/dist/style.css';
import integrationService from '../../services/integration';
import axios from 'axios';
import { config } from '../../config';

// Import custom nodes
import AgentNode from './nodes/AgentNode';
import TriggerNode from './nodes/TriggerNode';
import ConditionNode from './nodes/ConditionNode';
import ActionNode from './nodes/ActionNode';
import TransformNode from './nodes/TransformNode';

const nodeTypes = {
  agent: AgentNode,
  trigger: TriggerNode,
  condition: ConditionNode,
  action: ActionNode,
  transform: TransformNode,
};

const initialNodes: Node[] = [
  {
    id: '1',
    type: 'trigger',
    position: { x: 100, y: 100 },
    data: { label: 'Start Workflow', triggerType: 'manual' },
  },
  {
    id: '2',
    type: 'agent',
    position: { x: 400, y: 100 },
    data: { label: 'Supervisor Agent', agentId: 'supervisor', agentType: 'coordinator' },
  },
];

const initialEdges: Edge[] = [
  { id: 'e1-2', source: '1', target: '2', animated: true },
];

const WorkflowCanvas: React.FC = () => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [isExecuting, setIsExecuting] = useState(false);
  const { project } = useReactFlow();

  const onConnect = useCallback(
    (params: Edge | Connection) =>
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            type: 'smoothstep',
            animated: true,
            style: { stroke: '#3b82f6' },
          },
          eds
        )
      ),
    [setEdges]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
      const type = event.dataTransfer.getData('application/reactflow');

      if (typeof type === 'undefined' || !type || !reactFlowBounds) {
        return;
      }

      const position = project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      const nodeData = JSON.parse(type);
      const newNode: Node = {
        id: `node_${Date.now()}`,
        type: nodeData.type,
        position,
        data: { label: nodeData.label, ...nodeData.data },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [project, setNodes]
  );

  const executeWorkflow = async () => {
    setIsExecuting(true);

    // Update nodes to show execution
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: { ...node.data, status: 'running' },
      }))
    );

    // Build execution plan from graph
    const executionPlan = buildExecutionPlan(nodes, edges);

    // Execute each step through real integration
    for (const step of executionPlan) {
      const node = nodes.find(n => n.id === step.nodeId);
      if (!node) continue;

      try {
        // Mark node as running
        setNodes((nds) =>
          nds.map((n) =>
            n.id === node.id
              ? { ...n, data: { ...n.data, status: 'running' } }
              : n
          )
        );

        // Execute based on node type
        if (node.type === 'agent') {
          // Execute through agent
          const agentId = node.data.agentId;
          const task = {
            title: `Workflow task: ${node.data.label}`,
            command: step.command || `Execute ${node.data.label}`,
            priority: step.priority || 5,
            metadata: {
              workflow_node: node.id,
              workflow_execution: Date.now()
            }
          };

          const result = await integrationService.executeTask(agentId, task);
          console.log(`Executed on agent ${agentId}:`, result);

        } else if (node.type === 'action') {
          // Execute action (e.g., HTTP request)
          if (node.data.method && node.data.url) {
            const response = await axios({
              method: node.data.method,
              url: node.data.url,
              timeout: 5000
            });
            console.log('Action executed:', response.status);
          }

        } else if (node.type === 'condition') {
          // Evaluate condition
          const condition = node.data.condition || 'true';
          const result = eval(condition); // Simple evaluation (in production, use safer method)
          console.log('Condition result:', result);

          // Skip downstream nodes if condition fails
          if (!result) {
            // Mark as skipped
            setNodes((nds) =>
              nds.map((n) =>
                n.id === node.id
                  ? { ...n, data: { ...n.data, status: 'skipped' } }
                  : n
              )
            );
            continue;
          }
        }

        // Mark node as success
        setNodes((nds) =>
          nds.map((n) =>
            n.id === node.id
              ? { ...n, data: { ...n.data, status: 'success' } }
              : n
          )
        );

        // Small delay between executions
        await new Promise((resolve) => setTimeout(resolve, 500));

      } catch (error) {
        console.error(`Error executing node ${node.id}:`, error);
        // Mark node as error
        setNodes((nds) =>
          nds.map((n) =>
            n.id === node.id
              ? { ...n, data: { ...n.data, status: 'error', error: String(error) } }
              : n
          )
        );
      }
    }

    setIsExecuting(false);
  };

  // Build execution plan from graph (topological sort)
  const buildExecutionPlan = (nodes: Node[], edges: Edge[]) => {
    const plan: any[] = [];
    const visited = new Set<string>();
    const visiting = new Set<string>();

    const visit = (nodeId: string) => {
      if (visited.has(nodeId)) return;
      if (visiting.has(nodeId)) {
        console.warn('Cycle detected in workflow');
        return;
      }

      visiting.add(nodeId);

      // Visit dependencies first
      const incomingEdges = edges.filter(e => e.target === nodeId);
      for (const edge of incomingEdges) {
        visit(edge.source);
      }

      visiting.delete(nodeId);
      visited.add(nodeId);

      const node = nodes.find(n => n.id === nodeId);
      if (node) {
        plan.push({
          nodeId,
          type: node.type,
          data: node.data
        });
      }
    };

    // Start from nodes with no incoming edges (triggers)
    const startNodes = nodes.filter(node =>
      !edges.some(edge => edge.target === node.id)
    );

    for (const node of startNodes) {
      visit(node.id);
    }

    // Visit any remaining unconnected nodes
    for (const node of nodes) {
      visit(node.id);
    }

    return plan;
  };

  const saveWorkflow = async () => {
    const workflow = {
      name: `Workflow_${new Date().toISOString()}`,
      nodes,
      edges,
      timestamp: new Date().toISOString(),
      metadata: {
        created_by: 'UI',
        version: '1.0'
      }
    };

    try {
      // Save to database through API
      const response = await axios.post(`${config.API_URL}/api/workflows`, workflow);
      if (response.data.success) {
        alert(`Workflow saved with ID: ${response.data.workflow_id}`);
      }
    } catch (error) {
      console.error('Failed to save workflow:', error);
      alert('Failed to save workflow');
    }
  };

  const clearCanvas = () => {
    if (confirm('Are you sure you want to clear the canvas?')) {
      setNodes([]);
      setEdges([]);
    }
  };

  const loadWorkflow = async (workflowId: string) => {
    try {
      const response = await axios.get(`${config.API_URL}/api/workflows/${workflowId}`);
      if (response.data) {
        setNodes(response.data.nodes || []);
        setEdges(response.data.edges || []);
      }
    } catch (error) {
      console.error('Failed to load workflow:', error);
    }
  };

  return (
    <div className="h-[calc(100vh-8rem)] bg-gray-50 dark:bg-gray-900 rounded-lg overflow-hidden">
      <div className="flex h-full">
        {/* Node Palette */}
        <NodePalette />

        {/* Canvas */}
        <div className="flex-1" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onDragOver={onDragOver}
            onDrop={onDrop}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background color="#1f2937" gap={20} />
            <Controls />
            <MiniMap
              nodeColor={(node) => {
                switch (node.data?.status) {
                  case 'running':
                    return '#f59e0b';
                  case 'success':
                    return '#10b981';
                  case 'error':
                    return '#ef4444';
                  default:
                    return '#6b7280';
                }
              }}
            />

            {/* Toolbar */}
            <Panel position="top-center">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg px-4 py-2 flex space-x-2">
                <button
                  onClick={executeWorkflow}
                  disabled={isExecuting}
                  className={`px-4 py-2 rounded-md font-medium transition-colors ${
                    isExecuting
                      ? 'bg-gray-300 text-gray-500'
                      : 'bg-green-600 text-white hover:bg-green-700'
                  }`}
                >
                  {isExecuting ? '⏳ Executing...' : '▶️ Execute'}
                </button>
                <button
                  onClick={saveWorkflow}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
                >
                  💾 Save
                </button>
                <button
                  onClick={clearCanvas}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 font-medium"
                >
                  🗑️ Clear
                </button>
              </div>
            </Panel>
          </ReactFlow>
        </div>
      </div>
    </div>
  );
};

// Node Palette Component
const NodePalette: React.FC = () => {
  const nodeTemplates = [
    {
      type: 'trigger',
      label: 'Manual Trigger',
      icon: '▶️',
      data: { triggerType: 'manual' },
    },
    {
      type: 'agent',
      label: 'Supervisor',
      icon: '👥',
      data: { agentId: 'supervisor', agentType: 'coordinator' },
    },
    {
      type: 'agent',
      label: 'Backend API',
      icon: '🔧',
      data: { agentId: 'backend-api', agentType: 'backend' },
    },
    {
      type: 'agent',
      label: 'Database',
      icon: '🗄️',
      data: { agentId: 'database', agentType: 'database' },
    },
    {
      type: 'agent',
      label: 'Frontend UI',
      icon: '🎨',
      data: { agentId: 'frontend-ui', agentType: 'frontend' },
    },
    {
      type: 'agent',
      label: 'Testing',
      icon: '🧪',
      data: { agentId: 'testing', agentType: 'testing' },
    },
    {
      type: 'condition',
      label: 'IF Condition',
      icon: '❓',
      data: { condition: '' },
    },
    {
      type: 'action',
      label: 'HTTP Request',
      icon: '🌐',
      data: { method: 'GET', url: '' },
    },
    {
      type: 'transform',
      label: 'Transform Data',
      icon: '🔄',
      data: { transformer: 'jsonpath' },
    },
  ];

  const onDragStart = (event: React.DragEvent, nodeData: any) => {
    event.dataTransfer.setData('application/reactflow', JSON.stringify(nodeData));
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="w-64 bg-white dark:bg-gray-800 p-4 shadow-lg overflow-y-auto">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Node Palette
      </h3>
      <div className="space-y-2">
        {nodeTemplates.map((template, index) => (
          <div
            key={index}
            className="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg cursor-move hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
            draggable
            onDragStart={(e) => onDragStart(e, template)}
          >
            <span className="text-xl">{template.icon}</span>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {template.label}
            </span>
          </div>
        ))}
      </div>
      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <p className="text-xs text-blue-600 dark:text-blue-400">
          Drag and drop nodes onto the canvas to build your workflow
        </p>
      </div>
    </div>
  );
};

// Wrap with ReactFlowProvider
const WorkflowCanvasWrapper: React.FC = () => {
  return (
    <ReactFlowProvider>
      <WorkflowCanvas />
    </ReactFlowProvider>
  );
};

export default WorkflowCanvasWrapper;