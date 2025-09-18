# 🚀 PIANO IMPLEMENTAZIONE FINALE - Sistema Multi-Agent Completo

## 📊 STATO ATTUALE

### ✅ COSA FUNZIONA:
1. **MCP v2 Server** - 100% compliant, tutti i tool funzionanti
2. **Terminali tmux** - 9 agenti Claude attivi
3. **Comunicazione base** - I comandi arrivano agli agenti
4. **UI React** - Dashboard funzionante
5. **WebSocket** - Server attivo per real-time

### ⚠️ COSA MANCA:
1. **Agenti non rispondono automaticamente** - Richiedono input manuale
2. **Logica business mock** - I tool non eseguono azioni reali
3. **Database mock** - Nessuna persistenza reale
4. **Automazione task** - Nessuna pipeline automatica

## 🎯 IMPLEMENTAZIONE COMPLETA

### FASE 1: CONFIGURARE AGENTI AUTOMATICI (2 ore)

#### 1.1 Creare prompt di sistema per ogni agente
```python
# agent_prompts.py
AGENT_PROMPTS = {
    'supervisor': """
    Sei il Supervisor Agent. Il tuo ruolo è:
    - Ricevere task complessi e dividerli in subtask
    - Delegare task agli agenti appropriati
    - Monitorare il progresso
    - Risolvere conflitti tra agenti

    Quando ricevi un task nel formato "Task [ID]: [descrizione]":
    1. Analizza il task
    2. Identifica l'agente più adatto
    3. Delega usando il formato: "DELEGATE: [agent] - [task]"
    4. Monitora con: "STATUS: [task_id]"
    """,

    'backend-api': """
    Sei il Backend API Agent. Il tuo ruolo è:
    - Implementare endpoint REST
    - Gestire autenticazione e autorizzazione
    - Integrare con database
    - Scrivere test per le API

    Quando ricevi un task:
    1. Conferma con: "ACCEPTED: [task_id]"
    2. Pianifica l'implementazione
    3. Esegui il codice
    4. Riporta con: "COMPLETED: [task_id] - [risultato]"
    """,

    'database': """
    Sei il Database Agent. Gestisci:
    - Schema design
    - Migrations
    - Query optimization
    - Backup e recovery
    """
}
```

#### 1.2 Script di inizializzazione agenti
```bash
#!/bin/bash
# init_agents.sh

for agent in supervisor backend-api database frontend-ui testing; do
    echo "Inizializzando $agent..."
    tmux send-keys -t claude-$agent "
    Sei l'agente $agent del sistema multi-agent MCP.
    Rispondi SEMPRE ai task che ricevi.
    Formato risposte:
    - ACCEPTED: [task_id] quando ricevi un task
    - WORKING: [descrizione] mentre lavori
    - COMPLETED: [task_id] quando finisci
    - ERROR: [dettagli] se ci sono problemi
    "
    sleep 1
    tmux send-keys -t claude-$agent Enter
done
```

### FASE 2: LOGICA BUSINESS REALE (3 ore)

#### 2.1 Implementare azioni reali nei tool
```python
# mcp_real_actions.py

class RealActionExecutor:
    def __init__(self):
        self.db = sqlite3.connect('/tmp/mcp_real.db')
        self.init_database()

    def execute_register_component(self, name, owner):
        """Registra realmente un componente nel database"""
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO components (name, owner, created_at, status)
            VALUES (?, ?, ?, 'active')
        """, (name, owner, datetime.now()))
        self.db.commit()
        return cursor.lastrowid

    def execute_check_conflicts(self, agents):
        """Verifica conflitti reali nel database"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT * FROM active_tasks
            WHERE agent IN ({})
            AND component IN (
                SELECT component FROM active_tasks
                GROUP BY component
                HAVING COUNT(*) > 1
            )
        """.format(','.join(['?']*len(agents))), agents)

        conflicts = cursor.fetchall()
        return conflicts

    def execute_request_collaboration(self, from_agent, to_agent, task):
        """Crea richiesta reale e notifica l'agente"""
        # 1. Salva nel database
        request_id = self.save_collaboration_request(from_agent, to_agent, task)

        # 2. Notifica l'agente target via tmux
        subprocess.run([
            'tmux', 'send-keys', '-t', f'claude-{to_agent}',
            f'INCOMING TASK [{request_id}]: {task} (from: {from_agent})'
        ])
        subprocess.run([
            'tmux', 'send-keys', '-t', f'claude-{to_agent}', 'Enter'
        ])

        return request_id
```

