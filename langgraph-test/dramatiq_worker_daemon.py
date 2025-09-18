#!/usr/bin/env python3
"""
🚀 DRAMATIQ WORKER DAEMON
Background worker process for handling all Dramatiq queues
"""

import dramatiq
import signal
import sys
import time
import threading
import subprocess
import logging
from datetime import datetime
from dramatiq_broker import setup_emergency_dramatiq_system

# CRITICAL: Import all actors to register them with the broker
import dramatiq_agent_integration
from dramatiq_agent_integration import (
    notify_supervisor_new_request,
    execute_approved_command,
    notify_agent_request_result,
    agent_manager
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DramatiqWorkerDaemon:
    """🚀 Complete Dramatiq worker daemon"""

    def __init__(self):
        self.broker = setup_emergency_dramatiq_system()
        self.workers = {}
        self.running = True

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("🚀 DramatiqWorkerDaemon initialized")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"📡 Received signal {signum}, shutting down gracefully...")
        self.shutdown()

    def start_workers(self):
        """🚀 Start worker threads for all queues"""

        # Define queue configurations
        queue_configs = [
            {"name": "supervisor", "workers": 2, "description": "Supervisor notifications"},
            {"name": "execution", "workers": 3, "description": "Command execution"},
            {"name": "notifications", "workers": 2, "description": "Agent notifications"},
            {"name": "emergency", "workers": 2, "description": "Emergency tasks"},
            {"name": "urgent", "workers": 2, "description": "Urgent tasks"},
            {"name": "high", "workers": 1, "description": "High priority tasks"},
            {"name": "default", "workers": 2, "description": "Normal tasks"},
            {"name": "low", "workers": 1, "description": "Low priority tasks"}
        ]

        for config in queue_configs:
            queue_name = config["name"]
            worker_count = config["workers"]

            logger.info(f"🔥 Starting {worker_count} workers for {queue_name} queue")

            for i in range(worker_count):
                worker_id = f"{queue_name}_worker_{i+1}"

                # Create worker thread
                worker_thread = threading.Thread(
                    target=self._worker_loop,
                    args=(queue_name, worker_id),
                    daemon=True,
                    name=worker_id
                )

                worker_thread.start()
                self.workers[worker_id] = {
                    "thread": worker_thread,
                    "queue": queue_name,
                    "started_at": datetime.now(),
                    "processed_count": 0,
                    "failed_count": 0
                }

        logger.info(f"✅ Started {len(self.workers)} workers across {len(queue_configs)} queues")

    def _worker_loop(self, queue_name: str, worker_id: str):
        """🔥 Main worker loop for processing messages"""

        logger.info(f"🔥 Worker {worker_id} started for {queue_name} queue")

        while self.running:
            try:
                # Process one message
                processed = self.broker.do_work(queue_name, timeout=5000)

                if processed:
                    self.workers[worker_id]["processed_count"] += 1
                    logger.info(f"✅ {worker_id} processed message from {queue_name}")
                else:
                    # No message available, brief sleep
                    time.sleep(0.1)

            except Exception as e:
                self.workers[worker_id]["failed_count"] += 1
                logger.error(f"❌ {worker_id} error: {e}")
                time.sleep(1)  # Longer sleep on error

        logger.info(f"🛑 Worker {worker_id} stopped")

    def start_monitoring(self):
        """📊 Start monitoring thread"""

        def monitor_loop():
            while self.running:
                try:
                    # Log worker statistics every 30 seconds
                    total_processed = sum(w["processed_count"] for w in self.workers.values())
                    total_failed = sum(w["failed_count"] for w in self.workers.values())
                    active_workers = sum(1 for w in self.workers.values() if w["thread"].is_alive())

                    # Get system health
                    health = self.broker.db_backend.get_system_health()

                    logger.info(f"📊 WORKER STATS: {active_workers} active, {total_processed} processed, {total_failed} failed")
                    logger.info(f"📊 QUEUE HEALTH: {health['queue_totals']}")

                    # Check for stuck workers
                    for worker_id, worker_info in self.workers.items():
                        if not worker_info["thread"].is_alive():
                            logger.warning(f"⚠️ Worker {worker_id} died, restarting...")
                            # TODO: Restart dead workers

                    time.sleep(30)  # Monitor every 30 seconds

                except Exception as e:
                    logger.error(f"❌ Monitor error: {e}")
                    time.sleep(60)

        monitor_thread = threading.Thread(target=monitor_loop, daemon=True, name="monitor")
        monitor_thread.start()

        logger.info("📊 Monitoring thread started")

    def run(self):
        """🚀 Main daemon run method"""

        logger.info("🚀 Starting Dramatiq Worker Daemon...")

        try:
            # Start workers
            self.start_workers()

            # Start monitoring
            self.start_monitoring()

            # Keep main thread alive
            logger.info("✅ Dramatiq Worker Daemon running - Press Ctrl+C to stop")

            while self.running:
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("📡 Keyboard interrupt received")
        except Exception as e:
            logger.error(f"❌ Daemon error: {e}")
        finally:
            self.shutdown()

    def shutdown(self):
        """🛑 Graceful shutdown"""

        if not self.running:
            return

        logger.info("🛑 Shutting down Dramatiq Worker Daemon...")
        self.running = False

        # Wait for workers to finish current tasks
        logger.info("⏳ Waiting for workers to finish...")

        for worker_id, worker_info in self.workers.items():
            thread = worker_info["thread"]
            if thread.is_alive():
                thread.join(timeout=10)
                if thread.is_alive():
                    logger.warning(f"⚠️ Worker {worker_id} did not stop gracefully")

        # Close broker
        if self.broker:
            self.broker.close()

        # Close agent manager
        if agent_manager:
            agent_manager.close()

        logger.info("✅ Dramatiq Worker Daemon shutdown complete")

def main():
    """🚀 Main entry point"""

    print("🚀 DRAMATIQ WORKER DAEMON")
    print("=" * 50)
    print("🔥 High-performance queue worker system")
    print("📋 Handles all agent requests via Dramatiq")
    print("⚡ Replaces tmux subprocess architecture")
    print("=" * 50)

    # Create and run daemon
    daemon = DramatiqWorkerDaemon()
    daemon.run()

if __name__ == "__main__":
    main()