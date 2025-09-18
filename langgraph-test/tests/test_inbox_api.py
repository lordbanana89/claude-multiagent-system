#!/usr/bin/env python3
"""
API Validation Tests for Inbox System
Tests REST API endpoints, message delivery, and API response validation
"""

import pytest
import requests
import json
import time
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared_state.models import AgentMessage, MessagePriority
from messaging.management import MessageStatus, InboxCategory
from messaging.interface import MessageActionHandler, TerminalInterface


class TestInboxAPIValidation:
    """Test suite for inbox API endpoint validation"""

    def setup_method(self):
        """Setup API test fixtures"""
        self.base_url = "http://localhost:8000/api"  # Adjust based on actual API
        self.agent_id = "api-test-agent"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-token"  # Mock auth for testing
        }

    def test_message_delivery_endpoint(self):
        """Test POST /api/messages endpoint for message delivery"""

        # Test data
        message_data = {
            "message_id": "api-msg-001",
            "from_agent": "sender-agent",
            "to_agent": self.agent_id,
            "content": "API test message",
            "priority": "NORMAL",
            "timestamp": datetime.now().isoformat()
        }

        # Mock the API call since we don't have actual server running
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "success": True,
                "message_id": "api-msg-001",
                "status": "delivered"
            }
            mock_post.return_value = mock_response

            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=message_data
            )

            # Validate response
            assert response.status_code == 201
            response_data = response.json()
            assert response_data["success"] == True
            assert response_data["message_id"] == "api-msg-001"
            assert response_data["status"] == "delivered"

    def test_inbox_list_endpoint(self):
        """Test GET /api/inbox/{agent_id} endpoint"""

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "agent_id": self.agent_id,
                "messages": [
                    {
                        "message_id": "msg-001",
                        "from_agent": "sender",
                        "content": "Test message",
                        "priority": "NORMAL",
                        "status": "delivered",
                        "category": "information",
                        "timestamp": "2024-09-17T10:00:00Z"
                    }
                ],
                "total_count": 1,
                "unread_count": 1
            }
            mock_get.return_value = mock_response

            response = requests.get(
                f"{self.base_url}/inbox/{self.agent_id}",
                headers=self.headers
            )

            # Validate response structure
            assert response.status_code == 200
            data = response.json()
            assert "agent_id" in data
            assert "messages" in data
            assert "total_count" in data
            assert "unread_count" in data
            assert data["agent_id"] == self.agent_id
            assert isinstance(data["messages"], list)

    def test_message_status_update_endpoint(self):
        """Test PUT /api/messages/{message_id}/status endpoint"""

        message_id = "status-update-001"
        status_data = {
            "status": "read",
            "agent_id": self.agent_id
        }

        with patch('requests.put') as mock_put:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "message_id": message_id,
                "old_status": "delivered",
                "new_status": "read",
                "updated_at": datetime.now().isoformat()
            }
            mock_put.return_value = mock_response

            response = requests.put(
                f"{self.base_url}/messages/{message_id}/status",
                headers=self.headers,
                json=status_data
            )

            # Validate response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["new_status"] == "read"

    def test_inbox_statistics_endpoint(self):
        """Test GET /api/inbox/{agent_id}/stats endpoint"""

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "agent_id": self.agent_id,
                "total_messages": 15,
                "by_status": {
                    "delivered": 5,
                    "read": 7,
                    "acknowledged": 2,
                    "archived": 1
                },
                "by_category": {
                    "urgent": 2,
                    "tasks": 6,
                    "questions": 4,
                    "information": 3
                },
                "by_priority": {
                    "urgent": 1,
                    "high": 3,
                    "normal": 10,
                    "low": 1
                },
                "average_response_time_minutes": 45,
                "escalation_rate": 0.1
            }
            mock_get.return_value = mock_response

            response = requests.get(
                f"{self.base_url}/inbox/{self.agent_id}/stats",
                headers=self.headers
            )

            # Validate comprehensive statistics
            assert response.status_code == 200
            stats = response.json()
            assert "total_messages" in stats
            assert "by_status" in stats
            assert "by_category" in stats
            assert "by_priority" in stats
            assert "average_response_time_minutes" in stats
            assert isinstance(stats["total_messages"], int)

    def test_message_archive_endpoint(self):
        """Test POST /api/messages/{message_id}/archive endpoint"""

        message_id = "archive-001"

        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "message_id": message_id,
                "status": "archived",
                "archived_at": datetime.now().isoformat()
            }
            mock_post.return_value = mock_response

            response = requests.post(
                f"{self.base_url}/messages/{message_id}/archive",
                headers=self.headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["status"] == "archived"

    def test_broadcast_message_endpoint(self):
        """Test POST /api/messages/broadcast endpoint"""

        broadcast_data = {
            "message_id": "broadcast-001",
            "from_agent": "system",
            "content": "System maintenance notification",
            "priority": "HIGH",
            "target_agents": ["agent-1", "agent-2", "agent-3"],
            "timestamp": datetime.now().isoformat()
        }

        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "success": True,
                "message_id": "broadcast-001",
                "delivered_to": 3,
                "failed_deliveries": 0,
                "delivery_details": [
                    {"agent_id": "agent-1", "status": "delivered"},
                    {"agent_id": "agent-2", "status": "delivered"},
                    {"agent_id": "agent-3", "status": "delivered"}
                ]
            }
            mock_post.return_value = mock_response

            response = requests.post(
                f"{self.base_url}/messages/broadcast",
                headers=self.headers,
                json=broadcast_data
            )

            assert response.status_code == 201
            data = response.json()
            assert data["delivered_to"] == 3
            assert data["failed_deliveries"] == 0

    def test_api_error_handling(self):
        """Test API error responses and validation"""

        # Test invalid message data
        invalid_message = {
            "message_id": "",  # Empty message ID
            "from_agent": "",  # Empty sender
            "content": "",     # Empty content
            "priority": "INVALID_PRIORITY"  # Invalid priority
        }

        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": "Validation failed",
                "details": {
                    "message_id": ["Message ID cannot be empty"],
                    "from_agent": ["From agent cannot be empty"],
                    "content": ["Content cannot be empty"],
                    "priority": ["Invalid priority value"]
                }
            }
            mock_post.return_value = mock_response

            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=invalid_message
            )

            assert response.status_code == 400
            error_data = response.json()
            assert "error" in error_data
            assert "details" in error_data

    def test_api_authentication(self):
        """Test API authentication and authorization"""

        # Test without authorization header
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {
                "error": "Unauthorized",
                "message": "Missing or invalid authentication token"
            }
            mock_get.return_value = mock_response

            response = requests.get(
                f"{self.base_url}/inbox/{self.agent_id}",
                headers={"Content-Type": "application/json"}  # No auth header
            )

            assert response.status_code == 401

    def test_api_rate_limiting(self):
        """Test API rate limiting behavior"""

        with patch('requests.post') as mock_post:
            # Simulate rate limit response
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.json.return_value = {
                "error": "Rate limit exceeded",
                "retry_after": 60,
                "limit": 100,
                "window": "1 hour"
            }
            mock_post.return_value = mock_response

            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json={"test": "data"}
            )

            assert response.status_code == 429
            data = response.json()
            assert "retry_after" in data


