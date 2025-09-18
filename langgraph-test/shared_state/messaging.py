"""
Inter-Agent Messaging System
Implements direct communication between agents with real-time notifications
"""

from typing import Dict, List, Any, Optional, Literal
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json


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
    """Single message between agents"""
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


@dataclass
class AgentInbox:
    """Message inbox for a single agent"""
    agent_id: str
    messages: List[AgentMessage] = field(default_factory=list)
    unread_count: int = 0
    last_checked: datetime = field(default_factory=datetime.now)

    def add_message(self, message: AgentMessage):
        """Add a new message to inbox"""
        self.messages.append(message)
        if message.status != MessageStatus.READ:
            self.unread_count += 1
        # Keep only last 1000 messages to prevent memory issues
        if len(self.messages) > 1000:
            self.messages = self.messages[-1000:]

    def mark_message_read(self, message_id: str, reader_id: str) -> bool:
        """Mark a specific message as read"""
        for message in self.messages:
            if message.message_id == message_id:
                if message.status != MessageStatus.READ:
                    message.mark_as_read(reader_id)
                    self.unread_count = max(0, self.unread_count - 1)
                return True
        return False

    def get_unread_messages(self) -> List[AgentMessage]:
        """Get all unread messages"""
        return [msg for msg in self.messages if msg.status != MessageStatus.READ]

    def get_messages_by_sender(self, sender_id: str) -> List[AgentMessage]:
        """Get all messages from a specific sender"""
        return [msg for msg in self.messages if msg.sender_id == sender_id]

    def get_recent_messages(self, limit: int = 50) -> List[AgentMessage]:
        """Get most recent messages"""
        return sorted(self.messages, key=lambda x: x.timestamp, reverse=True)[:limit]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "agent_id": self.agent_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "unread_count": self.unread_count,
            "last_checked": self.last_checked.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentInbox":
        """Create instance from dictionary"""
        inbox = cls(agent_id=data.get("agent_id", ""))
        inbox.messages = [AgentMessage.from_dict(msg_data) for msg_data in data.get("messages", [])]
        inbox.unread_count = data.get("unread_count", 0)
        inbox.last_checked = datetime.fromisoformat(data.get("last_checked", datetime.now().isoformat()))
        return inbox


class MessagingSystem:
    """Core messaging system for inter-agent communication"""

    def __init__(self):
        self.inboxes: Dict[str, AgentInbox] = {}
        self.message_history: List[AgentMessage] = []
        self.observers: List[callable] = []

    def register_agent(self, agent_id: str):
        """Register an agent for messaging"""
        if agent_id not in self.inboxes:
            self.inboxes[agent_id] = AgentInbox(agent_id=agent_id)

    def send_message(self, sender_id: str, recipient_id: str, content: str,
                    subject: Optional[str] = None, priority: MessagePriority = MessagePriority.NORMAL,
                    message_type: MessageType = MessageType.DIRECT) -> AgentMessage:
        """Send a direct message to another agent"""
        message = AgentMessage(
            sender_id=sender_id,
            recipient_id=recipient_id,
            content=content,
            subject=subject,
            priority=priority,
            message_type=message_type
        )

        # Ensure both agents are registered
        self.register_agent(sender_id)
        self.register_agent(recipient_id)

        # Add to recipient's inbox
        self.inboxes[recipient_id].add_message(message)

        # Add to message history
        self.message_history.append(message)

        # Notify observers
        self._notify_observers("message_sent", message)

        return message

    def broadcast_message(self, sender_id: str, content: str, subject: Optional[str] = None,
                         priority: MessagePriority = MessagePriority.NORMAL,
                         exclude_agents: Optional[List[str]] = None) -> List[AgentMessage]:
        """Send a broadcast message to all agents except sender"""
        exclude_agents = exclude_agents or []
        exclude_agents.append(sender_id)  # Don't send to self

        messages = []

        for agent_id in self.inboxes.keys():
            if agent_id not in exclude_agents:
                message = AgentMessage(
                    sender_id=sender_id,
                    recipient_id=agent_id,
                    content=content,
                    subject=subject,
                    priority=priority,
                    message_type=MessageType.BROADCAST
                )

                self.inboxes[agent_id].add_message(message)
                self.message_history.append(message)
                messages.append(message)

        # Notify observers
        self._notify_observers("broadcast_sent", {"sender": sender_id, "messages": messages})

        return messages

    def get_inbox(self, agent_id: str) -> AgentInbox:
        """Get agent's inbox"""
        self.register_agent(agent_id)
        return self.inboxes[agent_id]

    def mark_message_read(self, agent_id: str, message_id: str) -> bool:
        """Mark a message as read"""
        if agent_id in self.inboxes:
            result = self.inboxes[agent_id].mark_message_read(message_id, agent_id)
            if result:
                self._notify_observers("message_read", {"agent_id": agent_id, "message_id": message_id})
            return result
        return False

    def get_conversation(self, agent1_id: str, agent2_id: str) -> List[AgentMessage]:
        """Get conversation between two agents"""
        conversation = []

        # Get messages from agent1 to agent2
        if agent1_id in self.inboxes:
            conversation.extend([
                msg for msg in self.inboxes[agent2_id].messages
                if msg.sender_id == agent1_id and msg.recipient_id == agent2_id
            ])

        # Get messages from agent2 to agent1
        if agent2_id in self.inboxes:
            conversation.extend([
                msg for msg in self.inboxes[agent1_id].messages
                if msg.sender_id == agent2_id and msg.recipient_id == agent1_id
            ])

        # Sort by timestamp
        return sorted(conversation, key=lambda x: x.timestamp)

    def get_system_stats(self) -> Dict[str, Any]:
        """Get messaging system statistics"""
        total_messages = len(self.message_history)
        unread_messages = sum(inbox.unread_count for inbox in self.inboxes.values())

        return {
            "total_agents": len(self.inboxes),
            "total_messages": total_messages,
            "unread_messages": unread_messages,
            "active_conversations": len([
                inbox for inbox in self.inboxes.values()
                if len(inbox.messages) > 0
            ])
        }

    def add_observer(self, callback: callable):
        """Add observer for messaging events"""
        self.observers.append(callback)

    def _notify_observers(self, event_type: str, data: Any):
        """Notify all observers of messaging events"""
        for observer in self.observers:
            try:
                observer(event_type, data)
            except Exception as e:
                print(f"Error notifying observer: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "inboxes": {agent_id: inbox.to_dict() for agent_id, inbox in self.inboxes.items()},
            "message_history": [msg.to_dict() for msg in self.message_history[-1000:]]  # Last 1000 messages
        }

    def from_dict(self, data: Dict[str, Any]):
        """Load from dictionary"""
        self.inboxes = {
            agent_id: AgentInbox.from_dict(inbox_data)
            for agent_id, inbox_data in data.get("inboxes", {}).items()
        }
        self.message_history = [
            AgentMessage.from_dict(msg_data)
            for msg_data in data.get("message_history", [])
        ]


