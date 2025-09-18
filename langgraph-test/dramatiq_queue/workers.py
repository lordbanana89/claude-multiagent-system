"""
Production-Ready Dramatiq Workers
High-performance workers for emergency queue system
"""

import dramatiq
import os
import sys
import signal
import threading
import time
import logging
import json
import subprocess
import psutil
from typing import Dict, List, Any, Optional
from datetime import datetime
from multiprocessing import cpu_count
import redis

from .core import queue_manager, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


class WorkerManager:
    """Manages production-ready Dramatiq workers"""

    def __init__(self):
        self.workers: Dict[str, subprocess.Popen] = {}
        self.worker_stats: Dict[str, Dict[str, Any]] = {}
        self.monitoring_active = True
        self.start_time = datetime.now()

        # Determine optimal worker count
        self.cpu_count = cpu_count()
        self.optimal_workers = min(max(self.cpu_count - 1, 2), 8)  # Reserve 1 CPU, max 8 workers

        # Worker configuration based on priority queues
        self.worker_configs = {
            "emergency": {"processes": 2, "concurrency": 4, "max_tasks": 100},
            "urgent": {"processes": 2, "concurrency": 3, "max_tasks": 200},
            "high": {"processes": 1, "concurrency": 2, "max_tasks": 300},
            "default": {"processes": 2, "concurrency": 2, "max_tasks": 500},
            "low": {"processes": 1, "concurrency": 1, "max_tasks": 1000}
        }

        logger.info(f"🏭 WorkerManager initialized: {self.optimal_workers} optimal workers on {self.cpu_count} CPUs")

    def start_production_workers(self) -> Dict[str, Any]:
        """Start production-ready workers for all priority queues"""
        logger.info("🚀 EMERGENCY: Starting production workers...")

        results = {
            "started_workers": 0,
            "failed_workers": 0,
            "worker_processes": {},
            "start_time": datetime.now().isoformat()
        }

        for queue_name, config in self.worker_configs.items():
            try:
                worker_processes = self._start_queue_workers(queue_name, config)
                results["worker_processes"][queue_name] = worker_processes
                results["started_workers"] += len(worker_processes)
                logger.info(f"✅ Started {len(worker_processes)} workers for {queue_name} queue")

            except Exception as e:
                logger.error(f"❌ Failed to start workers for {queue_name}: {e}")
                results["failed_workers"] += 1

        # Start monitoring thread
        if results["started_workers"] > 0:
            monitor_thread = threading.Thread(target=self._monitor_workers, daemon=True)
            monitor_thread.start()

        logger.info(f"🎯 Production workers started: {results['started_workers']} total")
        return results

    def _start_queue_workers(self, queue_name: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Start workers for specific queue"""
        worker_processes = []

        for i in range(config["processes"]):
            try:
                # Build dramatiq worker command
                worker_cmd = [
                    sys.executable, "-m", "dramatiq",
                    "dramatiq_queue.core",  # Module with actors
                    "--queues", queue_name,
                    "--processes", "1",
                    "--threads", str(config["concurrency"]),
                    "--max-tasks", str(config["max_tasks"]),
                    "--log-level", "INFO"
                ]

                # Add Redis broker configuration
                redis_url = "redis://localhost:6379/0"
                worker_cmd.extend(["--broker", redis_url])

                # Start worker process
                process = subprocess.Popen(
                    worker_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                worker_id = f"{queue_name}_worker_{i}"
                worker_info = {
                    "worker_id": worker_id,
                    "queue_name": queue_name,
                    "process": process,
                    "pid": process.pid,
                    "started_at": datetime.now().isoformat(),
                    "command": " ".join(worker_cmd)
                }

                self.workers[worker_id] = process
                self.worker_stats[worker_id] = {
                    "queue": queue_name,
                    "pid": process.pid,
                    "started_at": datetime.now(),
                    "tasks_processed": 0,
                    "status": "running"
                }

                worker_processes.append(worker_info)
                logger.info(f"🔧 Started worker {worker_id} (PID: {process.pid}) for {queue_name}")

            except Exception as e:
                logger.error(f"❌ Failed to start worker {i} for {queue_name}: {e}")
                raise

        return worker_processes

    def _monitor_workers(self):
        """Monitor worker health and performance"""
        logger.info("👁️ Worker monitoring started")

        while self.monitoring_active:
            try:
                # Check each worker process
                for worker_id, process in list(self.workers.items()):
                    try:
                        # Check if process is still alive
                        poll_result = process.poll()

                        if poll_result is not None:
                            # Process has terminated
                            logger.warning(f"⚠️ Worker {worker_id} terminated (exit code: {poll_result})")
                            self.worker_stats[worker_id]["status"] = "terminated"
                            self.worker_stats[worker_id]["exit_code"] = poll_result

                            # Restart critical workers
                            if any(queue in worker_id for queue in ["emergency", "urgent", "high"]):
                                logger.info(f"🔄 Restarting critical worker {worker_id}")
                                self._restart_worker(worker_id)

                        else:
                            # Process is running, update stats
                            try:
                                proc = psutil.Process(process.pid)
                                self.worker_stats[worker_id].update({
                                    "status": "running",
                                    "cpu_percent": proc.cpu_percent(),
                                    "memory_mb": proc.memory_info().rss / 1024 / 1024,
                                    "last_check": datetime.now()
                                })
                            except psutil.NoSuchProcess:
                                logger.warning(f"⚠️ Worker {worker_id} process not found")

                    except Exception as e:
                        logger.error(f"❌ Error monitoring worker {worker_id}: {e}")

                time.sleep(10)  # Monitor every 10 seconds

            except Exception as e:
                logger.error(f"❌ Worker monitoring error: {e}")
                time.sleep(30)

    def _restart_worker(self, worker_id: str):
        """Restart a failed worker"""
        try:
            # Extract queue name from worker ID
            queue_name = worker_id.split('_worker_')[0]
            config = self.worker_configs.get(queue_name, self.worker_configs["default"])

            # Remove old worker
            if worker_id in self.workers:
                del self.workers[worker_id]

            # Start new worker
            new_workers = self._start_queue_workers(queue_name, {"processes": 1, **config})
            if new_workers:
                logger.info(f"✅ Restarted worker for {queue_name} queue")

        except Exception as e:
            logger.error(f"❌ Failed to restart worker {worker_id}: {e}")

    def get_worker_stats(self) -> Dict[str, Any]:
        """Get comprehensive worker statistics"""
        running_workers = sum(1 for stats in self.worker_stats.values() if stats["status"] == "running")
        total_memory = sum(stats.get("memory_mb", 0) for stats in self.worker_stats.values())
        avg_cpu = sum(stats.get("cpu_percent", 0) for stats in self.worker_stats.values()) / len(self.worker_stats) if self.worker_stats else 0

        return {
            "total_workers": len(self.workers),
            "running_workers": running_workers,
            "worker_details": dict(self.worker_stats),
            "total_memory_mb": total_memory,
            "average_cpu_percent": avg_cpu,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "timestamp": datetime.now().isoformat()
        }

    def emergency_scale_workers(self, queue_name: str, additional_workers: int) -> bool:
        """Emergency scaling of workers for high load"""
        logger.warning(f"🚨 EMERGENCY SCALING: Adding {additional_workers} workers to {queue_name}")

        try:
            config = self.worker_configs.get(queue_name, self.worker_configs["default"])
            scale_config = {"processes": additional_workers, **config}

            new_workers = self._start_queue_workers(f"{queue_name}_scaled", scale_config)
            logger.info(f"✅ Emergency scaling complete: {len(new_workers)} additional workers")
            return True

        except Exception as e:
            logger.error(f"❌ Emergency scaling failed: {e}")
            return False

    def shutdown_workers(self):
        """Graceful shutdown of all workers"""
        logger.info("🛑 Shutting down workers...")

        self.monitoring_active = False

        for worker_id, process in self.workers.items():
            try:
                # Send SIGTERM for graceful shutdown
                process.terminate()

                # Wait for graceful shutdown
                try:
                    process.wait(timeout=30)
                    logger.info(f"✅ Worker {worker_id} shutdown gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    process.kill()
                    logger.warning(f"⚠️ Force killed worker {worker_id}")

            except Exception as e:
                logger.error(f"❌ Error shutting down worker {worker_id}: {e}")

        self.workers.clear()
        self.worker_stats.clear()


# Global worker manager
worker_manager = WorkerManager()


def start_production_workers() -> Dict[str, Any]:
    """Start production workers for emergency queue system"""
    return worker_manager.start_production_workers()


def get_worker_stats() -> Dict[str, Any]:
    """Get current worker statistics"""
    return worker_manager.get_worker_stats()


def emergency_scale_workers(queue_name: str = "emergency", additional_workers: int = 2) -> bool:
    """Emergency worker scaling"""
    return worker_manager.emergency_scale_workers(queue_name, additional_workers)


def shutdown_workers():
    """Shutdown all workers"""
    worker_manager.shutdown_workers()


# Emergency task processing functions
def process_pending_requests_emergency():
    """Emergency processing of 507+ pending requests"""
    logger.warning("🚨 EMERGENCY: Processing 507+ pending requests")

    # Get all pending tasks
    pending_tasks = queue_manager.get_pending_tasks(limit=1000)

    if len(pending_tasks) > 500:
        logger.critical(f"🚨 CRITICAL: {len(pending_tasks)} pending tasks causing system instability")

        # Emergency drain queue
        drain_result = queue_manager.emergency_drain_queue()
        logger.info(f"🔧 Emergency drain result: {drain_result}")

        # Scale workers immediately
        emergency_scale_workers("emergency", 4)
        emergency_scale_workers("urgent", 2)

        return {
            "emergency_action": "queue_drained_and_scaled",
            "pending_tasks": len(pending_tasks),
            "drain_result": drain_result
        }

    return {
        "emergency_action": "monitoring",
        "pending_tasks": len(pending_tasks)
    }


if __name__ == "__main__":
    # Emergency worker startup
    print("🚨 EMERGENCY: Starting production workers...")

    # Check for high pending load
    emergency_result = process_pending_requests_emergency()
    print(f"⚡ Emergency check: {emergency_result}")

    # Start workers
    worker_result = start_production_workers()
    print(f"🏭 Worker startup: {worker_result}")

    # Show stats
    stats = get_worker_stats()
    print(f"📊 Worker stats: {stats}")

    print("✅ Emergency worker system operational!")