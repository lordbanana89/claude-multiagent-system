#!/usr/bin/env node

/**
 * REPLICATE FRONTEND TO FIGMA
 * Replica l'intero frontend del sistema Claude Multi-Agent
 */

const { spawn } = require('child_process');

class FrontendReplicator {
  constructor() {
    this.coordinator = null;
    this.componentsToCreate = [];
  }

  async connect() {
    console.log('🚀 Connessione al coordinator...\n');

    // Usa il coordinator esistente tramite echo di comandi
    this.sendCommand = (cmd) => {
      return new Promise((resolve) => {
        const echo = spawn('echo', [cmd]);
        const node = spawn('node', ['figma-system/coordinator.js']);

        echo.stdout.pipe(node.stdin);

        node.stdout.on('data', (data) => {
          const output = data.toString();
          if (output.includes('CREATED:') || output.includes('VERIFIED:')) {
            console.log(`   ✅ ${output.trim()}`);
          }
        });

        setTimeout(resolve, 500);
      });
    };
  }

  async replicateFrontend() {
    console.log('╔════════════════════════════════════════╗');
    console.log('║   REPLICATING CLAUDE FRONTEND TO FIGMA ║');
    console.log('╚════════════════════════════════════════╝\n');

    // 1. Dashboard principale
    await this.createMainDashboard();

    // 2. Agent Cards
    await this.createAgentCards();

    // 3. Terminal Interface
    await this.createTerminalInterface();

    // 4. Component Library
    await this.createComponentLibrary();

    // 5. Activity Feed
    await this.createActivityFeed();

    console.log('\n✅ Frontend replicato con successo!\n');
  }

  async createMainDashboard() {
    console.log('📊 Creando Dashboard principale...');

    await this.sendCommand('CREATE:dashboard:{"x":100,"y":100,"title":"🚀 Claude Multi-Agent System"}');

    // Stats cards
    const stats = [
      { title: 'Active Agents', value: '9', color: 'success' },
      { title: 'Messages', value: '1,234', color: 'primary' },
      { title: 'Tasks', value: '56', color: 'secondary' },
      { title: 'Errors', value: '0', color: 'danger' }
    ];

    for (let i = 0; i < stats.length; i++) {
      const stat = stats[i];
      await this.sendCommand(`CREATE:card:{"x":${120 + i * 280},"y":200,"title":"${stat.title}","content":"${stat.value}"}`);
    }

    console.log('   ✓ Dashboard creato\n');
  }

  async createAgentCards() {
    console.log('🤖 Creando Agent Cards...');

    const agents = [
      'supervisor', 'master', 'backend-api',
      'database', 'frontend-ui', 'testing',
      'queue-manager', 'instagram', 'deployment'
    ];

    for (let i = 0; i < agents.length; i++) {
      const agent = agents[i];
      const row = Math.floor(i / 3);
      const col = i % 3;
      const x = 120 + col * 280;
      const y = 350 + row * 140;

      await this.sendCommand(`CREATE:agent:{"x":${x},"y":${y},"agent":"${agent}","status":"active"}`);
    }

    console.log('   ✓ Agent cards create\n');
  }

  async createTerminalInterface() {
    console.log('💻 Creando Terminal Interface...');

    await this.sendCommand('CREATE:terminal:{"x":100,"y":800,"agent":"supervisor"}');

    console.log('   ✓ Terminal creato\n');
  }

  async createComponentLibrary() {
    console.log('🎨 Creando Component Library...');

    // Buttons
    const buttons = ['Primary', 'Secondary', 'Success', 'Danger'];
    for (let i = 0; i < buttons.length; i++) {
      await this.sendCommand(`CREATE:button:{"x":${1200 + i * 130},"y":100,"text":"${buttons[i]}","variant":"${buttons[i].toLowerCase()}"}`);
    }

    // Inputs
    await this.sendCommand('CREATE:input:{"x":1200,"y":200,"label":"Email","placeholder":"user@example.com"}');
    await this.sendCommand('CREATE:input:{"x":1200,"y":290,"label":"Password","placeholder":"••••••••"}');

    // Modal
    await this.sendCommand('CREATE:modal:{"x":1200,"y":400,"title":"Confirm Action","content":"Are you sure you want to proceed?"}');

    console.log('   ✓ Component library creata\n');
  }

