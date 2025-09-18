import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { Node, Edge } from 'reactflow';

interface WorkflowExecution {
  id: string;
  workflowId: string;
  status: 'pending' | 'running' | 'success' | 'error';
  startTime: Date;
  endTime?: Date;
  logs: Array<{
    timestamp: Date;
    nodeId: string;
    message: string;
    level: 'info' | 'warning' | 'error';
  }>;
  results?: Record<string, any>;
}

interface Workflow {
  id: string;
  name: string;
  description?: string;
  nodes: Node[];
  edges: Edge[];
  createdAt: Date;
  updatedAt: Date;
  lastExecutionId?: string;
  isActive: boolean;
  tags?: string[];
  version: number;
}

interface WorkflowStore {
  // State
  workflows: Workflow[];
  currentWorkflow: Workflow | null;
  executions: WorkflowExecution[];
  isExecuting: boolean;
  selectedNodeId: string | null;

  // Actions
  createWorkflow: (name: string, description?: string) => void;
  updateWorkflow: (id: string, updates: Partial<Workflow>) => void;
  deleteWorkflow: (id: string) => void;
  loadWorkflow: (id: string) => void;
  saveCurrentWorkflow: () => void;

  // Execution
  executeWorkflow: (workflowId: string) => Promise<void>;
  stopExecution: (executionId: string) => void;
  getExecutionLogs: (executionId: string) => WorkflowExecution['logs'];

  // Node operations
  addNode: (node: Node) => void;
  updateNode: (nodeId: string, updates: Partial<Node>) => void;
  deleteNode: (nodeId: string) => void;
  selectNode: (nodeId: string | null) => void;

  // Edge operations
  addEdge: (edge: Edge) => void;
  updateEdge: (edgeId: string, updates: Partial<Edge>) => void;
  deleteEdge: (edgeId: string) => void;

  // Import/Export
  exportWorkflow: (workflowId: string) => string;
  importWorkflow: (jsonData: string) => void;

  // Utils
  duplicateWorkflow: (workflowId: string) => void;
  clearExecutions: () => void;
  getWorkflowStats: (workflowId: string) => {
    totalExecutions: number;
    successRate: number;
    averageDuration: number;
  };
}

