import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface Agent {
  id: string;
  name: string;
  type: 'supervisor' | 'master' | 'backend-api' | 'database' | 'frontend-ui' | 'testing' | 'instagram' | 'queue-manager' | 'deployment';
  status: 'online' | 'offline' | 'busy' | 'error';
  sessionId: string;
  capabilities: string[];
  currentTask?: {
    id: string;
    description: string;
    progress: number;
    startTime: Date;
  };
  stats: {
    tasksCompleted: number;
    tasksFailed: number;
    averageResponseTime: number;
    uptime: number;
  };
  lastActivity: Date;
  config: Record<string, any>;
}

interface AgentMessage {
  id: string;
  agentId: string;
  type: 'command' | 'response' | 'status' | 'error';
  content: string;
  timestamp: Date;
  metadata?: Record<string, any>;
}

interface AgentStore {
  // State
  agents: Agent[];
  messages: AgentMessage[];
  selectedAgentId: string | null;
  connectionStatus: 'connected' | 'disconnected' | 'connecting';

  // Actions
  connectToAgents: () => Promise<void>;
  disconnectFromAgents: () => void;

  // Agent operations
  sendCommand: (agentId: string, command: string) => Promise<void>;
  getAgentById: (agentId: string) => Agent | undefined;
  updateAgentStatus: (agentId: string, status: Agent['status']) => void;
  selectAgent: (agentId: string | null) => void;

  // Task operations
  assignTask: (agentId: string, task: string) => Promise<void>;
  completeTask: (agentId: string, taskId: string) => void;
  getAgentTasks: (agentId: string) => Agent['currentTask'][];

  // Message operations
  addMessage: (message: Omit<AgentMessage, 'id' | 'timestamp'>) => void;
  getAgentMessages: (agentId: string) => AgentMessage[];
  clearMessages: (agentId?: string) => void;

  // Monitoring
  getAgentStats: (agentId: string) => Agent['stats'] | undefined;
  getSystemHealth: () => {
    totalAgents: number;
    onlineAgents: number;
    busyAgents: number;
    errorAgents: number;
  };

  // Utils
  refreshAgentStatus: () => Promise<void>;
  exportAgentLogs: (agentId: string) => string;
}

