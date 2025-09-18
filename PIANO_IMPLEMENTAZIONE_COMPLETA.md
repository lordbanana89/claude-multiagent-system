# 📋 PIANO DI IMPLEMENTAZIONE COMPLETA - Sistema Multi-Agent

## 🎯 OBIETTIVO FINALE
Creare un sistema multi-agent VERAMENTE funzionante dove:
- Gli agenti eseguono task automaticamente
- Il workflow è completamente automatizzato
- I dati sono persistiti in database reale
- La comunicazione è bidirezionale e affidabile

## 📊 TIMELINE TOTALE: 

---

## FASE 1: AZIONI REALI (6 ore)
### Obiettivo: Sostituire tutti i mock con azioni reali

### 1.1 Refactor execute_tool() [2 ore]
```python
# File: mcp_server_v2_full.py

# DA CAMBIARE:
def execute_tool(self, tool_name: str, arguments: Dict) -> Dict:
    # return {"mock": "data"}  # ❌ MOCK

# A:
def execute_tool(self, tool_name: str, arguments: Dict) -> Dict:
    if tool_name == "heartbeat":
        return self.real_heartbeat(arguments)
    elif tool_name == "update_status":
        return self.real_update_status(arguments)
    # ... implementare tutti gli 8 tool
```

### 1.2 Database Schema Reale [2 ore]
```sql
-- schema.sql
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    status TEXT DEFAULT 'offline',
    last_heartbeat TIMESTAMP,
    capabilities JSON,
    current_task_id TEXT
);

CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    status TEXT NOT NULL,
    assigned_to TEXT,
    created_by TEXT,
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    payload JSON,
    result JSON,
    error TEXT,
    retry_count INTEGER DEFAULT 0
);

CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    from_agent TEXT,
    to_agent TEXT,
    type TEXT,
    content TEXT,
    timestamp TIMESTAMP,
    correlation_id TEXT,
    acknowledged BOOLEAN DEFAULT FALSE
);

CREATE TABLE collaborations (
    id TEXT PRIMARY KEY,
    from_agent TEXT,
    to_agent TEXT,
    task TEXT,
    status TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    result JSON
);
```

### 1.3 Implementazione Tool Reali [2 ore]
```python
# real_tools.py

class RealToolExecutor:
    def __init__(self):
        self.db = sqlite3.connect('mcp_system.db')
        self.message_bus = get_message_bus()

    def real_heartbeat(self, args):
        agent = args['agent']
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO agents (id, last_heartbeat, status)
            VALUES (?, datetime('now'), 'active')
        """, (agent,))
        self.db.commit()

        # Pubblica evento
        self.message_bus.publish(Event(
            type=EventType.AGENT_READY,
            source=agent
        ))

        return {"status": "alive", "timestamp": datetime.now().isoformat()}

    def real_update_status(self, args):
        # Implementazione reale...

    def real_request_collaboration(self, args):
        # Crea task reale nel database
        # Notifica agente target via message bus
        # Ritorna ID task reale
```

### Deliverables:
- [ ] 8 tool con implementazione reale
- [ ] Database SQLite funzionante
- [ ] Test per ogni tool

---

## FASE 2: MESSAGE BUS INTEGRATION (4 ore)
### Obiettivo: Collegare TUTTI i componenti al message bus centrale

### 2.1 MCP Server Integration [1 ora]
```python
# mcp_server_v2_full.py

def __init__(self):
    self.message_bus = get_message_bus()
    self.message_bus.start()

    # Sottoscrivi agli eventi
    self.message_bus.subscribe(
        EventType.TASK_CREATED,
        self.on_task_created
    )
```

### 2.2 Queue System Integration [1 ora]
```python
# start_queue_system.py

def __init__(self):
    self.message_bus = get_message_bus()

    # Pubblica eventi quando i task cambiano stato
    def on_task_complete(task):
        self.message_bus.publish(Event(
            type=EventType.TASK_COMPLETED,
            source="queue",
            payload={"task_id": task.id}
        ))
```

