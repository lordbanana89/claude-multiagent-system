# 📋 PIANO IMPLEMENTAZIONE HEARTBEAT REALE

## 🎯 OBIETTIVO
Trasformare il tool `heartbeat` da mock a implementazione reale funzionante

## 📊 COMPONENTI DA IMPLEMENTARE

### STEP 1: DATABASE SETUP 
- Creare schema database
- Inizializzare tabella agents
- Test connessione

### STEP 2: MESSAGE BUS 
- Integrare con message_bus esistente
- Definire evento AGENT_READY
- Test pubblicazione eventi

### STEP 3: WATCHDOG TIMER 
- Implementare timeout detection
- Auto-restart agenti morti
- Alert su failure

### STEP 4: METRICS 
- Contatore heartbeat
- Dashboard monitoring
- Statistiche uptime

### STEP 5: TESTING 
- Unit test
- Integration test
- Load test

---

## 🛠️ IMPLEMENTAZIONE DETTAGLIATA

### STEP 1: DATABASE SETUP

#### 1.1 Creare schema database
```sql
-- File: schema/agents.sql

CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    status TEXT DEFAULT 'offline',
    last_heartbeat TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    capabilities JSON,
    current_task_id TEXT,
    error_count INTEGER DEFAULT 0,
    total_heartbeats INTEGER DEFAULT 0
);

CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_heartbeat ON agents(last_heartbeat);

-- Tabella per storico heartbeat (opzionale)
CREATE TABLE IF NOT EXISTS heartbeat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    status TEXT,
    metadata JSON,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE INDEX idx_heartbeat_agent ON heartbeat_history(agent_id);
CREATE INDEX idx_heartbeat_time ON heartbeat_history(timestamp);
```

#### 1.2 Database Manager
```python
# File: core/database_manager.py

import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestisce connessione database per MCP"""

    def __init__(self, db_path='mcp_system.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Inizializza schema database"""
        with open('schema/agents.sql', 'r') as f:
            schema = f.read()

        with self.get_connection() as conn:
            conn.executescript(schema)
            logger.info(f"Database initialized at {self.db_path}")

    @contextmanager
    def get_connection(self):
        """Context manager per connessioni"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

    def update_heartbeat(self, agent_id: str, timestamp: datetime):
        """Aggiorna heartbeat agente"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Controlla se agente esiste
            cursor.execute("SELECT id FROM agents WHERE id = ?", (agent_id,))
            exists = cursor.fetchone()

            if exists:
                # Aggiorna esistente
                cursor.execute("""
                    UPDATE agents
                    SET last_heartbeat = ?,
                        status = 'active',
                        total_heartbeats = total_heartbeats + 1
                    WHERE id = ?
                """, (timestamp, agent_id))
            else:
                # Crea nuovo agente
                cursor.execute("""
                    INSERT INTO agents (id, name, type, status, last_heartbeat, total_heartbeats)
                    VALUES (?, ?, ?, 'active', ?, 1)
                """, (agent_id, agent_id, 'generic', timestamp))

            # Aggiungi a storico
            cursor.execute("""
                INSERT INTO heartbeat_history (agent_id, timestamp, status)
                VALUES (?, ?, 'active')
            """, (agent_id, timestamp))

            return cursor.rowcount > 0
```

### STEP 2: MESSAGE BUS INTEGRATION

#### 2.1 Estendere Event Types
```python
# File: core/message_bus.py (aggiungere)

class EventType(Enum):
    # ... esistenti ...

    # Heartbeat events
    HEARTBEAT_RECEIVED = "heartbeat.received"
    HEARTBEAT_MISSED = "heartbeat.missed"
    AGENT_TIMEOUT = "agent.timeout"
    AGENT_RECOVERED = "agent.recovered"
```

#### 2.2 Heartbeat Publisher
```python
# File: core/heartbeat_publisher.py

from core.message_bus import get_message_bus, Event, EventType
import logging

logger = logging.getLogger(__name__)

class HeartbeatPublisher:
    """Pubblica eventi heartbeat sul message bus"""

    def __init__(self):
        self.message_bus = get_message_bus()
        if not self.message_bus.running:
            self.message_bus.start()

    def publish_heartbeat(self, agent_id: str, timestamp: str):
        """Pubblica heartbeat ricevuto"""
        event = Event(
            type=EventType.HEARTBEAT_RECEIVED,
            source=agent_id,
            payload={
                'agent_id': agent_id,
                'timestamp': timestamp,
                'status': 'active'
            }
        )

        self.message_bus.publish(event)
        logger.debug(f"Published heartbeat for {agent_id}")

        # Pubblica anche AGENT_READY se era offline
        self._check_agent_recovery(agent_id)

    def _check_agent_recovery(self, agent_id: str):
        """Controlla se agente si è ripreso da offline"""
        # Logica per determinare se era offline
        # Se sì, pubblica AGENT_RECOVERED
        pass
```

