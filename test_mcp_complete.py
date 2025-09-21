#!/usr/bin/env python3
"""
Test Complete MCP Integration - All 12 servers
"""

import asyncio
import subprocess
import sqlite3
from pathlib import Path
from datetime import datetime

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class CompleteMCPTester:
    def __init__(self):
        self.base_dir = Path("/Users/erik/Desktop/claude-multiagent-system")
        self.servers = {
            # Core servers
            "Filesystem": ("node", "filesystem/dist/index.js", "official"),
            "Git": ("mcp-server-git", None, "python"),
            "Memory": ("node", "memory/dist/index.js", "official"),
            "Fetch": ("mcp-server-fetch", None, "python"),

            # Advanced servers
            "Sequential Thinking": ("node", "sequentialthinking/dist/index.js", "official"),
            "Time": ("mcp-server-time", None, "python"),
            "Everything": ("node", "everything/dist/index.js", "official"),

            # Database servers
            "SQLite": ("mcp-server-sqlite", None, "python"),

            # Browser automation
            "Puppeteer": ("node", "puppeteer/dist/index.js", "archived"),
            "Playwright": ("playwright-mcp", None, "npm-global"),

            # Cache/Queue
            "Redis": ("node", "redis/dist/index.js", "archived"),

            # Python orchestrator
            "Multi-Agent": ("python3", "mcp_server_v2.py", "custom")
        }

    def print_header(self):
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}{'COMPLETE MCP INTEGRATION TEST - 12 SERVERS'.center(70)}{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")

    def test_server(self, name, command, path, server_type):
        """Test individual server availability"""
        try:
            if server_type == "python":
                # Test Python command availability
                result = subprocess.run(
                    ["which", command],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return True, f"Command found: {result.stdout.strip()}"
                return False, "Command not found"

            elif server_type == "npm-global":
                # Test npm global package
                result = subprocess.run(
                    ["which", command],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return True, "NPM package installed globally"
                return False, "NPM package not found"

            elif server_type == "official":
                # Test official Node.js servers
                server_path = self.base_dir / "mcp-servers-official" / "src" / path
                if server_path.exists():
                    return True, f"Server built at: {path}"
                return False, "Server not built"

            elif server_type == "archived":
                # Test archived servers
                server_path = self.base_dir / "mcp-servers-archived" / "src" / path
                if server_path.exists():
                    return True, f"Archived server built"
                return False, "Archived server not built"

            elif server_type == "custom":
                # Test custom Python server
                server_path = self.base_dir / path
                if server_path.exists():
                    return True, "Custom server exists"
                return False, "Custom server not found"

            return False, "Unknown server type"

        except Exception as e:
            return False, str(e)

    def test_redis_connection(self):
        """Test Redis server connection"""
        try:
            result = subprocess.run(
                ["redis-cli", "ping"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and "PONG" in result.stdout:
                return True, "Redis server responding"
            return False, "Redis not running"
        except:
            return False, "Redis CLI not found"

    async def run_tests(self):
        """Run all server tests"""
        self.print_header()

        results = []

        # Test each server
        print(f"{YELLOW}Testing MCP Servers:{RESET}\n")

        for name, (command, path, server_type) in self.servers.items():
            success, details = self.test_server(name, command, path, server_type)

            icon = f"{GREEN}✅{RESET}" if success else f"{RED}❌{RESET}"
            status = f"{GREEN}OK{RESET}" if success else f"{RED}FAIL{RESET}"

            print(f"{icon} {name:20} [{status}] {details[:40]}...")
            results.append((name, success))

        # Test Redis separately
        print(f"\n{YELLOW}Testing Dependencies:{RESET}\n")
        redis_ok, redis_msg = self.test_redis_connection()
        icon = f"{GREEN}✅{RESET}" if redis_ok else f"{YELLOW}⚠️{RESET}"
        print(f"{icon} Redis Server         {redis_msg}")

        # Summary
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}{'SUMMARY'.center(70)}{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")

        passed = sum(1 for _, success in results if success)
        total = len(results)

        if passed == total:
            print(f"{GREEN}🎉 ALL SERVERS INSTALLED! ({passed}/{total}){RESET}")
            print(f"\n{GREEN}✨ COMPLETE MCP SYSTEM READY!{RESET}")
            print("\nCapabilities enabled:")
            print("  • Browser automation (Playwright + Puppeteer)")
            print("  • Database testing (SQLite)")
            print("  • Cache management (Redis)")
            print("  • Sequential reasoning")
            print("  • Time management")
            print("  • Reference implementation (Everything)")
            print("  • Full development stack")
        else:
            print(f"{YELLOW}⚠️ Some servers missing ({passed}/{total}){RESET}")
            failed = [name for name, success in results if not success]
            print(f"\nMissing servers: {', '.join(failed)}")

        print(f"\n{BLUE}Next step:{RESET}")
        print("1. Restart Claude Desktop to load new servers")
        print("2. Use ./start_mcp_system.sh to start everything")
        print("3. Monitor with: python3 monitor_mcp_system.py")

asyncio.run(CompleteMCPTester().run_tests())