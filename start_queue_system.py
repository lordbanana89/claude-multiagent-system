#!/usr/bin/env python3
"""
Activation script for the existing Distributed Queue System
Integrates with MCP v2 for task orchestration
"""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.distributed_queue import (
    DistributedQueue,
    Task,
    TaskPriority,
    TaskState,
    TaskWorker,
    get_distributed_queue
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QueueSystemActivator:
    """Activates and manages the distributed queue system"""

    def __init__(self, use_redis=False):
        """
        Initialize queue system activator

        Args:
            use_redis: Whether to use Redis (True) or SQLite (False) backend
        """
        self.use_redis = use_redis
        self.queue = None
        self.workers = {}
        self.agent_handlers = {}

    def start(self):
        """Start the queue system"""
        logger.info("🚀 Starting Distributed Queue System...")

        try:
            if self.use_redis:
                # Use Redis backend
                logger.info("Using Redis backend for queue")
                self.queue = DistributedQueue(
                    redis_host='localhost',
                    redis_port=6379,
                    redis_db=1
                )
            else:
                # Use SQLite backend (fallback)
                logger.info("Using SQLite backend for queue")
                # For SQLite, we'll use a modified version that doesn't require Redis
                self.queue = self._create_sqlite_queue()

            # Start the queue
            self.queue.start()

            # Register default handlers for each agent
            self._register_default_handlers()

            # Start workers for each agent
            self._start_workers()

            logger.info("✅ Queue system started successfully")

            # Print initial status
            self._print_status()

            return True

        except Exception as e:
            logger.error(f"❌ Failed to start queue system: {e}")
            return False

    def _create_sqlite_queue(self):
        """Create SQLite-based queue (fallback when Redis not available)"""
        # Import the SQLite queue implementation
        try:
            from langgraph_test.dramatiq_queue import DramatiqBackend
            logger.info("Using DramatiqBackend for SQLite queue")

            # Initialize Dramatiq backend with SQLite
            backend = DramatiqBackend(
                db_path='langgraph-test/dramatiq_queue.db'
            )
            backend.init_db()

            # Wrap it to match DistributedQueue interface
            class SQLiteQueueWrapper:
                def __init__(self, backend):
                    self.backend = backend
                    self._running = False

                def start(self):
                    self._running = True
                    logger.info("SQLite queue backend started")

                def stop(self):
                    self._running = False

                def submit(self, task):
                    """Submit task to SQLite backend"""
                    self.backend.enqueue(
                        queue_name=task.agent,
                        message={
                            'id': task.id,
                            'name': task.name,
                            'payload': task.payload,
                            'priority': task.priority
                        },
                        priority=task.priority
                    )
                    return task.id

                def get(self, agent, block=True, timeout=1):
                    """Get task from SQLite backend"""
                    messages = self.backend.get_messages(
                        queue_name=agent,
                        limit=1
                    )
                    if messages:
                        msg = messages[0]
                        task = Task(
                            id=msg['message_data']['id'],
                            name=msg['message_data']['name'],
                            agent=agent,
                            payload=msg['message_data']['payload'],
                            priority=msg['message_data']['priority']
                        )
                        return task
                    return None

                def complete(self, task_id, result=None):
                    """Mark task as completed"""
                    self.backend.ack(task_id)
                    logger.info(f"Task {task_id} completed")

                def fail(self, task_id, error):
                    """Mark task as failed"""
                    self.backend.nack(task_id, error)
                    logger.warning(f"Task {task_id} failed: {error}")

                def get_queue_status(self):
                    """Get queue status"""
                    stats = self.backend.get_stats()
                    return {
                        'pending': stats.get('pending', 0),
                        'processing': stats.get('processing', 0),
                        'completed': stats.get('completed', 0),
                        'failed': stats.get('failed', 0)
                    }

            return SQLiteQueueWrapper(backend)

        except ImportError:
            # Fallback to in-memory queue
            logger.warning("DramatiqBackend not found, using in-memory queue")
            return get_distributed_queue()

    def _register_default_handlers(self):
        """Register default task handlers for each agent"""

        def create_handler(agent_name):
            """Create a handler for an agent"""
            def handler(task):
                logger.info(f"📋 {agent_name} processing task: {task.name}")
                logger.debug(f"   Payload: {task.payload}")

                # Simulate processing based on task type
                if task.name == 'test':
                    return {'status': 'success', 'message': 'Test completed'}
                elif task.name == 'compile':
                    return {'status': 'success', 'output': 'Compilation successful'}
                elif task.name == 'deploy':
                    return {'status': 'success', 'url': 'http://localhost:8080'}
                else:
                    # Default processing
                    return {
                        'status': 'success',
                        'agent': agent_name,
                        'task': task.name,
                        'result': 'Task processed successfully'
                    }
            return handler

        # Register handlers for each agent
        agents = [
            'supervisor',
            'backend-api',
            'database',
            'frontend-ui',
            'testing',
            'queue-manager',
            'deployment',
            'instagram',
            'master'
        ]

        for agent in agents:
            self.agent_handlers[agent] = create_handler(agent)
            logger.info(f"✅ Registered handler for {agent}")

    def _start_workers(self):
        """Start worker threads for each agent"""
        for agent, handler in self.agent_handlers.items():
            worker = TaskWorker(
                agent_id=agent,
                queue=self.queue,
                handler=handler
            )
            worker.start()
            self.workers[agent] = worker
            logger.info(f"🔧 Started worker for {agent}")

    def submit_task(self, agent: str, task_name: str, payload: Dict[str, Any] = None,
                    priority: str = 'NORMAL') -> str:
        """
        Submit a task to the queue

        Args:
            agent: Target agent name
            task_name: Name/type of the task
            payload: Task data
            priority: Task priority (CRITICAL, HIGH, NORMAL, LOW, BACKGROUND)

        Returns:
            Task ID
        """
        priority_map = {
            'CRITICAL': TaskPriority.CRITICAL,
            'HIGH': TaskPriority.HIGH,
            'NORMAL': TaskPriority.NORMAL,
            'LOW': TaskPriority.LOW,
            'BACKGROUND': TaskPriority.BACKGROUND
        }

        task = Task(
            name=task_name,
            agent=agent,
            payload=payload or {},
            priority=priority_map.get(priority, TaskPriority.NORMAL)
        )

        task_id = self.queue.submit(task)
        logger.info(f"📤 Submitted task {task_id} to {agent} (priority: {priority})")
        return task_id

    def _print_status(self):
        """Print queue status"""
        try:
            status = self.queue.get_queue_status()
            logger.info("📊 Queue Status:")
            logger.info(f"   Pending: {status.get('pending', 0)}")
            logger.info(f"   Processing: {status.get('processing', 0)}")
            logger.info(f"   Completed: {status.get('completed', 0)}")
            logger.info(f"   Failed: {status.get('failed', 0)}")
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")

    def stop(self):
        """Stop the queue system"""
        logger.info("Stopping queue system...")

        # Stop workers
        for agent, worker in self.workers.items():
            worker.stop()
            logger.info(f"Stopped worker for {agent}")

        # Stop queue
        if self.queue:
            self.queue.stop()

        logger.info("Queue system stopped")


def test_queue_system():
    """Test the queue system with sample tasks"""
    activator = QueueSystemActivator(use_redis=False)  # Use SQLite by default

    if not activator.start():
        logger.error("Failed to start queue system")
        return

    # Submit test tasks
    logger.info("\n📝 Submitting test tasks...")

    # High priority task for supervisor
    task1 = activator.submit_task(
        agent='supervisor',
        task_name='orchestrate',
        payload={'action': 'coordinate', 'target': 'auth_system'},
        priority='HIGH'
    )

    # Normal priority task for backend
    task2 = activator.submit_task(
        agent='backend-api',
        task_name='implement',
        payload={'endpoint': '/api/auth/login', 'method': 'POST'},
        priority='NORMAL'
    )

    # Critical task for database
    task3 = activator.submit_task(
        agent='database',
        task_name='migrate',
        payload={'schema': 'users_v2', 'action': 'create'},
        priority='CRITICAL'
    )

    logger.info(f"\n✅ Submitted tasks: {task1}, {task2}, {task3}")

    # Wait for processing
    import time
    time.sleep(3)

    # Print final status
    activator._print_status()

    # Stop the system
    activator.stop()


if __name__ == "__main__":
    # Check for Redis availability
    try:
        import redis
        r = redis.StrictRedis(host='localhost', port=6379, db=1)
        r.ping()
        use_redis = True
        logger.info("Redis is available, using Redis backend")
    except:
        use_redis = False
        logger.info("Redis not available, using SQLite backend")

    # Run test
    test_queue_system()