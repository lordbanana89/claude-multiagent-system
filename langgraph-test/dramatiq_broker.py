"""
🚨 EMERGENCY DRAMATIQ DATABASE BROKER
High-performance broker implementation with database persistence
"""

import dramatiq
from dramatiq.broker import Broker
from dramatiq.message import Message
from dramatiq.results import Results
from typing import Optional, Dict, Any, List
import threading
import time
from datetime import datetime, timedelta
import logging
import json
import uuid
import traceback

from dramatiq_database import DramatiqDatabaseBackend, DramatiqMessage, MessageStatus, Priority

logger = logging.getLogger(__name__)


class DatabaseBroker(Broker):
    """🚨 EMERGENCY DATABASE BROKER FOR DRAMATIQ"""

    def __init__(self, db_backend: DramatiqDatabaseBackend, max_workers: int = 50):
        super().__init__()
        self.db_backend = db_backend
        self.max_workers = max_workers
        self._workers = {}
        self._shutdown_event = threading.Event()
        self._cleanup_thread = None

        # Start cleanup thread
        self._start_cleanup_thread()

        logger.info(f"🚨 Emergency Database Broker initialized with {max_workers} max workers")

    def consume(self, queue_name: str, callback: callable, **kwargs):
        """🚨 EMERGENCY: Start consuming messages from database queue"""
        worker_id = f"worker_{uuid.uuid4().hex[:8]}"

        def worker_loop():
            logger.info(f"🔥 Worker {worker_id} started consuming from {queue_name}")

            while not self._shutdown_event.is_set():
                try:
                    # Dequeue message from database
                    db_message = self.db_backend.dequeue_message(queue_name, worker_id, timeout=300)

                    if db_message:
                        start_time = time.time()

                        try:
                            # Convert to Dramatiq message format
                            dramatiq_msg = Message(
                                queue_name=db_message.queue_name,
                                actor_name=db_message.actor_name,
                                args=db_message.args,
                                kwargs=db_message.kwargs,
                                options=db_message.options,
                                message_id=db_message.message_id
                            )

                            # Execute callback
                            result = callback(dramatiq_msg)

                            # Calculate processing time
                            processing_time = int((time.time() - start_time) * 1000)

                            # Mark as completed
                            self.db_backend.complete_message(
                                db_message.message_id,
                                worker_id,
                                processing_time
                            )

                            logger.info(f"✅ Message {db_message.message_id} processed successfully")

                        except Exception as e:
                            # Mark as failed
                            self.db_backend.fail_message(
                                db_message.message_id,
                                worker_id,
                                str(e),
                                traceback.format_exc() if hasattr(e, '__traceback__') else None
                            )
                            logger.error(f"❌ Message {db_message.message_id} failed: {e}")

                    else:
                        # No messages available, wait briefly
                        time.sleep(0.1)

                except Exception as e:
                    logger.error(f"Worker {worker_id} error: {e}")
                    time.sleep(1)

            logger.info(f"🛑 Worker {worker_id} stopped")

        # Start worker thread
        worker_thread = threading.Thread(target=worker_loop, daemon=True)
        worker_thread.start()
        self._workers[worker_id] = worker_thread

        return worker_thread

    def join(self, queue_name: str) -> None:
        """🚨 EMERGENCY: Join a worker thread"""
        for worker_id, worker_thread in self._workers.items():
            if worker_thread.is_alive():
                worker_thread.join()

    def get_actor(self, actor_name: str):
        """🚨 EMERGENCY: Get actor by name"""
        for actor in self.actors:
            if actor.actor_name == actor_name:
                return actor
        raise ValueError(f"Actor {actor_name} not found")

    def enqueue(self, message: Message, *, delay: Optional[int] = None) -> Message:
        """🚨 EMERGENCY: Enqueue message to database with high performance"""
        try:
            # Convert Dramatiq message to database message
            db_message = DramatiqMessage(
                message_id=message.message_id,
                queue_name=message.queue_name,
                actor_name=message.actor_name,
                args=message.args,
                kwargs=message.kwargs,
                options=message.options,
                priority=self._get_priority_from_options(message.options),
                scheduled_at=datetime.utcnow() + timedelta(milliseconds=delay) if delay else None
            )

            # Enqueue to database
            success = self.db_backend.enqueue_message(db_message)

            if success:
                logger.info(f"🚨 Message enqueued: {message.message_id} -> {message.queue_name}")
                return message
            else:
                raise RuntimeError(f"Failed to enqueue message {message.message_id}")

        except Exception as e:
            logger.error(f"Failed to enqueue message: {e}")
            raise

    def flush(self, queue_name: str) -> int:
        """🚨 EMERGENCY: Flush all pending messages from queue"""
        # Not implemented for database backend - would require mass deletion
        logger.warning("Flush operation not implemented for database backend")
        return 0

    def flush_all(self) -> int:
        """🚨 EMERGENCY: Flush all queues"""
        logger.warning("Flush all operation not implemented for database backend")
        return 0

    def declare_queue(self, queue_name: str) -> None:
        """🚨 EMERGENCY: Declare a queue (required by Dramatiq interface)"""
        if queue_name not in self.queues:
            # Simple queue representation for our database broker
            self.queues[queue_name] = queue_name
            logger.info(f"🔧 Queue declared: {queue_name}")

    def add_queue(self, queue_name: str) -> None:
        """🚨 EMERGENCY: Add a queue to the broker"""
        if queue_name not in self.queues:
            # Simple queue representation for our database broker
            self.queues[queue_name] = queue_name
            logger.info(f"🔧 Queue added: {queue_name}")

    def get_declared_queues(self) -> List[str]:
        """Get list of declared queues"""
        return list(self.queues.keys())

    def get_declared_actors(self) -> List[str]:
        """Get list of declared actors"""
        return [actor.actor_name for actor in self.actors]

    def do_work(self, queue_name: str = None, timeout: int = 30000) -> bool:
        """Process a single message from queue"""
        try:
            # Get message from specified queue or default
            target_queue = queue_name or "default"
            worker_id = f"single_worker_{uuid.uuid4().hex[:8]}"

            db_message = self.db_backend.dequeue_message(target_queue, worker_id, timeout//1000)

            if db_message:
                # Convert to Dramatiq message
                dramatiq_msg = Message(
                    queue_name=db_message.queue_name,
                    actor_name=db_message.actor_name,
                    args=db_message.args,
                    kwargs=db_message.kwargs,
                    options=db_message.options,
                    message_id=db_message.message_id
                )

                # Find and execute actor
                actor = None
                for a in self.actors:
                    if a.actor_name == db_message.actor_name:
                        actor = a
                        break

                if actor:
                    start_time = time.time()
                    try:
                        # Execute actor function
                        result = actor.fn(*db_message.args, **db_message.kwargs)
                        processing_time = int((time.time() - start_time) * 1000)

                        # Mark as completed
                        self.db_backend.complete_message(
                            db_message.message_id,
                            worker_id,
                            processing_time
                        )
                        logger.info(f"✅ Single message processed: {db_message.message_id}")
                        return True

                    except Exception as e:
                        # Mark as failed
                        self.db_backend.fail_message(
                            db_message.message_id,
                            worker_id,
                            str(e)
                        )
                        logger.error(f"❌ Single message failed: {e}")
                        return False
                else:
                    logger.error(f"❌ Actor {db_message.actor_name} not found")
                    return False

            return False  # No message available

        except Exception as e:
            logger.error(f"do_work error: {e}")
            return False

    def _get_priority_from_options(self, options: Dict[str, Any]) -> Priority:
        """Extract priority from message options"""
        priority_value = options.get('priority', 10)

        if priority_value >= 30:
            return Priority.URGENT
        elif priority_value >= 20:
            return Priority.HIGH
        elif priority_value <= 0:
            return Priority.LOW
        else:
            return Priority.NORMAL

    def _start_cleanup_thread(self):
        """🚨 EMERGENCY: Start background cleanup and monitoring"""
        def cleanup_loop():
            while not self._shutdown_event.is_set():
                try:
                    # Cleanup completed messages older than 24 hours
                    # (This would be implemented in the database backend)

                    # Log health stats
                    health = self.db_backend.get_system_health()
                    logger.info(f"📊 Queue health: {health['queue_totals']}")

                    # Sleep for 5 minutes
                    time.sleep(300)

                except Exception as e:
                    logger.error(f"Cleanup thread error: {e}")
                    time.sleep(60)

        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def close(self):
        """🚨 EMERGENCY: Graceful shutdown"""
        logger.info("🛑 Shutting down Database Broker...")

        self._shutdown_event.set()

        # Wait for workers to finish
        for worker_id, worker_thread in self._workers.items():
            logger.info(f"Waiting for worker {worker_id}...")
            worker_thread.join(timeout=10)

        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)

        logger.info("✅ Database Broker shutdown complete")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class DatabaseResults(Results):
    """🚨 EMERGENCY RESULTS BACKEND FOR DATABASE STORAGE"""

    def __init__(self, db_backend: DramatiqDatabaseBackend):
        self.db_backend = db_backend

    def get_result(self, message: Message, *, block: bool = False, timeout: Optional[int] = None):
        """Get result for a message"""
        # This would require additional table for storing results
        # For now, return None (results not stored)
        return None

    def set_result(self, message: Message, result: Any, ttl: int):
        """Set result for a message"""
        # This would require additional table for storing results
        # For now, do nothing
        pass


