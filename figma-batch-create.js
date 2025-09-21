#!/usr/bin/env node

/**
 * Figma Batch Creation Script
 * Esegui operazioni lunghe in modo automatizzato
 */

const WebSocket = require('ws');

class FigmaBatchCreator {
  constructor(channel) {
    this.channel = channel || '5utu5pn0'; // Sostituisci col canale attuale
    this.ws = null;
    this.commandQueue = [];
    this.currentCommand = 0;
  }

  connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket('ws://localhost:3055');

      this.ws.on('open', () => {
        console.log('✓ Connesso al WebSocket');
        // Join channel
        this.ws.send(JSON.stringify({
          type: 'join',
          channel: this.channel
        }));
        setTimeout(resolve, 1000);
      });

      this.ws.on('message', (data) => {
        const msg = JSON.parse(data.toString());
        console.log('Response:', msg.type);
      });

      this.ws.on('error', reject);
    });
  }

  sendCommand(command, params) {
    return new Promise((resolve) => {
      const id = `cmd-${Date.now()}`;
      const message = {
        id: id,
        type: 'message',
        channel: this.channel,
        message: {
          id: id,
          command: command,
          params: {...params, commandId: id}
        }
      };

      console.log(`Sending: ${command}`);
      this.ws.send(JSON.stringify(message));

      // Non aspettiamo risposta per velocità
      setTimeout(resolve, 200);
    });
  }

  async createMultiAgentUI() {
    console.log('🚀 Creating Multi-Agent System UI...\n');

    const agents = [
      { name: 'Supervisor', emoji: '👨‍💼', color: {r: 0.2, g: 0.4, b: 0.8} },
      { name: 'Master', emoji: '🎖️', color: {r: 0.8, g: 0.2, b: 0.2} },
      { name: 'Backend API', emoji: '🔧', color: {r: 0.2, g: 0.6, b: 0.4} },
      { name: 'Database', emoji: '💾', color: {r: 0.6, g: 0.4, b: 0.8} },
      { name: 'Frontend UI', emoji: '🎨', color: {r: 0.9, g: 0.6, b: 0.2} },
      { name: 'Testing', emoji: '🧪', color: {r: 0.4, g: 0.8, b: 0.6} },
      { name: 'Queue Manager', emoji: '📦', color: {r: 0.7, g: 0.7, b: 0.3} },
      { name: 'Instagram', emoji: '📸', color: {r: 0.9, g: 0.2, b: 0.6} },
      { name: 'Deployment', emoji: '🚀', color: {r: 0.3, g: 0.3, b: 0.9} }
    ];

    // Create main container
    await this.sendCommand('create_frame', {
      x: 100,
      y: 500,
      width: 1200,
      height: 800,
      name: 'Multi-Agent System Dashboard',
      fillColor: {r: 0.05, g: 0.05, b: 0.08, a: 1}
    });

    // Create agent cards
    for (let i = 0; i < agents.length; i++) {
      const agent = agents[i];
      const x = 120 + (i % 3) * 380;
      const y = 550 + Math.floor(i / 3) * 240;

      console.log(`Creating card for ${agent.name}...`);

      // Agent card frame
      await this.sendCommand('create_frame', {
        x: x,
        y: y,
        width: 340,
        height: 200,
        name: `Agent Card - ${agent.name}`,
        fillColor: {r: 0.1, g: 0.1, b: 0.12, a: 1}
      });

      // Agent emoji
      await this.sendCommand('create_text', {
        x: x + 20,
        y: y + 20,
        text: agent.emoji,
        fontSize: 48,
        name: `${agent.name} Icon`
      });

      // Agent name
      await this.sendCommand('create_text', {
        x: x + 100,
        y: y + 30,
        text: agent.name,
        fontSize: 24,
        fontWeight: 700,
        fontColor: {r: 1, g: 1, b: 1, a: 1},
        name: `${agent.name} Title`
      });

      // Status indicator
      await this.sendCommand('create_ellipse', {
        x: x + 100,
        y: y + 65,
        width: 12,
        height: 12,
        name: `${agent.name} Status`,
        fillColor: {r: 0.2, g: 0.8, b: 0.3, a: 1}
      });

      await this.sendCommand('create_text', {
        x: x + 120,
        y: y + 60,
        text: 'Active',
        fontSize: 14,
        fontColor: {r: 0.7, g: 0.7, b: 0.7, a: 1},
        name: `${agent.name} Status Text`
      });

      // Progress bar background
      await this.sendCommand('create_frame', {
        x: x + 20,
        y: y + 150,
        width: 300,
        height: 8,
        name: `${agent.name} Progress BG`,
        fillColor: {r: 0.2, g: 0.2, b: 0.25, a: 1}
      });

      // Progress bar fill
      await this.sendCommand('create_frame', {
        x: x + 20,
        y: y + 150,
        width: Math.random() * 300,
        height: 8,
        name: `${agent.name} Progress`,
        fillColor: agent.color
      });
    }

    console.log('\n✅ Multi-Agent UI Created Successfully!');
  }

  async run() {
    try {
      await this.connect();
      await this.createMultiAgentUI();

      console.log('\n📊 Summary:');
      console.log('- 1 Main Dashboard');
      console.log('- 9 Agent Cards');
      console.log('- Status Indicators');
      console.log('- Progress Bars');

      this.ws.close();
      process.exit(0);
    } catch (error) {
      console.error('Error:', error);
      process.exit(1);
    }
  }
}

// Esegui
const channel = process.argv[2] || '5utu5pn0';
console.log(`Using channel: ${channel}`);
console.log('Make sure Figma plugin is connected to this channel!\n');

const creator = new FigmaBatchCreator(channel);
creator.run();