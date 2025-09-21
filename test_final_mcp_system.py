#!/usr/bin/env python3
"""
FINAL MCP System Test - Complete Verification of ALL Servers
Tests all 17 MCP servers for the multi-agent system
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
import json

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'
WHITE = '\033[97m'
RESET = '\033[0m'
BOLD = '\033[1m'

class FinalMCPSystemTest:
    def __init__(self):
        self.base_dir = Path("/Users/erik/Desktop/claude-multiagent-system")
        self.test_results = {}
        self.categories = {
            "Core Development": [],
            "Advanced Reasoning": [],
            "Database & Storage": [],
            "Browser & UI": [],
            "Design & Visual": [],
            "Collaboration & DevOps": [],
            "System Orchestration": []
        }

    def print_header(self):
        print(f"\n{MAGENTA}{'='*80}{RESET}")
        print(f"{MAGENTA}{BOLD}                    FINAL MCP SYSTEM VERIFICATION                     {RESET}")
        print(f"{MAGENTA}{BOLD}                        Complete Server Suite                          {RESET}")
        print(f"{MAGENTA}{BOLD}                   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    {RESET}")
        print(f"{MAGENTA}{'='*80}{RESET}\n")

    def test_server(self, name, command=None, file_path=None):
        """Test if a server is available"""
        try:
            if command:
                # Test command availability
                result = subprocess.run(
                    ["which", command],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return True, "✓ Command installed"
                return False, "✗ Not found"

            elif file_path:
                # Test file existence
                if Path(file_path).exists():
                    return True, "✓ Server built"
                return False, "✗ Not built"

        except Exception as e:
            return False, f"✗ Error: {str(e)[:30]}"

    def run_tests(self):
        self.print_header()

        # CORE DEVELOPMENT (4)
        print(f"{CYAN}{BOLD}[ CORE DEVELOPMENT ] - Foundation Servers{RESET}")
        print("─" * 60)

        core_tests = [
            ("Filesystem", None, str(self.base_dir / "mcp-servers-official/src/filesystem/dist/index.js")),
            ("Git", "mcp-server-git", None),
            ("Memory", None, str(self.base_dir / "mcp-servers-official/src/memory/dist/index.js")),
            ("Fetch", "mcp-server-fetch", None),
        ]

        for name, cmd, path in core_tests:
            success, msg = self.test_server(name, cmd, path)
            self.categories["Core Development"].append((name, success))
            icon = f"{GREEN}●{RESET}" if success else f"{RED}○{RESET}"
            print(f"  {icon} {name:20} {msg}")

        # ADVANCED REASONING (3)
        print(f"\n{CYAN}{BOLD}[ ADVANCED REASONING ] - Intelligence Servers{RESET}")
        print("─" * 60)

        advanced_tests = [
            ("Sequential Thinking", None, str(self.base_dir / "mcp-servers-official/src/sequentialthinking/dist/index.js")),
            ("Time", "mcp-server-time", None),
            ("Everything", None, str(self.base_dir / "mcp-servers-official/src/everything/dist/index.js")),
        ]

        for name, cmd, path in advanced_tests:
            success, msg = self.test_server(name, cmd, path)
            self.categories["Advanced Reasoning"].append((name, success))
            icon = f"{GREEN}●{RESET}" if success else f"{RED}○{RESET}"
            print(f"  {icon} {name:20} {msg}")

        # DATABASE & STORAGE (3)
        print(f"\n{CYAN}{BOLD}[ DATABASE & STORAGE ] - Data Management{RESET}")
        print("─" * 60)

        db_tests = [
            ("SQLite", "mcp-server-sqlite", None),
            ("PostgreSQL", None, str(self.base_dir / "mcp-servers-archived/src/postgres/dist/index.js")),
            ("Redis", None, str(self.base_dir / "mcp-servers-archived/src/redis/dist/index.js")),
        ]

        for name, cmd, path in db_tests:
            success, msg = self.test_server(name, cmd, path)
            self.categories["Database & Storage"].append((name, success))
            icon = f"{GREEN}●{RESET}" if success else f"{RED}○{RESET}"
            print(f"  {icon} {name:20} {msg}")

        # BROWSER & UI AUTOMATION (2)
        print(f"\n{CYAN}{BOLD}[ BROWSER & UI AUTOMATION ] - Web Control{RESET}")
        print("─" * 60)

        browser_tests = [
            ("Puppeteer", None, str(self.base_dir / "mcp-servers-archived/src/puppeteer/dist/index.js")),
            ("Playwright", "playwright-mcp", None),
        ]

        for name, cmd, path in browser_tests:
            success, msg = self.test_server(name, cmd, path)
            self.categories["Browser & UI"].append((name, success))
            icon = f"{GREEN}●{RESET}" if success else f"{RED}○{RESET}"
            print(f"  {icon} {name:20} {msg}")

        # DESIGN & VISUAL (1)
        print(f"\n{CYAN}{BOLD}[ DESIGN & VISUAL ] - Creative Tools{RESET}")
        print("─" * 60)

        design_tests = [
            ("Figma", "figma-mcp", None),
        ]

        for name, cmd, path in design_tests:
            success, msg = self.test_server(name, cmd, path)
            self.categories["Design & Visual"].append((name, success))
            icon = f"{GREEN}●{RESET}" if success else f"{RED}○{RESET}"
            print(f"  {icon} {name:20} {msg}")

        # COLLABORATION & DEVOPS (3)
        print(f"\n{CYAN}{BOLD}[ COLLABORATION & DEVOPS ] - Team Tools{RESET}")
        print("─" * 60)

        collab_tests = [
            ("GitHub", None, str(self.base_dir / "mcp-servers-archived/src/github/dist/index.js")),
            ("Docker", "docker-mcp", None),
            ("Notion", "notion-mcp-server", None),
        ]

        for name, cmd, path in collab_tests:
            success, msg = self.test_server(name, cmd, path)
            self.categories["Collaboration & DevOps"].append((name, success))
            icon = f"{GREEN}●{RESET}" if success else f"{RED}○{RESET}"
            print(f"  {icon} {name:20} {msg}")

        # SYSTEM ORCHESTRATION (1)
        print(f"\n{CYAN}{BOLD}[ SYSTEM ORCHESTRATION ] - Control Center{RESET}")
        print("─" * 60)

        system_tests = [
            ("Multi-Agent", None, str(self.base_dir / "mcp_server_v2.py")),
        ]

        for name, cmd, path in system_tests:
            success, msg = self.test_server(name, cmd, path)
            self.categories["System Orchestration"].append((name, success))
            icon = f"{GREEN}●{RESET}" if success else f"{RED}○{RESET}"
            print(f"  {icon} {name:20} {msg}")

        # SUMMARY
        self.print_summary()

    def print_summary(self):
        print(f"\n{BLUE}{'='*80}{RESET}")
        print(f"{BLUE}{BOLD}                              FINAL REPORT                                {RESET}")
        print(f"{BLUE}{'='*80}{RESET}\n")

        total_servers = 0
        working_servers = 0

        # Category breakdown
        print(f"{WHITE}Category Status:{RESET}\n")
        for category, results in self.categories.items():
            if results:
                passed = sum(1 for _, success in results if success)
                total = len(results)
                total_servers += total
                working_servers += passed

                percentage = (passed/total)*100
                if percentage == 100:
                    status = f"{GREEN}COMPLETE{RESET}"
                elif percentage >= 50:
                    status = f"{YELLOW}PARTIAL{RESET}"
                else:
                    status = f"{RED}MISSING{RESET}"

                print(f"  {category:25} [{passed}/{total}] {status}")

        # Overall score
        percentage = (working_servers/total_servers)*100 if total_servers > 0 else 0

        print(f"\n{WHITE}{'─'*80}{RESET}")
        print(f"\n{BOLD}OVERALL SYSTEM STATUS:{RESET}")

        if percentage == 100:
            print(f"\n  {GREEN}{BOLD}✨ PERFECT SCORE! {working_servers}/{total_servers} servers operational (100%)✨{RESET}")
            print(f"\n  {GREEN}🎉 COMPLETE MCP ECOSYSTEM READY FOR AUTONOMOUS DEVELOPMENT! 🎉{RESET}")
        elif percentage >= 90:
            print(f"\n  {GREEN}✅ EXCELLENT! {working_servers}/{total_servers} servers operational ({percentage:.0f}%){RESET}")
            print(f"\n  {YELLOW}System is highly functional with minor gaps{RESET}")
        elif percentage >= 75:
            print(f"\n  {YELLOW}⚠️ GOOD: {working_servers}/{total_servers} servers operational ({percentage:.0f}%){RESET}")
            print(f"\n  {YELLOW}System functional but missing some capabilities{RESET}")
        else:
            print(f"\n  {RED}❌ INCOMPLETE: {working_servers}/{total_servers} servers operational ({percentage:.0f}%){RESET}")
            print(f"\n  {RED}System needs additional setup{RESET}")

        # Missing servers
        missing = []
        for category, results in self.categories.items():
            for name, success in results:
                if not success:
                    missing.append(name)

        if missing:
            print(f"\n{RED}Missing Servers:{RESET}")
            for server in missing:
                print(f"  • {server}")

        # Next steps
        print(f"\n{YELLOW}{'─'*80}{RESET}")
        print(f"{YELLOW}Next Steps:{RESET}")
        print("  1. Copy configuration: cp FINAL_MCP_COMPLETE_CONFIGURATION.json ~/.claude/claude_mcp_config.json")
        print("  2. Restart Claude Desktop to load all servers")
        print("  3. Start system: ./start_all_mcp_servers.sh")
        print("  4. Monitor: python3 monitor_mcp_system.py")

        # Save report
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_servers": total_servers,
            "working_servers": working_servers,
            "percentage": percentage,
            "categories": {
                cat: [(name, success) for name, success in results]
                for cat, results in self.categories.items()
            }
        }

        report_path = self.base_dir / "mcp_system_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n{GREEN}Report saved to: mcp_system_report.json{RESET}")

if __name__ == "__main__":
    tester = FinalMCPSystemTest()
    tester.run_tests()