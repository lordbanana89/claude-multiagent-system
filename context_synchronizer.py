#!/usr/bin/env python3
"""
Context Synchronizer for Claude Multi-Agent System
Monitors all agents and maintains shared context visibility
"""

import time
import re
import threading
import json
from datetime import datetime
from typing import Dict, List, Set
from dataclasses import dataclass
from core.tmux_client import TMUXClient

@dataclass
class AgentActivity:
    """Represents an agent activity"""
    agent: str
    timestamp: datetime
    activity: str
    category: str  # 'decision', 'action', 'question', 'completion'

class ContextSynchronizer:
    def __init__(self):
        self.tmux = TMUXClient()
        self.shared_context = "claude-shared-context"

        # All possible agent sessions
        self.agents = [
            "claude-backend-api",
            "claude-database",
            "claude-frontend-ui",
            "claude-testing",
            "claude-supervisor",
            "claude-master"
        ]

        # Track last seen content per agent to detect changes
        self.last_content: Dict[str, str] = {}
        self.recent_activities: List[AgentActivity] = []
        self.running = False

    def start(self):
        """Start the synchronizer"""
        print("🚀 Starting Context Synchronizer...")
        self.running = True

        # Ensure shared context exists
        if not self.tmux.session_exists(self.shared_context):
            self.tmux.create_session(self.shared_context)
            print(f"✅ Created shared context session: {self.shared_context}")

        # Start monitoring threads
        threads = []

        # Monitor each agent
        for agent in self.agents:
            if self.tmux.session_exists(agent):
                t = threading.Thread(target=self.monitor_agent, args=(agent,))
                t.daemon = True
                t.start()
                threads.append(t)
                print(f"📡 Monitoring {agent}")

        # Periodic context injection
        t = threading.Thread(target=self.periodic_context_broadcast)
        t.daemon = True
        t.start()
        threads.append(t)

        # Status reporter
        t = threading.Thread(target=self.status_reporter)
        t.daemon = True
        t.start()
        threads.append(t)

        print("✅ Context Synchronizer running!")
        print("Press Ctrl+C to stop...")

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping Context Synchronizer...")
            self.running = False

    def monitor_agent(self, agent: str):
        """Monitor a single agent for significant activities"""
        while self.running:
            try:
                if not self.tmux.session_exists(agent):
                    time.sleep(5)
                    continue

                # Capture recent output
                current_content = self.tmux.capture_pane(agent)

                # Check for new content
                if agent not in self.last_content:
                    self.last_content[agent] = current_content
                    continue

                if current_content != self.last_content[agent]:
                    # Extract new lines
                    new_content = self.extract_new_content(
                        self.last_content[agent],
                        current_content
                    )

                    if new_content:
                        # Analyze and categorize the activity
                        activities = self.analyze_activity(agent, new_content)

                        for activity in activities:
                            # Log to shared context
                            self.log_to_shared_context(activity)

                            # Broadcast to other agents
                            self.broadcast_to_agents(activity, exclude=agent)

                            # Store activity
                            self.recent_activities.append(activity)

                    self.last_content[agent] = current_content

            except Exception as e:
                print(f"❌ Error monitoring {agent}: {e}")

            time.sleep(2)  # Check every 2 seconds

    def extract_new_content(self, old: str, new: str) -> str:
        """Extract only new content from output"""
        if not old:
            return new

        # Find where old content ends in new content
        old_lines = old.split('\n')
        new_lines = new.split('\n')

        # Find the last matching line
        for i in range(len(old_lines)-1, -1, -1):
            if old_lines[i] in new_lines:
                idx = new_lines.index(old_lines[i])
                return '\n'.join(new_lines[idx+1:])

        return '\n'.join(new_lines[-10:])  # Last 10 lines if no match

    def analyze_activity(self, agent: str, content: str) -> List[AgentActivity]:
        """Analyze content and extract significant activities"""
        activities = []

        # Patterns to detect significant activities
        patterns = {
            'decision': [
                r"I(?:'ll| will) (\w+.*)",
                r"Creating (\w+.*)",
                r"Implementing (\w+.*)",
                r"Setting up (\w+.*)",
                r"Configuring (\w+.*)"
            ],
            'action': [
                r"(?:Created|Modified|Deleted|Updated) (\w+.*)",
                r"Successfully (\w+.*)",
                r"Completed (\w+.*)",
                r"File .* (?:created|updated|deleted)"
            ],
            'question': [
                r"(?:Should I|Can I|Do you want) (.*\?)",
                r"(?:What|How|Where|When|Why) (.*\?)"
            ],
            'completion': [
                r"✅ (.*)",
                r"Done(?:\.|:) (.*)",
                r"Finished (.*)",
                r"Task completed"
            ]
        }

        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    activity_text = match if isinstance(match, str) else match[0]
                    activities.append(AgentActivity(
                        agent=agent.replace("claude-", ""),
                        timestamp=datetime.now(),
                        activity=activity_text[:200],  # Limit length
                        category=category
                    ))

        # If no patterns match but content seems significant
        if not activities and len(content.strip()) > 50:
            # Look for any substantive content
            lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#')]
            if lines:
                activities.append(AgentActivity(
                    agent=agent.replace("claude-", ""),
                    timestamp=datetime.now(),
                    activity=lines[0][:200],
                    category='action'
                ))

        return activities

    def log_to_shared_context(self, activity: AgentActivity):
        """Log activity to shared context terminal"""
        # Format based on category
        icons = {
            'decision': '🎯',
            'action': '⚡',
            'question': '❓',
            'completion': '✅'
        }

        icon = icons.get(activity.category, '📝')
        timestamp = activity.timestamp.strftime("%H:%M:%S")

        message = f"[{timestamp}] {icon} {activity.agent}: {activity.activity}"

        # Send to shared context
        self.tmux.send_command(self.shared_context, f"echo '{message}'")

    def broadcast_to_agents(self, activity: AgentActivity, exclude: str = None):
        """Broadcast activity to other agents"""
        # Format context update for agents
        context_update = f"""
# 📢 CONTEXT UPDATE from {activity.agent}
# {activity.activity}
"""

        for agent in self.agents:
            if agent == exclude or not self.tmux.session_exists(agent):
                continue

            # Send as a comment so it doesn't interfere with Claude's work
            self.tmux.send_command(agent, context_update)

    def periodic_context_broadcast(self):
        """Periodically broadcast full context summary"""
        while self.running:
            time.sleep(60)  # Every minute

            if len(self.recent_activities) == 0:
                continue

            # Create summary of recent activities
            summary = self.create_context_summary()

            # Broadcast to all agents
            for agent in self.agents:
                if self.tmux.session_exists(agent):
                    self.tmux.send_command(agent, f"""
# 📊 PERIODIC CONTEXT SUMMARY
# Recent system activities (last minute):
{summary}
# End of context summary
""")

            # Log to shared context
            self.tmux.send_command(self.shared_context, "echo '───────────────────────────'")
            self.tmux.send_command(self.shared_context, "echo '📊 Periodic Context Broadcast Sent'")

    def create_context_summary(self) -> str:
        """Create a summary of recent activities"""
        # Group by agent
        by_agent: Dict[str, List[str]] = {}

        for activity in self.recent_activities[-20:]:  # Last 20 activities
            if activity.agent not in by_agent:
                by_agent[activity.agent] = []
            by_agent[activity.agent].append(f"  - {activity.activity}")

        summary_lines = []
        for agent, activities in by_agent.items():
            summary_lines.append(f"# {agent}:")
            summary_lines.extend(activities[:3])  # Max 3 per agent

        return '\n'.join(summary_lines)

    def status_reporter(self):
        """Report synchronizer status periodically"""
        while self.running:
            time.sleep(30)  # Every 30 seconds

            active_agents = [a for a in self.agents if self.tmux.session_exists(a)]

            status = f"""
[{datetime.now().strftime('%H:%M:%S')}] 📡 Synchronizer Status:
  Active Agents: {len(active_agents)} ({', '.join([a.replace('claude-', '') for a in active_agents])})
  Activities Tracked: {len(self.recent_activities)}
  Last Activity: {self.recent_activities[-1].activity[:50] if self.recent_activities else 'None'}
"""
            print(status)

            # Keep only last 100 activities
            if len(self.recent_activities) > 100:
                self.recent_activities = self.recent_activities[-100:]


def main():
    """Main entry point"""
    synchronizer = ContextSynchronizer()
    synchronizer.start()


if __name__ == "__main__":
    main()