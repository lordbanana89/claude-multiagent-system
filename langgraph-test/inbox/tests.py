"""
Unit and Integration Tests for Inbox Infrastructure
Comprehensive test suite for all inbox components
"""

import unittest
import sqlite3
import tempfile
import os
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from shared_state.models import AgentMessage, MessageType, MessagePriority, MessageStatus
from .storage import InboxStorage, InboxManager
from .routing import MessageRouter, RoutingRule, RoutingStrategy, FilterType, CapabilityFilter
from .auth import AuthenticationManager, AgentCredentials, Role, Permission
from .validation import MessageValidator, ValidationResult, ErrorHandler, RateLimiter


class TestInboxStorage(unittest.TestCase):
    """Test InboxStorage functionality"""

    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(delete=False)
        self.db_file.close()
        self.storage = InboxStorage(self.db_file.name)

    def tearDown(self):
        os.unlink(self.db_file.name)

    def test_store_message(self):
        """Test storing a message"""
        message = AgentMessage(
            sender_id="agent1",
            recipient_id="agent2",
            content="Test message",
            subject="Test"
        )

        result = self.storage.store_message(message)
        self.assertTrue(result)

        # Try storing same message again (should fail due to unique constraint)
        result = self.storage.store_message(message)
        self.assertFalse(result)

    def test_get_messages_for_agent(self):
        """Test retrieving messages for agent"""
        # Store test messages
        msg1 = AgentMessage(sender_id="agent1", recipient_id="agent2", content="Message 1")
        msg2 = AgentMessage(sender_id="agent3", recipient_id="agent2", content="Message 2")
        msg3 = AgentMessage(sender_id="agent1", recipient_id="agent3", content="Message 3")

        self.storage.store_message(msg1)
        self.storage.store_message(msg2)
        self.storage.store_message(msg3)

        # Get messages for agent2
        messages = self.storage.get_messages_for_agent("agent2")
        self.assertEqual(len(messages), 2)

        # Get unread messages only
        unread_messages = self.storage.get_messages_for_agent("agent2", unread_only=True)
        self.assertEqual(len(unread_messages), 2)

    def test_mark_message_read(self):
        """Test marking message as read"""
        message = AgentMessage(
            sender_id="agent1",
            recipient_id="agent2",
            content="Test message"
        )
        self.storage.store_message(message)

        # Mark as read
        result = self.storage.mark_message_read(message.message_id, "agent2")
        self.assertTrue(result)

        # Verify message is marked as read
        retrieved_message = self.storage.get_message_by_id(message.message_id)
        self.assertEqual(retrieved_message.status, MessageStatus.READ)
        self.assertIsNotNone(retrieved_message.read_at)

    def test_search_messages(self):
        """Test message search functionality"""
        msg1 = AgentMessage(sender_id="agent1", recipient_id="agent2", content="Hello world", subject="Greeting")
        msg2 = AgentMessage(sender_id="agent1", recipient_id="agent2", content="Goodbye", subject="Farewell")
        msg3 = AgentMessage(sender_id="agent1", recipient_id="agent2", content="Python code", subject="Programming")

        self.storage.store_message(msg1)
        self.storage.store_message(msg2)
        self.storage.store_message(msg3)

        # Search by content
        results = self.storage.search_messages("agent2", "Hello")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Hello world")

        # Search by subject
        results = self.storage.search_messages("agent2", "Programming")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].subject, "Programming")

    def test_cleanup_old_messages(self):
        """Test cleaning up old messages"""
        # Create old message
        old_message = AgentMessage(
            sender_id="agent1",
            recipient_id="agent2",
            content="Old message"
        )
        old_message.timestamp = datetime.now() - timedelta(days=40)
        self.storage.store_message(old_message)

        # Create recent message
        recent_message = AgentMessage(
            sender_id="agent1",
            recipient_id="agent2",
            content="Recent message"
        )
        self.storage.store_message(recent_message)

        # Cleanup messages older than 30 days
        deleted_count = self.storage.cleanup_old_messages(30)
        self.assertEqual(deleted_count, 1)

        # Verify only recent message remains
        messages = self.storage.get_messages_for_agent("agent2")
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].content, "Recent message")