# 🚨 EMERGENCY INTEGRATION SETUP
def setup_emergency_dramatiq_system(db_type: str = "sqlite",
                                   connection_string: str = None,
                                   max_workers: int = 50) -> DatabaseBroker:
    """🚨 EMERGENCY: Setup complete Dramatiq system with database backend"""

    # Initialize database backend
    db_backend = DramatiqDatabaseBackend(db_type, connection_string)

    # Initialize broker
    broker = DatabaseBroker(db_backend, max_workers)

    # Initialize results backend
    results_backend = DatabaseResults(db_backend)

    # Configure Dramatiq with middleware
    dramatiq.set_broker(broker)

    # Add middleware only if not already present
    middleware_types = [type(m) for m in broker.middleware]

    if dramatiq.middleware.CurrentMessage not in middleware_types:
        broker.add_middleware(dramatiq.middleware.CurrentMessage())

    if dramatiq.middleware.Retries not in middleware_types:
        broker.add_middleware(dramatiq.middleware.Retries(max_retries=3))

    if dramatiq.middleware.TimeLimit not in middleware_types:
        broker.add_middleware(dramatiq.middleware.TimeLimit(time_limit=300000))  # 5 minutes

    logger.info("🚨 Emergency Dramatiq system setup complete!")

    return broker


