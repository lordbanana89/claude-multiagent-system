#!/usr/bin/env node

/**
 * FIGMA UI DESIGNER MCP - Complete UI Creation System
 * Permette a Claude Desktop di creare UI complete usando TUTTE le capacità di Figma
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema
} = require('@modelcontextprotocol/sdk/types.js');
const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

// Figma API configuration
const FIGMA_TOKEN = process.env.FIGMA_PERSONAL_ACCESS_TOKEN || "YOUR_FIGMA_TOKEN_HERE";
const FIGMA_API_BASE = "https://api.figma.com/v1";

class FigmaUIDesignerMCP {
  constructor() {
    this.server = new Server(
      {
        name: 'figma-ui-designer',
        version: '2.0.0',
      },
      {
        capabilities: {
          tools: {},
          resources: {},
        },
      }
    );

    this.axiosInstance = axios.create({
      baseURL: FIGMA_API_BASE,
      headers: {
        'X-Figma-Token': FIGMA_TOKEN,
      },
    });

    // Design system storage
    this.currentDesignSystem = null;
    this.currentFileKey = null;

    this.setupHandlers();
  }

  setupHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        // ===== CREAZIONE UI COMPLETA =====
        {
          name: 'create_complete_ui',
          description: 'Crea una UI completa per un software da zero',
          inputSchema: {
            type: 'object',
            properties: {
              app_name: {
                type: 'string',
                description: 'Nome dell\'applicazione',
              },
              app_type: {
                type: 'string',
                enum: ['web', 'mobile', 'desktop', 'dashboard', 'ecommerce', 'saas'],
                description: 'Tipo di applicazione',
              },
              features: {
                type: 'array',
                items: { type: 'string' },
                description: 'Lista delle features (es: login, dashboard, profile, settings)',
              },
              style: {
                type: 'string',
                enum: ['modern', 'minimal', 'corporate', 'playful', 'dark', 'glassmorphism'],
                description: 'Stile visivo',
              },
              color_scheme: {
                type: 'object',
                properties: {
                  primary: { type: 'string' },
                  secondary: { type: 'string' },
                  accent: { type: 'string' },
                },
              },
            },
            required: ['app_name', 'app_type', 'features'],
          },
        },

        // ===== DESIGN SYSTEM =====
        {
          name: 'create_design_system',
          description: 'Crea un design system completo con tokens, componenti e stili',
          inputSchema: {
            type: 'object',
            properties: {
              name: {
                type: 'string',
                description: 'Nome del design system',
              },
              brand_colors: {
                type: 'object',
                description: 'Colori del brand',
              },
              typography_scale: {
                type: 'array',
                items: {
                  type: 'object',
                  properties: {
                    name: { type: 'string' },
                    size: { type: 'number' },
                    weight: { type: 'string' },
                  },
                },
              },
              spacing_scale: {
                type: 'array',
                items: { type: 'number' },
                description: 'Scala di spacing (es: [4, 8, 12, 16, 24, 32])',
              },
            },
            required: ['name'],
          },
        },

        // ===== COMPONENTI UI =====
        {
          name: 'create_component_library',
          description: 'Crea una libreria di componenti UI riutilizzabili',
          inputSchema: {
            type: 'object',
            properties: {
              components: {
                type: 'array',
                items: {
                  type: 'string',
                  enum: ['button', 'input', 'card', 'modal', 'navbar', 'sidebar', 'table', 'form', 'dropdown', 'tabs', 'accordion', 'toast', 'badge', 'avatar', 'pagination'],
                },
                description: 'Lista dei componenti da creare',
              },
              variants: {
                type: 'object',
                properties: {
                  sizes: { type: 'array', items: { type: 'string' } },
                  states: { type: 'array', items: { type: 'string' } },
                  themes: { type: 'array', items: { type: 'string' } },
                },
              },
            },
            required: ['components'],
          },
        },

        // ===== PAGINE E LAYOUT =====
        {
          name: 'create_page_layouts',
          description: 'Crea layout di pagine complete per l\'applicazione',
          inputSchema: {
            type: 'object',
            properties: {
              pages: {
                type: 'array',
                items: {
                  type: 'object',
                  properties: {
                    name: { type: 'string' },
                    type: {
                      type: 'string',
                      enum: ['landing', 'dashboard', 'profile', 'settings', 'login', 'register', 'pricing', 'blog', 'contact', 'about'],
                    },
                    sections: {
                      type: 'array',
                      items: { type: 'string' },
                    },
                  },
                },
                description: 'Pagine da creare con le loro sezioni',
              },
              responsive: {
                type: 'boolean',
                default: true,
                description: 'Crea versioni responsive (desktop, tablet, mobile)',
              },
            },
            required: ['pages'],
          },
        },

        // ===== AUTO LAYOUT =====
        {
          name: 'apply_auto_layout',
          description: 'Applica auto-layout per design responsive e flessibili',
          inputSchema: {
            type: 'object',
            properties: {
              file_key: { type: 'string' },
              node_ids: {
                type: 'array',
                items: { type: 'string' },
              },
              direction: {
                type: 'string',
                enum: ['horizontal', 'vertical'],
              },
              spacing: { type: 'number' },
              padding: {
                type: 'object',
                properties: {
                  top: { type: 'number' },
                  right: { type: 'number' },
                  bottom: { type: 'number' },
                  left: { type: 'number' },
                },
              },
            },
            required: ['file_key', 'node_ids'],
          },
        },

        // ===== PROTOTIPAZIONE =====
        {
          name: 'create_interactive_prototype',
          description: 'Crea un prototipo interattivo con navigazione e animazioni',
          inputSchema: {
            type: 'object',
            properties: {
              file_key: { type: 'string' },
              flows: {
                type: 'array',
                items: {
                  type: 'object',
                  properties: {
                    from_frame: { type: 'string' },
                    to_frame: { type: 'string' },
                    trigger: {
                      type: 'string',
                      enum: ['click', 'hover', 'drag', 'keypress'],
                    },
                    animation: {
                      type: 'string',
                      enum: ['instant', 'dissolve', 'smart_animate', 'move_in', 'move_out', 'push', 'slide_in', 'slide_out'],
                    },
                    duration: { type: 'number' },
                  },
                },
              },
            },
            required: ['file_key', 'flows'],
          },
        },

        // ===== ESPORTAZIONE CODICE =====
        {
          name: 'export_to_code',
          description: 'Esporta il design completo in codice pronto per la produzione',
          inputSchema: {
            type: 'object',
            properties: {
              file_key: { type: 'string' },
              framework: {
                type: 'string',
                enum: ['react', 'vue', 'angular', 'svelte', 'html', 'react-native', 'flutter'],
                description: 'Framework target',
              },
              styling: {
                type: 'string',
                enum: ['tailwind', 'css-modules', 'styled-components', 'sass', 'emotion'],
                description: 'Sistema di styling',
              },
              include_components: { type: 'boolean', default: true },
              include_pages: { type: 'boolean', default: true },
              include_assets: { type: 'boolean', default: true },
              include_animations: { type: 'boolean', default: true },
              typescript: { type: 'boolean', default: true },
            },
            required: ['file_key', 'framework'],
          },
        },

        // ===== GESTIONE ASSETS =====
        {
          name: 'manage_assets',
          description: 'Gestisce icone, immagini e altri assets',
          inputSchema: {
            type: 'object',
            properties: {
              action: {
                type: 'string',
                enum: ['import', 'export', 'optimize', 'generate_icons'],
              },
              assets: {
                type: 'array',
                items: {
                  type: 'object',
                  properties: {
                    type: {
                      type: 'string',
                      enum: ['icon', 'image', 'logo', 'illustration'],
                    },
                    name: { type: 'string' },
                    formats: {
                      type: 'array',
                      items: {
                        type: 'string',
                        enum: ['png', 'svg', 'jpg', 'webp', 'pdf'],
                      },
                    },
                  },
                },
              },
            },
            required: ['action'],
          },
        },

        // ===== COLLABORAZIONE =====
        {
          name: 'setup_collaboration',
          description: 'Configura la collaborazione e il versioning del design',
          inputSchema: {
            type: 'object',
            properties: {
              file_key: { type: 'string' },
              action: {
                type: 'string',
                enum: ['share', 'comment', 'version', 'branch', 'merge'],
              },
              details: { type: 'object' },
            },
            required: ['file_key', 'action'],
          },
        },

        // ===== ANALISI E OTTIMIZZAZIONE =====
        {
          name: 'analyze_and_optimize',
          description: 'Analizza e ottimizza il design per performance e accessibilità',
          inputSchema: {
            type: 'object',
            properties: {
              file_key: { type: 'string' },
              checks: {
                type: 'array',
                items: {
                  type: 'string',
                  enum: ['accessibility', 'performance', 'consistency', 'responsive', 'color_contrast', 'typography', 'spacing'],
                },
              },
              auto_fix: { type: 'boolean', default: false },
            },
            required: ['file_key', 'checks'],
          },
        },
      ],
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'create_complete_ui':
            return await this.createCompleteUI(args);
          case 'create_design_system':
            return await this.createDesignSystem(args);
          case 'create_component_library':
            return await this.createComponentLibrary(args);
          case 'create_page_layouts':
            return await this.createPageLayouts(args);
          case 'apply_auto_layout':
            return await this.applyAutoLayout(args);
          case 'create_interactive_prototype':
            return await this.createInteractivePrototype(args);
          case 'export_to_code':
            return await this.exportToCode(args);
          case 'manage_assets':
            return await this.manageAssets(args);
          case 'setup_collaboration':
            return await this.setupCollaboration(args);
          case 'analyze_and_optimize':
            return await this.analyzeAndOptimize(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  async createCompleteUI(args) {
    const { app_name, app_type, features, style, color_scheme } = args;

    // Genera struttura UI completa
    const uiStructure = {
      app_name,
      app_type,
      design_system: this.generateDesignSystem(app_name, style, color_scheme),
      components: this.generateComponents(app_type, style),
      pages: this.generatePages(features, app_type),
      navigation: this.generateNavigation(features),
      responsive_breakpoints: {
        mobile: 375,
        tablet: 768,
        desktop: 1440,
      },
    };

    // Crea file Figma con API
    const figmaProject = await this.createFigmaProject(uiStructure);

    // Genera codice
    const code = await this.generateFullCode(uiStructure);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: true,
            message: `UI completa per ${app_name} creata con successo!`,
            figma_url: figmaProject.url,
            structure: uiStructure,
            code_preview: code.preview,
            next_steps: [
              '1. Apri il file Figma per vedere il design',
              '2. Usa export_to_code per ottenere il codice completo',
              '3. Personalizza componenti e stili secondo necessità',
              '4. Crea prototipo interattivo con create_interactive_prototype'
            ],
          }, null, 2),
        },
      ],
    };
  }

  async createDesignSystem(args) {
    const { name, brand_colors, typography_scale, spacing_scale } = args;

    const designSystem = {
      name,
      colors: this.generateColorPalette(brand_colors),
      typography: this.generateTypographySystem(typography_scale),
      spacing: spacing_scale || [4, 8, 12, 16, 24, 32, 48, 64],
      shadows: this.generateShadows(),
      borders: this.generateBorders(),
      animations: this.generateAnimations(),
    };

    this.currentDesignSystem = designSystem;

    // Crea stili in Figma
    await this.createFigmaStyles(designSystem);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: true,
            message: `Design System "${name}" creato con successo!`,
            design_system: designSystem,
            tokens: this.exportDesignTokens(designSystem),
          }, null, 2),
        },
      ],
    };
  }

  async createComponentLibrary(args) {
    const { components, variants } = args;

    const componentLibrary = {};

    for (const componentType of components) {
      componentLibrary[componentType] = await this.generateComponent(componentType, variants);
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: true,
            message: 'Component library creata con successo!',
            components: Object.keys(componentLibrary),
            total_variants: Object.values(componentLibrary).reduce((acc, comp) => acc + comp.variants.length, 0),
            library: componentLibrary,
          }, null, 2),
        },
      ],
    };
  }

  async createPageLayouts(args) {
    const { pages, responsive } = args;

    const layouts = {};

    for (const page of pages) {
      layouts[page.name] = await this.generatePageLayout(page, responsive);
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: true,
            message: `${pages.length} page layouts creati!`,
            pages: Object.keys(layouts),
            responsive: responsive,
            layouts: layouts,
          }, null, 2),
        },
      ],
    };
  }

  async exportToCode(args) {
    const { file_key, framework, styling, include_components, include_pages, include_assets, typescript } = args;

    // Ottieni dati dal file Figma
    const fileData = await this.axiosInstance.get(`/files/${file_key}`);

    // Genera codice basato sul framework
    const projectStructure = this.generateProjectStructure(framework, typescript);
    const components = include_components ? await this.generateComponentCode(fileData.data, framework, styling, typescript) : null;
    const pages = include_pages ? await this.generatePageCode(fileData.data, framework, styling, typescript) : null;
    const assets = include_assets ? await this.exportAssets(file_key) : null;

    // Crea package.json
    const packageJson = this.generatePackageJson(framework, styling, typescript);

    // Crea configurazione
    const config = this.generateProjectConfig(framework, styling);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: true,
            message: `Codice ${framework} generato con successo!`,
            structure: projectStructure,
            package_json: packageJson,
            config: config,
            components: components ? `${Object.keys(components).length} componenti` : 'Non inclusi',
            pages: pages ? `${Object.keys(pages).length} pagine` : 'Non incluse',
            assets: assets ? `${assets.length} assets` : 'Non inclusi',
            setup_instructions: this.getSetupInstructions(framework, styling),
          }, null, 2),
        },
      ],
    };
  }

  // ===== HELPER METHODS =====

  generateDesignSystem(appName, style, colorScheme) {
    return {
      name: `${appName} Design System`,
      colors: {
        primary: colorScheme?.primary || '#3B82F6',
        secondary: colorScheme?.secondary || '#10B981',
        accent: colorScheme?.accent || '#F59E0B',
        neutral: this.generateNeutralColors(),
        semantic: {
          success: '#10B981',
          warning: '#F59E0B',
          error: '#EF4444',
          info: '#3B82F6',
        },
      },
      typography: {
        fontFamily: style === 'corporate' ? 'Inter' : 'SF Pro Display',
        scale: [12, 14, 16, 18, 20, 24, 30, 36, 48, 60, 72],
        weights: [300, 400, 500, 600, 700, 800],
      },
      spacing: [0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128],
      borderRadius: style === 'playful' ? [8, 12, 16, 24] : [4, 6, 8, 12],
      shadows: [
        'none',
        '0 1px 3px rgba(0,0,0,0.12)',
        '0 4px 6px rgba(0,0,0,0.16)',
        '0 10px 20px rgba(0,0,0,0.19)',
        '0 14px 28px rgba(0,0,0,0.25)',
      ],
    };
  }

  generateComponents(appType, style) {
    const baseComponents = [
      'Button', 'Input', 'Select', 'Checkbox', 'Radio',
      'Card', 'Modal', 'Dropdown', 'Tabs', 'Badge',
      'Avatar', 'Toast', 'Tooltip', 'Progress', 'Spinner'
    ];

    const appSpecificComponents = {
      dashboard: ['Chart', 'Stat', 'Table', 'Sidebar', 'TopBar'],
      ecommerce: ['ProductCard', 'Cart', 'PriceTag', 'Rating', 'Filter'],
      mobile: ['BottomNav', 'SwipeCard', 'PullToRefresh', 'FAB'],
      saas: ['PricingCard', 'Feature', 'Testimonial', 'CTA', 'Hero'],
    };

    return [...baseComponents, ...(appSpecificComponents[appType] || [])];
  }

  generatePages(features, appType) {
    const pages = [];

    // Pagine base
    pages.push({ name: 'Home', path: '/', components: ['Hero', 'Features', 'CTA'] });

    // Pagine per feature
    features.forEach(feature => {
      switch (feature.toLowerCase()) {
        case 'login':
          pages.push({ name: 'Login', path: '/login', components: ['LoginForm', 'SocialAuth'] });
          pages.push({ name: 'Register', path: '/register', components: ['RegisterForm'] });
          pages.push({ name: 'ForgotPassword', path: '/forgot', components: ['PasswordReset'] });
          break;
        case 'dashboard':
          pages.push({ name: 'Dashboard', path: '/dashboard', components: ['Stats', 'Charts', 'RecentActivity'] });
          break;
        case 'profile':
          pages.push({ name: 'Profile', path: '/profile', components: ['UserInfo', 'Settings', 'Activity'] });
          break;
        case 'settings':
          pages.push({ name: 'Settings', path: '/settings', components: ['Preferences', 'Security', 'Billing'] });
          break;
        default:
          pages.push({ name: feature, path: `/${feature.toLowerCase()}`, components: [] });
      }
    });

    return pages;
  }

  generateNavigation(features) {
    return {
      main: features.map(f => ({
        label: f.charAt(0).toUpperCase() + f.slice(1),
        path: `/${f.toLowerCase()}`,
        icon: this.getIconForFeature(f),
      })),
      user: [
        { label: 'Profile', path: '/profile', icon: 'user' },
        { label: 'Settings', path: '/settings', icon: 'settings' },
        { label: 'Logout', path: '/logout', icon: 'logout' },
      ],
    };
  }

  generateColorPalette(brandColors) {
    const palette = {};

    if (brandColors) {
      Object.entries(brandColors).forEach(([key, value]) => {
        palette[key] = this.generateColorScale(value);
      });
    }

    return palette;
  }

  generateColorScale(baseColor) {
    // Genera scala di colori dal più chiaro al più scuro
    return {
      50: this.lighten(baseColor, 0.95),
      100: this.lighten(baseColor, 0.9),
      200: this.lighten(baseColor, 0.8),
      300: this.lighten(baseColor, 0.6),
      400: this.lighten(baseColor, 0.3),
      500: baseColor,
      600: this.darken(baseColor, 0.1),
      700: this.darken(baseColor, 0.2),
      800: this.darken(baseColor, 0.3),
      900: this.darken(baseColor, 0.4),
    };
  }

  generateNeutralColors() {
    return {
      50: '#FAFAFA',
      100: '#F4F4F5',
      200: '#E4E4E7',
      300: '#D4D4D8',
      400: '#A1A1AA',
      500: '#71717A',
      600: '#52525B',
      700: '#3F3F46',
      800: '#27272A',
      900: '#18181B',
    };
  }

  lighten(color, amount) {
    // Semplificato per esempio
    return color;
  }

  darken(color, amount) {
    // Semplificato per esempio
    return color;
  }

  getIconForFeature(feature) {
    const iconMap = {
      dashboard: 'grid',
      profile: 'user',
      settings: 'cog',
      login: 'lock',
      messages: 'mail',
      notifications: 'bell',
      search: 'search',
      analytics: 'chart',
    };
    return iconMap[feature.toLowerCase()] || 'folder';
  }

  generateProjectStructure(framework, typescript) {
    const ext = typescript ? 'tsx' : 'jsx';

    const structure = {
      react: {
        'src/': {
          'components/': {},
          'pages/': {},
          'styles/': {},
          'hooks/': {},
          'utils/': {},
          'assets/': {},
          [`App.${ext}`]: true,
          [`index.${typescript ? 'tsx' : 'js'}`]: true,
        },
        'public/': {},
        'package.json': true,
        'tsconfig.json': typescript,
        '.gitignore': true,
        'README.md': true,
      },
      vue: {
        'src/': {
          'components/': {},
          'views/': {},
          'assets/': {},
          'router/': {},
          'store/': {},
          'App.vue': true,
          'main.js': true,
        },
        'public/': {},
        'package.json': true,
        'vue.config.js': true,
      },
    };

    return structure[framework] || structure.react;
  }

  generatePackageJson(framework, styling, typescript) {
    const base = {
      name: 'figma-generated-app',
      version: '1.0.0',
      private: true,
      scripts: {},
      dependencies: {},
      devDependencies: {},
    };

    // Framework specifico
    switch (framework) {
      case 'react':
        base.dependencies.react = '^18.2.0';
        base.dependencies['react-dom'] = '^18.2.0';
        base.scripts.start = 'react-scripts start';
        base.scripts.build = 'react-scripts build';
        break;
      case 'vue':
        base.dependencies.vue = '^3.3.0';
        base.scripts.serve = 'vue-cli-service serve';
        base.scripts.build = 'vue-cli-service build';
        break;
    }

    // Styling
    switch (styling) {
      case 'tailwind':
        base.dependencies.tailwindcss = '^3.3.0';
        break;
      case 'styled-components':
        base.dependencies['styled-components'] = '^6.0.0';
        break;
    }

    // TypeScript
    if (typescript) {
      base.devDependencies.typescript = '^5.0.0';
      base.devDependencies['@types/react'] = framework === 'react' ? '^18.2.0' : undefined;
    }

    return base;
  }

  getSetupInstructions(framework, styling) {
    return [
      '1. Installa dipendenze: npm install',
      `2. ${framework === 'react' ? 'Avvia dev server: npm start' : 'Avvia dev server: npm run serve'}`,
      `3. ${styling === 'tailwind' ? 'Configura Tailwind CSS' : 'Stili già configurati'}`,
      '4. Personalizza componenti secondo necessità',
      '5. Deploy su Vercel/Netlify quando pronto',
    ];
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Figma UI Designer MCP Server running - Full UI Creation Enabled!');
  }
}

// Main execution
const server = new FigmaUIDesignerMCP();
server.run().catch(console.error);