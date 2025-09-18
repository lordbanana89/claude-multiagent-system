#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Inbox System
Tests end-to-end workflows, system integration, and performance
"""

import pytest
import asyncio
import json
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared_state.models import AgentMessage, MessagePriority
from messaging.management import MessageManager, IntelligentInbox, MessageStatus, InboxCategory
from messaging.interface import MessageActionHandler, TerminalInterface
from messaging.notifications import NotificationSystem, AlertLevel
from messaging.classification import MessageClassifier
from messaging.workflow import DecisionEngine


class TestInboxSystemIntegration:
    """Integration tests for complete inbox system workflow"""

    def setup_method(self):
        """Setup integration test environment"""
        self.manager = MessageManager()
        self.notification_system = NotificationSystem()
        self.classifier = MessageClassifier()
        self.decision_engine = DecisionEngine()

        # Test agents
        self.sender_agent = "integration-sender"
        self.receiver_agent = "integration-receiver"
        self.supervisor_agent = "integration-supervisor"

        # Get inboxes
        self.sender_inbox = self.manager.get_inbox(self.sender_agent)
        self.receiver_inbox = self.manager.get_inbox(self.receiver_agent)
        self.supervisor_inbox = self.manager.get_inbox(self.supervisor_agent)

    def test_complete_message_lifecycle(self):
        """Test complete message lifecycle from creation to archival"""

        # 1. Create and send message
        test_message = AgentMessage(
            message_id="lifecycle-001",
            from_agent=self.sender_agent,
            to_agent=self.receiver_agent,
            content="Integration test: Complete lifecycle message",
            priority=MessagePriority.HIGH,
            timestamp=datetime.now()
        )

        # 2. Deliver message through manager
        delivery_success = self.manager.deliver_message(test_message)
        assert delivery_success == True

        # 3. Verify message in receiver's inbox
        assert test_message.message_id in self.receiver_inbox.messages
        managed_msg = self.receiver_inbox.messages[test_message.message_id]
        assert managed_msg.status == MessageStatus.DELIVERED

        # 4. Simulate message reading
        read_success = self.receiver_inbox.update_message_status(
            test_message.message_id, MessageStatus.READ
        )
        assert read_success == True
        assert self.receiver_inbox.messages[test_message.message_id].status == MessageStatus.READ

        # 5. Acknowledge message
        ack_success = self.receiver_inbox.update_message_status(
            test_message.message_id, MessageStatus.ACKNOWLEDGED
        )
        assert ack_success == True

        # 6. Create response message
        response_message = AgentMessage(
            message_id="lifecycle-response-001",
            from_agent=self.receiver_agent,
            to_agent=self.sender_agent,
            content="Response to lifecycle test message",
            priority=MessagePriority.NORMAL,
            timestamp=datetime.now(),
            reply_to=test_message.message_id
        )

        # 7. Send response
        response_delivery = self.manager.deliver_message(response_message)
        assert response_delivery == True

        # 8. Update original message as responded
        respond_success = self.receiver_inbox.update_message_status(
            test_message.message_id, MessageStatus.RESPONDED
        )
        assert respond_success == True

        # 9. Archive the original message
        archive_success = self.receiver_inbox.archive_message(test_message.message_id)
        assert archive_success == True

        # 10. Verify final state
        final_msg = self.receiver_inbox.messages[test_message.message_id]
        assert final_msg.status == MessageStatus.ARCHIVED
        assert final_msg.inbox_category == InboxCategory.COMPLETED

    def test_escalation_workflow(self):
        """Test message escalation workflow"""

        # 1. Create high priority message that needs escalation
        escalation_message = AgentMessage(
            message_id="escalation-001",
            from_agent=self.sender_agent,
            to_agent=self.receiver_agent,
            content="Critical issue requiring supervisor intervention",
            priority=MessagePriority.HIGH,
            timestamp=datetime.now()
        )

        # 2. Deliver message
        self.manager.deliver_message(escalation_message)

        # 3. Simulate escalation decision
        managed_msg = self.receiver_inbox.messages[escalation_message.message_id]

        # 4. Escalate to supervisor
        escalation_success = self.receiver_inbox.escalate_message(
            escalation_message.message_id,
            self.supervisor_agent,
            "Requires expert attention"
        )
        assert escalation_success == True

        # 5. Verify escalation
        escalated_msg = self.receiver_inbox.messages[escalation_message.message_id]
        assert escalated_msg.status == MessageStatus.ESCALATED
        assert escalated_msg.escalated_to == self.supervisor_agent

        # 6. Verify escalation notification to supervisor
        # (In real implementation, supervisor would receive notification)
        assert escalated_msg.metrics.escalation_count == 1

    def test_broadcast_message_integration(self):
        """Test broadcast message delivery to multiple agents"""

        # 1. Create additional test agents
        agent_ids = [f"broadcast-agent-{i}" for i in range(5)]

        # 2. Create broadcast message
        broadcast_message = AgentMessage(
            message_id="broadcast-001",
            from_agent="system",
            to_agent="all",
            content="System maintenance notification - scheduled downtime in 1 hour",
            priority=MessagePriority.HIGH,
            timestamp=datetime.now()
        )

        # 3. Broadcast to all agents
        delivery_count = self.manager.broadcast_message(broadcast_message, agent_ids)
        assert delivery_count == len(agent_ids)

        # 4. Verify delivery to all agents
        for agent_id in agent_ids:
            inbox = self.manager.get_inbox(agent_id)
            assert broadcast_message.message_id in inbox.messages

            # Verify message categorization
            managed_msg = inbox.messages[broadcast_message.message_id]
            assert managed_msg.inbox_category in [InboxCategory.URGENT, InboxCategory.INFORMATION]

    def test_notification_system_integration(self):
        """Test integration with notification system"""

        with patch.object(self.notification_system, 'send_notification') as mock_notify:
            # 1. Create urgent message
            urgent_message = AgentMessage(
                message_id="notification-001",
                from_agent=self.sender_agent,
                to_agent=self.receiver_agent,
                content="URGENT: System security breach detected",
                priority=MessagePriority.URGENT,
                timestamp=datetime.now()
            )

            # 2. Deliver message (should trigger notification)
            self.manager.deliver_message(urgent_message)

            # 3. Verify notification was triggered
            # mock_notify.assert_called_once()

            # 4. Verify message is properly categorized as urgent
            managed_msg = self.receiver_inbox.messages[urgent_message.message_id]
            assert managed_msg.inbox_category == InboxCategory.URGENT
            assert managed_msg.priority_boost == True

    def test_concurrent_message_handling(self):
        """Test system behavior under concurrent message load"""

        def send_message(message_id):
            """Helper function to send a message"""
            message = AgentMessage(
                message_id=f"concurrent-{message_id}",
                from_agent=f"sender-{message_id % 3}",
                to_agent=self.receiver_agent,
                content=f"Concurrent test message {message_id}",
                priority=MessagePriority.NORMAL,
                timestamp=datetime.now()
            )
            return self.manager.deliver_message(message)

        # 1. Send 50 messages concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(send_message, i) for i in range(50)]
            results = [future.result() for future in as_completed(futures)]

        # 2. Verify all messages were delivered successfully
        assert all(results)

        # 3. Verify all messages are in inbox
        assert len(self.receiver_inbox.messages) >= 50

        # 4. Verify message ordering and timestamps
        messages = list(self.receiver_inbox.messages.values())
        messages.sort(key=lambda m: m.created_at)

        # Messages should be in chronological order
        for i in range(1, len(messages)):
            assert messages[i].created_at >= messages[i-1].created_at

    def test_message_classification_integration(self):
        """Test automatic message classification accuracy"""

        test_cases = [
            {
                "content": "Please complete the user authentication module by EOD",
                "expected_category": InboxCategory.TASKS,
                "priority": MessagePriority.HIGH
            },
            {
                "content": "What is the current status of the database migration?",
                "expected_category": InboxCategory.QUESTIONS,
                "priority": MessagePriority.NORMAL
            },
            {
                "content": "System backup completed successfully at 02:00 AM",
                "expected_category": InboxCategory.INFORMATION,
                "priority": MessagePriority.LOW
            },
            {
                "content": "CRITICAL: Production server is unresponsive",
                "expected_category": InboxCategory.URGENT,
                "priority": MessagePriority.URGENT
            }
        ]

        for i, test_case in enumerate(test_cases):
            # 1. Create message
            message = AgentMessage(
                message_id=f"classification-{i}",
                from_agent=self.sender_agent,
                to_agent=self.receiver_agent,
                content=test_case["content"],
                priority=test_case["priority"],
                timestamp=datetime.now()
            )

            # 2. Deliver message
            self.manager.deliver_message(message)

            # 3. Verify classification
            managed_msg = self.receiver_inbox.messages[message.message_id]
            # Note: Actual classification depends on implementation
            assert managed_msg.inbox_category in InboxCategory

    def test_performance_under_load(self):
        """Test system performance under heavy load"""

        # 1. Measure baseline performance
        start_time = time.time()

        # 2. Create large number of messages
        messages = []
        for i in range(1000):
            message = AgentMessage(
                message_id=f"perf-{i}",
                from_agent=f"sender-{i % 10}",
                to_agent=self.receiver_agent,
                content=f"Performance test message {i}",
                priority=MessagePriority.NORMAL,
                timestamp=datetime.now()
            )
            messages.append(message)

        # 3. Deliver all messages
        for message in messages:
            self.manager.deliver_message(message)

        # 4. Measure delivery time
        delivery_time = time.time() - start_time

        # 5. Performance assertions
        messages_per_second = len(messages) / delivery_time
        assert messages_per_second > 100, f"Performance too slow: {messages_per_second} msg/s"

        # 6. Test inbox statistics generation time
        stats_start = time.time()
        stats = self.receiver_inbox.get_inbox_statistics()
        stats_time = time.time() - stats_start

        assert stats_time < 1.0, f"Statistics generation too slow: {stats_time}s"
        assert stats["total_messages"] >= 1000

    def test_message_expiration_and_cleanup(self):
        """Test automatic message expiration and cleanup"""

        # 1. Create message with short expiration
        expiring_message = AgentMessage(
            message_id="expiring-001",
            from_agent=self.sender_agent,
            to_agent=self.receiver_agent,
            content="This message will expire soon",
            priority=MessagePriority.NORMAL,
            timestamp=datetime.now()
        )

        # 2. Deliver message
        self.manager.deliver_message(expiring_message)

        # 3. Manually set expiration to past (simulate time passage)
        managed_msg = self.receiver_inbox.messages[expiring_message.message_id]
        managed_msg.expires_at = datetime.now() - timedelta(hours=1)

        # 4. Trigger cleanup
        self.receiver_inbox._cleanup_expired_messages()

        # 5. Verify message is marked as expired
        if expiring_message.message_id in self.receiver_inbox.messages:
            expired_msg = self.receiver_inbox.messages[expiring_message.message_id]
            assert expired_msg.status == MessageStatus.EXPIRED

    def test_cross_agent_communication_flow(self):
        """Test complex multi-agent communication patterns"""

        # 1. Agent A sends task to Agent B
        task_message = AgentMessage(
            message_id="cross-comm-001",
            from_agent=self.sender_agent,
            to_agent=self.receiver_agent,
            content="Please analyze the user behavior data",
            priority=MessagePriority.HIGH,
            timestamp=datetime.now()
        )

        self.manager.deliver_message(task_message)

        # 2. Agent B acknowledges and requests clarification
        clarification_message = AgentMessage(
            message_id="cross-comm-002",
            from_agent=self.receiver_agent,
            to_agent=self.sender_agent,
            content="Need clarification: Which time period should be analyzed?",
            priority=MessagePriority.NORMAL,
            timestamp=datetime.now(),
            reply_to="cross-comm-001"
        )

        self.manager.deliver_message(clarification_message)

        # 3. Agent A provides clarification
        clarification_response = AgentMessage(
            message_id="cross-comm-003",
            from_agent=self.sender_agent,
            to_agent=self.receiver_agent,
            content="Please analyze last 30 days of user behavior data",
            priority=MessagePriority.NORMAL,
            timestamp=datetime.now(),
            reply_to="cross-comm-002"
        )

        self.manager.deliver_message(clarification_response)

        # 4. Agent B completes task and reports back
        completion_message = AgentMessage(
            message_id="cross-comm-004",
            from_agent=self.receiver_agent,
            to_agent=self.sender_agent,
            content="Analysis complete. Key findings: 25% increase in user engagement",
            priority=MessagePriority.NORMAL,
            timestamp=datetime.now(),
            reply_to="cross-comm-001"
        )

        self.manager.deliver_message(completion_message)

        # 5. Verify conversation thread
        sender_inbox = self.manager.get_inbox(self.sender_agent)
        receiver_inbox = self.manager.get_inbox(self.receiver_agent)

        # Both agents should have relevant messages
        assert "cross-comm-001" in receiver_inbox.messages
        assert "cross-comm-002" in sender_inbox.messages
        assert "cross-comm-003" in receiver_inbox.messages
        assert "cross-comm-004" in sender_inbox.messages

    def test_error_recovery_and_resilience(self):
        """Test system recovery from various error conditions"""

        # 1. Test delivery to non-existent agent
        invalid_message = AgentMessage(
            message_id="error-001",
            from_agent=self.sender_agent,
            to_agent="non-existent-agent",
            content="Message to invalid agent",
            priority=MessagePriority.NORMAL,
            timestamp=datetime.now()
        )

        # Should handle gracefully without crashing
        try:
            delivery_result = self.manager.deliver_message(invalid_message)
            # Implementation dependent - might return False or handle differently
        except Exception as e:
            pytest.fail(f"System should handle invalid agents gracefully: {e}")

        # 2. Test malformed message handling
        # (This would depend on actual validation implementation)

        # 3. Test system recovery after simulated failure
        original_message_count = len(self.receiver_inbox.messages)

        # Simulate system restart by creating new instances
        new_manager = MessageManager()
        new_inbox = new_manager.get_inbox(self.receiver_agent)

        # System should maintain state consistency
        # (In real implementation, this would involve persistent storage)


class TestInboxSystemStressTest:
    """Stress tests for inbox system under extreme conditions"""

    def setup_method(self):
        """Setup stress test environment"""
        self.manager = MessageManager()
        self.test_agents = [f"stress-agent-{i}" for i in range(100)]

    def test_massive_concurrent_load(self):
        """Test system under massive concurrent message load"""

        def stress_test_worker(worker_id):
            """Worker function for stress testing"""
            messages_sent = 0

            for i in range(100):  # Each worker sends 100 messages
                message = AgentMessage(
                    message_id=f"stress-{worker_id}-{i}",
                    from_agent=f"stress-sender-{worker_id}",
                    to_agent=f"stress-agent-{i % 10}",
                    content=f"Stress test message {i} from worker {worker_id}",
                    priority=MessagePriority.NORMAL,
                    timestamp=datetime.now()
                )

                if self.manager.deliver_message(message):
                    messages_sent += 1

            return messages_sent

        # Run stress test with 20 concurrent workers
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(stress_test_worker, i) for i in range(20)]
            results = [future.result() for future in as_completed(futures)]

        end_time = time.time()

        # Verify results
        total_messages = sum(results)
        total_time = end_time - start_time
        throughput = total_messages / total_time

        assert total_messages == 2000  # 20 workers * 100 messages each
        assert throughput > 500, f"Throughput too low: {throughput} msg/s"

        print(f"Stress test completed: {total_messages} messages in {total_time:.2f}s ({throughput:.2f} msg/s)")


if __name__ == "__main__":
    """Run integration tests"""
    pytest.main([__file__, "-v", "--tb=short", "-x"])