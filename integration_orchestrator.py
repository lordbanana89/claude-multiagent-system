#!/usr/bin/env python3
"""
Claude Squad Integration Orchestrator
Questo modulo collega tutti i componenti del sistema per farli lavorare insieme
"""

import asyncio
import json
import sqlite3
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import redis
import requests
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationOrchestrator:
    """Orchestratore centrale per integrare tutti i componenti"""

    def __init__(self):
        self.db_path = 'mcp_system.db'
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.agents = [
            'supervisor', 'master', 'backend-api', 'database',
            'frontend-ui', 'testing', 'instagram', 'queue-manager', 'deployment'
        ]
        self.api_base = 'http://localhost:5001'
        self.gateway_base = 'http://localhost:8888'
        # Use write-ahead logging to prevent locking
        self._init_database()

    def _init_database(self):
        """Initialize database with proper settings"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        # Enable WAL mode to prevent locking
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=NORMAL')
        conn.close()

    def _get_db_connection(self):
        """Get a database connection with timeout"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute('PRAGMA journal_mode=WAL')
        return conn

    def verify_system_health(self) -> Dict[str, Any]:
        """Verifica che tutti i componenti siano attivi"""
        health = {
            'database': False,
            'redis': False,
            'api': False,
            'gateway': False,
            'agents': {},
            'frontend': False
        }

        # Check database
        try:
            conn = self._get_db_connection()
            conn.execute('SELECT 1')
            conn.close()
            health['database'] = True
        except:
            logger.error("Database not accessible")

        # Check Redis
        try:
            self.redis_client.ping()
            health['redis'] = True
        except:
            logger.error("Redis not accessible")

        # Check APIs
        try:
            r = requests.get(f'{self.api_base}/api/health', timeout=2)
            health['api'] = r.status_code == 200
        except:
            logger.error("Main API not accessible")

        try:
            r = requests.get(f'{self.gateway_base}/health', timeout=2)
            health['gateway'] = r.status_code == 200
        except:
            logger.error("Gateway not accessible")

        # Check TMUX sessions
        for agent in self.agents:
            session_name = f'claude-{agent}'
            result = subprocess.run(
                ['tmux', 'has-session', '-t', session_name],
                capture_output=True
            )
            health['agents'][agent] = result.returncode == 0

        # Check frontend
        try:
            r = requests.get('http://localhost:5173', timeout=2)
            health['frontend'] = r.status_code == 200
        except:
            logger.error("Frontend not accessible")

        return health

    def sync_agent_states(self):
        """Sincronizza lo stato degli agenti tra TMUX e database"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        for agent in self.agents:
            session_name = f'claude-{agent}'

            # Check TMUX session
            result = subprocess.run(
                ['tmux', 'has-session', '-t', session_name],
                capture_output=True
            )

            status = 'active' if result.returncode == 0 else 'inactive'

            # Update database
            cursor.execute('''
                INSERT OR REPLACE INTO agent_states (agent, status, last_seen)
                VALUES (?, ?, ?)
            ''', (agent, status, datetime.now().isoformat()))

            # Log activity with unique ID using timestamp with microseconds
            activity_id = f'sync_{agent}_{int(time.time() * 1000000)}'
            cursor.execute('''
                INSERT OR IGNORE INTO activities (id, agent, timestamp, activity, category, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                activity_id,
                agent,
                datetime.now().isoformat(),
                f'Agent {agent} status: {status}',
                'sync',
                'completed'
            ))

        conn.commit()
        conn.close()
        logger.info(f"Synced {len(self.agents)} agent states")

    def route_message_to_agent(self, message: Dict[str, Any]) -> bool:
        """Instrada un messaggio all'agente corretto"""
        recipient = message.get('recipient')
        content = message.get('content')

        if not recipient or not content:
            return False

        session_name = f'claude-{recipient}'

        # Send to TMUX session
        try:
            # Escape special characters
            escaped_content = content.replace('"', '\\"').replace("'", "\\'")

            subprocess.run([
                'tmux', 'send-keys', '-t', session_name,
                f'echo "📩 Message received: {escaped_content}"', 'Enter'
            ])

            # Log in database
            conn = self._get_db_connection()
            cursor = conn.cursor()
            # Check if table has correct columns
            try:
                cursor.execute('''
                    INSERT INTO messages (sender, recipient, content, timestamp, priority, read)
                    VALUES (?, ?, ?, ?, ?, 0)
                ''', (
                    message.get('sender', 'system'),
                    recipient,
                    content,
                    datetime.now().isoformat(),
                    message.get('priority', 'normal')
                ))
            except sqlite3.OperationalError:
                # Fallback for older schema
                cursor.execute('''
                    INSERT INTO messages (id, sender, recipient, content, timestamp, read)
                    VALUES (?, ?, ?, ?, ?, 0)
                ''', (
                    f'msg_{int(time.time())}_{recipient}',
                    message.get('sender', 'system'),
                    recipient,
                    content,
                    datetime.now().isoformat()
                ))
            conn.commit()
            conn.close()

            return True
        except Exception as e:
            logger.error(f"Failed to route message: {e}")
            return False

    def execute_agent_task(self, agent: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue un task attraverso un agente specifico"""
        session_name = f'claude-{agent}'
        task_id = f'task_{int(time.time())}'

        # Store task in database
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (id, title, component, assigned_to, status, priority, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_id,
            task.get('title', 'Untitled Task'),
            task.get('component', 'general'),
            agent,
            'processing',
            task.get('priority', 5),
            datetime.now().isoformat(),
            json.dumps(task)
        ))
        conn.commit()

        # Send to TMUX session
        command = task.get('command', task.get('title', ''))
        subprocess.run([
            'tmux', 'send-keys', '-t', session_name,
            f'# Executing task: {task_id}', 'Enter'
        ])
        subprocess.run([
            'tmux', 'send-keys', '-t', session_name,
            command, 'Enter'
        ])

        # Update task status
        cursor.execute('''
            UPDATE tasks SET status = 'completed', updated_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), task_id))
        conn.commit()
        conn.close()

        return {
            'task_id': task_id,
            'agent': agent,
            'status': 'executed',
            'timestamp': datetime.now().isoformat()
        }

    def sync_knowledge_graph(self):
        """Sincronizza il knowledge graph con le attività degli agenti"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Get recent activities
        cursor.execute('''
            SELECT agent, activity, category, timestamp
            FROM activities
            WHERE timestamp > datetime('now', '-1 hour')
            ORDER BY timestamp DESC
            LIMIT 100
        ''')

        activities = cursor.fetchall()

        # Create knowledge connections
        for activity in activities:
            agent, description, category, timestamp = activity

            # Create knowledge node
            node_id = f'knowledge_{agent}_{category}_{int(time.time())}'
            cursor.execute('''
                INSERT OR IGNORE INTO components (id, name, type, owner, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                node_id,
                f'{agent}_{category}',
                'knowledge',
                agent,
                timestamp
            ))

        conn.commit()
        conn.close()
        logger.info("Knowledge graph synchronized")

    def broadcast_to_agents(self, message: str, priority: str = 'normal'):
        """Invia un messaggio broadcast a tutti gli agenti"""
        results = []

        for agent in self.agents:
            result = self.route_message_to_agent({
                'recipient': agent,
                'sender': 'orchestrator',
                'content': message,
                'priority': priority
            })
            results.append((agent, result))

        return results

    async def monitor_and_integrate(self):
        """Loop principale di monitoring e integrazione"""
        while True:
            try:
                # Sync agent states
                self.sync_agent_states()

                # Check for pending messages
                conn = self._get_db_connection()
                cursor = conn.cursor()
                # Try with new schema first
                try:
                    cursor.execute('''
                        SELECT id, sender, recipient, content
                        FROM messages
                        WHERE read = 0
                        LIMIT 10
                    ''')
                except sqlite3.OperationalError:
                    # Fallback to old schema
                    cursor.execute('''
                        SELECT id, sender, recipient, content
                        FROM messages
                        WHERE read = 0
                        LIMIT 10
                    ''')

                messages = cursor.fetchall()
                for msg in messages:
                    msg_id, sender, recipient, content = msg

                    # Route message
                    if self.route_message_to_agent({
                        'sender': sender,
                        'recipient': recipient,
                        'content': content
                    }):
                        # Mark as read
                        cursor.execute('UPDATE messages SET read = 1 WHERE id = ?', (msg_id,))

                conn.commit()
                conn.close()

                # Sync knowledge graph periodically
                if int(time.time()) % 60 == 0:  # Every minute
                    self.sync_knowledge_graph()

                # Sleep before next iteration
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Integration error: {e}")
                await asyncio.sleep(10)

    def initialize_integration(self):
        """Inizializza l'integrazione completa del sistema"""
        logger.info("🚀 Initializing Claude Squad Integration...")

        # Verify system health
        health = self.verify_system_health()
        logger.info(f"System Health: {health}")

        # Create missing database tables
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Ensure all tables exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_states (
                agent TEXT PRIMARY KEY,
                status TEXT,
                last_seen TEXT,
                current_task TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT,
                component TEXT,
                assigned_to TEXT,
                status TEXT,
                priority INTEGER,
                created_at TEXT,
                updated_at TEXT,
                metadata TEXT
            )
        ''')

        conn.commit()
        conn.close()

        # Initial sync
        self.sync_agent_states()
        self.sync_knowledge_graph()

        # Send initialization message to all agents
        self.broadcast_to_agents(
            "🎯 Integration Orchestrator initialized. All systems connected.",
            priority='high'
        )

        logger.info("✅ Integration initialized successfully!")

        return health

# API Endpoints for integration
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS for all routes and origins
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://localhost:5174", "http://localhost:5175",
                   "http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:8080"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "supports_credentials": True,
        "expose_headers": ["Content-Type", "Authorization"]
    }
})
orchestrator = IntegrationOrchestrator()