class TestMessageRouter(unittest.TestCase):
    """Test MessageRouter functionality"""

    def setUp(self):
        self.router = MessageRouter()

    def test_direct_routing(self):
        """Test direct message routing"""
        message = AgentMessage(
            sender_id="agent1",
            recipient_id="agent2",
            content="Direct message",
            message_type=MessageType.DIRECT
        )

        available_agents = ["agent1", "agent2", "agent3"]
        result = self.router.route_message(message, available_agents)

        self.assertEqual(result, ["agent2"])

    def test_broadcast_routing(self):
        """Test broadcast message routing"""
        message = AgentMessage(
            sender_id="agent1",
            content="Broadcast message",
            message_type=MessageType.BROADCAST
        )

        available_agents = ["agent1", "agent2", "agent3"]
        result = self.router.route_message(message, available_agents)

        self.assertEqual(set(result), set(available_agents))

    def test_routing_rules(self):
        """Test routing rules"""
        # Add priority routing rule
        rule = RoutingRule(
            rule_id="priority_rule",
            name="Priority Routing",
            strategy=RoutingStrategy.PRIORITY,
            filter_type=FilterType.PRIORITY,
            filter_value=4,  # Urgent messages
            priority=100
        )
        self.router.add_routing_rule(rule)

        # Create urgent message
        urgent_message = AgentMessage(
            sender_id="agent1",
            content="Urgent message",
            priority=MessagePriority.URGENT
        )

        available_agents = ["agent1", "agent2", "agent3"]
        agent_info = {
            "agent1": {"current_load": 0.1},
            "agent2": {"current_load": 0.5},
            "agent3": {"current_load": 0.3}
        }

        result = self.router.route_message(urgent_message, available_agents, agent_info)

        # Should route to top 3 least loaded agents
        self.assertLessEqual(len(result), 3)
        self.assertIn("agent1", result)  # Least loaded

    def test_capability_filter(self):
        """Test capability-based filtering"""
        capability_filter = CapabilityFilter(["python", "api"])
        self.router.add_filter("capability", capability_filter)

        message = AgentMessage(sender_id="agent1", content="Test message")
        available_agents = ["agent1", "agent2", "agent3"]
        agent_info = {
            "agent1": {"capabilities": ["python", "javascript"]},
            "agent2": {"capabilities": ["python", "api", "database"]},
            "agent3": {"capabilities": ["frontend", "css"]}
        }

        filtered_agents = capability_filter.apply(message, available_agents, agent_info)
        self.assertEqual(filtered_agents, ["agent2"])  # Only agent2 has both capabilities


class TestAuthenticationManager(unittest.TestCase):
    """Test AuthenticationManager functionality"""

    def setUp(self):
        self.auth_manager = AuthenticationManager("test-secret-key")

    def test_register_agent(self):
        """Test agent registration"""
        agent = self.auth_manager.register_agent(
            agent_id="test_agent",
            agent_name="Test Agent",
            role=Role.AGENT
        )

        self.assertEqual(agent.agent_id, "test_agent")
        self.assertEqual(agent.role, Role.AGENT)
        self.assertTrue(agent.has_permission(Permission.READ_OWN_MESSAGES))

    def test_generate_and_verify_jwt_token(self):
        """Test JWT token generation and verification"""
        # Register agent
        self.auth_manager.register_agent("test_agent", "Test Agent", Role.AGENT)

        # Generate token
        token = self.auth_manager.generate_jwt_token("test_agent")
        self.assertIsInstance(token, str)

        # Verify token
        agent = self.auth_manager.verify_jwt_token(token)
        self.assertIsNotNone(agent)
        self.assertEqual(agent.agent_id, "test_agent")

    def test_api_key_authentication(self):
        """Test API key authentication"""
        # Register agent
        self.auth_manager.register_agent("test_agent", "Test Agent", Role.AGENT)

        # Generate API key
        api_key = self.auth_manager.generate_api_key("test_agent")
        self.assertIsInstance(api_key, str)
        self.assertTrue(api_key.startswith("ak_"))

        # Authenticate with API key
        agent = self.auth_manager.authenticate_with_api_key(api_key)
        self.assertIsNotNone(agent)
        self.assertEqual(agent.agent_id, "test_agent")

    def test_permission_checking(self):
        """Test permission checking"""
        # Register agent with specific role
        agent = self.auth_manager.register_agent(
            "admin_agent",
            "Admin Agent",
            Role.ADMIN
        )

        self.assertTrue(agent.has_permission(Permission.READ_ALL_MESSAGES))
        self.assertTrue(agent.has_permission(Permission.ADMIN_CLEANUP))

        # Register regular agent
        regular_agent = self.auth_manager.register_agent(
            "regular_agent",
            "Regular Agent",
            Role.AGENT
        )

        self.assertFalse(regular_agent.has_permission(Permission.READ_ALL_MESSAGES))
        self.assertTrue(regular_agent.has_permission(Permission.READ_OWN_MESSAGES))


