# 📋 TUTTI I MOCK DEL SISTEMA - Mappa Completa

## 🔴 MOCK CRITICI - Core System

### 1. **MCP Server - execute_tool()**
- **File**: `mcp_server_v2_full.py:524`
- **Mock attuale**: Ritorna dati fittizi per tutti gli 8 tool
- **Cosa dovrebbe fare**: Eseguire azioni reali nel database, pubblicare eventi nel message bus, aggiornare stato agenti

### 2. **MCP Server - find_component_owner()**
- **File**: `mcp_server_v2_full.py:587-588`
- **Mock attuale**: `return {'owner': 'backend-api'}` hardcoded
- **Cosa dovrebbe fare**: Query database per trovare il vero proprietario del componente

### 3. **MCP Server - read_resource()**
- **File**: `mcp_server_v2_full.py:606-615`
- **Mock attuale**: `return {'content': f"Mock content for {uri}"}`
- **Cosa dovrebbe fare**: Leggere file reali dal filesystem, caricare risorse da URL, accedere a database

### 4. **MCP Server - get_prompt()**
- **File**: `mcp_server_v2_full.py:635-641`
- **Mock attuale**: `return {'template': f'Template for {name}'}`
- **Cosa dovrebbe fare**: Caricare template reali da file o database, con variabili e logica di rendering

### 5. **API Gateway - list_tasks()**
- **File**: `api/main.py:296-297`
- **Mock attuale**: `return []` sempre vuoto
- **Cosa dovrebbe fare**: Query al sistema queue per lista task attivi, con stato, priorità, assegnazione

### 6. **API Gateway - execute_workflow()**
- **File**: `api/main.py:375-386`
- **Mock attuale**: Simula progress con sleep e emit casuali
- **Cosa dovrebbe fare**: Invocare LangGraph reale, monitorare esecuzione vera, ritornare risultati effettivi

### 7. **API Gateway - get_logs()**
- **File**: `api/main.py:631-641`
- **Mock attuale**: Genera 10 log casuali hardcoded
- **Cosa dovrebbe fare**: Aggregare log reali da tutti gli agenti, filtrarli per livello/timestamp

### 8. **API Gateway - get_messages()**
- **File**: `api/main.py:660-673`
- **Mock attuale**: Genera 5 messaggi fake
- **Cosa dovrebbe fare**: Query message bus per messaggi reali tra agenti

### 9. **API Gateway - get_queue_status()**
- **File**: `api/main.py:769-790`
- **Mock attuale**: Ritorna un task hardcoded "Process data batch"
- **Cosa dovrebbe fare**: Connettersi a Dramatiq/Redis per stato queue reale

### 10. **Unified Gateway - get_aggregated_logs()**
- **File**: `api/unified_gateway.py:321-343`
- **Mock attuale**: 50 log mock generati in loop
- **Cosa dovrebbe fare**: Aggregare da multiple fonti (file, database, stream)

## 🟠 MOCK MEDI - Monitoring & UI

### 11. **Web Interface - performance_chart()**
- **File**: `interfaces/web/web_interface.py:303-305`
- **Mock attuale**: `values = [random.randint(50, 200)]` per 30 minuti
- **Cosa dovrebbe fare**: Query Prometheus/InfluxDB per metriche reali

### 12. **Web Interface - activity_timeline()**
- **File**: `interfaces/web/web_interface.py:618-624`
- **Mock attuale**: 4 attività hardcoded
- **Cosa dovrebbe fare**: Stream eventi reali dal message bus

### 13. **Metrics Endpoint - get_throughput()**
- **File**: `api/metrics_endpoint.py:91-95`
- **Mock attuale**: `[random.randint(5, 20) for _ in range(20)]`
- **Cosa dovrebbe fare**: Calcolare throughput reale da completed tasks/tempo

### 14. **Metrics Endpoint - resource_usage()**
- **File**: `api/metrics_endpoint.py:123-127`
- **Mock attuale**: CPU/Memory/Disk tutti random
- **Cosa dovrebbe fare**: Usare psutil per metriche sistema reali

