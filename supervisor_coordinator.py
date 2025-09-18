#!/usr/bin/env python3
"""
Supervisor Coordinator - Manages multi-agent system with small task delegation
"""
import sqlite3
import json
import time
import threading
from datetime import datetime
from pathlib import Path

# Database path
INBOX_DB = "/Users/erik/Desktop/claude-multiagent-system/langgraph-test/shared_inbox.db"

# Agent list
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

class SupervisorCoordinator:
    def __init__(self):
        self.db_path = INBOX_DB
        self.running = True
        self.agent_status = {agent: "unknown" for agent in AGENTS}
        self.init_database()

    def init_database(self):
        """Initialize inbox database if needed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create tables if they don't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent TEXT NOT NULL,
                task TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                response TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS heartbeat (
                agent TEXT PRIMARY KEY,
                last_seen TIMESTAMP,
                status TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def send_task(self, agent, task):
        """Send small task to agent (max 5 words)"""
        # Truncate to 5 words max
        words = task.split()[:5]
        task = ' '.join(words)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO inbox (agent, task, status, created_at)
            VALUES (?, ?, 'pending', ?)
        ''', (agent, task, datetime.now()))

        conn.commit()
        conn.close()

        print(f"[TASK SENT] {agent}: {task}")

    def check_responses(self):
        """Check for agent responses"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT agent, task, response, completed_at
            FROM inbox
            WHERE status = 'completed'
            AND completed_at > datetime('now', '-30 seconds')
            ORDER BY completed_at DESC
        ''')

        responses = cursor.fetchall()
        conn.close()

        for agent, task, response, completed_at in responses:
            print(f"[RESPONSE] {agent}: {task} -> {response}")
            self.agent_status[agent] = "active"

    def check_heartbeats(self):
        """Check agent heartbeats"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT agent, last_seen, status
            FROM heartbeat
            WHERE last_seen > datetime('now', '-60 seconds')
        ''')

        heartbeats = cursor.fetchall()
        conn.close()

        for agent, last_seen, status in heartbeats:
            self.agent_status[agent] = status or "alive"

    def initialize_agents(self):
        """Send initial heartbeat to all agents"""
        print("\n=== INITIALIZING AGENTS ===")

        for agent in AGENTS:
            self.send_task(agent, "heartbeat check")
            time.sleep(0.1)  # Small delay between sends

    def assign_micro_tasks(self):
        """Assign initial micro-tasks for system building"""
        print("\n=== ASSIGNING MICRO-TASKS ===")

        tasks = {
            "master": "init system core",
            "backend-api": "setup endpoints",
            "database": "create schemas",
            "frontend-ui": "init components",
            "testing": "setup test suite",
            "instagram": "check api keys",
            "queue-manager": "init queues",
            "deployment": "check docker"
        }

        for agent, task in tasks.items():
            self.send_task(agent, task)
            time.sleep(0.2)

    def coordination_loop(self):
        """Main coordination loop - runs every 30 seconds"""
        while self.running:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === COORDINATION CYCLE ===")

            # Check responses
            self.check_responses()

            # Check heartbeats
            self.check_heartbeats()

            # Display status
            print("\nAgent Status:")
            for agent, status in self.agent_status.items():
                print(f"  {agent}: {status}")

            # Send periodic heartbeats
            for agent in AGENTS:
                if self.agent_status[agent] != "active":
                    self.send_task(agent, "status check")

            # Wait 30 seconds
            time.sleep(30)

    def start(self):
        """Start the coordinator"""
        print("=== SUPERVISOR COORDINATOR STARTED ===")
        print(f"Database: {self.db_path}")
        print(f"Agents: {', '.join(AGENTS)}")

        # Initialize agents
        self.initialize_agents()
        time.sleep(2)

        # Assign initial tasks
        self.assign_micro_tasks()
        time.sleep(2)

        # Start coordination loop
        try:
            self.coordination_loop()
        except KeyboardInterrupt:
            print("\n=== COORDINATOR SHUTDOWN ===")
            self.running = False

if __name__ == "__main__":
    coordinator = SupervisorCoordinator()
    coordinator.start()