export const useAgentStore = create<AgentStore>()(
  devtools(
    (set, get) => ({
      // Initial state
      agents: [
        {
          id: 'supervisor',
          name: 'Supervisor Agent',
          type: 'supervisor',
          status: 'offline',
          sessionId: 'claude-supervisor',
          capabilities: ['task-delegation', 'coordination', 'monitoring'],
          stats: { tasksCompleted: 0, tasksFailed: 0, averageResponseTime: 0, uptime: 0 },
          lastActivity: new Date(),
          config: {}
        },
        {
          id: 'master',
          name: 'Master Agent',
          type: 'master',
          status: 'offline',
          sessionId: 'claude-master',
          capabilities: ['crisis-management', 'strategic-planning', 'override'],
          stats: { tasksCompleted: 0, tasksFailed: 0, averageResponseTime: 0, uptime: 0 },
          lastActivity: new Date(),
          config: {}
        },
        {
          id: 'backend-api',
          name: 'Backend API Agent',
          type: 'backend-api',
          status: 'offline',
          sessionId: 'claude-backend-api',
          capabilities: ['api-development', 'endpoint-creation', 'integration'],
          stats: { tasksCompleted: 0, tasksFailed: 0, averageResponseTime: 0, uptime: 0 },
          lastActivity: new Date(),
          config: {}
        },
        {
          id: 'database',
          name: 'Database Agent',
          type: 'database',
          status: 'offline',
          sessionId: 'claude-database',
          capabilities: ['schema-design', 'query-optimization', 'migration'],
          stats: { tasksCompleted: 0, tasksFailed: 0, averageResponseTime: 0, uptime: 0 },
          lastActivity: new Date(),
          config: {}
        },
        {
          id: 'frontend-ui',
          name: 'Frontend UI Agent',
          type: 'frontend-ui',
          status: 'offline',
          sessionId: 'claude-frontend-ui',
          capabilities: ['ui-design', 'component-development', 'responsive-design'],
          stats: { tasksCompleted: 0, tasksFailed: 0, averageResponseTime: 0, uptime: 0 },
          lastActivity: new Date(),
          config: {}
        },
        {
          id: 'testing',
          name: 'Testing Agent',
          type: 'testing',
          status: 'offline',
          sessionId: 'claude-testing',
          capabilities: ['unit-testing', 'integration-testing', 'e2e-testing'],
          stats: { tasksCompleted: 0, tasksFailed: 0, averageResponseTime: 0, uptime: 0 },
          lastActivity: new Date(),
          config: {}
        },
        {
          id: 'instagram',
          name: 'Instagram Agent',
          type: 'instagram',
          status: 'offline',
          sessionId: 'claude-instagram',
          capabilities: ['social-integration', 'content-posting', 'analytics'],
          stats: { tasksCompleted: 0, tasksFailed: 0, averageResponseTime: 0, uptime: 0 },
          lastActivity: new Date(),
          config: {}
        },
        {
          id: 'queue-manager',
          name: 'Queue Manager Agent',
          type: 'queue-manager',
          status: 'offline',
          sessionId: 'claude-queue-manager',
          capabilities: ['queue-management', 'task-scheduling', 'load-balancing'],
          stats: { tasksCompleted: 0, tasksFailed: 0, averageResponseTime: 0, uptime: 0 },
          lastActivity: new Date(),
          config: {}
        },
        {
          id: 'deployment',
          name: 'Deployment Agent',
          type: 'deployment',
          status: 'offline',
          sessionId: 'claude-deployment',
          capabilities: ['ci-cd', 'deployment', 'infrastructure'],
          stats: { tasksCompleted: 0, tasksFailed: 0, averageResponseTime: 0, uptime: 0 },
          lastActivity: new Date(),
          config: {}
        }
      ],
      messages: [],
      selectedAgentId: null,
      connectionStatus: 'disconnected',

      // Connect to all agents
      connectToAgents: async () => {
        set({ connectionStatus: 'connecting' });

        try {
          // Simulate connection to TMUX sessions
          await new Promise((resolve) => setTimeout(resolve, 1000));

          // Update all agents to online
          set((state) => ({
            agents: state.agents.map((agent) => ({
              ...agent,
              status: 'online',
              lastActivity: new Date()
            })),
            connectionStatus: 'connected'
          }));

          get().addMessage({
            agentId: 'system',
            type: 'status',
            content: 'Successfully connected to all agents'
          });
        } catch (error) {
          set({ connectionStatus: 'disconnected' });

          get().addMessage({
            agentId: 'system',
            type: 'error',
            content: `Failed to connect: ${error}`
          });
        }
      },

      // Disconnect from agents
      disconnectFromAgents: () => {
        set((state) => ({
          agents: state.agents.map((agent) => ({
            ...agent,
            status: 'offline'
          })),
          connectionStatus: 'disconnected'
        }));
      },

      // Send command to agent
      sendCommand: async (agentId, command) => {
        const agent = get().getAgentById(agentId);
        if (!agent || agent.status === 'offline') {
          throw new Error(`Agent ${agentId} is not available`);
        }

        // Add command message
        get().addMessage({
          agentId,
          type: 'command',
          content: command
        });

        // Update agent to busy
        get().updateAgentStatus(agentId, 'busy');

        try {
          // Simulate command execution
          await new Promise((resolve) => setTimeout(resolve, 2000));

          // Add response message
          get().addMessage({
            agentId,
            type: 'response',
            content: `Executed: ${command}`
          });

          // Update agent back to online
          get().updateAgentStatus(agentId, 'online');
        } catch (error) {
          get().updateAgentStatus(agentId, 'error');
          get().addMessage({
            agentId,
            type: 'error',
            content: `Failed to execute: ${error}`
          });
        }
      },

      // Get agent by ID
      getAgentById: (agentId) => {
        return get().agents.find((agent) => agent.id === agentId);
      },

      // Update agent status
      updateAgentStatus: (agentId, status) => {
        set((state) => ({
          agents: state.agents.map((agent) =>
            agent.id === agentId
              ? { ...agent, status, lastActivity: new Date() }
              : agent
          )
        }));
      },

      // Select agent
      selectAgent: (agentId) => {
        set({ selectedAgentId: agentId });
      },

      // Assign task to agent
      assignTask: async (agentId, task) => {
        const taskId = `task_${Date.now()}`;

        set((state) => ({
          agents: state.agents.map((agent) =>
            agent.id === agentId
              ? {
                  ...agent,
                  currentTask: {
                    id: taskId,
                    description: task,
                    progress: 0,
                    startTime: new Date()
                  },
                  status: 'busy'
                }
              : agent
          )
        }));

        await get().sendCommand(agentId, task);
      },

      // Complete task
      completeTask: (agentId, taskId) => {
        set((state) => ({
          agents: state.agents.map((agent) =>
            agent.id === agentId && agent.currentTask?.id === taskId
              ? {
                  ...agent,
                  currentTask: undefined,
                  status: 'online',
                  stats: {
                    ...agent.stats,
                    tasksCompleted: agent.stats.tasksCompleted + 1
                  }
                }
              : agent
          )
        }));
      },

      // Get agent tasks
      getAgentTasks: (agentId) => {
        const agent = get().getAgentById(agentId);
        return agent?.currentTask ? [agent.currentTask] : [];
      },

      // Add message
      addMessage: (message) => {
        set((state) => ({
          messages: [
            ...state.messages,
            {
              ...message,
              id: `msg_${Date.now()}`,
              timestamp: new Date()
            }
          ].slice(-100) // Keep only last 100 messages
        }));
      },

      // Get agent messages
      getAgentMessages: (agentId) => {
        return get().messages.filter((msg) => msg.agentId === agentId);
      },

      // Clear messages
      clearMessages: (agentId) => {
        if (agentId) {
          set((state) => ({
            messages: state.messages.filter((msg) => msg.agentId !== agentId)
          }));
        } else {
          set({ messages: [] });
        }
      },

      // Get agent stats
      getAgentStats: (agentId) => {
        const agent = get().getAgentById(agentId);
        return agent?.stats;
      },

      // Get system health
      getSystemHealth: () => {
        const agents = get().agents;
        return {
          totalAgents: agents.length,
          onlineAgents: agents.filter((a) => a.status === 'online').length,
          busyAgents: agents.filter((a) => a.status === 'busy').length,
          errorAgents: agents.filter((a) => a.status === 'error').length
        };
      },

      // Refresh agent status
      refreshAgentStatus: async () => {
        // Simulate checking TMUX sessions
        await new Promise((resolve) => setTimeout(resolve, 500));

        set((state) => ({
          agents: state.agents.map((agent) => ({
            ...agent,
            lastActivity: new Date()
          }))
        }));
      },

      // Export agent logs
      exportAgentLogs: (agentId) => {
        const messages = get().getAgentMessages(agentId);
        const agent = get().getAgentById(agentId);

        const logs = {
          agent: agent?.name,
          agentId,
          exportDate: new Date().toISOString(),
          messages: messages.map((msg) => ({
            timestamp: msg.timestamp,
            type: msg.type,
            content: msg.content,
            metadata: msg.metadata
          }))
        };

        return JSON.stringify(logs, null, 2);
      }
    })
  )
);