### 15. **Metrics Collector - success_rate**
- **File**: `core/metrics_collector.py:382`
- **Mock attuale**: `success_rate = 0.9` fisso
- **Cosa dovrebbe fare**: Calcolare da task completati vs falliti

### 16. **Frontend Agent - get_performance_data()**
- **File**: `agents/frontend_agent.py:485-504`
- **Mock attuale**: Array statico di response time
- **Cosa dovrebbe fare**: Query database metriche con aggregazione temporale

### 17. **MCP Performance - check_server_load()**
- **File**: `mcp_performance_v2.py:384-386`
- **Mock attuale**: Ritorna sempre 50.0 per server remoti
- **Cosa dovrebbe fare**: SSH/API call per load reale dei server

### 18. **MCP Compliant - get_user_consents()**
- **File**: `mcp_server_v2_compliant.py:238-248`
- **Mock attuale**: Un consent hardcoded user123
- **Cosa dovrebbe fare**: Query database consent con GDPR compliance

## 🟡 MOCK MINORI - Testing & Debug

### 19. **WebSocket Handler - MockMCPServer**
- **File**: `mcp_websocket_handler.py:424-426`
- **Mock attuale**: `return {"result": "ok"}` sempre
- **Cosa dovrebbe fare**: Routing a server MCP reale con gestione errori

### 20. **Debug Execution - scenarios**
- **File**: `debug_execution.py:110-117`
- **Mock attuale**: 5 scenari di output hardcoded
- **Cosa dovrebbe fare**: Dovrebbe essere rimosso in produzione

### 21. **CrewAI Integration**
- **File**: `core/crewai_real_system.py:134-136`
- **Mock attuale**: `{"error": "Anthropic API key required"}`
- **Cosa dovrebbe fare**: Integrare con CrewAI usando API key reale

### 22. **Config Settings - MOCK_CLAUDE**
- **File**: `config/settings.py:162-163`
- **Mock attuale**: Flag per modalità mock
- **Cosa dovrebbe fare**: Disabilitato in produzione

## 📊 RIEPILOGO PER COMPONENTE

### **MCP Server**
- 4 mock critici (tool, risorse, prompt, owner)
- Impatto: Nessuna azione reale viene eseguita

### **API Gateway**
- 6 mock critici (task, workflow, logs, messages, queue)
- Impatto: Nessun dato reale viene mostrato all'utente

### **Web Interface**
- 3 mock medi (charts, timeline, metrics)
- Impatto: Dashboard mostra solo dati demo

### **Monitoring**
- 4 mock medi (throughput, resources, success rate, load)
- Impatto: Nessuna metrica reale del sistema

### **Agents**
- 2 mock (performance data, CrewAI)
- Impatto: Agenti non possono operare autonomamente

## 🎯 PRIORITÀ IMPLEMENTAZIONE

### **FASE 1 - Fondamentali** (10 mock)
1. execute_tool() → azioni reali
2. list_tasks() → query queue reale
3. get_logs() → aggregazione log
4. get_messages() → message bus reale
5. find_component_owner() → database query
6. resource_usage() → psutil metriche
7. success_rate → calcolo reale
8. get_queue_status() → Dramatiq/Redis
9. execute_workflow() → LangGraph reale
10. read_resource() → file system reale

### **FASE 2 - Monitoring** (6 mock)
11. get_throughput() → calcolo da eventi
12. performance_chart() → time series DB
13. activity_timeline() → event stream
14. get_performance_data() → aggregazione DB
15. check_server_load() → monitoring remoto
16. get_user_consents() → database GDPR

### **FASE 3 - Completamento** (6 mock)
17. get_prompt() → template engine
18. get_aggregated_logs() → multi-source
19. MockMCPServer → routing reale
20. CrewAI Integration → API key
21. Debug scenarios → rimuovere
22. MOCK_CLAUDE flag → disabilitare

## 💡 IMPATTO TOTALE

- **22 mock identificati** nel sistema
- **10 critici** che bloccano funzionalità core
- **8 medi** che limitano monitoring/UI
- **4 minori** per testing/config

**Stima ore per rimozione completa**: 40-50 ore