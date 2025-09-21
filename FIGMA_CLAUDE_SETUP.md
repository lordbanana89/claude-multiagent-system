# 🎨 FIGMA + CLAUDE DESKTOP INTEGRATION COMPLETA

## ✅ STATO: PRONTO ALL'USO!

Ho configurato un sistema COMPLETO che permette a Claude Desktop di controllare Figma per creare UI complete!

## 🏗️ ARCHITETTURA (3 COMPONENTI)

```
Claude Desktop → MCP Server → WebSocket (3055) → Figma Plugin
```

## 📦 COMPONENTI INSTALLATI

### 1. ✅ WebSocket Server (ATTIVO)
- **Porta**: 3055
- **Status**: Running
- **Path**: `figma-mcp-complete/dist/socket.js`
- **Runtime**: Bun.js

### 2. ✅ MCP Server (CONFIGURATO)
- **Nome**: talk-to-figma
- **Path**: `figma-mcp-complete/dist/talk_to_figma_mcp/server.js`
- **Config**: `/Users/erik/Library/Application Support/Claude/claude_desktop_config.json`

### 3. ✅ Figma Plugin (PRONTO)
- **Path**: `/Users/erik/Desktop/claude-multiagent-system/figma-claude-plugin/`
- **Files**:
  - `manifest.json` - Configurazione plugin
  - `code.js` - Logica plugin
  - `ui.html` - Interfaccia plugin

## 🚀 ISTRUZIONI PER ATTIVARE

### STEP 1: Installa il Plugin in Figma

1. Apri **Figma Desktop App**
2. Vai su menu **Plugins → Development → Import plugin from manifest...**
3. Seleziona il file: `/Users/erik/Desktop/claude-multiagent-system/figma-claude-plugin/manifest.json`
4. Il plugin apparirà nei tuoi plugin di sviluppo

### STEP 2: Esegui il Plugin

1. Apri un file Figma
2. Vai su **Plugins → Development → Claude Talk to Figma**
3. Si aprirà una finestra del plugin
4. Clicca **"Connect to Server"**
5. Dovresti vedere: "Connected to WebSocket server"

### STEP 3: Riavvia Claude Desktop

1. Chiudi completamente Claude Desktop
2. Riapri Claude Desktop
3. Il server MCP "talk-to-figma" sarà disponibile

## 🎯 FUNZIONALITÀ DISPONIBILI

### Creazione Elementi
- `create_rectangle` - Crea rettangoli
- `create_frame` - Crea frame/container
- `create_text` - Crea testo
- `create_component_instance` - Istanzia componenti

### Modifica Elementi
- `set_fill_color` - Cambia colore riempimento
- `set_stroke_color` - Cambia colore bordo
- `move_node` - Sposta elementi
- `resize_node` - Ridimensiona
- `set_text_content` - Modifica testo
- `set_auto_layout` - Configura auto-layout
- `set_corner_radius` - Arrotonda angoli

### Lettura/Export
- `get_document_info` - Info documento
- `get_selection` - Elementi selezionati
- `get_styles` - Stili documento
- `export_node_as_image` - Esporta immagini

## 💬 COME USARE IN CLAUDE DESKTOP

Una volta configurato, puoi dire a Claude Desktop:

```
"Crea un'interfaccia login in Figma con:
- Un frame di 400x600px
- Campo username
- Campo password
- Bottone login blu
- Testo 'Forgot password?'"
```

Claude userà il plugin per creare tutto direttamente in Figma!

## 🔧 TROUBLESHOOTING

### Se WebSocket si disconnette:
```bash
# Riavvia il server
~/.bun/bin/bun run figma-mcp-complete/dist/socket.js
```

### Se il plugin non si connette:
1. Verifica che il WebSocket sia attivo (porta 3055)
2. Nel plugin Figma, clicca "Disconnect" poi "Connect" di nuovo
3. Controlla la console del plugin (tasto destro → Inspect Plugin)

### Se Claude non vede il server:
1. Riavvia Claude Desktop completamente
2. Verifica il file di config sia corretto:
```bash
cat "/Users/erik/Library/Application Support/Claude/claude_desktop_config.json"
```

## 📝 NOTE IMPORTANTI

- Il plugin DEVE essere attivo in Figma per funzionare
- Il WebSocket server DEVE essere in esecuzione
- Claude Desktop DEVE essere riavviato dopo modifiche alla config
- Usa SOLO con file Figma di test (il plugin può modificare tutto!)

## 🎉 FATTO!

Ora hai il controllo COMPLETO di Figma da Claude Desktop!
Puoi creare UI complete, modificare design, esportare asset - tutto via AI!

---
Token Figma: `YOUR_FIGMA_TOKEN_HERE`
WebSocket Port: 3055