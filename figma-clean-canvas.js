#!/usr/bin/env node

/**
 * FIGMA CLEAN CANVAS
 * Pulisce completamente il canvas di Figma
 */

const WebSocket = require('ws');

class FigmaCanvasCleaner {
  constructor(channel) {
    this.channel = channel;
    this.ws = null;
    this.deletedCount = 0;
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket('ws://localhost:3055');

      this.ws.on('open', () => {
        console.log('✅ Connesso a Figma');
        this.ws.send(JSON.stringify({
          type: 'join',
          channel: this.channel
        }));
        setTimeout(resolve, 500);
      });

      this.ws.on('message', (data) => {
        const msg = JSON.parse(data.toString());
        if (msg.message && msg.message.result) {
          // console.log('Risposta:', msg.message.result);
        }
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

      const handler = (data) => {
        const msg = JSON.parse(data.toString());
        if (msg.message && msg.message.id === id) {
          resolve(msg.message.result);
          this.ws.removeListener('message', handler);
        }
      };

      this.ws.on('message', handler);
      this.ws.send(JSON.stringify(message));

      setTimeout(() => {
        this.ws.removeListener('message', handler);
        resolve(null);
      }, 1000);
    });
  }

  async cleanCanvas() {
    console.log('\n🧹 Pulizia Canvas Figma...\n');

    // Ottieni tutti gli elementi nella pagina
    const docInfo = await this.sendCommand('get_document_info');

    if (!docInfo || !docInfo.children) {
      console.log('❌ Non riesco a ottenere info documento');
      return;
    }

    console.log(`📊 Trovati ${docInfo.children.length} elementi da rimuovere\n`);

    // Elimina ogni elemento (tranne la pagina stessa)
    for (const child of docInfo.children) {
      if (child.type !== 'PAGE') {
        console.log(`🗑️ Elimino: ${child.name} (${child.id})`);

        // Prova a eliminare
        const deleted = await this.sendCommand('delete_node', {
          nodeId: child.id
        });

        if (deleted !== null) {
          this.deletedCount++;
        }

        // Piccola pausa per non sovraccaricare
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    }

    console.log(`\n✅ Canvas pulito! Rimossi ${this.deletedCount} elementi\n`);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Main
async function main() {
  const channel = process.argv[2] || '5utu5pn0';

  console.log('╔════════════════════════════════════════╗');
  console.log('║         FIGMA CANVAS CLEANER           ║');
  console.log('╚════════════════════════════════════════╝');

  const cleaner = new FigmaCanvasCleaner(channel);

  try {
    await cleaner.connect();
    await cleaner.cleanCanvas();
    cleaner.disconnect();

    console.log('🎨 Canvas ora è vuoto e pronto per nuovi elementi!\n');

  } catch (error) {
    console.error('❌ Errore:', error);
    cleaner.disconnect();
  }
}

if (require.main === module) {
  main();
}

module.exports = FigmaCanvasCleaner;