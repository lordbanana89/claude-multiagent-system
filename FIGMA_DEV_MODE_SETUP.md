# 🎨 FIGMA DEV MODE MCP - SETUP COMPLETO

## ✅ STEP 1: ABILITA IN FIGMA DESKTOP

1. **Apri Figma Desktop App** (non il browser!)
2. **Menu Figma** → **Preferences** (⌘,)
3. Cerca **"Enable local MCP Server"**
4. **Abilita** il toggle
5. Dovresti vedere: **"MCP server enabled and running"** in basso

## ✅ STEP 2: VERIFICA CHE SIA ATTIVO

Apri Terminal e testa:
```bash
curl http://127.0.0.1:3845/mcp
```

Se risponde, il server è attivo!

## ✅ STEP 3: RIAVVIA CLAUDE DESKTOP

La configurazione è già pronta con `figma-dev-mode` server.

## 📝 STEP 4: USA FIGMA DEV MODE IN CLAUDE

### Comandi da usare in Claude Desktop:

```
# 1. Apri un file Figma nell'app Desktop
# 2. Seleziona un frame o componente
# 3. In Claude Desktop scrivi:

Get the selected Figma frame and generate React code

# Oppure:

Analyze the current Figma file structure

# O ancora:

Extract design tokens from the open Figma file
```

## 🔧 FUNZIONALITÀ FIGMA DEV MODE:

Con Figma Dev Mode puoi:
- 📐 **get_code** - Genera codice dal frame selezionato
- 🎨 **get_design_tokens** - Estrai variabili, colori, font
- 🧩 **get_components** - Ottieni tutti i componenti
- 📏 **get_layout** - Analizza layout e constraints
- 🔗 **get_code_connect** - Usa Code Connect per componenti reali

## ⚠️ IMPORTANTE:

1. **Figma Desktop DEVE essere aperto**
2. **Devi avere un file Figma aperto**
3. **Devi selezionare un frame/componente**
4. Il server gira su `http://127.0.0.1:3845/mcp`

## 🧪 TEST COMPLETO:

1. Apri Figma Desktop
2. Apri questo file di esempio:
   https://www.figma.com/community/file/1248919208161617387

3. Seleziona un componente

4. In Claude Desktop:
```
Using Figma Dev Mode, get the selected component and generate:
1. React component with TypeScript
2. Tailwind CSS classes
3. Responsive design
4. Accessibility attributes
```

## 🚀 WORKFLOW OTTIMALE:

1. **Designer crea in Figma**
2. **Developer apre in Figma Desktop**
3. **Seleziona frame da implementare**
4. **Claude genera il codice**
5. **Copia nel progetto**

## ❓ TROUBLESHOOTING:

Se non funziona:
- Verifica che Figma Desktop sia aperto
- Controlla Preferences → Enable local MCP Server
- Riavvia Figma Desktop
- Riavvia Claude Desktop
- Verifica: `curl http://127.0.0.1:3845/mcp`

---

**STATUS**: Configurazione completata! Ora testa con Figma Desktop aperto.