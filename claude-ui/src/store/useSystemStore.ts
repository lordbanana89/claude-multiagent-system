import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import axios, { AxiosError } from 'axios';
import { config } from '../config';
import { getErrorMessage, logError } from '../utils/error-handler';

const API_URL = config.API_URL;

interface Agent {
  id: string;
  name: string;
  status: 'idle' | 'busy' | 'error' | 'offline';
  currentTask?: string;
  lastActivity?: string;
  metrics?: {
    tasksCompleted: number;
    successRate: number;
    avgResponseTime: number;
  };
}

interface Task {
  id: string;
  name: string;
  description: string;
  agent?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  priority: number;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  result?: any;
  error?: string;
}

interface WorkflowNode {
  id: string;
  type: 'agent' | 'task' | 'decision' | 'queue';
  position: { x: number; y: number };
  data: any;
}

interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  type?: string;
  animated?: boolean;
  label?: string;
}

interface SystemMetrics {
  totalTasks: number;
  completedTasks: number;
  failedTasks: number;
  avgCompletionTime: number;
  systemLoad: number;
  queueSize: number;
}

interface SystemState {
  // Core entities
  agents: Map<string, Agent>;
  tasks: Map<string, Task>;
  workflow: {
    nodes: WorkflowNode[];
    edges: WorkflowEdge[];
  };

  // System state
  systemMetrics: SystemMetrics;
  activeView: 'orchestrator' | 'monitor' | 'history';
  selectedAgent: string | null;
  selectedTask: string | null;

  // Real-time connections
  wsConnected: boolean;
  notifications: Array<{
    id: string;
    type: 'info' | 'success' | 'warning' | 'error';
    message: string;
    timestamp: string;
  }>;

  // Actions
  setAgent: (agent: Agent) => void;
  removeAgent: (agentId: string) => void;

  addTask: (task: Task) => void;
  updateTask: (taskId: string, updates: Partial<Task>) => void;
  removeTask: (taskId: string) => void;

  executeTask: (taskName: string, description: string, agentId?: string) => Promise<void>;
  assignTaskToAgent: (taskId: string, agentId: string) => Promise<void>;

  updateWorkflow: (nodes: WorkflowNode[], edges: WorkflowEdge[]) => void;
  addWorkflowNode: (node: WorkflowNode) => void;
  removeWorkflowNode: (nodeId: string) => void;

  setActiveView: (view: 'orchestrator' | 'monitor' | 'history') => void;
  selectAgent: (agentId: string | null) => void;
  selectTask: (taskId: string | null) => void;

  setWsConnected: (connected: boolean) => void;
  addNotification: (type: 'info' | 'success' | 'warning' | 'error', message: string) => void;
  clearNotifications: () => void;

  fetchAgents: () => Promise<void>;
  fetchTasks: () => Promise<void>;
  fetchMetrics: () => Promise<void>;

  // WebSocket message handler
  handleWsMessage: (message: any) => void;
}

