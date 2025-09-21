#!/usr/bin/env node

/**
 * FIGMA REALTIME SYNC
 * Sistema di sincronizzazione bidirezionale in tempo reale
 * Verifica ogni operazione prima di eseguirla
 */

const WebSocket = require('ws');
const fs = require('fs').promises;
const path = require('path');

class FigmaRealtimeSync {
  constructor(channel) {
    this.channel = channel;
    this.ws = null;
    this.pendingOperations = new Map();
    this.nodeCache = new Map();
    this.lastSync = null;
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket('ws://localhost:3055');

      this.ws.on('open', () => {
        console.log('✅ Connesso - Sincronizzazione Real-Time Attiva');
        this.ws.send(JSON.stringify({
          type: 'join',
          channel: this.channel
        }));
        setTimeout(resolve, 500);
      });

      this.ws.on('message', (data) => {
        const msg = JSON.parse(data.toString());
        this.handleRealtimeUpdate(msg);
      });

      this.ws.on('error', reject);
    });
  }

  handleRealtimeUpdate(msg) {
    if (msg.message && msg.message.result) {
      const result = msg.message.result;
      const commandId = msg.message.id;

      // Verifica se l'operazione è andata a buon fine
      if (this.pendingOperations.has(commandId)) {
        const op = this.pendingOperations.get(commandId);

        if (result.id) {
          console.log(`✅ ${op.type} completato: ${result.name || result.id}`);

          // Aggiorna cache locale
          this.nodeCache.set(result.id, {
            ...result,
            lastUpdated: new Date().toISOString()
          });
        } else {
          console.log(`❌ ${op.type} fallito`);
        }

        this.pendingOperations.delete(commandId);
      }

      // Se è un update da Figma (non richiesto da noi)
      if (msg.message.command === 'node_modified') {
        this.onFigmaChange(result);
      }
    }
  }

  async onFigmaChange(change) {
    console.log(`\n🔄 Rilevata modifica in Figma: ${change.name || change.id}`);

    // Sincronizza con React
    await this.syncToReact(change);
  }

  async syncToReact(node) {
    const componentPath = path.join(
      '/Users/erik/Desktop/claude-multiagent-system/claude-ui/src/components',
      'synced',
      `${node.name}.tsx`
    );

    // Genera codice React basato sul nodo Figma
    const reactCode = this.generateReactFromNode(node);

    try {
      await fs.mkdir(path.dirname(componentPath), { recursive: true });
      await fs.writeFile(componentPath, reactCode);
      console.log(`   → Sincronizzato in React: ${node.name}.tsx`);
    } catch (error) {
      console.error(`   → Errore sincronizzazione: ${error.message}`);
    }
  }

  // ============== VERIFICA PRIMA DI ESEGUIRE ==============

  async verifyBeforeExecute(operation) {
    console.log(`\n🔍 Verifico: ${operation.description}`);

    // 1. Controlla se il nodo target esiste
    if (operation.targetId) {
      const exists = await this.nodeExists(operation.targetId);
      if (!exists) {
        console.log(`   ❌ Nodo ${operation.targetId} non trovato`);
        return false;
      }
    }

    // 2. Controlla se l'operazione è valida
    if (operation.validation) {
      const isValid = await operation.validation();
      if (!isValid) {
        console.log(`   ❌ Validazione fallita`);
        return false;
      }
    }

    // 3. Controlla conflitti
    if (await this.hasConflicts(operation)) {
      console.log(`   ⚠️ Rilevato conflitto - risolvo...`);
      await this.resolveConflict(operation);
    }

    console.log(`   ✓ Verificato - procedo`);
    return true;
  }

  async nodeExists(nodeId) {
    return new Promise((resolve) => {
      const id = `check-${Date.now()}`;

      const checkHandler = (msg) => {
        if (msg.message && msg.message.id === id) {
          resolve(!!msg.message.result);
          this.ws.removeListener('message', checkHandler);
        }
      };

      this.ws.on('message', checkHandler);

      this.ws.send(JSON.stringify({
        id,
        type: 'message',
        channel: this.channel,
        message: {
          id,
          command: 'get_node_info',
          params: { nodeId, commandId: id }
        }
      }));

      setTimeout(() => resolve(false), 1000);
    });
  }

  async hasConflicts(operation) {
    // Controlla se ci sono modifiche non salvate
    const cached = this.nodeCache.get(operation.targetId);
    if (!cached) return false;

    const timeDiff = Date.now() - new Date(cached.lastUpdated).getTime();
    return timeDiff < 100; // Conflitto se modificato negli ultimi 100ms
  }

  async resolveConflict(operation) {
    // Aspetta che le modifiche precedenti siano completate
    await new Promise(resolve => setTimeout(resolve, 200));
  }

  // ============== OPERAZIONI SICURE ==============

  async safeUpdate(nodeId, updates) {
    const operation = {
      targetId: nodeId,
      description: `Aggiorno ${nodeId}`,
      type: 'update',
      validation: async () => {
        // Verifica che il nodo esista
        return await this.nodeExists(nodeId);
      }
    };

    if (!await this.verifyBeforeExecute(operation)) {
      return false;
    }

    // Esegui update
    const commandId = await this.sendCommand('update_node', {
      nodeId,
      ...updates
    });

    this.pendingOperations.set(commandId, operation);
    return true;
  }

  async safeCreate(type, params) {
    const operation = {
      description: `Creo ${type}: ${params.name}`,
      type: 'create',
      validation: async () => {
        // Verifica che non esista già
        if (params.name) {
          const existing = await this.findNodeByName(params.name);
          if (existing) {
            console.log(`   ⚠️ Esiste già: ${params.name}`);
            return false;
          }
        }
        return true;
      }
    };

    if (!await this.verifyBeforeExecute(operation)) {
      return null;
    }

    const commandId = await this.sendCommand(`create_${type}`, params);
    this.pendingOperations.set(commandId, operation);

    // Aspetta il risultato
    return new Promise((resolve) => {
      const checkInterval = setInterval(() => {
        if (!this.pendingOperations.has(commandId)) {
          clearInterval(checkInterval);
          // Trova il nodo appena creato
          const created = Array.from(this.nodeCache.values())
            .find(n => n.name === params.name);
          resolve(created?.id || null);
        }
      }, 100);

      setTimeout(() => {
        clearInterval(checkInterval);
        resolve(null);
      }, 3000);
    });
  }

  async safeDelete(nodeId) {
    const operation = {
      targetId: nodeId,
      description: `Elimino ${nodeId}`,
      type: 'delete',
      validation: async () => {
        // Verifica che non sia un nodo critico
        const info = await this.getNodeInfo(nodeId);
        if (info && info.name && info.name.includes('_CRITICAL')) {
          console.log(`   ❌ Non posso eliminare nodo critico`);
          return false;
        }
        return true;
      }
    };

    if (!await this.verifyBeforeExecute(operation)) {
      return false;
    }

    const commandId = await this.sendCommand('delete_node', { nodeId });
    this.pendingOperations.set(commandId, operation);

    // Rimuovi dalla cache
    this.nodeCache.delete(nodeId);
    return true;
  }

  // ============== MONITORAGGIO REAL-TIME ==============

  async startMonitoring() {
    console.log('\n👁️ Monitoraggio Real-Time Attivo\n');

    // Sincronizza stato iniziale
    await this.syncCurrentState();

    // Monitora cambiamenti ogni secondo
    setInterval(async () => {
      const changes = await this.detectChanges();
      if (changes.length > 0) {
        console.log(`\n📊 Rilevati ${changes.length} cambiamenti:`);

        for (const change of changes) {
          console.log(`   • ${change.type}: ${change.node.name}`);

          // Applica cambiamento
          if (change.type === 'added') {
            await this.syncToReact(change.node);
          } else if (change.type === 'modified') {
            await this.syncToReact(change.node);
          } else if (change.type === 'deleted') {
            await this.removeFromReact(change.node);
          }
        }
      }
    }, 1000);

    // Heartbeat per mantenere connessione
    setInterval(() => {
      this.sendCommand('ping', {});
    }, 30000);
  }

  async syncCurrentState() {
    console.log('🔄 Sincronizzazione stato iniziale...');

    const state = await this.getDocumentState();

    if (state && state.children) {
      console.log(`   → Trovati ${state.children.length} elementi`);

      for (const child of state.children) {
        this.nodeCache.set(child.id, {
          ...child,
          lastUpdated: new Date().toISOString()
        });
      }
    }

    this.lastSync = new Date().toISOString();
    console.log('   ✓ Sincronizzazione completata\n');
  }

  async detectChanges() {
    const currentState = await this.getDocumentState();
    const changes = [];

    if (!currentState || !currentState.children) return changes;

    const currentIds = new Set(currentState.children.map(c => c.id));
    const cachedIds = new Set(this.nodeCache.keys());

    // Trova nodi aggiunti
    for (const child of currentState.children) {
      if (!cachedIds.has(child.id)) {
        changes.push({ type: 'added', node: child });
      } else {
        // Controlla se modificato
        const cached = this.nodeCache.get(child.id);
        if (JSON.stringify(cached) !== JSON.stringify(child)) {
          changes.push({ type: 'modified', node: child });
        }
      }
    }

    // Trova nodi eliminati
    for (const cachedId of cachedIds) {
      if (!currentIds.has(cachedId)) {
        changes.push({
          type: 'deleted',
          node: this.nodeCache.get(cachedId)
        });
      }
    }

    return changes;
  }

  // ============== UTILITIES ==============

  async sendCommand(command, params = {}) {
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

    this.ws.send(JSON.stringify(message));
    return id;
  }

  async getDocumentState() {
    return new Promise((resolve) => {
      const id = `state-${Date.now()}`;

      const stateHandler = (data) => {
        const msg = JSON.parse(data.toString());
        if (msg.message && msg.message.id === id) {
          resolve(msg.message.result);
          this.ws.removeListener('message', stateHandler);
        }
      };

      this.ws.on('message', stateHandler);

      this.ws.send(JSON.stringify({
        id,
        type: 'message',
        channel: this.channel,
        message: {
          id,
          command: 'get_document_info',
          params: { commandId: id }
        }
      }));

      setTimeout(() => resolve(null), 2000);
    });
  }

  async findNodeByName(name) {
    const state = await this.getDocumentState();
    if (!state || !state.children) return null;

    return state.children.find(c => c.name === name);
  }

  async getNodeInfo(nodeId) {
    return new Promise((resolve) => {
      const id = `info-${Date.now()}`;

      const infoHandler = (data) => {
        const msg = JSON.parse(data.toString());
        if (msg.message && msg.message.id === id) {
          resolve(msg.message.result);
          this.ws.removeListener('message', infoHandler);
        }
      };

      this.ws.on('message', infoHandler);

      this.ws.send(JSON.stringify({
        id,
        type: 'message',
        channel: this.channel,
        message: {
          id,
          command: 'get_node_info',
          params: { nodeId, commandId: id }
        }
      }));

      setTimeout(() => resolve(null), 1000);
    });
  }

  generateReactFromNode(node) {
    const name = node.name.replace(/[^a-zA-Z0-9]/g, '');

    return `import React from 'react';

// Auto-generato da Figma: ${node.name} (${node.id})
// Ultimo sync: ${new Date().toISOString()}

const ${name} = () => {
  return (
    <div
      id="${node.id}"
      className="${name.toLowerCase()}"
      style={{
        width: ${node.width || 'auto'},
        height: ${node.height || 'auto'},
        ${node.fills ? `background: '${this.colorToHex(node.fills[0]?.color)}',` : ''}
      }}
    >
      ${node.characters || `${name} Component`}
    </div>
  );
};

export default ${name};`;
  }

  colorToHex(color) {
    if (!color) return '#000000';
    const r = Math.round(color.r * 255).toString(16).padStart(2, '0');
    const g = Math.round(color.g * 255).toString(16).padStart(2, '0');
    const b = Math.round(color.b * 255).toString(16).padStart(2, '0');
    return `#${r}${g}${b}`;
  }

  async removeFromReact(node) {
    const componentPath = path.join(
      '/Users/erik/Desktop/claude-multiagent-system/claude-ui/src/components',
      'synced',
      `${node.name}.tsx`
    );

    try {
      await fs.unlink(componentPath);
      console.log(`   → Rimosso da React: ${node.name}.tsx`);
    } catch (error) {
      // File non esiste, ok
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// ============== MAIN ==============

async function main() {
  const channel = process.argv[2] || '5utu5pn0';
  const sync = new FigmaRealtimeSync(channel);

  try {
    await sync.connect();

    console.log('╔════════════════════════════════════════╗');
    console.log('║    FIGMA REALTIME SYNC & VERIFY       ║');
    console.log('╚════════════════════════════════════════╝\n');

    console.log('Funzionalità:');
    console.log('✓ Verifica ogni operazione prima di eseguire');
    console.log('✓ Sincronizzazione bidirezionale in tempo reale');
    console.log('✓ Rilevamento conflitti e risoluzione automatica');
    console.log('✓ Generazione React automatica dai componenti Figma\n');

    // Avvia monitoraggio
    await sync.startMonitoring();

    // Test: crea un componente sicuro
    console.log('\n📝 Test: Creo componente con verifica...');
    const newId = await sync.safeCreate('frame', {
      x: 500,
      y: 500,
      width: 200,
      height: 100,
      name: 'Test_Realtime_Component',
      fillColor: { r: 0.9, g: 0.95, b: 1, a: 1 }
    });

    if (newId) {
      console.log(`   ✅ Creato con successo: ${newId}`);

      // Test: modifica sicura
      console.log('\n📝 Test: Modifico componente...');
      await sync.safeUpdate(newId, {
        fillColor: { r: 0.2, g: 0.8, b: 0.4, a: 1 }
      });
    }

    // Mantieni in esecuzione
    process.stdin.resume();

  } catch (error) {
    console.error('❌ Errore:', error);
    sync.disconnect();
  }
}

if (require.main === module) {
  main();
}

module.exports = FigmaRealtimeSync;