# 🔍 ANALISI DETTAGLIATA: execute_tool() in MCP Server

## 📋 COS'È execute_tool()?

`execute_tool()` è il **CUORE del sistema MCP** - è la funzione che viene chiamata ogni volta che un agente vuole eseguire un'azione. È come il "motore" che dovrebbe far succedere le cose nel mondo reale.

## 🎯 A COSA SERVE?

Il Model Context Protocol (MCP) definisce 8 "tool" standard che gli agenti possono usare per:
- Comunicare tra loro
- Aggiornare il proprio stato
- Coordinare attività
- Risolvere conflitti
- Proporre decisioni

Quando un agente dice "voglio eseguire il tool X con parametri Y", la richiesta arriva a `execute_tool()`.

## 🔴 PROBLEMA ATTUALE

Attualmente `execute_tool()` **NON FA NULLA DI REALE**, solo ritorna dati finti:

```python
# ESEMPIO ATTUALE (MOCK):
elif tool_name == 'heartbeat':
    return {
        'status': 'alive',
        'agent': arguments.get('agent'),
        'timestamp': timestamp
    }
# ↑ Questo dice solo "sono vivo" ma non salva nulla!
```

## ✅ COSA DOVREBBE FARE OGNI TOOL

### 1. **heartbeat** - "Sono vivo"
**Scopo**: Un agente comunica che è attivo e operativo

**Mock attuale**:
```python
return {'status': 'alive', 'agent': agent, 'timestamp': timestamp}
```

**Implementazione REALE dovrebbe**:
```python
# 1. Salvare nel database
cursor.execute("""
    UPDATE agents
    SET last_heartbeat = ?, status = 'active'
    WHERE id = ?
""", (timestamp, agent))

# 2. Pubblicare evento nel message bus
message_bus.publish(Event(
    type=EventType.AGENT_READY,
    source=agent,
    payload={'timestamp': timestamp}
))

# 3. Resettare timeout watchdog
watchdog.reset_timeout(agent)

# 4. Aggiornare metriche
metrics.increment('heartbeats_received', agent=agent)

return {
    'status': 'alive',
    'agent': agent,
    'timestamp': timestamp,
    'next_expected': timestamp + heartbeat_interval
}
```

### 2. **update_status** - "Ora sono occupato/libero"
**Scopo**: Agente cambia il suo stato (idle, busy, error, offline)

**Mock attuale**:
```python
return {'success': True, 'agent': agent, 'status': status}
```

**Implementazione REALE dovrebbe**:
```python
# 1. Validare stato
valid_states = ['idle', 'busy', 'error', 'offline']
if status not in valid_states:
    raise ValueError(f"Invalid status: {status}")

# 2. Salvare nel database con storico
cursor.execute("""
    INSERT INTO agent_status_history (agent_id, status, task, timestamp)
    VALUES (?, ?, ?, ?)
""", (agent, status, current_task, timestamp))

cursor.execute("""
    UPDATE agents
    SET status = ?, current_task = ?, last_update = ?
    WHERE id = ?
""", (status, current_task, timestamp, agent))

# 3. Se busy -> assegnare task
if status == 'busy' and current_task:
    cursor.execute("""
        UPDATE tasks
        SET assigned_to = ?, status = 'in_progress'
        WHERE id = ?
    """, (agent, current_task))

# 4. Pubblicare evento
message_bus.publish(Event(
    type=EventType.AGENT_STATUS_CHANGED,
    source=agent,
    payload={'status': status, 'task': current_task}
))

# 5. Notificare supervisor se error
if status == 'error':
    notify_supervisor(agent, error_details)

return {
    'success': True,
    'agent': agent,
    'status': status,
    'previous_status': old_status,
    'task_assigned': current_task
}
```

### 3. **log_activity** - "Ho fatto questa cosa"
**Scopo**: Registrare un'attività completata

**Mock attuale**:
```python
return {'logged': True, 'id': uuid, 'timestamp': timestamp}
```

