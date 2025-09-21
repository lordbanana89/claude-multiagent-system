#!/usr/bin/env node

/**
 * FIGMA VISUAL FEEDBACK SYSTEM
 * Estende il plugin Figma per fornire screenshot in realtime
 * Da aggiungere al plugin Figma esistente
 */

// Questo codice va aggiunto al file code.js del plugin Figma
const FIGMA_PLUGIN_EXTENSION = `

// VISUAL FEEDBACK EXTENSION
// Aggiunge la capacità di esportare screenshot dei nodi

// Funzione per esportare nodo come immagine
async function exportNodeAsImage(nodeId) {
  try {
    const node = figma.getNodeById(nodeId);
    if (!node) {
      return { error: 'Node not found' };
    }

    // Esporta il nodo come PNG
    const bytes = await node.exportAsync({
      format: 'PNG',
      constraint: { type: 'SCALE', value: 1 }
    });

    // Converti in base64 per il trasferimento
    const base64 = uint8ArrayToBase64(bytes);

    return {
      nodeId: nodeId,
      nodeName: node.name,
      type: node.type,
      width: node.width,
      height: node.height,
      image: base64
    };
  } catch (error) {
    return { error: error.message };
  }
}

// Funzione per esportare l'intera pagina
async function exportCurrentView() {
  try {
    // Ottieni tutti i nodi di primo livello
    const nodes = figma.currentPage.children;
    if (nodes.length === 0) {
      return { error: 'No nodes on page' };
    }

    // Esporta il primo frame principale (di solito il container)
    const mainFrame = nodes.find(n => n.type === 'FRAME');
    if (!mainFrame) {
      return { error: 'No frame found' };
    }

    const bytes = await mainFrame.exportAsync({
      format: 'PNG',
      constraint: { type: 'SCALE', value: 0.5 } // Scala ridotta per velocità
    });

    const base64 = uint8ArrayToBase64(bytes);

    return {
      pageId: figma.currentPage.id,
      pageName: figma.currentPage.name,
      frameId: mainFrame.id,
      frameName: mainFrame.name,
      width: mainFrame.width,
      height: mainFrame.height,
      image: base64
    };
  } catch (error) {
    return { error: error.message };
  }
}

// Helper per convertire Uint8Array in base64
function uint8ArrayToBase64(bytes) {
  let binary = '';
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

// Aggiungi comando per screenshot al message handler esistente
// Nel tuo switch statement per i comandi, aggiungi:
case 'export_node':
  const exportResult = await exportNodeAsImage(msg.params.nodeId);
  figma.ui.postMessage({
    id: msg.id,
    result: exportResult
  });
  break;

case 'export_view':
  const viewResult = await exportCurrentView();
  figma.ui.postMessage({
    id: msg.id,
    result: viewResult
  });
  break;

case 'get_visual_feedback':
  // Esporta automaticamente dopo ogni operazione
  const feedback = await exportCurrentView();
  figma.ui.postMessage({
    id: msg.id,
    type: 'visual_feedback',
    result: feedback
  });
  break;

`;

// Server Node.js per ricevere e salvare gli screenshot
const express = require('express');
const fs = require('fs').promises;
const path = require('path');

class FigmaVisualServer {
  constructor(port = 8888) {
    this.port = port;
    this.app = express();
    this.screenshots = new Map();
    this.setupRoutes();
  }