### 2.3 Inbox Integration [1 ora]
```python
# mcp_inbox_bridge.py

async def on_message_received(self, message):
    # Converti in evento e pubblica
    event = Event(
        type=EventType.MESSAGE_RECEIVED,
        source="inbox",
        target=message['to'],
        payload=message
    )
    self.message_bus.publish(event)
```

### 2.4 Orchestrator Integration [1 ora]
```python
# mcp_orchestrator_adapter.py

def delegate_task(self, task):
    # Pubblica evento invece di chiamata diretta
    event = Event(
        type=EventType.TASK_ASSIGNED,
        source="orchestrator",
        target=task['to_agent'],
        payload=task
    )
    self.message_bus.publish(event)
```

### Deliverables:
- [ ] Tutti i componenti pubblicano eventi
- [ ] Tutti i componenti sottoscrivono agli eventi rilevanti
- [ ] Test di comunicazione end-to-end

---

## FASE 3: AGENT RUNTIME (6 ore)
### Obiettivo: Creare agenti che rispondono automaticamente

### 3.1 Agent Base Class [2 ore]
```python
# core/agent_runtime.py

class AgentRuntime:
    """Runtime automatico per agenti"""

    def __init__(self, agent_id: str, agent_type: str):
        self.id = agent_id
        self.type = agent_type
        self.message_bus = get_message_bus()
        self.current_task = None
        self.capabilities = self.load_capabilities()

        # Sottoscrivi agli eventi
        self.subscribe_to_events()

    def subscribe_to_events(self):
        # Ascolta task assegnati a questo agente
        self.message_bus.subscribe(
            EventType.TASK_ASSIGNED,
            self.on_task_assigned,
            filter_func=lambda e: e.target == self.id
        )

    async def on_task_assigned(self, event):
        """Gestisci task assegnato"""
        task = event.payload
        self.current_task = task

        # Notifica che stiamo iniziando
        self.publish_status("busy", f"Working on {task['id']}")

        try:
            # Esegui il task
            result = await self.execute_task(task)

            # Pubblica risultato
            self.publish_task_completed(task['id'], result)

        except Exception as e:
            # Pubblica errore
            self.publish_task_failed(task['id'], str(e))

        finally:
            self.current_task = None
            self.publish_status("idle")

    async def execute_task(self, task):
        """Override in subclasses"""
        raise NotImplementedError
```

### 3.2 Specialized Agents [3 ore]
```python
# agents/backend_api_agent.py

class BackendAPIAgent(AgentRuntime):
    """Agente specializzato per backend API"""

    async def execute_task(self, task):
        task_type = task.get('type')

        if task_type == 'create_endpoint':
            return await self.create_rest_endpoint(task)
        elif task_type == 'implement_auth':
            return await self.implement_authentication(task)
        elif task_type == 'add_validation':
            return await self.add_validation_logic(task)
        else:
            # Usa LLM per task generici
            return await self.execute_with_llm(task)

    async def create_rest_endpoint(self, task):
        """Crea endpoint REST reale"""
        endpoint = task['payload']['endpoint']
        method = task['payload']['method']

        # Genera codice
        code = self.generate_endpoint_code(endpoint, method)

        # Scrivi file
        file_path = f"api/{endpoint}.py"
        with open(file_path, 'w') as f:
            f.write(code)

        # Esegui test
        test_result = await self.run_tests(file_path)

        return {
            "file": file_path,
            "code": code,
            "tests": test_result
        }
```