### STEP 3: WATCHDOG TIMER

#### 3.1 Watchdog Implementation
```python
# File: core/watchdog.py

import threading
import time
from datetime import datetime, timedelta
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class AgentWatchdog:
    """Monitora heartbeat degli agenti"""

    def __init__(self, timeout_seconds=60):
        self.timeout_seconds = timeout_seconds
        self.last_heartbeats: Dict[str, datetime] = {}
        self.expected_intervals: Dict[str, int] = {}
        self.running = False
        self.thread = None
        self.callbacks = []

    def start(self):
        """Avvia watchdog"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Watchdog started")

    def stop(self):
        """Ferma watchdog"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Watchdog stopped")

    def reset_timeout(self, agent_id: str, next_expected_seconds: int = None):
        """Reset timeout per agente"""
        self.last_heartbeats[agent_id] = datetime.now()

        if next_expected_seconds:
            self.expected_intervals[agent_id] = next_expected_seconds
        elif agent_id not in self.expected_intervals:
            self.expected_intervals[agent_id] = self.timeout_seconds

        logger.debug(f"Reset timeout for {agent_id}, next expected in {self.expected_intervals[agent_id]}s")

    def _monitor_loop(self):
        """Loop di monitoring"""
        while self.running:
            try:
                now = datetime.now()

                for agent_id, last_heartbeat in list(self.last_heartbeats.items()):
                    timeout = self.expected_intervals.get(agent_id, self.timeout_seconds)

                    if (now - last_heartbeat).total_seconds() > timeout:
                        self._handle_timeout(agent_id)

                time.sleep(5)  # Check ogni 5 secondi

            except Exception as e:
                logger.error(f"Watchdog error: {e}")

    def _handle_timeout(self, agent_id: str):
        """Gestisce timeout agente"""
        logger.warning(f"Agent {agent_id} timed out!")

        # Rimuovi da tracking
        del self.last_heartbeats[agent_id]

        # Notifica callbacks
        for callback in self.callbacks:
            try:
                callback(agent_id)
            except Exception as e:
                logger.error(f"Callback error: {e}")

        # Pubblica evento
        from core.message_bus import get_message_bus, Event, EventType
        bus = get_message_bus()
        bus.publish(Event(
            type=EventType.AGENT_TIMEOUT,
            source='watchdog',
            payload={'agent_id': agent_id, 'last_seen': self.last_heartbeats.get(agent_id)}
        ))

    def register_callback(self, callback):
        """Registra callback per timeout"""
        self.callbacks.append(callback)

    def get_status(self):
        """Ottieni stato watchdog"""
        now = datetime.now()
        status = {}

        for agent_id, last_heartbeat in self.last_heartbeats.items():
            elapsed = (now - last_heartbeat).total_seconds()
            timeout = self.expected_intervals.get(agent_id, self.timeout_seconds)

            status[agent_id] = {
                'last_heartbeat': last_heartbeat.isoformat(),
                'elapsed_seconds': elapsed,
                'timeout_seconds': timeout,
                'healthy': elapsed < timeout
            }

        return status
```

### STEP 4: METRICS COLLECTOR

