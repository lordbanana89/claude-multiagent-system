#!/usr/bin/env node

/**
 * Replicate MCP Dashboard to Figma
 * Creates exact visual representation of our React component
 */

const WebSocket = require('ws');

class MCPDashboardReplicator {
  constructor(channel) {
    this.channel = channel;
    this.ws = null;
    this.createdIds = [];
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket('ws://localhost:3055');

      this.ws.on('open', () => {
        console.log('✅ Connected to Figma');
        this.ws.send(JSON.stringify({
          type: 'join',
          channel: this.channel
        }));
        setTimeout(resolve, 500);
      });

      this.ws.on('error', reject);
    });
  }

  async sendCommand(command, params = {}) {
    return new Promise((resolve) => {
      const id = `cmd-${Date.now()}-${Math.random()}`;
      const message = {
        id,
        type: 'message',
        channel: this.channel,
        message: {
          id,
          command,
          params: { ...params, commandId: id }
        }
      };

      console.log(`→ ${command}: ${params.name || params.text || ''}`);
      this.ws.send(JSON.stringify(message));

      setTimeout(() => {
        this.createdIds.push(id);
        resolve(id);
      }, 100);
    });
  }

  async createMCPDashboard() {
    console.log('\n📊 Creating MCP Dashboard...');

    // Main Dashboard Container
    const dashboardId = await this.sendCommand('create_frame', {
      x: 100,
      y: 100,
      width: 1440,
      height: 900,
      name: 'MCP_Dashboard',
      fillColor: { r: 0.98, g: 0.98, b: 0.99, a: 1 }
    });

    // Header
    const headerId = await this.sendCommand('create_frame', {
      x: 0,
      y: 0,
      width: 1440,
      height: 80,
      name: 'Header',
      fillColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId: dashboardId
    });

    // Title
    await this.sendCommand('create_text', {
      x: 32,
      y: 28,
      text: '🎮 MCP System Control',
      fontSize: 24,
      fontWeight: 700,
      name: 'Dashboard_Title',
      parentId: headerId
    });

    // Server Status
    await this.sendCommand('create_frame', {
      x: 1200,
      y: 20,
      width: 200,
      height: 40,
      name: 'Server_Status',
      fillColor: { r: 0.2, g: 0.8, b: 0.4, a: 0.1 },
      parentId: headerId
    });

    await this.sendCommand('create_text', {
      x: 1220,
      y: 32,
      text: '● Server Running',
      fontSize: 14,
      fontWeight: 500,
      fontColor: { r: 0.2, g: 0.7, b: 0.3, a: 1 },
      parentId: headerId
    });

    // Stats Cards Container
    const statsContainer = await this.sendCommand('create_frame', {
      x: 32,
      y: 100,
      width: 1376,
      height: 120,
      name: 'Stats_Container',
      fillColor: { r: 0, g: 0, b: 0, a: 0 },
      parentId: dashboardId
    });

    // Create 4 stat cards
    const statsData = [
      { title: 'Total Activities', value: '1,234', icon: '📊', color: { r: 0.2, g: 0.5, b: 1 } },
      { title: 'Components', value: '56', icon: '🧩', color: { r: 0.5, g: 0.2, b: 1 } },
      { title: 'Active Agents', value: '9', icon: '🤖', color: { r: 0.2, g: 0.8, b: 0.4 } },
      { title: 'Conflicts', value: '0', icon: '⚠️', color: { r: 1, g: 0.5, b: 0.2 } }
    ];

    for (let i = 0; i < statsData.length; i++) {
      const stat = statsData[i];
      const cardX = i * 350;

      const cardId = await this.sendCommand('create_frame', {
        x: cardX,
        y: 0,
        width: 330,
        height: 120,
        name: `Stat_Card_${stat.title}`,
        fillColor: { r: 1, g: 1, b: 1, a: 1 },
        parentId: statsContainer
      });

      // Add shadow
      await this.sendCommand('set_effect', {
        nodeId: cardId,
        effect: {
          type: 'DROP_SHADOW',
          color: { r: 0, g: 0, b: 0, a: 0.05 },
          offset: { x: 0, y: 2 },
          radius: 8
        }
      });

      // Icon
      await this.sendCommand('create_text', {
        x: 20,
        y: 20,
        text: stat.icon,
        fontSize: 28,
        parentId: cardId
      });

      // Title
      await this.sendCommand('create_text', {
        x: 20,
        y: 60,
        text: stat.title,
        fontSize: 12,
        fontColor: { r: 0.5, g: 0.5, b: 0.5, a: 1 },
        parentId: cardId
      });

      // Value
      await this.sendCommand('create_text', {
        x: 20,
        y: 80,
        text: stat.value,
        fontSize: 24,
        fontWeight: 700,
        fontColor: { r: stat.color.r, g: stat.color.g, b: stat.color.b, a: 1 },
        parentId: cardId
      });
    }

    // Agents Grid
    const agentsContainer = await this.sendCommand('create_frame', {
      x: 32,
      y: 240,
      width: 900,
      height: 600,
      name: 'Agents_Grid',
      fillColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId: dashboardId
    });

    // Agents Title
    await this.sendCommand('create_text', {
      x: 24,
      y: 24,
      text: '🤖 Agent Status',
      fontSize: 18,
      fontWeight: 600,
      parentId: agentsContainer
    });

    // Agent Cards
    const agents = [
      { name: 'supervisor', status: 'active', task: 'Coordinating tasks' },
      { name: 'master', status: 'active', task: 'Strategic planning' },
      { name: 'backend-api', status: 'active', task: 'Processing requests' },
      { name: 'database', status: 'active', task: 'Managing data' },
      { name: 'frontend-ui', status: 'active', task: 'Rendering UI' },
      { name: 'testing', status: 'idle', task: 'Waiting for tests' },
      { name: 'queue-manager', status: 'active', task: 'Processing queue' },
      { name: 'instagram', status: 'idle', task: 'Ready' },
      { name: 'deployment', status: 'idle', task: 'Standing by' }
    ];

    for (let i = 0; i < agents.length; i++) {
      const agent = agents[i];
      const row = Math.floor(i / 3);
      const col = i % 3;
      const cardX = 24 + (col * 290);
      const cardY = 70 + (row * 160);

      const agentCardId = await this.sendCommand('create_frame', {
        x: cardX,
        y: cardY,
        width: 270,
        height: 140,
        name: `Agent_${agent.name}`,
        fillColor: { r: 0.98, g: 0.98, b: 0.99, a: 1 },
        parentId: agentsContainer
      });

      // Status indicator
      const statusColor = agent.status === 'active'
        ? { r: 0.2, g: 0.8, b: 0.4 }
        : { r: 0.6, g: 0.6, b: 0.6 };

      await this.sendCommand('create_ellipse', {
        x: 16,
        y: 16,
        width: 12,
        height: 12,
        fillColor: statusColor,
        parentId: agentCardId
      });

      // Agent name
      await this.sendCommand('create_text', {
        x: 36,
        y: 16,
        text: agent.name,
        fontSize: 14,
        fontWeight: 600,
        parentId: agentCardId
      });

      // Status
      await this.sendCommand('create_text', {
        x: 16,
        y: 45,
        text: `Status: ${agent.status}`,
        fontSize: 12,
        fontColor: { r: 0.5, g: 0.5, b: 0.5, a: 1 },
        parentId: agentCardId
      });

      // Task
      await this.sendCommand('create_text', {
        x: 16,
        y: 70,
        text: agent.task,
        fontSize: 12,
        fontColor: { r: 0.4, g: 0.4, b: 0.4, a: 1 },
        parentId: agentCardId
      });

      // Action button
      const buttonId = await this.sendCommand('create_frame', {
        x: 16,
        y: 100,
        width: 80,
        height: 28,
        name: 'Action_Button',
        fillColor: { r: 0.2, g: 0.5, b: 1, a: 1 },
        parentId: agentCardId
      });

      await this.sendCommand('set_corner_radius', {
        nodeId: buttonId,
        radius: 4
      });

      await this.sendCommand('create_text', {
        x: 20,
        y: 7,
        text: 'View',
        fontSize: 12,
        fontWeight: 500,
        fontColor: { r: 1, g: 1, b: 1, a: 1 },
        parentId: buttonId
      });
    }

    // Activity Feed
    const activityContainer = await this.sendCommand('create_frame', {
      x: 960,
      y: 240,
      width: 448,
      height: 600,
      name: 'Activity_Feed',
      fillColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId: dashboardId
    });

    // Activity Title
    await this.sendCommand('create_text', {
      x: 24,
      y: 24,
      text: '📋 Recent Activity',
      fontSize: 18,
      fontWeight: 600,
      parentId: activityContainer
    });

    // Activity Items
    const activities = [
      { agent: 'backend-api', action: 'API endpoint created', time: '2 min ago' },
      { agent: 'database', action: 'Schema migration complete', time: '5 min ago' },
      { agent: 'frontend-ui', action: 'Component updated', time: '8 min ago' },
      { agent: 'testing', action: 'Tests passed', time: '12 min ago' },
      { agent: 'supervisor', action: 'Task delegation complete', time: '15 min ago' }
    ];

    for (let i = 0; i < activities.length; i++) {
      const activity = activities[i];
      const itemY = 70 + (i * 80);

      const itemId = await this.sendCommand('create_frame', {
        x: 24,
        y: itemY,
        width: 400,
        height: 70,
        name: `Activity_Item_${i}`,
        fillColor: { r: 0.98, g: 0.98, b: 0.99, a: 1 },
        parentId: activityContainer
      });

      // Agent name
      await this.sendCommand('create_text', {
        x: 12,
        y: 12,
        text: activity.agent,
        fontSize: 12,
        fontWeight: 600,
        fontColor: { r: 0.2, g: 0.5, b: 1, a: 1 },
        parentId: itemId
      });

      // Action
      await this.sendCommand('create_text', {
        x: 12,
        y: 32,
        text: activity.action,
        fontSize: 12,
        parentId: itemId
      });

      // Time
      await this.sendCommand('create_text', {
        x: 12,
        y: 50,
        text: activity.time,
        fontSize: 10,
        fontColor: { r: 0.6, g: 0.6, b: 0.6, a: 1 },
        parentId: itemId
      });
    }

    console.log(`✅ MCP Dashboard created with ${this.createdIds.length} elements`);
    return dashboardId;
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Main execution
async function main() {
  const channel = process.argv[2] || '5utu5pn0';
  const replicator = new MCPDashboardReplicator(channel);

  try {
    await replicator.connect();
    console.log('🚀 Starting MCP Dashboard Replication...\n');

    await replicator.createMCPDashboard();

    console.log('\n✅ MCP Dashboard Replication Complete!');
    console.log('📌 Check Figma to see your replicated dashboard!\n');

    replicator.disconnect();
  } catch (error) {
    console.error('❌ Error:', error);
    replicator.disconnect();
  }
}

if (require.main === module) {
  main();
}

module.exports = MCPDashboardReplicator;