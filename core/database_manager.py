#!/usr/bin/env python3
"""
Database Manager - Gestisce la persistenza per il sistema MCP
"""

import sqlite3
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import threading
from pathlib import Path

class DatabaseManager:
    """Gestisce tutte le operazioni database per MCP"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.db_path = Path(__file__).parent.parent / "mcp_system.db"
            self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.setup_tables()
            self.initialized = True

    def setup_tables(self):
        """Crea tutte le tabelle necessarie"""

        # Tabella agents
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'offline',
                last_heartbeat TIMESTAMP,
                current_task TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabella agent_status_history
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS agent_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                status TEXT NOT NULL,
                task TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents(id)
            )
        ''')

        # Tabella activity_logs
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                category TEXT,
                activity TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents(id)
            )
        ''')

        # Tabella tasks
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                component TEXT,
                assigned_to TEXT,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (assigned_to) REFERENCES agents(id)
            )
        ''')

        # Tabella components
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS components (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                type TEXT,
                owner TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (owner) REFERENCES agents(id)
            )
        ''')

        # Tabella component_dependencies
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS component_dependencies (
                component_id TEXT,
                depends_on TEXT,
                PRIMARY KEY (component_id, depends_on),
                FOREIGN KEY (component_id) REFERENCES components(id),
                FOREIGN KEY (depends_on) REFERENCES components(id)
            )
        ''')

        # Tabella collaboration_requests
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS collaboration_requests (
                id TEXT PRIMARY KEY,
                from_agent TEXT NOT NULL,
                to_agent TEXT NOT NULL,
                task TEXT,
                priority INTEGER DEFAULT 5,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accepted_at TIMESTAMP,
                completed_at TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (from_agent) REFERENCES agents(id),
                FOREIGN KEY (to_agent) REFERENCES agents(id)
            )
        ''')

        # Tabella decisions
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY,
                proposed_by TEXT NOT NULL,
                decision TEXT NOT NULL,
                category TEXT,
                confidence REAL,
                alternatives TEXT,
                status TEXT DEFAULT 'proposed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (proposed_by) REFERENCES agents(id)
            )
        ''')

        # Tabella decision_votes
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS decision_votes (
                decision_id TEXT,
                agent_id TEXT,
                vote TEXT,
                weight REAL DEFAULT 1.0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (decision_id, agent_id),
                FOREIGN KEY (decision_id) REFERENCES decisions(id),
                FOREIGN KEY (agent_id) REFERENCES agents(id)
            )
        ''')

        # Tabella agent_queues
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS agent_queues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                request_id TEXT NOT NULL,
                priority INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents(id),
                FOREIGN KEY (request_id) REFERENCES collaboration_requests(id)
            )
        ''')

        # Inserisci agenti predefiniti
        default_agents = [
            'supervisor', 'master', 'backend-api', 'database',
            'frontend-ui', 'testing', 'deployment', 'instagram',
            'queue-manager'
        ]

        for agent_name in default_agents:
            self.conn.execute('''
                INSERT OR IGNORE INTO agents (id, name, status)
                VALUES (?, ?, 'offline')
            ''', (agent_name, agent_name))

        self.conn.commit()

    def update_heartbeat(self, agent: str, timestamp: str) -> Dict:
        """Aggiorna heartbeat per un agente"""
        cursor = self.conn.cursor()

        # Aggiorna stato agente
        cursor.execute('''
            UPDATE agents
            SET last_heartbeat = ?, status = 'active', updated_at = ?
            WHERE id = ? OR name = ?
        ''', (timestamp, timestamp, agent, agent))

        # Log stato nella history
        cursor.execute('''
            INSERT INTO agent_status_history (agent_id, status, timestamp)
            VALUES (?, 'active', ?)
        ''', (agent, timestamp))

        self.conn.commit()

        # Calcola prossimo heartbeat atteso (30 secondi)
        next_expected = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        next_expected = next_expected.timestamp() + 30

        return {
            'status': 'alive',
            'agent': agent,
            'timestamp': timestamp,
            'next_expected': next_expected,
            'db_updated': True
        }

    def update_agent_status(self, agent: str, status: str, task: Optional[str] = None) -> Dict:
        """Aggiorna stato agente"""
        cursor = self.conn.cursor()
        timestamp = datetime.now(timezone.utc).isoformat()

        # Ottieni stato precedente
        cursor.execute('SELECT status FROM agents WHERE id = ? OR name = ?', (agent, agent))
        row = cursor.fetchone()
        previous_status = row[0] if row else None

        # Aggiorna stato
        cursor.execute('''
            UPDATE agents
            SET status = ?, current_task = ?, updated_at = ?
            WHERE id = ? OR name = ?
        ''', (status, task, timestamp, agent, agent))

        # Log nella history
        cursor.execute('''
            INSERT INTO agent_status_history (agent_id, status, task, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (agent, status, task, timestamp))

        # Se busy, assegna task
        if status == 'busy' and task:
            cursor.execute('''
                UPDATE tasks
                SET assigned_to = ?, status = 'in_progress', started_at = ?
                WHERE id = ?
            ''', (agent, timestamp, task))

        self.conn.commit()

        return {
            'success': True,
            'agent': agent,
            'status': status,
            'previous_status': previous_status,
            'task_assigned': task,
            'timestamp': timestamp
        }

    def log_activity(self, agent: str, category: str, activity: str, details: Dict) -> Dict:
        """Log attività agente"""
        activity_id = str(datetime.now().timestamp())
        timestamp = datetime.now(timezone.utc).isoformat()

        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO activity_logs (id, agent_id, category, activity, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (activity_id, agent, category, activity, json.dumps(details), timestamp))

        self.conn.commit()

        return {
            'logged': True,
            'id': activity_id,
            'timestamp': timestamp,
            'indexed': True
        }

    def check_conflicts(self, agents: List[str]) -> Dict:
        """Controlla conflitti tra agenti"""
        cursor = self.conn.cursor()

        # Query task assegnati
        placeholders = ','.join(['?' for _ in agents])
        cursor.execute(f'''
            SELECT t.id, t.component, t.assigned_to, a.status
            FROM tasks t
            JOIN agents a ON t.assigned_to = a.id
            WHERE t.assigned_to IN ({placeholders})
            AND t.status = 'in_progress'
        ''', agents)

        tasks = cursor.fetchall()

        # Trova conflitti
        conflicts = []
        component_agents = {}

        for task in tasks:
            component = task[1]
            agent = task[2]

            if component in component_agents:
                conflicts.append({
                    'type': 'component_conflict',
                    'component': component,
                    'agents': [component_agents[component], agent],
                    'severity': 'high'
                })
            else:
                component_agents[component] = agent

        return {
            'conflicts': conflicts,
            'agents_checked': agents,
            'components_analyzed': len(component_agents),
            'resolution_needed': len(conflicts) > 0
        }

    def register_component(self, name: str, type: str, owner: str, metadata: Dict) -> Dict:
        """Registra nuovo componente"""
        cursor = self.conn.cursor()
        component_id = str(datetime.now().timestamp())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Verifica unicità
        cursor.execute('SELECT id FROM components WHERE name = ?', (name,))
        if cursor.fetchone():
            raise ValueError(f"Component {name} already exists")

        # Registra componente
        cursor.execute('''
            INSERT INTO components (id, name, type, owner, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (component_id, name, type, owner, timestamp, json.dumps(metadata)))

        self.conn.commit()

        return {
            'registered': True,
            'component_id': component_id,
            'name': name,
            'owner': owner,
            'timestamp': timestamp
        }

    def request_collaboration(self, from_agent: str, to_agent: str, task: str,
                             priority: int = 5, metadata: Dict = None) -> Dict:
        """Richiedi collaborazione tra agenti"""
        cursor = self.conn.cursor()
        request_id = str(datetime.now().timestamp())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Crea richiesta
        cursor.execute('''
            INSERT INTO collaboration_requests
            (id, from_agent, to_agent, task, priority, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (request_id, from_agent, to_agent, task, priority, timestamp,
              json.dumps(metadata or {})))

        # Verifica disponibilità target
        cursor.execute('SELECT status, current_task FROM agents WHERE id = ?', (to_agent,))
        row = cursor.fetchone()

        if row and row[0] == 'idle':
            # Auto-accetta se idle
            cursor.execute('''
                UPDATE collaboration_requests
                SET status = 'accepted', accepted_at = ?
                WHERE id = ?
            ''', (timestamp, request_id))

            cursor.execute('''
                UPDATE agents
                SET status = 'busy', current_task = ?
                WHERE id = ?
            ''', (task, to_agent))

            status = 'accepted'
        else:
            # Aggiungi a coda
            cursor.execute('''
                INSERT INTO agent_queues (agent_id, request_id, priority)
                VALUES (?, ?, ?)
            ''', (to_agent, request_id, priority))

            status = 'queued'

        self.conn.commit()

        return {
            'request_id': request_id,
            'status': status,
            'from': from_agent,
            'to': to_agent,
            'timestamp': timestamp
        }

    def propose_decision(self, agent: str, decision: str, category: str,
                        confidence: float, alternatives: List[str]) -> Dict:
        """Proponi decisione"""
        cursor = self.conn.cursor()
        decision_id = str(datetime.now().timestamp())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Crea decisione
        cursor.execute('''
            INSERT INTO decisions
            (id, proposed_by, decision, category, confidence, alternatives, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (decision_id, agent, decision, category, confidence,
              json.dumps(alternatives), timestamp))

        # Auto-approva se alta confidence
        if confidence >= 0.95:
            cursor.execute('''
                UPDATE decisions
                SET status = 'auto_approved', approved_at = ?
                WHERE id = ?
            ''', (timestamp, decision_id))
            status = 'auto_approved'
        else:
            status = 'pending_votes'

        self.conn.commit()

        return {
            'decision_id': decision_id,
            'status': status,
            'category': category,
            'confidence': confidence,
            'timestamp': timestamp
        }

    def find_component_owner(self, component: str) -> Dict:
        """Trova proprietario componente"""
        cursor = self.conn.cursor()

        # Cerca nel database
        cursor.execute('''
            SELECT c.owner, c.type, c.status, a.status as agent_status
            FROM components c
            LEFT JOIN agents a ON c.owner = a.id
            WHERE c.name = ? OR c.id = ?
        ''', (component, component))

        row = cursor.fetchone()

        if row:
            return {
                'component': component,
                'owner': row[0],
                'type': row[1],
                'status': row[2],
                'agent_available': row[3] == 'active'
            }

        # Pattern matching fallback
        patterns = {
            'frontend': 'frontend-ui',
            'backend': 'backend-api',
            'database': 'database',
            'test': 'testing',
            'deploy': 'deployment'
        }

        owner = 'supervisor'  # default
        for pattern, agent in patterns.items():
            if pattern in component.lower():
                owner = agent
                break

        return {
            'component': component,
            'owner': owner,
            'type': 'inferred',
            'status': 'unknown',
            'agent_available': True
        }

    def get_agent_metrics(self, agent: str = None) -> Dict:
        """Ottieni metriche agenti"""
        cursor = self.conn.cursor()

        if agent:
            cursor.execute('''
                SELECT COUNT(*) as total_activities
                FROM activity_logs
                WHERE agent_id = ?
            ''', (agent,))
            activities = cursor.fetchone()[0]

            cursor.execute('''
                SELECT COUNT(*) as total_tasks
                FROM tasks
                WHERE assigned_to = ? AND status = 'completed'
            ''', (agent,))
            tasks = cursor.fetchone()[0]

            return {
                'agent': agent,
                'total_activities': activities,
                'completed_tasks': tasks
            }
        else:
            cursor.execute('SELECT COUNT(*) FROM agents WHERE status = "active"')
            active = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = "completed"')
            completed = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = "in_progress"')
            in_progress = cursor.fetchone()[0]

            return {
                'active_agents': active,
                'completed_tasks': completed,
                'in_progress_tasks': in_progress
            }

    def close(self):
        """Chiudi connessione database"""
        if hasattr(self, 'conn'):
            self.conn.close()