# 📋 Piano di Aggiornamento MCP v2 - Non Invasivo

## Stato Attuale del Sistema

### ✅ Componenti Funzionanti
1. **Frontend (claude-ui)**
   - DashboardV2 con WorkflowView, OperationsView, MonitoringView
   - MultiTerminal che mostra tutti i 9 agent terminals
   - Hook useMCPv2 per status MCP
   - Indicatore "MCP v2 (5 capabilities)" visibile

2. **Agent Terminals (ttyd)**
   - 7 terminals attivi su porte 8090-8096
   - Visibili e funzionanti nel MultiTerminal

3. **MCP v2 Server**
   - Server compliant su porta 8099
   - WebSocket su porta 8100
   - Database SQLite funzionante
   - JSON-RPC 2.0 implementato

### 🔧 Componenti da Integrare Meglio

1. **MCP Bridge**
   - Attualmente pattern-based
   - Necessita integrazione più profonda con agent commands

2. **API Layer**
   - MCP API server su porta 5001 (se presente)
   - Necessita connessione più stretta con frontend

3. **Real-time Updates**
   - WebSocket non completamente sfruttato
   - Possibilità di aggiornamenti live mancante

## 📊 Piano di Aggiornamento Incrementale

### Fase 1: Consolidamento (Non Invasivo)
**Obiettivo**: Verificare e consolidare ciò che già funziona

1. **Verifica Servizi Attivi**
   - [ ] MCP Server v2 (porta 8099) ✓
   - [ ] WebSocket Handler (porta 8100) ✓
   - [ ] Agent Terminals (8090-8096) ✓
   - [ ] Frontend (porta 5173) ✓

2. **Documentazione Stato**
   - [ ] Mappare tutti i componenti attivi
   - [ ] Documentare le API disponibili
   - [ ] Verificare database schema

### Fase 2: Integrazione API (Additiva)
**Obiettivo**: Aggiungere funzionalità senza modificare esistente

1. **Creare Service Layer nel Frontend**
   ```typescript
   // src/services/mcpService.ts
   - Wrapper per chiamate JSON-RPC
   - Gestione errori centralizzata
   - Caching responses
   ```

2. **Aggiungere Hooks React**
   ```typescript
   // src/hooks/useMCPTools.ts
   - Lista tools disponibili
   - Esecuzione tool con dry-run

   // src/hooks/useMCPResources.ts
   - Accesso risorse MCP
   - URI scheme handler
   ```

3. **Estendere useMCPv2 esistente**
   - Aggiungere metodi per tools/resources
   - WebSocket subscription per real-time

### Fase 3: UI Components (Non Distruttivi)
**Obiettivo**: Aggiungere nuovi componenti senza toccare esistenti

1. **MCP Control Panel**
   ```typescript
   // src/components/mcp/MCPControlPanel.tsx
   - Tool executor con form dinamico
   - Resource browser
   - Prompt templates
   ```

2. **MCP Activity Stream**
   ```typescript
   // src/components/mcp/ActivityStream.tsx
   - Real-time activities via WebSocket
   - Filtrabile per agent/tipo
   ```

3. **Integrazione in Dashboard**
   - Aggiungere tab "MCP Tools" in OperationsView
   - Mantenere tutti i tab esistenti intatti

### Fase 4: Agent Enhancement (Incrementale)
**Obiettivo**: Potenziare agents senza rompere funzionalità

1. **Agent Command Wrapper**
   - Intercettare comandi agent
   - Aggiungere MCP context
   - Logging automatico activities

2. **Tool Injection**
   - Iniettare tools MCP negli agent context
   - Permettere chiamate dirette a tools

3. **State Synchronization**
   - Sincronizzare agent states con MCP database
   - Mostrare stato real-time nel frontend

### Fase 5: Testing & Validation
**Obiettivo**: Verificare che tutto funzioni

1. **Test Automatici**
   - Unit test per nuovi componenti
   - Integration test per API calls
   - E2E test per workflow completi

2. **Validation Script Update**
   - Estendere validate_mcp_v2.py
   - Verificare nuove integrazioni
   - Performance benchmarks

## 🛡️ Principi Guida

1. **NON TOCCARE** componenti funzionanti:
   - DashboardV2.tsx (solo import hook)
   - MultiTerminal.tsx esistente
   - WorkflowView, MonitoringView

2. **SEMPRE ADDITIVO**:
   - Nuovi file in nuove cartelle
   - Nuovi hooks senza modificare esistenti
   - Nuovi componenti come plugin

3. **BACKWARD COMPATIBLE**:
   - Tutto deve funzionare anche senza MCP
   - Graceful degradation se servizi offline
   - Feature flags per nuove funzioni

## 📁 Struttura File Proposta

```
claude-ui/src/
├── components/          # Esistenti - NON TOCCARE
│   ├── DashboardV2.tsx
│   ├── terminal/
│   └── views/
├── mcp/                 # NUOVO - Tutto MCP v2
│   ├── components/
│   │   ├── MCPControlPanel.tsx
│   │   ├── ActivityStream.tsx
│   │   ├── ToolExecutor.tsx
│   │   └── ResourceBrowser.tsx
│   ├── hooks/
│   │   ├── useMCPTools.ts
│   │   ├── useMCPResources.ts
│   │   └── useMCPWebSocket.ts
│   └── services/
│       ├── mcpClient.ts
│       └── mcpTypes.ts
└── hooks/              # Esistente
    └── useMCPv2.ts     # Già creato, da estendere

```

## 🚀 Implementazione Immediata

### Step 1: Creare struttura MCP
```bash
mkdir -p claude-ui/src/mcp/{components,hooks,services}
```

### Step 2: Implementare MCP Client Service
- JSON-RPC client completo
- Type definitions TypeScript
- Error handling robusto

### Step 3: Creare primo componente
- MCPStatusCard più dettagliato
- Mostra tools/resources/prompts disponibili
- Click per espandere dettagli

### Step 4: Integrare in OperationsView
- Aggiungere import del nuovo componente
- Renderizzare in sidebar o come tab

## ✅ Success Metrics

1. **Nessuna Regressione**
   - Tutti i terminal continuano a funzionare
   - Dashboard esistente invariato
   - Nessun errore in console

2. **Nuove Funzionalità**
   - Tools MCP eseguibili da UI
   - Resources browsable
   - Activities in real-time

3. **Performance**
   - Load time < 2s
   - Response time < 100ms
   - No memory leaks

## 🔄 Rollback Plan

Se qualcosa va storto:
1. Git revert dei nuovi file
2. Rimuovere import da componenti esistenti
3. Restart servizi
4. Sistema torna allo stato attuale funzionante

---

Questo piano garantisce:
- **Zero rischio** per funzionalità esistenti
- **Aggiunta incrementale** di features
- **Testing continuo** ad ogni step
- **Rollback facile** se necessario