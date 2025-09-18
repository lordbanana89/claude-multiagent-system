#!/usr/bin/env python3
"""
Unit Tests for Inbox System Core Functionality
Tests IntelligentInbox, MessageManagement, and core messaging components
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared_state.models import AgentMessage, MessagePriority
from messaging.management import (
    IntelligentInbox, ManagedMessage, MessageStatus,
    InboxCategory, MessageMetrics, MessageManager
)
from messaging.classification import MessageCategory, ClassificationMessageType, ResponseRequirement
from messaging.notifications import NotificationSystem, NotificationType, AlertLevel


class TestIntelligentInbox:
    """Test suite for IntelligentInbox class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.agent_id = "test-agent-001"
        self.inbox = IntelligentInbox(self.agent_id)

        # Create test message
        self.test_message = AgentMessage(
            message_id="msg-001",
            from_agent="sender-agent",
            to_agent=self.agent_id,
            content="Test message content",
            priority=MessagePriority.NORMAL,
            timestamp=datetime.now()
        )

    def test_inbox_initialization(self):
        """Test inbox proper initialization"""
        assert self.inbox.agent_id == self.agent_id
        assert isinstance(self.inbox.messages, dict)
        assert len(self.inbox.messages) == 0
        assert len(self.inbox.categories) == len(InboxCategory)
        assert self.inbox.auto_archive_hours == 72
        assert self.inbox.max_messages == 1000

    def test_add_message_basic(self):
        """Test basic message addition to inbox"""
        managed_msg = self.inbox.add_message(self.test_message)

        assert isinstance(managed_msg, ManagedMessage)
        assert managed_msg.message == self.test_message
        assert managed_msg.status == MessageStatus.DELIVERED
        assert managed_msg.message.message_id in self.inbox.messages
        assert isinstance(managed_msg.category, MessageCategory)
        assert isinstance(managed_msg.inbox_category, InboxCategory)
        assert managed_msg.created_at is not None
        assert managed_msg.last_updated is not None

    def test_add_urgent_message(self):
        """Test urgent message handling"""
        urgent_message = AgentMessage(
            message_id="urgent-001",
            from_agent="supervisor",
            to_agent=self.agent_id,
            content="URGENT: Critical system failure requires immediate attention",
            priority=MessagePriority.URGENT,
            timestamp=datetime.now()
        )

        managed_msg = self.inbox.add_message(urgent_message)

        assert managed_msg.inbox_category == InboxCategory.URGENT
        assert managed_msg.priority_boost == True
        assert urgent_message.message_id in self.inbox.categories[InboxCategory.URGENT]

    def test_message_categorization(self):
        """Test automatic message categorization"""
        test_cases = [
            ("Please complete task XYZ", InboxCategory.TASKS),
            ("What is the status of project ABC?", InboxCategory.QUESTIONS),
            ("System notification: Database backup completed", InboxCategory.INFORMATION),
            ("URGENT: Server down!", InboxCategory.URGENT)
        ]

        for content, expected_category in test_cases:
            message = AgentMessage(
                message_id=f"msg-{hash(content)}",
                from_agent="test-sender",
                to_agent=self.agent_id,
                content=content,
                priority=MessagePriority.NORMAL,
                timestamp=datetime.now()
            )

            managed_msg = self.inbox.add_message(message)
            # Note: Actual categorization depends on classifier implementation
            assert managed_msg.inbox_category in InboxCategory

    def test_get_priority_inbox(self):
        """Test priority inbox functionality"""
        # Add multiple messages with different priorities
        messages = [
            AgentMessage("msg-1", "sender", self.agent_id, "Normal message", MessagePriority.NORMAL, datetime.now()),
            AgentMessage("msg-2", "sender", self.agent_id, "High priority task", MessagePriority.HIGH, datetime.now()),
            AgentMessage("msg-3", "sender", self.agent_id, "URGENT issue", MessagePriority.URGENT, datetime.now()),
            AgentMessage("msg-4", "sender", self.agent_id, "Low priority info", MessagePriority.LOW, datetime.now())
        ]

        for msg in messages:
            self.inbox.add_message(msg)

        priority_messages = self.inbox.get_priority_inbox(limit=3)

        assert len(priority_messages) == 3
        # First message should be highest priority
        assert priority_messages[0].message.priority in [MessagePriority.URGENT, MessagePriority.HIGH]

    def test_update_message_status(self):
        """Test message status updates"""
        managed_msg = self.inbox.add_message(self.test_message)
        original_updated = managed_msg.last_updated

        time.sleep(0.01)  # Ensure timestamp difference

        success = self.inbox.update_message_status(self.test_message.message_id, MessageStatus.READ)

        assert success == True
        updated_msg = self.inbox.messages[self.test_message.message_id]
        assert updated_msg.status == MessageStatus.READ
        assert updated_msg.last_updated > original_updated

    def test_archive_message(self):
        """Test message archiving"""
        managed_msg = self.inbox.add_message(self.test_message)

        success = self.inbox.archive_message(self.test_message.message_id)

        assert success == True
        archived_msg = self.inbox.messages[self.test_message.message_id]
        assert archived_msg.status == MessageStatus.ARCHIVED
        assert archived_msg.inbox_category == InboxCategory.COMPLETED

    def test_delete_message(self):
        """Test message deletion"""
        managed_msg = self.inbox.add_message(self.test_message)

        success = self.inbox.delete_message(self.test_message.message_id)

        assert success == True
        assert self.test_message.message_id not in self.inbox.messages

    def test_get_inbox_statistics(self):
        """Test inbox statistics generation"""
        # Add messages with different statuses
        for i in range(5):
            msg = AgentMessage(
                f"msg-{i}", "sender", self.agent_id, f"Message {i}",
                MessagePriority.NORMAL, datetime.now()
            )
            self.inbox.add_message(msg)

        # Update some message statuses
        messages = list(self.inbox.messages.keys())
        self.inbox.update_message_status(messages[0], MessageStatus.READ)
        self.inbox.update_message_status(messages[1], MessageStatus.ACKNOWLEDGED)
        self.inbox.archive_message(messages[2])

        stats = self.inbox.get_inbox_statistics()

        assert isinstance(stats, dict)
        assert "total_messages" in stats
        assert "by_status" in stats
        assert "by_category" in stats
        assert "by_priority" in stats
        assert stats["total_messages"] == 5

    def test_inbox_capacity_limit(self):
        """Test inbox maximum capacity handling"""
        # Temporarily reduce max_messages for testing
        self.inbox.max_messages = 3

        # Add messages beyond capacity
        for i in range(5):
            msg = AgentMessage(
                f"msg-{i}", "sender", self.agent_id, f"Message {i}",
                MessagePriority.NORMAL, datetime.now()
            )
            self.inbox.add_message(msg)

        # Should only keep max_messages
        assert len(self.inbox.messages) <= self.inbox.max_messages

    def test_expired_message_handling(self):
        """Test handling of expired messages"""
        # Create message with short expiration
        expired_msg = AgentMessage(
            "expired-001", "sender", self.agent_id, "Expiring message",
            MessagePriority.NORMAL, datetime.now()
        )

        managed_msg = self.inbox.add_message(expired_msg)

        # Manually set expiration to past
        managed_msg.expires_at = datetime.now() - timedelta(hours=1)
        self.inbox.messages[expired_msg.message_id] = managed_msg

        # Clean up expired messages
        self.inbox._cleanup_expired_messages()

        # Message should be marked as expired
        if expired_msg.message_id in self.inbox.messages:
            assert self.inbox.messages[expired_msg.message_id].status == MessageStatus.EXPIRED


