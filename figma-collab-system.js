#!/usr/bin/env node

/**
 * FIGMA COLLABORATION SYSTEM
 * Sistema completo di collaborazione Claude + Human
 *
 * WORKFLOW:
 * 1. Tu chiedi modifica → Io la disegno in Figma
 * 2. Tu la vedi e approvi → Io genero il codice
 * 3. Implementiamo nel sistema React
 * 4. Tutto sincronizzato e versionato
 */

const WebSocket = require('ws');
const fs = require('fs').promises;
const path = require('path');
const { promisify } = require('util');
const exec = promisify(require('child_process').exec);

class FigmaCollaborationSystem {
  constructor(channel) {
    this.channel = channel;
    this.ws = null;
    this.currentProject = '/Users/erik/Desktop/claude-multiagent-system/claude-ui';
    this.proposals = new Map(); // Traccia proposte in attesa di approvazione
    this.componentRegistry = new Map(); // Mappa componenti Figma → React
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket('ws://localhost:3055');

      this.ws.on('open', () => {
        console.log('🚀 Collaboration System Connected!');
        this.ws.send(JSON.stringify({ type: 'join', channel: this.channel }));
        setTimeout(resolve, 500);
      });

      this.ws.on('message', (data) => {
        // Handle messages if needed
      });
      this.ws.on('error', reject);
    });
  }

  // ============== REPLICO IL FRONTEND ATTUALE IN FIGMA ==============
  async replicateCurrentFrontend() {
    console.log('📦 Analyzing current frontend...');

    // Leggo tutti i componenti React esistenti
    const componentsPath = path.join(this.currentProject, 'src/components');
    const files = await fs.readdir(componentsPath, { recursive: true });

    console.log(`Found ${files.length} components to replicate in Figma\n`);

    // Per ogni componente React, creo la versione Figma
    for (const file of files) {
      if (file.endsWith('.tsx') || file.endsWith('.jsx')) {
        await this.componentToFigma(path.join(componentsPath, file));
      }
    }

    console.log('✅ Frontend replicated in Figma!');
  }

  async componentToFigma(filePath) {
    const content = await fs.readFile(filePath, 'utf-8');
    const componentName = path.basename(filePath, path.extname(filePath));

    console.log(`→ Replicating ${componentName} to Figma...`);

    // Analizzo il componente React
    const analysis = this.analyzeReactComponent(content);

    // Creo la struttura in Figma
    const figmaNode = await this.createFigmaFromAnalysis(componentName, analysis);

    // Registro il mapping
    this.componentRegistry.set(componentName, {
      reactPath: filePath,
      figmaNodeId: figmaNode,
      lastSync: new Date()
    });

    return figmaNode;
  }

  analyzeReactComponent(content) {
    const analysis = {
      hasState: content.includes('useState'),
      hasForm: content.includes('useForm') || content.includes('<form'),
      tailwindClasses: this.extractTailwindClasses(content),
      components: this.extractChildComponents(content),
      props: this.extractProps(content),
      text: this.extractTextContent(content)
    };

    // Determino il tipo di componente
    if (content.includes('MCPDashboard')) {
      analysis.type = 'dashboard';
      analysis.layout = 'grid';
    } else if (content.includes('Terminal')) {
      analysis.type = 'terminal';
      analysis.layout = 'vertical';
    } else if (content.includes('Button')) {
      analysis.type = 'button';
    } else if (content.includes('Card')) {
      analysis.type = 'card';
    } else if (content.includes('Input')) {
      analysis.type = 'input';
    } else {
      analysis.type = 'container';
      analysis.layout = 'flex';
    }

    return analysis;
  }

  async createFigmaFromAnalysis(name, analysis) {
    let x = 100 + (this.componentRegistry.size * 420); // Spazio componenti
    let y = 1000; // Sezione "Current Frontend"

    // Creo frame principale
    const mainFrame = await this.sendCommand('create_frame', {
      x, y,
      width: 400,
      height: analysis.type === 'dashboard' ? 600 : 300,
      name: `Current_${name}`,
      fillColor: { r: 1, g: 1, b: 1, a: 1 }
    });

    // Aggiungo label
    await this.sendCommand('create_text', {
      x: 0,
      y: -30,
      text: `📦 ${name} (Current)`,
      fontSize: 14,
      fontWeight: 600,
      fontColor: { r: 0.4, g: 0.4, b: 0.4, a: 1 },
      parentId: mainFrame
    });

    // Replico struttura basata sul tipo
    switch (analysis.type) {
      case 'dashboard':
        await this.createDashboardStructure(mainFrame, analysis);
        break;
      case 'terminal':
        await this.createTerminalStructure(mainFrame, analysis);
        break;
      case 'button':
        await this.createButtonStructure(mainFrame, analysis);
        break;
      case 'card':
        await this.createCardStructure(mainFrame, analysis);
        break;
      default:
        await this.createGenericStructure(mainFrame, analysis);
    }

    return mainFrame;
  }

  // ============== PROPONGO MODIFICHE IN FIGMA ==============
  async proposeModification(request) {
    console.log('\n🎨 Creating modification proposal in Figma...');
    console.log(`Request: "${request}"\n`);

    // Interpreto la richiesta
    const intent = this.interpretRequest(request);

    // Creo proposta visuale in Figma
    const proposalId = await this.createVisualProposal(intent);

    // Salvo proposta per approvazione
    this.proposals.set(proposalId, {
      request,
      intent,
      status: 'pending',
      createdAt: new Date()
    });

    console.log(`\n✅ Proposal created! ID: ${proposalId}`);
    console.log('👀 Check Figma to see the proposed changes');
    console.log('Type "approve" to implement or "reject" to discard\n');

    return proposalId;
  }

  interpretRequest(request) {
    const req = request.toLowerCase();

    // Riconosco pattern comuni
    if (req.includes('dark mode')) {
      return {
        type: 'theme_change',
        theme: 'dark',
        affects: 'all_components'
      };
    }

    if (req.includes('add') && req.includes('button')) {
      return {
        type: 'add_element',
        element: 'button',
        context: this.extractContext(req)
      };
    }

    if (req.includes('change color')) {
      return {
        type: 'style_change',
        property: 'color',
        target: this.extractTarget(req),
        value: this.extractColor(req)
      };
    }

    if (req.includes('mobile')) {
      return {
        type: 'responsive',
        breakpoint: 'mobile',
        width: 375
      };
    }

    if (req.includes('sidebar')) {
      return {
        type: 'layout_change',
        component: 'sidebar',
        modification: this.extractModification(req)
      };
    }

    return {
      type: 'generic',
      description: request
    };
  }

  async createVisualProposal(intent) {
    const proposalId = `proposal_${Date.now()}`;
    let x = 600;
    let y = 1400; // Sezione proposte

    // Frame contenitore proposta
    const proposalFrame = await this.sendCommand('create_frame', {
      x, y,
      width: 800,
      height: 400,
      name: proposalId,
      fillColor: { r: 0.98, g: 1, b: 0.98, a: 1 }
    });

    // Header proposta
    await this.sendCommand('create_frame', {
      x: 0,
      y: 0,
      width: 800,
      height: 60,
      name: 'Proposal_Header',
      fillColor: { r: 0.95, g: 0.97, b: 1, a: 1 },
      parentId: proposalFrame
    });

    // Titolo
    await this.sendCommand('create_text', {
      x: 20,
      y: 20,
      text: `💡 PROPOSAL: ${intent.type.replace('_', ' ').toUpperCase()}`,
      fontSize: 18,
      fontWeight: 700,
      parentId: proposalFrame
    });

    // Status badge
    await this.sendCommand('create_frame', {
      x: 700,
      y: 15,
      width: 80,
      height: 30,
      name: 'Status_Badge',
      fillColor: { r: 1, g: 0.8, b: 0.2, a: 1 },
      parentId: proposalFrame
    });

    await this.sendCommand('create_text', {
      x: 15,
      y: 8,
      text: 'PENDING',
      fontSize: 12,
      fontWeight: 600,
      fontColor: { r: 0.6, g: 0.4, b: 0, a: 1 },
      parentId: proposalFrame
    });

    // Contenuto proposta basato su intent
    await this.createProposalContent(proposalFrame, intent);

    // Before/After comparison
    await this.createComparison(proposalFrame, intent);

    return proposalId;
  }

  async createProposalContent(parent, intent) {
    switch (intent.type) {
      case 'theme_change':
        await this.proposeDarkMode(parent);
        break;

      case 'add_element':
        await this.proposeNewElement(parent, intent);
        break;

      case 'layout_change':
        await this.proposeLayoutChange(parent, intent);
        break;

      case 'style_change':
        await this.proposeStyleChange(parent, intent);
        break;

      default:
        await this.proposeGeneric(parent, intent);
    }
  }

  async proposeDarkMode(parent) {
    // Esempio componenti in dark mode
    const components = ['Sidebar', 'Header', 'Card', 'Button'];
    let xOffset = 20;

    for (const comp of components) {
      const frame = await this.sendCommand('create_frame', {
        x: xOffset,
        y: 80,
        width: 180,
        height: 100,
        name: `${comp}_Dark`,
        fillColor: { r: 0.1, g: 0.1, b: 0.12, a: 1 },
        parentId: parent
      });

      await this.sendCommand('create_text', {
        x: 10,
        y: 10,
        text: comp,
        fontSize: 14,
        fontColor: { r: 0.9, g: 0.9, b: 0.9, a: 1 },
        parentId: frame
      });

      xOffset += 190;
    }
  }

  // ============== APPROVO E IMPLEMENTO ==============
  async approveProposal(proposalId) {
    const proposal = this.proposals.get(proposalId);

    if (!proposal) {
      console.log('❌ Proposal not found');
      return;
    }

    console.log('✅ Proposal approved! Implementing...');
    proposal.status = 'approved';

    // Genero codice React dalla proposta Figma
    const code = await this.generateCodeFromProposal(proposalId);

    // Implemento nel progetto
    await this.implementInProject(code);

    // Aggiorno visual feedback in Figma
    await this.updateProposalStatus(proposalId, 'APPROVED', { r: 0.2, g: 0.8, b: 0.3 });

    // Git commit (opzionale)
    await this.commitChanges(proposal.request);

    console.log('🎉 Changes implemented successfully!');
  }

  async generateCodeFromProposal(proposalId) {
    // Leggo la struttura Figma della proposta
    const proposalNode = await this.sendCommand('get_node_info', {
      nodeId: proposalId
    });

    // Genero componenti React
    const components = [];

    for (const child of proposalNode.children || []) {
      const component = this.nodeToReactComponent(child);
      components.push(component);
    }

    return components;
  }

  async implementInProject(components) {
    for (const comp of components) {
      const filePath = path.join(
        this.currentProject,
        'src/components/generated',
        `${comp.name}.tsx`
      );

      await fs.mkdir(path.dirname(filePath), { recursive: true });
      await fs.writeFile(filePath, comp.code);

      console.log(`📝 Created: ${comp.name}.tsx`);
    }

    // Aggiorno index per export
    await this.updateComponentIndex(components);
  }

  async commitChanges(message) {
    try {
      await exec(`cd ${this.currentProject} && git add -A`);
      await exec(`cd ${this.currentProject} && git commit -m "🎨 Figma: ${message}"`);
      console.log('📦 Changes committed to git');
    } catch (error) {
      console.log('⚠️  Git commit skipped (no git or no changes)');
    }
  }

  // ============== SYNC BIDIREZIONALE ==============
  async syncFigmaToReact() {
    console.log('🔄 Syncing Figma → React...');

    for (const [name, mapping] of this.componentRegistry) {
      const figmaNode = await this.sendCommand('get_node_info', {
        nodeId: mapping.figmaNodeId
      });

      const reactCode = this.nodeToReactComponent(figmaNode);
      await fs.writeFile(mapping.reactPath, reactCode.code);

      console.log(`✅ Synced: ${name}`);
    }
  }

  async syncReactToFigma() {
    console.log('🔄 Syncing React → Figma...');

    for (const [name, mapping] of this.componentRegistry) {
      const content = await fs.readFile(mapping.reactPath, 'utf-8');
      const analysis = this.analyzeReactComponent(content);

      // Aggiorno Figma node
      await this.updateFigmaFromAnalysis(mapping.figmaNodeId, analysis);

      console.log(`✅ Synced: ${name}`);
    }
  }

  // ============== INTERACTIVE WORKFLOW ==============
  async startInteractiveSession() {
    console.log('\n╔══════════════════════════════════════════╗');
    console.log('║   🤝 FIGMA COLLABORATION MODE ACTIVE    ║');
    console.log('╚══════════════════════════════════════════╝\n');

    console.log('Commands:');
    console.log('  • "propose [change]" - I create visual proposal in Figma');
    console.log('  • "approve [id]" - Implement approved proposal');
    console.log('  • "sync" - Sync all components');
    console.log('  • "replicate" - Replicate current frontend to Figma');
    console.log('  • "watch" - Watch for changes\n');

    // Setup command handling
    const readline = require('readline');
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    rl.on('line', async (input) => {
      const [cmd, ...args] = input.trim().split(' ');

      switch (cmd) {
        case 'propose':
          await this.proposeModification(args.join(' '));
          break;

        case 'approve':
          await this.approveProposal(args[0]);
          break;

        case 'reject':
          await this.rejectProposal(args[0]);
          break;

        case 'sync':
          await this.syncFigmaToReact();
          await this.syncReactToFigma();
          break;

        case 'replicate':
          await this.replicateCurrentFrontend();
          break;

        case 'watch':
          await this.startWatchMode();
          break;

        case 'help':
          this.showHelp();
          break;

        default:
          console.log('Unknown command. Type "help" for available commands.');
      }
    });
  }

  // ============== UTILITIES ==============
  nodeToReactComponent(node) {
    const componentName = this.toPascalCase(node.name);
    const tailwindClasses = this.nodeToTailwind(node);

    const code = `import React from 'react';

interface ${componentName}Props {
  className?: string;
}

export const ${componentName}: React.FC<${componentName}Props> = ({ className }) => {
  return (
    <div className={\`${tailwindClasses} \${className || ''}\`}>
      ${this.generateChildrenJSX(node.children)}
    </div>
  );
};

export default ${componentName};`;

    return {
      name: componentName,
      code,
      tailwind: tailwindClasses
    };
  }

  nodeToTailwind(node) {
    const classes = [];

    // Background
    if (node.fills?.[0]?.color) {
      const { r, g, b } = node.fills[0].color;
      if (r < 0.2 && g < 0.2 && b < 0.2) {
        classes.push('bg-gray-900');
      } else if (r > 0.9 && g > 0.9 && b > 0.9) {
        classes.push('bg-white');
      } else {
        classes.push(`bg-[rgb(${Math.round(r*255)},${Math.round(g*255)},${Math.round(b*255)})]`);
      }
    }

    // Size
    if (node.width) classes.push(`w-[${Math.round(node.width)}px]`);
    if (node.height) classes.push(`h-[${Math.round(node.height)}px]`);

    // Layout
    if (node.layoutMode === 'HORIZONTAL') classes.push('flex flex-row');
    if (node.layoutMode === 'VERTICAL') classes.push('flex flex-col');

    // Border radius
    if (node.cornerRadius) {
      if (node.cornerRadius === 4) classes.push('rounded');
      else if (node.cornerRadius === 8) classes.push('rounded-lg');
      else classes.push(`rounded-[${node.cornerRadius}px]`);
    }

    // Padding
    if (node.paddingLeft) classes.push(`pl-${Math.round(node.paddingLeft / 4)}`);
    if (node.paddingRight) classes.push(`pr-${Math.round(node.paddingRight / 4)}`);
    if (node.paddingTop) classes.push(`pt-${Math.round(node.paddingTop / 4)}`);
    if (node.paddingBottom) classes.push(`pb-${Math.round(node.paddingBottom / 4)}`);

    return classes.join(' ');
  }

  generateChildrenJSX(children) {
    if (!children || children.length === 0) return '';

    return children.map(child => {
      if (child.type === 'TEXT') {
        return `<span>${child.characters || ''}</span>`;
      }
      return `<div className="${this.nodeToTailwind(child)}">${this.generateChildrenJSX(child.children)}</div>`;
    }).join('\n      ');
  }

  async sendCommand(command, params = {}) {
    return new Promise((resolve) => {
      const id = `cmd-${Date.now()}`;
      const message = {
        id,
        type: 'message',
        channel: this.channel,
        message: { id, command, params: { ...params, commandId: id } }
      };

      this.ws.send(JSON.stringify(message));
      setTimeout(() => resolve(id), 200);
    });
  }

  extractTailwindClasses(content) {
    const matches = content.match(/className=["'`]([^"'`]+)["'`]/g) || [];
    return matches.map(m => m.replace(/className=["'`]|["'`]/g, ''));
  }

  extractChildComponents(content) {
    const matches = content.match(/<([A-Z][a-zA-Z]*)/g) || [];
    return [...new Set(matches.map(m => m.substring(1)))];
  }

  extractProps(content) {
    const match = content.match(/interface.*Props\s*{([^}]*)}/);
    if (match) {
      return match[1].trim().split('\n').map(line => line.trim()).filter(Boolean);
    }
    return [];
  }

  extractTextContent(content) {
    const matches = content.match(/>([^<>]+)</g) || [];
    return matches.map(m => m.slice(1, -1)).filter(text => text.trim());
  }

  toPascalCase(str) {
    return str.replace(/(?:^\w|[A-Z]|\b\w)/g, w => w.toUpperCase()).replace(/\s+/g, '');
  }
}

// ============== START COLLABORATION ==============
if (require.main === module) {
  const channel = process.argv[2] || '5utu5pn0';

  async function start() {
    const collab = new FigmaCollaborationSystem(channel);

    try {
      await collab.connect();
      await collab.startInteractiveSession();

    } catch (error) {
      console.error('Error:', error);
    }
  }

  start();
}

module.exports = FigmaCollaborationSystem;