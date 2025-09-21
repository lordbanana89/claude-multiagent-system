#!/usr/bin/env python3
"""
MCP System Monitor - Real-time dashboard for MCP servers and agents
"""

import asyncio
import sqlite3
import json
import subprocess
import psutil
from datetime import datetime
from pathlib import Path
import time
import os
import sys

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

class MCPSystemMonitor:
    def __init__(self):
        self.base_dir = Path("/Users/erik/Desktop/claude-multiagent-system")
        self.memory_db = self.base_dir / "data" / "memory.db"
        self.system_db = self.base_dir / "mcp_system.db"
        self.refresh_interval = 2  # seconds

    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')

    def get_process_status(self, process_name):
        """Check if a process is running"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if process_name in cmdline:
                    return True, proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False, None

    def get_mcp_servers_status(self):
        """Check status of MCP servers"""
        servers = {
            "Filesystem": ("node", "filesystem/dist/index.js"),
            "Git": ("mcp-server-git", ""),
            "Memory": ("node", "memory/dist/index.js"),
            "Fetch": ("mcp-server-fetch", ""),
            "Python MCP": ("python", "mcp_server_v2.py")
        }

        status_list = []
        for server_name, (process, identifier) in servers.items():
            is_running = False
            if identifier:
                is_running, pid = self.get_process_status(identifier)
            else:
                is_running, pid = self.get_process_status(process)

            status_list.append({
                "name": server_name,
                "running": is_running,
                "pid": pid
            })

        return status_list

    def get_agents_status(self):
        """Get status of all agents from database"""
        try:
            conn = sqlite3.connect(str(self.system_db))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, status, current_task, updated_at
                FROM agents
                ORDER BY name
            """)
            agents = cursor.fetchall()
            conn.close()
            return agents
        except Exception as e:
            return []

    def get_memory_stats(self):
        """Get memory database statistics"""
        try:
            if not self.memory_db.exists():
                return {"entities": 0, "observations": 0, "relations": 0}

            conn = sqlite3.connect(str(self.memory_db))
            cursor = conn.cursor()

            stats = {}
            for table in ["entities", "observations", "relations"]:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]

            conn.close()
            return stats
        except:
            return {"entities": 0, "observations": 0, "relations": 0}

    def get_git_status(self):
        """Get current git branch and changes"""
        try:
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.base_dir,
                capture_output=True,
                text=True
            )
            branch = result.stdout.strip() if result.returncode == 0 else "unknown"

            # Get number of changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.base_dir,
                capture_output=True,
                text=True
            )
            changes = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0

            return {"branch": branch, "changes": changes}
        except:
            return {"branch": "unknown", "changes": 0}

    def get_api_status(self):
        """Check if API servers are running"""
        apis = [
            {"name": "Main API", "port": 5001},
            {"name": "React Dashboard", "port": 5173}
        ]

        for api in apis:
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', api['port']))
                sock.close()
                api['status'] = result == 0
            except:
                api['status'] = False

        return apis

    def display_dashboard(self):
        """Display the monitoring dashboard"""
        self.clear_screen()

        # Header
        print(f"{BLUE}{BOLD}╔{'═'*70}╗{RESET}")
        print(f"{BLUE}{BOLD}║{'MCP SYSTEM MONITOR'.center(70)}║{RESET}")
        print(f"{BLUE}{BOLD}║{datetime.now().strftime('%Y-%m-%d %H:%M:%S').center(70)}║{RESET}")
        print(f"{BLUE}{BOLD}╚{'═'*70}╝{RESET}\n")

        # MCP Servers Status
        print(f"{CYAN}{BOLD}MCP SERVERS:{RESET}")
        print("─" * 70)
        servers = self.get_mcp_servers_status()
        for server in servers:
            status_icon = f"{GREEN}●{RESET}" if server['running'] else f"{RED}○{RESET}"
            pid_info = f"(PID: {server['pid']})" if server['pid'] else ""
            print(f"  {status_icon} {server['name']:20} {'Running' if server['running'] else 'Stopped':10} {pid_info}")

        # Agents Status
        print(f"\n{CYAN}{BOLD}AGENTS STATUS:{RESET}")
        print("─" * 70)
        agents = self.get_agents_status()
        for name, status, task, updated_at in agents:
            if status in ['active', 'monitoring', 'coordinating', 'developing', 'validating']:
                status_color = GREEN
                icon = "●"
            elif status == 'idle':
                status_color = YELLOW
                icon = "○"
            else:
                status_color = RED
                icon = "✗"

            task_info = f"[{task[:30]}...]" if task and len(task) > 30 else f"[{task}]" if task else ""
            print(f"  {status_color}{icon}{RESET} {name:15} {status:12} {task_info}")

        # Memory Database Stats
        print(f"\n{CYAN}{BOLD}KNOWLEDGE GRAPH:{RESET}")
        print("─" * 70)
        memory_stats = self.get_memory_stats()
        print(f"  Entities:     {memory_stats['entities']:5}")
        print(f"  Observations: {memory_stats['observations']:5}")
        print(f"  Relations:    {memory_stats['relations']:5}")

        # Git Status
        print(f"\n{CYAN}{BOLD}GIT STATUS:{RESET}")
        print("─" * 70)
        git_info = self.get_git_status()
        print(f"  Branch:  {git_info['branch']}")
        print(f"  Changes: {git_info['changes']}")

        # API Status
        print(f"\n{CYAN}{BOLD}API ENDPOINTS:{RESET}")
        print("─" * 70)
        apis = self.get_api_status()
        for api in apis:
            status_icon = f"{GREEN}●{RESET}" if api['status'] else f"{RED}○{RESET}"
            url = f"http://localhost:{api['port']}" if api['status'] else "Not running"
            print(f"  {status_icon} {api['name']:20} Port {api['port']:5} {url}")

        # System Resources
        print(f"\n{CYAN}{BOLD}SYSTEM RESOURCES:{RESET}")
        print("─" * 70)
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(str(self.base_dir))

        print(f"  CPU Usage:    {cpu_percent:5.1f}%")
        print(f"  Memory Usage: {memory.percent:5.1f}% ({memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB)")
        print(f"  Disk Usage:   {disk.percent:5.1f}% ({disk.used / (1024**3):.1f}GB / {disk.total / (1024**3):.1f}GB)")

        # Footer
        print(f"\n{BLUE}{'─'*70}{RESET}")
        print(f"{YELLOW}Press Ctrl+C to exit | Refreshing every {self.refresh_interval} seconds{RESET}")

    async def run(self):
        """Run the monitoring dashboard"""
        print(f"{GREEN}Starting MCP System Monitor...{RESET}")

        try:
            while True:
                self.display_dashboard()
                await asyncio.sleep(self.refresh_interval)
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Monitor stopped.{RESET}")
            sys.exit(0)

def main():
    monitor = MCPSystemMonitor()
    asyncio.run(monitor.run())

if __name__ == "__main__":
    main()