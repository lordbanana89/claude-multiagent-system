#!/usr/bin/env python3
"""
Intelligent Message Management and Lifecycle System
Advanced inbox management with smart categorization and automated workflows
"""

import json
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Import from parent shared_state and messaging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_state.models import AgentMessage, MessagePriority
from messaging.classification import MessageClassifier, MessageCategory, ClassificationMessageType, ResponseRequirement


class MessageStatus(Enum):
    """Extended message status lifecycle"""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    ACKNOWLEDGED = "acknowledged"
    RESPONDED = "responded"
    ESCALATED = "escalated"
    ARCHIVED = "archived"
    EXPIRED = "expired"
    DELETED = "deleted"


class InboxCategory(Enum):
    """Inbox categorization"""
    URGENT = "urgent"              # Immediate attention required
    TASKS = "tasks"                # Task assignments
    QUESTIONS = "questions"        # Questions requiring response
    INFORMATION = "information"    # Informational messages
    COMPLETED = "completed"        # Completed/archived messages
    WAITING = "waiting"            # Waiting for response/action
    ESCALATED = "escalated"        # Escalated messages


@dataclass
class MessageMetrics:
    """Metrics for message tracking"""
    response_time_minutes: Optional[int] = None
    escalation_count: int = 0
    reminder_count: int = 0
    category_confidence: float = 0.0
    workflow_efficiency: float = 0.0


@dataclass
class ManagedMessage:
    """Enhanced message with management metadata"""
    message: AgentMessage
    category: MessageCategory
    status: MessageStatus
    inbox_category: InboxCategory
    created_at: datetime
    last_updated: datetime
    expires_at: Optional[datetime] = None
    escalated_to: Optional[str] = None
    response_deadline: Optional[datetime] = None
    reminder_sent: bool = False
    metrics: MessageMetrics = None
    tags: List[str] = None
    priority_boost: bool = False

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = MessageMetrics()
        if self.tags is None:
            self.tags = []