  async createActivityFeed() {
    console.log('📋 Creando Activity Feed...');

    await this.sendCommand('CREATE:card:{"x":1200,"y":600,"title":"Recent Activity","content":"Loading activities..."}');

    console.log('   ✓ Activity feed creato\n');
  }
}

// Script diretto per inviare comandi al sistema
async function sendDirectCommand(command) {
  const net = require('net');

  const client = net.createConnection({ port: 9999 }, () => {
    client.write(command + '\n');
  });

  client.on('data', (data) => {
    console.log('Risposta:', data.toString());
    client.end();
  });

  client.on('error', (err) => {
    // Usa WebSocket direttamente
    const WebSocket = require('ws');
    const ws = new WebSocket('ws://localhost:3055');

    ws.on('open', () => {
      const [cmd, type, ...rest] = command.split(':');
      const config = rest.length > 0 ? JSON.parse(rest.join(':')) : {};

      // Crea direttamente in base al tipo
      const commands = {
        dashboard: () => createDashboard(ws, config),
        agent: () => createAgentCard(ws, config),
        button: () => createButton(ws, config),
        card: () => createCard(ws, config),
        terminal: () => createTerminal(ws, config),
        input: () => createInput(ws, config),
        modal: () => createModal(ws, config)
      };

      if (commands[type]) {
        commands[type]();
      }
    });
  });
}

// Funzioni helper per creare componenti direttamente
function createDashboard(ws, config) {
  const id = `dash-${Date.now()}`;
  ws.send(JSON.stringify({
    id,
    type: 'message',
    channel: '5utu5pn0',
    message: {
      id,
      command: 'create_frame',
      params: {
        x: config.x || 100,
        y: config.y || 100,
        width: 1400,
        height: 900,
        name: 'Dashboard_Main',
        fillColor: { r: 0.98, g: 0.98, b: 1, a: 1 },
        commandId: id
      }
    }
  }));

  setTimeout(() => {
    // Aggiungi titolo
    const titleId = `title-${Date.now()}`;
    ws.send(JSON.stringify({
      id: titleId,
      type: 'message',
      channel: '5utu5pn0',
      message: {
        id: titleId,
        command: 'create_text',
        params: {
          x: (config.x || 100) + 40,
          y: (config.y || 100) + 30,
          text: config.title || 'Claude Multi-Agent System',
          fontSize: 28,
          fontWeight: 700,
          commandId: titleId
        }
      }
    }));
  }, 500);

  console.log(`✅ Dashboard creato`);
  setTimeout(() => ws.close(), 1500);
}

function createAgentCard(ws, config) {
  const id = `agent-${Date.now()}`;
  ws.send(JSON.stringify({
    id,
    type: 'message',
    channel: '5utu5pn0',
    message: {
      id,
      command: 'create_frame',
      params: {
        x: config.x || 100,
        y: config.y || 100,
        width: 250,
        height: 120,
        name: `Agent_${config.agent || 'unknown'}`,
        fillColor: { r: 1, g: 1, b: 1, a: 1 },
        commandId: id
      }
    }
  }));

  setTimeout(() => {
    // Status dot
    const dotId = `dot-${Date.now()}`;
    ws.send(JSON.stringify({
      id: dotId,
      type: 'message',
      channel: '5utu5pn0',
      message: {
        id: dotId,
        command: 'create_ellipse',
        params: {
          x: (config.x || 100) + 16,
          y: (config.y || 100) + 16,
          width: 12,
          height: 12,
          fillColor: config.status === 'active'
            ? { r: 0.2, g: 0.8, b: 0.4, a: 1 }
            : { r: 0.6, g: 0.6, b: 0.6, a: 1 },
          commandId: dotId
        }
      }
    }));

    // Agent name
    const nameId = `name-${Date.now()}`;
    ws.send(JSON.stringify({
      id: nameId,
      type: 'message',
      channel: '5utu5pn0',
      message: {
        id: nameId,
        command: 'create_text',
        params: {
          x: (config.x || 100) + 36,
          y: (config.y || 100) + 14,
          text: config.agent || 'agent',
          fontSize: 16,
          fontWeight: 600,
          commandId: nameId
        }
      }
    }));
  }, 500);

  console.log(`✅ Agent card ${config.agent} creato`);
  setTimeout(() => ws.close(), 1500);
}