**Implementazione REALE dovrebbe**:
```python
# 1. Salvare log strutturato
activity_id = str(uuid.uuid4())
cursor.execute("""
    INSERT INTO activity_logs
    (id, agent, category, activity, details, timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
""", (activity_id, agent, category, activity, json.dumps(details), timestamp))

# 2. Aggiornare contatori
if category == 'task':
    metrics.increment('tasks_processed', agent=agent)
elif category == 'error':
    metrics.increment('errors_logged', agent=agent)

# 3. Triggerare alert se necessario
if category == 'error' and severity == 'critical':
    alert_manager.trigger('critical_error', agent, details)

# 4. Aggiungere a audit trail
audit_logger.log(agent, activity, request_context)

# 5. Stream a dashboard real-time
websocket.broadcast({
    'type': 'activity',
    'agent': agent,
    'activity': activity,
    'timestamp': timestamp
})

return {
    'logged': True,
    'id': activity_id,
    'timestamp': timestamp,
    'indexed': True,
    'alerts_triggered': alerts
}
```

### 4. **check_conflicts** - "C'è conflitto tra agenti?"
**Scopo**: Verificare se più agenti stanno lavorando sulla stessa cosa

**Mock attuale**:
```python
return {'conflicts': [], 'agents_checked': agents}
```

**Implementazione REALE dovrebbe**:
```python
# 1. Query task assegnati
cursor.execute("""
    SELECT t.id, t.component, t.assigned_to, a.status
    FROM tasks t
    JOIN agents a ON t.assigned_to = a.id
    WHERE t.assigned_to IN ({})
    AND t.status = 'in_progress'
""".format(','.join(['?']*len(agents))), agents)

tasks = cursor.fetchall()

# 2. Trovare conflitti reali
conflicts = []
component_agents = {}

for task in tasks:
    component = task['component']
    agent = task['assigned_to']

    if component in component_agents:
        # CONFLITTO! Due agenti sullo stesso componente
        conflicts.append({
            'type': 'component_conflict',
            'component': component,
            'agents': [component_agents[component], agent],
            'severity': 'high'
        })
    else:
        component_agents[component] = agent

# 3. Verificare conflitti di risorse
resource_conflicts = check_resource_locks(agents)
conflicts.extend(resource_conflicts)

# 4. Se ci sono conflitti, notificare supervisor
if conflicts:
    message_bus.publish(Event(
        type=EventType.CONFLICT_DETECTED,
        source='conflict_checker',
        payload={'conflicts': conflicts}
    ))

return {
    'conflicts': conflicts,
    'agents_checked': agents,
    'components_analyzed': len(component_agents),
    'resolution_needed': len(conflicts) > 0
}
```

### 5. **register_component** - "Ho creato questo componente"
**Scopo**: Registrare un nuovo componente creato da un agente

**Mock attuale**:
```python
return {'registered': True, 'component': name, 'owner': owner}
```

**Implementazione REALE dovrebbe**:
```python
# 1. Verificare unicità
existing = cursor.execute(
    "SELECT id FROM components WHERE name = ?", (name,)
).fetchone()

if existing:
    raise ValueError(f"Component {name} already exists")

# 2. Registrare nel database
component_id = str(uuid.uuid4())
cursor.execute("""
    INSERT INTO components
    (id, name, type, owner, created_at, status, metadata)
    VALUES (?, ?, ?, ?, ?, 'active', ?)
""", (component_id, name, type, owner, timestamp, json.dumps(metadata)))

# 3. Creare struttura file/directory se necessario
if type == 'module':
    os.makedirs(f"components/{name}", exist_ok=True)
    create_component_structure(name, metadata)

# 4. Registrare dipendenze
for dep in dependencies:
    cursor.execute("""
        INSERT INTO component_dependencies (component_id, depends_on)
        VALUES (?, ?)
    """, (component_id, dep))

# 5. Notificare altri agenti
message_bus.publish(Event(
    type=EventType.COMPONENT_CREATED,
    source=owner,
    payload={
        'component_id': component_id,
        'name': name,
        'type': type
    }
))

# 6. Aggiornare grafo dipendenze
dependency_graph.add_node(component_id, name, dependencies)

return {
    'registered': True,
    'component_id': component_id,
    'name': name,
    'owner': owner,
    'dependencies_registered': len(dependencies),
    'files_created': files_created
}
```

