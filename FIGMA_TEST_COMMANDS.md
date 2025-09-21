# 🧪 COMANDI TEST FIGMA PER CLAUDE DESKTOP

## RIAVVIA PRIMA CLAUDE DESKTOP, POI USA QUESTI COMANDI:

### TEST 1: File Figma Pubblici Funzionanti

```
# Opzione 1 - Material Design System
Analyze this Figma file: https://www.figma.com/community/file/778763161265841481

# Opzione 2 - iOS UI Kit
Extract components from: https://www.figma.com/community/file/809487622678629513

# Opzione 3 - Dashboard Template
Generate code from: https://www.figma.com/community/file/1195050839018617974
```

### TEST 2: Verifica Server Figma

```
Check if figma-developer MCP server is active and list available functions
```

### TEST 3: Se hai un tuo file Figma

```
Extract layout from my Figma file: [INCOLLA QUI L'URL DEL TUO FILE]
The API key is: YOUR_FIGMA_TOKEN_HERE
```

### TEST 4: Comando Completo

```
Using the figma-developer MCP server with API key YOUR_FIGMA_TOKEN_HERE:
1. Connect to any public Figma community file
2. Extract the main layout structure
3. List all components found
4. Generate React code for the main frame
```

## 🔍 COME TROVARE FILE FIGMA PUBBLICI:

1. Vai su https://www.figma.com/community
2. Scegli qualsiasi template gratuito
3. Copia l'URL dalla barra degli indirizzi
4. Usa l'URL in Claude Desktop

## ⚠️ FORMATO URL FIGMA:

Gli URL Figma hanno questo formato:
- Community: `https://www.figma.com/community/file/[FILE_ID]/[NAME]`
- Design: `https://www.figma.com/design/[FILE_ID]/[NAME]`
- File: `https://www.figma.com/file/[FILE_ID]/[NAME]`

## 📝 ESEMPIO SPECIFICO CHE FUNZIONA:

```
I need to analyze a Figma design. Here's what I want to do:

1. First, confirm the figma-developer MCP server is available
2. Then analyze this Material Design system: https://www.figma.com/community/file/778763161265841481
3. Extract the color palette
4. List the main components
5. Generate sample React code for a button component

My Figma API key is: YOUR_FIGMA_TOKEN_HERE
```

## ✅ RISPOSTA ATTESA:

Se funziona, Claude dovrebbe:
- Confermare che il server figma-developer è attivo
- Accedere al file Figma
- Mostrare informazioni sul layout
- Generare codice basato sul design

## ❌ SE NON FUNZIONA:

1. Verifica che hai riavviato Claude Desktop
2. Controlla il file di configurazione:
   ```bash
   cat "/Users/erik/Library/Application Support/Claude/claude_desktop_config.json" | grep figma
   ```
3. Assicurati che il server sia installato:
   ```bash
   npx figma-developer-mcp --version
   ```

---

**NOTA**: I file della Figma Community sono pubblici e gratuiti, quindi dovrebbero funzionare con il tuo token API.