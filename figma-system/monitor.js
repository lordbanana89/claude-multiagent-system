#!/usr/bin/env node

/**
 * FIGMA MONITOR
 * Monitora in real-time tutti i cambiamenti in Figma
 */

const WebSocket = require('ws');

class FigmaMonitor {
  constructor(channel) {
    this.channel = channel;
    this.ws = null;
    this.nodeMap = new Map();
    this.lastSnapshot = null;
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket('ws://localhost:3055');

      this.ws.on('open', () => {
        console.log('[MONITOR] Connesso');
        this.ws.send(JSON.stringify({
          type: 'join',
          channel: this.channel
        }));
        setTimeout(resolve, 500);
      });

      this.ws.on('message', this.handleMessage.bind(this));
      this.ws.on('error', reject);
    });
  }

  handleMessage(data) {
    const msg = JSON.parse(data.toString());

    if (msg.message && msg.message.result) {
      const result = msg.message.result;

      // Rileva tipo di cambiamento
      if (msg.message.command === 'node_modified') {
        this.onNodeModified(result);
      } else if (msg.message.command === 'node_created') {
        this.onNodeCreated(result);
      } else if (msg.message.command === 'node_deleted') {
        this.onNodeDeleted(result);
      }

      // Aggiorna mappa nodi
      if (result.id) {
        this.nodeMap.set(result.id, {
          ...result,
          lastSeen: Date.now()
        });
      }
    }
  }

  onNodeCreated(node) {
    console.log(`CHANGE:CREATE:${node.id}:${node.name || 'unnamed'}`);
    this.emit('node-created', node);
  }

  onNodeModified(node) {
    console.log(`CHANGE:MODIFY:${node.id}:${JSON.stringify(node)}`);
    this.emit('node-modified', node);
  }

  onNodeDeleted(nodeId) {
    console.log(`CHANGE:DELETE:${nodeId}`);
    this.emit('node-deleted', nodeId);
  }

  async startMonitoring() {
    console.log('[MONITOR] Monitoraggio attivo');

    // Snapshot iniziale
    await this.takeSnapshot();

    // Monitora ogni secondo
    setInterval(async () => {
      await this.checkForChanges();
    }, 1000);

    // Gestisci input
    process.stdin.on('data', (data) => {
      const cmd = data.toString().trim();

      if (cmd.startsWith('TRACK:')) {
        const nodeId = cmd.split(':')[1];
        this.trackNode(nodeId);
      } else if (cmd === 'SNAPSHOT') {
        this.takeSnapshot();
      } else if (cmd === 'STATUS') {
        this.printStatus();
      }
    });
  }

  async takeSnapshot() {
    const snapshot = await this.sendCommand('get_document_info');

    if (snapshot && snapshot.children) {
      this.lastSnapshot = {
        timestamp: Date.now(),
        nodes: snapshot.children.map(c => ({
          id: c.id,
          name: c.name,
          type: c.type
        }))
      };

      console.log(`[MONITOR] Snapshot: ${snapshot.children.length} nodi`);
    }
  }

  async checkForChanges() {
    const current = await this.sendCommand('get_document_info');

    if (!current || !current.children || !this.lastSnapshot) return;

    const currentIds = new Set(current.children.map(c => c.id));
    const lastIds = new Set(this.lastSnapshot.nodes.map(n => n.id));

    // Trova nuovi nodi
    for (const child of current.children) {
      if (!lastIds.has(child.id)) {
        this.onNodeCreated(child);
      }
    }

    // Trova nodi rimossi
    for (const node of this.lastSnapshot.nodes) {
      if (!currentIds.has(node.id)) {
        this.onNodeDeleted(node.id);
      }
    }

    // Aggiorna snapshot
    this.lastSnapshot = {
      timestamp: Date.now(),
      nodes: current.children.map(c => ({
        id: c.id,
        name: c.name,
        type: c.type
      }))
    };
  }

  trackNode(nodeId) {
    console.log(`[MONITOR] Tracking nodo: ${nodeId}`);
    this.nodeMap.set(nodeId, {
      tracked: true,
      since: Date.now()
    });
  }

  printStatus() {
    console.log('[MONITOR] Status:');
    console.log(`  Nodi tracciati: ${this.nodeMap.size}`);
    console.log(`  Ultimo snapshot: ${this.lastSnapshot ? new Date(this.lastSnapshot.timestamp).toISOString() : 'N/A'}`);
    console.log(`  Canale: ${this.channel}`);
  }

  async sendCommand(command, params = {}) {
    return new Promise((resolve) => {
      const id = `mon-${Date.now()}`;

      const handler = (data) => {
        const msg = JSON.parse(data.toString());
        if (msg.message && msg.message.id === id) {
          resolve(msg.message.result);
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

  emit(event, data) {
    // Emette eventi per altri script
    if (process.send) {
      process.send({ event, data });
    }
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
  const monitor = new FigmaMonitor(channel);

  monitor.connect()
    .then(() => monitor.startMonitoring())
    .catch(console.error);

  process.on('SIGINT', () => {
    monitor.disconnect();
    process.exit(0);
  });
}

module.exports = FigmaMonitor;