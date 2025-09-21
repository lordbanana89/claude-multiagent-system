#!/usr/bin/env node

/**
 * TEST FIGMA COMMANDS
 * Verifica quali comandi sono supportati dal plugin
 */

const WebSocket = require('ws');

class FigmaCommandTester {
  constructor(channel) {
    this.channel = channel;
    this.ws = null;
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket('ws://localhost:3055');

      this.ws.on('open', () => {
        console.log('✅ Connesso a Figma\n');
        this.ws.send(JSON.stringify({
          type: 'join',
          channel: this.channel
        }));
        setTimeout(resolve, 500);
      });

      this.ws.on('error', reject);
    });
  }

  async testCommand(command, params = {}) {
    return new Promise((resolve) => {
      const id = `test-${Date.now()}`;

      console.log(`\n📝 Test comando: ${command}`);
      console.log(`   Parametri: ${JSON.stringify(params)}`);

      const handler = (data) => {
        const msg = JSON.parse(data.toString());
        if (msg.message && msg.message.id === id) {
          if (msg.message.result) {
            console.log(`   ✅ Supportato! Risultato:`, JSON.stringify(msg.message.result).substring(0, 100));
            resolve(true);
          } else if (msg.message.error) {
            console.log(`   ❌ Errore:`, msg.message.error);
            resolve(false);
          } else {
            console.log(`   ⚠️ Risposta vuota`);
            resolve(false);
          }
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
        console.log(`   ⏱️ Timeout - comando non supportato`);
        this.ws.removeListener('message', handler);
        resolve(false);
      }, 2000);
    });
  }

  async runTests() {
    console.log('╔════════════════════════════════════════╗');
    console.log('║      TEST COMANDI FIGMA PLUGIN        ║');
    console.log('╚════════════════════════════════════════╝\n');

    const commands = [
      // Read commands
      { cmd: 'get_document_info', params: {} },
      { cmd: 'get_selection', params: {} },
      { cmd: 'get_node_info', params: { nodeId: '0:1' } },
      { cmd: 'get_styles', params: {} },

      // Create commands
      { cmd: 'create_frame', params: { x: 100, y: 100, width: 200, height: 100, name: 'Test_Frame' } },
      { cmd: 'create_text', params: { x: 100, y: 200, text: 'Test Text', fontSize: 16 } },
      { cmd: 'create_rectangle', params: { x: 100, y: 300, width: 100, height: 50, name: 'Test_Rect' } },
      { cmd: 'create_ellipse', params: { x: 100, y: 400, width: 50, height: 50, name: 'Test_Ellipse' } },
      { cmd: 'create_star', params: { x: 100, y: 500, width: 50, height: 50, points: 5 } },

      // Modify commands
      { cmd: 'set_fill_color', params: { nodeId: '1:2', color: { r: 1, g: 0, b: 0, a: 1 } } },
      { cmd: 'set_stroke_color', params: { nodeId: '1:2', color: { r: 0, g: 0, b: 1, a: 1 } } },
      { cmd: 'set_corner_radius', params: { nodeId: '1:2', radius: 10 } },
      { cmd: 'set_text', params: { nodeId: '1:3', text: 'New Text' } },
      { cmd: 'set_position', params: { nodeId: '1:2', x: 200, y: 200 } },
      { cmd: 'resize_node', params: { nodeId: '1:2', width: 300, height: 200 } },
      { cmd: 'set_opacity', params: { nodeId: '1:2', opacity: 0.5 } },
      { cmd: 'set_effect', params: { nodeId: '1:2', effect: { type: 'DROP_SHADOW' } } },

      // Selection commands
      { cmd: 'select_node', params: { nodeId: '1:2' } },
      { cmd: 'clear_selection', params: {} },

      // Delete commands (potrebbero non essere supportati)
      { cmd: 'delete_node', params: { nodeId: '1:2' } },
      { cmd: 'delete_selection', params: {} },
      { cmd: 'remove_node', params: { nodeId: '1:2' } },

      // Update commands
      { cmd: 'update_node', params: { nodeId: '1:2', fillColor: { r: 0, g: 1, b: 0, a: 1 } } },

      // Other
      { cmd: 'ping', params: {} },
      { cmd: 'node_modified', params: {} }
    ];

    const results = {
      supported: [],
      unsupported: []
    };

    for (const { cmd, params } of commands) {
      const isSupported = await this.testCommand(cmd, params);
      if (isSupported) {
        results.supported.push(cmd);
      } else {
        results.unsupported.push(cmd);
      }
    }

    console.log('\n\n═══════════════════════════════════════');
    console.log('📊 RISULTATI TEST');
    console.log('═══════════════════════════════════════\n');

    console.log(`✅ COMANDI SUPPORTATI (${results.supported.length}):`);
    results.supported.forEach(cmd => console.log(`   • ${cmd}`));

    console.log(`\n❌ COMANDI NON SUPPORTATI (${results.unsupported.length}):`);
    results.unsupported.forEach(cmd => console.log(`   • ${cmd}`));

    return results;
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
  const tester = new FigmaCommandTester(channel);

  try {
    await tester.connect();
    await tester.runTests();
    tester.disconnect();

  } catch (error) {
    console.error('❌ Errore:', error);
    tester.disconnect();
  }
}

if (require.main === module) {
  main();
}

module.exports = FigmaCommandTester;