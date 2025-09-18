"""
🚀 DRAMATIQ AGENT INTEGRATION SYSTEM
Complete replacement for tmux subprocess architecture with Dramatiq queue system
"""

import dramatiq
import json
import time
import threading
import subprocess
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our emergency database systems
from dramatiq_broker import setup_emergency_dramatiq_system
from dramatiq_database import DramatiqDatabaseBackend, DramatiqMessage, Priority

# Global broker instance
broker = None

class AgentRequestPriority(Enum):
    """Agent request priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    EMERGENCY = 5

class AgentRequestStatus(Enum):
    """Agent request status"""
    PENDING = "pending"
    APPROVED = "approved"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"

@dataclass
class AgentRequest:
    """Enhanced agent request structure"""
    request_id: str = field(default_factory=lambda: f"req_{uuid.uuid4().hex[:8]}")
    agent_id: str = ""
    session_id: str = ""
    command: str = ""
    description: str = ""
    priority: AgentRequestPriority = AgentRequestPriority.NORMAL
    status: AgentRequestStatus = AgentRequestStatus.PENDING
    auto_approve: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    approved_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None
    supervisor_notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "command": self.command,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "auto_approve": self.auto_approve,
            "created_at": self.created_at.isoformat(),
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "supervisor_notes": self.supervisor_notes,
            "metadata": self.metadata
        }

class DramatiqAgentManager:
    """🚀 Complete Agent Request Manager using Dramatiq"""

    def __init__(self):
        global broker

        # Initialize Dramatiq system
        broker = setup_emergency_dramatiq_system()
        self.broker = broker

        # Request storage
        self.pending_requests: Dict[str, AgentRequest] = {}
        self.active_requests: Dict[str, AgentRequest] = {}
        self.completed_requests: List[AgentRequest] = []

        # Statistics
        self.stats = {
            "total_requests": 0,
            "pending_requests": 0,
            "approved_requests": 0,
            "completed_requests": 0,
            "failed_requests": 0,
            "auto_approved": 0
        }

        # Thread safety
        self.lock = threading.RLock()

        # Monitoring
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_system, daemon=True)
        self.monitor_thread.start()

        logger.info("🚀 DramatiqAgentManager initialized with complete integration")

    def submit_agent_request(self, agent_id: str, session_id: str, command: str,
                           description: str = "", priority: AgentRequestPriority = AgentRequestPriority.NORMAL,
                           auto_approve: bool = False, **kwargs) -> str:
        """🚨 EMERGENCY: Submit agent request to Dramatiq queue system"""

        request = AgentRequest(
            agent_id=agent_id,
            session_id=session_id,
            command=command,
            description=description,
            priority=priority,
            auto_approve=auto_approve,
            **kwargs
        )

        with self.lock:
            self.pending_requests[request.request_id] = request
            self.stats["total_requests"] += 1
            self.stats["pending_requests"] += 1

        try:
            # Send notification to supervisor
            notify_supervisor_new_request.send(request.to_dict())

            # Auto-approve if enabled
            if auto_approve:
                self.approve_request(request.request_id, "Auto-approved by system")

            logger.info(f"📩 Agent request submitted: {request.request_id} from {agent_id}")
            return request.request_id

        except Exception as e:
            request.status = AgentRequestStatus.FAILED
            request.error = str(e)
            logger.error(f"❌ Failed to submit agent request {request.request_id}: {e}")
            return request.request_id

    def approve_request(self, request_id: str, supervisor_notes: str = "") -> bool:
        """🚨 EMERGENCY: Approve and execute agent request"""

        with self.lock:
            request = self.pending_requests.get(request_id)
            if not request:
                logger.warning(f"⚠️ Request {request_id} not found for approval")
                return False

            if request.status != AgentRequestStatus.PENDING:
                logger.warning(f"⚠️ Request {request_id} not in pending status: {request.status}")
                return False

            # Move to approved status
            request.status = AgentRequestStatus.APPROVED
            request.approved_at = datetime.now()
            request.supervisor_notes = supervisor_notes

            # Move to active requests
            self.active_requests[request_id] = request
            del self.pending_requests[request_id]

            self.stats["pending_requests"] -= 1
            self.stats["approved_requests"] += 1

            if request.auto_approve:
                self.stats["auto_approved"] += 1

        try:
            # Execute the approved command via Dramatiq
            execute_approved_command.send(request.to_dict())

            logger.info(f"✅ Request approved and queued: {request_id}")
            return True

        except Exception as e:
            request.status = AgentRequestStatus.FAILED
            request.error = str(e)
            logger.error(f"❌ Failed to execute approved request {request_id}: {e}")
            return False

    def reject_request(self, request_id: str, reason: str = "") -> bool:
        """🚨 EMERGENCY: Reject agent request"""

        with self.lock:
            request = self.pending_requests.get(request_id)
            if not request:
                return False

            request.status = AgentRequestStatus.REJECTED
            request.supervisor_notes = reason
            request.completed_at = datetime.now()

            # Move to completed
            self.completed_requests.append(request)
            del self.pending_requests[request_id]

            self.stats["pending_requests"] -= 1

        # Notify agent of rejection
        try:
            notify_agent_request_result.send({
                "request_id": request_id,
                "session_id": request.session_id,
                "status": "rejected",
                "reason": reason
            })

            logger.info(f"❌ Request rejected: {request_id} - {reason}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to notify rejection for {request_id}: {e}")
            return False

    def get_pending_requests(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get pending requests requiring supervisor attention"""

        with self.lock:
            pending = list(self.pending_requests.values())

        # Sort by priority and creation time
        pending.sort(key=lambda r: (r.priority.value, r.created_at), reverse=True)

        return [req.to_dict() for req in pending[:limit]]

    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific request"""

        with self.lock:
            # Check pending
            if request_id in self.pending_requests:
                return self.pending_requests[request_id].to_dict()

            # Check active
            if request_id in self.active_requests:
                return self.active_requests[request_id].to_dict()

            # Check completed
            for req in self.completed_requests:
                if req.request_id == request_id:
                    return req.to_dict()

        return None

    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""

        with self.lock:
            # Get broker health
            broker_health = self.broker.db_backend.get_system_health()

            return {
                **self.stats,
                "active_requests_count": len(self.active_requests),
                "completed_requests_count": len(self.completed_requests),
                "broker_health": broker_health,
                "timestamp": datetime.now().isoformat()
            }

    def emergency_drain_requests(self) -> Dict[str, Any]:
        """🚨 EMERGENCY: Process all pending requests immediately"""

        logger.warning("🚨 EMERGENCY REQUEST DRAIN INITIATED")

        with self.lock:
            pending_reqs = list(self.pending_requests.values())

        results = {
            "total_drained": len(pending_reqs),
            "auto_approved": 0,
            "requiring_manual": 0,
            "start_time": datetime.now().isoformat()
        }

        for request in pending_reqs:
            if request.auto_approve or request.priority == AgentRequestPriority.EMERGENCY:
                self.approve_request(request.request_id, "Emergency auto-approval")
                results["auto_approved"] += 1
            else:
                results["requiring_manual"] += 1

        results["end_time"] = datetime.now().isoformat()
        logger.info(f"🚨 Emergency drain completed: {results}")
        return results

    def _monitor_system(self):
        """Monitor system health and cleanup"""

        while self.monitoring_active:
            try:
                with self.lock:
                    # Check for stuck active requests
                    now = datetime.now()
                    stuck_requests = []

                    for req_id, request in self.active_requests.items():
                        if request.started_at:
                            time_elapsed = (now - request.started_at).total_seconds()
                            if time_elapsed > 300:  # 5 minutes timeout
                                stuck_requests.append(req_id)

                    # Handle stuck requests
                    for req_id in stuck_requests:
                        request = self.active_requests[req_id]
                        request.status = AgentRequestStatus.FAILED
                        request.error = "Request timeout - no response from agent"
                        request.completed_at = now

                        self.completed_requests.append(request)
                        del self.active_requests[req_id]

                        logger.warning(f"⏰ Request {req_id} timed out and marked as failed")

                    # Cleanup old completed requests (keep last 1000)
                    if len(self.completed_requests) > 1000:
                        self.completed_requests = self.completed_requests[-500:]

                time.sleep(30)  # Monitor every 30 seconds

            except Exception as e:
                logger.error(f"❌ Monitor error: {e}")
                time.sleep(60)

    def close(self):
        """Graceful shutdown"""

        logger.info("🛑 Shutting down DramatiqAgentManager...")

        self.monitoring_active = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)

        if self.broker:
            self.broker.close()

        logger.info("✅ DramatiqAgentManager shutdown complete")

# Global manager instance
agent_manager = DramatiqAgentManager()

# ===== DRAMATIQ ACTORS =====

@dramatiq.actor(queue_name="supervisor", max_retries=3, time_limit=60000)
def notify_supervisor_new_request(request_data: Dict[str, Any]):
    """🚨 EMERGENCY: Notify supervisor of new agent request"""

    try:
        request_id = request_data["request_id"]
        agent_id = request_data["agent_id"]
        session_id = request_data["session_id"]
        command = request_data["command"]
        priority = request_data["priority"]

        # Format notification message
        priority_emoji = {
            1: "🔵", 2: "🟡", 3: "🟠", 4: "🔴", 5: "🚨"
        }

        emoji = priority_emoji.get(priority, "🟡")

        notification = f"""
{emoji} NEW AGENT REQUEST {emoji}