@app.route('/api/integration/health', methods=['GET', 'OPTIONS'])
def get_integration_health():
    """Get integration health status"""
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response

    response = jsonify(orchestrator.verify_system_health())
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/api/integration/sync')
def sync_all():
    """Force sync all components"""
    orchestrator.sync_agent_states()
    orchestrator.sync_knowledge_graph()
    return jsonify({'status': 'synced'})

@app.route('/api/integration/route', methods=['POST'])
def route_message():
    """Route a message to an agent"""
    data = request.json
    result = orchestrator.route_message_to_agent(data)
    return jsonify({'success': result})

@app.route('/api/integration/execute', methods=['POST'])
def execute_task():
    """Execute a task through an agent"""
    data = request.json
    agent = data.get('agent')
    task = data.get('task')

    if not agent or not task:
        return jsonify({'error': 'Agent and task required'}), 400

    result = orchestrator.execute_agent_task(agent, task)
    return jsonify(result)

@app.route('/api/integration/broadcast', methods=['POST'])
def broadcast():
    """Broadcast message to all agents"""
    data = request.json
    message = data.get('message', '')
    priority = data.get('priority', 'normal')

    results = orchestrator.broadcast_to_agents(message, priority)
    return jsonify({'results': results})

async def run_async_monitor():
    """Run the async monitoring loop"""
    await orchestrator.monitor_and_integrate()

def main():
    """Main entry point"""
    import threading

    # Initialize
    orchestrator.initialize_integration()

    # Start async monitor in background
    def run_monitor():
        asyncio.run(run_async_monitor())

    monitor_thread = threading.Thread(target=run_monitor, daemon=True)
    monitor_thread.start()

    # Start Flask API
    logger.info("🌐 Starting Integration API on port 5002...")
    app.run(host='0.0.0.0', port=5002, debug=False)

if __name__ == '__main__':
    main()