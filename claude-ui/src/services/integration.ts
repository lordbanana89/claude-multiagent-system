/**
 * Integration Service
 * Handles communication between all components through the Integration Orchestrator
 */

import axios from 'axios';
import { config } from '../config';

const INTEGRATION_API = 'http://localhost:5002';

export interface SystemHealth {
  database: boolean;
  redis: boolean;
  api: boolean;
  gateway: boolean;
  agents: Record<string, boolean>;
  frontend: boolean;
}

export interface TaskExecution {
  task_id: string;
  agent: string;
  status: string;
  timestamp: string;
}

export interface Message {
  sender: string;
  recipient: string;
  content: string;
  priority?: string;
}

class IntegrationService {
  private healthCheckInterval: ReturnType<typeof setInterval> | null = null;
  private lastHealth: SystemHealth | null = null;

  /**
   * Get current system health
   */
  async getSystemHealth(): Promise<SystemHealth> {
    try {
      const response = await axios.get(`${INTEGRATION_API}/api/integration/health`);
      this.lastHealth = response.data;
      return response.data;
    } catch (error) {
      console.error('Failed to get system health:', error);
      return this.lastHealth || {
        database: false,
        redis: false,
        api: false,
        gateway: false,
        agents: {},
        frontend: false,
      };
    }
  }

  /**
   * Force sync all components
   */
  async syncAll(): Promise<boolean> {
    try {
      const response = await axios.get(`${INTEGRATION_API}/api/integration/sync`);
      return response.data.status === 'synced';
    } catch (error) {
      console.error('Failed to sync components:', error);
      return false;
    }
  }

  /**
   * Route a message to an agent
   */
  async routeMessage(message: Message): Promise<boolean> {
    try {
      const response = await axios.post(`${INTEGRATION_API}/api/integration/route`, message);
      return response.data.success;
    } catch (error) {
      console.error('Failed to route message:', error);
      return false;
    }
  }

  /**
   * Execute a task through an agent
   */
  async executeTask(agent: string, task: any): Promise<TaskExecution | null> {
    try {
      const response = await axios.post(`${INTEGRATION_API}/api/integration/execute`, {
        agent,
        task,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to execute task:', error);
      return null;
    }
  }

  /**
   * Broadcast message to all agents
   */
  async broadcast(message: string, priority: string = 'normal'): Promise<any[]> {
    try {
      const response = await axios.post(`${INTEGRATION_API}/api/integration/broadcast`, {
        message,
        priority,
      });
      return response.data.results || [];
    } catch (error) {
      console.error('Failed to broadcast message:', error);
      return [];
    }
  }

  /**
   * Execute custom agent from Agent Builder
   */
  async executeCustomAgent(agentConfig: any, input: string): Promise<any> {
    try {
      // First, deploy the agent if not already deployed
      const deployResponse = await axios.post(`${config.API_MAIN_URL}/api/agents/deploy`, agentConfig);

      if (!deployResponse.data.success) {
        throw new Error('Failed to deploy agent');
      }

      const agentId = deployResponse.data.agent_id;

      // Execute task through the deployed agent
      const task = {
        title: `Custom Agent Execution: ${agentConfig.name}`,
        command: input,
        skills: agentConfig.skills,
        knowledge: agentConfig.knowledge,
      };

      return await this.executeTask(agentId, task);
    } catch (error) {
      console.error('Failed to execute custom agent:', error);
      throw error;
    }
  }

  /**
   * Get knowledge graph data
   */
  async getKnowledgeGraph(): Promise<any> {
    try {
      const response = await axios.get(`${config.API_MAIN_URL}/api/knowledge/graph`);
      return response.data;
    } catch (error) {
      console.error('Failed to get knowledge graph:', error);
      return { nodes: [], edges: [] };
    }
  }

  /**
   * Link knowledge to agent
   */
  async linkKnowledgeToAgent(agentId: string, knowledgeNodeId: string): Promise<boolean> {
    try {
      await this.routeMessage({
        sender: 'knowledge-graph',
        recipient: agentId,
        content: `KNOWLEDGE_UPDATE: ${knowledgeNodeId}`,
        priority: 'high',
      });
      return true;
    } catch (error) {
      console.error('Failed to link knowledge to agent:', error);
      return false;
    }
  }

  /**
   * Start continuous health monitoring
   */
  startHealthMonitoring(callback: (health: SystemHealth) => void, interval: number = 5000): void {
    this.stopHealthMonitoring();

    // Initial check
    this.getSystemHealth().then(callback);

    // Periodic checks
    this.healthCheckInterval = setInterval(async () => {
      const health = await this.getSystemHealth();
      callback(health);
    }, interval);
  }

  /**
   * Stop health monitoring
   */
  stopHealthMonitoring(): void {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
    }
  }

  /**
   * Get agent terminal output
   */
  async getAgentOutput(agentId: string, lines: number = 50): Promise<string[]> {
    try {
      const response = await axios.get(`${config.API_MAIN_URL}/api/agents/${agentId}/output`, {
        params: { lines },
      });
      return response.data.output || [];
    } catch (error) {
      console.error('Failed to get agent output:', error);
      return [];
    }
  }

  /**
   * Check if all core services are running
   */
  async checkCoreServices(): Promise<{
    allRunning: boolean;
    missing: string[];
  }> {
    const health = await this.getSystemHealth();
    const missing: string[] = [];

    if (!health.database) missing.push('Database');
    if (!health.redis) missing.push('Redis');
    if (!health.api) missing.push('Main API');
    if (!health.gateway) missing.push('Gateway');
    if (!health.frontend) missing.push('Frontend');

    // Check critical agents
    const criticalAgents = ['supervisor', 'master'];
    for (const agent of criticalAgents) {
      if (!health.agents[agent]) {
        missing.push(`Agent: ${agent}`);
      }
    }

    return {
      allRunning: missing.length === 0,
      missing,
    };
  }

  /**
   * Auto-fix missing services
   */
  async autoFixServices(): Promise<{
    fixed: string[];
    failed: string[];
  }> {
    const { missing } = await this.checkCoreServices();
    const fixed: string[] = [];
    const failed: string[] = [];

    for (const service of missing) {
      try {
        // Attempt to restart service
        if (service.startsWith('Agent:')) {
          const agentName = service.replace('Agent: ', '');
          await axios.post(`${config.API_MAIN_URL}/api/agents/${agentName}/restart`);
          fixed.push(service);
        } else {
          // For other services, trigger sync
          await this.syncAll();
          fixed.push(service);
        }
      } catch (error) {
        failed.push(service);
      }
    }

    return { fixed, failed };
  }
}

// Export singleton instance
export const integrationService = new IntegrationService();

// Export for use in React components
export default integrationService;