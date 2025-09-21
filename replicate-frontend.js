#!/usr/bin/env node

/**
 * REPLICATE FRONTEND TO FIGMA
 * Replica tutto il frontend attuale in Figma
 */

const WebSocket = require('ws');
const fs = require('fs').promises;
const path = require('path');

const CHANNEL = process.argv[2] || '5utu5pn0';
const PROJECT_PATH = '/Users/erik/Desktop/claude-multiagent-system/claude-ui';

class FrontendReplicator {
  constructor() {
    this.ws = null;
    this.componentMap = new Map();
    this.yOffset = 100;
    this.xOffset = 100;
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket('ws://localhost:3055');

      this.ws.on('open', () => {
        console.log('✅ Connected to Figma');
        this.ws.send(JSON.stringify({ type: 'join', channel: CHANNEL }));
        setTimeout(resolve, 500);
      });

      this.ws.on('error', reject);
    });
  }

  async replicateAll() {
    console.log('🚀 Starting Frontend Replication to Figma...\n');

    // 1. Create main container
    await this.createMainContainer();

    // 2. Replicate MCPDashboard
    await this.replicateMCPDashboard();

    // 3. Replicate MultiTerminal
    await this.replicateMultiTerminal();

    // 4. Replicate other components
    await this.replicateComponents();

    console.log('\n✅ Frontend Replication Complete!');
    console.log(`📊 Created ${this.componentMap.size} components in Figma`);
  }

  async createMainContainer() {
    console.log('📦 Creating main container...');

    await this.sendCommand('create_frame', {
      x: 0,
      y: 0,
      width: 1920,
      height: 3000,
      name: 'Claude_Multi_Agent_Frontend',
      fillColor: { r: 0.98, g: 0.98, b: 0.99, a: 1 }
    });

    // Title
    await this.sendCommand('create_text', {
      x: 100,
      y: 40,
      text: '🚀 Claude Multi-Agent System - Frontend Components',
      fontSize: 32,
      fontWeight: 700,
      fontColor: { r: 0.1, g: 0.1, b: 0.15, a: 1 }
    });
  }

  async replicateMCPDashboard() {
    console.log('📊 Replicating MCP Dashboard...');

    // Main dashboard container
    const dashboardId = await this.sendCommand('create_frame', {
      x: this.xOffset,
      y: this.yOffset,
      width: 1400,
      height: 800,
      name: 'MCPDashboard',
      fillColor: { r: 0.05, g: 0.05, b: 0.08, a: 1 }
    });

    // Header
    await this.createDashboardHeader(dashboardId);

    // Stats Cards
    await this.createStatsCards(dashboardId);

    // Agent Grid
    await this.createAgentGrid(dashboardId);

    // Activity Feed
    await this.createActivityFeed(dashboardId);

    this.yOffset += 850;
  }

  async createDashboardHeader(parentId) {
    const headerId = await this.sendCommand('create_frame', {
      x: 0,
      y: 0,
      width: 1400,
      height: 80,
      name: 'Dashboard_Header',
      fillColor: { r: 0.08, g: 0.08, b: 0.1, a: 1 },
      parentId
    });

    // Logo & Title
    await this.sendCommand('create_text', {
      x: 30,
      y: 25,
      text: '🤖 Claude Multi-Agent System',
      fontSize: 24,
      fontWeight: 700,
      fontColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId: headerId
    });

    // Status indicator
    await this.sendCommand('create_ellipse', {
      x: 1300,
      y: 30,
      width: 20,
      height: 20,
      name: 'Status_Indicator',
      fillColor: { r: 0.2, g: 0.9, b: 0.3, a: 1 },
      parentId: headerId
    });

    await this.sendCommand('create_text', {
      x: 1330,
      y: 28,
      text: 'Active',
      fontSize: 14,
      fontColor: { r: 0.2, g: 0.9, b: 0.3, a: 1 },
      parentId: headerId
    });
  }

  async createStatsCards(parentId) {
    const stats = [
      { label: 'Active Agents', value: '9', color: { r: 0.2, g: 0.6, b: 1 } },
      { label: 'Messages', value: '1,247', color: { r: 0.9, g: 0.6, b: 0.2 } },
      { label: 'Tasks Completed', value: '89', color: { r: 0.2, g: 0.9, b: 0.5 } },
      { label: 'Success Rate', value: '98.5%', color: { r: 0.9, g: 0.2, b: 0.6 } }
    ];

    let xPos = 30;

    for (const stat of stats) {
      const cardId = await this.sendCommand('create_frame', {
        x: xPos,
        y: 100,
        width: 320,
        height: 120,
        name: `Stat_${stat.label}`,
        fillColor: { r: 0.1, g: 0.1, b: 0.12, a: 1 },
        parentId
      });

      // Add corner radius
      await this.sendCommand('set_corner_radius', {
        nodeId: cardId,
        radius: 12
      });

      // Label
      await this.sendCommand('create_text', {
        x: 20,
        y: 20,
        text: stat.label,
        fontSize: 14,
        fontColor: { r: 0.6, g: 0.6, b: 0.65, a: 1 },
        parentId: cardId
      });

      // Value
      await this.sendCommand('create_text', {
        x: 20,
        y: 45,
        text: stat.value,
        fontSize: 36,
        fontWeight: 700,
        fontColor: stat.color,
        parentId: cardId
      });

      xPos += 340;
    }
  }

  async createAgentGrid(parentId) {
    const agents = [
      { name: 'Supervisor', emoji: '👨‍💼', status: 'active' },
      { name: 'Master', emoji: '🎖️', status: 'active' },
      { name: 'Backend API', emoji: '🔧', status: 'active' },
      { name: 'Database', emoji: '💾', status: 'idle' },
      { name: 'Frontend UI', emoji: '🎨', status: 'active' },
      { name: 'Testing', emoji: '🧪', status: 'busy' }
    ];

    let xPos = 30;
    let yPos = 240;

    for (let i = 0; i < agents.length; i++) {
      const agent = agents[i];

      if (i > 0 && i % 3 === 0) {
        xPos = 30;
        yPos += 160;
      }

      const agentId = await this.sendCommand('create_frame', {
        x: xPos,
        y: yPos,
        width: 440,
        height: 140,
        name: `Agent_${agent.name}`,
        fillColor: { r: 0.12, g: 0.12, b: 0.15, a: 1 },
        parentId
      });

      await this.sendCommand('set_corner_radius', {
        nodeId: agentId,
        radius: 8
      });

      // Emoji
      await this.sendCommand('create_text', {
        x: 20,
        y: 30,
        text: agent.emoji,
        fontSize: 48,
        parentId: agentId
      });

      // Name
      await this.sendCommand('create_text', {
        x: 100,
        y: 40,
        text: agent.name,
        fontSize: 20,
        fontWeight: 600,
        fontColor: { r: 1, g: 1, b: 1, a: 1 },
        parentId: agentId
      });

      // Status
      const statusColor = agent.status === 'active'
        ? { r: 0.2, g: 0.9, b: 0.3 }
        : agent.status === 'busy'
        ? { r: 0.9, g: 0.6, b: 0.2 }
        : { r: 0.5, g: 0.5, b: 0.5 };

      await this.sendCommand('create_ellipse', {
        x: 100,
        y: 75,
        width: 12,
        height: 12,
        fillColor: statusColor,
        parentId: agentId
      });

      await this.sendCommand('create_text', {
        x: 120,
        y: 70,
        text: agent.status,
        fontSize: 14,
        fontColor: statusColor,
        parentId: agentId
      });

      xPos += 460;
    }
  }

  async createActivityFeed(parentId) {
    const feedId = await this.sendCommand('create_frame', {
      x: 30,
      y: 560,
      width: 1340,
      height: 200,
      name: 'Activity_Feed',
      fillColor: { r: 0.08, g: 0.08, b: 0.1, a: 1 },
      parentId
    });

    await this.sendCommand('set_corner_radius', {
      nodeId: feedId,
      radius: 8
    });

    // Title
    await this.sendCommand('create_text', {
      x: 20,
      y: 20,
      text: '📋 Recent Activity',
      fontSize: 16,
      fontWeight: 600,
      fontColor: { r: 0.9, g: 0.9, b: 0.95, a: 1 },
      parentId: feedId
    });

    // Activity items
    const activities = [
      '[10:23] Supervisor: Task assigned to Backend API',
      '[10:24] Backend API: Processing request...',
      '[10:24] Database: Query executed successfully',
      '[10:25] Frontend UI: Dashboard updated'
    ];

    let yPos = 50;
    for (const activity of activities) {
      await this.sendCommand('create_text', {
        x: 20,
        y: yPos,
        text: activity,
        fontSize: 13,
        fontColor: { r: 0.7, g: 0.7, b: 0.75, a: 1 },
        parentId: feedId
      });
      yPos += 25;
    }
  }

  async replicateMultiTerminal() {
    console.log('💻 Replicating Multi-Terminal...');

    const terminalId = await this.sendCommand('create_frame', {
      x: this.xOffset,
      y: this.yOffset,
      width: 1400,
      height: 600,
      name: 'MultiTerminal',
      fillColor: { r: 0.05, g: 0.05, b: 0.08, a: 1 }
    });

    // Terminal tabs
    const tabs = ['Supervisor', 'Master', 'Backend', 'Database'];
    let xPos = 0;

    for (const tab of tabs) {
      const tabId = await this.sendCommand('create_frame', {
        x: xPos,
        y: 0,
        width: 150,
        height: 40,
        name: `Tab_${tab}`,
        fillColor: xPos === 0
          ? { r: 0.15, g: 0.4, b: 0.8, a: 1 }
          : { r: 0.08, g: 0.08, b: 0.1, a: 1 },
        parentId: terminalId
      });

      await this.sendCommand('create_text', {
        x: 20,
        y: 12,
        text: tab,
        fontSize: 14,
        fontWeight: 500,
        fontColor: { r: 1, g: 1, b: 1, a: 1 },
        parentId: tabId
      });

      xPos += 150;
    }

    // Terminal content
    const contentId = await this.sendCommand('create_frame', {
      x: 0,
      y: 40,
      width: 1400,
      height: 560,
      name: 'Terminal_Content',
      fillColor: { r: 0.02, g: 0.02, b: 0.03, a: 1 },
      parentId: terminalId
    });

    // Terminal text
    const terminalText = [
      '$ supervisor status',
      '✅ All agents operational',
      '📊 System metrics:',
      '   CPU: 42%',
      '   Memory: 1.2GB / 4GB',
      '   Tasks in queue: 3',
      '',
      '$ backend-api health',
      '🟢 API server running on port 5001',
      '   Endpoints: 24 active',
      '   Response time: 45ms avg'
    ];

    let yPos = 20;
    for (const line of terminalText) {
      await this.sendCommand('create_text', {
        x: 20,
        y: yPos,
        text: line,
        fontSize: 14,
        fontColor: { r: 0.2, g: 0.9, b: 0.5, a: 1 },
        fontName: 'Monaco',
        parentId: contentId
      });
      yPos += 22;
    }

    this.yOffset += 650;
  }

  async replicateComponents() {
    console.log('🎨 Replicating UI Components...');

    // Button variations
    await this.createButtonShowcase();

    // Input fields
    await this.createInputShowcase();

    // Cards
    await this.createCardShowcase();
  }

  async createButtonShowcase() {
    const containerId = await this.sendCommand('create_frame', {
      x: this.xOffset,
      y: this.yOffset,
      width: 600,
      height: 200,
      name: 'Button_Components',
      fillColor: { r: 1, g: 1, b: 1, a: 1 }
    });

    // Title
    await this.sendCommand('create_text', {
      x: 20,
      y: 20,
      text: 'Button Components',
      fontSize: 18,
      fontWeight: 600,
      parentId: containerId
    });

    // Button variants
    const variants = [
      { text: 'Primary', bg: { r: 0.2, g: 0.5, b: 1 }, text_color: { r: 1, g: 1, b: 1 } },
      { text: 'Secondary', bg: { r: 0.9, g: 0.9, b: 0.9 }, text_color: { r: 0.2, g: 0.2, b: 0.2 } },
      { text: 'Danger', bg: { r: 0.9, g: 0.2, b: 0.2 }, text_color: { r: 1, g: 1, b: 1 } }
    ];

    let xPos = 20;
    for (const variant of variants) {
      const btnId = await this.sendCommand('create_frame', {
        x: xPos,
        y: 60,
        width: 120,
        height: 40,
        name: `Button_${variant.text}`,
        fillColor: variant.bg,
        parentId: containerId
      });

      await this.sendCommand('set_corner_radius', {
        nodeId: btnId,
        radius: 6
      });

      await this.sendCommand('create_text', {
        x: 30,
        y: 12,
        text: variant.text,
        fontSize: 14,
        fontWeight: 600,
        fontColor: variant.text_color,
        parentId: btnId
      });

      xPos += 140;
    }

    this.xOffset += 650;
  }

  async createInputShowcase() {
    const containerId = await this.sendCommand('create_frame', {
      x: this.xOffset,
      y: this.yOffset,
      width: 600,
      height: 200,
      name: 'Input_Components',
      fillColor: { r: 1, g: 1, b: 1, a: 1 }
    });

    // Title
    await this.sendCommand('create_text', {
      x: 20,
      y: 20,
      text: 'Input Components',
      fontSize: 18,
      fontWeight: 600,
      parentId: containerId
    });

    // Input field
    const inputId = await this.sendCommand('create_frame', {
      x: 20,
      y: 60,
      width: 300,
      height: 40,
      name: 'Input_Field',
      fillColor: { r: 0.98, g: 0.98, b: 0.98, a: 1 },
      parentId: containerId
    });

    await this.sendCommand('set_stroke_color', {
      nodeId: inputId,
      color: { r: 0.8, g: 0.8, b: 0.8, a: 1 }
    });

    await this.sendCommand('set_corner_radius', {
      nodeId: inputId,
      radius: 4
    });

    await this.sendCommand('create_text', {
      x: 12,
      y: 12,
      text: 'Enter text...',
      fontSize: 14,
      fontColor: { r: 0.6, g: 0.6, b: 0.6, a: 1 },
      parentId: inputId
    });
  }

  async createCardShowcase() {
    // Similar structure for cards...
  }

  async sendCommand(command, params = {}) {
    return new Promise((resolve) => {
      const id = `cmd-${Date.now()}-${Math.random()}`;
      const message = {
        id,
        type: 'message',
        channel: CHANNEL,
        message: {
          id,
          command,
          params: { ...params, commandId: id }
        }
      };

      this.ws.send(JSON.stringify(message));
      setTimeout(() => resolve(id), 100);
    });
  }

  async run() {
    try {
      await this.connect();
      await this.replicateAll();

      console.log('\n📌 Check Figma to see your replicated frontend!');

      this.ws.close();
      process.exit(0);
    } catch (error) {
      console.error('Error:', error);
      process.exit(1);
    }
  }
}

// Execute
const replicator = new FrontendReplicator();
replicator.run();