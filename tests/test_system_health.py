#!/usr/bin/env python3
"""
🔍 System Health Test Suite
Test essenziali per verificare lo stato del sistema
"""

import sys
import os
import json
import time
import redis
import sqlite3
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from colorama import init, Fore, Style

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import (
    REDIS_URL,
    AUTH_DB_PATH,
    SHARED_STATE_FILE,
    AGENT_SESSIONS,
    PROJECT_ROOT,
    TMUX_BIN
)

init(autoreset=True)

class SystemHealthTester:
    """Test suite per verificare la salute del sistema"""

    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0

    def test(self, name: str, func, *args, **kwargs) -> bool:
        """Esegue un test e registra il risultato"""
        self.total_tests += 1
        try:
            result = func(*args, **kwargs)
            if result:
                self.passed_tests += 1
                print(f"{Fore.GREEN}✓{Style.RESET_ALL} {name}")
                self.results.append((name, True, None))
                return True
            else:
                print(f"{Fore.RED}✗{Style.RESET_ALL} {name}")
                self.results.append((name, False, "Test failed"))
                return False
        except Exception as e:
            print(f"{Fore.RED}✗{Style.RESET_ALL} {name}: {str(e)}")
            self.results.append((name, False, str(e)))
            return False

    def test_redis_connection(self) -> bool:
        """Test connessione Redis"""
        try:
            r = redis.Redis.from_url(REDIS_URL)
            r.ping()

            # Test write/read
            test_key = "test:health:check"
            test_value = f"test_{int(time.time())}"
            r.set(test_key, test_value, ex=10)
            retrieved = r.get(test_key)

            return retrieved.decode() == test_value
        except Exception:
            return False

    def test_tmux_availability(self) -> bool:
        """Test disponibilità TMUX"""
        try:
            result = subprocess.run(
                [TMUX_BIN, "ls"],
                capture_output=True,
                text=True
            )
            return result.returncode in [0, 1]  # 0=sessions exist, 1=no sessions
        except Exception:
            return False

    def test_tmux_sessions(self) -> Dict[str, bool]:
        """Test presenza sessioni TMUX richieste"""
        try:
            result = subprocess.run(
                [TMUX_BIN, "ls", "-F"],
                capture_output=True,
                text=True
            )

            existing_sessions = []
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if ':' in line:
                        session_name = line.split(':')[0]
                        existing_sessions.append(session_name)

            session_status = {}
            for agent_id, session_name in AGENT_SESSIONS.items():
                session_status[agent_id] = session_name in existing_sessions

            return session_status
        except Exception:
            return {}

    def test_auth_database(self) -> bool:
        """Test database autenticazione"""
        try:
            if not AUTH_DB_PATH.exists():
                AUTH_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
                # Create if not exists
                conn = sqlite3.connect(AUTH_DB_PATH)
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                conn.close()

            conn = sqlite3.connect(AUTH_DB_PATH)
            cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            count = cursor.fetchone()[0]
            conn.close()

            return count > 0
        except Exception:
            return False

    def test_shared_state_file(self) -> bool:
        """Test file shared state"""
        try:
            if SHARED_STATE_FILE.exists():
                with open(SHARED_STATE_FILE, 'r') as f:
                    data = json.load(f)
                    return isinstance(data, dict)
            else:
                # Create default
                SHARED_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
                default_state = {
                    "agents": {},
                    "tasks": {},
                    "messages": []
                }
                with open(SHARED_STATE_FILE, 'w') as f:
                    json.dump(default_state, f, indent=2)
                return True
        except Exception:
            return False

    def test_python_dependencies(self) -> Dict[str, bool]:
        """Test dipendenze Python"""
        required_packages = [
            'redis',
            'dramatiq',
            'streamlit',
            'fastapi',
            'uvicorn',
            'sqlalchemy',
            'pytest',
            'langgraph'
        ]

        package_status = {}
        for package in required_packages:
            try:
                __import__(package)
                package_status[package] = True
            except ImportError:
                package_status[package] = False

        return package_status

    def test_port_availability(self) -> Dict[int, bool]:
        """Test porte disponibili"""
        import socket

        critical_ports = {
            6379: "Redis",
            8501: "Streamlit",
            8090: "MCP API",
            8123: "LangGraph"
        }

        port_status = {}
        for port, service in critical_ports.items():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.5)
                    result = s.connect_ex(('localhost', port))
                    port_status[port] = (result == 0, service)
            except Exception:
                port_status[port] = (False, service)

        return port_status

    def test_directory_structure(self) -> Dict[str, bool]:
        """Test struttura directory"""
        required_dirs = [
            'config',
            'core',
            'agents',
            'instructions',
            'tests',
            'scripts',
            'langgraph-test'
        ]

        dir_status = {}
        for dir_name in required_dirs:
            dir_path = PROJECT_ROOT / dir_name
            dir_status[dir_name] = dir_path.exists() and dir_path.is_dir()

        return dir_status

    def run_all_tests(self):
        """Esegue tutti i test"""
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"{Fore.CYAN}🔍 System Health Check")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}\n")

        # Core Services
        print(f"{Fore.YELLOW}[Core Services]{Style.RESET_ALL}")
        self.test("Redis Connection", self.test_redis_connection)
        self.test("TMUX Availability", self.test_tmux_availability)
        self.test("Auth Database", self.test_auth_database)
        self.test("Shared State File", self.test_shared_state_file)

        # Directory Structure
        print(f"\n{Fore.YELLOW}[Directory Structure]{Style.RESET_ALL}")
        dir_status = self.test_directory_structure()
        for dir_name, exists in dir_status.items():
            status = f"{Fore.GREEN}✓" if exists else f"{Fore.RED}✗"
            print(f"  {status} {dir_name}")

        # Python Dependencies
        print(f"\n{Fore.YELLOW}[Python Dependencies]{Style.RESET_ALL}")
        dep_status = self.test_python_dependencies()
        for package, installed in dep_status.items():
            status = f"{Fore.GREEN}✓" if installed else f"{Fore.RED}✗"
            print(f"  {status} {package}")

        # Port Availability
        print(f"\n{Fore.YELLOW}[Port Status]{Style.RESET_ALL}")
        port_status = self.test_port_availability()
        for port, (available, service) in port_status.items():
            status = f"{Fore.GREEN}✓ IN USE" if available else f"{Fore.YELLOW}○ FREE"
            print(f"  {status} Port {port} ({service})")

        # TMUX Sessions
        print(f"\n{Fore.YELLOW}[TMUX Sessions]{Style.RESET_ALL}")
        session_status = self.test_tmux_sessions()
        if session_status:
            for agent_id, exists in session_status.items():
                status = f"{Fore.GREEN}✓" if exists else f"{Fore.YELLOW}○"
                print(f"  {status} {agent_id} ({AGENT_SESSIONS[agent_id]})")
        else:
            print(f"  {Fore.YELLOW}No TMUX sessions found")

        # Summary
        print(f"\n{Fore.CYAN}{'='*50}")
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0

        if success_rate >= 80:
            color = Fore.GREEN
            status = "HEALTHY"
        elif success_rate >= 50:
            color = Fore.YELLOW
            status = "DEGRADED"
        else:
            color = Fore.RED
            status = "CRITICAL"

        print(f"{color}System Status: {status}")
        print(f"Tests Passed: {self.passed_tests}/{self.total_tests} ({success_rate:.1f}%)")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}\n")

        # Recommendations
        if success_rate < 100:
            print(f"{Fore.YELLOW}Recommendations:{Style.RESET_ALL}")

            if not self.test_redis_connection():
                print(f"  • Start Redis: redis-server")

            missing_deps = [pkg for pkg, installed in dep_status.items() if not installed]
            if missing_deps:
                print(f"  • Install missing packages: pip install {' '.join(missing_deps)}")

            missing_dirs = [d for d, exists in dir_status.items() if not exists]
            if missing_dirs:
                print(f"  • Create missing directories: {', '.join(missing_dirs)}")

            if not session_status or not any(session_status.values()):
                print(f"  • Start TMUX sessions: ./scripts/start_complete_system.sh")

        return success_rate >= 50


def main():
    """Main function"""
    tester = SystemHealthTester()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()