#!/usr/bin/env python3
"""
Agent Responder - Simulates agent responses for testing
"""
import sqlite3
import time
import random
from datetime import datetime
import sys

INBOX_DB = "/Users/erik/Desktop/claude-multiagent-system/langgraph-test/shared_inbox.db"

class AgentResponder:
    def __init__(self, agent_name):
        self.agent_name = agent_name
        self.db_path = INBOX_DB

    def update_heartbeat(self):
        """Update heartbeat status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO heartbeat (agent, last_seen, status)
            VALUES (?, ?, 'active')
        ''', (self.agent_name, datetime.now()))

        conn.commit()
        conn.close()

    def get_pending_tasks(self):
        """Get pending tasks for this agent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, task
            FROM inbox
            WHERE agent = ? AND status = 'pending'
            ORDER BY created_at ASC
            LIMIT 5
        ''', (self.agent_name,))

        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def complete_task(self, task_id, task, response):
        """Mark task as completed with response"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE inbox
            SET status = 'completed',
                completed_at = ?,
                response = ?
            WHERE id = ?
        ''', (datetime.now(), response, task_id))

        conn.commit()
        conn.close()

        print(f"[{self.agent_name}] Completed: {task} -> {response}")

    def process_task(self, task):
        """Process a specific task and generate response"""
        responses = {
            "heartbeat check": "alive",
            "status check": "ready",
            "init system core": "core initialized",
            "setup endpoints": "endpoints ready",
            "create schemas": "schemas created",
            "init components": "components ready",
            "setup test suite": "tests configured",
            "check api keys": "keys verified",
            "init queues": "queues started",
            "check docker": "docker running"
        }

        # Return specific response or generic
        return responses.get(task, f"done: {task[:10]}")

    def run(self):
        """Main agent loop"""
        print(f"=== AGENT {self.agent_name} STARTED ===")

        while True:
            try:
                # Update heartbeat
                self.update_heartbeat()

                # Get pending tasks
                tasks = self.get_pending_tasks()

                for task_id, task in tasks:
                    # Process with small delay
                    time.sleep(random.uniform(0.5, 2.0))

                    # Generate response
                    response = self.process_task(task)

                    # Complete task
                    self.complete_task(task_id, task, response)

                # Wait before next check
                time.sleep(5)

            except KeyboardInterrupt:
                print(f"\n[{self.agent_name}] Shutdown")
                break
            except Exception as e:
                print(f"[{self.agent_name}] Error: {e}")
                time.sleep(10)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent_responder.py <agent-name>")
        sys.exit(1)

    agent_name = sys.argv[1]
    responder = AgentResponder(agent_name)
    responder.run()