### 6. **request_collaboration** - "Ho bisogno di aiuto"
**Scopo**: Un agente richiede aiuto da un altro

**Mock attuale**:
```python
return {'request_id': uuid, 'status': 'pending', 'from': from_agent, 'to': to_agent}
```

**Implementazione REALE dovrebbe**:
```python
# 1. Creare richiesta nel database
request_id = str(uuid.uuid4())
cursor.execute("""
    INSERT INTO collaboration_requests
    (id, from_agent, to_agent, task, priority, status, created_at, metadata)
    VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
""", (request_id, from_agent, to_agent, task, priority, timestamp, json.dumps(metadata)))

# 2. Verificare disponibilità agente target
target_status = cursor.execute(
    "SELECT status, current_task FROM agents WHERE id = ?", (to_agent,)
).fetchone()

# 3. Auto-accettare se agente è idle
if target_status['status'] == 'idle':
    cursor.execute("""
        UPDATE collaboration_requests
        SET status = 'accepted', accepted_at = ?
        WHERE id = ?
    """, (timestamp, request_id))

    # Assegnare task
    cursor.execute("""
        UPDATE agents
        SET status = 'busy', current_task = ?
        WHERE id = ?
    """, (task, to_agent))

    status = 'accepted'
else:
    # Aggiungere a coda
    cursor.execute("""
        INSERT INTO agent_queues (agent_id, request_id, priority)
        VALUES (?, ?, ?)
    """, (to_agent, request_id, priority))

    status = 'queued'

# 4. Notificare agente target
message_bus.publish(Event(
    type=EventType.COLLABORATION_REQUEST,
    source=from_agent,
    target=to_agent,
    payload={
        'request_id': request_id,
        'task': task,
        'priority': priority
    }
))

# 5. Inviare a terminale tmux se configurato
if tmux_enabled:
    send_to_tmux(to_agent, f"[TASK {request_id}] {task} (from: {from_agent})")

return {
    'request_id': request_id,
    'status': status,
    'from': from_agent,
    'to': to_agent,
    'queue_position': queue_position if status == 'queued' else None,
    'estimated_start': estimated_start_time
}
```

### 7. **propose_decision** - "Propongo questa soluzione"
**Scopo**: Proporre una decisione che richiede consenso

**Mock attuale**:
```python
return {'decision_id': uuid, 'status': 'proposed', 'category': category}
```

**Implementazione REALE dovrebbe**:
```python
# 1. Creare proposta
decision_id = str(uuid.uuid4())
cursor.execute("""
    INSERT INTO decisions
    (id, proposed_by, decision, category, confidence, alternatives,
     status, created_at, metadata)
    VALUES (?, ?, ?, ?, ?, ?, 'proposed', ?, ?)
""", (decision_id, agent, decision, category, confidence,
      json.dumps(alternatives), timestamp, json.dumps(metadata)))

# 2. Determinare chi deve votare
if category == 'architecture':
    voters = get_senior_agents()
elif category == 'deployment':
    voters = ['deployment', 'testing', 'supervisor']
else:
    voters = get_affected_agents(decision)

# 3. Creare voti pendenti
for voter in voters:
    cursor.execute("""
        INSERT INTO decision_votes
        (decision_id, agent_id, status, weight)
        VALUES (?, ?, 'pending', ?)
    """, (decision_id, voter, get_agent_weight(voter)))

# 4. Se confidence alta, auto-approvare
if confidence >= 0.95 and risk_level == 'low':
    cursor.execute("""
        UPDATE decisions
        SET status = 'auto_approved', approved_at = ?
        WHERE id = ?
    """, (timestamp, decision_id))

    execute_decision(decision_id)
    status = 'auto_approved'
else:
    # Notificare voters
    for voter in voters:
        message_bus.publish(Event(
            type=EventType.DECISION_PENDING,
            target=voter,
            payload={'decision_id': decision_id, 'decision': decision}
        ))
    status = 'pending_votes'

return {
    'decision_id': decision_id,
    'status': status,
    'category': category,
    'voters': voters,
    'required_votes': required_votes,
    'auto_approved': status == 'auto_approved'
}
```

