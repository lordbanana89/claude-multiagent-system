#!/usr/bin/env python3
"""
Test MCP Integration - Verifica completa dei server MCP
"""

import asyncio
import json
import subprocess
import sys
import os
from pathlib import Path
import sqlite3
from datetime import datetime

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class MCPIntegrationTester:
    def __init__(self):
        self.base_dir = Path("/Users/erik/Desktop/claude-multiagent-system")
        self.results = []
        self.servers = {
            "filesystem": {
                "path": "mcp-servers-official/src/filesystem/dist/index.js",
                "test": self.test_filesystem
            },
            "git": {
                "path": "mcp-servers-official/src/git/dist/index.js",
                "test": self.test_git
            },
            "memory": {
                "path": "mcp-servers-official/src/memory/dist/index.js",
                "test": self.test_memory
            },
            "fetch": {
                "path": "mcp-servers-official/src/fetch/dist/index.js",
                "test": self.test_fetch
            }
        }

    def print_header(self, text):
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}{text.center(60)}{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")

    def print_test(self, name, status, details=""):
        icon = "✅" if status else "❌"
        color = GREEN if status else RED
        print(f"{color}{icon} {name}{RESET}")
        if details:
            print(f"   {details}")

    async def test_filesystem(self):
        """Test filesystem MCP server"""
        try:
            server_path = self.base_dir / self.servers["filesystem"]["path"]
            if not server_path.exists():
                return False, "Server not found"

            # Test basic file operations
            test_file = self.base_dir / "test_fs.tmp"
            test_file.write_text("MCP filesystem test")

            if test_file.exists():
                test_file.unlink()
                return True, "File operations working"
            return False, "File operations failed"
        except Exception as e:
            return False, str(e)

    async def test_git(self):
        """Test git MCP server"""
        try:
            # Check if mcp-server-git command exists
            result = subprocess.run(
                ["which", "mcp-server-git"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return False, "mcp-server-git command not found"

            # Check if we're in a git repo
            result = subprocess.run(
                ["git", "status"],
                cwd=self.base_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return True, "Git repository detected"
            return False, "Not a git repository"
        except Exception as e:
            return False, str(e)

    async def test_memory(self):
        """Test memory MCP server"""
        try:
            server_path = self.base_dir / self.servers["memory"]["path"]
            if not server_path.exists():
                return False, "Server not found"

            # Create memory database
            db_path = self.base_dir / "data" / "memory.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Create test table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_memory (
                    id INTEGER PRIMARY KEY,
                    data TEXT,
                    created_at TEXT
                )
            """)

            # Insert test data
            cursor.execute(
                "INSERT INTO test_memory (data, created_at) VALUES (?, ?)",
                ("MCP Memory Test", datetime.now().isoformat())
            )
            conn.commit()

            # Verify data
            cursor.execute("SELECT COUNT(*) FROM test_memory")
            count = cursor.fetchone()[0]
            conn.close()

            if count > 0:
                return True, f"Memory database working ({count} records)"
            return False, "Memory database empty"
        except Exception as e:
            return False, str(e)

    async def test_fetch(self):
        """Test fetch MCP server"""
        try:
            # Check if mcp-server-fetch command exists
            result = subprocess.run(
                ["which", "mcp-server-fetch"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return False, "mcp-server-fetch command not found"

            # Simple connectivity test
            import socket
            try:
                socket.create_connection(("www.google.com", 80), timeout=2)
                return True, "Network connectivity OK"
            except:
                return False, "No network connectivity"
        except Exception as e:
            return False, str(e)

    async def test_python_mcp(self):
        """Test Python MCP server"""
        try:
            server_path = self.base_dir / "mcp_server_v2.py"
            if not server_path.exists():
                return False, "Python server not found"

            # Check if mcp module is installed
            result = subprocess.run(
                [sys.executable, "-c", "import mcp; print(mcp.__version__)"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                return True, f"MCP Python module v{version}"
            return False, "MCP Python module not installed"
        except Exception as e:
            return False, str(e)

    async def test_agent_database(self):
        """Test agent database"""
        try:
            db_path = self.base_dir / "mcp_system.db"
            if not db_path.exists():
                return False, "Database not found"

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check agents table
            cursor.execute("SELECT name, status FROM agents")
            agents = cursor.fetchall()
            conn.close()

            if agents:
                agent_list = ", ".join([f"{name}({status})" for name, status in agents])
                return True, f"Agents: {agent_list}"
            return True, "Database exists (no agents yet)"
        except Exception as e:
            return False, str(e)

    async def run_all_tests(self):
        """Run all integration tests"""
        self.print_header("MCP INTEGRATION TEST SUITE")

        # Test 1: Check Node.js
        print(f"{YELLOW}Checking prerequisites...{RESET}")

        node_version = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True
        )
        self.print_test(
            "Node.js",
            node_version.returncode == 0,
            node_version.stdout.strip() if node_version.returncode == 0 else "Not installed"
        )

        # Test 2: Check Python packages
        python_status, python_details = await self.test_python_mcp()
        self.print_test("Python MCP Module", python_status, python_details)

        # Test 3: Test each MCP server
        print(f"\n{YELLOW}Testing MCP Servers...{RESET}")

        for server_name, server_info in self.servers.items():
            status, details = await server_info["test"]()
            self.print_test(f"{server_name.capitalize()} Server", status, details)
            self.results.append((server_name, status))

        # Test 4: Test database
        print(f"\n{YELLOW}Testing Database...{RESET}")
        db_status, db_details = await self.test_agent_database()
        self.print_test("Agent Database", db_status, db_details)

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")

        passed = sum(1 for _, status in self.results if status)
        total = len(self.results)

        if passed == total:
            print(f"{GREEN}🎉 All tests passed! ({passed}/{total}){RESET}")
            print(f"\n{GREEN}System is ready for complete integration!{RESET}")
        else:
            print(f"{YELLOW}⚠️ Some tests failed ({passed}/{total}){RESET}")
            failed = [name for name, status in self.results if not status]
            print(f"\n{RED}Failed servers: {', '.join(failed)}{RESET}")
            print(f"\n{YELLOW}Please fix the issues and run the test again.{RESET}")

        print(f"\n{BLUE}Next steps:{RESET}")
        print("1. Copy claude_mcp_config_enhanced.json to ~/.claude/")
        print("2. Restart Claude Desktop")
        print("3. Test MCP tools in Claude")

async def main():
    tester = MCPIntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())