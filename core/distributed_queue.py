"""
Distributed Task Queue with Priority Management
"""

import json
import time
import uuid
import threading
import heapq
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import IntEnum
import redis
import logging
from datetime import datetime, timedelta
import pickle
import hashlib

logger = logging.getLogger(__name__)


class TaskPriority(IntEnum):
    """Task priority levels"""
    CRITICAL = 0  # Highest priority
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4  # Lowest priority


class TaskState(IntEnum):
    """Task execution states"""
    PENDING = 0
    SCHEDULED = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4
    CANCELLED = 5
    RETRYING = 6


@dataclass
class Task:
    """Distributed task"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    agent: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    state: TaskState = TaskState.PENDING
    max_retries: int = 3
    retry_count: int = 0
    timeout: int = 300  # seconds
    created_at: float = field(default_factory=time.time)
    scheduled_at: Optional[float] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    ttl: int = 86400  # Time to live in seconds

    def __lt__(self, other):
        """For priority queue sorting"""
        return (self.priority, self.created_at) < (other.priority, other.created_at)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'agent': self.agent,
            'payload': self.payload,
            'priority': self.priority,
            'state': self.state,
            'max_retries': self.max_retries,
            'retry_count': self.retry_count,
            'timeout': self.timeout,
            'created_at': self.created_at,
            'scheduled_at': self.scheduled_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'result': self.result,
            'error': self.error,
            'dependencies': self.dependencies,
            'metadata': self.metadata,
            'ttl': self.ttl
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        """Create from dictionary"""
        task = cls()
        for key, value in data.items():
            if hasattr(task, key):
                setattr(task, key, value)
        return task


class DistributedQueue:
    """
    Distributed task queue with Redis backend
    """

    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=1):
        self.redis = redis.StrictRedis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=False  # We'll handle encoding/decoding
        )

        # Queue keys
        self.QUEUE_PREFIX = "queue:"
        self.TASK_PREFIX = "task:"
        self.AGENT_QUEUE_PREFIX = "agent_queue:"
        self.DELAYED_QUEUE = "delayed_queue"
        self.PROCESSING_SET = "processing"
        self.COMPLETED_SET = "completed"
        self.FAILED_SET = "failed"
        self.METRICS_KEY = "queue_metrics"

        # In-memory priority queues per agent
        self.priority_queues: Dict[str, List[Task]] = {}
        self.queue_locks: Dict[str, threading.Lock] = {}

        # Background threads
        self.scheduler_thread = None
        self.monitor_thread = None
        self.cleanup_thread = None
        self._running = False

        logger.info("DistributedQueue initialized")

    def start(self):
        """Start background threads"""
        if self._running:
            return

        self._running = True

        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()

        # Start monitor thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop)
        self.cleanup_thread.daemon = True
        self.cleanup_thread.start()

        logger.info("DistributedQueue started")

    def stop(self):
        """Stop background threads"""
        self._running = False

        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2)
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=2)

        logger.info("DistributedQueue stopped")

    def submit(self, task: Task) -> str:
        """Submit task to queue"""
        # Validate task
        if not task.agent:
            raise ValueError("Task must specify target agent")

        # Set task ID if not set
        if not task.id:
            task.id = str(uuid.uuid4())

        # Check dependencies
        if task.dependencies:
            if not self._check_dependencies(task.dependencies):
                task.state = TaskState.PENDING
                # Store in delayed queue
                self._add_to_delayed_queue(task)
                logger.info(f"Task {task.id} delayed due to dependencies")
                return task.id

        # Add to Redis
        self._save_task(task)

        # Add to agent's queue
        self._enqueue_task(task)

        # Update metrics
        self._increment_metric('tasks_submitted')
        self._increment_metric(f'tasks_submitted_{task.priority.name.lower()}')

        logger.info(f"Task {task.id} submitted to {task.agent} with priority {task.priority.name}")
        return task.id

    def get(self, agent: str, block: bool = True, timeout: int = 1) -> Optional[Task]:
        """Get next task for agent"""
        # Initialize queue if needed
        if agent not in self.queue_locks:
            self.queue_locks[agent] = threading.Lock()
            self.priority_queues[agent] = []

        start_time = time.time()

        while True:
            # Try to get task from priority queue
            with self.queue_locks[agent]:
                if self.priority_queues[agent]:
                    task = heapq.heappop(self.priority_queues[agent])

                    # Update task state
                    task.state = TaskState.RUNNING
                    task.started_at = time.time()

                    # Save to Redis
                    self._save_task(task)

                    # Add to processing set
                    self.redis.sadd(self.PROCESSING_SET, task.id.encode())

                    # Update metrics
                    self._increment_metric('tasks_started')

                    logger.debug(f"Task {task.id} dequeued for {agent}")
                    return task

            # Try to load from Redis
            self._load_agent_queue(agent)

            # Check if we should continue waiting
            if not block:
                return None

            if timeout and (time.time() - start_time) >= timeout:
                return None

            time.sleep(0.1)

    def complete(self, task_id: str, result: Any = None):
        """Mark task as completed"""
        task = self._load_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        task.state = TaskState.COMPLETED
        task.completed_at = time.time()
        task.result = result

        # Save task
        self._save_task(task)

        # Move from processing to completed
        self.redis.srem(self.PROCESSING_SET, task_id.encode())
        self.redis.sadd(self.COMPLETED_SET, task_id.encode())

        # Update metrics
        self._increment_metric('tasks_completed')
        duration = task.completed_at - task.started_at if task.started_at else 0
        self._update_metric('task_duration_sum', duration)

        # Check dependent tasks
        self._check_dependent_tasks(task_id)

        logger.info(f"Task {task_id} completed in {duration:.2f}s")

    def fail(self, task_id: str, error: str):
        """Mark task as failed"""
        task = self._load_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        task.error = error
        task.retry_count += 1

        # Check if should retry
        if task.retry_count < task.max_retries:
            task.state = TaskState.RETRYING
            # Re-queue with delay
            delay = min(2 ** task.retry_count, 60)  # Exponential backoff
            task.scheduled_at = time.time() + delay
            self._add_to_delayed_queue(task)

            logger.info(f"Task {task_id} failed, retry {task.retry_count}/{task.max_retries} in {delay}s")
        else:
            task.state = TaskState.FAILED
            task.completed_at = time.time()

            # Move to failed set
            self.redis.srem(self.PROCESSING_SET, task_id.encode())
            self.redis.sadd(self.FAILED_SET, task_id.encode())

            # Update metrics
            self._increment_metric('tasks_failed')

            logger.error(f"Task {task_id} failed permanently: {error}")

        # Save task
        self._save_task(task)

    def cancel(self, task_id: str):
        """Cancel a task"""
        task = self._load_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        if task.state in [TaskState.COMPLETED, TaskState.FAILED]:
            logger.warning(f"Cannot cancel task {task_id} in state {task.state}")
            return

        task.state = TaskState.CANCELLED
        task.completed_at = time.time()

        # Save task
        self._save_task(task)

        # Remove from queues
        self.redis.srem(self.PROCESSING_SET, task_id.encode())

        # Update metrics
        self._increment_metric('tasks_cancelled')

        logger.info(f"Task {task_id} cancelled")

    def get_status(self, task_id: str) -> Optional[Dict]:
        """Get task status"""
        task = self._load_task(task_id)
        if not task:
            return None

        return {
            'id': task.id,
            'name': task.name,
            'agent': task.agent,
            'state': TaskState(task.state).name,
            'priority': TaskPriority(task.priority).name,
            'retry_count': task.retry_count,
            'created_at': task.created_at,
            'started_at': task.started_at,
            'completed_at': task.completed_at,
            'result': task.result,
            'error': task.error
        }

    def get_queue_status(self) -> Dict:
        """Get overall queue status"""
        metrics = self._get_metrics()

        # Count tasks by state
        pending = self.redis.scard(self.DELAYED_QUEUE)
        processing = self.redis.scard(self.PROCESSING_SET)
        completed = self.redis.scard(self.COMPLETED_SET)
        failed = self.redis.scard(self.FAILED_SET)

        # Get queue sizes per agent
        agent_queues = {}
        for key in self.redis.keys(f"{self.AGENT_QUEUE_PREFIX}*"):
            agent = key.decode().replace(self.AGENT_QUEUE_PREFIX, "")
            agent_queues[agent] = self.redis.llen(key)

        return {
            'pending': pending,
            'processing': processing,
            'completed': completed,
            'failed': failed,
            'agent_queues': agent_queues,
            'metrics': metrics
        }

    def _enqueue_task(self, task: Task):
        """Add task to agent's queue"""
        # Add to Redis list
        queue_key = f"{self.AGENT_QUEUE_PREFIX}{task.agent}"
        task_data = pickle.dumps(task)

        # Add based on priority
        if task.priority <= TaskPriority.HIGH:
            # High priority: add to front
            self.redis.lpush(queue_key, task_data)
        else:
            # Normal/Low priority: add to back
            self.redis.rpush(queue_key, task_data)

        # Also add to in-memory queue if agent is active
        if task.agent in self.queue_locks:
            with self.queue_locks[task.agent]:
                heapq.heappush(self.priority_queues[task.agent], task)

    def _load_agent_queue(self, agent: str):
        """Load tasks from Redis to in-memory queue"""
        queue_key = f"{self.AGENT_QUEUE_PREFIX}{agent}"

        # Load up to 10 tasks
        tasks_data = self.redis.lrange(queue_key, 0, 9)

        if tasks_data:
            with self.queue_locks[agent]:
                for task_data in tasks_data:
                    try:
                        task = pickle.loads(task_data)
                        heapq.heappush(self.priority_queues[agent], task)
                    except Exception as e:
                        logger.error(f"Failed to load task: {e}")

                # Remove loaded tasks from Redis
                self.redis.ltrim(queue_key, len(tasks_data), -1)

    def _save_task(self, task: Task):
        """Save task to Redis"""
        key = f"{self.TASK_PREFIX}{task.id}"
        self.redis.setex(key, task.ttl, pickle.dumps(task))

    def _load_task(self, task_id: str) -> Optional[Task]:
        """Load task from Redis"""
        key = f"{self.TASK_PREFIX}{task_id}"
        task_data = self.redis.get(key)

        if task_data:
            try:
                return pickle.loads(task_data)
            except Exception as e:
                logger.error(f"Failed to load task {task_id}: {e}")

        return None

    def _add_to_delayed_queue(self, task: Task):
        """Add task to delayed queue"""
        scheduled_time = task.scheduled_at or time.time()
        self.redis.zadd(self.DELAYED_QUEUE, {task.id: scheduled_time})
        self._save_task(task)

    def _check_dependencies(self, dependencies: List[str]) -> bool:
        """Check if all dependencies are completed"""
        for dep_id in dependencies:
            dep_task = self._load_task(dep_id)
            if not dep_task or dep_task.state != TaskState.COMPLETED:
                return False
        return True

    def _check_dependent_tasks(self, completed_task_id: str):
        """Check and schedule tasks dependent on completed task"""
        # Get all tasks in delayed queue
        delayed_tasks = self.redis.zrange(self.DELAYED_QUEUE, 0, -1)

        for task_id_bytes in delayed_tasks:
            task_id = task_id_bytes.decode()
            task = self._load_task(task_id)

            if task and completed_task_id in task.dependencies:
                # Check if all dependencies are now satisfied
                if self._check_dependencies(task.dependencies):
                    # Remove from delayed queue
                    self.redis.zrem(self.DELAYED_QUEUE, task_id)

                    # Schedule task
                    task.state = TaskState.SCHEDULED
                    self._enqueue_task(task)

                    logger.info(f"Task {task_id} scheduled after dependency {completed_task_id} completed")

    def _scheduler_loop(self):
        """Background thread for scheduling delayed tasks"""
        while self._running:
            try:
                # Get tasks ready to be scheduled
                now = time.time()
                ready_tasks = self.redis.zrangebyscore(self.DELAYED_QUEUE, 0, now)

                for task_id_bytes in ready_tasks:
                    task_id = task_id_bytes.decode()
                    task = self._load_task(task_id)

                    if task:
                        # Remove from delayed queue
                        self.redis.zrem(self.DELAYED_QUEUE, task_id)

                        # Check dependencies
                        if not task.dependencies or self._check_dependencies(task.dependencies):
                            task.state = TaskState.SCHEDULED
                            self._enqueue_task(task)
                            logger.debug(f"Scheduled task {task_id}")

                time.sleep(1)

            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(5)

    def _monitor_loop(self):
        """Background thread for monitoring tasks"""
        while self._running:
            try:
                # Check for timed out tasks
                processing = self.redis.smembers(self.PROCESSING_SET)

                for task_id_bytes in processing:
                    task_id = task_id_bytes.decode()
                    task = self._load_task(task_id)

                    if task and task.started_at:
                        elapsed = time.time() - task.started_at

                        if elapsed > task.timeout:
                            # Task timed out
                            logger.warning(f"Task {task_id} timed out after {elapsed:.2f}s")
                            self.fail(task_id, f"Timeout after {task.timeout}s")

                # Update queue metrics
                self._update_queue_metrics()

                time.sleep(10)

            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(10)

    def _cleanup_loop(self):
        """Background thread for cleaning up old tasks"""
        while self._running:
            try:
                # Clean completed tasks older than 24 hours
                cutoff_time = time.time() - 86400

                # Clean completed set
                completed = self.redis.smembers(self.COMPLETED_SET)
                for task_id_bytes in completed:
                    task_id = task_id_bytes.decode()
                    task = self._load_task(task_id)

                    if task and task.completed_at and task.completed_at < cutoff_time:
                        # Remove task
                        self.redis.srem(self.COMPLETED_SET, task_id)
                        self.redis.delete(f"{self.TASK_PREFIX}{task_id}")
                        logger.debug(f"Cleaned up completed task {task_id}")

                # Clean failed set (keep for 7 days)
                failed_cutoff = time.time() - (7 * 86400)
                failed = self.redis.smembers(self.FAILED_SET)
                for task_id_bytes in failed:
                    task_id = task_id_bytes.decode()
                    task = self._load_task(task_id)

                    if task and task.completed_at and task.completed_at < failed_cutoff:
                        # Remove task
                        self.redis.srem(self.FAILED_SET, task_id)
                        self.redis.delete(f"{self.TASK_PREFIX}{task_id}")
                        logger.debug(f"Cleaned up failed task {task_id}")

                # Sleep for 1 hour
                time.sleep(3600)

            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                time.sleep(3600)

    def _increment_metric(self, key: str, value: int = 1):
        """Increment a metric"""
        self.redis.hincrby(self.METRICS_KEY, key, value)

    def _update_metric(self, key: str, value: float):
        """Update a metric value"""
        self.redis.hincrbyfloat(self.METRICS_KEY, key, value)

    def _get_metrics(self) -> Dict:
        """Get all metrics"""
        metrics = self.redis.hgetall(self.METRICS_KEY)
        return {k.decode(): float(v) for k, v in metrics.items()}

    def _update_queue_metrics(self):
        """Update queue size metrics"""
        for key in self.redis.keys(f"{self.AGENT_QUEUE_PREFIX}*"):
            agent = key.decode().replace(self.AGENT_QUEUE_PREFIX, "")
            queue_size = self.redis.llen(key)
            self.redis.hset(self.METRICS_KEY, f"queue_size_{agent}", queue_size)


