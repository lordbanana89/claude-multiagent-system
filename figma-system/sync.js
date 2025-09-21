#!/usr/bin/env node

/**
 * FIGMA SYNC MANAGER
 * Sincronizza Figma con React in tempo reale
 */

const WebSocket = require('ws');
const fs = require('fs').promises;
const path = require('path');

class FigmaSyncManager {
  constructor(channel) {
    this.channel = channel;
    this.ws = null;
    this.syncedComponents = new Map();
    this.reactPath = '/Users/erik/Desktop/claude-multiagent-system/claude-ui/src/components/figma-synced';
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket('ws://localhost:3055');

      this.ws.on('open', () => {
        console.log('[SYNC] Connesso');
        this.ws.send(JSON.stringify({
          type: 'join',
          channel: this.channel
        }));
        setTimeout(resolve, 500);
      });

      this.ws.on('error', reject);
    });
  }

  async startSyncing() {
    console.log('[SYNC] Manager attivo');

    // Crea directory se non esiste
    await fs.mkdir(this.reactPath, { recursive: true });

    process.stdin.on('data', async (data) => {
      const cmd = data.toString().trim();

      if (cmd.startsWith('SYNC:')) {
        const parts = cmd.split(':');
        const operation = parts[1];
        const data = parts.slice(2).join(':');

        await this.syncOperation(operation, data);
      } else if (cmd === 'STATUS') {
        this.printStatus();
      } else if (cmd === 'EXPORT') {
        await this.exportAll();
      }
    });

    // Sync periodico
    setInterval(async () => {
      await this.syncAll();
    }, 5000);
  }

  async syncOperation(operation, data) {
    console.log(`[SYNC] Sincronizzando: ${operation}`);

    switch (operation) {
      case 'CREATE':
      case 'MODIFY':
        await this.syncToReact(data);
        break;
      case 'DELETE':
        await this.removeFromReact(data);
        break;
    }
  }

  async syncToReact(nodeData) {
    try {
      const node = JSON.parse(nodeData);

      if (!node.id || !node.name) return;

      // Genera componente React
      const componentCode = this.generateReactComponent(node);

      // Salva file
      const fileName = `${node.name.replace(/[^a-zA-Z0-9]/g, '')}.tsx`;
      const filePath = path.join(this.reactPath, fileName);

      await fs.writeFile(filePath, componentCode);

      this.syncedComponents.set(node.id, {
        fileName,
        lastSync: Date.now()
      });

      console.log(`SYNCED:${node.id}:${fileName}`);
    } catch (e) {
      console.error('[SYNC] Errore:', e.message);
    }
  }

  generateReactComponent(node) {
    const componentName = this.toPascalCase(node.name);

    return `import React from 'react';
import { cn } from '@/lib/utils';

/**
 * Auto-generated from Figma
 * ID: ${node.id}
 * Last sync: ${new Date().toISOString()}
 */

interface ${componentName}Props {
  className?: string;
  children?: React.ReactNode;
}

const ${componentName}: React.FC<${componentName}Props> = ({ className, children }) => {
  return (
    <div
      className={cn(
        "${this.generateTailwindClasses(node)}",
        className
      )}
      data-figma-id="${node.id}"
    >
      ${node.characters || children || `{children}`}
    </div>
  );
};

export default ${componentName};

// Figma metadata
export const figmaMetadata = ${JSON.stringify({
  id: node.id,
  name: node.name,
  type: node.type,
  width: node.width,
  height: node.height,
  x: node.x,
  y: node.y
}, null, 2)};`;
  }

  generateTailwindClasses(node) {
    const classes = [];

    // Dimensioni
    if (node.width) {
      if (node.width === 100) classes.push('w-full');
      else if (node.width < 50) classes.push('w-12');
      else if (node.width < 100) classes.push('w-24');
      else if (node.width < 200) classes.push('w-48');
      else if (node.width < 400) classes.push('w-96');
      else classes.push(`w-[${node.width}px]`);
    }

    if (node.height) {
      if (node.height < 50) classes.push('h-12');
      else if (node.height < 100) classes.push('h-24');
      else if (node.height < 200) classes.push('h-48');
      else classes.push(`h-[${node.height}px]`);
    }

    // Layout
    if (node.layoutMode === 'HORIZONTAL') classes.push('flex flex-row');
    else if (node.layoutMode === 'VERTICAL') classes.push('flex flex-col');

    // Colori di sfondo
    if (node.fills && node.fills[0]) {
      const fill = node.fills[0];
      if (fill.color) {
        const { r, g, b } = fill.color;
        if (r > 0.9 && g > 0.9 && b > 0.9) classes.push('bg-white');
        else if (r < 0.1 && g < 0.1 && b < 0.1) classes.push('bg-black');
        else if (r > 0.9 && g < 0.3 && b < 0.3) classes.push('bg-red-500');
        else if (r < 0.3 && g > 0.7 && b < 0.3) classes.push('bg-green-500');
        else if (r < 0.3 && g < 0.3 && b > 0.7) classes.push('bg-blue-500');
        else classes.push('bg-gray-100');
      }
    }

    // Bordi
    if (node.cornerRadius) {
      if (node.cornerRadius <= 4) classes.push('rounded');
      else if (node.cornerRadius <= 8) classes.push('rounded-md');
      else if (node.cornerRadius <= 12) classes.push('rounded-lg');
      else if (node.cornerRadius <= 16) classes.push('rounded-xl');
      else classes.push('rounded-2xl');
    }

    // Padding
    if (node.paddingLeft || node.paddingTop) {
      classes.push('p-4');
    }

    return classes.join(' ');
  }

  async removeFromReact(nodeId) {
    const component = this.syncedComponents.get(nodeId);

    if (component) {
      const filePath = path.join(this.reactPath, component.fileName);

      try {
        await fs.unlink(filePath);
        this.syncedComponents.delete(nodeId);
        console.log(`[SYNC] Rimosso: ${component.fileName}`);
      } catch (e) {
        // File già rimosso
      }
    }
  }

  async syncAll() {
    // Ottieni stato attuale da Figma
    const doc = await this.sendCommand('get_document_info');

    if (!doc || !doc.children) return;

    // Sincronizza tutti i componenti
    for (const child of doc.children) {
      if (child.name && !child.name.startsWith('_')) {
        // Salta elementi privati
        await this.syncToReact(JSON.stringify(child));
      }
    }
  }

  async exportAll() {
    console.log('[SYNC] Esportazione completa...');

    // Crea index file
    const indexContent = Array.from(this.syncedComponents.values())
      .map(comp => {
        const name = comp.fileName.replace('.tsx', '');
        return `export { default as ${name} } from './${name}';`;
      })
      .join('\n');

    await fs.writeFile(
      path.join(this.reactPath, 'index.ts'),
      indexContent
    );

    console.log(`[SYNC] Esportati ${this.syncedComponents.size} componenti`);
  }

  async sendCommand(command, params = {}) {
    return new Promise((resolve) => {
      const id = `sync-${Date.now()}`;

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

  toPascalCase(str) {
    return str
      .replace(/[^a-zA-Z0-9]/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join('');
  }

  printStatus() {
    console.log('[SYNC] Status:');
    console.log(`  Componenti sincronizzati: ${this.syncedComponents.size}`);
    console.log(`  Path React: ${this.reactPath}`);
    console.log(`  Canale: ${this.channel}`);
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
  const sync = new FigmaSyncManager(channel);

  sync.connect()
    .then(() => sync.startSyncing())
    .catch(console.error);

  process.on('SIGINT', () => {
    sync.disconnect();
    process.exit(0);
  });
}

module.exports = FigmaSyncManager;