### 8. **find_component_owner** - "Chi gestisce questo?"
**Scopo**: Trovare quale agente è responsabile di un componente

**Mock attuale**:
```python
return {'component': component, 'owner': 'backend-api'}  # SEMPRE backend-api!
```

**Implementazione REALE dovrebbe**:
```python
# 1. Cercare nel database
result = cursor.execute("""
    SELECT c.owner, c.type, c.status, a.status as agent_status
    FROM components c
    LEFT JOIN agents a ON c.owner = a.id
    WHERE c.name = ? OR c.id = ?
""", (component, component)).fetchone()

if not result:
    # 2. Provare pattern matching
    patterns = {
        r'.*\.(jsx?|tsx?)$': 'frontend-ui',
        r'.*\.(py|api)$': 'backend-api',
        r'.*\.(sql|db)$': 'database',
        r'.*test.*': 'testing',
        r'.*deploy.*': 'deployment'
    }

    for pattern, default_owner in patterns.items():
        if re.match(pattern, component):
            owner = default_owner
            break
    else:
        owner = 'supervisor'  # Default al supervisor

    # Registrare per futuri lookup
    cursor.execute("""
        INSERT INTO components (name, owner, type, created_at)
        VALUES (?, ?, 'inferred', ?)
    """, (component, owner, timestamp))
else:
    owner = result['owner']

# 3. Verificare se owner è disponibile
if result and result['agent_status'] != 'active':
    # Trovare backup owner
    backup = find_backup_owner(component, result['type'])

    return {
        'component': component,
        'owner': owner,
        'owner_status': result['agent_status'],
        'backup_owner': backup,
        'reassignment_needed': True
    }

# 4. Aggiornare cache per performance
cache.set(f"owner:{component}", owner, ttl=3600)

return {
    'component': component,
    'owner': owner,
    'type': result['type'] if result else 'inferred',
    'status': result['status'] if result else 'unknown',
    'agent_available': result['agent_status'] == 'active' if result else True
}
```

## 🔧 COMPONENTI DA INTEGRARE

Per far funzionare `execute_tool()` servono:

### 1. **Database SQLite/PostgreSQL**
```python
# Connessione database
self.db = sqlite3.connect('mcp_system.db')
```

### 2. **Message Bus**
```python
# Per pubblicare eventi
from core.message_bus import get_message_bus
self.message_bus = get_message_bus()
```

### 3. **Metrics Collector**
```python
# Per tracciare metriche
from core.metrics import MetricsCollector
self.metrics = MetricsCollector()
```

### 4. **Alert Manager**
```python
# Per gestire alert critici
from core.alerts import AlertManager
self.alerts = AlertManager()
```

### 5. **WebSocket Broadcaster**
```python
# Per aggiornamenti real-time
from core.websocket import WebSocketManager
self.ws = WebSocketManager()
```

### 6. **Tmux Integration**
```python
# Per comunicare con terminali
from core.tmux_client import TMUXClient
self.tmux = TMUXClient()
```

## 📊 IMPATTO DELLA CORREZIONE

Implementando `execute_tool()` correttamente:

✅ **Gli agenti potranno**:
- Comunicare veramente tra loro
- Salvare stato persistente
- Coordinare task complessi
- Risolvere conflitti automaticamente

❌ **Senza questa correzione**:
- Tutto è solo simulazione
- Nessun dato viene salvato
- Nessuna comunicazione reale
- Sistema completamente inutile

## 🎯 PRIORITÀ

**Questa è la correzione PIÙ IMPORTANTE del sistema** perché:
1. Tutto passa da qui
2. Senza questo, gli agenti sono "ciechi e sordi"
3. È il ponte tra intenzione e azione

**Tempo stimato**: 6-8 ore per implementare tutti gli 8 tool correttamente