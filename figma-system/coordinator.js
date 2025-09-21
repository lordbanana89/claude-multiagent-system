#!/usr/bin/env node

/**
 * FIGMA SYSTEM COORDINATOR
 * Coordina tutti gli script del sistema
 */

const EventEmitter = require('events');
const { spawn } = require('child_process');
const path = require('path');

class FigmaSystemCoordinator extends EventEmitter {
  constructor() {
    super();
    this.scripts = new Map();
    this.channel = process.env.FIGMA_CHANNEL || '5utu5pn0';
    this.state = {
      monitoring: false,
      creating: false,
      syncing: false,
      verifying: false
    };
  }

  async start() {
    console.log('╔════════════════════════════════════════╗');
    console.log('║   FIGMA SYSTEM COORDINATOR ACTIVE     ║');
    console.log('╚════════════════════════════════════════╝\n');

    // Avvia gli script in ordine
    await this.startMonitor();
    await this.startVerifier();
    await this.startCreator();
    await this.startSync();

    console.log('\n✅ Sistema completo attivo\n');
    this.setupCommunication();
  }

  async startMonitor() {
    console.log('🔍 Avvio Monitor...');
    const monitor = spawn('node', [
      path.join(__dirname, 'monitor.js'),
      this.channel
    ], {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, FIGMA_CHANNEL: this.channel }
    });

    monitor.stdout.on('data', (data) => {
      const msg = data.toString();
      if (msg.includes('CHANGE:')) {
        this.emit('figma-change', msg);
      }
    });

    this.scripts.set('monitor', monitor);
    this.state.monitoring = true;
  }

  async startVerifier() {
    console.log('✓ Avvio Verifier...');
    const verifier = spawn('node', [
      path.join(__dirname, 'verifier.js'),
      this.channel
    ], {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, FIGMA_CHANNEL: this.channel }
    });

    verifier.stdout.on('data', (data) => {
      const msg = data.toString();
      if (msg.includes('VERIFIED:')) {
        this.emit('verified', msg);
      }
    });

    this.scripts.set('verifier', verifier);
    this.state.verifying = true;
  }

  async startCreator() {
    console.log('🎨 Avvio Creator...');
    const creator = spawn('node', [
      path.join(__dirname, 'creator.js'),
      this.channel
    ], {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, FIGMA_CHANNEL: this.channel }
    });

    creator.stdout.on('data', (data) => {
      const msg = data.toString();
      if (msg.includes('CREATED:')) {
        this.emit('created', msg);
      }
    });

    this.scripts.set('creator', creator);
    this.state.creating = true;
  }

  async startSync() {
    console.log('🔄 Avvio Sync Manager...');
    const sync = spawn('node', [
      path.join(__dirname, 'sync.js'),
      this.channel
    ], {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, FIGMA_CHANNEL: this.channel }
    });

    sync.stdout.on('data', (data) => {
      const msg = data.toString();
      if (msg.includes('SYNCED:')) {
        this.emit('synced', msg);
      }
    });

    this.scripts.set('sync', sync);
    this.state.syncing = true;
  }

  setupCommunication() {
    // Quando monitor rileva un cambiamento
    this.on('figma-change', (change) => {
      console.log(`\n🔄 Cambiamento rilevato: ${change}`);

      // Invia al verifier
      const verifier = this.scripts.get('verifier');
      if (verifier) {
        verifier.stdin.write(`VERIFY:${change}\n`);
      }
    });

    // Quando verifier conferma
    this.on('verified', (verification) => {
      console.log(`✅ Verificato: ${verification}`);

      // Invia al sync
      const sync = this.scripts.get('sync');
      if (sync) {
        sync.stdin.write(`SYNC:${verification}\n`);
      }
    });

    // Quando creator crea qualcosa
    this.on('created', (creation) => {
      console.log(`🎨 Creato: ${creation}`);

      // Invia al monitor per tracking
      const monitor = this.scripts.get('monitor');
      if (monitor) {
        monitor.stdin.write(`TRACK:${creation}\n`);
      }
    });

    // Quando sync completa
    this.on('synced', (syncResult) => {
      console.log(`🔄 Sincronizzato: ${syncResult}`);
    });
  }

  sendCommand(scriptName, command) {
    const script = this.scripts.get(scriptName);
    if (script && script.stdin) {
      script.stdin.write(`${command}\n`);
      return true;
    }
    return false;
  }

  async createComponent(type, config) {
    console.log(`\n📝 Richiesta creazione ${type}`);

    // Prima verifica
    this.sendCommand('verifier', `CHECK:${type}:${JSON.stringify(config)}`);

    // Poi crea
    setTimeout(() => {
      this.sendCommand('creator', `CREATE:${type}:${JSON.stringify(config)}`);
    }, 500);
  }

  getStatus() {
    return {
      scripts: Array.from(this.scripts.keys()),
      state: this.state,
      channel: this.channel
    };
  }

  stop() {
    console.log('\n🛑 Arresto sistema...');

    for (const [name, script] of this.scripts) {
      console.log(`   Fermando ${name}...`);
      script.kill();
    }

    this.scripts.clear();
    console.log('✅ Sistema arrestato\n');
  }
}

// Main
if (require.main === module) {
  const coordinator = new FigmaSystemCoordinator();

  coordinator.start().catch(console.error);

  // Gestisci shutdown
  process.on('SIGINT', () => {
    coordinator.stop();
    process.exit(0);
  });

  // API per comandi esterni
  process.stdin.on('data', (data) => {
    const cmd = data.toString().trim();

    if (cmd.startsWith('CREATE:')) {
      const [, type, ...args] = cmd.split(':');
      coordinator.createComponent(type, JSON.parse(args.join(':')));
    } else if (cmd === 'STATUS') {
      console.log(JSON.stringify(coordinator.getStatus(), null, 2));
    } else if (cmd === 'STOP') {
      coordinator.stop();
    }
  });
}

module.exports = FigmaSystemCoordinator;