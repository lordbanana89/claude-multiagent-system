#!/usr/bin/env python3
"""
👨‍💼 Supervisor Agent - Coordinatore Centrale di tutti gli agenti
Gestisce task delegation, monitoring e logging completo
"""

import sys
import time
import subprocess
import json
import threading
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))  # Also add langgraph-test dir
from shared_state.manager import SharedStateManager
from shared_state.models import TaskPriority
from config.settings import PROJECT_ROOT, AGENT_SESSIONS

class SupervisorAgent:
    """Agent Supervisor - coordina tutti gli altri agenti"""

    def __init__(self):
        self.manager = SharedStateManager()
        self.log_file = PROJECT_ROOT / "langgraph-test" / "supervisor.log"

        # Use centralized agent sessions mapping
        self.agents = AGENT_SESSIONS

        self.active_tasks: Dict[str, str] = {}  # agent_id -> task_id
        self.agent_logs: Dict[str, List[str]] = {agent: [] for agent in self.agents}

        # Initialize logging
        self._log("🚀 Supervisor Agent initialized")
        self._log(f"📋 Managing {len(self.agents)} agents: {list(self.agents.keys())}")

    def _log(self, message: str, agent_id: str = "SUPERVISOR"):
        """Centralized logging system"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{agent_id}] {message}"

        # Console output
        print(log_entry)

        # File logging
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry + "\n")
        except:
            pass

        # Agent-specific logs
        if agent_id != "SUPERVISOR":
            if agent_id not in self.agent_logs:
                self.agent_logs[agent_id] = []
            self.agent_logs[agent_id].append(log_entry)

    def send_command_properly(self, agent_id: str, command: str, wait_time: float = 2.0) -> bool:
        """
        Invia comando all'agente CORRETTAMENTE:
        1. Invia comando
        2. Premi Enter
        3. Aspetta risposta
        4. Log tutto
        """
        if agent_id not in self.agents:
            self._log(f"❌ Agent {agent_id} not found", agent_id)
            return False

        session = self.agents[agent_id]
        self._log(f"📤 Sending command: {command}", agent_id)

        try:
            # Step 1: Send command
            subprocess.run([
                "tmux", "send-keys", "-t", session, command
            ], check=True, timeout=5)

            self._log(f"✅ Command sent to {session}", agent_id)

            # Step 2: Press Enter
            time.sleep(0.2)  # Small delay
            subprocess.run([
                "tmux", "send-keys", "-t", session, "Enter"
            ], check=True, timeout=5)

            self._log(f"⏎ Enter pressed", agent_id)

            # Step 3: Wait for response
            time.sleep(wait_time)

            # Step 4: Capture output
            result = subprocess.run([
                "tmux", "capture-pane", "-t", session, "-p"
            ], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                output_lines = result.stdout.split('\n')[-10:]  # Last 10 lines
                for line in output_lines:
                    if line.strip():
                        self._log(f"📥 OUTPUT: {line.strip()}", agent_id)
                return True
            else:
                self._log(f"❌ Failed to capture output", agent_id)
                return False

        except subprocess.TimeoutExpired:
            self._log(f"⏰ Command timed out", agent_id)
            return False
        except Exception as e:
            self._log(f"❌ Error: {e}", agent_id)
            return False

    def delegate_task(self, task_description: str, agent_id: str = "backend-api") -> str:
        """
        Delega task a un agente specifico con processo completo:
        1. Crea task in SharedState
        2. Assegna ad agente
        3. Invia comando all'agente
        4. Monitora esecuzione
        """
        self._log(f"🎯 Delegating task: '{task_description}' to {agent_id}")

        try:
            # Step 1: Create task
            task = self.manager.create_task(task_description, TaskPriority.MEDIUM)
            self.manager.add_task(task)

            # Step 2: Assign to agent
            success = self.manager.assign_task(task.task_id, [agent_id])
            if not success:
                self._log(f"❌ Failed to assign task to {agent_id}")
                return None

            self._log(f"✅ Task {task.task_id} assigned to {agent_id}")
            self.active_tasks[agent_id] = task.task_id

            # Step 3: Send to agent terminal
            command = f"🎯 NEW TASK: {task_description}"
            success = self.send_command_properly(agent_id, command)

            if success:
                self._log(f"✅ Task successfully delegated to {agent_id}")
                return task.task_id
            else:
                self._log(f"❌ Failed to send task to {agent_id}")
                return None

        except Exception as e:
            self._log(f"❌ Error delegating task: {e}")
            return None

    def check_agent_status(self, agent_id: str) -> Dict:
        """Controlla status dettagliato di un agente"""
        self._log(f"🔍 Checking status of {agent_id}")

        try:
            # Get agent state from SharedState
            agent_state = self.manager.state.agents.get(agent_id)
            if not agent_state:
                return {"error": f"Agent {agent_id} not found in SharedState"}

            # Capture terminal output
            session = self.agents[agent_id]
            result = subprocess.run([
                "tmux", "capture-pane", "-t", session, "-p"
            ], capture_output=True, text=True, timeout=5)

            terminal_output = result.stdout if result.returncode == 0 else "Error capturing output"

            status = {
                "agent_id": agent_id,
                "status": agent_state.status.value,
                "current_task": agent_state.current_task,
                "last_activity": agent_state.last_activity,
                "session": session,
                "terminal_active": result.returncode == 0,
                "recent_output": terminal_output.split('\n')[-5:],  # Last 5 lines
                "logs_count": len(self.agent_logs.get(agent_id, []))
            }

            self._log(f"📊 Agent {agent_id} status: {agent_state.status.value}", agent_id)
            return status

        except Exception as e:
            self._log(f"❌ Error checking {agent_id}: {e}")
            return {"error": str(e)}

    def complete_task(self, agent_id: str, message: str = "Task completed by supervisor") -> bool:
        """Completa task di un agente"""
        if agent_id not in self.active_tasks:
            self._log(f"❌ No active task for {agent_id}")
            return False

        task_id = self.active_tasks[agent_id]
        self._log(f"✅ Completing task {task_id} for {agent_id}")

        try:
            results = {agent_id: message}
            success = self.manager.complete_task(task_id, results)

            if success:
                del self.active_tasks[agent_id]
                self._log(f"🎉 Task {task_id} completed successfully")
                return True
            else:
                self._log(f"❌ Failed to complete task {task_id}")
                return False

        except Exception as e:
            self._log(f"❌ Error completing task: {e}")
            return False

    def monitor_all_agents(self) -> Dict:
        """Monitora tutti gli agenti e ritorna report completo"""
        self._log("🔍 Monitoring all agents")

        report = {
            "timestamp": datetime.now().isoformat(),
            "system_status": self.manager.state.system_status,
            "current_task": self.manager.state.current_task.task_id if self.manager.state.current_task else None,
            "agents": {}
        }

        for agent_id in self.agents:
            report["agents"][agent_id] = self.check_agent_status(agent_id)

        self._log(f"📊 System status: {report['system_status']}")
        return report

    def emergency_reset_all(self) -> bool:
        """Reset di emergenza di tutti gli agenti"""
        self._log("🚨 EMERGENCY RESET - Resetting all agents")

        try:
            # Run emergency reset script
            result = subprocess.run([
                "python3",
                "/Users/erik/Desktop/claude-multiagent-system/langgraph-test/reset_stuck_agents.py"
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                self._log("✅ Emergency reset completed successfully")
                self.active_tasks.clear()  # Clear all active tasks
                return True
            else:
                self._log(f"❌ Emergency reset failed: {result.stderr}")
                return False

        except Exception as e:
            self._log(f"❌ Emergency reset error: {e}")
            return False

    def get_logs(self, agent_id: str = None, last_n: int = 20) -> List[str]:
        """Ottieni log di un agente specifico o del supervisor"""
        if agent_id and agent_id in self.agent_logs:
            return self.agent_logs[agent_id][-last_n:]

        # Return supervisor logs from file
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
                return [line.strip() for line in lines[-last_n:]]
        except:
            return ["No logs available"]

def main():
    """Test del Supervisor Agent"""
    print("👨‍💼 Starting Supervisor Agent Test")

    supervisor = SupervisorAgent()

    # Test delegation
    task_id = supervisor.delegate_task("Write 'Hello from Supervisor!' to the terminal", "backend-api")

    if task_id:
        print(f"✅ Task delegated: {task_id}")

        # Wait and monitor
        time.sleep(10)

        # Check status
        status = supervisor.check_agent_status("backend-api")
        print(f"📊 Agent status: {status}")

        # Complete task
        success = supervisor.complete_task("backend-api", "Task completed via supervisor")
        print(f"✅ Task completed: {success}")

    # Full report
    report = supervisor.monitor_all_agents()
    print(f"📊 Full system report: {json.dumps(report, indent=2, default=str)}")

if __name__ == "__main__":
    main()