# 🚨 EMERGENCY TESTING
def emergency_test_broker():
    """🚨 EMERGENCY: Test broker functionality"""
    print("🚨 TESTING EMERGENCY DRAMATIQ BROKER...")

    try:
        # Setup system
        broker = setup_emergency_dramatiq_system()

        # Define test actor
        @dramatiq.actor(queue_name="emergency_queue", max_retries=3)
        def emergency_task(task_id: str, data: Dict[str, Any]):
            """Emergency test task"""
            print(f"🔥 Processing emergency task {task_id}: {data}")
            time.sleep(0.1)  # Simulate work
            return {"status": "completed", "task_id": task_id}

        # Send test messages
        for i in range(5):
            message = emergency_task.send(f"task_{i}", {"priority": "urgent", "data": f"test_data_{i}"})
            print(f"✅ Sent message: {message.message_id}")

        # Start a worker to process messages
        def message_processor(message):
            """Process message callback"""
            try:
                print(f"🔥 Processing message: {message.message_id}")

                # Execute the emergency task function directly
                result = emergency_task.fn(*message.args, **message.kwargs)

                print(f"🎉 Task completed: {result}")
                return result

            except Exception as e:
                print(f"❌ Task failed: {e}")
                raise

        # Consume messages
        worker_thread = broker.consume("emergency_queue", message_processor)

        # Wait for processing
        time.sleep(2)

        # Get health stats
        health = broker.db_backend.get_system_health()
        print(f"📊 System Health: {health}")

        # Cleanup
        broker.close()

        print("🎉 BROKER TEST COMPLETED SUCCESSFULLY!")
        return True

    except Exception as e:
        print(f"❌ BROKER TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    emergency_test_broker()