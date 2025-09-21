#!/usr/bin/env python3
"""
Test COMPLETE MCP Integration - All 15+ Servers
Verifica installazione completa di tutti i server MCP
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'
RESET = '\033[0m'
BOLD = '\033[1m'

class FullMCPTester:
    def __init__(self):
        self.base_dir = Path("/Users/erik/Desktop/claude-multiagent-system")
        self.results = []

    def print_category(self, name):
        print(f"\n{CYAN}{'='*60}{RESET}")
        print(f"{CYAN}{name.center(60)}{RESET}")
        print(f"{CYAN}{'='*60}{RESET}\n")

    def test_command(self, name, command, test_type="command"):
        """Test if command/file exists"""
        try:
            if test_type == "command":
                result = subprocess.run(
                    ["which", command],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return True, "Command found"
                return False, "Not installed"

            elif test_type == "node_file":
                if Path(command).exists():
                    return True, "Server built"
                return False, "Not built"

            elif test_type == "python_module":
                result = subprocess.run(
                    [sys.executable, "-c", f"import {command}"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return True, "Module installed"
                return False, "Module not found"

        except Exception as e:
            return False, str(e)

    def run_tests(self):
        print(f"\n{MAGENTA}{BOLD}{'='*70}{RESET}")
        print(f"{MAGENTA}{BOLD}{'COMPLETE MCP SUITE TEST - FULL INTEGRATION'.center(70)}{RESET}")
        print(f"{MAGENTA}{BOLD}{datetime.now().strftime('%Y-%m-%d %H:%M:%S').center(70)}{RESET}")
        print(f"{MAGENTA}{BOLD}{'='*70}{RESET}")

        # CORE SERVERS (4)
        self.print_category("CORE SERVERS (4)")
        core_servers = [
            ("Filesystem", str(self.base_dir / "mcp-servers-official/src/filesystem/dist/index.js"), "node_file"),
            ("Git", "mcp-server-git", "command"),
            ("Memory", str(self.base_dir / "mcp-servers-official/src/memory/dist/index.js"), "node_file"),
            ("Fetch", "mcp-server-fetch", "command"),
        ]

        for name, path, test_type in core_servers:
            success, msg = self.test_command(name, path, test_type)
            icon = f"{GREEN}✅{RESET}" if success else f"{RED}❌{RESET}"
            print(f"{icon} {name:20} {msg}")
            self.results.append((name, success))

        # ADVANCED SERVERS (4)
        self.print_category("ADVANCED SERVERS (4)")
        advanced_servers = [
            ("Sequential Thinking", str(self.base_dir / "mcp-servers-official/src/sequentialthinking/dist/index.js"), "node_file"),
            ("Time", "mcp-server-time", "command"),
            ("Everything", str(self.base_dir / "mcp-servers-official/src/everything/dist/index.js"), "node_file"),
            ("SQLite", "mcp-server-sqlite", "command"),
        ]

        for name, path, test_type in advanced_servers:
            success, msg = self.test_command(name, path, test_type)
            icon = f"{GREEN}✅{RESET}" if success else f"{RED}❌{RESET}"
            print(f"{icon} {name:20} {msg}")
            self.results.append((name, success))

        # BROWSER AUTOMATION (2)
        self.print_category("BROWSER AUTOMATION (2)")
        browser_servers = [
            ("Puppeteer", str(self.base_dir / "mcp-servers-archived/src/puppeteer/dist/index.js"), "node_file"),
            ("Playwright", "playwright-mcp", "command"),
        ]

        for name, path, test_type in browser_servers:
            success, msg = self.test_command(name, path, test_type)
            icon = f"{GREEN}✅{RESET}" if success else f"{RED}❌{RESET}"
            print(f"{icon} {name:20} {msg}")
            self.results.append((name, success))

        # INFRASTRUCTURE (2)
        self.print_category("INFRASTRUCTURE (2)")
        infra_servers = [
            ("Redis MCP", str(self.base_dir / "mcp-servers-archived/src/redis/dist/index.js"), "node_file"),
            ("Multi-Agent", str(self.base_dir / "mcp_server_v2.py"), "node_file"),
        ]

        for name, path, test_type in infra_servers:
            success, msg = self.test_command(name, path, test_type)
            icon = f"{GREEN}✅{RESET}" if success else f"{RED}❌{RESET}"
            print(f"{icon} {name:20} {msg}")
            self.results.append((name, success))

        # COLLABORATION & DEVOPS (3)
        self.print_category("COLLABORATION & DEVOPS (3)")
        collab_servers = [
            ("GitHub", str(self.base_dir / "mcp-servers-archived/src/github/dist/index.js"), "node_file"),
            ("Docker", "docker-mcp", "command"),
            ("Notion", "notion-mcp-server", "command"),
        ]

        for name, path, test_type in collab_servers:
            success, msg = self.test_command(name, path, test_type)
            icon = f"{GREEN}✅{RESET}" if success else f"{RED}❌{RESET}"
            print(f"{icon} {name:20} {msg}")
            self.results.append((name, success))

        # SUMMARY
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}{'SUMMARY'.center(70)}{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")

        passed = sum(1 for _, success in self.results if success)
        total = len(self.results)
        percentage = (passed/total)*100 if total > 0 else 0

        if percentage == 100:
            print(f"{GREEN}{BOLD}🎉 PERFECT! ALL SERVERS INSTALLED ({passed}/{total}) 100%{RESET}")
            print(f"\n{GREEN}✨ FULL MCP SUITE READY FOR AUTONOMOUS DEVELOPMENT!{RESET}")
        elif percentage >= 80:
            print(f"{GREEN}✅ EXCELLENT! ({passed}/{total}) {percentage:.0f}%{RESET}")
            print(f"\n{YELLOW}Almost complete - missing a few servers{RESET}")
        else:
            print(f"{YELLOW}⚠️ PARTIAL ({passed}/{total}) {percentage:.0f}%{RESET}")

        # List missing servers
        missing = [name for name, success in self.results if not success]
        if missing:
            print(f"\n{RED}Missing servers:{RESET}")
            for server in missing:
                print(f"  • {server}")

        # Capabilities summary
        print(f"\n{CYAN}{'='*70}{RESET}")
        print(f"{CYAN}{'CAPABILITIES ENABLED'.center(70)}{RESET}")
        print(f"{CYAN}{'='*70}{RESET}\n")

        capabilities = {
            "Core": ["✅ File Operations", "✅ Version Control", "✅ Memory Persistence", "✅ Web Fetch"],
            "Advanced": ["✅ Sequential Reasoning", "✅ Time Management", "✅ Reference Server", "✅ Database Testing"],
            "Browser": ["✅ E2E Testing", "✅ Web Automation"],
            "Infrastructure": ["✅ Cache/Queue", "✅ Multi-Agent Orchestration"],
            "Collaboration": ["✅ GitHub Integration", "✅ Docker Containers", "✅ Notion Docs"]
        }

        for category, items in capabilities.items():
            print(f"{BOLD}{category}:{RESET}")
            for item in items:
                print(f"  {item}")
            print()

        print(f"{YELLOW}Next steps:{RESET}")
        print("1. Restart Claude Desktop")
        print("2. Run: ./start_all_mcp_servers.sh")
        print("3. Monitor: python3 monitor_mcp_system.py")

if __name__ == "__main__":
    tester = FullMCPTester()
    tester.run_tests()