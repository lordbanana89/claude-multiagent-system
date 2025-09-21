#!/usr/bin/env node

/**
 * FIGMA VISUAL LAYOUT SYSTEM
 * Crea un layout visivo organizzato e professionale
 */

const WebSocket = require('ws');

class FigmaVisualLayout {
  constructor(channel = '5utu5pn0') {
    this.channel = channel;
    this.ws = null;
    this.layout = {
      margin: 40,
      spacing: 20,
      gridColumns: 3,
      cardWidth: 280,
      cardHeight: 140,
      buttonWidth: 120,
      buttonHeight: 44
    };
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket('ws://localhost:3055');

      this.ws.onopen = () => {
        console.log('✅ Connesso a Figma');
        this.ws.send(JSON.stringify({
          type: 'join',
          channel: this.channel
        }));
        setTimeout(resolve, 500);
      };

      this.ws.onerror = reject;
    });
  }

  async clearCanvas() {
    console.log('🧹 Pulizia canvas...');
    // Prima ottieni tutti i nodi esistenti
    const nodes = await this.sendCommand('get_document_info');

    if (nodes && nodes.children) {
      for (const node of nodes.children) {
        if (node.id && node.id !== '0:1') { // Non cancellare la pagina
          await this.sendCommand('delete_node', { nodeId: node.id });
        }
      }
    }
  }

  async createProfessionalLayout() {
    console.log('🎨 Creazione layout professionale...\n');

    // 1. MAIN CONTAINER
    const containerId = await this.createFrame({
      x: 100,
      y: 100,
      width: 1440,
      height: 900,
      name: 'Multi_Agent_Dashboard',
      fillColor: { r: 0.98, g: 0.98, b: 1, a: 1 },
      cornerRadius: 0
    });

    // 2. HEADER
    const headerId = await this.createFrame({
      x: 0,
      y: 0,
      width: 1440,
      height: 80,
      name: 'Header',
      fillColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId: containerId
    });

    // Logo/Title
    await this.createText({
      x: 40,
      y: 26,
      text: '🚀 Claude Multi-Agent System',
      fontSize: 24,
      fontWeight: 700,
      parentId: headerId
    });

    // Navigation buttons
    const navButtons = ['Dashboard', 'Agents', 'Messages', 'Settings'];
    for (let i = 0; i < navButtons.length; i++) {
      await this.createFrame({
        x: 1000 + i * 110,
        y: 20,
        width: 100,
        height: 40,
        name: `Nav_${navButtons[i]}`,
        fillColor: i === 0 ? { r: 0.2, g: 0.5, b: 1, a: 1 } : { r: 0, g: 0, b: 0, a: 0 },
        cornerRadius: 6,
        parentId: headerId
      });

      await this.createText({
        x: 1000 + i * 110 + 20,
        y: 30,
        text: navButtons[i],
        fontSize: 14,
        fontWeight: 500,
        fontColor: i === 0 ? { r: 1, g: 1, b: 1, a: 1 } : { r: 0.4, g: 0.4, b: 0.4, a: 1 },
        parentId: headerId
      });
    }

    // 3. STATS ROW
    const stats = [
      { label: 'Active Agents', value: '9', color: { r: 0.2, g: 0.8, b: 0.4, a: 1 } },
      { label: 'Total Messages', value: '1,234', color: { r: 0.2, g: 0.5, b: 1, a: 1 } },
      { label: 'Tasks Completed', value: '56', color: { r: 0.9, g: 0.6, b: 0.2, a: 1 } },
      { label: 'System Health', value: '100%', color: { r: 0.2, g: 0.8, b: 0.4, a: 1 } }
    ];

    for (let i = 0; i < stats.length; i++) {
      const statCard = await this.createFrame({
        x: 40 + i * 350,
        y: 100,
        width: 330,
        height: 100,
        name: `Stat_${stats[i].label}`,
        fillColor: { r: 1, g: 1, b: 1, a: 1 },
        cornerRadius: 12,
        parentId: containerId
      });

      // Add shadow
      await this.sendCommand('set_effect', {
        nodeId: statCard,
        effect: {
          type: 'DROP_SHADOW',
          color: { r: 0, g: 0, b: 0, a: 0.08 },
          offset: { x: 0, y: 2 },
          radius: 8
        }
      });

      // Icon circle
      await this.createEllipse({
        x: 20,
        y: 25,
        width: 50,
        height: 50,
        fillColor: stats[i].color,
        opacity: 0.1,
        parentId: statCard
      });

      // Value
      await this.createText({
        x: 90,
        y: 25,
        text: stats[i].value,
        fontSize: 28,
        fontWeight: 700,
        parentId: statCard
      });

      // Label
      await this.createText({
        x: 90,
        y: 58,
        text: stats[i].label,
        fontSize: 14,
        fontColor: { r: 0.5, g: 0.5, b: 0.5, a: 1 },
        parentId: statCard
      });
    }

    // 4. AGENT GRID
    const agentsSection = await this.createFrame({
      x: 40,
      y: 220,
      width: 1360,
      height: 400,
      name: 'Agents_Section',
      fillColor: { r: 0, g: 0, b: 0, a: 0 },
      parentId: containerId
    });

    // Section title
    await this.createText({
      x: 0,
      y: 0,
      text: 'Active Agents',
      fontSize: 20,
      fontWeight: 600,
      parentId: agentsSection
    });

    const agents = [
      { name: 'Supervisor', status: 'active', role: 'Orchestration' },
      { name: 'Master', status: 'active', role: 'Command' },
      { name: 'Backend API', status: 'active', role: 'Services' },
      { name: 'Database', status: 'active', role: 'Storage' },
      { name: 'Frontend UI', status: 'active', role: 'Interface' },
      { name: 'Testing', status: 'idle', role: 'Quality' },
      { name: 'Queue Manager', status: 'active', role: 'Tasks' },
      { name: 'Instagram', status: 'idle', role: 'Integration' },
      { name: 'Deployment', status: 'idle', role: 'Release' }
    ];

    for (let i = 0; i < agents.length; i++) {
      const row = Math.floor(i / 3);
      const col = i % 3;

      const agentCard = await this.createFrame({
        x: col * 460,
        y: 40 + row * 120,
        width: 440,
        height: 100,
        name: `Agent_${agents[i].name}`,
        fillColor: { r: 1, g: 1, b: 1, a: 1 },
        cornerRadius: 8,
        parentId: agentsSection
      });

      // Add shadow
      await this.sendCommand('set_effect', {
        nodeId: agentCard,
        effect: {
          type: 'DROP_SHADOW',
          color: { r: 0, g: 0, b: 0, a: 0.06 },
          offset: { x: 0, y: 1 },
          radius: 4
        }
      });

      // Status indicator
      const statusColor = agents[i].status === 'active'
        ? { r: 0.2, g: 0.8, b: 0.4, a: 1 }
        : { r: 0.6, g: 0.6, b: 0.6, a: 1 };

      await this.createEllipse({
        x: 20,
        y: 44,
        width: 12,
        height: 12,
        fillColor: statusColor,
        parentId: agentCard
      });

      // Agent name
      await this.createText({
        x: 20,
        y: 20,
        text: agents[i].name,
        fontSize: 16,
        fontWeight: 600,
        parentId: agentCard
      });

      // Role
      await this.createText({
        x: 40,
        y: 44,
        text: agents[i].role,
        fontSize: 13,
        fontColor: { r: 0.5, g: 0.5, b: 0.5, a: 1 },
        parentId: agentCard
      });

      // Status text
      await this.createText({
        x: 20,
        y: 68,
        text: `Status: ${agents[i].status}`,
        fontSize: 12,
        fontColor: { r: 0.6, g: 0.6, b: 0.6, a: 1 },
        parentId: agentCard
      });

      // Action button
      await this.createFrame({
        x: 340,
        y: 30,
        width: 80,
        height: 40,
        name: 'View_Button',
        fillColor: { r: 0.95, g: 0.95, b: 0.96, a: 1 },
        cornerRadius: 6,
        parentId: agentCard
      });

      await this.createText({
        x: 360,
        y: 40,
        text: 'View',
        fontSize: 14,
        fontWeight: 500,
        parentId: agentCard
      });
    }

    // 5. TERMINAL SECTION
    const terminalSection = await this.createFrame({
      x: 40,
      y: 640,
      width: 1360,
      height: 220,
      name: 'Terminal_Section',
      fillColor: { r: 0.08, g: 0.08, b: 0.12, a: 1 },
      cornerRadius: 8,
      parentId: containerId
    });

    // Terminal header
    await this.createFrame({
      x: 0,
      y: 0,
      width: 1360,
      height: 40,
      name: 'Terminal_Header',
      fillColor: { r: 0.06, g: 0.06, b: 0.1, a: 1 },
      cornerRadius: 8,
      parentId: terminalSection
    });

    // Terminal title
    await this.createText({
      x: 16,
      y: 12,
      text: 'supervisor@claude-system:~$',
      fontSize: 14,
      fontFamily: 'SF Mono',
      fontColor: { r: 0.4, g: 1, b: 0.4, a: 1 },
      parentId: terminalSection
    });

    // Terminal content
    const terminalLines = [
      '[2024-09-20 23:15:42] System initialized successfully',
      '[2024-09-20 23:15:43] All agents connected',
      '[2024-09-20 23:15:44] MCP server running on port 9999',
      '[2024-09-20 23:15:45] WebSocket server active on port 3055',
      '[2024-09-20 23:15:46] Ready for operations'
    ];

    for (let i = 0; i < terminalLines.length; i++) {
      await this.createText({
        x: 16,
        y: 50 + i * 20,
        text: terminalLines[i],
        fontSize: 13,
        fontFamily: 'SF Mono',
        fontColor: { r: 0.8, g: 0.8, b: 0.8, a: 1 },
        parentId: terminalSection
      });
    }

    console.log('✅ Layout professionale completato!');
  }

  // Helper methods
  async createFrame(config) {
    return await this.sendCommand('create_frame', {
      x: config.x,
      y: config.y,
      width: config.width,
      height: config.height,
      name: config.name,
      fillColor: config.fillColor,
      parentId: config.parentId
    });
  }

  async createText(config) {
    return await this.sendCommand('create_text', {
      x: config.x,
      y: config.y,
      text: config.text,
      fontSize: config.fontSize || 14,
      fontWeight: config.fontWeight || 400,
      fontColor: config.fontColor || { r: 0, g: 0, b: 0, a: 1 },
      fontFamily: config.fontFamily || 'Inter',
      parentId: config.parentId
    });
  }

  async createEllipse(config) {
    return await this.sendCommand('create_ellipse', {
      x: config.x,
      y: config.y,
      width: config.width,
      height: config.height,
      fillColor: config.fillColor,
      opacity: config.opacity || 1,
      parentId: config.parentId
    });
  }

  async sendCommand(command, params = {}) {
    return new Promise((resolve) => {
      const id = `cmd-${Date.now()}`;

      const handler = (event) => {
        const data = JSON.parse(event.data);
        if (data.message && data.message.id === id) {
          resolve(data.message.result?.id || data.message.result);
          this.ws.removeEventListener('message', handler);
        }
      };

      this.ws.addEventListener('message', handler);

      this.ws.send(JSON.stringify({
        id,
        type: 'message',
        channel: this.channel,
        message: {
          id,
          command,
          params: { ...params, commandId: id }
        }
      }));

      setTimeout(() => {
        this.ws.removeEventListener('message', handler);
        resolve(null);
      }, 1000);
    });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Main
async function main() {
  const layout = new FigmaVisualLayout();

  try {
    await layout.connect();
    // await layout.clearCanvas(); // Opzionale: pulisce prima
    await layout.createProfessionalLayout();
  } catch (error) {
    console.error('❌ Errore:', error);
  } finally {
    setTimeout(() => {
      layout.disconnect();
      process.exit(0);
    }, 2000);
  }
}

if (require.main === module) {
  main();
}

module.exports = FigmaVisualLayout;