# Terminal command helpers
def create_send_message_command(messaging_system: MessagingSystem, current_agent_id: str):
    """Create send-message terminal command function"""
    def send_message_cmd(recipient_id: str, *message_parts):
        """Send message: send-message <recipient_id> <message>"""
        if not recipient_id:
            return "❌ Error: Recipient ID required"

        if not message_parts:
            return "❌ Error: Message content required"

        content = " ".join(message_parts)

        try:
            message = messaging_system.send_message(
                sender_id=current_agent_id,
                recipient_id=recipient_id,
                content=content
            )
            return f"✅ Message sent to {recipient_id} (ID: {message.message_id[:8]})"
        except Exception as e:
            return f"❌ Error sending message: {str(e)}"

    return send_message_cmd


def create_broadcast_command(messaging_system: MessagingSystem, current_agent_id: str):
    """Create broadcast terminal command function"""
    def broadcast_cmd(*message_parts):
        """Broadcast message: broadcast <message>"""
        if not message_parts:
            return "❌ Error: Message content required"

        content = " ".join(message_parts)

        try:
            messages = messaging_system.broadcast_message(
                sender_id=current_agent_id,
                content=content
            )
            return f"✅ Broadcast sent to {len(messages)} agents"
        except Exception as e:
            return f"❌ Error broadcasting message: {str(e)}"

    return broadcast_cmd


def create_inbox_command(messaging_system: MessagingSystem, current_agent_id: str):
    """Create inbox terminal command function"""
    def inbox_cmd(action: str = "list", message_id: str = ""):
        """Inbox management: inbox [list|read <message_id>|unread]"""
        inbox = messaging_system.get_inbox(current_agent_id)

        if action == "list":
            recent_messages = inbox.get_recent_messages(10)
            if not recent_messages:
                return "📭 No messages in inbox"

            result = f"📬 Inbox ({inbox.unread_count} unread):\n"
            for msg in recent_messages:
                status_icon = "📩" if msg.status == MessageStatus.READ else "📬"
                msg_type = "🔊" if msg.is_broadcast() else "💬"
                result += f"{status_icon} {msg_type} [{msg.message_id[:8]}] From: {msg.sender_id}\n"
                result += f"   Subject: {msg.subject or 'No subject'}\n"
                result += f"   Content: {msg.content[:50]}{'...' if len(msg.content) > 50 else ''}\n"
                result += f"   Time: {msg.timestamp.strftime('%H:%M:%S')}\n\n"
            return result.strip()

        elif action == "read" and message_id:
            for msg in inbox.messages:
                if msg.message_id.startswith(message_id):
                    messaging_system.mark_message_read(current_agent_id, msg.message_id)
                    msg_type = "🔊 BROADCAST" if msg.is_broadcast() else "💬 DIRECT"
                    return f"📖 {msg_type} Message from {msg.sender_id}:\n" \
                           f"Subject: {msg.subject or 'No subject'}\n" \
                           f"Content: {msg.content}\n" \
                           f"Time: {msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            return f"❌ Message {message_id} not found"

        elif action == "unread":
            unread_messages = inbox.get_unread_messages()
            if not unread_messages:
                return "📭 No unread messages"

            result = f"📬 {len(unread_messages)} unread messages:\n"
            for msg in unread_messages[-5:]:  # Last 5 unread
                msg_type = "🔊" if msg.is_broadcast() else "💬"
                result += f"{msg_type} [{msg.message_id[:8]}] {msg.sender_id}: {msg.content[:30]}...\n"
            return result.strip()

        else:
            return "Usage: inbox [list|read <message_id>|unread]"

    return inbox_cmd