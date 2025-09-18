# 🚀 Come Usare MCP con i tuoi Agenti Claude

## ✅ Setup Completato!

Abbiamo installato e configurato:
1. **MCP Python SDK** - Installato (`pip3 install mcp`)
2. **MCP Coordinator Server** - Creato (`mcp_coordinator_server.py`)
3. **Configurazione Claude** - Pronta (`claude_mcp_config.json`)

## 📋 Come Avviare il Sistema

### 1. Avvia il MCP Server
```bash
python3 mcp_coordinator_server.py
```

### 2. Configura Claude Code per Usare MCP

**Opzione A: Configurazione Globale**
```bash
# Copia la configurazione nella directory Claude
cp claude_mcp_config.json ~/.claude/mcp_config.json
```

**Opzione B: Per Sessione**
```bash
# Avvia Claude con configurazione MCP
claude --mcp-config ./claude_mcp_config.json
```

### 3. Avvia gli Agenti Claude

In ogni terminale TMUX, quando avvii Claude, sarà automaticamente connesso al coordinator:

```bash
tmux new-session -d -s claude-backend-api
tmux send-keys -t claude-backend-api "claude --mcp-config /Users/erik/Desktop/claude-multiagent-system/claude_mcp_config.json" Enter
```

## 🎯 Come Gli Agenti Usano MCP

Una volta connessi, gli agenti Claude possono usare questi comandi MCP nativamente:

### Loggare Attività
```
Use the log_activity tool to announce: "Creating user authentication endpoint"
```

### Controllare Conflitti
```
Use the check_conflicts tool to verify: "Creating users table in database"
```

### Registrare Componenti
```
Use the register_component tool: component_type="api", component_name="/users"
```

### Vedere Status Altri Agenti
```
Use the get_agent_status tool to see what other agents are doing
```

### Coordinare Decisioni
```
Use the coordinate_decision tool: "Should we use JWT or session auth?"
```

## 📊 Visualizzare il Contesto Condiviso

### Via Log File
```bash
tail -f /tmp/mcp_shared_context.log
```

### Via MCP Query
```bash
# Da qualsiasi agente Claude
Read the resource context://shared/state
```

## 🔄 Workflow Esempio

1. **Backend Agent**:
   ```
   Use check_conflicts tool: "Creating /api/users endpoint"
   → No conflicts
   Use register_component: type="api", name="/users"
   Use log_activity: "Created /api/users with POST, GET, PUT, DELETE"
   ```

2. **Database Agent**:
   ```
   Read resource context://shared/state
   → Sees backend created /api/users
   Use log_activity: "Creating users table to support /api/users endpoint"
   ```

3. **Frontend Agent**:
   ```
   Use get_agent_status tool
   → Sees both backend and database work
   Use log_activity: "Creating user form to match /api/users structure"
   ```

## ⚠️ Troubleshooting

### Se MCP non si connette:
1. Verifica che il server sia in esecuzione: `ps aux | grep mcp_coordinator`
2. Controlla i log: `tail -f /tmp/mcp_shared_context.log`
3. Verifica configurazione: `cat ~/.claude/mcp_config.json`

### Se gli agenti non vedono MCP:
1. Assicurati di avviare Claude con `--mcp-config`
2. O configura globalmente in `~/.claude/`

## ✨ Vantaggi di Questa Soluzione

1. **Nativo** - Claude Code supporta MCP nativamente
2. **Event-driven** - Nessun polling, tutto su richiesta
3. **Standard** - Protocollo ufficiale Anthropic
4. **Efficiente** - Minimo overhead
5. **Scalabile** - Può gestire molti agenti

## 🎉 Il Sistema è Pronto!

Ora i tuoi agenti Claude possono:
- 📝 Loggare le loro attività
- 👀 Vedere cosa fanno gli altri
- 🤝 Coordinarsi senza conflitti
- 🎯 Prendere decisioni condivise

**Tutto senza hack o monitoring continuo!**