#!/usr/bin/env python3
"""
🤖 Task Completion Monitor - Automatic Completion Detection
Monitors Claude agents and automatically detects task completion
"""

import sys
import os
import time
import subprocess
import re
from datetime import datetime, timedelta
import threading
from typing import Dict, List, Optional

# Add shared_state to path
sys.path.append('/Users/erik/Desktop/claude-multiagent-system/langgraph-test')

from shared_state.manager import SharedStateManager

class TaskCompletionMonitor:
    """Monitors agents and automatically detects task completion"""

    def __init__(self):
        self.manager = SharedStateManager(
            persistence_type="json",
            persistence_file="/Users/erik/Desktop/claude-multiagent-system/langgraph-test/shared_state.json"
        )

        self.monitoring = False
        self.monitor_thread = None

        # Completion detection patterns
        self.completion_patterns = [
            r"task[\s\-_]*complete",
            r"completed successfully",
            r"task[\s\-_]*finished",
            r"done with task",
            r"task[\s\-_]*done",
            r"finished.*task",
        ]

        # Error patterns that indicate failure
        self.error_patterns = [
            r"error.*task",
            r"task.*failed",
            r"cannot.*complete",
            r"unable.*to.*complete",
            r"task.*error",
        ]

        # Timeout for stuck tasks (in minutes)
        self.task_timeout_minutes = 30

    def start_monitoring(self):
        """Start the background monitoring thread"""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("🤖 Task Completion Monitor started")

    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("🤖 Task Completion Monitor stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Reload state to get latest data
                self.manager.state = self.manager.persistence_manager.load()

                current_task = self.manager.state.current_task
                if current_task and current_task.status == "in_progress":
                    self._check_task_completion(current_task)
                    self._check_task_timeout(current_task)

                # Check every 10 seconds
                time.sleep(10)

            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                time.sleep(30)  # Wait longer on error

    def _check_task_completion(self, task):
        """Check if any agents have completed their tasks"""
        for agent_id in task.assigned_agents:
            if agent_id not in task.results:  # Agent hasn't completed yet
                # Check agent's terminal output for completion signals
                completion_detected = self._check_agent_output(agent_id)

                if completion_detected['completed']:
                    print(f"✅ Detected completion for agent {agent_id}")

                    # Mark this agent as completed
                    self._complete_agent_task(
                        task.task_id,
                        agent_id,
                        completion_detected['message']
                    )

                elif completion_detected['failed']:
                    print(f"❌ Detected failure for agent {agent_id}")

                    # Mark this agent as failed
                    self._fail_agent_task(
                        task.task_id,
                        agent_id,
                        completion_detected['error_message']
                    )

    def _check_agent_output(self, agent_id: str) -> Dict[str, any]:
        """Check agent's terminal output for completion/failure signals"""
        try:
            # Get session name from agent
            agent = self.manager.state.agents.get(agent_id)
            if not agent:
                return {'completed': False, 'failed': False}

            session_id = agent.session_id

            # Capture recent terminal output
            result = subprocess.run([
                "tmux", "capture-pane", "-t", session_id, "-p"
            ], capture_output=True, text=True, timeout=5)

            if result.returncode != 0:
                return {'completed': False, 'failed': False}

            recent_output = result.stdout.lower()

            # Check for completion patterns
            for pattern in self.completion_patterns:
                if re.search(pattern, recent_output):
                    return {
                        'completed': True,
                        'failed': False,
                        'message': f"Automatic completion detected via pattern: {pattern}"
                    }

            # Check for error patterns
            for pattern in self.error_patterns:
                if re.search(pattern, recent_output):
                    return {
                        'completed': False,
                        'failed': True,
                        'error_message': f"Error detected via pattern: {pattern}"
                    }

            return {'completed': False, 'failed': False}

        except Exception as e:
            print(f"❌ Error checking agent {agent_id} output: {e}")
            return {'completed': False, 'failed': False}

    def _check_task_timeout(self, task):
        """Check if task has timed out"""
        try:
            started_at = datetime.fromisoformat(task.started_at.replace('Z', '+00:00'))
            now = datetime.now()

            elapsed = now - started_at
            if elapsed > timedelta(minutes=self.task_timeout_minutes):
                print(f"⏰ Task {task.task_id} timed out after {elapsed}")

                # Complete task with timeout message
                timeout_results = {}
                for agent_id in task.assigned_agents:
                    if agent_id not in task.results:
                        timeout_results[agent_id] = f"Task timed out after {self.task_timeout_minutes} minutes"

                if timeout_results:
                    self.manager.complete_task(
                        task.task_id,
                        results=timeout_results,
                        error_message=f"Task timed out after {self.task_timeout_minutes} minutes"
                    )

        except Exception as e:
            print(f"❌ Error checking task timeout: {e}")

    def _complete_agent_task(self, task_id: str, agent_id: str, message: str):
        """Mark a specific agent's part of the task as completed"""
        try:
            # Add result for this agent
            task = self.manager.state.current_task
            if task and task.task_id == task_id:
                if not task.results:
                    task.results = {}
                task.results[agent_id] = message

                # Update agent status
                self.manager.update_agent_status(agent_id, "idle")
                agent = self.manager.state.agents[agent_id]
                agent.current_task = None
                agent.last_activity = datetime.now().isoformat()

                # Check if all agents completed
                if len(task.results) >= len(task.assigned_agents):
                    print(f"🎉 All agents completed task {task_id}")
                    self.manager.complete_task(task_id, task.results)
                else:
                    # Save progress
                    self.manager.persistence_manager.save(self.manager.state)
                    print(f"📊 Task {task_id} progress: {len(task.results)}/{len(task.assigned_agents)} agents completed")

        except Exception as e:
            print(f"❌ Error completing agent task: {e}")

    def _fail_agent_task(self, task_id: str, agent_id: str, error_message: str):
        """Mark a specific agent's part of the task as failed"""
        try:
            # Update agent status
            self.manager.update_agent_status(agent_id, "error")
            agent = self.manager.state.agents[agent_id]
            agent.current_task = None
            agent.error_message = error_message
            agent.last_activity = datetime.now().isoformat()

            # Fail the entire task
            self.manager.complete_task(
                task_id,
                error_message=f"Agent {agent_id} failed: {error_message}"
            )

        except Exception as e:
            print(f"❌ Error failing agent task: {e}")

    def get_monitoring_status(self) -> Dict[str, any]:
        """Get current monitoring status"""
        return {
            'monitoring': self.monitoring,
            'current_task': self.manager.state.current_task.task_id if self.manager.state.current_task else None,
            'agents_status': {aid: agent.status for aid, agent in self.manager.state.agents.items()},
            'timeout_minutes': self.task_timeout_minutes
        }

def main():
    """Main function for CLI usage"""
    import argparse

    parser = argparse.ArgumentParser(description="Task Completion Monitor")
    parser.add_argument('--timeout', type=int, default=30,
                       help='Timeout in minutes for stuck tasks (default: 30)')
    parser.add_argument('--daemon', action='store_true',
                       help='Run as daemon (background)')

    args = parser.parse_args()

    monitor = TaskCompletionMonitor()
    monitor.task_timeout_minutes = args.timeout

    print(f"🤖 Starting Task Completion Monitor")
    print(f"   Timeout: {args.timeout} minutes")
    print(f"   Daemon mode: {args.daemon}")

    try:
        monitor.start_monitoring()

        if args.daemon:
            # Run forever
            while monitor.monitoring:
                time.sleep(60)
        else:
            # Run for demonstration
            print("   Running for 2 minutes for demonstration...")
            time.sleep(120)

    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal")
    finally:
        monitor.stop_monitoring()
        print("🤖 Task Completion Monitor stopped")

if __name__ == "__main__":
    main()