#!/usr/bin/env node

/**
 * Replicate UI Component Library to Figma
 * Creates all reusable components from the system
 */

const WebSocket = require('ws');

class UIComponentsReplicator {
  constructor(channel) {
    this.channel = channel;
    this.ws = null;
    this.createdIds = [];
  }

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

      console.log(`→ ${command}: ${params.name || params.text || ''}`);
      this.ws.send(JSON.stringify(message));

      setTimeout(() => {
        this.createdIds.push(id);
        resolve(id);
      }, 100);
    });
  }

  async createComponentLibrary() {
    console.log('\n🎨 Creating UI Component Library...');

    // Main Container for Component Library
    const libraryId = await this.sendCommand('create_frame', {
      x: 100,
      y: 2000,
      width: 1440,
      height: 1200,
      name: 'UI_Component_Library',
      fillColor: { r: 0.98, g: 0.98, b: 1, a: 1 }
    });

    // Title
    await this.sendCommand('create_text', {
      x: 32,
      y: 32,
      text: '🎨 Claude Multi-Agent UI Components',
      fontSize: 28,
      fontWeight: 700,
      parentId: libraryId
    });

    // Buttons Section
    await this.createButtonsSection(libraryId);

    // Inputs Section
    await this.createInputsSection(libraryId);

    // Cards Section
    await this.createCardsSection(libraryId);

    // Modals Section
    await this.createModalsSection(libraryId);

    // Navigation Section
    await this.createNavigationSection(libraryId);

    // Status Indicators Section
    await this.createStatusIndicators(libraryId);

    console.log(`✅ Component Library created with ${this.createdIds.length} elements`);
    return libraryId;
  }

  async createButtonsSection(parentId) {
    console.log('  → Creating Buttons...');

    // Section container
    const sectionId = await this.sendCommand('create_frame', {
      x: 32,
      y: 100,
      width: 400,
      height: 300,
      name: 'Buttons_Section',
      fillColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId
    });

    // Section title
    await this.sendCommand('create_text', {
      x: 20,
      y: 20,
      text: 'Buttons',
      fontSize: 18,
      fontWeight: 600,
      parentId: sectionId
    });

    // Primary Button
    const primaryBtnId = await this.sendCommand('create_frame', {
      x: 20,
      y: 60,
      width: 120,
      height: 40,
      name: 'Button_Primary',
      fillColor: { r: 0.2, g: 0.5, b: 1, a: 1 },
      parentId: sectionId
    });

    await this.sendCommand('set_corner_radius', {
      nodeId: primaryBtnId,
      radius: 6
    });

    await this.sendCommand('create_text', {
      x: 35,
      y: 12,
      text: 'Primary',
      fontSize: 14,
      fontWeight: 500,
      fontColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId: primaryBtnId
    });

    // Secondary Button
    const secondaryBtnId = await this.sendCommand('create_frame', {
      x: 160,
      y: 60,
      width: 120,
      height: 40,
      name: 'Button_Secondary',
      fillColor: { r: 0.95, g: 0.95, b: 0.96, a: 1 },
      parentId: sectionId
    });

    await this.sendCommand('set_corner_radius', {
      nodeId: secondaryBtnId,
      radius: 6
    });

    await this.sendCommand('create_text', {
      x: 28,
      y: 12,
      text: 'Secondary',
      fontSize: 14,
      fontWeight: 500,
      fontColor: { r: 0.2, g: 0.2, b: 0.3, a: 1 },
      parentId: secondaryBtnId
    });

    // Danger Button
    const dangerBtnId = await this.sendCommand('create_frame', {
      x: 20,
      y: 120,
      width: 120,
      height: 40,
      name: 'Button_Danger',
      fillColor: { r: 0.9, g: 0.2, b: 0.2, a: 1 },
      parentId: sectionId
    });

    await this.sendCommand('set_corner_radius', {
      nodeId: dangerBtnId,
      radius: 6
    });

    await this.sendCommand('create_text', {
      x: 37,
      y: 12,
      text: 'Danger',
      fontSize: 14,
      fontWeight: 500,
      fontColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId: dangerBtnId
    });

    // Success Button
    const successBtnId = await this.sendCommand('create_frame', {
      x: 160,
      y: 120,
      width: 120,
      height: 40,
      name: 'Button_Success',
      fillColor: { r: 0.2, g: 0.8, b: 0.4, a: 1 },
      parentId: sectionId
    });

    await this.sendCommand('set_corner_radius', {
      nodeId: successBtnId,
      radius: 6
    });

    await this.sendCommand('create_text', {
      x: 35,
      y: 12,
      text: 'Success',
      fontSize: 14,
      fontWeight: 500,
      fontColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId: successBtnId
    });

    // Icon Button
    const iconBtnId = await this.sendCommand('create_frame', {
      x: 20,
      y: 180,
      width: 40,
      height: 40,
      name: 'Button_Icon',
      fillColor: { r: 0.2, g: 0.5, b: 1, a: 1 },
      parentId: sectionId
    });

    await this.sendCommand('set_corner_radius', {
      nodeId: iconBtnId,
      radius: 20
    });

    await this.sendCommand('create_text', {
      x: 13,
      y: 10,
      text: '🚀',
      fontSize: 18,
      parentId: iconBtnId
    });

    // Disabled Button
    const disabledBtnId = await this.sendCommand('create_frame', {
      x: 80,
      y: 180,
      width: 120,
      height: 40,
      name: 'Button_Disabled',
      fillColor: { r: 0.9, g: 0.9, b: 0.9, a: 1 },
      parentId: sectionId
    });

    await this.sendCommand('set_corner_radius', {
      nodeId: disabledBtnId,
      radius: 6
    });

    await this.sendCommand('create_text', {
      x: 32,
      y: 12,
      text: 'Disabled',
      fontSize: 14,
      fontWeight: 500,
      fontColor: { r: 0.6, g: 0.6, b: 0.6, a: 1 },
      parentId: disabledBtnId
    });
  }

  async createInputsSection(parentId) {
    console.log('  → Creating Inputs...');

    const sectionId = await this.sendCommand('create_frame', {
      x: 480,
      y: 100,
      width: 400,
      height: 300,
      name: 'Inputs_Section',
      fillColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId
    });

    // Section title
    await this.sendCommand('create_text', {
      x: 20,
      y: 20,
      text: 'Inputs',
      fontSize: 18,
      fontWeight: 600,
      parentId: sectionId
    });

    // Text Input
    const textInputId = await this.sendCommand('create_frame', {
      x: 20,
      y: 60,
      width: 360,
      height: 40,
      name: 'Input_Text',
      fillColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId: sectionId
    });

    await this.sendCommand('set_stroke_color', {
      nodeId: textInputId,
      color: { r: 0.8, g: 0.8, b: 0.85, a: 1 },
      strokeWeight: 1
    });

    await this.sendCommand('set_corner_radius', {
      nodeId: textInputId,
      radius: 4
    });

    await this.sendCommand('create_text', {
      x: 12,
      y: 12,
      text: 'Enter text...',
      fontSize: 14,
      fontColor: { r: 0.6, g: 0.6, b: 0.65, a: 1 },
      parentId: textInputId
    });

    // Search Input with Icon
    const searchInputId = await this.sendCommand('create_frame', {
      x: 20,
      y: 120,
      width: 360,
      height: 40,
      name: 'Input_Search',
      fillColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId: sectionId
    });

    await this.sendCommand('set_stroke_color', {
      nodeId: searchInputId,
      color: { r: 0.8, g: 0.8, b: 0.85, a: 1 },
      strokeWeight: 1
    });

    await this.sendCommand('set_corner_radius', {
      nodeId: searchInputId,
      radius: 20
    });

    await this.sendCommand('create_text', {
      x: 12,
      y: 12,
      text: '🔍',
      fontSize: 16,
      parentId: searchInputId
    });

    await this.sendCommand('create_text', {
      x: 40,
      y: 12,
      text: 'Search...',
      fontSize: 14,
      fontColor: { r: 0.6, g: 0.6, b: 0.65, a: 1 },
      parentId: searchInputId
    });

    // Textarea
    const textareaId = await this.sendCommand('create_frame', {
      x: 20,
      y: 180,
      width: 360,
      height: 80,
      name: 'Input_Textarea',
      fillColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId: sectionId
    });

    await this.sendCommand('set_stroke_color', {
      nodeId: textareaId,
      color: { r: 0.8, g: 0.8, b: 0.85, a: 1 },
      strokeWeight: 1
    });

    await this.sendCommand('set_corner_radius', {
      nodeId: textareaId,
      radius: 4
    });

    await this.sendCommand('create_text', {
      x: 12,
      y: 12,
      text: 'Enter multiple lines of text...',
      fontSize: 14,
      fontColor: { r: 0.6, g: 0.6, b: 0.65, a: 1 },
      parentId: textareaId
    });
  }

  async createCardsSection(parentId) {
    console.log('  → Creating Cards...');

    const sectionId = await this.sendCommand('create_frame', {
      x: 920,
      y: 100,
      width: 480,
      height: 300,
      name: 'Cards_Section',
      fillColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId
    });

    // Section title
    await this.sendCommand('create_text', {
      x: 20,
      y: 20,
      text: 'Cards',
      fontSize: 18,
      fontWeight: 600,
      parentId: sectionId
    });

    // Agent Card
    const agentCardId = await this.sendCommand('create_frame', {
      x: 20,
      y: 60,
      width: 200,
      height: 120,
      name: 'Card_Agent',
      fillColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId: sectionId
    });

    await this.sendCommand('set_effect', {
      nodeId: agentCardId,
      effect: {
        type: 'DROP_SHADOW',
        color: { r: 0, g: 0, b: 0, a: 0.1 },
        offset: { x: 0, y: 2 },
        radius: 8
      }
    });

    await this.sendCommand('set_corner_radius', {
      nodeId: agentCardId,
      radius: 8
    });

    // Status dot
    await this.sendCommand('create_ellipse', {
      x: 12,
      y: 12,
      width: 10,
      height: 10,
      fillColor: { r: 0.2, g: 0.8, b: 0.4, a: 1 },
      parentId: agentCardId
    });

    await this.sendCommand('create_text', {
      x: 28,
      y: 10,
      text: 'backend-api',
      fontSize: 14,
      fontWeight: 600,
      parentId: agentCardId
    });

    await this.sendCommand('create_text', {
      x: 12,
      y: 40,
      text: 'Status: Active',
      fontSize: 12,
      fontColor: { r: 0.5, g: 0.5, b: 0.5, a: 1 },
      parentId: agentCardId
    });

    await this.sendCommand('create_text', {
      x: 12,
      y: 60,
      text: 'Processing requests',
      fontSize: 12,
      fontColor: { r: 0.4, g: 0.4, b: 0.4, a: 1 },
      parentId: agentCardId
    });

    // Stats Card
    const statsCardId = await this.sendCommand('create_frame', {
      x: 240,
      y: 60,
      width: 200,
      height: 120,
      name: 'Card_Stats',
      fillColor: { r: 0.98, g: 0.99, b: 1, a: 1 },
      parentId: sectionId
    });

    await this.sendCommand('set_corner_radius', {
      nodeId: statsCardId,
      radius: 8
    });

    await this.sendCommand('create_text', {
      x: 12,
      y: 12,
      text: '📊',
      fontSize: 24,
      parentId: statsCardId
    });

    await this.sendCommand('create_text', {
      x: 12,
      y: 50,
      text: 'Total Activities',
      fontSize: 12,
      fontColor: { r: 0.5, g: 0.5, b: 0.5, a: 1 },
      parentId: statsCardId
    });

    await this.sendCommand('create_text', {
      x: 12,
      y: 75,
      text: '1,234',
      fontSize: 24,
      fontWeight: 700,
      fontColor: { r: 0.2, g: 0.5, b: 1, a: 1 },
      parentId: statsCardId
    });
  }

  async createModalsSection(parentId) {
    console.log('  → Creating Modals...');

    const sectionId = await this.sendCommand('create_frame', {
      x: 32,
      y: 440,
      width: 500,
      height: 320,
      name: 'Modals_Section',
      fillColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId
    });

    // Section title
    await this.sendCommand('create_text', {
      x: 20,
      y: 20,
      text: 'Modals',
      fontSize: 18,
      fontWeight: 600,
      parentId: sectionId
    });

    // Modal
    const modalId = await this.sendCommand('create_frame', {
      x: 20,
      y: 60,
      width: 400,
      height: 240,
      name: 'Modal',
      fillColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId: sectionId
    });

    await this.sendCommand('set_effect', {
      nodeId: modalId,
      effect: {
        type: 'DROP_SHADOW',
        color: { r: 0, g: 0, b: 0, a: 0.2 },
        offset: { x: 0, y: 4 },
        radius: 16
      }
    });

    await this.sendCommand('set_corner_radius', {
      nodeId: modalId,
      radius: 12
    });

    // Modal header
    await this.sendCommand('create_text', {
      x: 24,
      y: 24,
      text: 'Confirm Action',
      fontSize: 18,
      fontWeight: 600,
      parentId: modalId
    });

    // Close button
    await this.sendCommand('create_text', {
      x: 360,
      y: 20,
      text: '×',
      fontSize: 24,
      fontColor: { r: 0.5, g: 0.5, b: 0.5, a: 1 },
      parentId: modalId
    });

    // Modal content
    await this.sendCommand('create_text', {
      x: 24,
      y: 70,
      text: 'Are you sure you want to proceed with this action?',
      fontSize: 14,
      fontColor: { r: 0.4, g: 0.4, b: 0.4, a: 1 },
      parentId: modalId
    });

    await this.sendCommand('create_text', {
      x: 24,
      y: 95,
      text: 'This operation cannot be undone.',
      fontSize: 14,
      fontColor: { r: 0.6, g: 0.6, b: 0.6, a: 1 },
      parentId: modalId
    });

    // Modal buttons
    const cancelBtnId = await this.sendCommand('create_frame', {
      x: 200,
      y: 180,
      width: 80,
      height: 36,
      name: 'Button_Cancel',
      fillColor: { r: 0.95, g: 0.95, b: 0.96, a: 1 },
      parentId: modalId
    });

    await this.sendCommand('set_corner_radius', {
      nodeId: cancelBtnId,
      radius: 6
    });

    await this.sendCommand('create_text', {
      x: 20,
      y: 10,
      text: 'Cancel',
      fontSize: 14,
      fontWeight: 500,
      parentId: cancelBtnId
    });

    const confirmBtnId = await this.sendCommand('create_frame', {
      x: 296,
      y: 180,
      width: 80,
      height: 36,
      name: 'Button_Confirm',
      fillColor: { r: 0.2, g: 0.5, b: 1, a: 1 },
      parentId: modalId
    });

    await this.sendCommand('set_corner_radius', {
      nodeId: confirmBtnId,
      radius: 6
    });

    await this.sendCommand('create_text', {
      x: 18,
      y: 10,
      text: 'Confirm',
      fontSize: 14,
      fontWeight: 500,
      fontColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId: confirmBtnId
    });
  }

  async createNavigationSection(parentId) {
    console.log('  → Creating Navigation...');

    const sectionId = await this.sendCommand('create_frame', {
      x: 580,
      y: 440,
      width: 400,
      height: 320,
      name: 'Navigation_Section',
      fillColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId
    });

    // Section title
    await this.sendCommand('create_text', {
      x: 20,
      y: 20,
      text: 'Navigation',
      fontSize: 18,
      fontWeight: 600,
      parentId: sectionId
    });

    // Tabs
    const tabsContainer = await this.sendCommand('create_frame', {
      x: 20,
      y: 60,
      width: 360,
      height: 40,
      name: 'Tabs',
      fillColor: { r: 0.98, g: 0.98, b: 0.99, a: 1 },
      parentId: sectionId
    });

    const tabs = ['Overview', 'Analytics', 'Settings'];
    let tabX = 0;

    for (let i = 0; i < tabs.length; i++) {
      const isActive = i === 0;
      const tabId = await this.sendCommand('create_frame', {
        x: tabX,
        y: 0,
        width: 120,
        height: 40,
        name: `Tab_${tabs[i]}`,
        fillColor: isActive
          ? { r: 0.2, g: 0.5, b: 1, a: 1 }
          : { r: 0.98, g: 0.98, b: 0.99, a: 1 },
        parentId: tabsContainer
      });

      await this.sendCommand('create_text', {
        x: 120 / 2 - 30,
        y: 12,
        text: tabs[i],
        fontSize: 14,
        fontWeight: isActive ? 600 : 400,
        fontColor: isActive
          ? { r: 1, g: 1, b: 1, a: 1 }
          : { r: 0.4, g: 0.4, b: 0.4, a: 1 },
        parentId: tabId
      });

      tabX += 120;
    }

    // Breadcrumbs
    const breadcrumbsId = await this.sendCommand('create_frame', {
      x: 20,
      y: 120,
      width: 360,
      height: 30,
      name: 'Breadcrumbs',
      fillColor: { r: 0, g: 0, b: 0, a: 0 },
      parentId: sectionId
    });

    const crumbs = ['Home', 'Dashboard', 'Settings'];
    let crumbX = 0;

    for (let i = 0; i < crumbs.length; i++) {
      if (i > 0) {
        await this.sendCommand('create_text', {
          x: crumbX,
          y: 5,
          text: '/',
          fontSize: 12,
          fontColor: { r: 0.6, g: 0.6, b: 0.6, a: 1 },
          parentId: breadcrumbsId
        });
        crumbX += 20;
      }

      const isLast = i === crumbs.length - 1;
      await this.sendCommand('create_text', {
        x: crumbX,
        y: 5,
        text: crumbs[i],
        fontSize: 12,
        fontWeight: isLast ? 600 : 400,
        fontColor: isLast
          ? { r: 0.2, g: 0.2, b: 0.3, a: 1 }
          : { r: 0.2, g: 0.5, b: 1, a: 1 },
        parentId: breadcrumbsId
      });
      crumbX += crumbs[i].length * 7 + 10;
    }
  }

  async createStatusIndicators(parentId) {
    console.log('  → Creating Status Indicators...');

    const sectionId = await this.sendCommand('create_frame', {
      x: 1020,
      y: 440,
      width: 380,
      height: 320,
      name: 'Status_Section',
      fillColor: { r: 1, g: 1, b: 1, a: 1 },
      parentId
    });

    // Section title
    await this.sendCommand('create_text', {
      x: 20,
      y: 20,
      text: 'Status Indicators',
      fontSize: 18,
      fontWeight: 600,
      parentId: sectionId
    });

    // Status badges
    const statuses = [
      { label: 'Success', color: { r: 0.2, g: 0.8, b: 0.4 } },
      { label: 'Warning', color: { r: 1, g: 0.6, b: 0 } },
      { label: 'Error', color: { r: 0.9, g: 0.2, b: 0.2 } },
      { label: 'Info', color: { r: 0.2, g: 0.5, b: 1 } }
    ];

    let badgeX = 20;
    for (const status of statuses) {
      const badgeId = await this.sendCommand('create_frame', {
        x: badgeX,
        y: 60,
        width: 80,
        height: 28,
        name: `Badge_${status.label}`,
        fillColor: { ...status.color, a: 0.1 },
        parentId: sectionId
      });

      await this.sendCommand('set_corner_radius', {
        nodeId: badgeId,
        radius: 14
      });

      await this.sendCommand('create_ellipse', {
        x: 8,
        y: 9,
        width: 10,
        height: 10,
        fillColor: status.color,
        parentId: badgeId
      });

      await this.sendCommand('create_text', {
        x: 22,
        y: 6,
        text: status.label,
        fontSize: 12,
        fontWeight: 500,
        fontColor: status.color,
        parentId: badgeId
      });

      badgeX += 90;
    }

    // Progress bars
    const progressY = 120;
    const progressData = [
      { label: 'Upload Progress', percent: 75 },
      { label: 'Processing', percent: 40 },
      { label: 'Complete', percent: 100 }
    ];

    for (let i = 0; i < progressData.length; i++) {
      const progress = progressData[i];
      const yOffset = progressY + (i * 60);

      await this.sendCommand('create_text', {
        x: 20,
        y: yOffset,
        text: progress.label,
        fontSize: 12,
        fontColor: { r: 0.4, g: 0.4, b: 0.4, a: 1 },
        parentId: sectionId
      });

      // Progress track
      const trackId = await this.sendCommand('create_frame', {
        x: 20,
        y: yOffset + 20,
        width: 340,
        height: 8,
        name: 'Progress_Track',
        fillColor: { r: 0.9, g: 0.9, b: 0.92, a: 1 },
        parentId: sectionId
      });

      await this.sendCommand('set_corner_radius', {
        nodeId: trackId,
        radius: 4
      });

      // Progress fill
      const fillId = await this.sendCommand('create_frame', {
        x: 0,
        y: 0,
        width: (340 * progress.percent) / 100,
        height: 8,
        name: 'Progress_Fill',
        fillColor: progress.percent === 100
          ? { r: 0.2, g: 0.8, b: 0.4, a: 1 }
          : { r: 0.2, g: 0.5, b: 1, a: 1 },
        parentId: trackId
      });

      await this.sendCommand('set_corner_radius', {
        nodeId: fillId,
        radius: 4
      });

      // Percentage text
      await this.sendCommand('create_text', {
        x: 320,
        y: yOffset,
        text: `${progress.percent}%`,
        fontSize: 12,
        fontWeight: 500,
        fontColor: { r: 0.2, g: 0.5, b: 1, a: 1 },
        parentId: sectionId
      });
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Main execution
async function main() {
  const channel = process.argv[2] || '5utu5pn0';
  const replicator = new UIComponentsReplicator(channel);

  try {
    await replicator.connect();
    console.log('🚀 Starting UI Components Replication...\n');

    await replicator.createComponentLibrary();

    console.log('\n✅ UI Components Replication Complete!');
    console.log('📌 Check Figma to see your component library!\n');

    replicator.disconnect();
  } catch (error) {
    console.error('❌ Error:', error);
    replicator.disconnect();
  }
}

if (require.main === module) {
  main();
}

module.exports = UIComponentsReplicator;