### FASE 3: DATABASE REALE (2 ore)

#### 3.1 Schema database
```sql
-- schema.sql
CREATE TABLE agents (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    status TEXT,
    last_heartbeat TIMESTAMP,
    current_task TEXT,
    capabilities TEXT
);

CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP,
    assigned_to TEXT,
    created_by TEXT,
    description TEXT,
    priority TEXT,
    status TEXT,
    completed_at TIMESTAMP,
    result TEXT
);

CREATE TABLE components (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    owner TEXT,
    created_at TIMESTAMP,
    status TEXT,
    metadata TEXT
);

CREATE TABLE activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP,
    agent TEXT,
    action TEXT,
    details TEXT,
    task_id TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE conflicts (
    id INTEGER PRIMARY KEY,
    detected_at TIMESTAMP,
    agents TEXT,
    component TEXT,
    resolved BOOLEAN,
    resolution TEXT
);
```

### FASE 4: AUTOMAZIONE TASK (3 ore)

#### 4.1 Task Queue Manager
```python
# task_queue_manager.py

class TaskQueueManager:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.workers = {}
        self.results = {}

    async def add_task(self, task):
        """Aggiunge task alla coda"""
        task_id = str(uuid.uuid4())
        task['id'] = task_id
        task['status'] = 'pending'
        task['created_at'] = datetime.now()

        await self.queue.put(task)
        return task_id

    async def process_tasks(self):
        """Processa task dalla coda"""
        while True:
            task = await self.queue.get()

            # 1. Trova agente appropriato
            agent = self.find_best_agent(task)

            # 2. Assegna task
            await self.assign_to_agent(agent, task)

            # 3. Monitora progresso
            asyncio.create_task(self.monitor_task(task['id']))

    def find_best_agent(self, task):
        """Trova l'agente più adatto basato su:
        - Tipo di task
        - Carico di lavoro corrente
        - Capabilities dell'agente
        """
        task_type = task.get('type', 'general')

        agent_mapping = {
            'api': 'backend-api',
            'database': 'database',
            'ui': 'frontend-ui',
            'test': 'testing',
            'deploy': 'deployment',
            'general': 'supervisor'
        }

        return agent_mapping.get(task_type, 'supervisor')

    async def monitor_task(self, task_id):
        """Monitora il progresso del task"""
        while True:
            # Controlla stato nel database
            status = self.get_task_status(task_id)

            if status == 'completed':
                # Notifica completamento
                await self.notify_completion(task_id)
                break
            elif status == 'failed':
                # Gestisci fallimento
                await self.handle_failure(task_id)
                break

            await asyncio.sleep(5)  # Check ogni 5 secondi
```

