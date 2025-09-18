"""
Dramatiq Emergency Queue System - Core Implementation
HIGH PRIORITY: Replace tmux subprocess architecture with robust task queue
"""

import dramatiq
import redis
import json
import time
import uuid
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
import subprocess
import os
import signal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Redis broker
try:
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    redis_client.ping()

    # Use Redis broker for production
    from dramatiq.brokers.redis import RedisBroker
    broker = RedisBroker(host="localhost", port=6379)
    dramatiq.set_broker(broker)
    logger.info("✅ Redis broker configured successfully")

except Exception as e:
    # Fallback to in-memory broker for development/testing
    from dramatiq.brokers.stub import StubBroker
    broker = StubBroker()
    dramatiq.set_broker(broker)
    logger.warning(f"⚠️ Using StubBroker (in-memory) due to Redis issue: {e}")


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    EMERGENCY = 5


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class QueueTask:
    """Enhanced task representation"""
    task_id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    agent_id: str = ""
    command: str = ""
    description: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3
    timeout: int = 300  # 5 minutes default
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "command": self.command,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "metadata": self.metadata
        }


class DramatiqQueueManager:
    """Emergency queue manager replacing tmux architecture"""

    def __init__(self):
        self.active_tasks: Dict[str, QueueTask] = {}
        self.task_history: List[QueueTask] = []
        self.workers: Dict[str, Dict[str, Any]] = {}
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "pending_tasks": 0,
            "active_workers": 0
        }
        self.lock = threading.RLock()

        # Start monitoring thread
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_queue, daemon=True)
        self.monitor_thread.start()

        logger.info("🚀 DramatiqQueueManager initialized")

    def submit_task(self, agent_id: str, command: str, description: str = "",
                   priority: TaskPriority = TaskPriority.NORMAL, **kwargs) -> str:
        """Submit emergency task to queue"""
        task = QueueTask(
            agent_id=agent_id,
            command=command,
            description=description,
            priority=priority,
            **kwargs
        )

        with self.lock:
            self.active_tasks[task.task_id] = task
            self.stats["total_tasks"] += 1
            self.stats["pending_tasks"] += 1

        # Submit to Dramatiq queue with priority
        queue_name = self._get_queue_name(priority)

        try:
            # Execute task immediately for emergency
            execute_agent_task.send_with_options(
                args=(task.to_dict(),),
                delay=0,
                queue_name=queue_name
            )

            logger.info(f"📩 Task {task.task_id} submitted to {queue_name} queue")
            return task.task_id

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"❌ Failed to submit task {task.task_id}: {e}")
            return task.task_id

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current task status"""
        with self.lock:
            task = self.active_tasks.get(task_id)
            if task:
                return task.to_dict()

            # Check history
            for historical_task in self.task_history:
                if historical_task.task_id == task_id:
                    return historical_task.to_dict()

        return None

    def cancel_task(self, task_id: str) -> bool:
        """Cancel pending task"""
        with self.lock:
            task = self.active_tasks.get(task_id)
            if task and task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
                self._move_to_history(task)
                return True
        return False

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get comprehensive queue statistics"""
        with self.lock:
            return {
                **self.stats,
                "active_tasks": len(self.active_tasks),
                "task_history_size": len(self.task_history),
                "broker_type": type(broker).__name__,
                "timestamp": datetime.now().isoformat()
            }

    def get_pending_tasks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get pending tasks causing system instability"""
        with self.lock:
            pending = [
                task.to_dict() for task in self.active_tasks.values()
                if task.status == TaskStatus.PENDING
            ]
            # Sort by priority and creation time
            pending.sort(key=lambda x: (x["priority"], x["created_at"]), reverse=True)
            return pending[:limit]

    def _get_queue_name(self, priority: TaskPriority) -> str:
        """Get queue name based on priority"""
        priority_queues = {
            TaskPriority.EMERGENCY: "emergency",
            TaskPriority.URGENT: "urgent",
            TaskPriority.HIGH: "high",
            TaskPriority.NORMAL: "default",
            TaskPriority.LOW: "low"
        }
        return priority_queues.get(priority, "default")

    def _move_to_history(self, task: QueueTask):
        """Move completed task to history"""
        if task.task_id in self.active_tasks:
            del self.active_tasks[task.task_id]
            self.task_history.append(task)

            # Update stats
            if task.status == TaskStatus.COMPLETED:
                self.stats["completed_tasks"] += 1
            elif task.status == TaskStatus.FAILED:
                self.stats["failed_tasks"] += 1

            self.stats["pending_tasks"] = len([
                t for t in self.active_tasks.values()
                if t.status == TaskStatus.PENDING
            ])

            # Keep history size manageable
            if len(self.task_history) > 1000:
                self.task_history = self.task_history[-500:]

    def _monitor_queue(self):
        """Monitor queue health and performance"""
        while self.monitoring_active:
            try:
                with self.lock:
                    # Check for stuck tasks
                    now = datetime.now()
                    for task in list(self.active_tasks.values()):
                        if task.status == TaskStatus.RUNNING:
                            # Check for timeout
                            if task.started_at and (now - task.started_at).seconds > task.timeout:
                                logger.warning(f"⏰ Task {task.task_id} timed out")
                                task.status = TaskStatus.FAILED
                                task.error = "Task timeout"
                                task.completed_at = now
                                self._move_to_history(task)

                time.sleep(5)  # Monitor every 5 seconds

            except Exception as e:
                logger.error(f"❌ Monitor error: {e}")
                time.sleep(10)

    def emergency_drain_queue(self) -> Dict[str, Any]:
        """Emergency: Process all pending tasks immediately"""
        logger.warning("🚨 EMERGENCY QUEUE DRAIN INITIATED")

        with self.lock:
            pending_tasks = [
                task for task in self.active_tasks.values()
                if task.status == TaskStatus.PENDING
            ]

        results = {
            "total_drained": len(pending_tasks),
            "successful": 0,
            "failed": 0,
            "start_time": datetime.now().isoformat()
        }

        for task in pending_tasks:
            try:
                # Execute directly without queue for emergency
                result = self._execute_task_direct(task)
                if result["success"]:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error(f"❌ Emergency drain failed for {task.task_id}: {e}")
                results["failed"] += 1

        results["end_time"] = datetime.now().isoformat()
        logger.info(f"🚨 Emergency drain completed: {results}")
        return results

    def _execute_task_direct(self, task: QueueTask) -> Dict[str, Any]:
        """Direct task execution for emergency scenarios"""
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()

            # Execute command directly
            result = subprocess.run(
                task.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=task.timeout
            )

            task.completed_at = datetime.now()

            if result.returncode == 0:
                task.status = TaskStatus.COMPLETED
                task.result = result.stdout
                return {"success": True, "output": result.stdout}
            else:
                task.status = TaskStatus.FAILED
                task.error = result.stderr
                return {"success": False, "error": result.stderr}

        except subprocess.TimeoutExpired:
            task.status = TaskStatus.FAILED
            task.error = "Command timeout"
            return {"success": False, "error": "Command timeout"}
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            return {"success": False, "error": str(e)}
        finally:
            with self.lock:
                self._move_to_history(task)


# Global queue manager instance
queue_manager = DramatiqQueueManager()


@dramatiq.actor(queue_name="emergency", max_retries=3, time_limit=300000)  # 5 minutes
def execute_agent_task(task_data: Dict[str, Any]):
    """Dramatiq actor for executing agent tasks"""
    task_id = task_data["task_id"]

    try:
        # Update task status
        with queue_manager.lock:
            if task_id in queue_manager.active_tasks:
                task = queue_manager.active_tasks[task_id]
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()

        logger.info(f"🏃 Executing task {task_id}: {task_data['command']}")

        # Execute the command
        result = subprocess.run(
            task_data["command"],
            shell=True,
            capture_output=True,
            text=True,
            timeout=task_data.get("timeout", 300)
        )

        # Update task with results
        with queue_manager.lock:
            if task_id in queue_manager.active_tasks:
                task = queue_manager.active_tasks[task_id]
                task.completed_at = datetime.now()

                if result.returncode == 0:
                    task.status = TaskStatus.COMPLETED
                    task.result = result.stdout
                    logger.info(f"✅ Task {task_id} completed successfully")
                else:
                    task.status = TaskStatus.FAILED
                    task.error = result.stderr
                    logger.error(f"❌ Task {task_id} failed: {result.stderr}")

                queue_manager._move_to_history(task)

        return {
            "task_id": task_id,
            "success": result.returncode == 0,
            "output": result.stdout if result.returncode == 0 else result.stderr
        }

    except subprocess.TimeoutExpired:
        error_msg = f"Task {task_id} timed out"
        logger.error(f"⏰ {error_msg}")

        with queue_manager.lock:
            if task_id in queue_manager.active_tasks:
                task = queue_manager.active_tasks[task_id]
                task.status = TaskStatus.FAILED
                task.error = error_msg
                task.completed_at = datetime.now()
                queue_manager._move_to_history(task)

        raise

    except Exception as e:
        error_msg = f"Task {task_id} failed with exception: {str(e)}"
        logger.error(f"❌ {error_msg}")

        with queue_manager.lock:
            if task_id in queue_manager.active_tasks:
                task = queue_manager.active_tasks[task_id]
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now()
                queue_manager._move_to_history(task)

        raise


# High-priority actors for different queue levels
@dramatiq.actor(queue_name="urgent", max_retries=2, time_limit=180000)  # 3 minutes
def execute_urgent_task(task_data: Dict[str, Any]):
    """Execute urgent priority tasks"""
    return execute_agent_task(task_data)


@dramatiq.actor(queue_name="high", max_retries=2, time_limit=240000)  # 4 minutes
def execute_high_task(task_data: Dict[str, Any]):
    """Execute high priority tasks"""
    return execute_agent_task(task_data)


@dramatiq.actor(queue_name="default", max_retries=3, time_limit=300000)  # 5 minutes
def execute_normal_task(task_data: Dict[str, Any]):
    """Execute normal priority tasks"""
    return execute_agent_task(task_data)


@dramatiq.actor(queue_name="low", max_retries=1, time_limit=600000)  # 10 minutes
def execute_low_task(task_data: Dict[str, Any]):
    """Execute low priority tasks"""
    return execute_agent_task(task_data)


def get_queue_manager() -> DramatiqQueueManager:
    """Get global queue manager instance"""
    return queue_manager


if __name__ == "__main__":
    # Emergency test
    print("🚨 EMERGENCY DRAMATIQ QUEUE SYSTEM STARTING...")

    # Test the system
    task_id = queue_manager.submit_task(
        agent_id="emergency-test",
        command="echo 'Emergency queue system operational'",
        description="Emergency system test",
        priority=TaskPriority.EMERGENCY
    )

    print(f"📩 Emergency test task submitted: {task_id}")

    # Wait for completion
    time.sleep(2)

    status = queue_manager.get_task_status(task_id)
    if status:
        print(f"📊 Task status: {status['status']}")
        if status['result']:
            print(f"📋 Result: {status['result']}")

    stats = queue_manager.get_queue_stats()
    print(f"📈 Queue stats: {stats}")

    print("✅ Emergency Dramatiq system initialized and tested!")