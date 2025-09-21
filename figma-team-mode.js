#!/usr/bin/env node

/**
 * FIGMA TEAM MODE
 * Sistema collaborativo Claude + Human per design frontend
 * Tu disegni → Io vedo → Genero codice → Tu modifichi → Io aggiorno
 */

const WebSocket = require('ws');
const fs = require('fs').promises;
const path = require('path');
const { promisify } = require('util');
const exec = promisify(require('child_process').exec);

class FigmaTeamMode {
  constructor(channel) {
    this.channel = channel;
    this.ws = null;
    this.lastSelection = null;
    this.watchMode = false;
    this.componentMap = new Map();
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket('ws://localhost:3055');

      this.ws.on('open', () => {
        console.log('🤝 Team Mode Activated!');
        this.ws.send(JSON.stringify({ type: 'join', channel: this.channel }));
        setTimeout(resolve, 500);
      });

      this.ws.on('message', this.handleMessage.bind(this));
      this.ws.on('error', reject);
    });
  }

  handleMessage(data) {
    const msg = JSON.parse(data.toString());

    // Se ricevo modifiche da Figma, aggiorno automaticamente il codice
    if (msg.message && msg.message.command === 'node_modified') {
      console.log('📝 Detected change in Figma!');
      this.onFigmaChange(msg.message.result);
    }
  }

  // ============== OSSERVO LE TUE MODIFICHE ==============
  async watchYourChanges() {
    console.log('👀 Watching for your changes in Figma...');
    this.watchMode = true;

    setInterval(async () => {
      if (!this.watchMode) return;

      const selection = await this.getSelection();
      if (selection && selection !== this.lastSelection) {
        console.log('🎯 New selection detected!');
        await this.analyzeYourIntent(selection);
        this.lastSelection = selection;
      }
    }, 2000);
  }

  async analyzeYourIntent(selection) {
    console.log('\n🧠 Analyzing your intent...');

    // Capisco cosa vuoi fare dal nome e tipo di elemento
    const intent = this.detectIntent(selection);

    switch (intent.type) {
      case 'create_component':
        console.log(`→ You want to create a ${intent.component} component`);
        await this.helpYouCreateComponent(selection, intent);
        break;

      case 'modify_style':
        console.log(`→ You're modifying styles`);
        await this.updateReactStyles(selection);
        break;

      case 'add_interaction':
        console.log(`→ You're adding interactions`);
        await this.addReactInteraction(selection);
        break;

      case 'create_page':
        console.log(`→ You're creating a new page`);
        await this.scaffoldNewPage(selection);
        break;
    }
  }

  detectIntent(node) {
    const name = node.name?.toLowerCase() || '';

    // Riconosco pattern comuni
    if (name.includes('button')) return { type: 'create_component', component: 'Button' };
    if (name.includes('input')) return { type: 'create_component', component: 'Input' };
    if (name.includes('card')) return { type: 'create_component', component: 'Card' };
    if (name.includes('nav')) return { type: 'create_component', component: 'Navigation' };
    if (name.includes('hero')) return { type: 'create_component', component: 'Hero' };
    if (name.includes('form')) return { type: 'create_component', component: 'Form' };
    if (name.includes('modal')) return { type: 'create_component', component: 'Modal' };
    if (name.includes('page')) return { type: 'create_page', page: name };

    // Se ha hover/active/focus nel nome, è un'interazione
    if (name.match(/hover|active|focus|click/)) {
      return { type: 'add_interaction' };
    }

    return { type: 'modify_style' };
  }

  // ============== TI AIUTO A COMPLETARE ==============
  async helpYouCreateComponent(selection, intent) {
    console.log(`\n🛠️ Let me help you complete the ${intent.component}...`);

    // Aggiungo elementi mancanti basati sul tipo
    switch (intent.component) {
      case 'Button':
        await this.completeButton(selection);
        break;
      case 'Input':
        await this.completeInput(selection);
        break;
      case 'Card':
        await this.completeCard(selection);
        break;
      case 'Form':
        await this.completeForm(selection);
        break;
    }

    // Genero il codice React
    const code = await this.generateReactFromNode(selection);
    await this.saveToProject(code);
  }

  async completeButton(node) {
    // Se è solo un rettangolo, aggiungo il testo
    if (!node.children || node.children.length === 0) {
      console.log('→ Adding button text...');
      await this.sendCommand('create_text', {
        x: node.x + 20,
        y: node.y + 12,
        text: 'Click Me',
        fontSize: 14,
        fontWeight: 600,
        parentId: node.id
      });
    }

    // Aggiungo stati hover se non ci sono
    console.log('→ Adding hover state...');
    const hoverId = await this.duplicateNode(node, '_hover');
    await this.sendCommand('set_fill_color', {
      nodeId: hoverId,
      color: { r: 0.15, g: 0.45, b: 0.9, a: 1 }
    });
  }

  async completeInput(node) {
    // Aggiungo label se manca
    if (!this.hasLabel(node)) {
      console.log('→ Adding input label...');
      await this.sendCommand('create_text', {
        x: node.x,
        y: node.y - 24,
        text: 'Label',
        fontSize: 12,
        fontWeight: 500,
        fontColor: { r: 0.4, g: 0.4, b: 0.4, a: 1 }
      });
    }

    // Aggiungo placeholder
    console.log('→ Adding placeholder...');
    await this.sendCommand('create_text', {
      x: node.x + 12,
      y: node.y + 14,
      text: 'Enter text...',
      fontSize: 14,
      fontColor: { r: 0.6, g: 0.6, b: 0.6, a: 1 },
      parentId: node.id
    });
  }

  async completeCard(node) {
    console.log('→ Structuring card layout...');

    // Aggiungo struttura tipica card
    const sections = [
      { name: 'Card_Header', height: 60 },
      { name: 'Card_Body', height: 120 },
      { name: 'Card_Footer', height: 60 }
    ];

    let yOffset = 0;
    for (const section of sections) {
      await this.sendCommand('create_frame', {
        x: 0,
        y: yOffset,
        width: node.width,
        height: section.height,
        name: section.name,
        parentId: node.id,
        fillColor: { r: 0, g: 0, b: 0, a: 0 }
      });
      yOffset += section.height;
    }
  }

  async completeForm(node) {
    console.log('→ Adding form fields...');

    const fields = ['Name', 'Email', 'Message'];
    let yOffset = 40;

    for (const field of fields) {
      await this.createInput({
        x: 20,
        y: yOffset,
        width: node.width - 40,
        label: field,
        parentId: node.id
      });
      yOffset += 80;
    }

    // Aggiungo submit button
    await this.createButton({
      x: 20,
      y: yOffset,
      text: 'Submit',
      parentId: node.id
    });
  }

  // ============== GENERO REACT AUTOMATICAMENTE ==============
  async generateReactFromNode(node) {
    const componentName = this.toPascalCase(node.name);

    // Analizzo struttura e genero codice intelligente
    const analysis = this.analyzeStructure(node);

    let imports = ['import React'];
    let hooks = [];
    let jsx = '';
    let styles = '';

    // Se ha interazioni, aggiungo useState
    if (analysis.hasInteractions) {
      imports.push('{ useState }');
      hooks.push('const [isHovered, setIsHovered] = useState(false);');
    }

    // Se è un form, aggiungo gestione form
    if (analysis.isForm) {
      imports.push('{ useForm }');
      hooks.push('const { register, handleSubmit } = useForm();');
    }

    // Genero JSX basato sull'analisi
    jsx = this.generateSmartJSX(node, analysis);

    // Genero Tailwind classes
    const tailwindClasses = this.generateTailwindClasses(node);

    const component = `${imports.join(', ')} from 'react';
${analysis.isForm ? "import { useForm } from 'react-hook-form';" : ''}
import { cn } from '@/lib/utils';

const ${componentName} = ({ className, ...props }) => {
  ${hooks.join('\n  ')}

  return (
    ${jsx}
  );
};

export default ${componentName};`;

    return {
      name: componentName,
      component,
      path: `components/generated/${componentName}.tsx`
    };
  }

  generateSmartJSX(node, analysis) {
    // Genero JSX intelligente basato sul tipo di componente
    if (analysis.isButton) {
      return `<button
      className={cn(
        "px-4 py-2 rounded-lg font-medium transition-all",
        "bg-blue-500 text-white hover:bg-blue-600",
        className
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      {...props}
    >
      ${node.children?.[0]?.characters || 'Button'}
    </button>`;
    }

    if (analysis.isInput) {
      return `<div className="flex flex-col gap-2">
      <label className="text-sm font-medium text-gray-600">
        ${this.extractLabel(node)}
      </label>
      <input
        className={cn(
          "px-3 py-2 border border-gray-300 rounded-md",
          "focus:outline-none focus:ring-2 focus:ring-blue-500",
          className
        )}
        placeholder="${this.extractPlaceholder(node)}"
        {...props}
      />
    </div>`;
    }

    if (analysis.isCard) {
      return `<div className={cn(
        "bg-white rounded-lg shadow-md p-6",
        "hover:shadow-lg transition-shadow",
        className
      )} {...props}>
      ${this.generateChildrenJSX(node.children)}
    </div>`;
    }

    // Default
    return `<div className={cn("${this.generateTailwindClasses(node)}", className)} {...props}>
      ${this.generateChildrenJSX(node.children)}
    </div>`;
  }

  // ============== AGGIORNO IN TEMPO REALE ==============
  async onFigmaChange(change) {
    console.log('🔄 Syncing change to React...');

    // Trovo il componente React corrispondente
    const componentPath = this.componentMap.get(change.nodeId);

    if (componentPath) {
      // Rigenero il componente
      const node = await this.getNodeInfo(change.nodeId);
      const code = await this.generateReactFromNode(node);

      // Salvo aggiornamento
      await this.saveToProject(code);

      // Hot reload automatico
      console.log('🔥 Hot reloading...');
    }
  }

  async saveToProject(code) {
    const outputPath = path.join(
      '/Users/erik/Desktop/claude-multiagent-system/claude-ui/src',
      code.path
    );

    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, code.component);

    console.log(`✅ Saved: ${code.name} → ${code.path}`);

    // Registro mapping per aggiornamenti futuri
    this.componentMap.set(code.nodeId, outputPath);
  }

  // ============== COMUNICAZIONE VISUALE ==============
  async showMeWhatYouWant() {
    console.log('\n🎨 Show me what you want in Figma!');
    console.log('I can understand:');
    console.log('  • Component names (Button, Input, Card, etc.)');
    console.log('  • Layout structures');
    console.log('  • Colors and styles');
    console.log('  • Interactions (hover, click states)');
    console.log('\nI will:');
    console.log('  ✓ Complete missing parts');
    console.log('  ✓ Generate React code');
    console.log('  ✓ Keep everything in sync');
    console.log('  ✓ Update when you change things');
  }

  // ============== UTILITIES ==============
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

  async getSelection() {
    return this.sendCommand('get_selection');
  }

  async getNodeInfo(nodeId) {
    return this.sendCommand('get_node_info', { nodeId });
  }

  toPascalCase(str) {
    return str.replace(/(?:^\w|[A-Z]|\b\w)/g, w => w.toUpperCase()).replace(/\s+/g, '');
  }

  generateTailwindClasses(node) {
    const classes = [];

    // Dimensioni
    if (node.width) classes.push(`w-[${Math.round(node.width)}px]`);
    if (node.height) classes.push(`h-[${Math.round(node.height)}px]`);

    // Layout
    if (node.layoutMode === 'HORIZONTAL') classes.push('flex flex-row');
    if (node.layoutMode === 'VERTICAL') classes.push('flex flex-col');

    // Colori
    if (node.fills?.[0]?.color) {
      const { r, g, b } = node.fills[0].color;
      if (r > 0.9 && g > 0.9 && b > 0.9) classes.push('bg-white');
      else if (r < 0.1 && g < 0.1 && b < 0.1) classes.push('bg-black');
      else classes.push(`bg-[rgb(${Math.round(r*255)},${Math.round(g*255)},${Math.round(b*255)})]`);
    }

    // Bordi
    if (node.cornerRadius) classes.push(`rounded-[${node.cornerRadius}px]`);

    return classes.join(' ');
  }

  analyzeStructure(node) {
    const name = node.name?.toLowerCase() || '';

    return {
      isButton: name.includes('button') || name.includes('btn'),
      isInput: name.includes('input') || name.includes('field'),
      isCard: name.includes('card'),
      isForm: name.includes('form'),
      hasInteractions: node.children?.some(c => c.name?.includes('hover')),
      hasStates: node.children?.some(c => c.name?.match(/active|disabled|focus/))
    };
  }
}

// ============== START TEAM MODE ==============
if (require.main === module) {
  const channel = process.argv[2] || '5utu5pn0';

  async function startTeamMode() {
    const team = new FigmaTeamMode(channel);

    try {
      await team.connect();

      console.log('\n╔════════════════════════════════════╗');
      console.log('║     🤝 FIGMA TEAM MODE ACTIVE      ║');
      console.log('╚════════════════════════════════════╝\n');

      console.log('How it works:');
      console.log('1. You design in Figma → I see it');
      console.log('2. I generate React code automatically');
      console.log('3. You modify → I update in real-time');
      console.log('4. Perfect frontend together!\n');

      await team.showMeWhatYouWant();
      await team.watchYourChanges();

      // Keep running
      process.stdin.resume();

    } catch (error) {
      console.error('Error:', error);
    }
  }

  startTeamMode();
}

module.exports = FigmaTeamMode;