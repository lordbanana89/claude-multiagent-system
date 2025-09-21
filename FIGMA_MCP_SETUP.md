# 🎨 FIGMA MCP SETUP COMPLETO

## ✅ CONFIGURAZIONE COMPLETATA

Ora hai **DUE** server Figma configurati:

### 1. **figma-developer** (Community)
- **Funziona SUBITO** con il tuo token API
- Non richiede Figma Desktop
- Usa direttamente l'API di Figma

### 2. **figma-dev-mode** (Ufficiale Figma)
- Richiede **Figma Desktop App** aperta
- Più potente per Dev Mode
- URL: `http://127.0.0.1:3845/mcp`

## 📋 STEPS PER ATTIVARE:

### Per usare `figma-developer` (CONSIGLIATO):
1. **Riavvia Claude Desktop**
2. Test con: `Analyze this Figma file: [URL]`

### Per usare `figma-dev-mode` (Opzionale):
1. Apri **Figma Desktop App**
2. Vai su **Menu → Preferences**
3. Abilita **"Enable local MCP Server"**
4. Riavvia Claude Desktop

## 🧪 COMANDI TEST PER CLAUDE DESKTOP:

```
# Test figma-developer (funziona subito)
Extract layout from Figma file: https://www.figma.com/file/[YOUR-FILE-ID]/[YOUR-FILE-NAME]

# Test con un file pubblico
Analyze this Figma design: https://www.figma.com/community/file/1234567890

# Genera codice da Figma
Generate React components from Figma file: [URL]

# Estrai design tokens
Extract colors and typography from Figma: [URL]
```

## ✅ COSA PUOI FARE ORA:

Con `figma-developer` MCP puoi:
- 📐 **Estrarre layout** e struttura dei componenti
- 🎨 **Ottenere stili** (colori, font, spacing)
- 🔧 **Generare codice** React/Vue/HTML dal design
- 📏 **Analizzare dimensioni** e constraints
- 🧩 **Identificare componenti** riutilizzabili

## 🔑 IL TUO TOKEN FIGMA:
```
YOUR_FIGMA_TOKEN_HERE
```

## ⚠️ TROUBLESHOOTING:

Se non funziona:
1. Verifica che il token sia valido su https://www.figma.com/developers/api
2. Riavvia Claude Desktop
3. Controlla che il file JSON sia valido:
   ```bash
   python3 -c "import json; json.load(open('/Users/erik/Library/Application Support/Claude/claude_desktop_config.json'))"
   ```

## 📝 ESEMPIO PRATICO:

Incolla questo in Claude Desktop dopo il riavvio:
```
Using the figma-developer MCP server, analyze this Figma community file:
https://www.figma.com/community/file/1251906516178548766

Extract:
1. Main layout structure
2. Color palette
3. Typography scales
4. Component hierarchy
```

---

**STATUS: ✅ PRONTO ALL'USO**

Riavvia Claude Desktop e inizia a usare Figma!