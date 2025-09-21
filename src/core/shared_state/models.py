"""
Data models for SharedState system
"""

from typing import Dict, List, Any, Optional, Literal
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid


# Enhanced Messaging System Models
class MessageType(Enum):
    """Types of messages between agents"""
    DIRECT = "direct"           # One-to-one message
    BROADCAST = "broadcast"     # One-to-all message
    SYSTEM = "system"          # System notification
    TASK_UPDATE = "task_update" # Task-related update


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class MessageStatus(Enum):
    """Message delivery status"""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


@dataclass
class AgentMessage:
    """Enhanced message between agents with full metadata"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: Optional[str] = None  # None for broadcast messages
    message_type: MessageType = MessageType.DIRECT
    priority: MessagePriority = MessagePriority.NORMAL
    subject: Optional[str] = None
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    status: MessageStatus = MessageStatus.SENT
    read_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "subject": self.subject,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Create instance from dictionary"""
        message = cls()
        message.message_id = data.get("message_id", str(uuid.uuid4()))
        message.sender_id = data.get("sender_id", "")
        message.recipient_id = data.get("recipient_id")
        message.message_type = MessageType(data.get("message_type", "direct"))
        message.priority = MessagePriority(data.get("priority", 2))
        message.subject = data.get("subject")
        message.content = data.get("content", "")
        message.timestamp = datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat()))
        message.status = MessageStatus(data.get("status", "sent"))
        message.read_at = datetime.fromisoformat(data["read_at"]) if data.get("read_at") else None
        message.metadata = data.get("metadata", {})
        return message

    def mark_as_read(self, reader_id: str):
        """Mark message as read"""
        self.status = MessageStatus.READ
        self.read_at = datetime.now()
        self.metadata["read_by"] = reader_id

    def is_broadcast(self) -> bool:
        """Check if this is a broadcast message"""
        return self.message_type == MessageType.BROADCAST or self.recipient_id is None


class AgentStatus(Enum):
    """Status possibili per un agente"""
    IDLE = "idle"
    BUSY = "busy"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"


class TaskPriority(Enum):
    """Priorità task"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class AgentState:
    """Stato di un singolo agente"""
    agent_id: str
    name: str
    status: AgentStatus
    current_task: Optional[str] = None
    last_activity: datetime = field(default_factory=datetime.now)
    session_id: str = ""
    port: int = 0
    capabilities: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte in dizionario per serializzazione"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "current_task": self.current_task,
            "last_activity": self.last_activity.isoformat(),
            "session_id": self.session_id,
            "port": self.port,
            "capabilities": self.capabilities,
            "error_message": self.error_message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentState':
        """Crea AgentState da dizionario"""
        return cls(
            agent_id=data["agent_id"],
            name=data["name"],
            status=AgentStatus(data["status"]),
            current_task=data.get("current_task"),
            last_activity=datetime.fromisoformat(data["last_activity"]),
            session_id=data.get("session_id", ""),
            port=data.get("port", 0),
            capabilities=data.get("capabilities", []),
            error_message=data.get("error_message")
        )


@dataclass
class TaskInfo:
    """Informazioni su un task"""
    task_id: str
    description: str
    priority: TaskPriority
    created_at: datetime = field(default_factory=datetime.now)
    assigned_agents: List[str] = field(default_factory=list)
    status: Literal["pending", "in_progress", "completed", "failed"] = "pending"
    progress: float = 0.0
    results: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        """Auto-genera task_id se non fornito"""
        if not self.task_id:
            self.task_id = f"task_{uuid.uuid4().hex[:8]}"

    def to_dict(self) -> Dict[str, Any]:
        """Converte in dizionario per serializzazione"""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "assigned_agents": self.assigned_agents,
            "status": self.status,
            "progress": self.progress,
            "results": self.results,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskInfo':
        """Crea TaskInfo da dizionario"""
        return cls(
            task_id=data["task_id"],
            description=data["description"],
            priority=TaskPriority(data["priority"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            assigned_agents=data.get("assigned_agents", []),
            status=data.get("status", "pending"),
            progress=data.get("progress", 0.0),
            results=data.get("results", {}),
            error_message=data.get("error_message"),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        )


@dataclass
class InterAgentMessage:
    """Messaggio tra agenti"""
    message_id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")
    from_agent: str = ""
    to_agent: str = ""
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    read: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Converte in dizionario per serializzazione"""
        return {
            "message_id": self.message_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "read": self.read
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InterAgentMessage':
        """Crea InterAgentMessage da dizionario"""
        return cls(
            message_id=data["message_id"],
            from_agent=data["from_agent"],
            to_agent=data["to_agent"],
            message=data["message"],
            data=data.get("data", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            read=data.get("read", False)
        )


@dataclass
class SharedState:
    """Stato condiviso del sistema multi-agente"""
    # Task Management
    current_task: Optional[TaskInfo] = None
    task_queue: List[TaskInfo] = field(default_factory=list)
    task_history: List[TaskInfo] = field(default_factory=list)

    # Agent Management
    agents: Dict[str, AgentState] = field(default_factory=dict)

    # Communication
    messages: List[InterAgentMessage] = field(default_factory=list)

    # Shared Data
    shared_variables: Dict[str, Any] = field(default_factory=dict)

    # System State
    system_status: Literal["idle", "busy", "error"] = "idle"
    last_updated: datetime = field(default_factory=datetime.now)

    # Configuration
    settings: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converte in dizionario per serializzazione"""
        return {
            "current_task": self.current_task.to_dict() if self.current_task else None,
            "task_queue": [task.to_dict() for task in self.task_queue],
            "task_history": [task.to_dict() for task in self.task_history],
            "agents": {k: v.to_dict() for k, v in self.agents.items()},
            "messages": [msg.to_dict() for msg in self.messages],
            "shared_variables": self.shared_variables,
            "system_status": self.system_status,
            "last_updated": self.last_updated.isoformat(),
            "settings": self.settings
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SharedState':
        """Crea SharedState da dizionario"""
        return cls(
            current_task=TaskInfo.from_dict(data["current_task"]) if data.get("current_task") else None,
            task_queue=[TaskInfo.from_dict(task) for task in data.get("task_queue", [])],
            task_history=[TaskInfo.from_dict(task) for task in data.get("task_history", [])],
            agents={k: AgentState.from_dict(v) for k, v in data.get("agents", {}).items()},
            messages=[InterAgentMessage.from_dict(msg) for msg in data.get("messages", [])],
            shared_variables=data.get("shared_variables", {}),
            system_status=data.get("system_status", "idle"),
            last_updated=datetime.fromisoformat(data["last_updated"]) if data.get("last_updated") else datetime.now(),
            settings=data.get("settings", {})
        )

    def get_active_agents(self) -> List[AgentState]:
        """Ottieni agenti attivi (non idle)"""
        return [agent for agent in self.agents.values() if agent.status != AgentStatus.IDLE]

    def get_available_agents(self) -> List[AgentState]:
        """Ottieni agenti disponibili per nuovi task"""
        return [agent for agent in self.agents.values() if agent.status == AgentStatus.IDLE]

    def get_task_by_id(self, task_id: str) -> Optional[TaskInfo]:
        """Trova task per ID"""
        # Check current task
        if self.current_task and self.current_task.task_id == task_id:
            return self.current_task

        # Check queue
        for task in self.task_queue:
            if task.task_id == task_id:
                return task

        # Check history
        for task in self.task_history:
            if task.task_id == task_id:
                return task

        return None