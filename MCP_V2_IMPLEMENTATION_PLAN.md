# 🚀 Piano di Implementazione Completa MCP v2

## 📊 Stato Attuale: 38.9% → Target: 100%

## 🎯 Obiettivi Prioritari

### FASE 1: FIX CRITICI (38.9% → 70%)
**Timeline: Immediato**

#### 1.1 Fix dei 6 Tool MCP con errori
```python
# PROBLEMA: Validazione parametri fallisce
# SOLUZIONE: Pulire parametri prima dell'invio

def clean_tool_params(tool_name: str, params: Dict) -> Dict:
    """Rimuove parametri non validi per ogni tool"""

    TOOL_SCHEMAS = {
        'log_activity': ['agent', 'activity', 'category', 'status', 'details', 'dry_run'],
        'check_conflicts': ['agents', 'dry_run'],
        'register_component': ['name', 'owner', 'status', 'metadata', 'dry_run'],
        'request_collaboration': ['from_agent', 'to_agent', 'task', 'priority', 'dry_run'],
        'propose_decision': ['category', 'question', 'proposed_by', 'metadata', 'dry_run'],
        'find_component_owner': ['component', 'dry_run']
    }

    valid_params = TOOL_SCHEMAS.get(tool_name, [])
    return {k: v for k, v in params.items() if k in valid_params}
```

#### 1.2 Session Management Reale
```python
# PROBLEMA: Nessuna gestione sessioni
# SOLUZIONE: Database sessioni in memoria

import sqlite3
from datetime import datetime, timedelta

class SessionManager:
    def __init__(self):
        self.conn = sqlite3.connect(':memory:')
        self.setup_db()

    def setup_db(self):
        self.conn.execute('''
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                client_name TEXT,
                created_at TIMESTAMP,
                last_activity TIMESTAMP,
                capabilities TEXT,
                metadata TEXT
            )
        ''')

    def create_session(self, client_info: Dict) -> str:
        session_id = str(uuid.uuid4())
        self.conn.execute(
            'INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?)',
            (session_id, client_info.get('name'),
             datetime.now(), datetime.now(),
             json.dumps(client_info.get('capabilities', [])),
             json.dumps(client_info))
        )
        return session_id

    def validate_session(self, session_id: str) -> bool:
        cursor = self.conn.execute(
            'SELECT * FROM sessions WHERE id = ? AND last_activity > ?',
            (session_id, datetime.now() - timedelta(hours=1))
        )
        return cursor.fetchone() is not None
```

### FASE 2: IMPLEMENTAZIONI CORE (70% → 85%)
**Timeline: 2 ore**

#### 2.1 Resources Reali
```python
# PROBLEMA: Resources sono mock
# SOLUZIONE: Implementare accesso reale a file

class ResourceManager:
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.resources = {}
        self.scan_resources()

    def scan_resources(self):
        """Scansiona il progetto per risorse disponibili"""
        for file in self.project_dir.rglob('*'):
            if file.is_file():
                uri = f"file://{file.relative_to(self.project_dir)}"
                self.resources[uri] = {
                    'uri': uri,
                    'name': file.name,
                    'type': self._get_mime_type(file),
                    'size': file.stat().st_size,
                    'modified': file.stat().st_mtime
                }

    def list_resources(self) -> List[Dict]:
        return list(self.resources.values())

    def read_resource(self, uri: str) -> Dict:
        if uri not in self.resources:
            raise ValueError(f"Resource not found: {uri}")

        path = self.project_dir / uri.replace('file://', '')
        content = path.read_text() if path.suffix in ['.txt', '.md', '.py', '.js'] else None

        return {
            'uri': uri,
            'content': content,
            'metadata': self.resources[uri]
        }
```

#### 2.2 Prompts Reali
```python
# PROBLEMA: Prompts sono mock
# SOLUZIONE: Sistema di template prompts

class PromptManager:
    def __init__(self):
        self.prompts = {
            'analyze_code': {
                'name': 'analyze_code',
                'description': 'Analyze code for issues',
                'parameters': ['file_path', 'analysis_type'],
                'template': 'Analyze the {analysis_type} of the code in {file_path}'
            },
            'generate_test': {
                'name': 'generate_test',
                'description': 'Generate tests for code',
                'parameters': ['code', 'framework'],
                'template': 'Generate {framework} tests for:\n{code}'
            },
            'explain_error': {
                'name': 'explain_error',
                'description': 'Explain an error message',
                'parameters': ['error', 'context'],
                'template': 'Explain this error:\n{error}\nContext: {context}'
            }
        }

    def list_prompts(self) -> List[Dict]:
        return list(self.prompts.values())

    def get_prompt(self, name: str) -> Dict:
        if name not in self.prompts:
            raise ValueError(f"Prompt not found: {name}")
        return self.prompts[name]

    def run_prompt(self, name: str, arguments: Dict) -> str:
        prompt = self.get_prompt(name)
        template = prompt['template']

        # Sostituisci parametri nel template
        for param in prompt['parameters']:
            if param in arguments:
                template = template.replace(f'{{{param}}}', str(arguments[param]))

        return template
```

### FASE 3: FEATURES AVANZATE (85% → 100%)
**Timeline: 3 ore**