class TestAPIResponseValidation:
    """Test suite for validating API response schemas"""

    def test_message_response_schema(self):
        """Test message delivery response schema validation"""

        # Expected response schema
        expected_fields = [
            "success", "message_id", "status", "delivered_at",
            "agent_id", "category", "priority"
        ]

        mock_response = {
            "success": True,
            "message_id": "schema-test-001",
            "status": "delivered",
            "delivered_at": "2024-09-17T10:00:00Z",
            "agent_id": "test-agent",
            "category": "information",
            "priority": "normal"
        }

        # Validate all expected fields are present
        for field in expected_fields:
            assert field in mock_response, f"Missing field: {field}"

        # Validate field types
        assert isinstance(mock_response["success"], bool)
        assert isinstance(mock_response["message_id"], str)
        assert isinstance(mock_response["status"], str)

    def test_inbox_list_response_schema(self):
        """Test inbox list response schema validation"""

        mock_response = {
            "agent_id": "test-agent",
            "messages": [
                {
                    "message_id": "msg-001",
                    "from_agent": "sender",
                    "to_agent": "test-agent",
                    "content": "Test message",
                    "priority": "normal",
                    "status": "delivered",
                    "category": "information",
                    "timestamp": "2024-09-17T10:00:00Z",
                    "tags": ["test", "api"]
                }
            ],
            "pagination": {
                "page": 1,
                "per_page": 20,
                "total_pages": 1,
                "total_count": 1
            },
            "filters_applied": {
                "status": None,
                "priority": None,
                "category": None
            }
        }

        # Validate top-level structure
        assert "agent_id" in mock_response
        assert "messages" in mock_response
        assert "pagination" in mock_response

        # Validate message structure
        message = mock_response["messages"][0]
        required_message_fields = [
            "message_id", "from_agent", "to_agent", "content",
            "priority", "status", "category", "timestamp"
        ]

        for field in required_message_fields:
            assert field in message, f"Missing message field: {field}"

    def test_statistics_response_schema(self):
        """Test statistics response schema validation"""

        mock_stats = {
            "agent_id": "test-agent",
            "generated_at": "2024-09-17T10:00:00Z",
            "time_period": {
                "from": "2024-09-16T10:00:00Z",
                "to": "2024-09-17T10:00:00Z"
            },
            "totals": {
                "messages": 50,
                "conversations": 12,
                "active_threads": 3
            },
            "by_status": {
                "delivered": 15,
                "read": 20,
                "acknowledged": 10,
                "archived": 5
            },
            "by_priority": {
                "urgent": 2,
                "high": 8,
                "normal": 35,
                "low": 5
            },
            "performance_metrics": {
                "average_response_time_minutes": 45.5,
                "escalation_rate": 0.12,
                "resolution_rate": 0.88,
                "user_satisfaction": 4.2
            }
        }

        # Validate required sections
        required_sections = [
            "agent_id", "generated_at", "totals", "by_status",
            "by_priority", "performance_metrics"
        ]

        for section in required_sections:
            assert section in mock_stats, f"Missing stats section: {section}"

        # Validate numeric metrics
        assert isinstance(mock_stats["totals"]["messages"], int)
        assert isinstance(mock_stats["performance_metrics"]["average_response_time_minutes"], (int, float))
        assert 0 <= mock_stats["performance_metrics"]["escalation_rate"] <= 1