  setupRoutes() {
    this.app.use(express.json({ limit: '50mb' }));
    this.app.use(express.static('public'));

    // Endpoint per ricevere screenshot dal plugin
    this.app.post('/screenshot', async (req, res) => {
      const { nodeId, image, metadata } = req.body;

      if (!image) {
        return res.status(400).json({ error: 'No image data' });
      }

      try {
        // Salva lo screenshot
        const filename = `screenshot_${Date.now()}.png`;
        const filepath = path.join(__dirname, 'screenshots', filename);

        // Crea directory se non esiste
        await fs.mkdir(path.join(__dirname, 'screenshots'), { recursive: true });

        // Decodifica base64 e salva
        const buffer = Buffer.from(image, 'base64');
        await fs.writeFile(filepath, buffer);

        // Salva metadata
        this.screenshots.set(nodeId || 'latest', {
          filename,
          filepath,
          metadata,
          timestamp: Date.now()
        });

        console.log(`📸 Screenshot salvato: ${filename}`);
        res.json({ success: true, filename });
      } catch (error) {
        console.error('Errore salvataggio screenshot:', error);
        res.status(500).json({ error: error.message });
      }
    });

    // Endpoint per visualizzare ultimo screenshot
    this.app.get('/latest', (req, res) => {
      const latest = this.screenshots.get('latest');
      if (!latest) {
        return res.status(404).json({ error: 'No screenshots available' });
      }
      res.sendFile(latest.filepath);
    });

    // Pagina HTML per visualizzare screenshot in realtime
    this.app.get('/', (req, res) => {
      res.send(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>Figma Visual Feedback</title>
          <style>
            body {
              font-family: sans-serif;
              background: #1a1a1a;
              color: white;
              padding: 20px;
            }
            #preview {
              max-width: 100%;
              border: 2px solid #333;
              border-radius: 8px;
              margin: 20px 0;
            }
            .status {
              padding: 10px;
              background: #2a2a2a;
              border-radius: 4px;
              margin: 10px 0;
            }
          </style>
        </head>
        <body>
          <h1>🎨 Figma Visual Feedback</h1>
          <div class="status" id="status">Waiting for screenshots...</div>
          <img id="preview" />
          <script>
            // Polling per nuovo screenshot ogni 2 secondi
            setInterval(async () => {
              try {
                const img = document.getElementById('preview');
                img.src = '/latest?' + Date.now();
                document.getElementById('status').textContent = 'Updated: ' + new Date().toLocaleTimeString();
              } catch (e) {
                console.error('Error loading screenshot:', e);
              }
            }, 2000);
          </script>
        </body>
        </html>
      `);
    });
  }

  start() {
    this.app.listen(this.port, () => {
      console.log(`🖼️ Visual Feedback Server running at http://localhost:${this.port}`);
      console.log(`📸 Screenshots will be saved in ./screenshots/`);
    });
  }
}

// Script per integrare con il sistema esistente
const WebSocket = require('ws');

async function requestScreenshot(channel = '5utu5pn0') {
  const ws = new WebSocket('ws://localhost:3055');

  return new Promise((resolve, reject) => {
    ws.on('open', () => {
      ws.send(JSON.stringify({
        type: 'join',
        channel
      }));

      setTimeout(() => {
        // Richiedi screenshot
        ws.send(JSON.stringify({
          id: 'screenshot-' + Date.now(),
          type: 'message',
          channel,
          message: {
            id: 'screenshot-req',
            command: 'export_view',
            params: {}
          }
        }));
      }, 500);
    });

    ws.on('message', (data) => {
      const msg = JSON.parse(data);
      if (msg.message && msg.message.result && msg.message.result.image) {
        // Invia screenshot al server
        fetch('http://localhost:8888/screenshot', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            nodeId: msg.message.result.frameId,
            image: msg.message.result.image,
            metadata: msg.message.result
          })
        }).then(() => {
          console.log('✅ Screenshot inviato al server');
          resolve();
        }).catch(reject);

        ws.close();
      }
    });

    ws.on('error', reject);
  });
}

// Main
if (require.main === module) {
  console.log('═══════════════════════════════════════');
  console.log('  FIGMA VISUAL FEEDBACK SYSTEM');
  console.log('═══════════════════════════════════════\n');

  console.log('📝 ISTRUZIONI PER INTEGRARE NEL PLUGIN:\n');
  console.log('1. Apri il file code.js del plugin Figma');
  console.log('2. Aggiungi il codice dalla variabile FIGMA_PLUGIN_EXTENSION');
  console.log('3. Ricarica il plugin in Figma\n');

  console.log('🚀 AVVIO SERVER VISUAL FEEDBACK...\n');

  // Avvia server
  const server = new FigmaVisualServer();
  server.start();

  // Test screenshot ogni 5 secondi
  setInterval(() => {
    console.log('📸 Richiedo screenshot...');
    requestScreenshot().catch(console.error);
  }, 5000);
}

module.exports = { FigmaVisualServer, requestScreenshot };