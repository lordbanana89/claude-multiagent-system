import React, { useEffect, useState, useCallback, useMemo } from 'react';
import ReactFlow, {
  Controls,
  Background,
  MiniMap,
  Panel,
  ReactFlowProvider,
  useReactFlow,
  ConnectionMode,
  Position
} from 'reactflow';
import type { Node, Edge, Connection } from 'reactflow';
import 'reactflow/dist/style.css';
import axios from 'axios';
import { config, getAgentConfig, getTaskStatusConfig } from '../config';
import { getErrorMessage, logError } from '../utils/error-handler';

import AgentNode from './nodes/AgentNode';

const API_URL = config.API_URL;

const nodeTypes = {
  agent: AgentNode,
};

// Main Component
const EnhancedSystemOrchestrator: React.FC = () => {
  const [agents, setAgents] = useState<any[]>([]);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [selectedAgent, setSelectedAgent] = useState<any>(null);
  const [taskInput, setTaskInput] = useState({ name: '', description: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Fetch all data on mount and periodically
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch agents
        const agentsRes = await axios.get(`${API_URL}/api/agents`);
        setAgents(agentsRes.data);

        // Fetch system health
        const healthRes = await axios.get(`${API_URL}/api/system/health`);
        setSystemHealth(healthRes.data);

        // Fetch queue stats
        const queueRes = await axios.get(`${API_URL}/api/queue/tasks`);
        setTasks(queueRes.data);

        setError(null);
      } catch (err) {
        console.error('Failed to fetch data:', err);
        setError('Failed to fetch system data');
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  // Generate nodes from agents with better positioning
  useEffect(() => {
    const generateNodesFromAgents = () => {
      const agentNodes: Node[] = agents.map((agent, index) => {
        // Arrange agents in a hierarchical layout
        let position = { x: 0, y: 0 };

        if (agent.id === 'master') {
          position = { x: 400, y: 50 };
        } else if (agent.id === 'supervisor') {
          position = { x: 400, y: 200 };
        } else {
          // Arrange other agents in a semicircle below
          const angle = (Math.PI / (agents.length - 2)) * (index - 2);
          position = {
            x: 400 + Math.cos(angle) * 300,
            y: 400 + Math.sin(angle) * 150
          };
        }

        return {
          id: agent.id,
          type: 'agent',
          position,
          data: {
            ...agent,
            label: agent.name
          },
          sourcePosition: Position.Bottom,
          targetPosition: Position.Top,
        };
      });

      setNodes(agentNodes);

      // Create edges showing hierarchy
      const hierarchyEdges: Edge[] = [];

      // Master -> Supervisor
      if (agents.find(a => a.id === 'master') && agents.find(a => a.id === 'supervisor')) {
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

      // Supervisor -> Other agents
      const supervisor = agents.find(a => a.id === 'supervisor');
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

      setEdges(hierarchyEdges);
    };

    generateNodesFromAgents();
  }, [agents]);

  // Execute task
  const executeTask = async () => {
    if (!taskInput.name || !taskInput.description) {
      setError('Please provide task name and description');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await axios.post(`${API_URL}/api/tasks/execute`, {
        name: taskInput.name,
        description: taskInput.description,
        agent_id: selectedAgent?.id
      });

      setSuccess(`Task "${taskInput.name}" submitted successfully`);
      setTaskInput({ name: '', description: '' });

      // Refresh tasks
      const queueRes = await axios.get(`${API_URL}/api/queue/tasks`);
      setTasks(queueRes.data);
    } catch (err) {
      const errorMsg = getErrorMessage(err);
      logError('executeTask', err);
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    const agent = agents.find(a => a.id === node.id);
    setSelectedAgent(agent);
  }, [agents]);

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Enhanced Header with Health Status */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <h1 className="text-2xl font-bold text-white">
              🎯 System Orchestrator
            </h1>
            <div className="flex items-center space-x-4 text-sm">
              <span className={`flex items-center ${
                systemHealth?.status === 'healthy' ? 'text-green-400' : 'text-yellow-400'
              }`}>
                <span className={`w-2 h-2 rounded-full mr-2 ${
                  systemHealth?.status === 'healthy' ? 'bg-green-500' : 'bg-yellow-500'
                } animate-pulse`}></span>
                System: {systemHealth?.status || 'checking...'}
              </span>
              <span className="text-gray-400">|</span>
              <span className="text-gray-300">
                Agents: {agents.length}
              </span>
              <span className="text-gray-400">|</span>
              <span className="text-gray-300">
                Tasks: {tasks.length}
              </span>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => window.location.reload()}
              className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm text-white transition-colors"
            >
              🔄 Refresh
            </button>
            <button
              onClick={() => window.open(`${API_URL}/docs`, '_blank')}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm text-white transition-colors"
            >
              📚 API Docs
            </button>
          </div>
        </div>
      </header>

      {/* Alert Messages */}
      {error && (
        <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-2 flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-200">✕</button>
        </div>
      )}
      {success && (
        <div className="bg-green-900/50 border border-green-500 text-green-200 px-4 py-2 flex items-center justify-between">
          <span>{success}</span>
          <button onClick={() => setSuccess(null)} className="text-green-400 hover:text-green-200">✕</button>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Sidebar */}
        <aside className="w-80 bg-gray-800 border-r border-gray-700 flex flex-col">
          {/* Task Execution */}
          <div className="p-4 border-b border-gray-700">
            <h2 className="text-lg font-semibold text-white mb-3">Execute Task</h2>

            {selectedAgent && (
              <div className="mb-3 p-2 bg-gray-700 rounded">
                <span className="text-xs text-gray-400">Selected Agent:</span>
                <div className="text-sm text-white font-medium">{selectedAgent.name}</div>
              </div>
            )}

            <input
              type="text"
              placeholder="Task name"
              value={taskInput.name}
              onChange={(e) => setTaskInput({ ...taskInput, name: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none mb-2"
            />

            <textarea
              placeholder="Task description"
              value={taskInput.description}
              onChange={(e) => setTaskInput({ ...taskInput, description: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none mb-3 h-24 resize-none"
            />

            <button
              onClick={executeTask}
              disabled={loading}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded transition-colors font-medium"
            >
              {loading ? '⏳ Executing...' : '🚀 Execute Task'}
            </button>
          </div>

          {/* Active Tasks */}
          <div className="flex-1 p-4 overflow-y-auto">
            <h3 className="text-lg font-semibold text-white mb-3">Active Tasks</h3>
            <div className="space-y-2">
              {tasks.length === 0 ? (
                <p className="text-gray-500 text-sm">No active tasks</p>
              ) : (
                tasks.slice(0, 10).map((task: any) => (
                  <div key={task.id} className="p-2 bg-gray-700 rounded">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-white truncate">{task.name}</span>
                      <span className={`text-xs px-2 py-1 rounded ${
                        task.status === 'completed' ? 'bg-green-900 text-green-300' :
                        task.status === 'failed' ? 'bg-red-900 text-red-300' :
                        task.status === 'processing' ? 'bg-blue-900 text-blue-300' :
                        'bg-yellow-900 text-yellow-300'
                      }`}>
                        {task.status}
                      </span>
                    </div>
                    {task.actor && (
                      <div className="text-xs text-gray-400 mt-1">
                        Agent: {task.actor}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </aside>

        {/* Workflow Visualization */}
        <main className="flex-1 relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            connectionMode={ConnectionMode.Loose}
            fitView
            className="bg-gray-900"
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

            {/* System Metrics Panel */}
            <Panel position="top-right" className="bg-gray-800/90 backdrop-blur rounded-lg p-4 m-4 min-w-[250px]">
              <h3 className="text-lg font-semibold text-white mb-3">System Metrics</h3>

              {systemHealth && (
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Redis:</span>
                    <span className={`font-medium ${
                      systemHealth.components?.redis?.status === 'healthy' ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {systemHealth.components?.redis?.status || 'unknown'}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-gray-400">Uptime:</span>
                    <span className="text-white font-medium">
                      {systemHealth.uptime_human || '0m'}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-gray-400">Online Agents:</span>
                    <span className="text-green-400 font-medium">
                      {agents.filter(a => a.status === 'online').length}/{agents.length}
                    </span>
                  </div>

                  {systemHealth.components?.redis?.details && (
                    <>
                      <div className="border-t border-gray-700 pt-2 mt-2">
                        <div className="text-xs text-gray-500 mb-1">Redis Details:</div>
                        <div className="flex justify-between">
                          <span className="text-gray-400 text-xs">Memory:</span>
                          <span className="text-white text-xs">
                            {systemHealth.components.redis.details.used_memory_human}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400 text-xs">Clients:</span>
                          <span className="text-white text-xs">
                            {systemHealth.components.redis.details.connected_clients}
                          </span>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              )}
            </Panel>
          </ReactFlow>
        </main>
      </div>
    </div>
  );
};

// Wrapper Component
const EnhancedSystemOrchestratorWrapper: React.FC = () => {
  return (
    <ReactFlowProvider>
      <EnhancedSystemOrchestrator />
    </ReactFlowProvider>
  );
};

export default EnhancedSystemOrchestratorWrapper;