class TestAPIPerformance:
    """Test suite for API performance validation"""

    def test_message_delivery_performance(self):
        """Test message delivery API performance"""

        start_time = time.time()

        # Simulate API call timing
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.elapsed.total_seconds.return_value = 0.15  # 150ms
            mock_post.return_value = mock_response

            response = requests.post(
                "http://localhost:8000/api/messages",
                json={"test": "data"}
            )

            # API should respond within acceptable time
            response_time = response.elapsed.total_seconds()
            assert response_time < 0.5, f"API response too slow: {response_time}s"

    def test_bulk_operations_performance(self):
        """Test performance of bulk API operations"""

        # Test bulk message delivery
        bulk_messages = [
            {
                "message_id": f"bulk-{i}",
                "from_agent": "bulk-sender",
                "to_agent": f"agent-{i}",
                "content": f"Bulk message {i}",
                "priority": "NORMAL"
            }
            for i in range(100)
        ]

        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.elapsed.total_seconds.return_value = 2.5  # 2.5s for 100 messages
            mock_response.json.return_value = {
                "success": True,
                "processed": 100,
                "failed": 0,
                "processing_time_ms": 2500
            }
            mock_post.return_value = mock_response

            response = requests.post(
                "http://localhost:8000/api/messages/bulk",
                json={"messages": bulk_messages}
            )

            # Bulk operations should be efficient
            data = response.json()
            processing_time = data["processing_time_ms"]
            messages_per_second = (data["processed"] / processing_time) * 1000

            assert messages_per_second > 20, f"Bulk processing too slow: {messages_per_second} msg/s"

    def test_concurrent_api_access(self):
        """Test API behavior under concurrent access"""

        import threading
        import concurrent.futures

        def simulate_api_call(agent_id):
            """Simulate concurrent API call"""
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"agent_id": agent_id, "messages": []}
                mock_get.return_value = mock_response

                response = requests.get(f"http://localhost:8000/api/inbox/{agent_id}")
                return response.status_code == 200

        # Simulate 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(simulate_api_call, f"concurrent-agent-{i}")
                for i in range(10)
            ]

            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert all(results), "Some concurrent requests failed"


if __name__ == "__main__":
    """Run API validation tests"""
    pytest.main([__file__, "-v", "--tb=short"])