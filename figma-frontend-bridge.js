#!/usr/bin/env node

/**
 * FIGMA FRONTEND BRIDGE
 * Sistema completo per controllo totale di Figma e generazione frontend
 */

const WebSocket = require('ws');
const fs = require('fs').promises;
const path = require('path');

class FigmaFrontendBridge {
  constructor(channel) {
    this.channel = channel;
    this.ws = null;
    this.nodes = new Map();
    this.components = [];
  }

  // ============== CONNESSIONE ==============
  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket('ws://localhost:3055');

      this.ws.on('open', () => {
        console.log('✅ Connected to Figma');
        this.ws.send(JSON.stringify({
          type: 'join',
          channel: this.channel
        }));
        setTimeout(resolve, 500);
      });

      this.ws.on('message', (data) => {
        const msg = JSON.parse(data.toString());
        if (msg.message && msg.message.result) {
          this.processResponse(msg.message.result);
        }
      });

      this.ws.on('error', reject);
    });
  }

  processResponse(result) {
    if (result.id) {
      this.nodes.set(result.id, result);
    }
  }

  // ============== READ FROM FIGMA ==============
  async getSelection() {
    return this.sendCommand('get_selection');
  }

  async getDocumentInfo() {
    return this.sendCommand('get_document_info');
  }

  async getNodeInfo(nodeId) {
    return this.sendCommand('get_node_info', { nodeId });
  }

  async getStyles() {
    return this.sendCommand('get_styles');
  }

  // ============== WRITE TO FIGMA ==============
  async createComponent(config) {
    const {
      type = 'frame',
      x = 0,
      y = 0,
      width = 200,
      height = 100,
      name = 'Component',
      fillColor = {r: 1, g: 1, b: 1, a: 1},
      children = []
    } = config;

    // Create main container
    const containerId = await this.createElement(type, {
      x, y, width, height, name, fillColor
    });

    // Create children
    for (const child of children) {
      await this.createChildElement(containerId, child);
    }

    return containerId;
  }

  async createElement(type, params) {
    const commandMap = {
      'frame': 'create_frame',
      'text': 'create_text',
      'rectangle': 'create_rectangle',
      'ellipse': 'create_ellipse',
      'star': 'create_star'
    };

    const command = commandMap[type] || 'create_frame';
    const result = await this.sendCommand(command, params);
    return result?.id;
  }

  async createChildElement(parentId, config) {
    const params = { ...config, parentId };
    return this.createElement(config.type, params);
  }

  // ============== DESIGN SYSTEM ==============
  async createButton(config = {}) {
    const {
      x = 100,
      y = 100,
      width = 120,
      height = 48,
      text = 'Button',
      variant = 'primary', // primary, secondary, ghost
      size = 'medium' // small, medium, large
    } = config;

    const variants = {
      primary: { bg: {r: 0.2, g: 0.5, b: 1, a: 1}, text: {r: 1, g: 1, b: 1, a: 1} },
      secondary: { bg: {r: 0.9, g: 0.9, b: 0.9, a: 1}, text: {r: 0.2, g: 0.2, b: 0.2, a: 1} },
      ghost: { bg: {r: 0, g: 0, b: 0, a: 0}, text: {r: 0.2, g: 0.5, b: 1, a: 1} }
    };

    const sizes = {
      small: { width: 80, height: 32, fontSize: 12 },
      medium: { width: 120, height: 48, fontSize: 14 },
      large: { width: 160, height: 56, fontSize: 16 }
    };

    const v = variants[variant];
    const s = sizes[size];

    // Create button frame
    const buttonId = await this.sendCommand('create_frame', {
      x, y,
      width: s.width,
      height: s.height,
      name: `Button_${variant}_${text}`,
      fillColor: v.bg
    });

    // Add corner radius
    await this.sendCommand('set_corner_radius', {
      nodeId: buttonId,
      radius: 8
    });

    // Add text
    await this.sendCommand('create_text', {
      x: s.width / 2 - (text.length * s.fontSize * 0.3),
      y: s.height / 2 - s.fontSize / 2,
      text: text,
      fontSize: s.fontSize,
      fontWeight: 600,
      fontColor: v.text,
      parentId: buttonId
    });

    return buttonId;
  }

  async createInput(config = {}) {
    const {
      x = 100,
      y = 100,
      width = 280,
      height = 48,
      label = 'Label',
      placeholder = 'Enter text...',
      type = 'text' // text, email, password
    } = config;

    // Container
    const containerId = await this.sendCommand('create_frame', {
      x, y,
      width: width + 20,
      height: height + 40,
      name: `Input_${label}`,
      fillColor: {r: 0, g: 0, b: 0, a: 0}
    });

    // Label
    await this.sendCommand('create_text', {
      x: 0,
      y: 0,
      text: label,
      fontSize: 12,
      fontWeight: 500,
      fontColor: {r: 0.4, g: 0.4, b: 0.4, a: 1},
      parentId: containerId
    });

    // Input field
    const inputId = await this.sendCommand('create_frame', {
      x: 0,
      y: 20,
      width: width,
      height: height,
      name: 'Input Field',
      fillColor: {r: 0.98, g: 0.98, b: 0.98, a: 1},
      parentId: containerId
    });

    // Border
    await this.sendCommand('set_stroke_color', {
      nodeId: inputId,
      color: {r: 0.8, g: 0.8, b: 0.8, a: 1},
      strokeWeight: 1
    });

    // Corner radius
    await this.sendCommand('set_corner_radius', {
      nodeId: inputId,
      radius: 4
    });

    // Placeholder text
    await this.sendCommand('create_text', {
      x: 12,
      y: 14,
      text: placeholder,
      fontSize: 14,
      fontColor: {r: 0.6, g: 0.6, b: 0.6, a: 1},
      parentId: inputId
    });

    return containerId;
  }

  async createCard(config = {}) {
    const {
      x = 100,
      y = 100,
      width = 320,
      height = 200,
      title = 'Card Title',
      description = 'Card description goes here',
      hasImage = true
    } = config;

    // Card container
    const cardId = await this.sendCommand('create_frame', {
      x, y, width, height,
      name: `Card_${title}`,
      fillColor: {r: 1, g: 1, b: 1, a: 1}
    });

    // Shadow
    await this.sendCommand('set_effect', {
      nodeId: cardId,
      effect: {
        type: 'DROP_SHADOW',
        color: {r: 0, g: 0, b: 0, a: 0.1},
        offset: {x: 0, y: 2},
        radius: 8
      }
    });

    // Corner radius
    await this.sendCommand('set_corner_radius', {
      nodeId: cardId,
      radius: 12
    });

    // Image placeholder
    if (hasImage) {
      await this.sendCommand('create_frame', {
        x: 0,
        y: 0,
        width: width,
        height: 120,
        name: 'Image',
        fillColor: {r: 0.9, g: 0.9, b: 0.95, a: 1},
        parentId: cardId
      });
    }

    // Title
    await this.sendCommand('create_text', {
      x: 16,
      y: hasImage ? 136 : 16,
      text: title,
      fontSize: 18,
      fontWeight: 700,
      parentId: cardId
    });

    // Description
    await this.sendCommand('create_text', {
      x: 16,
      y: hasImage ? 164 : 44,
      text: description,
      fontSize: 14,
      fontColor: {r: 0.5, g: 0.5, b: 0.5, a: 1},
      parentId: cardId
    });

    return cardId;
  }

  // ============== FIGMA TO REACT ==============
  async generateReactComponent(nodeId) {
    const nodeInfo = await this.getNodeInfo(nodeId);

    const componentName = this.toPascalCase(nodeInfo.name || 'Component');

    const jsx = `import React from 'react';
import './styles/${componentName}.css';

const ${componentName} = () => {
  return (
    <div className="${this.toKebabCase(nodeInfo.name)}">
      ${this.nodeToJSX(nodeInfo)}
    </div>
  );
};

export default ${componentName};`;

    const css = this.nodeToCSS(nodeInfo);

    return { jsx, css, componentName };
  }

  nodeToJSX(node) {
    if (node.type === 'TEXT') {
      return `<span>${node.characters || ''}</span>`;
    }

    if (node.children && node.children.length > 0) {
      const childrenJSX = node.children.map(child => this.nodeToJSX(child)).join('\n      ');
      return `<div className="${this.toKebabCase(node.name)}">
        ${childrenJSX}
      </div>`;
    }

    return `<div className="${this.toKebabCase(node.name)}" />`;
  }

  nodeToCSS(node) {
    const className = '.' + this.toKebabCase(node.name);
    const styles = [];

    if (node.absoluteBoundingBox) {
      const { width, height } = node.absoluteBoundingBox;
      styles.push(`width: ${width}px;`);
      styles.push(`height: ${height}px;`);
    }

    if (node.fills && node.fills[0]) {
      const fill = node.fills[0];
      if (fill.color) {
        const { r, g, b } = fill.color;
        styles.push(`background-color: rgb(${r*255}, ${g*255}, ${b*255});`);
      }
    }

    if (node.cornerRadius) {
      styles.push(`border-radius: ${node.cornerRadius}px;`);
    }

    return `${className} {
  ${styles.join('\n  ')}
}`;
  }

  // ============== UTILITIES ==============
  async sendCommand(command, params = {}) {
    return new Promise((resolve) => {
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

      console.log(`→ ${command}`);
      this.ws.send(JSON.stringify(message));

      setTimeout(() => resolve(this.nodes.get(id)), 300);
    });
  }

  toPascalCase(str) {
    return str.replace(/(?:^\w|[A-Z]|\b\w)/g, (word, index) =>
      word.toUpperCase()
    ).replace(/\s+/g, '');
  }

  toKebabCase(str) {
    return str.replace(/\s+/g, '-').toLowerCase();
  }

  async saveComponent(component, outputDir = './claude-ui/src/components') {
    const { jsx, css, componentName } = component;

    // Save JSX
    await fs.mkdir(path.join(outputDir, 'generated'), { recursive: true });
    await fs.writeFile(
      path.join(outputDir, 'generated', `${componentName}.jsx`),
      jsx
    );

    // Save CSS
    await fs.mkdir(path.join(outputDir, 'styles'), { recursive: true });
    await fs.writeFile(
      path.join(outputDir, 'styles', `${componentName}.css`),
      css
    );

    console.log(`✅ Saved ${componentName} to ${outputDir}`);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

module.exports = FigmaFrontendBridge;

// ============== CLI USAGE ==============
if (require.main === module) {
  const channel = process.argv[2] || '5utu5pn0';

  async function demo() {
    const bridge = new FigmaFrontendBridge(channel);

    try {
      await bridge.connect();
      console.log('🎨 Figma Frontend Bridge Ready!\n');

      // Create a complete login form
      console.log('Creating Login Form...');

      // Main container
      await bridge.sendCommand('create_frame', {
        x: 600,
        y: 100,
        width: 400,
        height: 500,
        name: 'Login_Form',
        fillColor: {r: 0.98, g: 0.98, b: 1, a: 1}
      });

      // Title
      await bridge.createText({
        x: 650,
        y: 140,
        text: 'Welcome Back',
        fontSize: 28,
        fontWeight: 700
      });

      // Email input
      await bridge.createInput({
        x: 650,
        y: 200,
        label: 'Email',
        placeholder: 'your@email.com',
        type: 'email'
      });

      // Password input
      await bridge.createInput({
        x: 650,
        y: 290,
        label: 'Password',
        placeholder: '••••••••',
        type: 'password'
      });

      // Login button
      await bridge.createButton({
        x: 650,
        y: 400,
        text: 'Sign In',
        variant: 'primary',
        size: 'large'
      });

      console.log('✅ Login form created in Figma!');

      bridge.disconnect();
    } catch (error) {
      console.error('Error:', error);
    }
  }

  demo();
}