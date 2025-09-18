"""
System recovery and retry mechanisms
"""

import time
import logging
from typing import Dict, List, Optional
from core.persistence import get_persistence_manager
from core.message_bus import get_message_bus
from core.workflow_engine import get_workflow_engine
from core.tmux_client import TMUXClient
from agents.agent_bridge import get_bridge_manager

logger = logging.getLogger(__name__)


class RecoveryManager:
    """Manages system recovery and retry operations"""

    def __init__(self):
        self.persistence = get_persistence_manager()
        self.message_bus = get_message_bus()
        self.workflow_engine = get_workflow_engine()
        self.tmux = TMUXClient()
        self.bridge_manager = get_bridge_manager()

        logger.info("RecoveryManager initialized")

    def recover_system(self) -> Dict[str, any]:
        """Perform full system recovery"""
        logger.info("Starting system recovery...")
        results = {}

        # 1. Recover TMUX sessions
        results['sessions'] = self._recover_sessions()

        # 2. Recover message bus
        results['message_bus'] = self._recover_message_bus()

        # 3. Recover agent bridges
        results['bridges'] = self._recover_bridges()

        # 4. Recover pending tasks
        results['tasks'] = self._recover_pending_tasks()

        # 5. Recover incomplete workflows
        results['workflows'] = self._recover_incomplete_workflows()

        logger.info("System recovery complete")
        return results

    def _recover_sessions(self) -> Dict[str, bool]:
        """Recover TMUX sessions"""
        logger.info("Recovering TMUX sessions...")
        results = {}

        expected_sessions = [
            "claude-supervisor",
            "claude-master",
            "claude-backend-api",
            "claude-database",
            "claude-frontend-ui",
            "claude-testing",
            "claude-queue-manager",
            "claude-deployment",
            "claude-instagram"
        ]

        for session in expected_sessions:
            if not self.tmux.session_exists(session):
                try:
                    self.tmux.create_session(session)
                    logger.info(f"Recovered session: {session}")
                    results[session] = True
                except Exception as e:
                    logger.error(f"Failed to recover session {session}: {e}")
                    results[session] = False
            else:
                results[session] = True

        return results

    def _recover_message_bus(self) -> bool:
        """Ensure message bus is running"""
        logger.info("Recovering message bus...")

        if not self.message_bus.running:
            try:
                self.message_bus.start()
                logger.info("Message bus recovered")
                return True
            except Exception as e:
                logger.error(f"Failed to recover message bus: {e}")
                return False
        return True

    def _recover_bridges(self) -> Dict[str, bool]:
        """Recover agent bridges"""
        logger.info("Recovering agent bridges...")
        results = {}

        # Start all bridges
        try:
            self.bridge_manager.start_all()

            # Check each bridge
            for agent_name in ["supervisor", "backend-api", "database", "frontend-ui", "testing"]:
                bridge = self.bridge_manager.get_bridge(agent_name)
                if bridge and bridge.running:
                    results[agent_name] = True
                else:
                    # Try to restart individual bridge
                    try:
                        self.bridge_manager.restart_bridge(agent_name)
                        results[agent_name] = True
                        logger.info(f"Recovered bridge: {agent_name}")
                    except Exception as e:
                        logger.error(f"Failed to recover bridge {agent_name}: {e}")
                        results[agent_name] = False

        except Exception as e:
            logger.error(f"Failed to recover bridges: {e}")

        return results

    def _recover_pending_tasks(self) -> Dict[str, int]:
        """Retry pending tasks from persistence"""
        logger.info("Recovering pending tasks...")
        results = {"retried": 0, "failed": 0}

        # Get all pending tasks from persistence
        pending_tasks = self.persistence.get_pending_tasks()

        for task in pending_tasks:
            task_id = task['task_id']

            # Check if task is stale (older than 5 minutes)
            if time.time() - task.get('created_at', 0) > 300:
                try:
                    # Republish task to message bus
                    self.message_bus.publish_task(
                        agent=task['agent'],
                        task={
                            'command': task.get('command', ''),
                            'params': task.get('params', {}),
                            'original_task_id': task_id  # Keep reference
                        }
                    )

                    # Update original task status
                    self.persistence.update_task_status(
                        task_id=task_id,
                        status='retried',
                        error='Task was stale and has been retried'
                    )

                    results["retried"] += 1
                    logger.info(f"Retried stale task: {task_id}")

                except Exception as e:
                    logger.error(f"Failed to retry task {task_id}: {e}")
                    results["failed"] += 1

        logger.info(f"Task recovery: {results['retried']} retried, {results['failed']} failed")
        return results

    def _recover_incomplete_workflows(self) -> Dict[str, int]:
        """Recover incomplete workflow executions"""
        logger.info("Recovering incomplete workflows...")
        results = {"resumed": 0, "failed": 0}

        # Get incomplete executions from persistence
        incomplete = self.persistence.get_incomplete_executions()

        for execution in incomplete:
            execution_id = execution['execution_id']

            # Check if execution is stale (older than 10 minutes)
            if time.time() - execution.get('started_at', 0) > 600:
                try:
                    # Get workflow definition
                    workflow_id = execution['workflow_id']

                    # Mark as failed and create new execution
                    self.persistence.update_workflow_execution(
                        execution_id=execution_id,
                        status='failed',
                        error='Execution timed out and was marked as failed'
                    )

                    # Start new execution
                    new_execution_id = self.workflow_engine.execute(workflow_id)

                    results["resumed"] += 1
                    logger.info(f"Restarted stale workflow: {workflow_id} (new execution: {new_execution_id})")

                except Exception as e:
                    logger.error(f"Failed to recover workflow {execution_id}: {e}")
                    results["failed"] += 1

        logger.info(f"Workflow recovery: {results['resumed']} resumed, {results['failed']} failed")
        return results

    def retry_failed_task(self, task_id: str, max_retries: int = 3) -> bool:
        """Retry a specific failed task"""
        task = self.persistence.get_task(task_id)

        if not task:
            logger.error(f"Task {task_id} not found")
            return False

        if task['status'] != 'failed':
            logger.warning(f"Task {task_id} is not failed (status: {task['status']})")
            return False

        # Check retry count
        retry_count = task.get('retry_count', 0)
        if retry_count >= max_retries:
            logger.error(f"Task {task_id} has exceeded max retries ({max_retries})")
            return False

        try:
            # Republish task with incremented retry count
            new_task_id = self.message_bus.publish_task(
                agent=task['agent'],
                task={
                    'command': task.get('command', ''),
                    'params': task.get('params', {}),
                    'retry_count': retry_count + 1,
                    'original_task_id': task_id
                }
            )

            logger.info(f"Retried task {task_id} as {new_task_id} (retry {retry_count + 1}/{max_retries})")
            return True

        except Exception as e:
            logger.error(f"Failed to retry task {task_id}: {e}")
            return False

    def health_check(self) -> Dict[str, any]:
        """Perform system health check"""
        health = {
            "healthy": True,
            "components": {}
        }

        # Check TMUX sessions
        expected_sessions = ["claude-supervisor", "claude-backend-api", "claude-database"]
        for session in expected_sessions:
            exists = self.tmux.session_exists(session)
            health["components"][f"session_{session}"] = exists
            if not exists:
                health["healthy"] = False

        # Check message bus
        bus_running = self.message_bus.running
        health["components"]["message_bus"] = bus_running
        if not bus_running:
            health["healthy"] = False

        # Check persistence
        try:
            stats = self.persistence.get_statistics()
            health["components"]["persistence"] = True
            health["persistence_stats"] = stats
        except Exception as e:
            health["components"]["persistence"] = False
            health["healthy"] = False

        # Check for stale tasks
        pending_tasks = self.persistence.get_pending_tasks()
        stale_tasks = [
            t for t in pending_tasks
            if time.time() - t.get('created_at', 0) > 300
        ]
        health["stale_tasks"] = len(stale_tasks)
        if stale_tasks:
            health["needs_recovery"] = True

        return health

    def auto_recover(self) -> bool:
        """Automatically recover unhealthy components"""
        health = self.health_check()

        if health["healthy"]:
            logger.info("System is healthy, no recovery needed")
            return True

        logger.info("System is unhealthy, starting auto-recovery...")

        # Recover unhealthy components
        for component, status in health["components"].items():
            if not status:
                if component.startswith("session_"):
                    session = component.replace("session_", "")
                    try:
                        self.tmux.create_session(session)
                        logger.info(f"Auto-recovered session: {session}")
                    except Exception as e:
                        logger.error(f"Failed to auto-recover session {session}: {e}")

                elif component == "message_bus":
                    try:
                        self.message_bus.start()
                        logger.info("Auto-recovered message bus")
                    except Exception as e:
                        logger.error(f"Failed to auto-recover message bus: {e}")

        # Retry stale tasks if needed
        if health.get("needs_recovery"):
            self._recover_pending_tasks()

        # Re-check health
        new_health = self.health_check()
        return new_health["healthy"]


# Singleton instance
_recovery_manager = None

def get_recovery_manager() -> RecoveryManager:
    """Get or create recovery manager instance"""
    global _recovery_manager
    if _recovery_manager is None:
        _recovery_manager = RecoveryManager()
    return _recovery_manager