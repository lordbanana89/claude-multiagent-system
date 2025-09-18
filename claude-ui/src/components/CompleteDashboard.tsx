import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, {
  Controls,
  Background,
  MiniMap,
  ReactFlowProvider,
  ConnectionMode,
  addEdge,
  useNodesState,
  useEdgesState
} from 'reactflow';
import type { Node, Edge, Connection } from 'reactflow';
import 'reactflow/dist/style.css';
import axios from 'axios';
import { config } from '../config';
import { getErrorMessage, logError } from '../utils/error-handler';
import AgentNode from './nodes/AgentNode';
import wsManager from '../services/websocket';

// Components
import TerminalPanel from './panels/TerminalPanel';
import InboxPanel from './panels/InboxPanel';
import QueuePanel from './panels/QueuePanel';
import TaskExecutor from './panels/TaskExecutor';
import LogsPanel from './panels/LogsPanel';
import MetricsPanel from './panels/MetricsPanel';

// New Components
import WorkflowCanvas from './workflow/WorkflowCanvas';
import MultiTerminal from './terminal/MultiTerminal';
import PerformanceChart from './charts/PerformanceChart';

const API_URL = config.API_URL;

const nodeTypes = {
  agent: AgentNode,
};

interface TabItem {
  id: string;
  label: string;
  icon: string;
}

const tabs: TabItem[] = [
  { id: 'workflow', label: 'Workflow', icon: '🔄' },
  { id: 'builder', label: 'Builder', icon: '🔧' },
  { id: 'terminal', label: 'Terminal', icon: '💻' },
  { id: 'multi-terminal', label: 'Multi-Terminal', icon: '🖥️' },
  { id: 'inbox', label: 'Inbox', icon: '📨' },
  { id: 'queue', label: 'Queue', icon: '📋' },
  { id: 'logs', label: 'Logs', icon: '📜' },
  { id: 'metrics', label: 'Metrics', icon: '📊' },
  { id: 'performance', label: 'Performance', icon: '📈' },
];

