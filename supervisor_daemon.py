#!/usr/bin/env python3
"""
Supervisor Daemon - Background coordinator for multi-agent system
"""
import sqlite3
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
import signal
import sys

INBOX_DB = "/Users/erik/Desktop/claude-multiagent-system/langgraph-test/shared_inbox.db"
STATE_FILE = "/Users/erik/Desktop/claude-multiagent-system/supervisor_state.json"

AGENTS = [
    "master",
    "backend-api",
    "database",
    "frontend-ui",
    "testing",
    "instagram",
    "queue-manager",
    "deployment"
]

# System building micro-tasks (max 5 words each)
SYSTEM_TASKS = {
    "phase1": {
        "master": ["init core system", "setup message bus", "create state manager"],
        "backend-api": ["setup express server", "create api routes", "init middleware"],
        "database": ["create user table", "create task table", "setup indexes"],
        "frontend-ui": ["init react app", "create base layout", "setup routing"],
        "testing": ["setup jest config", "create test utils", "init coverage"],
        "instagram": ["check api auth", "setup rate limits", "init client"],
        "queue-manager": ["create job queue", "setup workers", "init redis"],
        "deployment": ["check docker", "create compose file", "setup nginx"]
    },
    "phase2": {
        "master": ["coordinate agents", "monitor health", "handle errors"],
        "backend-api": ["implement auth", "add validation", "setup websocket"],
        "database": ["add migrations", "optimize queries", "setup backup"],
        "frontend-ui": ["add components", "implement state", "add styling"],
        "testing": ["write unit tests", "add integration", "setup e2e"],
        "instagram": ["implement posting", "add scheduling", "handle media"],
        "queue-manager": ["process jobs", "handle retries", "monitor queues"],
        "deployment": ["setup ci cd", "configure env", "add monitoring"]
    }
}