### 3.3 Agent Manager [1 ora]
```python
# core/agent_manager.py

class AgentManager:
    """Gestisce tutti gli agenti runtime"""

    def __init__(self):
        self.agents = {}
        self.message_bus = get_message_bus()

    def spawn_agent(self, agent_id: str, agent_type: str):
        """Crea e avvia un agente"""

        if agent_type == "backend-api":
            agent = BackendAPIAgent(agent_id, agent_type)
        elif agent_type == "database":
            agent = DatabaseAgent(agent_id, agent_type)
        elif agent_type == "frontend-ui":
            agent = FrontendAgent(agent_id, agent_type)
        else:
            agent = GenericAgent(agent_id, agent_type)

        self.agents[agent_id] = agent
        agent.start()

        return agent

    def start_all_agents(self):
        """Avvia tutti gli agenti configurati"""

        agent_configs = [
            ("backend-api", "backend-api"),
            ("database", "database"),
            ("frontend-ui", "frontend-ui"),
            ("testing", "testing"),
            ("supervisor", "supervisor")
        ]

        for agent_id, agent_type in agent_configs:
            self.spawn_agent(agent_id, agent_type)
            print(f"✅ Started agent: {agent_id}")
```

### Deliverables:
- [ ] AgentRuntime base class
- [ ] 5 specialized agents
- [ ] Agent Manager
- [ ] Auto-execution di task

---

## FASE 4: STATE MACHINE (4 ore)
### Obiettivo: Gestire workflow complessi con stati

### 4.1 Workflow State Machine [2 ore]
```python
# core/workflow_engine.py

from enum import Enum
from transitions import Machine

class WorkflowState(Enum):
    CREATED = "created"
    PLANNING = "planning"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"

class WorkflowEngine:
    """State machine per workflow complessi"""

    states = [s.value for s in WorkflowState]

    transitions = [
        {'trigger': 'start', 'source': 'created', 'dest': 'planning'},
        {'trigger': 'plan_complete', 'source': 'planning', 'dest': 'executing'},
        {'trigger': 'execution_complete', 'source': 'executing', 'dest': 'reviewing'},
        {'trigger': 'review_passed', 'source': 'reviewing', 'dest': 'completed'},
        {'trigger': 'review_failed', 'source': 'reviewing', 'dest': 'executing'},
        {'trigger': 'error', 'source': '*', 'dest': 'failed'},
    ]

    def __init__(self, workflow_id: str):
        self.id = workflow_id
        self.tasks = []
        self.current_task_index = 0
        self.results = {}

        # Initialize state machine
        self.machine = Machine(
            model=self,
            states=WorkflowEngine.states,
            transitions=WorkflowEngine.transitions,
            initial='created'
        )

    def add_task(self, task):
        """Aggiungi task al workflow"""
        self.tasks.append(task)

    def on_enter_planning(self):
        """Pianifica l'esecuzione"""
        # Analizza dipendenze
        # Ordina task
        # Assegna agenti
        self.plan_complete()

    def on_enter_executing(self):
        """Esegui i task"""
        self.execute_next_task()

    def execute_next_task(self):
        """Esegui il prossimo task"""
        if self.current_task_index < len(self.tasks):
            task = self.tasks[self.current_task_index]

            # Pubblica task per esecuzione
            event = Event(
                type=EventType.TASK_CREATED,
                source="workflow",
                payload=task
            )
            self.message_bus.publish(event)

            self.current_task_index += 1
        else:
            # Tutti i task completati
            self.execution_complete()
```

### 4.2 Dependency Resolution [2 ore]
```python
# core/dependency_resolver.py

import networkx as nx

class DependencyResolver:
    """Risolve dipendenze tra task"""

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_task(self, task_id, dependencies=[]):
        """Aggiungi task con dipendenze"""
        self.graph.add_node(task_id)
        for dep in dependencies:
            self.graph.add_edge(dep, task_id)

    def get_execution_order(self):
        """Ottieni ordine di esecuzione"""
        try:
            return list(nx.topological_sort(self.graph))
        except nx.NetworkXError:
            raise ValueError("Circular dependency detected!")

    def get_ready_tasks(self, completed_tasks):
        """Ottieni task pronti per esecuzione"""
        ready = []
        for task in self.graph.nodes():
            if task not in completed_tasks:
                # Controlla se tutte le dipendenze sono complete
                deps = list(self.graph.predecessors(task))
                if all(d in completed_tasks for d in deps):
                    ready.append(task)
        return ready
```