class TaskWorker:
    """Worker for processing tasks from queue"""

    def __init__(self, agent_id: str, queue: DistributedQueue, handler: Callable[[Task], Any]):
        self.agent_id = agent_id
        self.queue = queue
        self.handler = handler
        self._running = False
        self._thread = None

        logger.info(f"TaskWorker initialized for {agent_id}")

    def start(self):
        """Start worker"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._work_loop)
        self._thread.daemon = True
        self._thread.start()

        logger.info(f"TaskWorker {self.agent_id} started")

    def stop(self):
        """Stop worker"""
        self._running = False

        if self._thread:
            self._thread.join(timeout=5)

        logger.info(f"TaskWorker {self.agent_id} stopped")

    def _work_loop(self):
        """Main work loop"""
        while self._running:
            try:
                # Get task from queue
                task = self.queue.get(self.agent_id, block=True, timeout=1)

                if task:
                    logger.debug(f"Worker {self.agent_id} processing task {task.id}")

                    try:
                        # Process task
                        result = self.handler(task)

                        # Mark as completed
                        self.queue.complete(task.id, result)

                    except Exception as e:
                        logger.error(f"Task {task.id} failed: {e}")
                        self.queue.fail(task.id, str(e))

            except Exception as e:
                logger.error(f"Worker {self.agent_id} error: {e}")
                time.sleep(1)


# Singleton instance
_distributed_queue = None

def get_distributed_queue() -> DistributedQueue:
    """Get or create distributed queue instance"""
    global _distributed_queue
    if _distributed_queue is None:
        _distributed_queue = DistributedQueue()
        _distributed_queue.start()
    return _distributed_queue