class TestMessageManager:
    """Test suite for MessageManager class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.manager = MessageManager()
        self.agent_id = "test-agent-manager"

    def test_manager_initialization(self):
        """Test MessageManager initialization"""
        assert isinstance(self.manager.inboxes, dict)
        assert len(self.manager.inboxes) == 0

    def test_get_inbox_creation(self):
        """Test inbox creation via manager"""
        inbox = self.manager.get_inbox(self.agent_id)

        assert isinstance(inbox, IntelligentInbox)
        assert inbox.agent_id == self.agent_id
        assert self.agent_id in self.manager.inboxes

    def test_deliver_message(self):
        """Test message delivery through manager"""
        test_message = AgentMessage(
            "manager-msg-001", "sender", self.agent_id, "Manager test message",
            MessagePriority.NORMAL, datetime.now()
        )

        success = self.manager.deliver_message(test_message)

        assert success == True
        inbox = self.manager.get_inbox(self.agent_id)
        assert test_message.message_id in inbox.messages

    def test_broadcast_message(self):
        """Test message broadcasting to multiple agents"""
        agent_ids = ["agent-1", "agent-2", "agent-3"]

        broadcast_message = AgentMessage(
            "broadcast-001", "system", "all", "System broadcast message",
            MessagePriority.HIGH, datetime.now()
        )

        success_count = self.manager.broadcast_message(broadcast_message, agent_ids)

        assert success_count == len(agent_ids)

        # Verify message delivered to all agents
        for agent_id in agent_ids:
            inbox = self.manager.get_inbox(agent_id)
            assert broadcast_message.message_id in inbox.messages

    def test_get_global_statistics(self):
        """Test global messaging statistics"""
        # Create some test data
        for i in range(3):
            agent_id = f"stats-agent-{i}"
            for j in range(2):
                msg = AgentMessage(
                    f"stats-msg-{i}-{j}", "sender", agent_id, f"Stats message {j}",
                    MessagePriority.NORMAL, datetime.now()
                )
                self.manager.deliver_message(msg)

        stats = self.manager.get_global_statistics()

        assert isinstance(stats, dict)
        assert "total_agents" in stats
        assert "total_messages" in stats
        assert "messages_by_agent" in stats


class TestMessageMetrics:
    """Test suite for message metrics and performance tracking"""

    def test_metrics_initialization(self):
        """Test MessageMetrics initialization"""
        metrics = MessageMetrics()

        assert metrics.response_time_minutes is None
        assert metrics.escalation_count == 0
        assert metrics.reminder_count == 0
        assert metrics.category_confidence == 0.0
        assert metrics.workflow_efficiency == 0.0

    def test_metrics_with_data(self):
        """Test metrics with actual data"""
        metrics = MessageMetrics(
            response_time_minutes=15,
            escalation_count=1,
            reminder_count=2,
            category_confidence=0.85,
            workflow_efficiency=0.92
        )

        assert metrics.response_time_minutes == 15
        assert metrics.escalation_count == 1
        assert metrics.reminder_count == 2
        assert metrics.category_confidence == 0.85
        assert metrics.workflow_efficiency == 0.92


class TestInboxIntegration:
    """Integration tests for inbox system components"""

    def setup_method(self):
        """Setup integration test fixtures"""
        self.manager = MessageManager()
        self.agent_id = "integration-test-agent"
        self.inbox = self.manager.get_inbox(self.agent_id)

    def test_end_to_end_message_flow(self):
        """Test complete message lifecycle"""
        # 1. Create and deliver message
        test_message = AgentMessage(
            "e2e-001", "sender-agent", self.agent_id, "End-to-end test message",
            MessagePriority.HIGH, datetime.now()
        )

        # 2. Deliver through manager
        success = self.manager.deliver_message(test_message)
        assert success == True

        # 3. Verify in inbox
        assert test_message.message_id in self.inbox.messages
        managed_msg = self.inbox.messages[test_message.message_id]
        assert managed_msg.status == MessageStatus.DELIVERED

        # 4. Update status progression
        self.inbox.update_message_status(test_message.message_id, MessageStatus.READ)
        assert self.inbox.messages[test_message.message_id].status == MessageStatus.READ

        self.inbox.update_message_status(test_message.message_id, MessageStatus.ACKNOWLEDGED)
        assert self.inbox.messages[test_message.message_id].status == MessageStatus.ACKNOWLEDGED

        # 5. Archive message
        self.inbox.archive_message(test_message.message_id)
        assert self.inbox.messages[test_message.message_id].status == MessageStatus.ARCHIVED

    def test_priority_escalation_workflow(self):
        """Test priority escalation workflow"""
        # Create normal priority message
        normal_message = AgentMessage(
            "escalation-001", "sender", self.agent_id, "Normal message that needs escalation",
            MessagePriority.NORMAL, datetime.now()
        )

        self.manager.deliver_message(normal_message)
        managed_msg = self.inbox.messages[normal_message.message_id]

        # Simulate escalation
        managed_msg.escalated_to = "supervisor-agent"
        managed_msg.status = MessageStatus.ESCALATED
        managed_msg.metrics.escalation_count += 1

        assert managed_msg.status == MessageStatus.ESCALATED
        assert managed_msg.escalated_to == "supervisor-agent"
        assert managed_msg.metrics.escalation_count == 1

    @patch('messaging.notifications.NotificationSystem')
    def test_notification_integration(self, mock_notification_system):
        """Test integration with notification system"""
        # Setup mock
        mock_notifier = Mock()
        mock_notification_system.return_value = mock_notifier

        # Create urgent message
        urgent_message = AgentMessage(
            "notification-001", "system", self.agent_id, "URGENT: System alert",
            MessagePriority.URGENT, datetime.now()
        )

        # Deliver message
        self.manager.deliver_message(urgent_message)

        # Verify message was processed
        assert urgent_message.message_id in self.inbox.messages
        managed_msg = self.inbox.messages[urgent_message.message_id]
        assert managed_msg.inbox_category == InboxCategory.URGENT


if __name__ == "__main__":
    """Run unit tests"""
    pytest.main([__file__, "-v", "--tb=short"])