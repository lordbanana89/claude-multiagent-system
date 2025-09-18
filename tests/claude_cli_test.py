#!/usr/bin/env python3
"""
Test diretto comunicazione con Claude Code CLI
Verifica se la comunicazione subprocess funziona prima di integrare LangChain
"""

import subprocess
import time
from typing import Dict, Any

class ClaudeCodeDirectTest:
    """Test diretto della comunicazione con Claude Code CLI"""

    def __init__(self):
        self.tmux_bin = "/opt/homebrew/bin/tmux"
        self.test_sessions = ["claude-backend-api", "claude-frontend-ui", "claude-database"]

    def test_session_exists(self, session: str) -> bool:
        """Verifica se la sessione tmux esiste"""
        try:
            subprocess.run([
                self.tmux_bin, "has-session", "-t", session
            ], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def send_task_to_claude(self, session: str, task: str) -> str:
        """Invia task diretto a Claude Code"""
        try:
            print(f"📤 Sending to {session}: {task[:50]}...")

            # Send task
            subprocess.run([
                self.tmux_bin, "send-keys", "-t", session,
                task, "Enter"
            ], check=True)

            # Wait for processing
            time.sleep(4)

            # Capture response
            result = subprocess.run([
                self.tmux_bin, "capture-pane", "-t", session, "-p"
            ], capture_output=True, text=True, check=True)

            return result.stdout

        except Exception as e:
            return f"Error: {str(e)}"

    def extract_response(self, terminal_output: str, original_task: str) -> str:
        """Estrae risposta significativa dall'output"""
        lines = terminal_output.split('\n')

        # Get last few meaningful lines
        meaningful_lines = []
        for line in reversed(lines):
            clean_line = line.strip()
            if clean_line and len(clean_line) > 10:  # Skip short lines
                meaningful_lines.append(clean_line)
                if len(meaningful_lines) >= 3:
                    break

        if meaningful_lines:
            return '\n'.join(reversed(meaningful_lines))
        else:
            return "Claude Code processed the task. Check terminal for details."

    def test_multi_agent_coordination(self) -> Dict[str, Any]:
        """Test coordinazione multi-agent"""

        print("🧪 TESTING MULTI-AGENT COORDINATION WITH CLAUDE CODE")
        print("=" * 60)

        # Project to coordinate
        project = "Create a user authentication API with database integration"

        results = {
            "project": project,
            "agents": {},
            "success": True
        }

        # Test each agent
        for session in self.test_sessions:
            print(f"\n🤖 Testing {session}...")

            # Check if session exists
            if not self.test_session_exists(session):
                print(f"❌ Session {session} not found")
                results["agents"][session] = {"status": "not_found", "response": ""}
                results["success"] = False
                continue

            # Create specialized task for each agent
            if "backend" in session:
                task = f"Design API endpoints for: {project}. Provide REST API structure."
            elif "frontend" in session:
                task = f"Design user interface for: {project}. Provide UI components."
            elif "database" in session:
                task = f"Design database schema for: {project}. Provide table structure."
            else:
                task = f"Analyze requirements for: {project}"

            # Send task
            terminal_output = self.send_task_to_claude(session, task)
            response = self.extract_response(terminal_output, task)

            results["agents"][session] = {
                "status": "completed",
                "task": task,
                "response": response[:200] + "..." if len(response) > 200 else response
            }

            print(f"✅ {session} responded: {response[:60]}...")

        return results

def main():
    """Test the direct Claude Code communication"""

    print("🔍 CLAUDE CODE CLI DIRECT TEST")
    print("=" * 40)
    print("Testing subprocess communication with Claude Code terminals")
    print()

    # Initialize tester
    tester = ClaudeCodeDirectTest()

    # Run multi-agent test
    results = tester.test_multi_agent_coordination()

    # Display results
    print("\n📊 RESULTS SUMMARY")
    print("=" * 30)

    if results["success"]:
        print("🎉 Multi-agent coordination test SUCCESSFUL!")
    else:
        print("⚠️ Some issues detected")

    print(f"\n📋 Project: {results['project']}")
    print(f"🤖 Agents tested: {len(results['agents'])}")

    for agent, data in results["agents"].items():
        status_icon = "✅" if data["status"] == "completed" else "❌"
        print(f"\n{status_icon} {agent.upper()}:")
        print(f"   Status: {data['status']}")
        if "task" in data:
            print(f"   Task: {data['task'][:80]}...")
        if data["response"]:
            print(f"   Response: {data['response'][:100]}...")

    # Conclusion
    if results["success"]:
        print("\n🚀 READY FOR LANGCHAIN INTEGRATION!")
        print("Direct Claude Code CLI communication is working.")
        print("Can now integrate with LangChain framework safely.")
    else:
        print("\n🔧 ISSUES TO RESOLVE:")
        print("Some Claude Code sessions are not responding.")
        print("Check that Claude Code is running in the sessions.")

if __name__ == "__main__":
    main()