function createButton(ws, config) {
  const id = `btn-${Date.now()}`;

  const colors = {
    primary: { r: 0.2, g: 0.5, b: 1, a: 1 },
    secondary: { r: 0.8, g: 0.8, b: 0.85, a: 1 },
    success: { r: 0.2, g: 0.8, b: 0.4, a: 1 },
    danger: { r: 0.9, g: 0.2, b: 0.2, a: 1 }
  };

  ws.send(JSON.stringify({
    id,
    type: 'message',
    channel: '5utu5pn0',
    message: {
      id,
      command: 'create_frame',
      params: {
        x: config.x || 100,
        y: config.y || 100,
        width: 120,
        height: 40,
        name: `Button_${config.text || 'Button'}`,
        fillColor: colors[config.variant] || colors.primary,
        commandId: id
      }
    }
  }));

  setTimeout(() => {
    const textId = `btn-text-${Date.now()}`;
    ws.send(JSON.stringify({
      id: textId,
      type: 'message',
      channel: '5utu5pn0',
      message: {
        id: textId,
        command: 'create_text',
        params: {
          x: (config.x || 100) + 40,
          y: (config.y || 100) + 12,
          text: config.text || 'Button',
          fontSize: 14,
          fontWeight: 500,
          fontColor: { r: 1, g: 1, b: 1, a: 1 },
          commandId: textId
        }
      }
    }));
  }, 500);

  console.log(`✅ Button ${config.text} creato`);
  setTimeout(() => ws.close(), 1500);
}

// Main diretto con WebSocket
async function replicateDirectly() {
  const WebSocket = require('ws');

  console.log('╔════════════════════════════════════════╗');
  console.log('║   REPLICATING FRONTEND TO FIGMA        ║');
  console.log('╚════════════════════════════════════════╝\n');

  // Dashboard
  console.log('📊 Creando Dashboard...');
  await createComponent('dashboard', { x: 100, y: 100, title: '🚀 Claude Multi-Agent System' });

  // Agent Cards
  console.log('🤖 Creando Agent Cards...');
  const agents = ['supervisor', 'master', 'backend-api', 'database', 'frontend-ui', 'testing'];
  for (let i = 0; i < agents.length; i++) {
    const row = Math.floor(i / 3);
    const col = i % 3;
    await createComponent('agent', {
      x: 150 + col * 270,
      y: 250 + row * 140,
      agent: agents[i],
      status: 'active'
    });
  }

  // Buttons
  console.log('🔘 Creando Buttons...');
  const buttons = ['Primary', 'Secondary', 'Success', 'Danger'];
  for (let i = 0; i < buttons.length; i++) {
    await createComponent('button', {
      x: 150 + i * 130,
      y: 600,
      text: buttons[i],
      variant: buttons[i].toLowerCase()
    });
  }

  console.log('\n✅ Frontend replicato con successo!\n');
}

async function createComponent(type, config) {
  return new Promise((resolve) => {
    const ws = new WebSocket('ws://localhost:3055');

    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: 'join',
        channel: '5utu5pn0'
      }));

      setTimeout(() => {
        if (type === 'dashboard') {
          createDashboard(ws, config);
        } else if (type === 'agent') {
          createAgentCard(ws, config);
        } else if (type === 'button') {
          createButton(ws, config);
        }
      }, 300);
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      resolve();
    };

    setTimeout(resolve, 2000);
  });
}

// Esegui direttamente
if (require.main === module) {
  replicateDirectly().catch(console.error);
}