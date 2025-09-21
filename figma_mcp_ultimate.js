#!/usr/bin/env node

/**
 * Figma MCP Ultimate Bridge
 * Connette Claude Desktop con Figma (API + Desktop App)
 * Basato sul protocollo MCP ufficiale
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

class FigmaUltimateMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'figma-ultimate-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.axiosInstance = axios.create({
      baseURL: FIGMA_API_BASE,
      headers: {
        'X-Figma-Token': FIGMA_TOKEN,
      },
    });

    this.setupHandlers();
  }

  setupHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'figma_list_files',
          description: 'List all Figma files in your account',
          inputSchema: {
            type: 'object',
            properties: {
              team_id: {
                type: 'string',
                description: 'Optional team ID to filter files',
              },
            },
          },
        },
        {
          name: 'figma_get_file',
          description: 'Get detailed information about a Figma file',
          inputSchema: {
            type: 'object',
            properties: {
              file_key: {
                type: 'string',
                description: 'The file key from Figma URL (e.g., from https://www.figma.com/file/FILE_KEY/name)',
              },
            },
            required: ['file_key'],
          },
        },
        {
          name: 'figma_get_components',
          description: 'Get all components from a Figma file',
          inputSchema: {
            type: 'object',
            properties: {
              file_key: {
                type: 'string',
                description: 'The file key',
              },
            },
            required: ['file_key'],
          },
        },
        {
          name: 'figma_get_styles',
          description: 'Get all styles (colors, fonts, effects) from a Figma file',
          inputSchema: {
            type: 'object',
            properties: {
              file_key: {
                type: 'string',
                description: 'The file key',
              },
            },
            required: ['file_key'],
          },
        },
        {
          name: 'figma_get_node',
          description: 'Get specific node/frame details',
          inputSchema: {
            type: 'object',
            properties: {
              file_key: {
                type: 'string',
                description: 'The file key',
              },
              node_id: {
                type: 'string',
                description: 'The node ID (e.g., 0:1)',
              },
            },
            required: ['file_key', 'node_id'],
          },
        },
        {
          name: 'figma_export_images',
          description: 'Export images from Figma nodes',
          inputSchema: {
            type: 'object',
            properties: {
              file_key: {
                type: 'string',
                description: 'The file key',
              },
              node_ids: {
                type: 'array',
                items: { type: 'string' },
                description: 'Array of node IDs to export',
              },
              format: {
                type: 'string',
                enum: ['png', 'jpg', 'svg', 'pdf'],
                description: 'Export format',
                default: 'png',
              },
              scale: {
                type: 'number',
                description: 'Scale factor (1-4)',
                default: 1,
              },
            },
            required: ['file_key', 'node_ids'],
          },
        },
        {
          name: 'figma_to_react',
          description: 'Convert Figma design to React component',
          inputSchema: {
            type: 'object',
            properties: {
              file_key: {
                type: 'string',
                description: 'The file key',
              },
              node_id: {
                type: 'string',
                description: 'The node ID to convert',
              },
              use_tailwind: {
                type: 'boolean',
                description: 'Use Tailwind CSS classes',
                default: true,
              },
            },
            required: ['file_key', 'node_id'],
          },
        },
        {
          name: 'figma_open_desktop',
          description: 'Open a Figma file in Desktop app',
          inputSchema: {
            type: 'object',
            properties: {
              file_url: {
                type: 'string',
                description: 'Figma file URL',
              },
            },
            required: ['file_url'],
          },
        },
      ],
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'figma_list_files':
            return await this.listFiles(args);
          case 'figma_get_file':
            return await this.getFile(args);
          case 'figma_get_components':
            return await this.getComponents(args);
          case 'figma_get_styles':
            return await this.getStyles(args);
          case 'figma_get_node':
            return await this.getNode(args);
          case 'figma_export_images':
            return await this.exportImages(args);
          case 'figma_to_react':
            return await this.figmaToReact(args);
          case 'figma_open_desktop':
            return await this.openInDesktop(args);
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

  async listFiles(args) {
    const { team_id } = args;

    try {
      let files = [];

      if (team_id) {
        const response = await this.axiosInstance.get(`/teams/${team_id}/projects`);
        const projects = response.data.projects || [];

        for (const project of projects) {
          const projectFiles = await this.axiosInstance.get(`/projects/${project.id}/files`);
          files = files.concat(projectFiles.data.files || []);
        }
      } else {
        // Try to get recent files
        const response = await this.axiosInstance.get('/me');
        files = response.data.files || [];
      }

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(files, null, 2),
          },
        ],
      };
    } catch (error) {
      // If me endpoint doesn't work, provide instructions
      return {
        content: [
          {
            type: 'text',
            text: `Please provide a specific file URL or team_id. You can also use a file key directly with figma_get_file.`,
          },
        ],
      };
    }
  }

  async getFile(args) {
    const { file_key } = args;

    const response = await this.axiosInstance.get(`/files/${file_key}`);
    const file = response.data;

    // Simplify the response
    const simplified = {
      name: file.name,
      lastModified: file.lastModified,
      version: file.version,
      role: file.role,
      editorType: file.editorType,
      components: Object.keys(file.components || {}).length,
      styles: Object.keys(file.styles || {}).length,
      documentStructure: this.simplifyNode(file.document, 0, 2),
    };

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(simplified, null, 2),
        },
      ],
    };
  }

  async getComponents(args) {
    const { file_key } = args;

    const response = await this.axiosInstance.get(`/files/${file_key}/components`);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(response.data, null, 2),
        },
      ],
    };
  }

  async getStyles(args) {
    const { file_key } = args;

    const response = await this.axiosInstance.get(`/files/${file_key}/styles`);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(response.data, null, 2),
        },
      ],
    };
  }

  async getNode(args) {
    const { file_key, node_id } = args;

    const response = await this.axiosInstance.get(`/files/${file_key}/nodes`, {
      params: { ids: node_id },
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(response.data, null, 2),
        },
      ],
    };
  }

  async exportImages(args) {
    const { file_key, node_ids, format = 'png', scale = 1 } = args;

    const response = await this.axiosInstance.get(`/images/${file_key}`, {
      params: {
        ids: node_ids.join(','),
        format,
        scale,
      },
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(response.data, null, 2),
        },
      ],
    };
  }

  async figmaToReact(args) {
    const { file_key, node_id, use_tailwind = true } = args;

    // Get node data
    const response = await this.axiosInstance.get(`/files/${file_key}/nodes`, {
      params: { ids: node_id },
    });

    const nodes = response.data.nodes;
    const node = nodes[node_id];

    if (!node) {
      throw new Error('Node not found');
    }

    const componentCode = this.generateReactComponent(node.document, use_tailwind);

    return {
      content: [
        {
          type: 'text',
          text: componentCode,
        },
      ],
    };
  }

  async openInDesktop(args) {
    const { file_url } = args;

    try {
      // Try to open with Figma Desktop on macOS
      await execPromise(`open -a Figma "${file_url}"`);

      return {
        content: [
          {
            type: 'text',
            text: `Opening ${file_url} in Figma Desktop...`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `Could not open Figma Desktop. Please open manually: ${file_url}`,
          },
        ],
      };
    }
  }

  simplifyNode(node, depth = 0, maxDepth = 3) {
    if (!node || depth > maxDepth) {
      return null;
    }

    const simplified = {
      type: node.type,
      name: node.name,
    };

    if (node.children && depth < maxDepth) {
      simplified.children = node.children
        .slice(0, 5)
        .map(child => this.simplifyNode(child, depth + 1, maxDepth));
    }

    return simplified;
  }

  generateReactComponent(node, useTailwind = true) {
    const componentName = (node.name || 'Component').replace(/[^a-zA-Z0-9]/g, '');

    const styles = useTailwind ?
      this.nodesToTailwind(node) :
      this.nodesToInlineStyles(node);

    const jsx = this.nodeToJSX(node, useTailwind);

    return `import React from 'react';

const ${componentName} = () => {
  return (
    ${jsx}
  );
};

export default ${componentName};`;
  }

  nodeToJSX(node, useTailwind = true) {
    if (!node) return '<div />';

    const className = useTailwind ? this.nodesToTailwind(node) : '';
    const style = useTailwind ? {} : this.nodesToInlineStyles(node);

    if (node.type === 'TEXT') {
      return `<span className="${className}">${node.characters || ''}</span>`;
    }

    if (node.type === 'RECTANGLE' || node.type === 'FRAME') {
      const children = (node.children || [])
        .map(child => this.nodeToJSX(child, useTailwind))
        .join('\n    ');

      return `<div className="${className}">
    ${children || '/* Empty */'}
    </div>`;
    }

    return `<div className="${className}">/* ${node.type} */</div>`;
  }

  nodesToTailwind(node) {
    const classes = [];

    // Layout
    if (node.layoutMode === 'HORIZONTAL') {
      classes.push('flex', 'flex-row');
    } else if (node.layoutMode === 'VERTICAL') {
      classes.push('flex', 'flex-col');
    }

    // Spacing
    if (node.paddingLeft) {
      classes.push(`pl-${Math.round(node.paddingLeft / 4)}`);
    }
    if (node.paddingRight) {
      classes.push(`pr-${Math.round(node.paddingRight / 4)}`);
    }
    if (node.paddingTop) {
      classes.push(`pt-${Math.round(node.paddingTop / 4)}`);
    }
    if (node.paddingBottom) {
      classes.push(`pb-${Math.round(node.paddingBottom / 4)}`);
    }

    // Size
    if (node.absoluteBoundingBox) {
      const { width, height } = node.absoluteBoundingBox;
      if (width) classes.push(`w-[${Math.round(width)}px]`);
      if (height) classes.push(`h-[${Math.round(height)}px]`);
    }

    // Colors
    if (node.backgroundColor) {
      const color = this.rgbaToHex(node.backgroundColor);
      classes.push(`bg-[${color}]`);
    }

    if (node.fills && node.fills[0] && node.fills[0].color) {
      const color = this.rgbaToHex(node.fills[0].color);
      classes.push(`bg-[${color}]`);
    }

    return classes.join(' ');
  }

  nodesToInlineStyles(node) {
    const styles = {};

    if (node.absoluteBoundingBox) {
      const { width, height } = node.absoluteBoundingBox;
      if (width) styles.width = `${width}px`;
      if (height) styles.height = `${height}px`;
    }

    if (node.backgroundColor) {
      styles.backgroundColor = this.rgbaToHex(node.backgroundColor);
    }

    if (node.fills && node.fills[0] && node.fills[0].color) {
      styles.backgroundColor = this.rgbaToHex(node.fills[0].color);
    }

    return styles;
  }

  rgbaToHex(rgba) {
    if (!rgba) return '#000000';

    const r = Math.round((rgba.r || 0) * 255);
    const g = Math.round((rgba.g || 0) * 255);
    const b = Math.round((rgba.b || 0) * 255);

    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Figma Ultimate MCP Server running...');
  }
}

// Main execution
const server = new FigmaUltimateMCPServer();
server.run().catch(console.error);