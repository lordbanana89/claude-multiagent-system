"""
Dramatiq Actors - Queue-based task processing for Claude Multi-Agent System
"""

import dramatiq
import json
import logging
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.tmux_client import TMUXClient
from config.settings import AGENT_SESSIONS, DEBUG
from task_queue.broker import broker

# Configure logging
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger(__name__)


@dramatiq.actor(max_retries=3, min_backoff=1000, max_backoff=60000)
def process_agent_command(agent_id: str, command: str, task_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a command for a specific agent via TMUX

    Args:
        agent_id: Agent identifier (e.g., 'backend-api', 'supervisor')
        command: Command to send to the agent
        task_id: Optional task ID for tracking

    Returns:
        Dictionary with execution result
    """
    logger.info(f"Processing command for {agent_id}: {command[:100]}...")

    # Get TMUX session name for agent
    session_name = AGENT_SESSIONS.get(agent_id)
    if not session_name:
        error_msg = f"Unknown agent: {agent_id}"
        logger.error(error_msg)
        return {
            "success": False,
            "agent_id": agent_id,
            "error": error_msg,
            "task_id": task_id
        }

    # Check if session exists
    if not TMUXClient.session_exists(session_name):
        error_msg = f"Session {session_name} not found for agent {agent_id}"
        logger.error(error_msg)
        return {
            "success": False,
            "agent_id": agent_id,
            "error": error_msg,
            "task_id": task_id
        }

    # Send command via TMUXClient
    success = TMUXClient.send_command(session_name, command)

    result = {
        "success": success,
        "agent_id": agent_id,
        "session": session_name,
        "command": command[:100] + "..." if len(command) > 100 else command,
        "task_id": task_id,
        "timestamp": time.time()
    }

    if success:
        logger.info(f"✅ Command sent to {agent_id}")
    else:
        logger.error(f"❌ Failed to send command to {agent_id}")
        result["error"] = "Failed to send command via TMUX"

    return result


@dramatiq.actor(max_retries=1)
def broadcast_message(message: str, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Broadcast a message to all agents (except excluded ones)

    Args:
        message: Message to broadcast
        exclude: List of agent IDs to exclude from broadcast

    Returns:
        Dictionary with broadcast results
    """
    logger.info(f"Broadcasting message: {message[:100]}...")

    exclude = exclude or []
    results = {}
    success_count = 0
    failure_count = 0

    for agent_id, session_name in AGENT_SESSIONS.items():
        # Skip excluded agents
        if agent_id in exclude:
            results[agent_id] = {"skipped": True}
            continue

        # Check if session exists
        if not TMUXClient.session_exists(session_name):
            results[agent_id] = {
                "success": False,
                "error": f"Session {session_name} not found"
            }
            failure_count += 1
            continue

        # Format broadcast message
        broadcast_cmd = f'echo "📢 [BROADCAST] {message}"'

        # Send via TMUXClient
        success = TMUXClient.send_command(session_name, broadcast_cmd)

        results[agent_id] = {"success": success}
        if success:
            success_count += 1
        else:
            failure_count += 1
            results[agent_id]["error"] = "Failed to send via TMUX"

    logger.info(f"Broadcast complete: {success_count} success, {failure_count} failures")

    return {
        "message": message,
        "total_agents": len(AGENT_SESSIONS),
        "excluded": len(exclude),
        "success_count": success_count,
        "failure_count": failure_count,
        "results": results,
        "timestamp": time.time()
    }


@dramatiq.actor(max_retries=5, min_backoff=2000, max_backoff=120000)
def execute_task(task_definition: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a complex task that may involve multiple agents

    Args:
        task_definition: Dictionary defining the task:
            - task_id: Unique task identifier
            - task_type: Type of task to execute
            - agents: List of agents involved
            - steps: List of steps to execute
            - config: Additional configuration

    Returns:
        Dictionary with execution results
    """
    task_id = task_definition.get("task_id", "unknown")
    logger.info(f"Executing task {task_id}")

    results = {
        "task_id": task_id,
        "started_at": time.time(),
        "steps": [],
        "success": True
    }

    try:
        steps = task_definition.get("steps", [])

        for i, step in enumerate(steps, 1):
            step_result = {
                "step": i,
                "description": step.get("description", f"Step {i}"),
                "agent_id": step.get("agent_id"),
                "command": step.get("command"),
            }

            # Execute step command if provided
            if step.get("agent_id") and step.get("command"):
                # Use process_agent_command for individual steps
                cmd_result = process_agent_command(
                    step["agent_id"],
                    step["command"],
                    task_id
                )
                step_result["result"] = cmd_result
                step_result["success"] = cmd_result.get("success", False)

                if not step_result["success"]:
                    results["success"] = False
                    if not step.get("continue_on_failure", False):
                        logger.warning(f"Task {task_id} failed at step {i}")
                        break

            # Add delay between steps if specified
            delay = step.get("delay", 0)
            if delay > 0:
                time.sleep(delay)

            results["steps"].append(step_result)

    except Exception as e:
        logger.error(f"Task {task_id} failed with exception: {e}")
        results["success"] = False
        results["error"] = str(e)

    results["completed_at"] = time.time()
    results["duration"] = results["completed_at"] - results["started_at"]

    logger.info(f"Task {task_id} completed: success={results['success']}")
    return results


@dramatiq.actor(max_retries=2)
def notify_agent(agent_id: str, notification: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a notification to a specific agent

    Args:
        agent_id: Target agent ID
        notification: Notification data including:
            - type: Notification type (info, warning, error, task)
            - title: Notification title
            - message: Notification message
            - priority: Priority level (low, medium, high, critical)
            - data: Additional data

    Returns:
        Dictionary with notification result
    """
    logger.info(f"Notifying {agent_id}: {notification.get('title', 'Notification')}")

    # Get session name
    session_name = AGENT_SESSIONS.get(agent_id)
    if not session_name:
        error_msg = f"Unknown agent: {agent_id}"
        logger.error(error_msg)
        return {
            "success": False,
            "agent_id": agent_id,
            "error": error_msg
        }

    # Format notification message
    notif_type = notification.get("type", "info").upper()
    priority = notification.get("priority", "medium").upper()
    title = notification.get("title", "Notification")
    message = notification.get("message", "")

    # Choose icon based on type
    icons = {
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "TASK": "📋",
        "SUCCESS": "✅"
    }
    icon = icons.get(notif_type, "📬")

    # Build notification command
    notif_cmd = f'echo "{icon} [{priority}] {title}: {message}"'

    # Send notification
    success = TMUXClient.send_command(session_name, notif_cmd)

    result = {
        "success": success,
        "agent_id": agent_id,
        "session": session_name,
        "notification": notification,
        "timestamp": time.time()
    }

    if success:
        logger.info(f"✅ Notification sent to {agent_id}")
    else:
        logger.error(f"❌ Failed to send notification to {agent_id}")
        result["error"] = "Failed to send notification via TMUX"

    return result


@dramatiq.actor(queue_name="dead_letter_queue", max_retries=0)
def handle_failed_task(message_data: Dict[str, Any]):
    """
    Handle tasks that failed after all retries
    This actor processes messages from the Dead Letter Queue

    Args:
        message_data: Failed message information
    """
    logger.error(f"📥 DLQ Handler received failed task: {message_data}")

    # Log to file for persistence
    dlq_log_file = Path("logs") / "dlq_tasks.jsonl"
    dlq_log_file.parent.mkdir(exist_ok=True)

    try:
        with open(dlq_log_file, "a") as f:
            log_entry = {
                "timestamp": time.time(),
                "failed_task": message_data,
            }
            f.write(json.dumps(log_entry) + "\n")
        logger.info(f"Failed task logged to {dlq_log_file}")
    except Exception as e:
        logger.error(f"Failed to log DLQ message: {e}")


# Health check function
def check_actors_health() -> Dict[str, Any]:
    """
    Check health of all actors and queue system

    Returns:
        Dictionary with health status
    """
    health = {
        "status": "healthy",
        "actors": {
            "process_agent_command": "registered",
            "broadcast_message": "registered",
            "execute_task": "registered",
            "notify_agent": "registered",
            "handle_failed_task": "registered"
        },
        "broker": {
            "type": type(broker).__name__,
            "connected": True  # Assume connected if we got this far
        },
        "agents_available": len(AGENT_SESSIONS),
        "timestamp": time.time()
    }

    # Check if any TMUX sessions exist
    active_sessions = 0
    for agent_id, session_name in AGENT_SESSIONS.items():
        if TMUXClient.session_exists(session_name):
            active_sessions += 1

    health["active_sessions"] = active_sessions

    if active_sessions == 0:
        health["status"] = "degraded"
        health["warning"] = "No active TMUX sessions found"

    return health


if __name__ == "__main__":
    # Test actors health
    print("🧪 Testing Dramatiq actors...")
    health = check_actors_health()

    print("\n📊 Actors Health Check:")
    print(f"  Status: {health['status']}")
    print(f"  Actors registered: {len(health['actors'])}")
    print(f"  Broker type: {health['broker']['type']}")
    print(f"  Available agents: {health['agents_available']}")
    print(f"  Active TMUX sessions: {health['active_sessions']}")

    if health.get("warning"):
        print(f"  ⚠️ Warning: {health['warning']}")

    print("\n✅ Actors module ready!")