class SupervisorDaemon:
    def __init__(self):
        self.db_path = INBOX_DB
        self.state_file = STATE_FILE
        self.running = True
        self.current_phase = "phase1"
        self.task_index = {agent: 0 for agent in AGENTS}
        self.agent_status = {agent: {"status": "unknown", "last_seen": None} for agent in AGENTS}
        self.statistics = {
            "tasks_sent": 0,
            "tasks_completed": 0,
            "start_time": datetime.now().isoformat()
        }

        self.load_state()
        self.init_database()
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent TEXT NOT NULL,
                task TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                response TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS heartbeat (
                agent TEXT PRIMARY KEY,
                last_seen TIMESTAMP,
                status TEXT,
                tasks_completed INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coordination_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event TEXT,
                details TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def load_state(self):
        """Load saved state if exists"""
        if Path(self.state_file).exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.current_phase = state.get("current_phase", "phase1")
                    self.task_index = state.get("task_index", self.task_index)
                    self.statistics = state.get("statistics", self.statistics)
                    print(f"[STATE] Loaded previous state: phase={self.current_phase}")
            except:
                pass

    def save_state(self):
        """Save current state"""
        state = {
            "current_phase": self.current_phase,
            "task_index": self.task_index,
            "agent_status": self.agent_status,
            "statistics": self.statistics,
            "last_save": datetime.now().isoformat()
        }

        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)

    def log_event(self, event, details=""):
        """Log coordination events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO coordination_log (event, details)
            VALUES (?, ?)
        ''', (event, details))

        conn.commit()
        conn.close()

    def send_task(self, agent, task, priority=5):
        """Send task to agent (max 5 words)"""
        words = task.split()[:5]
        task = ' '.join(words)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO inbox (agent, task, status, priority)
            VALUES (?, ?, 'pending', ?)
        ''', (agent, task, priority))

        conn.commit()
        conn.close()

        self.statistics["tasks_sent"] += 1
        self.log_event("task_sent", f"{agent}: {task}")
        print(f"[→] {agent}: {task}")

    def check_responses(self):
        """Check for completed tasks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get recent completions
        cursor.execute('''
            SELECT agent, task, response, completed_at
            FROM inbox
            WHERE status = 'completed'
            AND completed_at > datetime('now', '-60 seconds')
            ORDER BY completed_at DESC
        ''')

        responses = cursor.fetchall()

        for agent, task, response, completed_at in responses:
            print(f"[✓] {agent}: {task} → {response}")
            self.statistics["tasks_completed"] += 1

            # Update agent status
            self.agent_status[agent]["status"] = "active"
            self.agent_status[agent]["last_seen"] = completed_at

        conn.close()

    def check_heartbeats(self):
        """Check agent heartbeats"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT agent, last_seen, status, tasks_completed
            FROM heartbeat
        ''')

        heartbeats = cursor.fetchall()
        conn.close()

        for agent, last_seen, status, tasks_completed in heartbeats:
            if last_seen:
                last_seen_dt = datetime.strptime(last_seen, "%Y-%m-%d %H:%M:%S.%f")
                if (datetime.now() - last_seen_dt).seconds < 60:
                    self.agent_status[agent]["status"] = "alive"
                    self.agent_status[agent]["last_seen"] = last_seen

    def assign_next_tasks(self):
        """Assign next batch of tasks to agents"""
        if self.current_phase not in SYSTEM_TASKS:
            return

        phase_tasks = SYSTEM_TASKS[self.current_phase]
        all_done = True

        for agent in AGENTS:
            if agent not in phase_tasks:
                continue

            agent_tasks = phase_tasks[agent]
            idx = self.task_index[agent]

            if idx < len(agent_tasks):
                # Agent has more tasks
                all_done = False

                # Only send if agent is responsive
                if self.agent_status[agent]["status"] in ["active", "alive", "unknown"]:
                    self.send_task(agent, agent_tasks[idx])
                    self.task_index[agent] = idx + 1

        # Check if phase complete
        if all_done:
            if self.current_phase == "phase1":
                print("\n[PHASE] Completed Phase 1, starting Phase 2")
                self.current_phase = "phase2"
                self.task_index = {agent: 0 for agent in AGENTS}
                self.log_event("phase_complete", "phase1")
            else:
                print("\n[COMPLETE] All phases completed!")
                self.log_event("system_complete", "All tasks done")

    def display_status(self):
        """Display current system status"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === STATUS ===")
        print(f"Phase: {self.current_phase}")
        print(f"Tasks: {self.statistics['tasks_sent']} sent, {self.statistics['tasks_completed']} completed")

        print("\nAgents:")
        for agent, info in self.agent_status.items():
            status_icon = "✓" if info["status"] == "active" else "○"
            print(f"  {status_icon} {agent}: {info['status']}")

    def coordination_loop(self):
        """Main coordination loop"""
        cycle = 0

        while self.running:
            cycle += 1

            # Check responses
            self.check_responses()

            # Check heartbeats
            self.check_heartbeats()

            # Send heartbeats every 2 cycles
            if cycle % 2 == 0:
                for agent in AGENTS:
                    if self.agent_status[agent]["status"] == "unknown":
                        self.send_task(agent, "heartbeat", priority=1)

            # Assign new tasks every 3 cycles
            if cycle % 3 == 0:
                self.assign_next_tasks()

            # Display status every 4 cycles
            if cycle % 4 == 0:
                self.display_status()

            # Save state every 5 cycles
            if cycle % 5 == 0:
                self.save_state()

            # Wait 10 seconds
            time.sleep(10)

    def shutdown(self, signum=None, frame=None):
        """Graceful shutdown"""
        print("\n[SHUTDOWN] Supervisor daemon stopping...")
        self.running = False
        self.save_state()
        self.log_event("shutdown", "Daemon stopped")
        sys.exit(0)

    def start(self):
        """Start the daemon"""
        print("=== SUPERVISOR DAEMON STARTED ===")
        print(f"Database: {self.db_path}")
        print(f"State: {self.state_file}")
        print(f"Phase: {self.current_phase}")

        self.log_event("startup", f"Daemon started, phase={self.current_phase}")

        # Initial heartbeat
        print("\n[INIT] Sending initial heartbeats...")
        for agent in AGENTS:
            self.send_task(agent, "heartbeat", priority=1)

        time.sleep(3)

        # Start main loop
        try:
            self.coordination_loop()
        except Exception as e:
            print(f"[ERROR] {e}")
            self.shutdown()

if __name__ == "__main__":
    daemon = SupervisorDaemon()
    daemon.start()