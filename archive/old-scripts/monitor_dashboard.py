#!/usr/bin/env python3
"""
Multi-Agent System Monitor Dashboard
"""
import sqlite3
import time
import os
from datetime import datetime, timedelta
import json

INBOX_DB = "/Users/erik/Desktop/claude-multiagent-system/langgraph-test/shared_inbox.db"
STATE_FILE = "/Users/erik/Desktop/claude-multiagent-system/supervisor_state.json"

class MonitorDashboard:
    def __init__(self):
        self.db_path = INBOX_DB
        self.state_file = STATE_FILE

    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')

    def get_statistics(self):
        """Get system statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Total tasks
        cursor.execute("SELECT COUNT(*) FROM inbox")
        stats['total_tasks'] = cursor.fetchone()[0]

        # Tasks by status
        cursor.execute('''
            SELECT status, COUNT(*)
            FROM inbox
            GROUP BY status
        ''')
        stats['by_status'] = dict(cursor.fetchall())

        # Tasks per agent
        cursor.execute('''
            SELECT agent,
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM inbox
            GROUP BY agent
        ''')
        stats['by_agent'] = {}
        for row in cursor.fetchall():
            stats['by_agent'][row[0]] = {
                'total': row[1],
                'completed': row[2]
            }

        conn.close()
        return stats

    def get_recent_activity(self, limit=10):
        """Get recent task activity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT agent, task, status, response,
                   created_at, completed_at
            FROM inbox
            ORDER BY
                CASE
                    WHEN completed_at IS NOT NULL THEN completed_at
                    ELSE created_at
                END DESC
            LIMIT ?
        ''', (limit,))

        activities = cursor.fetchall()
        conn.close()
        return activities

    def get_agent_status(self):
        """Get current agent status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT agent, last_seen, status, tasks_completed
            FROM heartbeat
            ORDER BY agent
        ''')

        agents = {}
        for agent, last_seen, status, tasks_completed in cursor.fetchall():
            is_active = False
            if last_seen:
                try:
                    last_seen_dt = datetime.strptime(last_seen, "%Y-%m-%d %H:%M:%S.%f")
                    is_active = (datetime.now() - last_seen_dt).seconds < 60
                except:
                    pass

            agents[agent] = {
                'last_seen': last_seen,
                'status': status,
                'tasks_completed': tasks_completed or 0,
                'is_active': is_active
            }

        conn.close()
        return agents

    def get_coordination_logs(self, limit=5):
        """Get recent coordination events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT timestamp, event, details
            FROM coordination_log
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))

        logs = cursor.fetchall()
        conn.close()
        return logs

    def load_supervisor_state(self):
        """Load supervisor state"""
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except:
            return None

    def display_dashboard(self):
        """Display the dashboard"""
        self.clear_screen()

        print("=" * 80)
        print("                     MULTI-AGENT SYSTEM MONITOR")
        print("=" * 80)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Load supervisor state
        sup_state = self.load_supervisor_state()
        if sup_state:
            print(f"Phase: {sup_state.get('current_phase', 'unknown')}")
            print(f"Last Save: {sup_state.get('last_save', 'unknown')}")

        # Statistics
        stats = self.get_statistics()
        print(f"\nTASK STATISTICS:")
        print(f"  Total Tasks: {stats['total_tasks']}")
        print(f"  Status: ", end="")
        for status, count in stats['by_status'].items():
            print(f"{status}={count} ", end="")
        print()

        # Agent Status
        print(f"\nAGENT STATUS:")
        print("-" * 80)
        print(f"{'Agent':<15} {'Status':<10} {'Active':<8} {'Tasks':<15} {'Last Seen'}")
        print("-" * 80)

        agents = self.get_agent_status()
        all_agents = [
            "master", "backend-api", "database", "frontend-ui",
            "testing", "instagram", "queue-manager", "deployment"
        ]

        for agent_name in all_agents:
            if agent_name in agents:
                agent = agents[agent_name]
                status_icon = "✓" if agent['is_active'] else "✗"
                active = "Yes" if agent['is_active'] else "No"

                agent_stats = stats['by_agent'].get(agent_name, {'total': 0, 'completed': 0})
                tasks = f"{agent_stats['completed']}/{agent_stats['total']}"

                last_seen = "Never"
                if agent['last_seen']:
                    try:
                        dt = datetime.strptime(agent['last_seen'], "%Y-%m-%d %H:%M:%S.%f")
                        last_seen = dt.strftime("%H:%M:%S")
                    except:
                        last_seen = agent['last_seen'][:19]

                print(f"{agent_name:<15} {status_icon:<10} {active:<8} {tasks:<15} {last_seen}")
            else:
                print(f"{agent_name:<15} {'?':<10} {'No':<8} {'0/0':<15} Never")

        # Recent Activity
        print(f"\nRECENT ACTIVITY:")
        print("-" * 80)
        activities = self.get_recent_activity(5)
        for activity in activities:
            agent, task, status, response, created, completed = activity
            timestamp = completed if completed else created
            if timestamp:
                try:
                    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = timestamp[:19]
            else:
                time_str = "unknown"

            status_icon = "✓" if status == "completed" else "⧗"
            print(f"{time_str} [{status_icon}] {agent}: {task[:20]}")
            if response and status == "completed":
                print(f"{'':>21} → {response[:40]}")

        # Coordination Logs
        print(f"\nCOORDINATION EVENTS:")
        print("-" * 80)
        logs = self.get_coordination_logs(3)
        for log in logs:
            timestamp, event, details = log
            if timestamp:
                try:
                    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = timestamp[:19]
            else:
                time_str = "unknown"

            print(f"{time_str} [{event}] {details[:50]}")

        print("\n" + "=" * 80)
        print("Press Ctrl+C to exit | Updates every 5 seconds")

    def run(self):
        """Run the dashboard"""
        try:
            while True:
                self.display_dashboard()
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n\nDashboard stopped.")

if __name__ == "__main__":
    dashboard = MonitorDashboard()
    dashboard.run()