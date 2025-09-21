#!/usr/bin/env node

/**
 * Verifica lo stato attuale di Figma
 * Ottiene info sul documento e selezione corrente
 */

const WebSocket = require('ws');

class FigmaVerifier {
  constructor(channel) {
    this.channel = channel;
    this.ws = null;
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
          console.log('\n📊 Risposta da Figma:');
          console.log(JSON.stringify(msg.message.result, null, 2));
        }
      });

      this.ws.on('error', reject);
    });
  }

  async sendCommand(command, params = {}) {
    const id = `cmd-${Date.now()}`;
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

    console.log(`\n→ Eseguo comando: ${command}`);
    this.ws.send(JSON.stringify(message));

    // Aspetta per la risposta
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  async verify() {
    console.log('\n🔍 Verifico stato Figma...\n');

    // 1. Info documento
    await this.sendCommand('get_document_info');

    // 2. Selezione corrente
    await this.sendCommand('get_selection');

    // 3. Provo a creare un elemento di test per confermare funzionamento
    console.log('\n✏️ Creo elemento di test...');
    await this.sendCommand('create_text', {
      x: 100,
      y: 50,
      text: `✅ Verifica ${new Date().toLocaleTimeString()}`,
      fontSize: 16,
      fontColor: { r: 0.2, g: 0.8, b: 0.4, a: 1 },
      name: 'Verification_Test'
    });

    console.log('\n✅ Verifica completata!');
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Esecuzione
async function main() {
  const channel = process.argv[2] || '5utu5pn0';
  const verifier = new FigmaVerifier(channel);

  try {
    await verifier.connect();
    await verifier.verify();

    setTimeout(() => {
      verifier.disconnect();
      console.log('\n👋 Disconnesso');
    }, 2000);

  } catch (error) {
    console.error('❌ Errore:', error);
    verifier.disconnect();
  }
}

if (require.main === module) {
  main();
}

module.exports = FigmaVerifier;