Request ID: {request_id}
Agent: {agent_id}
Session: {session_id}
Command: {command}
Description: {request_data.get('description', 'No description')}
Priority: {priority}

⚡ Use: approve {request_id} <notes>
❌ Use: reject {request_id} <reason>
        """

        # Send to supervisor tmux session
        supervisor_session = "claude-supervisor"

        subprocess.run([
            "tmux", "send-keys", "-t", supervisor_session,
            f"echo '{notification.strip()}'", "Enter"
        ], check=False)

        logger.info(f"📢 Supervisor notified of request {request_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to notify supervisor: {e}")
        raise

@dramatiq.actor(queue_name="execution", max_retries=2, time_limit=300000)
def execute_approved_command(request_data: Dict[str, Any]):
    """🚨 EMERGENCY: Execute approved agent command"""

    request_id = request_data["request_id"]

    try:
        # Update request status to processing
        with agent_manager.lock:
            if request_id in agent_manager.active_requests:
                request = agent_manager.active_requests[request_id]
                request.status = AgentRequestStatus.PROCESSING
                request.started_at = datetime.now()

        session_id = request_data["session_id"]
        command = request_data["command"]

        logger.info(f"🏃 Executing command for request {request_id}: {command}")

        # Execute command in target tmux session
        result = subprocess.run([
            "tmux", "send-keys", "-t", session_id, command, "Enter"
        ], capture_output=True, text=True, timeout=30)

        # Update request with results
        with agent_manager.lock:
            if request_id in agent_manager.active_requests:
                request = agent_manager.active_requests[request_id]
                request.completed_at = datetime.now()

                if result.returncode == 0:
                    request.status = AgentRequestStatus.COMPLETED
                    request.result = "Command executed successfully"
                    agent_manager.stats["completed_requests"] += 1
                else:
                    request.status = AgentRequestStatus.FAILED
                    request.error = result.stderr or "Command execution failed"
                    agent_manager.stats["failed_requests"] += 1

                # Move to completed
                agent_manager.completed_requests.append(request)
                del agent_manager.active_requests[request_id]

        # Notify agent of completion
        notify_agent_request_result.send({
            "request_id": request_id,
            "session_id": session_id,
            "status": request.status.value,
            "result": request.result,
            "error": request.error
        })

        logger.info(f"✅ Request {request_id} execution completed")
        return True

    except subprocess.TimeoutExpired:
        error_msg = f"Command execution timed out for request {request_id}"
        logger.error(f"⏰ {error_msg}")

        with agent_manager.lock:
            if request_id in agent_manager.active_requests:
                request = agent_manager.active_requests[request_id]
                request.status = AgentRequestStatus.FAILED
                request.error = error_msg
                request.completed_at = datetime.now()

                agent_manager.completed_requests.append(request)
                del agent_manager.active_requests[request_id]
                agent_manager.stats["failed_requests"] += 1

        raise

    except Exception as e:
        error_msg = f"Command execution failed for request {request_id}: {str(e)}"
        logger.error(f"❌ {error_msg}")

        with agent_manager.lock:
            if request_id in agent_manager.active_requests:
                request = agent_manager.active_requests[request_id]
                request.status = AgentRequestStatus.FAILED
                request.error = str(e)
                request.completed_at = datetime.now()

                agent_manager.completed_requests.append(request)
                del agent_manager.active_requests[request_id]
                agent_manager.stats["failed_requests"] += 1

        raise

@dramatiq.actor(queue_name="notifications", max_retries=3, time_limit=30000)
def notify_agent_request_result(result_data: Dict[str, Any]):
    """🚨 EMERGENCY: Notify agent of request result"""

    try:
        request_id = result_data["request_id"]
        session_id = result_data["session_id"]
        status = result_data["status"]

        # Format result message
        status_emoji = {
            "completed": "✅",
            "failed": "❌",
            "rejected": "🚫"
        }

        emoji = status_emoji.get(status, "ℹ️")

        if status == "completed":
            message = f"{emoji} Request {request_id} completed successfully"
            if result_data.get("result"):
                message += f": {result_data['result']}"
        elif status == "failed":
            message = f"{emoji} Request {request_id} failed"
            if result_data.get("error"):
                message += f": {result_data['error']}"
        elif status == "rejected":
            message = f"{emoji} Request {request_id} rejected"
            if result_data.get("reason"):
                message += f": {result_data['reason']}"
        else:
            message = f"{emoji} Request {request_id} status: {status}"

        # Send to agent tmux session
        subprocess.run([
            "tmux", "send-keys", "-t", session_id,
            f"echo '{message}'", "Enter"
        ], check=False)

        logger.info(f"📢 Agent {session_id} notified of request {request_id} result")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to notify agent: {e}")
        raise

# ===== INTEGRATION FUNCTIONS =====

def submit_agent_request(agent_id: str, session_id: str, command: str,
                        description: str = "", priority: str = "normal",
                        auto_approve: bool = False) -> str:
    """🚨 EMERGENCY: Submit agent request (API compatible)"""

    priority_map = {
        "low": AgentRequestPriority.LOW,
        "normal": AgentRequestPriority.NORMAL,
        "high": AgentRequestPriority.HIGH,
        "urgent": AgentRequestPriority.URGENT,
        "emergency": AgentRequestPriority.EMERGENCY
    }

    return agent_manager.submit_agent_request(
        agent_id=agent_id,
        session_id=session_id,
        command=command,
        description=description,
        priority=priority_map.get(priority, AgentRequestPriority.NORMAL),
        auto_approve=auto_approve
    )

def approve_agent_request(request_id: str, notes: str = "") -> bool:
    """🚨 EMERGENCY: Approve agent request (API compatible)"""
    return agent_manager.approve_request(request_id, notes)

def reject_agent_request(request_id: str, reason: str = "") -> bool:
    """🚨 EMERGENCY: Reject agent request (API compatible)"""
    return agent_manager.reject_request(request_id, reason)

def get_pending_requests() -> List[Dict[str, Any]]:
    """🚨 EMERGENCY: Get pending requests (API compatible)"""
    return agent_manager.get_pending_requests()

def get_system_status() -> Dict[str, Any]:
    """🚨 EMERGENCY: Get system status (API compatible)"""
    return agent_manager.get_system_stats()

# ===== TESTING FUNCTIONS =====

def emergency_test_integration():
    """🚨 EMERGENCY: Test complete Dramatiq agent integration"""

    print("🚨 EMERGENCY DRAMATIQ AGENT INTEGRATION TEST...")

    try:
        # Test 1: Submit agent request
        request_id = submit_agent_request(
            agent_id="test-agent",
            session_id="claude-backend-api",
            command="echo 'Dramatiq integration test successful'",
            description="Emergency integration test",
            priority="urgent",
            auto_approve=True
        )

        print(f"✅ Request submitted: {request_id}")

        # Test 2: Check system status
        status = get_system_status()
        print(f"📊 System status: {status['total_requests']} total requests")

        # Test 3: Wait for processing
        time.sleep(3)

        # Test 4: Check request status
        request_status = agent_manager.get_request_status(request_id)
        if request_status:
            print(f"📋 Request status: {request_status['status']}")

        print("🎉 DRAMATIQ AGENT INTEGRATION TEST COMPLETED!")
        return True

    except Exception as e:
        print(f"❌ INTEGRATION TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    emergency_test_integration()