const CompleteDashboard: React.FC = () => {
  // State Management
  const [activeTab, setActiveTab] = useState('workflow');
  const [agents, setAgents] = useState<any[]>([]);
  const [nodes, onNodesChange, setNodes] = useNodesState([]);
  const [edges, onEdgesChange, setEdges] = useEdgesState([]);
  const [selectedAgent, setSelectedAgent] = useState<any>(null);
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [tasks, setTasks] = useState<any[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [inboxMessages, setInboxMessages] = useState<any[]>([]);
  const [queueStatus, setQueueStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch all system data
  const fetchSystemData = async () => {
    try {
      setLoading(true);

      // Fetch agents
      const [agentsRes, healthRes, tasksRes, queueRes] = await Promise.all([
        axios.get(`${API_URL}/api/agents`),
        axios.get(`${API_URL}/api/system/health`),
        axios.get(`${API_URL}/api/queue/tasks`),
        axios.get(`${API_URL}/api/queue/status`)
      ]);

      setAgents(agentsRes.data);
      setSystemHealth(healthRes.data);
      setTasks(tasksRes.data);
      setQueueStatus(queueRes.data);

      // Generate workflow nodes from agents
      generateWorkflowNodes(agentsRes.data);

      setError(null);
    } catch (err) {
      const errorMsg = getErrorMessage(err);
      logError('fetchSystemData', err);
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // Generate workflow nodes
  const generateWorkflowNodes = (agentList: any[]) => {
    const agentNodes: Node[] = agentList.map((agent, index) => {
      let position = { x: 0, y: 0 };

      // Hierarchical positioning
      if (agent.id === 'master') {
        position = { x: 600, y: 50 };
      } else if (agent.id === 'supervisor') {
        position = { x: 600, y: 200 };
      } else {
        const angle = (Math.PI / (agentList.length - 2)) * (index - 2);
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

    const master = agentList.find(a => a.id === 'master');
    const supervisor = agentList.find(a => a.id === 'supervisor');

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
      agentList.filter(a => a.id !== 'master' && a.id !== 'supervisor').forEach(agent => {
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
  };

  // Handle edge connection
  const onConnect = useCallback((connection: Connection) => {
    setEdges((eds) => addEdge({
      ...connection,
      animated: true,
      style: { stroke: '#10b981' }
    }, eds));
  }, [setEdges]);

  // Handle node click
  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    const agent = agents.find(a => a.id === node.id);
    setSelectedAgent(agent);
  }, [agents]);

  // WebSocket message handler
  useEffect(() => {
    const handleWsMessage = (message: any) => {
      switch (message.type) {
        case 'agent_update':
          setAgents(prev => prev.map(a =>
            a.id === message.data.id ? { ...a, ...message.data } : a
          ));
          break;
        case 'task_update':
          setTasks(prev => [...prev, message.data]);
          break;
        case 'log':
          setLogs(prev => [...prev, message.data]);
          break;
        case 'inbox_message':
          setInboxMessages(prev => [...prev, message.data]);
          break;
      }
    };

    // Subscribe to WebSocket events
    if (wsManager) {
      // wsManager.on('message', handleWsMessage);
    }

    return () => {
      // Cleanup
    };
  }, []);

  // Initial fetch and polling
  useEffect(() => {
    fetchSystemData();
    const interval = setInterval(fetchSystemData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <h1 className="text-2xl font-bold text-white">
              🎯 Claude Multi-Agent System
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
                Agents: {agents.filter(a => a.status === 'online').length}/{agents.length}
              </span>
              <span className="text-gray-400">|</span>
              <span className="text-gray-300">
                Queue: {queueStatus?.pending || 0} pending
              </span>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => window.open(`${API_URL}/docs`, '_blank')}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm text-white transition-colors"
            >
              📚 API Docs
            </button>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <div className="bg-gray-800 border-b border-gray-700 px-6">
        <nav className="flex space-x-6">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'text-blue-400 border-blue-400'
                  : 'text-gray-400 border-transparent hover:text-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Alert Messages */}
      {error && (
        <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-2 flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-200">✕</button>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Task Executor & Agent Status */}
        <aside className="w-80 bg-gray-800 border-r border-gray-700 flex flex-col">
          <TaskExecutor
            agents={agents}
            selectedAgent={selectedAgent}
            onSelectAgent={setSelectedAgent}
          />

          {/* Agent Status List */}
          <div className="flex-1 p-4 overflow-y-auto">
            <h3 className="text-lg font-semibold text-white mb-3">Agent Status</h3>
            <div className="space-y-2">
              {agents.map(agent => (
                <div
                  key={agent.id}
                  onClick={() => setSelectedAgent(agent)}
                  className={`p-3 bg-gray-700 rounded cursor-pointer transition-all hover:bg-gray-600 ${
                    selectedAgent?.id === agent.id ? 'ring-2 ring-blue-500' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-white">{agent.name}</span>
                    <span className={`w-2 h-2 rounded-full ${
                      agent.status === 'online' ? 'bg-green-500' :
                      agent.status === 'busy' ? 'bg-yellow-500' :
                      'bg-gray-500'
                    }`}></span>
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    {agent.type} • {agent.sessionId}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </aside>

        {/* Main Content Panel */}
        <main className="flex-1 relative bg-gray-900">
          {activeTab === 'workflow' && (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
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
              <MetricsPanel systemHealth={systemHealth} agents={agents} />
            </ReactFlow>
          )}

          {activeTab === 'terminal' && (
            <TerminalPanel
              selectedAgent={selectedAgent}
              agents={agents}
            />
          )}

          {activeTab === 'inbox' && (
            <InboxPanel
              messages={inboxMessages}
              agents={agents}
              selectedAgent={selectedAgent}
            />
          )}

          {activeTab === 'queue' && (
            <QueuePanel
              tasks={tasks}
              queueStatus={queueStatus}
              agents={agents}
            />
          )}

          {activeTab === 'logs' && (
            <LogsPanel
              logs={logs}
              selectedAgent={selectedAgent}
              agents={agents}
            />
          )}

          {activeTab === 'metrics' && (
            <div className="p-6">
              <MetricsPanel
                systemHealth={systemHealth}
                agents={agents}
                detailed={true}
              />
            </div>
          )}

          {activeTab === 'builder' && (
            <WorkflowCanvas />
          )}

          {activeTab === 'multi-terminal' && (
            <MultiTerminal agents={agents} />
          )}

          {activeTab === 'performance' && (
            <div className="p-6">
              <h2 className="text-xl font-semibold text-white mb-4">System Performance</h2>
              <PerformanceChart />
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

// Wrapper Component
const CompleteDashboardWrapper: React.FC = () => {
  return (
    <ReactFlowProvider>
      <CompleteDashboard />
    </ReactFlowProvider>
  );
};

export default CompleteDashboardWrapper;