### Deliverables:
- [ ] State machine per workflow
- [ ] Dependency resolver
- [ ] Parallel execution support
- [ ] Rollback mechanism

---

## FASE 5: PERSISTENZA REALE (3 ore)
### Obiettivo: Database reale con migrations

### 5.1 Database Manager [1 ora]
```python
# core/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

class DatabaseManager:
    """Gestisce connessione e transazioni database"""

    def __init__(self, db_url="sqlite:///mcp_system.db"):
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.init_database()

    def init_database(self):
        """Inizializza schema database"""
        with open('schema.sql', 'r') as f:
            schema = f.read()

        with self.engine.connect() as conn:
            conn.execute(schema)
            conn.commit()

    @contextmanager
    def get_session(self):
        """Context manager per sessioni"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def save_task(self, task):
        """Salva task nel database"""
        with self.get_session() as session:
            session.execute("""
                INSERT INTO tasks (id, type, status, payload)
                VALUES (:id, :type, :status, :payload)
            """, task)

    def update_task_status(self, task_id, status, result=None, error=None):
        """Aggiorna stato task"""
        with self.get_session() as session:
            session.execute("""
                UPDATE tasks
                SET status = :status,
                    result = :result,
                    error = :error,
                    completed_at = CASE
                        WHEN :status IN ('completed', 'failed')
                        THEN datetime('now')
                        ELSE completed_at
                    END
                WHERE id = :task_id
            """, {
                'task_id': task_id,
                'status': status,
                'result': json.dumps(result) if result else None,
                'error': error
            })
```

### 5.2 Migration System [2 ore]
```python
# core/migrations.py

class MigrationManager:
    """Gestisce migrations database"""

    def __init__(self, db):
        self.db = db
        self.ensure_migration_table()

    def ensure_migration_table(self):
        """Crea tabella migrations se non esiste"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def apply_migrations(self):
        """Applica tutte le migrations pendenti"""
        current_version = self.get_current_version()
        migrations = self.get_pending_migrations(current_version)

        for version, migration in migrations:
            print(f"Applying migration {version}...")
            migration(self.db)
            self.mark_applied(version)
```

### Deliverables:
- [ ] SQLAlchemy integration
- [ ] Migration system
- [ ] Transaction support
- [ ] Backup/restore functionality

---

## FASE 6: TASK EXECUTOR (4 ore)
### Obiettivo: Esecuzione affidabile con retry

### 6.1 Task Executor [2 ore]
```python
# core/task_executor.py

class TaskExecutor:
    """Esegue task con retry e error handling"""

    def __init__(self):
        self.db = DatabaseManager()
        self.message_bus = get_message_bus()
        self.retry_policy = RetryPolicy()

    async def execute(self, task):
        """Esegue un task con gestione errori"""
        task_id = task['id']
        max_retries = task.get('max_retries', 3)

        for attempt in range(max_retries + 1):
            try:
                # Log inizio esecuzione
                self.db.update_task_status(task_id, 'running')

                # Esegui
                result = await self._execute_task(task)

                # Successo
                self.db.update_task_status(task_id, 'completed', result=result)

                # Pubblica evento successo
                self.message_bus.publish(Event(
                    type=EventType.TASK_COMPLETED,
                    source="executor",
                    payload={"task_id": task_id, "result": result}
                ))

                return result

            except Exception as e:
                # Log errore
                error_msg = f"Attempt {attempt + 1} failed: {str(e)}"

                if attempt < max_retries:
                    # Retry con backoff
                    wait_time = self.retry_policy.get_wait_time(attempt)
                    await asyncio.sleep(wait_time)
                else:
                    # Fallimento finale
                    self.db.update_task_status(task_id, 'failed', error=error_msg)

                    # Pubblica evento fallimento
                    self.message_bus.publish(Event(
                        type=EventType.TASK_FAILED,
                        source="executor",
                        payload={"task_id": task_id, "error": error_msg}
                    ))

                    raise
```

