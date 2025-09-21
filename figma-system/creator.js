#!/usr/bin/env node

/**
 * FIGMA CREATOR
 * Crea componenti in modo intelligente e coordinato
 */

const WebSocket = require('ws');

class FigmaCreator {
  constructor(channel) {
    this.channel = channel;
    this.ws = null;
    this.createdComponents = new Map();
    this.queue = [];
    this.isCreating = false;
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket('ws://localhost:3055');

      this.ws.on('open', () => {
        console.log('[CREATOR] Connesso');
        this.ws.send(JSON.stringify({
          type: 'join',
          channel: this.channel
        }));
        setTimeout(resolve, 500);
      });

      this.ws.on('message', this.handleResponse.bind(this));
      this.ws.on('error', reject);
    });
  }

  handleResponse(data) {
    const msg = JSON.parse(data.toString());

    if (msg.message && msg.message.result && msg.message.result.id) {
      const result = msg.message.result;

      // Salva componente creato
      this.createdComponents.set(result.id, {
        ...result,
        createdAt: Date.now()
      });

      console.log(`CREATED:${result.id}:${result.name || 'component'}`);
    }
  }

  async startCreating() {
    console.log('[CREATOR] Pronto per creare componenti');

    // Gestisci coda di creazione
    setInterval(() => {
      if (this.queue.length > 0 && !this.isCreating) {
        this.processQueue();
      }
    }, 500);

    // Gestisci comandi
    process.stdin.on('data', async (data) => {
      const cmd = data.toString().trim();

      if (cmd.startsWith('CREATE:')) {
        const parts = cmd.split(':');
        const type = parts[1];
        const config = parts[2] ? JSON.parse(parts.slice(2).join(':')) : {};

        await this.createComponent(type, config);
      } else if (cmd === 'LIST') {
        this.listCreatedComponents();
      } else if (cmd === 'CLEAR') {
        this.clearQueue();
      }
    });
  }

  async createComponent(type, config = {}) {
    console.log(`[CREATOR] Aggiunto in coda: ${type}`);

    this.queue.push({ type, config });

    if (!this.isCreating) {
      await this.processQueue();
    }
  }

  async processQueue() {
    if (this.queue.length === 0) return;

    this.isCreating = true;
    const { type, config } = this.queue.shift();

    console.log(`[CREATOR] Creando: ${type}`);

    switch (type) {
      case 'dashboard':
        await this.createDashboard(config);
        break;
      case 'terminal':
        await this.createTerminal(config);
        break;
      case 'button':
        await this.createButton(config);
        break;
      case 'card':
        await this.createCard(config);
        break;
      case 'agent':
        await this.createAgentCard(config);
        break;
      case 'input':
        await this.createInput(config);
        break;
      case 'modal':
        await this.createModal(config);
        break;
      default:
        await this.createGeneric(type, config);
    }

    this.isCreating = false;
  }

  async createDashboard(config) {
    const {
      x = 100,
      y = 100,
      title = 'MCP Dashboard'
    } = config;

    // Container principale
    const dashboardId = await this.sendCommand('create_frame', {
      x, y,
      width: 1200,
      height: 800,
      name: 'Dashboard_Container',
      fillColor: { r: 0.98, g: 0.98, b: 1, a: 1 }
    });

    // Header
    await this.sendCommand('create_frame', {
      x: 0,
      y: 0,
      width: 1200,
      height: 80,
      name: 'Dashboard_Header',
      fillColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId: dashboardId
    });

    // Title
    await this.sendCommand('create_text', {
      x: 32,
      y: 28,
      text: title,
      fontSize: 24,
      fontWeight: 700,
      parentId: dashboardId
    });

    return dashboardId;
  }

  async createTerminal(config) {
    const {
      x = 100,
      y = 100,
      agent = 'supervisor'
    } = config;

    const terminalId = await this.sendCommand('create_frame', {
      x, y,
      width: 800,
      height: 600,
      name: `Terminal_${agent}`,
      fillColor: { r: 0.08, g: 0.08, b: 0.12, a: 1 }
    });

    // Terminal header
    await this.sendCommand('create_frame', {
      x: 0,
      y: 0,
      width: 800,
      height: 40,
      name: 'Terminal_Header',
      fillColor: { r: 0.06, g: 0.06, b: 0.1, a: 1 },
      parentId: terminalId
    });

    // Terminal title
    await this.sendCommand('create_text', {
      x: 16,
      y: 12,
      text: `${agent}@claude-system`,
      fontSize: 14,
      fontFamily: 'SF Mono',
      fontColor: { r: 0.4, g: 1, b: 0.4, a: 1 },
      parentId: terminalId
    });

    return terminalId;
  }

  async createButton(config) {
    const {
      x = 100,
      y = 100,
      text = 'Button',
      variant = 'primary'
    } = config;

    const colors = {
      primary: { r: 0.2, g: 0.5, b: 1, a: 1 },
      secondary: { r: 0.8, g: 0.8, b: 0.85, a: 1 },
      danger: { r: 0.9, g: 0.2, b: 0.2, a: 1 },
      success: { r: 0.2, g: 0.8, b: 0.4, a: 1 }
    };

    const buttonId = await this.sendCommand('create_frame', {
      x, y,
      width: 120,
      height: 40,
      name: `Button_${text}`,
      fillColor: colors[variant] || colors.primary
    });

    await this.sendCommand('set_corner_radius', {
      nodeId: buttonId,
      radius: 6
    });

    await this.sendCommand('create_text', {
      x: 40,
      y: 12,
      text: text,
      fontSize: 14,
      fontWeight: 500,
      fontColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId: buttonId
    });

    return buttonId;
  }

  async createCard(config) {
    const {
      x = 100,
      y = 100,
      title = 'Card',
      content = 'Content'
    } = config;

    const cardId = await this.sendCommand('create_frame', {
      x, y,
      width: 300,
      height: 200,
      name: `Card_${title}`,
      fillColor: { r: 1, g: 1, b: 1, a: 1 }
    });

    // Shadow
    await this.sendCommand('set_effect', {
      nodeId: cardId,
      effect: {
        type: 'DROP_SHADOW',
        color: { r: 0, g: 0, b: 0, a: 0.1 },
        offset: { x: 0, y: 2 },
        radius: 8
      }
    });

    // Corner radius
    await this.sendCommand('set_corner_radius', {
      nodeId: cardId,
      radius: 8
    });

    // Title
    await this.sendCommand('create_text', {
      x: 20,
      y: 20,
      text: title,
      fontSize: 18,
      fontWeight: 600,
      parentId: cardId
    });

    // Content
    await this.sendCommand('create_text', {
      x: 20,
      y: 50,
      text: content,
      fontSize: 14,
      fontColor: { r: 0.5, g: 0.5, b: 0.5, a: 1 },
      parentId: cardId
    });

    return cardId;
  }

  async createAgentCard(config) {
    const {
      x = 100,
      y = 100,
      agent = 'supervisor',
      status = 'active'
    } = config;

    const cardId = await this.sendCommand('create_frame', {
      x, y,
      width: 250,
      height: 120,
      name: `Agent_${agent}`,
      fillColor: { r: 0.98, g: 0.98, b: 0.99, a: 1 }
    });

    // Status indicator
    const statusColor = status === 'active'
      ? { r: 0.2, g: 0.8, b: 0.4, a: 1 }
      : { r: 0.6, g: 0.6, b: 0.6, a: 1 };

    await this.sendCommand('create_ellipse', {
      x: 16,
      y: 16,
      width: 12,
      height: 12,
      fillColor: statusColor,
      parentId: cardId
    });

    // Agent name
    await this.sendCommand('create_text', {
      x: 36,
      y: 14,
      text: agent,
      fontSize: 16,
      fontWeight: 600,
      parentId: cardId
    });

    // Status text
    await this.sendCommand('create_text', {
      x: 16,
      y: 45,
      text: `Status: ${status}`,
      fontSize: 12,
      fontColor: { r: 0.5, g: 0.5, b: 0.5, a: 1 },
      parentId: cardId
    });

    return cardId;
  }

  async createInput(config) {
    const {
      x = 100,
      y = 100,
      label = 'Input',
      placeholder = 'Enter text...'
    } = config;

    const containerId = await this.sendCommand('create_frame', {
      x, y,
      width: 300,
      height: 70,
      name: `Input_${label}`,
      fillColor: { r: 0, g: 0, b: 0, a: 0 }
    });

    // Label
    await this.sendCommand('create_text', {
      x: 0,
      y: 0,
      text: label,
      fontSize: 12,
      fontWeight: 500,
      fontColor: { r: 0.4, g: 0.4, b: 0.4, a: 1 },
      parentId: containerId
    });

    // Input field
    const inputId = await this.sendCommand('create_frame', {
      x: 0,
      y: 20,
      width: 300,
      height: 40,
      name: 'Input_Field',
      fillColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId: containerId
    });

    // Border
    await this.sendCommand('set_stroke_color', {
      nodeId: inputId,
      color: { r: 0.8, g: 0.8, b: 0.85, a: 1 },
      strokeWeight: 1
    });

    await this.sendCommand('set_corner_radius', {
      nodeId: inputId,
      radius: 4
    });

    // Placeholder
    await this.sendCommand('create_text', {
      x: 12,
      y: 12,
      text: placeholder,
      fontSize: 14,
      fontColor: { r: 0.6, g: 0.6, b: 0.65, a: 1 },
      parentId: inputId
    });

    return containerId;
  }

  async createModal(config) {
    const {
      x = 400,
      y = 200,
      title = 'Modal Title',
      content = 'Modal content'
    } = config;

    // Backdrop
    const backdropId = await this.sendCommand('create_frame', {
      x: 0,
      y: 0,
      width: 1440,
      height: 900,
      name: 'Modal_Backdrop',
      fillColor: { r: 0, g: 0, b: 0, a: 0.5 }
    });

    // Modal
    const modalId = await this.sendCommand('create_frame', {
      x, y,
      width: 400,
      height: 300,
      name: 'Modal',
      fillColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId: backdropId
    });

    await this.sendCommand('set_corner_radius', {
      nodeId: modalId,
      radius: 12
    });

    await this.sendCommand('set_effect', {
      nodeId: modalId,
      effect: {
        type: 'DROP_SHADOW',
        color: { r: 0, g: 0, b: 0, a: 0.2 },
        offset: { x: 0, y: 4 },
        radius: 16
      }
    });

    // Title
    await this.sendCommand('create_text', {
      x: 24,
      y: 24,
      text: title,
      fontSize: 20,
      fontWeight: 600,
      parentId: modalId
    });

    // Content
    await this.sendCommand('create_text', {
      x: 24,
      y: 70,
      text: content,
      fontSize: 14,
      fontColor: { r: 0.4, g: 0.4, b: 0.4, a: 1 },
      parentId: modalId
    });

    return backdropId;
  }

  async createGeneric(type, config) {
    const {
      x = 100,
      y = 100,
      width = 200,
      height = 100,
      name = type
    } = config;

    return await this.sendCommand('create_frame', {
      x, y, width, height, name,
      fillColor: { r: 0.95, g: 0.95, b: 0.96, a: 1 }
    });
  }

  async sendCommand(command, params = {}) {
    return new Promise((resolve) => {
      const id = `create-${Date.now()}`;

      const handler = (data) => {
        const msg = JSON.parse(data.toString());
        if (msg.message && msg.message.id === id) {
          resolve(msg.message.result?.id || null);
          this.ws.removeListener('message', handler);
        }
      };

      this.ws.on('message', handler);

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
        this.ws.removeListener('message', handler);
        resolve(null);
      }, 1000);
    });
  }

  listCreatedComponents() {
    console.log('[CREATOR] Componenti creati:');
    for (const [id, component] of this.createdComponents) {
      console.log(`  ${id}: ${component.name || 'unnamed'} (${new Date(component.createdAt).toISOString()})`);
    }
  }

  clearQueue() {
    console.log(`[CREATOR] Coda svuotata (${this.queue.length} elementi rimossi)`);
    this.queue = [];
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Main
if (require.main === module) {
  const channel = process.argv[2] || process.env.FIGMA_CHANNEL || '5utu5pn0';
  const creator = new FigmaCreator(channel);

  creator.connect()
    .then(() => creator.startCreating())
    .catch(console.error);

  process.on('SIGINT', () => {
    creator.disconnect();
    process.exit(0);
  });
}

module.exports = FigmaCreator;