class TestMessageValidator(unittest.TestCase):
    """Test MessageValidator functionality"""

    def test_validate_message_content(self):
        """Test message content validation"""
        # Valid message
        valid_data = {
            "recipient_id": "agent2",
            "content": "Hello world",
            "subject": "Greeting",
            "priority": 2
        }

        result = MessageValidator.validate_message_content(valid_data)
        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors), 0)

        # Invalid message - empty content
        invalid_data = {
            "recipient_id": "agent2",
            "content": "",
            "subject": "Test"
        }

        result = MessageValidator.validate_message_content(invalid_data)
        self.assertFalse(result.valid)
        self.assertTrue(any("content cannot be empty" in error.message for error in result.errors))

    def test_content_security_validation(self):
        """Test content security validation"""
        # Malicious content
        malicious_data = {
            "recipient_id": "agent2",
            "content": "<script>alert('xss')</script>",
            "subject": "Test"
        }

        result = MessageValidator.validate_message_content(malicious_data)
        self.assertFalse(result.valid)
        self.assertTrue(any("malicious code" in error.message for error in result.errors))

    def test_validate_search_query(self):
        """Test search query validation"""
        # Valid query
        result = MessageValidator.validate_search_query("hello world")
        self.assertTrue(result.valid)

        # Empty query
        result = MessageValidator.validate_search_query("")
        self.assertFalse(result.valid)

        # Query with SQL injection attempt
        result = MessageValidator.validate_search_query("hello'; DROP TABLE messages; --")
        self.assertTrue(result.valid)  # Should be valid but with warnings
        self.assertTrue(len(result.warnings) > 0)

    def test_validate_pagination(self):
        """Test pagination validation"""
        # Valid pagination
        result = MessageValidator.validate_pagination(50, 0)
        self.assertTrue(result.valid)
        self.assertEqual(result.sanitized_data['limit'], 50)
        self.assertEqual(result.sanitized_data['offset'], 0)

        # Invalid limit
        result = MessageValidator.validate_pagination(-1, 0)
        self.assertFalse(result.valid)

        # Limit too high (should be capped)
        result = MessageValidator.validate_pagination(2000, 0)
        self.assertTrue(result.valid)
        self.assertEqual(result.sanitized_data['limit'], 1000)
        self.assertTrue(len(result.warnings) > 0)


class TestRateLimiter(unittest.TestCase):
    """Test RateLimiter functionality"""

    def setUp(self):
        self.rate_limiter = RateLimiter()

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        agent_id = "test_agent"
        max_requests = 5
        window_seconds = 60

        # Should allow first 5 requests
        for i in range(max_requests):
            allowed = self.rate_limiter.is_allowed(agent_id, max_requests, window_seconds)
            self.assertTrue(allowed, f"Request {i+1} should be allowed")

        # 6th request should be denied
        allowed = self.rate_limiter.is_allowed(agent_id, max_requests, window_seconds)
        self.assertFalse(allowed)

    def test_remaining_requests(self):
        """Test remaining requests calculation"""
        agent_id = "test_agent"
        max_requests = 10
        window_seconds = 60

        # Initially should have all requests available
        remaining = self.rate_limiter.get_remaining_requests(agent_id, max_requests, window_seconds)
        self.assertEqual(remaining, max_requests)

        # After making some requests
        for i in range(3):
            self.rate_limiter.is_allowed(agent_id, max_requests, window_seconds)

        remaining = self.rate_limiter.get_remaining_requests(agent_id, max_requests, window_seconds)
        self.assertEqual(remaining, max_requests - 3)


class TestInboxManager(unittest.TestCase):
    """Test InboxManager integration"""

    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(delete=False)
        self.db_file.close()
        self.storage = InboxStorage(self.db_file.name)
        self.manager = InboxManager(self.storage)

    def tearDown(self):
        os.unlink(self.db_file.name)

    def test_send_and_retrieve_message(self):
        """Test sending and retrieving messages through manager"""
        # Send message
        message = self.manager.send_message(
            sender_id="agent1",
            recipient_id="agent2",
            content="Test message",
            subject="Test"
        )

        self.assertIsNotNone(message.message_id)

        # Get inbox
        inbox = self.manager.get_inbox("agent2")
        self.assertEqual(inbox['unread_count'], 1)
        self.assertEqual(len(inbox['messages']), 1)
        self.assertEqual(inbox['messages'][0].content, "Test message")

    def test_broadcast_message(self):
        """Test broadcast messaging"""
        recipients = ["agent2", "agent3", "agent4"]
        messages = self.manager.broadcast_message(
            sender_id="agent1",
            content="Broadcast test",
            recipients=recipients
        )

        self.assertEqual(len(messages), 3)

        # Check each recipient received the message
        for recipient in recipients:
            inbox = self.manager.get_inbox(recipient)
            self.assertEqual(inbox['unread_count'], 1)

    def test_mark_as_read(self):
        """Test marking messages as read"""
        # Send message
        message = self.manager.send_message(
            sender_id="agent1",
            recipient_id="agent2",
            content="Test message"
        )

        # Mark as read
        result = self.manager.mark_as_read(message.message_id, "agent2")
        self.assertTrue(result)

        # Check unread count
        inbox = self.manager.get_inbox("agent2")
        self.assertEqual(inbox['unread_count'], 0)


if __name__ == "__main__":
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestInboxStorage,
        TestMessageRouter,
        TestAuthenticationManager,
        TestMessageValidator,
        TestRateLimiter,
        TestInboxManager
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Print summary
    print(f"\n{'='*50}")
    print(f"Test Results Summary")
    print(f"{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    if result.failures:
        print(f"\nFailures:")
        for test, failure in result.failures:
            print(f"- {test}: {failure}")

    if result.errors:
        print(f"\nErrors:")
        for test, error in result.errors:
            print(f"- {test}: {error}")

    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)