### 6.2 Retry Policy [2 ore]
```python
# core/retry_policy.py

class RetryPolicy:
    """Politiche di retry configurabili"""

    def __init__(self, base_wait=1.0, max_wait=60.0, multiplier=2.0):
        self.base_wait = base_wait
        self.max_wait = max_wait
        self.multiplier = multiplier

    def get_wait_time(self, attempt):
        """Calcola tempo di attesa (exponential backoff)"""
        wait = self.base_wait * (self.multiplier ** attempt)
        return min(wait, self.max_wait)

    def should_retry(self, error):
        """Determina se fare retry basato sull'errore"""
        # Retry su errori temporanei
        retryable_errors = [
            "ConnectionError",
            "TimeoutError",
            "TemporaryFailure"
        ]

        return any(err in str(error) for err in retryable_errors)
```

### Deliverables:
- [ ] Robust task execution
- [ ] Configurable retry policies
- [ ] Error categorization
- [ ] Dead letter queue

---

## FASE 7: RESULT AGGREGATOR (3 ore)
### Obiettivo: Aggregare e presentare risultati

### 7.1 Result Aggregator [2 ore]
```python
# core/result_aggregator.py

class ResultAggregator:
    """Aggrega risultati da multiple fonti"""

    def __init__(self):
        self.results = {}
        self.message_bus = get_message_bus()
        self.subscribe_to_results()

    def subscribe_to_results(self):
        """Sottoscrivi a eventi risultato"""
        self.message_bus.subscribe(
            EventType.TASK_COMPLETED,
            self.on_task_completed
        )

    def on_task_completed(self, event):
        """Gestisci risultato task"""
        task_id = event.payload['task_id']
        result = event.payload['result']

        # Aggrega risultato
        if 'workflow_id' in event.payload:
            workflow_id = event.payload['workflow_id']
            if workflow_id not in self.results:
                self.results[workflow_id] = {}
            self.results[workflow_id][task_id] = result

            # Controlla se workflow completo
            self.check_workflow_completion(workflow_id)

    def aggregate_workflow_results(self, workflow_id):
        """Aggrega tutti i risultati di un workflow"""
        workflow_results = self.results.get(workflow_id, {})

        return {
            'workflow_id': workflow_id,
            'total_tasks': len(workflow_results),
            'successful': sum(1 for r in workflow_results.values() if r.get('status') == 'success'),
            'failed': sum(1 for r in workflow_results.values() if r.get('status') == 'failed'),
            'results': workflow_results,
            'summary': self.generate_summary(workflow_results)
        }

    def generate_summary(self, results):
        """Genera summary leggibile"""
        # Analizza risultati e genera report
        pass
```

### 7.2 Report Generator [1 ora]
```python
# core/report_generator.py

class ReportGenerator:
    """Genera report da risultati aggregati"""

    def generate_html_report(self, aggregated_results):
        """Genera report HTML"""
        template = """
        <html>
        <body>
            <h1>Workflow Report</h1>
            <p>Total Tasks: {total_tasks}</p>
            <p>Successful: {successful}</p>
            <p>Failed: {failed}</p>
            <h2>Details</h2>
            {details}
        </body>
        </html>
        """
        return template.format(**aggregated_results)

    def generate_json_report(self, aggregated_results):
        """Genera report JSON"""
        return json.dumps(aggregated_results, indent=2)
```

### Deliverables:
- [ ] Result aggregation
- [ ] Report generation (HTML/JSON/PDF)
- [ ] Real-time dashboard updates
- [ ] Export functionality

---