export const useWorkflowStore = create<WorkflowStore>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        workflows: [],
        currentWorkflow: null,
        executions: [],
        isExecuting: false,
        selectedNodeId: null,

        // Create new workflow
        createWorkflow: (name, description) => {
          const newWorkflow: Workflow = {
            id: `workflow_${Date.now()}`,
            name,
            description,
            nodes: [],
            edges: [],
            createdAt: new Date(),
            updatedAt: new Date(),
            isActive: true,
            version: 1,
            tags: []
          };

          set((state) => ({
            workflows: [...state.workflows, newWorkflow],
            currentWorkflow: newWorkflow
          }));
        },

        // Update workflow
        updateWorkflow: (id, updates) => {
          set((state) => ({
            workflows: state.workflows.map((wf) =>
              wf.id === id
                ? { ...wf, ...updates, updatedAt: new Date() }
                : wf
            ),
            currentWorkflow:
              state.currentWorkflow?.id === id
                ? { ...state.currentWorkflow, ...updates, updatedAt: new Date() }
                : state.currentWorkflow
          }));
        },

        // Delete workflow
        deleteWorkflow: (id) => {
          set((state) => ({
            workflows: state.workflows.filter((wf) => wf.id !== id),
            currentWorkflow:
              state.currentWorkflow?.id === id ? null : state.currentWorkflow
          }));
        },

        // Load workflow
        loadWorkflow: (id) => {
          const workflow = get().workflows.find((wf) => wf.id === id);
          if (workflow) {
            set({ currentWorkflow: workflow });
          }
        },

        // Save current workflow
        saveCurrentWorkflow: () => {
          const { currentWorkflow } = get();
          if (currentWorkflow) {
            get().updateWorkflow(currentWorkflow.id, {
              nodes: currentWorkflow.nodes,
              edges: currentWorkflow.edges
            });
          }
        },

        // Execute workflow
        executeWorkflow: async (workflowId) => {
          const workflow = get().workflows.find((wf) => wf.id === workflowId);
          if (!workflow) return;

          const execution: WorkflowExecution = {
            id: `exec_${Date.now()}`,
            workflowId,
            status: 'running',
            startTime: new Date(),
            logs: []
          };

          set((state) => ({
            executions: [...state.executions, execution],
            isExecuting: true
          }));

          // Simulate workflow execution
          try {
            for (const node of workflow.nodes) {
              // Add log entry
              execution.logs.push({
                timestamp: new Date(),
                nodeId: node.id,
                message: `Executing node: ${node.data?.label || node.id}`,
                level: 'info'
              });

              // Simulate processing time
              await new Promise((resolve) => setTimeout(resolve, 1000));
            }

            // Mark as successful
            set((state) => ({
              executions: state.executions.map((ex) =>
                ex.id === execution.id
                  ? { ...ex, status: 'success', endTime: new Date() }
                  : ex
              ),
              isExecuting: false
            }));
          } catch (error) {
            // Mark as error
            set((state) => ({
              executions: state.executions.map((ex) =>
                ex.id === execution.id
                  ? { ...ex, status: 'error', endTime: new Date() }
                  : ex
              ),
              isExecuting: false
            }));
          }
        },

        // Stop execution
        stopExecution: (executionId) => {
          set((state) => ({
            executions: state.executions.map((ex) =>
              ex.id === executionId
                ? { ...ex, status: 'error', endTime: new Date() }
                : ex
            ),
            isExecuting: false
          }));
        },

        // Get execution logs
        getExecutionLogs: (executionId) => {
          const execution = get().executions.find((ex) => ex.id === executionId);
          return execution?.logs || [];
        },

        // Add node
        addNode: (node) => {
          set((state) => ({
            currentWorkflow: state.currentWorkflow
              ? {
                  ...state.currentWorkflow,
                  nodes: [...state.currentWorkflow.nodes, node]
                }
              : state.currentWorkflow
          }));
        },

        // Update node
        updateNode: (nodeId, updates) => {
          set((state) => ({
            currentWorkflow: state.currentWorkflow
              ? {
                  ...state.currentWorkflow,
                  nodes: state.currentWorkflow.nodes.map((node) =>
                    node.id === nodeId ? { ...node, ...updates } : node
                  )
                }
              : state.currentWorkflow
          }));
        },

        // Delete node
        deleteNode: (nodeId) => {
          set((state) => ({
            currentWorkflow: state.currentWorkflow
              ? {
                  ...state.currentWorkflow,
                  nodes: state.currentWorkflow.nodes.filter(
                    (node) => node.id !== nodeId
                  ),
                  edges: state.currentWorkflow.edges.filter(
                    (edge) => edge.source !== nodeId && edge.target !== nodeId
                  )
                }
              : state.currentWorkflow
          }));
        },

        // Select node
        selectNode: (nodeId) => {
          set({ selectedNodeId: nodeId });
        },

        // Add edge
        addEdge: (edge) => {
          set((state) => ({
            currentWorkflow: state.currentWorkflow
              ? {
                  ...state.currentWorkflow,
                  edges: [...state.currentWorkflow.edges, edge]
                }
              : state.currentWorkflow
          }));
        },

        // Update edge
        updateEdge: (edgeId, updates) => {
          set((state) => ({
            currentWorkflow: state.currentWorkflow
              ? {
                  ...state.currentWorkflow,
                  edges: state.currentWorkflow.edges.map((edge) =>
                    edge.id === edgeId ? { ...edge, ...updates } : edge
                  )
                }
              : state.currentWorkflow
          }));
        },

        // Delete edge
        deleteEdge: (edgeId) => {
          set((state) => ({
            currentWorkflow: state.currentWorkflow
              ? {
                  ...state.currentWorkflow,
                  edges: state.currentWorkflow.edges.filter(
                    (edge) => edge.id !== edgeId
                  )
                }
              : state.currentWorkflow
          }));
        },

        // Export workflow
        exportWorkflow: (workflowId) => {
          const workflow = get().workflows.find((wf) => wf.id === workflowId);
          return JSON.stringify(workflow, null, 2);
        },

        // Import workflow
        importWorkflow: (jsonData) => {
          try {
            const workflow = JSON.parse(jsonData) as Workflow;
            workflow.id = `workflow_${Date.now()}`;
            workflow.createdAt = new Date();
            workflow.updatedAt = new Date();

            set((state) => ({
              workflows: [...state.workflows, workflow],
              currentWorkflow: workflow
            }));
          } catch (error) {
            console.error('Failed to import workflow:', error);
          }
        },

        // Duplicate workflow
        duplicateWorkflow: (workflowId) => {
          const workflow = get().workflows.find((wf) => wf.id === workflowId);
          if (workflow) {
            const duplicated = {
              ...workflow,
              id: `workflow_${Date.now()}`,
              name: `${workflow.name} (Copy)`,
              createdAt: new Date(),
              updatedAt: new Date()
            };

            set((state) => ({
              workflows: [...state.workflows, duplicated]
            }));
          }
        },

        // Clear executions
        clearExecutions: () => {
          set({ executions: [] });
        },

        // Get workflow stats
        getWorkflowStats: (workflowId) => {
          const executions = get().executions.filter(
            (ex) => ex.workflowId === workflowId
          );

          const successful = executions.filter((ex) => ex.status === 'success');
          const successRate = executions.length > 0
            ? (successful.length / executions.length) * 100
            : 0;

          const durations = successful
            .filter((ex) => ex.endTime)
            .map((ex) => ex.endTime!.getTime() - ex.startTime.getTime());

          const averageDuration = durations.length > 0
            ? durations.reduce((a, b) => a + b, 0) / durations.length
            : 0;

          return {
            totalExecutions: executions.length,
            successRate,
            averageDuration
          };
        }
      }),
      {
        name: 'workflow-store',
        partialize: (state) => ({
          workflows: state.workflows,
          executions: state.executions
        })
      }
    )
  )
);