class IntelligentInbox:
    """Advanced inbox management with intelligent categorization"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.messages: Dict[str, ManagedMessage] = {}
        self.categories: Dict[InboxCategory, List[str]] = {
            category: [] for category in InboxCategory
        }
        self.classifier = MessageClassifier()
        self.auto_archive_hours = 72  # Auto-archive after 72 hours
        self.max_messages = 1000      # Maximum messages to keep

    def add_message(self, message: AgentMessage) -> ManagedMessage:
        """Add message to inbox with intelligent categorization"""

        # Classify the message
        category = self.classifier.classify_message(message)

        # Determine inbox category
        inbox_category = self._determine_inbox_category(category)

        # Determine status
        status = MessageStatus.DELIVERED

        # Calculate expiration and deadline
        expires_at = self._calculate_expiration(category)
        response_deadline = self._calculate_response_deadline(category)

        # Create managed message
        managed_msg = ManagedMessage(
            message=message,
            category=category,
            status=status,
            inbox_category=inbox_category,
            created_at=datetime.now(),
            last_updated=datetime.now(),
            expires_at=expires_at,
            response_deadline=response_deadline,
            metrics=MessageMetrics(category_confidence=category.confidence)
        )

        # Add to inbox
        self.messages[message.message_id] = managed_msg
        self.categories[inbox_category].append(message.message_id)

        # Apply auto-processing if configured
        self._apply_auto_processing(managed_msg)

        # Cleanup old messages if needed
        self._cleanup_old_messages()

        return managed_msg

    def update_message_status(self, message_id: str, new_status: MessageStatus, metadata: Dict[str, Any] = None) -> bool:
        """Update message status and metadata"""
        if message_id not in self.messages:
            return False

        managed_msg = self.messages[message_id]
        old_status = managed_msg.status

        # Update status
        managed_msg.status = new_status
        managed_msg.last_updated = datetime.now()

        # Calculate response time if transitioning to responded
        if new_status == MessageStatus.RESPONDED and old_status != MessageStatus.RESPONDED:
            response_time = (datetime.now() - managed_msg.created_at).total_seconds() / 60
            managed_msg.metrics.response_time_minutes = int(response_time)

        # Update category if status changed significantly
        if new_status in [MessageStatus.ARCHIVED]:
            self._move_to_category(message_id, InboxCategory.COMPLETED)
        elif new_status == MessageStatus.ESCALATED:
            self._move_to_category(message_id, InboxCategory.ESCALATED)

        # Apply metadata updates
        if metadata:
            if 'escalated_to' in metadata:
                managed_msg.escalated_to = metadata['escalated_to']
                managed_msg.metrics.escalation_count += 1
            if 'tags' in metadata:
                managed_msg.tags.extend(metadata['tags'])
            if 'priority_boost' in metadata:
                managed_msg.priority_boost = metadata['priority_boost']

        return True

    def get_category_messages(self, category: InboxCategory, limit: int = None) -> List[ManagedMessage]:
        """Get messages from specific category"""
        message_ids = self.categories[category]
        messages = [self.messages[msg_id] for msg_id in message_ids if msg_id in self.messages]

        # Sort by priority and recency
        messages.sort(key=lambda x: (
            -self._get_priority_score(x),
            -x.created_at.timestamp()
        ))

        return messages[:limit] if limit else messages

    def get_priority_inbox(self, limit: int = 10) -> List[ManagedMessage]:
        """Get priority messages requiring immediate attention"""
        all_messages = list(self.messages.values())

        # Filter active messages (not completed/archived)
        active_messages = [
            msg for msg in all_messages
            if msg.status not in [MessageStatus.ARCHIVED, MessageStatus.EXPIRED, MessageStatus.DELETED]
        ]

        # Sort by priority score
        active_messages.sort(key=lambda x: -self._get_priority_score(x))

        return active_messages[:limit]

    def get_overdue_messages(self) -> List[ManagedMessage]:
        """Get messages that are overdue for response"""
        now = datetime.now()
        overdue = []

        for managed_msg in self.messages.values():
            if (managed_msg.response_deadline and
                now > managed_msg.response_deadline and
                managed_msg.status not in [MessageStatus.RESPONDED, MessageStatus.ARCHIVED]):
                overdue.append(managed_msg)

        return sorted(overdue, key=lambda x: x.response_deadline)

    def auto_archive_eligible(self) -> List[str]:
        """Get messages eligible for auto-archiving"""
        cutoff_time = datetime.now() - timedelta(hours=self.auto_archive_hours)
        eligible = []

        for msg_id, managed_msg in self.messages.items():
            if (managed_msg.category.auto_archive and
                managed_msg.status in [MessageStatus.READ, MessageStatus.ACKNOWLEDGED] and
                managed_msg.last_updated < cutoff_time):
                eligible.append(msg_id)

        return eligible

    def search_messages(self, query: str, category: Optional[InboxCategory] = None) -> List[ManagedMessage]:
        """Search messages by content, subject, or sender"""
        query_lower = query.lower()
        results = []

        messages_to_search = (
            self.get_category_messages(category) if category
            else list(self.messages.values())
        )

        for managed_msg in messages_to_search:
            msg = managed_msg.message
            searchable_text = f"{msg.subject or ''} {msg.content} {msg.sender_id}".lower()

            if query_lower in searchable_text:
                results.append(managed_msg)

        return results

    def get_inbox_statistics(self) -> Dict[str, Any]:
        """Get comprehensive inbox statistics"""
        total_messages = len(self.messages)

        if total_messages == 0:
            return {'total_messages': 0}

        # Status distribution
        status_counts = {}
        category_counts = {}
        response_times = []
        overdue_count = 0

        now = datetime.now()

        for managed_msg in self.messages.values():
            # Count statuses
            status = managed_msg.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

            # Count categories
            category = managed_msg.inbox_category.value
            category_counts[category] = category_counts.get(category, 0) + 1

            # Collect response times
            if managed_msg.metrics.response_time_minutes:
                response_times.append(managed_msg.metrics.response_time_minutes)

            # Count overdue
            if (managed_msg.response_deadline and
                now > managed_msg.response_deadline and
                managed_msg.status not in [MessageStatus.RESPONDED, MessageStatus.ARCHIVED]):
                overdue_count += 1

        # Calculate averages
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        return {
            'total_messages': total_messages,
            'status_distribution': status_counts,
            'category_distribution': category_counts,
            'average_response_time_minutes': avg_response_time,
            'overdue_messages': overdue_count,
            'unread_count': status_counts.get('delivered', 0) + status_counts.get('read', 0),
            'completion_rate': (status_counts.get('responded', 0) + status_counts.get('archived', 0)) / total_messages * 100
        }

    def _determine_inbox_category(self, category: MessageCategory) -> InboxCategory:
        """Determine appropriate inbox category"""
        if category.urgency_level.value in ['urgent', 'critical']:
            return InboxCategory.URGENT
        elif category.message_type == ClassificationMessageType.TASK_ASSIGNMENT:
            return InboxCategory.TASKS
        elif category.message_type == ClassificationMessageType.QUESTION:
            return InboxCategory.QUESTIONS
        elif category.message_type == ClassificationMessageType.INFORMATION:
            return InboxCategory.INFORMATION
        else:
            return InboxCategory.WAITING

    def _calculate_expiration(self, category: MessageCategory) -> Optional[datetime]:
        """Calculate message expiration time"""
        if category.timeout_minutes:
            return datetime.now() + timedelta(minutes=category.timeout_minutes * 2)  # Double timeout for expiration
        return None

    def _calculate_response_deadline(self, category: MessageCategory) -> Optional[datetime]:
        """Calculate response deadline"""
        if category.timeout_minutes:
            return datetime.now() + timedelta(minutes=category.timeout_minutes)
        return None

    def _get_priority_score(self, managed_msg: ManagedMessage) -> float:
        """Calculate priority score for sorting"""
        score = 0.0

        # Base priority from message
        priority_scores = {
            MessagePriority.LOW: 1.0,
            MessagePriority.NORMAL: 2.0,
            MessagePriority.HIGH: 4.0,
            MessagePriority.URGENT: 8.0
        }
        score += priority_scores.get(managed_msg.message.priority, 2.0)

        # Urgency level boost
        urgency_boost = {
            'low': 0.0,
            'normal': 1.0,
            'high': 3.0,
            'urgent': 6.0,
            'critical': 10.0
        }
        score += urgency_boost.get(managed_msg.category.urgency_level.value, 1.0)

        # Time-based urgency (older messages get higher priority)
        age_hours = (datetime.now() - managed_msg.created_at).total_seconds() / 3600
        score += min(age_hours * 0.1, 2.0)  # Cap at 2.0 points for age

        # Overdue penalty/boost
        if managed_msg.response_deadline and datetime.now() > managed_msg.response_deadline:
            score += 5.0  # Big boost for overdue messages

        # Priority boost flag
        if managed_msg.priority_boost:
            score += 3.0

        return score

    def _move_to_category(self, message_id: str, new_category: InboxCategory):
        """Move message to different category"""
        if message_id not in self.messages:
            return

        managed_msg = self.messages[message_id]
        old_category = managed_msg.inbox_category

        # Remove from old category
        if message_id in self.categories[old_category]:
            self.categories[old_category].remove(message_id)

        # Add to new category
        managed_msg.inbox_category = new_category
        self.categories[new_category].append(message_id)

    def _apply_auto_processing(self, managed_msg: ManagedMessage):
        """Apply automatic processing rules"""
        # Auto-read informational messages
        if (managed_msg.category.message_type == ClassificationMessageType.INFORMATION and
            managed_msg.category.response_requirement == ResponseRequirement.NONE):
            managed_msg.status = MessageStatus.READ

        # Auto-acknowledge confirmations
        if managed_msg.category.message_type == ClassificationMessageType.CONFIRMATION:
            managed_msg.status = MessageStatus.ACKNOWLEDGED

    def _cleanup_old_messages(self):
        """Clean up old messages to maintain performance"""
        if len(self.messages) <= self.max_messages:
            return

        # Get messages sorted by age (oldest first)
        messages_by_age = sorted(
            self.messages.items(),
            key=lambda x: x[1].created_at
        )

        # Remove oldest messages that are completed/archived
        to_remove = []
        for msg_id, managed_msg in messages_by_age:
            if (managed_msg.status in [MessageStatus.ARCHIVED, MessageStatus.EXPIRED] and
                len(to_remove) < (len(self.messages) - self.max_messages)):
                to_remove.append(msg_id)

        # Remove selected messages
        for msg_id in to_remove:
            self._remove_message(msg_id)

    def _remove_message(self, message_id: str):
        """Remove message from inbox completely"""
        if message_id not in self.messages:
            return

        managed_msg = self.messages[message_id]

        # Remove from category
        category = managed_msg.inbox_category
        if message_id in self.categories[category]:
            self.categories[category].remove(message_id)

        # Remove from messages
        del self.messages[message_id]


class MessageLifecycleManager:
    """Manages message lifecycles across all agents"""

    def __init__(self):
        self.inboxes: Dict[str, IntelligentInbox] = {}
        self.lifecycle_rules: List[Dict] = []
        self.processing_enabled = True

        # Background processing thread
        self.lifecycle_thread = threading.Thread(target=self._process_lifecycles, daemon=True)
        self.lifecycle_thread.start()

    def get_inbox(self, agent_id: str) -> IntelligentInbox:
        """Get or create inbox for agent"""
        if agent_id not in self.inboxes:
            self.inboxes[agent_id] = IntelligentInbox(agent_id)
        return self.inboxes[agent_id]

    def add_message(self, agent_id: str, message: AgentMessage) -> ManagedMessage:
        """Add message to agent's inbox"""
        inbox = self.get_inbox(agent_id)
        return inbox.add_message(message)

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get system-wide message statistics"""
        total_messages = 0
        total_overdue = 0
        agent_stats = {}

        for agent_id, inbox in self.inboxes.items():
            stats = inbox.get_inbox_statistics()
            agent_stats[agent_id] = stats
            total_messages += stats['total_messages']
            total_overdue += stats['overdue_messages']

        return {
            'total_agents': len(self.inboxes),
            'total_messages': total_messages,
            'total_overdue': total_overdue,
            'agent_statistics': agent_stats
        }

    def process_auto_archiving(self) -> Dict[str, int]:
        """Process auto-archiving for all inboxes"""
        archived_counts = {}

        for agent_id, inbox in self.inboxes.items():
            eligible = inbox.auto_archive_eligible()
            archived_count = 0

            for msg_id in eligible:
                if inbox.update_message_status(msg_id, MessageStatus.ARCHIVED):
                    archived_count += 1

            archived_counts[agent_id] = archived_count

        return archived_counts

    def _process_lifecycles(self):
        """Background processing for message lifecycles"""
        while self.processing_enabled:
            try:
                # Process auto-archiving every hour
                self.process_auto_archiving()

                # Process expiration checks
                self._process_expirations()

                # Process reminders
                self._process_reminders()

                time.sleep(3600)  # Check every hour

            except Exception as e:
                print(f"Lifecycle processing error: {e}")
                time.sleep(1800)  # Wait 30 minutes on error

    def _process_expirations(self):
        """Process message expirations"""
        now = datetime.now()

        for inbox in self.inboxes.values():
            for msg_id, managed_msg in inbox.messages.items():
                if (managed_msg.expires_at and
                    now > managed_msg.expires_at and
                    managed_msg.status not in [MessageStatus.ARCHIVED, MessageStatus.EXPIRED]):
                    inbox.update_message_status(msg_id, MessageStatus.EXPIRED)

    def _process_reminders(self):
        """Process reminder notifications"""
        for agent_id, inbox in self.inboxes.items():
            overdue_messages = inbox.get_overdue_messages()

            for managed_msg in overdue_messages:
                if not managed_msg.reminder_sent:
                    # Send reminder notification
                    print(f"⏰ Reminder: {agent_id} has overdue message {managed_msg.message.message_id[:8]}")
                    managed_msg.reminder_sent = True
                    managed_msg.metrics.reminder_count += 1

    def shutdown(self):
        """Shutdown lifecycle manager"""
        self.processing_enabled = False
        if self.lifecycle_thread.is_alive():
            self.lifecycle_thread.join(timeout=5)


# Global lifecycle manager instance
_lifecycle_manager = None


def get_lifecycle_manager() -> MessageLifecycleManager:
    """Get global lifecycle manager instance"""
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = MessageLifecycleManager()
    return _lifecycle_manager


def get_agent_inbox(agent_id: str) -> IntelligentInbox:
    """Get intelligent inbox for agent"""
    return get_lifecycle_manager().get_inbox(agent_id)


if __name__ == "__main__":
    # Test the intelligent inbox system
    from shared_state.models import MessageType as OriginalMessageType

    # Create test manager
    manager = MessageLifecycleManager()

    # Create test messages
    test_messages = [
        AgentMessage(
            sender_id="supervisor",
            recipient_id="backend-api",
            content="Deploy the authentication module immediately!",
            subject="URGENT: Deploy Auth Module",
            priority=MessagePriority.URGENT,
            message_type=OriginalMessageType.DIRECT
        ),
        AgentMessage(
            sender_id="frontend-ui",
            recipient_id="backend-api",
            content="How do I integrate the new user API?",
            subject="API Integration Question",
            priority=MessagePriority.NORMAL,
            message_type=OriginalMessageType.DIRECT
        ),
        AgentMessage(
            sender_id="database",
            recipient_id="backend-api",
            content="Migration completed successfully.",
            subject="Migration Status",
            priority=MessagePriority.LOW,
            message_type=OriginalMessageType.DIRECT
        )
    ]

    # Add messages to inbox
    inbox = manager.get_inbox("backend-api")

    for message in test_messages:
        managed_msg = manager.add_message("backend-api", message)
        print(f"📧 Added: {message.subject}")
        print(f"   Category: {managed_msg.inbox_category.value}")
        print(f"   Status: {managed_msg.status.value}")
        print(f"   Priority Score: {inbox._get_priority_score(managed_msg):.2f}")
        print()

    # Test priority inbox
    priority_messages = inbox.get_priority_inbox(5)
    print(f"🎯 Priority Inbox ({len(priority_messages)} messages):")
    for msg in priority_messages:
        print(f"   {msg.message.subject} (Score: {inbox._get_priority_score(msg):.2f})")

    # Test statistics
    stats = inbox.get_inbox_statistics()
    print(f"\n📊 Inbox Statistics:")
    print(f"   Total Messages: {stats['total_messages']}")
    print(f"   Categories: {stats['category_distribution']}")
    print(f"   Completion Rate: {stats['completion_rate']:.1f}%")

    manager.shutdown()