#!/usr/bin/env node

/**
 * FIGMA DIRECT CONTROL
 * Controllo puntuale e preciso di ogni elemento in Figma
 */

const WebSocket = require('ws');
const readline = require('readline');

class FigmaDirectControl {
  constructor(channel) {
    this.channel = channel;
    this.ws = null;
    this.selectedNode = null;
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket('ws://localhost:3055');

      this.ws.on('open', () => {
        console.log('✅ Connesso a Figma - Controllo Diretto');
        this.ws.send(JSON.stringify({
          type: 'join',
          channel: this.channel
        }));
        setTimeout(resolve, 500);
      });

      this.ws.on('message', (data) => {
        const msg = JSON.parse(data.toString());
        if (msg.message && msg.message.result) {
          this.handleResponse(msg.message);
        }
      });

      this.ws.on('error', reject);
    });
  }

  handleResponse(message) {
    if (message.command === 'get_selection' && message.result.selection?.length > 0) {
      this.selectedNode = message.result.selection[0];
      console.log(`\n✅ Selezionato: ${this.selectedNode.name} (${this.selectedNode.id})`);
    } else if (message.result) {
      console.log(`\n✅ Comando eseguito`);
      if (message.result.id) {
        console.log(`   ID: ${message.result.id}`);
        console.log(`   Nome: ${message.result.name || 'N/A'}`);
      }
    }
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

    this.ws.send(JSON.stringify(message));
    await new Promise(resolve => setTimeout(resolve, 200));
  }

  // ============== COMANDI DIRETTI ==============

  async selectNode(nodeId) {
    await this.sendCommand('select_node', { nodeId });
    this.selectedNode = { id: nodeId };
  }

  async modifySelected(changes) {
    if (!this.selectedNode) {
      console.log('❌ Nessun elemento selezionato!');
      return;
    }

    // Modifica diretta dell'elemento selezionato
    if (changes.text !== undefined) {
      await this.sendCommand('set_text', {
        nodeId: this.selectedNode.id,
        text: changes.text
      });
    }

    if (changes.fillColor) {
      await this.sendCommand('set_fill_color', {
        nodeId: this.selectedNode.id,
        color: changes.fillColor
      });
    }

    if (changes.position) {
      await this.sendCommand('set_position', {
        nodeId: this.selectedNode.id,
        x: changes.position.x,
        y: changes.position.y
      });
    }

    if (changes.size) {
      await this.sendCommand('resize_node', {
        nodeId: this.selectedNode.id,
        width: changes.size.width,
        height: changes.size.height
      });
    }

    if (changes.opacity !== undefined) {
      await this.sendCommand('set_opacity', {
        nodeId: this.selectedNode.id,
        opacity: changes.opacity
      });
    }

    if (changes.cornerRadius !== undefined) {
      await this.sendCommand('set_corner_radius', {
        nodeId: this.selectedNode.id,
        radius: changes.cornerRadius
      });
    }
  }

  // ============== MODIFICHE PUNTUALI ==============

  async updateDashboardTitle(newTitle) {
    console.log(`\n📝 Aggiorno titolo dashboard: "${newTitle}"`);
    await this.sendCommand('set_text', {
      nodeId: '5:157', // Dashboard_Title
      text: newTitle
    });
  }

  async updateAgentStatus(agentName, status, color) {
    console.log(`\n🔄 Aggiorno stato ${agentName}: ${status}`);

    // Mappa gli ID degli agenti
    const agentIds = {
      'supervisor': { card: '5:179', status: '5:180' },
      'master': { card: '5:186', status: '5:187' },
      'backend-api': { card: '5:193', status: '5:194' },
      'database': { card: '5:200', status: '5:201' },
      'frontend-ui': { card: '5:207', status: '5:208' },
      'testing': { card: '5:214', status: '5:215' },
      'queue-manager': { card: '5:221', status: '5:222' },
      'instagram': { card: '5:228', status: '5:229' },
      'deployment': { card: '5:235', status: '5:236' }
    };

    const agent = agentIds[agentName];
    if (agent) {
      // Aggiorna colore status indicator
      await this.sendCommand('set_fill_color', {
        nodeId: agent.status,
        color: color || { r: 0.2, g: 0.8, b: 0.4, a: 1 }
      });

      // Aggiorna testo status (assumendo che sia il secondo testo nel card)
      await this.sendCommand('set_text', {
        nodeId: `${agent.card.split(':')[0]}:${parseInt(agent.card.split(':')[1]) + 3}`,
        text: `Status: ${status}`
      });
    }
  }

  async addActivityItem(agent, action, time) {
    console.log(`\n➕ Aggiungo attività: ${agent} - ${action}`);

    // Crea nuovo item nell'activity feed
    const activityFeedId = '5:242';
    const yOffset = 70 + (5 * 80); // Dopo i 5 item esistenti

    const itemId = await this.sendCommand('create_frame', {
      x: 24,
      y: yOffset,
      width: 400,
      height: 70,
      name: `Activity_Item_New`,
      fillColor: { r: 0.98, g: 0.98, b: 0.99, a: 1 },
      parentId: activityFeedId
    });

    // Aggiungi testi
    await this.sendCommand('create_text', {
      x: 12,
      y: 12,
      text: agent,
      fontSize: 12,
      fontWeight: 600,
      fontColor: { r: 0.2, g: 0.5, b: 1, a: 1 },
      parentId: itemId
    });

    await this.sendCommand('create_text', {
      x: 12,
      y: 32,
      text: action,
      fontSize: 12,
      parentId: itemId
    });

    await this.sendCommand('create_text', {
      x: 12,
      y: 50,
      text: time,
      fontSize: 10,
      fontColor: { r: 0.6, g: 0.6, b: 0.6, a: 1 },
      parentId: itemId
    });
  }

  async updateTerminalOutput(lines) {
    console.log(`\n💻 Aggiorno output terminal`);

    const terminalContentId = '5:299';
    let lineY = 20;

    for (const line of lines) {
      await this.sendCommand('create_text', {
        x: 20,
        y: lineY,
        text: line.text,
        fontSize: 13,
        fontFamily: 'SF Mono',
        fontWeight: line.bold ? 600 : 400,
        fontColor: line.color || { r: 0.8, g: 0.8, b: 0.9, a: 1 },
        parentId: terminalContentId
      });
      lineY += 20;
    }
  }

  async highlightComponent(componentId, color = { r: 1, g: 0.5, b: 0, a: 1 }) {
    console.log(`\n✨ Evidenzio componente ${componentId}`);

    await this.sendCommand('set_stroke_color', {
      nodeId: componentId,
      color: color,
      strokeWeight: 3
    });

    // Rimuovi highlight dopo 2 secondi
    setTimeout(async () => {
      await this.sendCommand('set_stroke_color', {
        nodeId: componentId,
        color: { r: 0, g: 0, b: 0, a: 0 },
        strokeWeight: 0
      });
    }, 2000);
  }

  // ============== INTERACTIVE MODE ==============

  async interactiveMode() {
    console.log('\n╔═══════════════════════════════════════╗');
    console.log('║     FIGMA DIRECT CONTROL MODE         ║');
    console.log('╚═══════════════════════════════════════╝\n');

    console.log('Comandi disponibili:');
    console.log('  select <id>     - Seleziona elemento per ID');
    console.log('  text <testo>    - Cambia testo elemento selezionato');
    console.log('  color r g b     - Cambia colore (0-1)');
    console.log('  move x y        - Sposta elemento');
    console.log('  size w h        - Ridimensiona');
    console.log('  radius n        - Corner radius');
    console.log('  opacity n       - Opacità (0-1)');
    console.log('  agent <name> <status> - Aggiorna agent status');
    console.log('  activity <agent> <action> <time> - Aggiungi attività');
    console.log('  title <text>    - Cambia titolo dashboard');
    console.log('  highlight <id>  - Evidenzia componente');
    console.log('  exit            - Esci\n');

    this.promptCommand();
  }

  promptCommand() {
    this.rl.question('figma> ', async (input) => {
      const parts = input.trim().split(' ');
      const cmd = parts[0];

      switch(cmd) {
        case 'select':
          await this.selectNode(parts[1]);
          break;

        case 'text':
          await this.modifySelected({ text: parts.slice(1).join(' ') });
          break;

        case 'color':
          await this.modifySelected({
            fillColor: {
              r: parseFloat(parts[1]),
              g: parseFloat(parts[2]),
              b: parseFloat(parts[3]),
              a: 1
            }
          });
          break;

        case 'move':
          await this.modifySelected({
            position: { x: parseInt(parts[1]), y: parseInt(parts[2]) }
          });
          break;

        case 'size':
          await this.modifySelected({
            size: { width: parseInt(parts[1]), height: parseInt(parts[2]) }
          });
          break;

        case 'radius':
          await this.modifySelected({ cornerRadius: parseInt(parts[1]) });
          break;

        case 'opacity':
          await this.modifySelected({ opacity: parseFloat(parts[1]) });
          break;

        case 'agent':
          await this.updateAgentStatus(
            parts[1],
            parts[2],
            parts[3] === 'green' ? { r: 0.2, g: 0.8, b: 0.4, a: 1 } :
            parts[3] === 'red' ? { r: 0.9, g: 0.2, b: 0.2, a: 1 } :
            { r: 0.6, g: 0.6, b: 0.6, a: 1 }
          );
          break;

        case 'activity':
          await this.addActivityItem(
            parts[1],
            parts.slice(2, -1).join(' '),
            parts[parts.length - 1]
          );
          break;

        case 'title':
          await this.updateDashboardTitle(parts.slice(1).join(' '));
          break;

        case 'highlight':
          await this.highlightComponent(parts[1]);
          break;

        case 'exit':
          console.log('\n👋 Arrivederci!');
          this.disconnect();
          process.exit(0);
          break;

        default:
          console.log('❓ Comando non riconosciuto');
      }

      this.promptCommand();
    });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
    this.rl.close();
  }
}

// ============== MAIN ==============

async function main() {
  const channel = process.argv[2] || '5utu5pn0';
  const control = new FigmaDirectControl(channel);

  try {
    await control.connect();

    // Se viene passato un comando specifico, eseguilo
    if (process.argv[3]) {
      const command = process.argv[3];
      const args = process.argv.slice(4);

      switch(command) {
        case 'title':
          await control.updateDashboardTitle(args.join(' '));
          break;
        case 'agent':
          await control.updateAgentStatus(args[0], args[1]);
          break;
        case 'activity':
          await control.addActivityItem(args[0], args[1], args[2]);
          break;
        case 'highlight':
          await control.highlightComponent(args[0]);
          break;
        default:
          console.log('Comando non supportato');
      }

      setTimeout(() => {
        control.disconnect();
        process.exit(0);
      }, 1000);
    } else {
      // Altrimenti entra in modalità interattiva
      await control.interactiveMode();
    }

  } catch (error) {
    console.error('❌ Errore:', error);
    control.disconnect();
  }
}

if (require.main === module) {
  main();
}

module.exports = FigmaDirectControl;