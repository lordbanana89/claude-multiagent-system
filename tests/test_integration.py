"""
Comprehensive Integration Test Suite
"""

import pytest
import asyncio
import aiohttp
import aioredis
import asyncpg
import json
import uuid
from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.backend_agent import BackendAgent
from agents.database_agent import DatabaseAgent
from agents.frontend_agent import FrontendAgent
from core.message_bus import MessageBus
from core.distributed_queue import DistributedQueue, Task
from core.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from core.workflow_engine import WorkflowEngine, WorkflowDefinition
from api.unified_gateway import app


class TestSystemIntegration:
    """Test complete system integration"""

    @pytest.fixture
    async def redis_client(self):
        """Create Redis client"""
        client = await aioredis.create_redis_pool('redis://localhost:6379')
        yield client
        client.close()
        await client.wait_closed()

    @pytest.fixture
    async def postgres_conn(self):
        """Create PostgreSQL connection"""
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            database='claude_agents_test',
            user='claude',
            password='claude_secret'
        )
        yield conn
        await conn.close()

    @pytest.fixture
    async def message_bus(self, redis_client):
        """Create message bus"""
        bus = MessageBus()
        await bus.initialize()
        yield bus
        await bus.cleanup()

    @pytest.fixture
    async def backend_agent(self):
        """Create backend agent"""
        agent = BackendAgent('test-backend')
        await agent.initialize()
        yield agent
        await agent.cleanup()

    @pytest.fixture
    async def database_agent(self):
        """Create database agent"""
        agent = DatabaseAgent('test-database')
        await agent.initialize()
        yield agent
        await agent.cleanup()

    @pytest.fixture
    async def frontend_agent(self):
        """Create frontend agent"""
        agent = FrontendAgent('test-frontend')
        await agent.initialize()
        yield agent
        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_end_to_end_task_flow(self, message_bus, backend_agent, database_agent, frontend_agent):
        """Test complete task flow through all agents"""

        # Create a task that flows through all agents
        task_id = str(uuid.uuid4())

        # 1. Frontend creates UI request
        ui_task = {
            'id': task_id,
            'type': 'generate_dashboard',
            'dashboard_type': 'performance'
        }

        await message_bus.redis_client.publish(
            'frontend:tasks',
            json.dumps(ui_task)
        )

        # Wait for frontend to process
        await asyncio.sleep(1)

        # 2. Backend fetches data for dashboard
        api_task = {
            'id': f"{task_id}-api",
            'type': 'api_request',
            'method': 'GET',
            'endpoint': '/metrics',
            'data': {}
        }

        await message_bus.redis_client.publish(
            'backend:tasks',
            json.dumps(api_task)
        )

        # 3. Database queries for metrics
        db_task = {
            'id': f"{task_id}-db",
            'type': 'query',
            'query': 'SELECT * FROM metrics WHERE timestamp > NOW() - INTERVAL \'1 hour\'',
            'params': {}
        }

        await message_bus.redis_client.publish(
            'database:tasks',
            json.dumps(db_task)
        )

        # Wait for all processing
        await asyncio.sleep(2)

        # Verify all tasks completed
        for tid in [task_id, f"{task_id}-api", f"{task_id}-db"]:
            status = await message_bus.redis_client.hget(f'task:{tid}', 'status')
            assert status == b'completed'

    @pytest.mark.asyncio
    async def test_workflow_execution(self, message_bus):
        """Test workflow execution with multiple steps"""

        workflow_def = WorkflowDefinition(
            name="test-workflow",
            steps=[
                {
                    'name': 'validate',
                    'agent': 'backend',
                    'task': {
                        'type': 'validate',
                        'schema_type': 'user',
                        'data': {'username': 'test', 'email': 'test@example.com'}
                    }
                },
                {
                    'name': 'save',
                    'agent': 'database',
                    'task': {
                        'type': 'query',
                        'query': 'INSERT INTO users (username, email) VALUES ($1, $2)',
                        'params': ['test', 'test@example.com']
                    },
                    'depends_on': ['validate']
                },
                {
                    'name': 'notify',
                    'agent': 'frontend',
                    'task': {
                        'type': 'render_component',
                        'component_type': 'notification',
                        'data': {'message': 'User created successfully'}
                    },
                    'depends_on': ['save']
                }
            ]
        )

        engine = WorkflowEngine(message_bus)
        workflow_id = await engine.execute_workflow(workflow_def, {})

        # Wait for workflow to complete
        await asyncio.sleep(3)

        status = await engine.get_workflow_status(workflow_id)
        assert status['status'] in ['completed', 'running']

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, backend_agent):
        """Test circuit breaker with failing service"""

        # Configure circuit breaker with low threshold
        config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout=5,
            success_threshold=1
        )

        breaker = CircuitBreaker('test-service', config)

        # Simulate failures
        failing_task = {
            'type': 'api_request',
            'method': 'GET',
            'endpoint': '/failing-endpoint'
        }

        failures = 0
        for _ in range(3):
            try:
                await breaker.call_async(
                    backend_agent.handle_api_request,
                    failing_task
                )
            except Exception:
                failures += 1

        # Circuit should be open after 2 failures
        assert breaker.state.value == 'open'
        assert failures >= 2

    @pytest.mark.asyncio
    async def test_distributed_queue_priority(self, redis_client):
        """Test distributed queue with priorities"""

        queue = DistributedQueue('test-queue')
        await queue.initialize()

        # Add tasks with different priorities
        high_priority = Task(
            id='high',
            type='important',
            priority=10,
            data={'message': 'urgent'}
        )

        low_priority = Task(
            id='low',
            type='regular',
            priority=1,
            data={'message': 'normal'}
        )

        await queue.enqueue(low_priority)
        await queue.enqueue(high_priority)

        # High priority should be processed first
        next_task = await queue.dequeue()
        assert next_task.id == 'high'

        await queue.cleanup()

    @pytest.mark.asyncio
    async def test_database_transaction(self, database_agent):
        """Test database transaction with rollback"""

        transaction_task = {
            'type': 'transaction',
            'operations': [
                {
                    'query': 'INSERT INTO test_table (id, value) VALUES ($1, $2)',
                    'params': [1, 'test1']
                },
                {
                    'query': 'INSERT INTO test_table (id, value) VALUES ($1, $2)',
                    'params': [1, 'test2']  # Duplicate ID should cause rollback
                }
            ]
        }

        result = await database_agent.handle_task(transaction_task)

        # Transaction should fail due to duplicate key
        assert 'error' in result or not result.get('success')

    @pytest.mark.asyncio
    async def test_frontend_form_validation(self, frontend_agent):
        """Test frontend form validation"""

        validation_task = {
            'type': 'validate_form',
            'data': {
                'username': 'ab',  # Too short
                'email': 'invalid-email',
                'age': 'not-a-number'
            },
            'rules': {
                'username': {'required': True, 'min_length': 3},
                'email': {'required': True, 'type': 'email'},
                'age': {'type': 'integer'}
            }
        }

        result = await frontend_agent.handle_task(validation_task)

        assert result['valid'] is False
        assert 'username' in result['errors']
        assert 'email' in result['errors']
        assert 'age' in result['errors']

    @pytest.mark.asyncio
    async def test_api_gateway_authentication(self):
        """Test API Gateway authentication flow"""

        async with aiohttp.ClientSession() as session:
            # Attempt unauthorized access
            async with session.get('http://localhost:8000/api/protected') as resp:
                assert resp.status == 401

            # Login to get token
            login_data = {
                'username': 'admin',
                'password': 'admin123'
            }

            async with session.post(
                'http://localhost:8000/auth/login',
                json=login_data
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    token = data.get('token')

                    # Access protected endpoint with token
                    headers = {'Authorization': f'Bearer {token}'}
                    async with session.get(
                        'http://localhost:8000/api/protected',
                        headers=headers
                    ) as resp:
                        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_metrics_collection(self, message_bus):
        """Test metrics collection across agents"""

        # Generate some activity
        for i in range(5):
            task = {
                'id': str(uuid.uuid4()),
                'type': 'test',
                'data': {'index': i}
            }

            await message_bus.publish_task(task)

        await asyncio.sleep(1)

        # Fetch metrics
        metrics = {}
        metric_keys = await message_bus.redis_client.keys('metrics:*')

        for key in metric_keys:
            metric_name = key.decode().split(':')[1]
            value = await message_bus.redis_client.get(key)
            if value:
                metrics[metric_name] = json.loads(value)

        # Should have collected some metrics
        assert len(metrics) > 0

    @pytest.mark.asyncio
    async def test_error_recovery(self, message_bus, backend_agent):
        """Test error recovery mechanisms"""

        # Create a task that will fail initially
        task = {
            'id': 'recovery-test',
            'type': 'api_request',
            'method': 'GET',
            'endpoint': '/unstable-endpoint',
            'max_retries': 3
        }

        # Track retry attempts
        retry_count = 0

        async def on_retry(attempt, error):
            nonlocal retry_count
            retry_count = attempt

        # Execute with retry
        result = await backend_agent.handle_task(task)

        # Should have attempted retries
        assert retry_count > 0 or result.get('status') == 'success'

    @pytest.mark.asyncio
    async def test_realtime_updates(self, frontend_agent, redis_client):
        """Test real-time WebSocket updates"""

        # Simulate WebSocket connection
        ws_id = str(uuid.uuid4())

        class MockWebSocket:
            def __init__(self):
                self.messages = []

            async def send_json(self, data):
                self.messages.append(data)

        mock_ws = MockWebSocket()
        frontend_agent.websocket_connections[ws_id] = mock_ws

        # Send real-time update
        update_task = {
            'type': 'update_realtime',
            'update_type': 'metrics',
            'data': {'cpu': 45, 'memory': 78}
        }

        result = await frontend_agent.handle_task(update_task)

        assert result['sent_to'] == 1
        assert len(mock_ws.messages) == 1
        assert mock_ws.messages[0]['type'] == 'metrics'

    @pytest.mark.asyncio
    async def test_load_balancing(self, message_bus):
        """Test load balancing across multiple agent instances"""

        # Create multiple backend agents
        agents = []
        for i in range(3):
            agent = BackendAgent(f'backend-{i}')
            await agent.initialize()
            agents.append(agent)

        # Send multiple tasks
        tasks_sent = 10
        for i in range(tasks_sent):
            task = {
                'id': f'lb-test-{i}',
                'type': 'api_request',
                'method': 'GET',
                'endpoint': f'/test/{i}'
            }

            await message_bus.publish_task(task)

        await asyncio.sleep(2)

        # Check task distribution
        task_counts = {}
        for agent in agents:
            task_counts[agent.agent_id] = agent.metrics.get('requests_total', 0)
            await agent.cleanup()

        # Tasks should be distributed (not all to one agent)
        assert len([count for count in task_counts.values() if count > 0]) > 1

    @pytest.mark.asyncio
    async def test_cache_performance(self, backend_agent):
        """Test caching improves performance"""

        # First request (cache miss)
        task = {
            'type': 'api_request',
            'method': 'GET',
            'endpoint': '/data',
            'data': {'param': 'test'}
        }

        start = datetime.now()
        result1 = await backend_agent.handle_task(task)
        time_without_cache = (datetime.now() - start).total_seconds()

        # Second request (cache hit)
        start = datetime.now()
        result2 = await backend_agent.handle_task(task)
        time_with_cache = (datetime.now() - start).total_seconds()

        # Cached request should be faster
        assert time_with_cache < time_without_cache
        assert backend_agent.metrics['cache_hits'] > 0

    @pytest.mark.asyncio
    async def test_database_query_optimization(self, database_agent):
        """Test database query optimization"""

        # Unoptimized query
        unoptimized = {
            'type': 'analyze',
            'query': 'SELECT * FROM large_table WHERE status = \'active\''
        }

        result = await database_agent.handle_task(unoptimized)

        # Should suggest index
        assert 'suggestions' in result
        assert any('index' in s.lower() for s in result['suggestions'])

    @pytest.mark.asyncio
    async def test_concurrent_workflows(self, message_bus):
        """Test concurrent workflow execution"""

        engine = WorkflowEngine(message_bus)

        # Create multiple workflows
        workflow_ids = []
        for i in range(5):
            workflow_def = WorkflowDefinition(
                name=f"concurrent-{i}",
                steps=[
                    {
                        'name': 'step1',
                        'agent': 'backend',
                        'task': {'type': 'test', 'data': {'index': i}}
                    },
                    {
                        'name': 'step2',
                        'agent': 'database',
                        'task': {'type': 'test', 'data': {'index': i}},
                        'depends_on': ['step1']
                    }
                ]
            )

            workflow_id = await engine.execute_workflow(workflow_def, {})
            workflow_ids.append(workflow_id)

        # Wait for completion
        await asyncio.sleep(3)

        # All workflows should complete
        for workflow_id in workflow_ids:
            status = await engine.get_workflow_status(workflow_id)
            assert status['status'] in ['completed', 'running']


class TestPerformance:
    """Performance and load tests"""

    @pytest.mark.asyncio
    async def test_high_throughput(self, message_bus):
        """Test system under high load"""

        tasks_count = 1000
        start_time = datetime.now()

        # Send many tasks rapidly
        for i in range(tasks_count):
            task = {
                'id': f'load-{i}',
                'type': 'test',
                'data': {'index': i}
            }

            await message_bus.publish_task(task)

        publish_time = (datetime.now() - start_time).total_seconds()

        # Should handle at least 100 tasks/second
        throughput = tasks_count / publish_time
        assert throughput > 100

    @pytest.mark.asyncio
    async def test_memory_usage(self, backend_agent):
        """Test memory usage under load"""

        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process many tasks
        for i in range(100):
            task = {
                'type': 'api_request',
                'method': 'POST',
                'endpoint': '/data',
                'data': {'large_field': 'x' * 10000}  # 10KB per task
            }

            await backend_agent.handle_task(task)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (< 100MB)
        assert memory_increase < 100

    @pytest.mark.asyncio
    async def test_connection_pool_limits(self, database_agent):
        """Test database connection pool under stress"""

        # Create many concurrent queries
        tasks = []
        for i in range(100):
            task = database_agent.handle_task({
                'type': 'query',
                'query': 'SELECT pg_sleep(0.1)',
                'params': {}
            })
            tasks.append(task)

        # Should handle concurrent queries without exhausting pool
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Most queries should succeed
        successful = sum(1 for r in results if not isinstance(r, Exception))
        assert successful > 80  # Allow some failures under extreme load


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])