# Test Plan MCP Frontend Connection

## Checklist Sistematica

### Backend (✅ Completato)
- [x] API endpoint `/api/mcp/status` su porta 5001
- [x] Database `mcp_system.db` con dati
- [x] CORS abilitato
- [x] Risposta JSON corretta

### Frontend (❓ Da verificare)
- [ ] Component `MultiTerminal.tsx` chiama porta 5001
- [ ] Parsing corretto di `agent_states`
- [ ] Mapping corretto agent name -> status
- [ ] Badge rendering con status 'active'

## Test Manuale Step-by-Step

1. **Aprire Chrome DevTools** (F12)
2. **Tab Network** - filtrare per "mcp"
3. **Tab Console** - cercare errori

## Verifica nel Browser

```javascript
// Incollare in Console:
fetch('http://localhost:5001/api/mcp/status')
  .then(r => r.json())
  .then(data => {
    console.log('Server running:', data.server_running);
    console.log('Active agents:', data.stats.active_agents);
    console.log('Agent states:', data.agent_states);

    // Check what frontend expects
    data.agent_states.forEach(agent => {
      const willShowConnected = agent.status === 'active';
      console.log(`${agent.agent}: ${willShowConnected ? '✅' : '❌'} ${agent.status}`);
    });
  });
```

## Debug React Component

```javascript
// In React DevTools:
// 1. Trova MultiTerminal component
// 2. Controlla props: agentMCPStatus
// 3. Ogni agent dovrebbe avere syncStatus: 'connected'
```

## Se ancora non funziona

1. **Hard refresh**: Cmd+Shift+R
2. **Clear localStorage**: `localStorage.clear()`
3. **Restart Vite**: Kill e restart del dev server
4. **Check per typos** nei nomi degli agenti