## FASE 8: TESTING END-TO-END (4 ore)
### Obiettivo: Test completo del sistema

### 8.1 Integration Tests [2 ore]
```python
# tests/test_integration.py

class TestFullIntegration:
    """Test integrazione completa"""

    def test_simple_workflow(self):
        """Test workflow semplice"""
        # 1. Crea workflow
        workflow = WorkflowEngine("test_workflow")

        # 2. Aggiungi task
        workflow.add_task({
            'id': 'task1',
            'type': 'create_endpoint',
            'agent': 'backend-api',
            'payload': {'endpoint': '/test', 'method': 'GET'}
        })

        # 3. Esegui
        workflow.start()

        # 4. Attendi completamento
        result = workflow.wait_completion(timeout=60)

        # 5. Verifica
        assert result['status'] == 'completed'
        assert 'task1' in result['results']

    def test_parallel_execution(self):
        """Test esecuzione parallela"""
        # Multiple task senza dipendenze
        pass

    def test_failure_recovery(self):
        """Test recovery da fallimenti"""
        # Task che fallisce e retry
        pass
```

### 8.2 Performance Tests [1 ora]
```python
# tests/test_performance.py

class TestPerformance:
    """Test performance sistema"""

    def test_throughput(self):
        """Test throughput massimo"""
        # Invia 100 task
        # Misura tempo completamento
        pass

    def test_latency(self):
        """Test latenza comunicazione"""
        # Misura tempo message bus
        pass

    def test_concurrent_agents(self):
        """Test agenti concorrenti"""
        # 10 agenti, 100 task
        pass
```

### 8.3 Smoke Tests [1 ora]
```python
# tests/test_smoke.py

def test_all_components_running():
    """Verifica che tutti i componenti siano attivi"""

    components = [
        ("MCP Server", "http://localhost:8099/health"),
        ("Inbox API", "http://localhost:8098/api/health"),
        ("Message Bus", check_message_bus),
        ("Database", check_database),
        ("Agents", check_agents)
    ]

    for name, check in components:
        assert check(), f"{name} not running!"
```

### Deliverables:
- [ ] Integration test suite
- [ ] Performance benchmarks
- [ ] Smoke tests
- [ ] Load testing

---

## 📊 RIEPILOGO TIMELINE

| Fase | Ore | Priorità | Dipendenze |
|------|-----|----------|------------|
| 1. Azioni Reali | 6h | CRITICA | - |
| 2. Message Bus Integration | 4h | CRITICA | Fase 1 |
| 3. Agent Runtime | 6h | CRITICA | Fase 1, 2 |
| 4. State Machine | 4h | ALTA | Fase 3 |
| 5. Persistenza | 3h | ALTA | Fase 1 |
| 6. Task Executor | 4h | ALTA | Fase 3, 5 |
| 7. Result Aggregator | 3h | MEDIA | Fase 6 |
| 8. Testing | 4h | ALTA | Tutte |
| **TOTALE** | **34h** | - | - |

## 🎯 MILESTONES

### Milestone 1 (10h) - Foundation
- ✅ Azioni reali funzionanti
- ✅ Message bus integrato
- ✅ Database persistente

### Milestone 2 (20h) - Automation
- ✅ Agenti automatici
- ✅ Workflow engine
- ✅ Task execution con retry

### Milestone 3 (34h) - Production Ready
- ✅ Result aggregation
- ✅ Testing completo
- ✅ Monitoring & logging

## 🚀 RISULTATO FINALE ATTESO

Un sistema dove:
1. **Input**: "Implementa sistema di autenticazione"
2. **Processo**:
   - Supervisor divide in subtask
   - Database agent crea schema
   - Backend agent implementa API
   - Frontend agent crea UI
   - Testing agent esegue test
3. **Output**: Sistema completo funzionante con report dettagliato

**TUTTO AUTOMATICO, SENZA INTERVENTO MANUALE**