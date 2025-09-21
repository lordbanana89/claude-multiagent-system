# 🔧 FIX DEFINITIVO PER MCP IN CLAUDE DESKTOP

## ⚠️ PROBLEMA IDENTIFICATO
Claude Desktop non sta caricando i server MCP dalla configurazione.

## 📍 POSSIBILI POSIZIONI CONFIG FILE:
1. `~/Library/Application Support/Claude/claude_desktop_config.json` ✅ (abbiamo provato)
2. `~/.claude/claude_desktop_config.json` ✅ (abbiamo provato)
3. `~/Library/Application Support/Claude/mcp.json` ❓
4. Configurazione interna di Claude Desktop ❓

## 🛠️ SOLUZIONE ALTERNATIVA - USA CLAUDE CLI

### 1. Installa Claude CLI (se non l'hai):
```bash
npm install -g @anthropic/claude-cli
```

### 2. Configura MCP via CLI:
```bash
# Aggiungi Figma server
claude mcp add figma-developer npx -- -y figma-developer-mcp --figma-api-key=YOUR_FIGMA_TOKEN_HERE

# Aggiungi Filesystem
claude mcp add filesystem node -- /Users/erik/Desktop/claude-multiagent-system/mcp-servers-official/src/filesystem/dist/index.js

# Aggiungi Git
claude mcp add git mcp-server-git

# Lista server configurati
claude mcp list
```

### 3. Oppure configura manualmente:

Cerca nelle **Preferenze di Claude Desktop**:
- Menu Claude → Preferences → Developer
- Cerca opzione "MCP Configuration" o "Server Configuration"
- Potrebbe esserci un'interfaccia grafica per aggiungere server

## 💡 WORKAROUND TEMPORANEO

Se Claude Desktop non vede i server MCP, puoi:

### Opzione A: Usa l'API di Figma direttamente
```python
import requests

FIGMA_TOKEN = "YOUR_FIGMA_TOKEN_HERE"
FILE_ID = "YOUR_FILE_ID"

headers = {"X-Figma-Token": FIGMA_TOKEN}
response = requests.get(f"https://api.figma.com/v1/files/{FILE_ID}", headers=headers)
```

### Opzione B: Usa un server proxy locale
```bash
# Crea un server che Claude può chiamare
python3 -m http.server 8000

# Poi in Claude puoi usare:
# fetch http://localhost:8000/figma-proxy
```

## 🔍 VERIFICA FINALE

Per verificare se MCP è attivo in Claude Desktop:

1. Apri Claude Desktop
2. Nella chat, scrivi: `#` (hashtag)
3. Se MCP funziona, vedrai un menu con i server disponibili

Se non vedi nulla:
- Claude Desktop potrebbe non supportare MCP nella tua versione
- Potrebbe richiedere un account Pro/Enterprise
- Potrebbe essere disabilitato nelle impostazioni

## 📝 CONTATTA IL SUPPORTO

Se nulla funziona, contatta il supporto Anthropic:
- https://support.anthropic.com
- Chiedi: "How to configure MCP servers in Claude Desktop?"

---

## 🚀 PIANO B - USA CLAUDE WEB + SCRIPT LOCALE

1. Crea uno script Python che usa l'API Figma:
```python
# figma_to_react.py
import sys
import requests
import json

def fetch_figma(file_url):
    token = "YOUR_FIGMA_TOKEN_HERE"
    # Extract file ID from URL
    file_id = file_url.split("/file/")[1].split("/")[0]

    headers = {"X-Figma-Token": token}
    response = requests.get(f"https://api.figma.com/v1/files/{file_id}", headers=headers)

    return response.json()

if __name__ == "__main__":
    data = fetch_figma(sys.argv[1])
    print(json.dumps(data, indent=2))
```

2. Esegui lo script e incolla l'output in Claude Web
3. Claude può generare React components dal JSON

Questo bypassa completamente il problema MCP!