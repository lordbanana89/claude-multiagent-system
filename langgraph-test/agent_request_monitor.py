#!/usr/bin/env python3
"""
🔍 Agent Request Monitor - Monitora e gestisce richieste agenti in tempo reale
"""

import sys
import time
import subprocess
import threading
from datetime import datetime

sys.path.append('/Users/erik/Desktop/claude-multiagent-system/langgraph-test')
from agent_request_manager import AgentRequestManager, RequestType
from shared_state.manager import SharedStateManager

class AgentRequestMonitor:
    """Monitora richieste agenti dai terminali tmux"""

    def __init__(self):
        self.request_manager = AgentRequestManager()
        self.monitoring = False
        self.monitor_thread = None

        # Inizializza sistema messaging per notifiche supervisor
        self.state_manager = SharedStateManager()
        self.notified_requests = set()  # Track requests già notificate

        # Sessioni da monitorare
        self.agent_sessions = {
            "backend-api": "claude-backend-api",
            "database": "claude-database",
            "frontend-ui": "claude-frontend-ui",
            "instagram": "claude-instagram",
            "testing": "claude-testing"
        }

    def start_monitoring(self):
        """Avvia monitoraggio richieste"""

        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("🔍 Agent Request Monitor started")

    def stop_monitoring(self):
        """Ferma monitoraggio"""

        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("🔍 Agent Request Monitor stopped")

    def _monitor_loop(self):
        """Loop principale di monitoraggio"""

        while self.monitoring:
            try:
                # Controlla ogni sessione agente
                for agent_id, session_id in self.agent_sessions.items():
                    self._check_agent_requests(agent_id, session_id)

                # Processa richieste auto-approvate
                self._process_auto_approved_requests()

                # Cleanup richieste vecchie
                if datetime.now().minute % 10 == 0:  # Ogni 10 minuti
                    self.request_manager.cleanup_old_requests()

                time.sleep(5)  # Controlla ogni 5 secondi

            except Exception as e:
                print(f"❌ Error in monitor loop: {e}")
                time.sleep(10)

    def _check_agent_requests(self, agent_id: str, session_id: str):
        """Controlla richieste di un agente specifico"""

        try:
            # Cattura output terminale
            result = subprocess.run([
                "tmux", "capture-pane", "-t", session_id, "-p"
            ], capture_output=True, text=True, timeout=5)

            if result.returncode != 0:
                return

            terminal_output = result.stdout

            # Cerca pattern di richieste
            self._detect_bash_requests(agent_id, terminal_output)
            self._detect_task_requests(agent_id, terminal_output)
            self._detect_file_creation_requests(agent_id, terminal_output)

        except Exception as e:
            pass  # Ignora errori di monitoraggio

    def _detect_bash_requests(self, agent_id: str, output: str):
        """Rileva richieste di comandi bash"""

        # Pattern per richieste di conferma bash
        if "Do you want to proceed?" in output and "Bash command" in output:
            # Estrai comando dalla richiesta
            lines = output.split('\n')
            command = None

            for i, line in enumerate(lines):
                if "Bash command" in line and i + 2 < len(lines):
                    # Il comando dovrebbe essere 2 righe sotto
                    potential_command = lines[i + 2].strip()
                    if potential_command and not potential_command.startswith('│'):
                        command = potential_command
                        break

            if command:
                # Crea richiesta per comando bash
                req_id = self.request_manager.create_request(
                    agent_id=agent_id,
                    request_type=RequestType.BASH_COMMAND,
                    command=command,
                    description=f"Agent {agent_id} requesting bash command"
                )

                print(f"🔍 Detected bash request from {agent_id}: {command}")

                # Notifica supervisor di nuova richiesta
                if req_id and req_id not in self.notified_requests:
                    self._notify_supervisor_new_request(req_id, agent_id, "BASH_COMMAND", command)
                    self.notified_requests.add(req_id)

    def _detect_task_requests(self, agent_id: str, output: str):
        """Rileva richieste di comandi task"""

        # Pattern per task-complete
        if "task-complete" in output.lower():
            req_id = self.request_manager.create_request(
                agent_id=agent_id,
                request_type=RequestType.TASK_COMPLETE,
                command="task-complete",
                description=f"Agent {agent_id} requesting task completion"
            )

            # Notifica supervisor
            if req_id and req_id not in self.notified_requests:
                self._notify_supervisor_new_request(req_id, agent_id, "TASK_COMPLETE", "task-complete")
                self.notified_requests.add(req_id)

        # Pattern per task-progress
        if "task-progress" in output.lower():
            req_id = self.request_manager.create_request(
                agent_id=agent_id,
                request_type=RequestType.TASK_PROGRESS,
                command="task-progress",
                description=f"Agent {agent_id} requesting progress update"
            )

            # Notifica supervisor
            if req_id and req_id not in self.notified_requests:
                self._notify_supervisor_new_request(req_id, agent_id, "TASK_PROGRESS", "task-progress")
                self.notified_requests.add(req_id)

    def _detect_file_creation_requests(self, agent_id: str, output: str):
        """Rileva richieste di creazione file da Claude Code"""

        # Pattern per richieste di creazione file
        if "Do you want to create" in output and "1. Yes" in output:
            # Estrai nome file dalla richiesta
            lines = output.split('\n')
            filename = None

            for line in lines:
                if "Do you want to create" in line:
                    # Estrai nome file dalla riga
                    parts = line.split("create")
                    if len(parts) > 1:
                        filename_part = parts[1].strip()
                        # Rimuovi caratteri non necessari
                        filename = filename_part.replace("?", "").strip()
                        break

            if filename:
                # Crea richiesta per creazione file
                req_id = self.request_manager.create_request(
                    agent_id=agent_id,
                    request_type=RequestType.BASH_COMMAND,  # Usa BASH_COMMAND per file creation
                    command=f"create_file {filename}",
                    description=f"Agent {agent_id} requesting file creation: {filename}"
                )

                print(f"🔍 Detected file creation request from {agent_id}: {filename}")

                # Notifica supervisor di nuova richiesta
                if req_id and req_id not in self.notified_requests:
                    self._notify_supervisor_new_request(req_id, agent_id, "FILE_CREATION", f"create {filename}")
                    self.notified_requests.add(req_id)

    def _notify_supervisor_new_request(self, request_id: str, agent_id: str, request_type: str, command: str):
        """Invia notifica al supervisor per nuova richiesta"""
        try:
            # Messaggi molto specifici per evitare azioni indesiderate del supervisor
            if request_type == "FILE_CREATION":
                alert_message = f"NOTIFICATION ONLY: Agent {agent_id} awaiting user approval to create file. No supervisor action required. Check Request Manager tab for manual approval."
            elif request_type == "TASK_COMPLETE":
                alert_message = f"INFORMATION: Agent {agent_id} has finished assigned task. Please review completion status. No immediate action required."
            elif request_type == "BASH_COMMAND":
                alert_message = f"SECURITY REVIEW: Agent {agent_id} requesting permission to execute command. Manual approval needed in Request Manager. Do not take agent actions."
            else:
                alert_message = f"STATUS UPDATE: Agent {agent_id} has pending {request_type} request. Manual review required. No agent modifications needed."

            # PRIMO COMANDO BASH SEPARATO: Incolla solo il messaggio di notifica
            subprocess.run([
                "/opt/homebrew/bin/tmux", "send-keys", "-t", "claude-supervisor", alert_message
            ], check=True)

            print(f"📤 Phase 1: Sent detailed command to supervisor terminal")

            # Pausa tra i due comandi
            time.sleep(1.0)

            # SECONDO COMANDO BASH SEPARATO: Invia Enter
            subprocess.run([
                "/opt/homebrew/bin/tmux", "send-keys", "-t", "claude-supervisor", "Enter"
            ], check=True)

            print(f"📡 Phase 2: Executed command - Notified supervisor about request {request_id} from {agent_id}")

        except Exception as e:
            print(f"❌ Failed to notify supervisor: {e}")

    def _process_auto_approved_requests(self):
        """Processa richieste auto-approvate"""

        try:
            # Ottieni richieste approvate non ancora eseguite
            for request in self.request_manager.requests.values():
                if (request.status.value == "approved" and
                    request.auto_approve and
                    not request.executed_at):

                    # Esegui richiesta
                    success = self.request_manager.execute_request(request.request_id)
                    if success:
                        print(f"⚡ Auto-executed request {request.request_id}")

        except Exception as e:
            print(f"❌ Error processing auto-approved requests: {e}")

    def get_monitoring_status(self) -> dict:
        """Ottieni status monitoraggio"""

        pending_requests = self.request_manager.get_pending_requests()
        recent_requests = self.request_manager.get_request_history(10)

        return {
            "monitoring": self.monitoring,
            "pending_count": len(pending_requests),
            "recent_count": len(recent_requests),
            "pending_requests": [
                {
                    "id": req.request_id,
                    "agent": req.agent_id,
                    "command": req.command,
                    "risk": req.risk_level,
                    "created": req.created_at.strftime("%H:%M:%S")
                }
                for req in pending_requests
            ]
        }

def main():
    """Test del monitor"""

    monitor = AgentRequestMonitor()

    print("🔍 Starting Agent Request Monitor Test")
    monitor.start_monitoring()

    try:
        # Monitora per 30 secondi
        for i in range(6):
            time.sleep(5)
            status = monitor.get_monitoring_status()
            print(f"Status: {status['pending_count']} pending, {status['recent_count']} recent")

    except KeyboardInterrupt:
        print("\n🛑 Stopping monitor...")
    finally:
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()