#### 4.2 Orchestratore principale
```python
# orchestrator.py

class MasterOrchestrator:
    def __init__(self):
        self.mcp_server = MCPServerV2Full()
        self.task_queue = TaskQueueManager()
        self.agent_monitor = AgentMonitor()

    async def start(self):
        """Avvia l'orchestrazione completa"""

        # 1. Avvia MCP server
        asyncio.create_task(self.mcp_server.start())

        # 2. Avvia task processor
        asyncio.create_task(self.task_queue.process_tasks())

        # 3. Avvia agent monitor
        asyncio.create_task(self.agent_monitor.monitor_all())

        # 4. Avvia API endpoint
        await self.start_api()

    async def handle_user_request(self, request):
        """Gestisce richieste utente di alto livello"""

        # Es: "Implementa sistema di autenticazione completo"

        # 1. Analizza richiesta
        tasks = self.analyze_request(request)

        # 2. Crea task plan
        plan = {
            'tasks': [
                {'type': 'database', 'desc': 'Create users table'},
                {'type': 'api', 'desc': 'Create /auth/register endpoint'},
                {'type': 'api', 'desc': 'Create /auth/login endpoint'},
                {'type': 'api', 'desc': 'Implement JWT tokens'},
                {'type': 'test', 'desc': 'Write auth tests'},
                {'type': 'ui', 'desc': 'Create login form'},
            ],
            'dependencies': {
                1: [],
                2: [1],
                3: [1],
                4: [2, 3],
                5: [2, 3, 4],
                6: [4]
            }
        }

        # 3. Esegui plan
        await self.execute_plan(plan)
```

### FASE 5: INTEGRAZIONE COMPLETA (2 ore)

#### 5.1 Bridge MCP-Agenti bidirezionale
```python
# mcp_agent_bridge.py

class BidirectionalBridge:
    def __init__(self):
        self.mcp_to_agent = asyncio.Queue()
        self.agent_to_mcp = asyncio.Queue()

    async def start(self):
        """Avvia bridge bidirezionale"""
        asyncio.create_task(self.process_mcp_to_agent())
        asyncio.create_task(self.process_agent_to_mcp())

    async def process_mcp_to_agent(self):
        """MCP -> Agent"""
        while True:
            message = await self.mcp_to_agent.get()

            # Invia all'agente appropriato
            agent = message['target']
            command = message['command']

            # Due fasi come richiesto
            subprocess.run(['tmux', 'send-keys', '-t', f'claude-{agent}', command])
            await asyncio.sleep(0.5)
            subprocess.run(['tmux', 'send-keys', '-t', f'claude-{agent}', 'Enter'])

    async def process_agent_to_mcp(self):
        """Agent -> MCP (monitora output)"""
        while True:
            for agent in self.agents:
                output = self.capture_agent_output(agent)

                # Parsea comandi dall'agente
                if "COMPLETED:" in output:
                    task_id = self.extract_task_id(output)
                    await self.update_mcp_status(task_id, 'completed')

                elif "ERROR:" in output:
                    await self.handle_agent_error(agent, output)

            await asyncio.sleep(2)
```

## 📋 TIMELINE IMPLEMENTAZIONE

| Fase | Tempo | Priorità | Output |
|------|-------|----------|---------|
| 1. Configurare agenti automatici | 2h | ALTA | Agenti che rispondono automaticamente |
| 2. Logica business reale | 3h | ALTA | Tool che eseguono azioni reali |
| 3. Database reale | 2h | MEDIA | Persistenza dati |
| 4. Automazione task | 3h | ALTA | Pipeline automatica |
| 5. Integrazione completa | 2h | MEDIA | Sistema unificato |
| **TOTALE** | **12h** | - | **Sistema completo funzionante** |

## ✅ RISULTATO FINALE ATTESO

Un sistema dove:
1. **L'utente dice**: "Implementa autenticazione JWT"
2. **Il Supervisor**: Divide in subtask e delega
3. **Database Agent**: Crea schema users
4. **Backend Agent**: Implementa endpoint
5. **Testing Agent**: Scrive e esegue test
6. **Frontend Agent**: Crea UI login
7. **Tutto automaticamente**, con monitoring real-time nella dashboard

## 🚀 PROSSIMI PASSI IMMEDIATI

1. **Inizializzare gli agenti** con i prompt corretti
2. **Testare comunicazione** bidirezionale
3. **Implementare** almeno un tool con logica reale
4. **Verificare** che il ciclo completo funzioni