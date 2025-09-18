#!/usr/bin/env python3
"""
🎯 Agent Request Manager - Sistema di Tracciamento e Autorizzazione Richieste
Gestisce le richieste degli agenti con sistema di autorizzazione e trigger
"""

import sys
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared_state.manager import SharedStateManager

class RequestType(Enum):
    """Tipi di richieste degli agenti"""
    BASH_COMMAND = "bash_command"
    TASK_COMPLETE = "task_complete"
    TASK_PROGRESS = "task_progress"
    TASK_FAIL = "task_fail"
    FILE_ACCESS = "file_access"
    SYSTEM_ACCESS = "system_access"

class RequestStatus(Enum):
    """Status delle richieste"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    TIMEOUT = "timeout"

@dataclass
class AgentRequest:
    """Rappresenta una richiesta di un agente"""
    request_id: str
    agent_id: str
    request_type: RequestType
    command: str
    description: str
    created_at: datetime
    status: RequestStatus
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    result: Optional[str] = None
    risk_level: str = "medium"  # low, medium, high, critical
    auto_approve: bool = False

class AgentRequestManager:
    """Gestore centrale delle richieste degli agenti"""

    def __init__(self):
        self.requests: Dict[str, AgentRequest] = {}
        self.pending_requests: List[str] = []
        self.approval_rules: Dict[RequestType, Callable] = {}
        self.auto_approval_patterns: List[Dict] = []

        # Thread safety
        self.lock = threading.RLock()

        # Persistence
        self.requests_file = "/Users/erik/Desktop/claude-multiagent-system/langgraph-test/agent_requests.json"

        # SharedState integration
        self.state_manager = SharedStateManager(
            persistence_type="json",
            persistence_file="/Users/erik/Desktop/claude-multiagent-system/langgraph-test/shared_state.json"
        )

        # Initialize default rules
        self._setup_default_rules()
        self._load_requests()

    def _setup_default_rules(self):
        """Configura regole di autorizzazione di default"""

        # Regole per comandi bash
        self.approval_rules[RequestType.BASH_COMMAND] = self._evaluate_bash_command
        self.approval_rules[RequestType.TASK_COMPLETE] = self._evaluate_task_complete
        self.approval_rules[RequestType.TASK_PROGRESS] = self._evaluate_task_progress

        # Pattern per auto-approvazione
        self.auto_approval_patterns = [
            {
                "type": RequestType.BASH_COMMAND,
                "patterns": ["echo", "task-status", "task-help"],
                "risk_level": "low"
            },
            {
                "type": RequestType.TASK_PROGRESS,
                "patterns": [".*"],
                "risk_level": "low"
            }
        ]

    def create_request(self, agent_id: str, request_type: RequestType,
                      command: str, description: str = "") -> str:
        """Crea una nuova richiesta"""

        with self.lock:
            request_id = f"req_{int(time.time() * 1000)}"

            # Valuta livello di rischio
            risk_level = self._assess_risk(request_type, command)

            # Controlla auto-approvazione
            auto_approve = self._check_auto_approval(request_type, command, risk_level)

            request = AgentRequest(
                request_id=request_id,
                agent_id=agent_id,
                request_type=request_type,
                command=command,
                description=description or f"{request_type.value}: {command}",
                created_at=datetime.now(),
                status=RequestStatus.APPROVED if auto_approve else RequestStatus.PENDING,
                risk_level=risk_level,
                auto_approve=auto_approve
            )

            if auto_approve:
                request.approved_by = "auto_system"
                request.approved_at = datetime.now()
                print(f"✅ Auto-approved request {request_id}: {command}")
            else:
                self.pending_requests.append(request_id)
                print(f"⏳ Pending approval request {request_id}: {command}")

            self.requests[request_id] = request
            self._save_requests()

            return request_id

    def _assess_risk(self, request_type: RequestType, command: str) -> str:
        """Valuta il livello di rischio di una richiesta"""

        # Comandi critici
        critical_patterns = ["rm -rf", "sudo", "chmod 777", ">/dev/null", "kill -9"]
        high_patterns = ["git push", "npm install", "pip install", "curl", "wget"]
        low_patterns = ["echo", "ls", "pwd", "task-", "help"]

        command_lower = command.lower()

        if any(pattern in command_lower for pattern in critical_patterns):
            return "critical"
        elif any(pattern in command_lower for pattern in high_patterns):
            return "high"
        elif any(pattern in command_lower for pattern in low_patterns):
            return "low"
        else:
            return "medium"

    def _check_auto_approval(self, request_type: RequestType, command: str, risk_level: str) -> bool:
        """Controlla se la richiesta può essere auto-approvata"""

        # Non auto-approva mai richieste critiche
        if risk_level == "critical":
            return False

        # Controlla pattern di auto-approvazione
        for pattern_rule in self.auto_approval_patterns:
            if pattern_rule["type"] == request_type:
                import re
                for pattern in pattern_rule["patterns"]:
                    if re.search(pattern, command, re.IGNORECASE):
                        return risk_level in ["low", "medium"]

        return False

    def _evaluate_bash_command(self, request: AgentRequest) -> bool:
        """Valuta se approvare un comando bash"""

        # Verifica che l'agente abbia un task attivo per comandi task-*
        if request.command.startswith("task-"):
            agent = self.state_manager.state.agents.get(request.agent_id)
            if agent and agent.current_task:
                return True

        # Altri criteri di valutazione
        return request.risk_level in ["low", "medium"]

    def _evaluate_task_complete(self, request: AgentRequest) -> bool:
        """Valuta se approvare un task-complete"""

        # Verifica che l'agente abbia effettivamente un task attivo
        agent = self.state_manager.state.agents.get(request.agent_id)
        return bool(agent and agent.current_task)

    def _evaluate_task_progress(self, request: AgentRequest) -> bool:
        """Valuta se approvare un task-progress"""

        # Progress updates sono generalmente sicuri
        return True

    def approve_request(self, request_id: str, approver: str = "manual") -> bool:
        """Approva una richiesta"""

        with self.lock:
            if request_id not in self.requests:
                return False

            request = self.requests[request_id]
            if request.status != RequestStatus.PENDING:
                return False

            request.status = RequestStatus.APPROVED
            request.approved_by = approver
            request.approved_at = datetime.now()

            if request_id in self.pending_requests:
                self.pending_requests.remove(request_id)

            self._save_requests()
            print(f"✅ Request {request_id} approved by {approver}")
            return True

    def reject_request(self, request_id: str, reason: str = "") -> bool:
        """Rifiuta una richiesta"""

        with self.lock:
            if request_id not in self.requests:
                return False

            request = self.requests[request_id]
            if request.status != RequestStatus.PENDING:
                return False

            request.status = RequestStatus.REJECTED
            request.result = f"Rejected: {reason}"

            if request_id in self.pending_requests:
                self.pending_requests.remove(request_id)

            self._save_requests()
            print(f"❌ Request {request_id} rejected: {reason}")
            return True

    def execute_request(self, request_id: str) -> bool:
        """Esegue una richiesta approvata"""

        with self.lock:
            if request_id not in self.requests:
                return False

            request = self.requests[request_id]
            if request.status != RequestStatus.APPROVED:
                return False

            # Esecuzione basata sul tipo
            success = self._execute_by_type(request)

            request.status = RequestStatus.EXECUTED if success else RequestStatus.REJECTED
            request.executed_at = datetime.now()

            self._save_requests()
            return success

    def _execute_by_type(self, request: AgentRequest) -> bool:
        """Esegue la richiesta basata sul tipo"""

        try:
            if request.request_type == RequestType.BASH_COMMAND:
                return self._execute_bash_command(request)
            elif request.request_type == RequestType.TASK_COMPLETE:
                return self._execute_task_complete(request)
            elif request.request_type == RequestType.TASK_PROGRESS:
                return self._execute_task_progress(request)
            else:
                return False
        except Exception as e:
            request.result = f"Execution error: {e}"
            return False

    def _execute_bash_command(self, request: AgentRequest) -> bool:
        """Esegue un comando bash"""
        import subprocess

        try:
            # Per sicurezza, esegui solo comandi task-* direttamente
            if request.command.startswith("task-"):
                # Esegui tramite tmux nella sessione dell'agente
                agent = self.state_manager.state.agents.get(request.agent_id)
                if agent:
                    session_id = agent.session_id
                    subprocess.run([
                        "tmux", "send-keys", "-t", session_id,
                        request.command
                    ], check=True)

                    # Wait for command to be processed, then send Enter
                    import time
                    time.sleep(0.1)  # Short delay to let command be processed
                    subprocess.run([
                        "tmux", "send-keys", "-t", session_id,
                        "Enter"
                    ], check=True)
                    request.result = "Command sent to agent terminal"
                    return True

            request.result = "Command type not supported for execution"
            return False

        except Exception as e:
            request.result = f"Bash execution error: {e}"
            return False

    def _execute_task_complete(self, request: AgentRequest) -> bool:
        """Esegue completamento task"""

        try:
            # Estrai parametri dal comando
            parts = request.command.split('"')
            message = parts[1] if len(parts) > 1 else "Task completed via request system"

            # Ottieni current task per l'agente
            agent = self.state_manager.state.agents.get(request.agent_id)
            if not agent or not agent.current_task:
                request.result = "No active task for agent"
                return False

            # Completa il task
            success = self.state_manager.complete_task(
                agent.current_task,
                {request.agent_id: message}
            )

            request.result = "Task completed successfully" if success else "Task completion failed"
            return success

        except Exception as e:
            request.result = f"Task completion error: {e}"
            return False

    def _execute_task_progress(self, request: AgentRequest) -> bool:
        """Esegue aggiornamento progresso task"""

        try:
            # Estrai percentuale dal comando
            import re
            match = re.search(r'(\d+)', request.command)
            if not match:
                request.result = "Invalid progress format"
                return False

            progress = float(match.group(1))

            # Aggiorna progresso nel current task
            current_task = self.state_manager.state.current_task
            if current_task:
                current_task.progress = progress
                self.state_manager.save_state()
                request.result = f"Progress updated to {progress}%"
                return True
            else:
                request.result = "No active task to update"
                return False

        except Exception as e:
            request.result = f"Progress update error: {e}"
            return False

    def get_pending_requests(self) -> List[AgentRequest]:
        """Ottiene richieste in attesa di approvazione"""

        with self.lock:
            return [self.requests[req_id] for req_id in self.pending_requests
                   if req_id in self.requests]

    def get_request_history(self, limit: int = 20) -> List[AgentRequest]:
        """Ottiene storico richieste"""

        with self.lock:
            requests = list(self.requests.values())
            requests.sort(key=lambda x: x.created_at, reverse=True)
            return requests[:limit]

    def cleanup_old_requests(self, days: int = 7):
        """Rimuove richieste vecchie"""

        with self.lock:
            cutoff = datetime.now() - timedelta(days=days)

            to_remove = []
            for req_id, request in self.requests.items():
                if request.created_at < cutoff:
                    to_remove.append(req_id)

            for req_id in to_remove:
                del self.requests[req_id]
                if req_id in self.pending_requests:
                    self.pending_requests.remove(req_id)

            self._save_requests()
            print(f"🧹 Cleaned up {len(to_remove)} old requests")

    def _save_requests(self):
        """Salva richieste su file"""

        try:
            data = {
                "requests": {req_id: {
                    **asdict(request),
                    "created_at": request.created_at.isoformat(),
                    "approved_at": request.approved_at.isoformat() if request.approved_at else None,
                    "executed_at": request.executed_at.isoformat() if request.executed_at else None,
                    "request_type": request.request_type.value,
                    "status": request.status.value
                } for req_id, request in self.requests.items()},
                "pending_requests": self.pending_requests
            }

            with open(self.requests_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"❌ Error saving requests: {e}")

    def _load_requests(self):
        """Carica richieste da file"""

        try:
            with open(self.requests_file, 'r') as f:
                data = json.load(f)

            for req_id, req_data in data.get("requests", {}).items():
                request = AgentRequest(
                    request_id=req_data["request_id"],
                    agent_id=req_data["agent_id"],
                    request_type=RequestType(req_data["request_type"]),
                    command=req_data["command"],
                    description=req_data["description"],
                    created_at=datetime.fromisoformat(req_data["created_at"]),
                    status=RequestStatus(req_data["status"]),
                    approved_by=req_data.get("approved_by"),
                    approved_at=datetime.fromisoformat(req_data["approved_at"]) if req_data.get("approved_at") else None,
                    executed_at=datetime.fromisoformat(req_data["executed_at"]) if req_data.get("executed_at") else None,
                    result=req_data.get("result"),
                    risk_level=req_data.get("risk_level", "medium"),
                    auto_approve=req_data.get("auto_approve", False)
                )
                self.requests[req_id] = request

            self.pending_requests = data.get("pending_requests", [])
            print(f"📋 Loaded {len(self.requests)} requests from storage")

        except FileNotFoundError:
            print("📋 No existing requests file - starting fresh")
        except Exception as e:
            print(f"❌ Error loading requests: {e}")

def main():
    """Test del sistema"""

    manager = AgentRequestManager()

    print("🎯 Agent Request Manager Test")
    print("=" * 40)

    # Test richiesta
    req_id = manager.create_request(
        agent_id="backend-api",
        request_type=RequestType.BASH_COMMAND,
        command="task-status",
        description="Check current task status"
    )

    print(f"Created request: {req_id}")

    # Mostra richieste pending
    pending = manager.get_pending_requests()
    print(f"Pending requests: {len(pending)}")

    for req in pending:
        print(f"  - {req.request_id}: {req.command} ({req.risk_level})")

if __name__ == "__main__":
    main()