#### 3.1 Sistema di Notifiche
```python
# PROBLEMA: Nessun sistema di notifiche
# SOLUZIONE: Event-driven notifications

import asyncio
from typing import List, Callable

class NotificationSystem:
    def __init__(self, ws_handler):
        self.ws_handler = ws_handler
        self.subscribers = {}
        self.event_queue = asyncio.Queue()
        asyncio.create_task(self._process_notifications())

    async def _process_notifications(self):
        """Processa notifiche in background"""
        while True:
            notification = await self.event_queue.get()
            await self._broadcast(notification)

    async def _broadcast(self, notification: Dict):
        """Invia notifica a tutti i client connessi"""
        message = {
            'jsonrpc': '2.0',
            'method': f'notifications/{notification["type"]}',
            'params': notification['data']
        }
        await self.ws_handler.broadcast(message)

    async def notify_initialized(self):
        await self.event_queue.put({
            'type': 'initialized',
            'data': {'timestamp': datetime.now().isoformat()}
        })

    async def notify_progress(self, token: str, progress: int, message: str = ""):
        await self.event_queue.put({
            'type': 'progress',
            'data': {
                'progressToken': token,
                'progress': progress,
                'message': message
            }
        })

    async def notify_cancelled(self, request_id: str):
        await self.event_queue.put({
            'type': 'cancelled',
            'data': {'requestId': request_id}
        })
```

#### 3.2 Streaming Support
```python
# PROBLEMA: No streaming
# SOLUZIONE: Async streaming con generator

class StreamingHandler:
    def __init__(self):
        self.active_streams = {}

    async def stream_response(self, request_id: str, generator):
        """Stream response in chunks"""
        stream_token = str(uuid.uuid4())
        self.active_streams[stream_token] = True

        try:
            async for chunk in generator:
                if not self.active_streams.get(stream_token):
                    break  # Stream cancelled

                yield {
                    'jsonrpc': '2.0',
                    'method': 'stream/chunk',
                    'params': {
                        'requestId': request_id,
                        'streamToken': stream_token,
                        'chunk': chunk,
                        'done': False
                    }
                }

            # Send completion
            yield {
                'jsonrpc': '2.0',
                'method': 'stream/chunk',
                'params': {
                    'requestId': request_id,
                    'streamToken': stream_token,
                    'chunk': None,
                    'done': True
                }
            }
        finally:
            del self.active_streams[stream_token]
```

#### 3.3 Batch Operations
```python
# PROBLEMA: No batch support
# SOLUZIONE: Processare array di richieste

class BatchProcessor:
    def __init__(self, handler):
        self.handler = handler

    async def process_batch(self, requests: List[Dict]) -> List[Dict]:
        """Processa batch di richieste"""
        results = []

        # Esegui in parallelo per performance
        tasks = []
        for request in requests:
            task = self.handler.handle_request(request)
            tasks.append(task)

        # Attendi tutti i risultati
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Formatta risposte
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                results.append({
                    'jsonrpc': '2.0',
                    'error': {
                        'code': -32603,
                        'message': str(response)
                    },
                    'id': requests[i].get('id')
                })
            else:
                results.append(response)

        return results
```

## 📋 File da Creare/Modificare

### 1. `mcp_server_v2_full.py`
Server MCP v2 completamente compliant con tutte le feature

### 2. `mcp_session_manager.py`
Gestione sessioni persistenti

### 3. `mcp_resource_manager.py`
Gestione risorse reali del progetto

### 4. `mcp_prompt_manager.py`
Sistema di prompt templates

### 5. `mcp_notification_system.py`
Sistema di notifiche event-driven

### 6. `mcp_streaming_handler.py`
Supporto streaming responses

### 7. `mcp_batch_processor.py`
Processamento batch richieste

## 🧪 Test di Validazione

```python
# test_full_compliance_v2.py

def test_all_tools():
    """Testa tutti gli 8 tool MCP"""
    tools = [
        'heartbeat', 'update_status', 'log_activity',
        'check_conflicts', 'register_component',
        'request_collaboration', 'propose_decision',
        'find_component_owner'
    ]

    for tool in tools:
        result = call_tool(tool, get_valid_params(tool))
        assert result['success'] == True

def test_session_persistence():
    """Testa persistenza sessioni"""
    session_id = initialize_session()
    assert session_id is not None

    # Usa sessione dopo 5 minuti
    time.sleep(300)
    assert validate_session(session_id) == True

def test_streaming():
    """Testa streaming responses"""
    stream = request_streaming_response()
    chunks = []
    async for chunk in stream:
        chunks.append(chunk)
    assert len(chunks) > 1

def test_batch():
    """Testa batch operations"""
    batch = [
        {'method': 'tools/list'},
        {'method': 'heartbeat'},
        {'method': 'update_status'}
    ]
    results = process_batch(batch)
    assert len(results) == 3
    assert all('error' not in r for r in results)
```

## ⏱️ Timeline Implementazione

| Fase | Ore | Compliance |
|------|-----|------------|
| Fase 1: Fix Critici | 1h | 38.9% → 70% |
| Fase 2: Core Features | 2h | 70% → 85% |
| Fase 3: Advanced | 3h | 85% → 100% |
| **TOTALE** | **6h** | **100%** |

## ✅ Risultato Atteso

- **100% MCP v2 Compliance**
- Tutti gli 8 tool funzionanti
- Session management completo
- Resources/Prompts reali
- Notifications funzionanti
- Streaming support
- Batch operations
- Production ready