const useSystemStore = create<SystemState>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // Initial state
      agents: new Map(),
      tasks: new Map(),
      workflow: {
        nodes: [],
        edges: []
      },
      systemMetrics: {
        totalTasks: 0,
        completedTasks: 0,
        failedTasks: 0,
        avgCompletionTime: 0,
        systemLoad: 0,
        queueSize: 0
      },
      activeView: 'orchestrator',
      selectedAgent: null,
      selectedTask: null,
      wsConnected: false,
      notifications: [],

      // Agent actions
      setAgent: (agent) => set((state) => {
        const agents = new Map(state.agents);
        agents.set(agent.id, agent);
        return { agents };
      }),

      removeAgent: (agentId) => set((state) => {
        const agents = new Map(state.agents);
        agents.delete(agentId);
        return { agents };
      }),

      // Task actions
      addTask: (task) => set((state) => {
        const tasks = new Map(state.tasks);
        tasks.set(task.id, task);
        return { tasks };
      }),

      updateTask: (taskId, updates) => set((state) => {
        const tasks = new Map(state.tasks);
        const task = tasks.get(taskId);
        if (task) {
          tasks.set(taskId, { ...task, ...updates });
        }
        return { tasks };
      }),

      removeTask: (taskId) => set((state) => {
        const tasks = new Map(state.tasks);
        tasks.delete(taskId);
        return { tasks };
      }),

      executeTask: async (taskName, description, agentId) => {
        try {
          const response = await axios.post(`${API_URL}/api/tasks/execute`, {
            name: taskName,
            description,
            agent_id: agentId
          });

          const task = response.data;
          get().addTask(task);
          get().addNotification('success', `Task "${taskName}" submitted successfully`);
        } catch (error) {
          const errorMsg = getErrorMessage(error);
          logError('executeTask', error);
          get().addNotification('error', `Failed to execute task: ${errorMsg}`);
        }
      },

      assignTaskToAgent: async (taskId, agentId) => {
        try {
          await axios.post(`${API_URL}/api/tasks/${taskId}/assign`, {
            agent_id: agentId
          });

          get().updateTask(taskId, { agent: agentId });
          get().addNotification('success', `Task assigned to agent ${agentId}`);
        } catch (error) {
          const errorMsg = getErrorMessage(error);
          logError('assignTaskToAgent', error);
          get().addNotification('error', `Failed to assign task: ${errorMsg}`);
        }
      },

      // Workflow actions
      updateWorkflow: (nodes, edges) => set({
        workflow: { nodes, edges }
      }),

      addWorkflowNode: (node) => set((state) => ({
        workflow: {
          ...state.workflow,
          nodes: [...state.workflow.nodes, node]
        }
      })),

      removeWorkflowNode: (nodeId) => set((state) => ({
        workflow: {
          nodes: state.workflow.nodes.filter(n => n.id !== nodeId),
          edges: state.workflow.edges.filter(e => e.source !== nodeId && e.target !== nodeId)
        }
      })),

      // UI actions
      setActiveView: (view) => set({ activeView: view }),
      selectAgent: (agentId) => set({ selectedAgent: agentId }),
      selectTask: (taskId) => set({ selectedTask: taskId }),

      // Connection actions
      setWsConnected: (connected) => set({ wsConnected: connected }),

      // Notification actions
      addNotification: (type, message) => set((state) => ({
        notifications: [
          ...state.notifications,
          {
            id: Date.now().toString(),
            type,
            message,
            timestamp: new Date().toISOString()
          }
        ].slice(-10) // Keep only last 10 notifications
      })),

      clearNotifications: () => set({ notifications: [] }),

      // Data fetching
      fetchAgents: async () => {
        try {
          const response = await axios.get(`${API_URL}/api/agents`);
          const agents = new Map();
          response.data.forEach((agent: Agent) => {
            agents.set(agent.id, agent);
          });
          set({ agents });
        } catch (error) {
          get().addNotification('error', 'Failed to fetch agents');
        }
      },

      fetchTasks: async () => {
        try {
          const response = await axios.get(`${API_URL}/api/queue/tasks`);
          const tasks = new Map();
          response.data.forEach((task: any) => {
            tasks.set(task.id, {
              ...task,
              createdAt: task.created_at,
              startedAt: task.started_at,
              completedAt: task.completed_at
            });
          });
          set({ tasks });
        } catch (error) {
          get().addNotification('error', 'Failed to fetch tasks');
        }
      },

      fetchMetrics: async () => {
        try {
          const response = await axios.get(`${API_URL}/api/queue/stats`);
          const stats = response.data;
          set({
            systemMetrics: {
              totalTasks: stats.total,
              completedTasks: stats.completed,
              failedTasks: stats.failed,
              avgCompletionTime: stats.avgProcessingTime || 0,
              systemLoad: stats.processing,
              queueSize: stats.pending
            }
          });
        } catch (error) {
          get().addNotification('error', 'Failed to fetch metrics');
        }
      },

      // WebSocket message handler
      handleWsMessage: (message) => {
        const { type, data } = message;

        switch (type) {
          case 'agent_update':
            get().setAgent(data);
            break;

          case 'task_update':
            get().updateTask(data.id, data);
            break;

          case 'task_completed':
            get().updateTask(data.id, {
              status: 'completed',
              completedAt: new Date().toISOString(),
              result: data.result
            });
            get().addNotification('success', `Task "${data.name}" completed`);
            break;

          case 'task_failed':
            get().updateTask(data.id, {
              status: 'failed',
              error: data.error
            });
            get().addNotification('error', `Task "${data.name}" failed: ${data.error}`);
            break;

          case 'system_metrics':
            set({ systemMetrics: data });
            break;

          case 'notification':
            get().addNotification(data.type, data.message);
            break;

          default:
            console.log('Unknown WebSocket message type:', type);
        }
      }
    }))
  )
);

export default useSystemStore;