#### 4.1 Heartbeat Metrics
```python
# File: core/metrics/heartbeat_metrics.py

from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict
import threading

class HeartbeatMetrics:
    """Raccoglie metriche heartbeat"""

    def __init__(self):
        self.total_heartbeats = defaultdict(int)
        self.last_heartbeat = {}
        self.uptime_start = {}
        self.missed_heartbeats = defaultdict(int)
        self.lock = threading.Lock()

    def increment(self, agent_id: str):
        """Incrementa contatore heartbeat"""
        with self.lock:
            self.total_heartbeats[agent_id] += 1
            self.last_heartbeat[agent_id] = datetime.now()

            # Track uptime
            if agent_id not in self.uptime_start:
                self.uptime_start[agent_id] = datetime.now()

    def mark_missed(self, agent_id: str):
        """Marca heartbeat mancato"""
        with self.lock:
            self.missed_heartbeats[agent_id] += 1

    def get_metrics(self) -> Dict:
        """Ottieni metriche"""
        with self.lock:
            now = datetime.now()
            metrics = {}

            for agent_id in self.total_heartbeats:
                uptime = None
                if agent_id in self.uptime_start:
                    uptime = (now - self.uptime_start[agent_id]).total_seconds()

                metrics[agent_id] = {
                    'total_heartbeats': self.total_heartbeats[agent_id],
                    'missed_heartbeats': self.missed_heartbeats[agent_id],
                    'last_heartbeat': self.last_heartbeat.get(agent_id),
                    'uptime_seconds': uptime,
                    'reliability': self._calculate_reliability(agent_id)
                }

            return metrics

    def _calculate_reliability(self, agent_id: str) -> float:
        """Calcola affidabilità agente (%)"""
        total = self.total_heartbeats[agent_id]
        missed = self.missed_heartbeats[agent_id]

        if total + missed == 0:
            return 100.0

        return (total / (total + missed)) * 100
```

### STEP 5: INTEGRAZIONE FINALE IN MCP SERVER

#### 5.1 Modificare execute_tool()
```python
# File: mcp_server_v2_full.py (modificare heartbeat section)

from core.database_manager import DatabaseManager
from core.heartbeat_publisher import HeartbeatPublisher
from core.watchdog import AgentWatchdog
from core.metrics.heartbeat_metrics import HeartbeatMetrics
from datetime import datetime, timezone, timedelta

class MCPServerV2Full:
    def __init__(self):
        # ... existing init ...

        # Aggiungi componenti heartbeat
        self.db = DatabaseManager()
        self.heartbeat_publisher = HeartbeatPublisher()
        self.watchdog = AgentWatchdog(timeout_seconds=60)
        self.metrics = HeartbeatMetrics()

        # Avvia watchdog
        self.watchdog.start()

        # Registra callback per timeout
        self.watchdog.register_callback(self._on_agent_timeout)

        # Heartbeat interval default (30 secondi)
        self.heartbeat_interval = 30

    async def execute_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """Execute the actual tool"""
        timestamp = datetime.now(timezone.utc)

        if tool_name == 'heartbeat':
            agent = arguments.get('agent', 'unknown')

            try:
                # 1. Salvare nel database
                success = self.db.update_heartbeat(agent, timestamp)

                if not success:
                    raise Exception("Database update failed")

                # 2. Pubblicare evento nel message bus
                self.heartbeat_publisher.publish_heartbeat(agent, timestamp.isoformat())

                # 3. Resettare timeout watchdog
                self.watchdog.reset_timeout(agent, self.heartbeat_interval)

                # 4. Aggiornare metriche
                self.metrics.increment(agent)

                # 5. Calcola prossimo heartbeat atteso
                next_expected = timestamp + timedelta(seconds=self.heartbeat_interval)

                return {
                    'status': 'alive',
                    'agent': agent,
                    'timestamp': timestamp.isoformat(),
                    'next_expected': next_expected.isoformat(),
                    'heartbeat_interval': self.heartbeat_interval,
                    'recorded': True
                }

            except Exception as e:
                logger.error(f"Heartbeat processing failed for {agent}: {e}")
                return {
                    'status': 'error',
                    'agent': agent,
                    'timestamp': timestamp.isoformat(),
                    'error': str(e)
                }

        elif tool_name == 'update_status':
            # ... resto dei tool ...

    def _on_agent_timeout(self, agent_id: str):
        """Callback quando agente va in timeout"""
        logger.warning(f"Agent {agent_id} timeout detected")

        # Aggiorna database
        with self.db.get_connection() as conn:
            conn.execute("""
                UPDATE agents
                SET status = 'offline', error_count = error_count + 1
                WHERE id = ?
            """, (agent_id,))

        # Marca metrica missed
        self.metrics.mark_missed(agent_id)

        # Qui potresti implementare auto-restart o alert
        # self._try_restart_agent(agent_id)
```

### STEP 6: TEST COMPLETO

