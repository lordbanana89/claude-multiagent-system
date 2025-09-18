#!/usr/bin/env python3
"""
Real-time Monitor for Claude CLI Agents
Captures actual Claude output and logs to shared context
"""

import time
import re
import threading
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import os
import signal
import sys

class ClaudeAgentMonitor:
    """Monitors real Claude CLI sessions and extracts activities"""

    def __init__(self, agent_name: str, session_name: str):
        self.agent_name = agent_name
        self.session_name = session_name
        self.log_file = "/tmp/claude_shared_context.log"
        self.last_content = ""
        self.last_line_count = 0
        self.running = True

        # Patterns that indicate Claude is doing something important
        self.action_patterns = [
            # File operations
            (r"(?:Creating|Writing|Editing|Reading) .*\.(py|js|ts|html|css|json|md)", "file_op"),
            (r"File .* (?:created|updated|deleted) successfully", "file_complete"),

            # Code generation
            (r"(?:Here's|I'll create|Let me write) .*(?:code|function|class|component)", "code_gen"),
            (r"```[\w]*\n", "code_block"),

            # API/Database operations
            (r"(?:Creating|Implementing) .*/api/.*", "api"),
            (r"(?:CREATE TABLE|ALTER TABLE|INSERT INTO|UPDATE|DELETE FROM)", "sql"),

            # Decisions and planning
            (r"I(?:'ll| will) (?:now |next )?(\w+.*)", "decision"),
            (r"(?:First|Next|Then|Finally), .*", "step"),
            (r"(?:Setting up|Configuring|Initializing) .*", "setup"),

            # Questions and clarifications
            (r"\?$", "question"),
            (r"(?:Should I|Would you like|Do you want) .*\?", "confirm"),

            # Completions
            (r"(?:✓|✅|Done|Completed|Finished|Successfully) .*", "complete"),

            # Errors and issues
            (r"(?:Error|Warning|Failed|Cannot|Unable) .*", "error"),
        ]

    def capture_tmux_pane(self) -> str:
        """Capture current content from TMUX pane"""
        try:
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", self.session_name, "-p"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return ""

    def extract_claude_activity(self, content: str) -> List[Tuple[str, str, str]]:
        """Extract meaningful activities from Claude's output"""
        activities = []

        # Get only new content since last check
        lines = content.split('\n')

        # Find where we left off
        if self.last_content:
            old_lines = self.last_content.split('\n')
            # Find the last matching line
            new_start = 0
            for i in range(len(old_lines) - 1, max(0, len(old_lines) - 10), -1):
                if old_lines[i] in lines:
                    idx = lines.index(old_lines[i])
                    new_start = idx + 1
                    break

            new_lines = lines[new_start:]
        else:
            # First run, take last 10 lines
            new_lines = lines[-10:] if len(lines) > 10 else lines

        # Analyze new lines
        for line in new_lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('$'):
                continue

            # Check against patterns
            for pattern, category in self.action_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    activities.append((line, category, datetime.now().strftime("%H:%M:%S")))
                    break
            else:
                # If no pattern matches but line seems significant
                if len(line) > 30 and not line.startswith('>'):
                    # Check if it's Claude talking (not command output)
                    if any(word in line.lower() for word in ['i', "i'll", "i'm", 'let', 'here', 'this', 'that']):
                        activities.append((line[:200], "response", datetime.now().strftime("%H:%M:%S")))

        return activities

    def log_activity(self, message: str, category: str = "info"):
        """Log activity to shared context"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Choose icon based on category
        icons = {
            "file_op": "📁",
            "file_complete": "✅",
            "code_gen": "💻",
            "code_block": "📝",
            "api": "🌐",
            "sql": "🗄️",
            "decision": "🎯",
            "step": "👉",
            "setup": "⚙️",
            "question": "❓",
            "confirm": "🤔",
            "complete": "✅",
            "error": "❌",
            "response": "💬",
            "info": "ℹ️"
        }

        icon = icons.get(category, "📌")

        # Format and write to log
        log_entry = f"[{timestamp}] {icon} {self.agent_name}: {message}\n"

        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error logging: {e}")

    def monitor_loop(self):
        """Main monitoring loop"""
        print(f"📡 Monitoring {self.session_name} as {self.agent_name}")

        while self.running:
            try:
                # Capture current pane content
                current_content = self.capture_tmux_pane()

                if current_content and current_content != self.last_content:
                    # Extract activities
                    activities = self.extract_claude_activity(current_content)

                    # Log each activity
                    for activity, category, _ in activities:
                        self.log_activity(activity, category)
                        print(f"  → Logged: [{category}] {activity[:80]}...")

                    # Update last content
                    self.last_content = current_content

                # Sleep before next check
                time.sleep(2)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(5)

    def start(self):
        """Start monitoring"""
        self.monitor_loop()

    def stop(self):
        """Stop monitoring"""
        self.running = False


class MultiAgentMonitor:
    """Monitors multiple Claude agents simultaneously"""

    def __init__(self):
        self.monitors = {}
        self.threads = {}
        self.log_file = "/tmp/claude_shared_context.log"

        # Agent configurations
        self.agent_configs = [
            ("backend-api", "claude-backend-api"),
            ("database", "claude-database"),
            ("frontend-ui", "claude-frontend-ui"),
            ("testing", "claude-testing"),
            ("supervisor", "claude-supervisor"),
        ]

    def check_session_exists(self, session_name: str) -> bool:
        """Check if TMUX session exists"""
        try:
            result = subprocess.run(
                ["tmux", "has-session", "-t", session_name],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def check_session_has_claude(self, session_name: str) -> bool:
        """Check if session actually has Claude running"""
        try:
            content = subprocess.run(
                ["tmux", "capture-pane", "-t", session_name, "-p"],
                capture_output=True,
                text=True,
                check=True
            ).stdout

            # Look for signs of Claude CLI
            claude_indicators = [
                "Claude",
                "claude>",
                "I'll help",
                "I can help",
                "Let me",
                "Human:",
                "Assistant:"
            ]

            return any(indicator in content for indicator in claude_indicators)
        except:
            return False

    def initialize_log(self):
        """Initialize or append to shared log"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                f.write("═" * 64 + "\n")
                f.write("           🧠 CLAUDE MULTI-AGENT SHARED CONTEXT\n")
                f.write("═" * 64 + "\n")
                f.write("\nReal-time activity log from Claude CLI agents\n")
                f.write("─" * 64 + "\n")

        # Log monitor start
        with open(self.log_file, 'a') as f:
            f.write(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🚀 Monitor started\n")

    def start_monitoring(self):
        """Start monitoring all available Claude agents"""
        print("🧠 Claude Multi-Agent Monitor Starting...")
        print("=" * 60)

        self.initialize_log()

        # Check for active Claude sessions
        active_agents = []
        for agent_name, session_name in self.agent_configs:
            if self.check_session_exists(session_name):
                if self.check_session_has_claude(session_name):
                    active_agents.append((agent_name, session_name))
                    print(f"✅ Found Claude in {session_name}")
                else:
                    print(f"⚠️  Session {session_name} exists but Claude not detected")
            else:
                print(f"❌ Session {session_name} not found")

        if not active_agents:
            print("\n❌ No active Claude agents found!")
            print("Start Claude agents first with:")
            print("  tmux new-session -d -s claude-backend-api")
            print("  tmux send-keys -t claude-backend-api 'claude' Enter")
            return False

        print(f"\n📡 Monitoring {len(active_agents)} agents:")

        # Start monitor thread for each agent
        for agent_name, session_name in active_agents:
            monitor = ClaudeAgentMonitor(agent_name, session_name)
            self.monitors[agent_name] = monitor

            thread = threading.Thread(target=monitor.start, name=f"monitor-{agent_name}")
            thread.daemon = True
            thread.start()
            self.threads[agent_name] = thread

            print(f"  → Started monitor for {agent_name}")

        # Create or attach to shared context terminal
        self.setup_shared_terminal()

        print("\n✨ Monitoring active! Press Ctrl+C to stop")
        print(f"📊 View shared context: tail -f {self.log_file}")
        print("🖥️  Or in TMUX: tmux attach -t claude-shared-context")

        return True

    def setup_shared_terminal(self):
        """Setup shared context terminal with tail -f"""
        session_name = "claude-shared-context"

        # Kill existing if any
        subprocess.run(["tmux", "kill-session", "-t", session_name],
                      capture_output=True, stderr=subprocess.DEVNULL)

        # Create new session with tail
        subprocess.run(["tmux", "new-session", "-d", "-s", session_name])
        subprocess.run(["tmux", "send-keys", "-t", session_name,
                       f"tail -f {self.log_file}", "Enter"])

    def run(self):
        """Run the monitor until interrupted"""
        if not self.start_monitoring():
            return

        try:
            # Keep running until interrupted
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping monitors...")

            # Stop all monitors
            for monitor in self.monitors.values():
                monitor.stop()

            # Log shutdown
            with open(self.log_file, 'a') as f:
                f.write(f"[{datetime.now().strftime('%H:%M:%S')}] 🛑 Monitor stopped\n")

            print("✅ All monitors stopped")


def main():
    """Main entry point"""
    monitor = MultiAgentMonitor()

    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print("\nShutting down...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Run the monitor
    monitor.run()


if __name__ == "__main__":
    main()