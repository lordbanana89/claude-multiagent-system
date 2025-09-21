#!/usr/bin/env node

/**
 * Replicate MultiTerminal to Figma
 * Creates visual representation of the terminal interface
 */

const WebSocket = require('ws');

class MultiTerminalReplicator {
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

  async createMultiTerminal() {
    console.log('\n💻 Creating MultiTerminal Interface...');

    // Main Terminal Container
    const terminalId = await this.sendCommand('create_frame', {
      x: 100,
      y: 1100,
      width: 1440,
      height: 800,
      name: 'MultiTerminal_Container',
      fillColor: { r: 0.08, g: 0.08, b: 0.12, a: 1 }
    });

    // Header with tabs
    const headerHeight = 48;
    const headerId = await this.sendCommand('create_frame', {
      x: 0,
      y: 0,
      width: 1440,
      height: headerHeight,
      name: 'Terminal_Header',
      fillColor: { r: 0.06, g: 0.06, b: 0.1, a: 1 },
      parentId: terminalId
    });

    // Terminal tabs
    const agents = [
      { name: 'supervisor', active: true },
      { name: 'master', active: false },
      { name: 'backend-api', active: false },
      { name: 'database', active: false },
      { name: 'frontend-ui', active: false },
      { name: 'testing', active: false },
      { name: 'queue-manager', active: false },
      { name: 'instagram', active: false },
      { name: 'deployment', active: false }
    ];

    let tabX = 16;
    for (const agent of agents) {
      const tabWidth = 120;

      const tabId = await this.sendCommand('create_frame', {
        x: tabX,
        y: 8,
        width: tabWidth,
        height: 32,
        name: `Tab_${agent.name}`,
        fillColor: agent.active
          ? { r: 0.12, g: 0.12, b: 0.18, a: 1 }
          : { r: 0.06, g: 0.06, b: 0.1, a: 1 },
        parentId: headerId
      });

      if (!agent.active) {
        // Add border for inactive tabs
        await this.sendCommand('set_stroke_color', {
          nodeId: tabId,
          color: { r: 0.2, g: 0.2, b: 0.3, a: 1 },
          strokeWeight: 1
        });
      }

      // Tab text
      await this.sendCommand('create_text', {
        x: 12,
        y: 9,
        text: agent.name,
        fontSize: 12,
        fontWeight: agent.active ? 600 : 400,
        fontColor: agent.active
          ? { r: 1, g: 1, b: 1, a: 1 }
          : { r: 0.6, g: 0.6, b: 0.7, a: 1 },
        parentId: tabId
      });

      // Close button
      await this.sendCommand('create_text', {
        x: tabWidth - 24,
        y: 9,
        text: '×',
        fontSize: 16,
        fontColor: { r: 0.5, g: 0.5, b: 0.6, a: 1 },
        parentId: tabId
      });

      tabX += tabWidth + 4;
    }

    // Terminal controls (right side of header)
    const controls = ['─', '□', '×'];
    let controlX = 1340;

    for (const control of controls) {
      await this.sendCommand('create_frame', {
        x: controlX,
        y: 12,
        width: 24,
        height: 24,
        name: `Control_${control}`,
        fillColor: { r: 0.2, g: 0.2, b: 0.3, a: 1 },
        parentId: headerId
      });

      await this.sendCommand('create_text', {
        x: controlX + 6,
        y: 16,
        text: control,
        fontSize: 12,
        fontColor: { r: 0.8, g: 0.8, b: 0.9, a: 1 },
        parentId: headerId
      });

      controlX += 28;
    }

    // Terminal content area
    const contentId = await this.sendCommand('create_frame', {
      x: 0,
      y: headerHeight,
      width: 1440,
      height: 752,
      name: 'Terminal_Content',
      fillColor: { r: 0.04, g: 0.04, b: 0.08, a: 1 },
      parentId: terminalId
    });

    // Terminal output lines
    const terminalLines = [
      { text: '🎖️ SUPERVISOR Agent Terminal', color: { r: 0.4, g: 0.8, b: 1 }, isBold: true },
      { text: '================================', color: { r: 0.3, g: 0.3, b: 0.5 } },
      { text: '', color: { r: 1, g: 1, b: 1 } },
      { text: '> Initializing supervisor agent...', color: { r: 0.8, g: 0.8, b: 0.9 } },
      { text: '✓ Connected to MCP server', color: { r: 0.4, g: 0.9, b: 0.4 } },
      { text: '✓ Loading task orchestration module', color: { r: 0.4, g: 0.9, b: 0.4 } },
      { text: '✓ Agent network synchronized', color: { r: 0.4, g: 0.9, b: 0.4 } },
      { text: '', color: { r: 1, g: 1, b: 1 } },
      { text: '📋 Current Tasks:', color: { r: 1, g: 0.8, b: 0.3 }, isBold: true },
      { text: '  1. [IN PROGRESS] Coordinate frontend replication', color: { r: 0.8, g: 0.8, b: 0.9 } },
      { text: '  2. [PENDING] Synchronize component state', color: { r: 0.6, g: 0.6, b: 0.7 } },
      { text: '  3. [PENDING] Deploy to production', color: { r: 0.6, g: 0.6, b: 0.7 } },
      { text: '', color: { r: 1, g: 1, b: 1 } },
      { text: '🤖 Agent Status:', color: { r: 0.6, g: 0.8, b: 1 }, isBold: true },
      { text: '  backend-api: ● active - Processing API requests', color: { r: 0.7, g: 0.7, b: 0.8 } },
      { text: '  database: ● active - Managing data persistence', color: { r: 0.7, g: 0.7, b: 0.8 } },
      { text: '  frontend-ui: ● active - Rendering components', color: { r: 0.7, g: 0.7, b: 0.8 } },
      { text: '  testing: ○ idle - Awaiting test commands', color: { r: 0.5, g: 0.5, b: 0.6 } },
      { text: '  deployment: ○ idle - Standing by', color: { r: 0.5, g: 0.5, b: 0.6 } },
      { text: '', color: { r: 1, g: 1, b: 1 } },
      { text: '> Task delegation complete', color: { r: 0.8, g: 0.8, b: 0.9 } },
      { text: '> Monitoring agent performance...', color: { r: 0.8, g: 0.8, b: 0.9 } },
      { text: '', color: { r: 1, g: 1, b: 1 } },
      { text: 'supervisor@mcp-system:~$ █', color: { r: 0.4, g: 1, b: 0.4 }, isBold: true }
    ];

    let lineY = 20;
    const lineHeight = 20;
    const monoFont = 'SF Mono';

    for (const line of terminalLines) {
      if (line.text) {
        await this.sendCommand('create_text', {
          x: 20,
          y: lineY,
          text: line.text,
          fontSize: 13,
          fontFamily: monoFont,
          fontWeight: line.isBold ? 600 : 400,
          fontColor: line.color,
          parentId: contentId
        });
      }
      lineY += lineHeight;
    }

    // Add scrollbar
    const scrollbarId = await this.sendCommand('create_frame', {
      x: 1420,
      y: 0,
      width: 12,
      height: 752,
      name: 'Scrollbar_Track',
      fillColor: { r: 0.1, g: 0.1, b: 0.15, a: 1 },
      parentId: contentId
    });

    // Scrollbar thumb
    await this.sendCommand('create_frame', {
      x: 2,
      y: 20,
      width: 8,
      height: 100,
      name: 'Scrollbar_Thumb',
      fillColor: { r: 0.3, g: 0.3, b: 0.4, a: 1 },
      parentId: scrollbarId
    });

    // Status bar at bottom
    const statusBarId = await this.sendCommand('create_frame', {
      x: 0,
      y: 752,
      width: 1440,
      height: 24,
      name: 'Status_Bar',
      fillColor: { r: 0.08, g: 0.08, b: 0.12, a: 1 },
      parentId: contentId
    });

    // Status info
    await this.sendCommand('create_text', {
      x: 12,
      y: 5,
      text: 'TMUX Session: supervisor | UTF-8 | Line 24, Col 31',
      fontSize: 11,
      fontColor: { r: 0.5, g: 0.5, b: 0.6, a: 1 },
      parentId: statusBarId
    });

    // Connection status
    await this.sendCommand('create_text', {
      x: 1320,
      y: 5,
      text: '● Connected',
      fontSize: 11,
      fontColor: { r: 0.4, g: 0.9, b: 0.4, a: 1 },
      parentId: statusBarId
    });

    console.log(`✅ MultiTerminal created with ${this.createdIds.length} elements`);
    return terminalId;
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
  const replicator = new MultiTerminalReplicator(channel);

  try {
    await replicator.connect();
    console.log('🚀 Starting MultiTerminal Replication...\n');

    await replicator.createMultiTerminal();

    console.log('\n✅ MultiTerminal Replication Complete!');
    console.log('📌 Check Figma to see your terminal interface!\n');

    replicator.disconnect();
  } catch (error) {
    console.error('❌ Error:', error);
    replicator.disconnect();
  }
}

if (require.main === module) {
  main();
}

module.exports = MultiTerminalReplicator;