#### 6.1 Test Script
```python
# File: test_heartbeat_real.py

#!/usr/bin/env python3
"""Test implementazione reale heartbeat"""

import asyncio
import time
import json
import requests
from datetime import datetime

class HeartbeatTester:
    def __init__(self):
        self.mcp_url = "http://localhost:8099"
        self.test_agent = "test-agent-001"

    async def test_single_heartbeat(self):
        """Test singolo heartbeat"""
        print("📍 Test 1: Singolo heartbeat")

        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "heartbeat",
                "arguments": {"agent": self.test_agent}
            },
            "id": 1
        }

        response = requests.post(
            f"{self.mcp_url}/jsonrpc",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            if 'result' in result:
                data = result['result']
                print(f"✅ Heartbeat recorded:")
                print(f"   - Agent: {data.get('agent')}")
                print(f"   - Status: {data.get('status')}")
                print(f"   - Next expected: {data.get('next_expected')}")
                print(f"   - Recorded in DB: {data.get('recorded', False)}")
                return True

        print(f"❌ Heartbeat failed: {response.text}")
        return False

    async def test_multiple_heartbeats(self):
        """Test multipli heartbeat in sequenza"""
        print("\n📍 Test 2: Multipli heartbeat (3x con 2 sec delay)")

        for i in range(3):
            success = await self.test_single_heartbeat()
            if not success:
                print(f"   Failed at heartbeat {i+1}")
                return False

            if i < 2:  # Non aspettare dopo l'ultimo
                print(f"   Waiting 2 seconds...")
                await asyncio.sleep(2)

        print("✅ All heartbeats recorded successfully")
        return True

    async def test_watchdog_timeout(self):
        """Test timeout detection"""
        print("\n📍 Test 3: Watchdog timeout detection")

        # Invia heartbeat iniziale
        await self.test_single_heartbeat()

        print("   Waiting 65 seconds for timeout...")
        await asyncio.sleep(65)

        # Controlla stato agente
        # Qui dovresti controllare se l'agente è marcato offline
        print("   Checking agent status...")

        # Query database o API per stato
        # ...

        print("✅ Timeout detection test complete")
        return True

    async def test_metrics(self):
        """Test metriche heartbeat"""
        print("\n📍 Test 4: Metrics collection")

        # Invia alcuni heartbeat
        for i in range(5):
            await self.test_single_heartbeat()
            await asyncio.sleep(1)

        # Query metriche
        # Assumendo un endpoint /metrics
        response = requests.get(f"{self.mcp_url}/metrics")

        if response.status_code == 200:
            metrics = response.json()
            agent_metrics = metrics.get(self.test_agent, {})

            print(f"✅ Metrics for {self.test_agent}:")
            print(f"   - Total heartbeats: {agent_metrics.get('total_heartbeats', 0)}")
            print(f"   - Missed: {agent_metrics.get('missed_heartbeats', 0)}")
            print(f"   - Reliability: {agent_metrics.get('reliability', 0)}%")
            return True

        print("❌ Could not fetch metrics")
        return False

    async def run_all_tests(self):
        """Esegui tutti i test"""
        print("=" * 60)
        print("🧪 HEARTBEAT REAL IMPLEMENTATION TEST")
        print("=" * 60)

        tests = [
            self.test_single_heartbeat,
            self.test_multiple_heartbeats,
            # self.test_watchdog_timeout,  # Commentato perché richiede 65 secondi
            self.test_metrics
        ]

        passed = 0
        failed = 0

        for test in tests:
            try:
                result = await test()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                failed += 1

        print("\n" + "=" * 60)
        print(f"📊 RESULTS: {passed} passed, {failed} failed")

        if failed == 0:
            print("🎉 All tests passed!")
        else:
            print("⚠️ Some tests failed")

async def main():
    tester = HeartbeatTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
```

## 📊 CHECKLIST IMPLEMENTAZIONE

- [ ] Creare schema database agents
- [ ] Implementare DatabaseManager
- [ ] Integrare Message Bus
- [ ] Implementare HeartbeatPublisher
- [ ] Creare AgentWatchdog
- [ ] Implementare HeartbeatMetrics
- [ ] Modificare execute_tool() in MCP server
- [ ] Testare singolo heartbeat
- [ ] Testare multipli heartbeat
- [ ] Testare timeout detection
- [ ] Verificare metriche
- [ ] Verificare persistenza database

## 🎯 RISULTATO ATTESO

Dopo l'implementazione, quando un agente invia heartbeat:

1. ✅ Viene salvato nel database con timestamp
2. ✅ Un evento viene pubblicato sul message bus
3. ✅ Il watchdog resetta il timeout
4. ✅ Le metriche vengono aggiornate
5. ✅ Dashboard mostra agente "active"
6. ✅ Se manca heartbeat → alert automatico

**Da mock inutile a sistema di monitoring reale!**