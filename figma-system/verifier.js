#!/usr/bin/env node

/**
 * FIGMA VERIFIER
 * Verifica che ogni operazione sia valida prima di eseguirla
 */

const WebSocket = require('ws');

class FigmaVerifier {
  constructor(channel) {
    this.channel = channel;
    this.ws = null;
    this.verificationLog = [];
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket('ws://localhost:3055');

      this.ws.on('open', () => {
        console.log('[VERIFIER] Connesso');
        this.ws.send(JSON.stringify({
          type: 'join',
          channel: this.channel
        }));
        setTimeout(resolve, 500);
      });

      this.ws.on('error', reject);
    });
  }

  async startVerifying() {
    console.log('[VERIFIER] Sistema di verifica attivo');

    process.stdin.on('data', async (data) => {
      const cmd = data.toString().trim();

      if (cmd.startsWith('VERIFY:')) {
        const parts = cmd.split(':');
        await this.verify(parts[1], parts.slice(2).join(':'));
      } else if (cmd.startsWith('CHECK:')) {
        const parts = cmd.split(':');
        await this.checkBeforeCreate(parts[1], parts[2]);
      } else if (cmd === 'LOG') {
        this.printLog();
      }
    });
  }

  async verify(operation, data) {
    console.log(`[VERIFIER] Verifico: ${operation}`);

    const verification = {
      operation,
      data,
      timestamp: Date.now(),
      valid: true,
      issues: []
    };

    // Verifica in base al tipo di operazione
    switch (operation) {
      case 'CREATE':
        verification.valid = await this.verifyCreate(data);
        break;
      case 'MODIFY':
        verification.valid = await this.verifyModify(data);
        break;
      case 'DELETE':
        verification.valid = await this.verifyDelete(data);
        break;
      default:
        verification.valid = true;
    }

    this.verificationLog.push(verification);

    if (verification.valid) {
      console.log(`VERIFIED:${operation}:${data}`);
    } else {
      console.log(`REJECTED:${operation}:${verification.issues.join(', ')}`);
    }

    return verification.valid;
  }

  async verifyCreate(data) {
    try {
      const config = JSON.parse(data);

      // Verifica coordinate valide
      if (config.x < 0 || config.y < 0) {
        console.log('[VERIFIER] ❌ Coordinate negative');
        return false;
      }

      // Verifica dimensioni valide
      if (config.width && config.width <= 0) {
        console.log('[VERIFIER] ❌ Larghezza non valida');
        return false;
      }

      if (config.height && config.height <= 0) {
        console.log('[VERIFIER] ❌ Altezza non valida');
        return false;
      }

      // Verifica nome unico
      if (config.name) {
        const exists = await this.checkNodeExists(config.name);
        if (exists) {
          console.log(`[VERIFIER] ⚠️ Nome già esistente: ${config.name}`);
        }
      }

      return true;
    } catch (e) {
      console.log('[VERIFIER] ❌ Dati non validi');
      return false;
    }
  }

  async verifyModify(data) {
    try {
      const parts = data.split(':');
      const nodeId = parts[0];

      // Verifica che il nodo esista
      const exists = await this.checkNodeById(nodeId);
      if (!exists) {
        console.log(`[VERIFIER] ❌ Nodo non trovato: ${nodeId}`);
        return false;
      }

      return true;
    } catch (e) {
      return false;
    }
  }

  async verifyDelete(data) {
    // Non permettere cancellazioni per ora
    console.log('[VERIFIER] ⚠️ Cancellazioni non permesse');
    return false;
  }

  async checkBeforeCreate(type, configStr) {
    console.log(`[VERIFIER] Pre-check per ${type}`);

    try {
      const config = JSON.parse(configStr);

      // Controlla spazio disponibile
      const hasSpace = await this.checkAvailableSpace(config.x, config.y, config.width, config.height);
      if (!hasSpace) {
        console.log('[VERIFIER] ⚠️ Spazio occupato');
      }

      // Controlla limiti
      if (config.x + config.width > 1440) {
        console.log('[VERIFIER] ⚠️ Esce dai limiti del canvas');
      }

      console.log(`VERIFIED:${type}:${configStr}`);
      return true;
    } catch (e) {
      console.log(`REJECTED:${type}:Invalid config`);
      return false;
    }
  }

  async checkNodeExists(name) {
    const doc = await this.sendCommand('get_document_info');
    if (!doc || !doc.children) return false;

    return doc.children.some(c => c.name === name);
  }

  async checkNodeById(nodeId) {
    const node = await this.sendCommand('get_node_info', { nodeId });
    return !!node;
  }

  async checkAvailableSpace(x, y, width, height) {
    // Per ora assume sempre spazio disponibile
    // In futuro può controllare sovrapposizioni
    return true;
  }

  async sendCommand(command, params = {}) {
    return new Promise((resolve) => {
      const id = `verify-${Date.now()}`;

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

  printLog() {
    console.log('[VERIFIER] Log verifiche:');
    for (const v of this.verificationLog.slice(-10)) {
      console.log(`  ${new Date(v.timestamp).toISOString()} - ${v.operation}: ${v.valid ? '✓' : '✗'}`);
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
  const verifier = new FigmaVerifier(channel);

  verifier.connect()
    .then(() => verifier.startVerifying())
    .catch(console.error);

  process.on('SIGINT', () => {
    verifier.disconnect();
    process.exit(0);
  });
}

module.exports = FigmaVerifier;