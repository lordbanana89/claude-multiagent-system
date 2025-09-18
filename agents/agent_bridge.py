"""
Fixed Agent Bridge - Corrects output capture and task completion
"""

import json
import time
import re
import threading
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

from core.tmux_client import TMUXClient
from core.message_bus import get_message_bus, Message, MessageType, MessagePriority
from config.settings import AGENT_SESSIONS, TMUX_COMMAND_DELAY
import dramatiq

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentTask:
    """Represents a task to be executed by an agent"""
    id: str
    agent: str
    command: str
    params: Dict[str, Any]
    timeout: int = 300
    retry_count: int = 0
    max_retries: int = 3


class AgentBridge:
    """
    Fixed bridge between TMUX sessions and message bus
    - Better output capture
    - Reliable completion detection
    - Proper error handling
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.session_name = AGENT_SESSIONS.get(agent_name)
        if not self.session_name:
            raise ValueError(f"Unknown agent: {agent_name}")

        self.tmux_client = TMUXClient()
        self.message_bus = get_message_bus()
        self.running = False
        self.current_task: Optional[AgentTask] = None

        logger.info(f"AgentBridge initialized for {agent_name} ({self.session_name})")

    def start(self):
        """Start the agent bridge"""
        self.running = True

        # Ensure TMUX session exists
        if not self.tmux_client.session_exists(self.session_name):
            self.tmux_client.create_session(self.session_name)
            logger.info(f"Created TMUX session: {self.session_name}")

        # Subscribe to task messages
        task_channel = f"bus:tasks:{self.agent_name}"
        self.message_bus.subscribe(task_channel, self._handle_task_message)

        # Update agent status
        self.message_bus.update_agent_status(
            self.agent_name,
            "ready",
            {"session": self.session_name, "bridge": "active"}
        )

        logger.info(f"Agent bridge started for {self.agent_name}")

    def stop(self):
        """Stop the agent bridge"""
        self.running = False
        self.message_bus.update_agent_status(
            self.agent_name,
            "stopped",
            {"session": self.session_name, "bridge": "inactive"}
        )
        logger.info(f"Agent bridge stopped for {self.agent_name}")

    def _handle_task_message(self, message: Message):
        """Handle incoming task message from message bus"""
        if message.type != MessageType.TASK:
            return

        task = AgentTask(
            id=message.id,
            agent=self.agent_name,
            command=message.payload.get('command', ''),
            params=message.payload.get('params', {}),
            timeout=message.payload.get('timeout', 300)
        )

        logger.info(f"Received task {task.id} for {self.agent_name}")
        self._execute_task(task)

    def _execute_task(self, task: AgentTask):
        """Execute task in TMUX session with improved output capture"""
        self.current_task = task
        start_time = time.time()

        # Update status to running
        self.message_bus.update_agent_status(
            self.agent_name,
            "busy",
            {"task_id": task.id, "command": task.command[:100]}
        )

        try:
            # Prepare command with markers
            command_lines = [
                f"echo '### TASK_START:{task.id}'",
                task.command,
                f"echo '### TASK_END:{task.id}'"
            ]

            # Clear the session first
            self.tmux_client.send_command(self.session_name, "clear")
            time.sleep(0.5)

            # Send commands
            for line in command_lines:
                logger.debug(f"Sending: {line}")
                self.tmux_client.send_command(self.session_name, line)
                time.sleep(0.2)  # Small delay between commands

            # Wait for completion with better detection
            success, output = self._wait_for_completion_improved(task.id, task.timeout)

            # Process result
            if success:
                result = self._parse_output(output, task.id)
                self.message_bus.publish_result(
                    task.id,
                    {
                        "agent": self.agent_name,
                        "command": task.command,
                        "output": result,
                        "duration": time.time() - start_time
                    },
                    success=True
                )
                logger.info(f"Task {task.id} completed successfully in {time.time()-start_time:.2f}s")
            else:
                self._handle_task_failure(task, output)

        except Exception as e:
            logger.error(f"Error executing task {task.id}: {e}")
            self._handle_task_failure(task, str(e))

        finally:
            self.current_task = None
            self.message_bus.update_agent_status(
                self.agent_name,
                "ready",
                {"last_task": task.id}
            )

    def _wait_for_completion_improved(self, task_id: str, timeout: int) -> tuple[bool, str]:
        """Improved completion detection that actually works"""
        start_time = time.time()
        end_marker = f"### TASK_END:{task_id}"
        last_output = ""
        no_change_count = 0

        while time.time() - start_time < timeout:
            # Capture current pane output
            current_output = self.tmux_client.capture_pane(self.session_name)

            # Check if output has changed
            if current_output == last_output:
                no_change_count += 1
                # If output hasn't changed for 3 checks and we have the end marker, we're done
                if no_change_count >= 3 and end_marker in current_output:
                    logger.debug(f"Task {task_id} completed (output stable)")
                    return True, current_output
            else:
                no_change_count = 0
                last_output = current_output

            # Check for completion marker
            if end_marker in current_output:
                # Wait a bit more to ensure all output is captured
                time.sleep(0.5)
                final_output = self.tmux_client.capture_pane(self.session_name)
                logger.debug(f"Task {task_id} completed (marker found)")
                return True, final_output

            # Check for error patterns
            if self._check_for_errors(current_output):
                logger.warning(f"Error detected in task {task_id}")
                return False, current_output

            time.sleep(0.5)  # Check every 500ms

        # Timeout
        logger.warning(f"Task {task_id} timed out after {timeout} seconds")
        final_output = self.tmux_client.capture_pane(self.session_name)
        return False, final_output

    def _check_for_errors(self, output: str) -> bool:
        """Check output for error patterns"""
        error_patterns = [
            r"command not found",
            r"No such file or directory",
            r"Permission denied",
            r"fatal:",
            r"FATAL:",
            r"Traceback \(most recent call last\):",
            r"SyntaxError:",
            r"NameError:",
            r"ImportError:"
        ]

        for pattern in error_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                return True
        return False

    def _parse_output(self, output: str, task_id: str) -> Dict[str, Any]:
        """Parse and structure the output"""
        # Extract task output between markers
        pattern = f"### TASK_START:{task_id}(.*?)### TASK_END:{task_id}"
        match = re.search(pattern, output, re.DOTALL)

        if match:
            task_output = match.group(1).strip()
            # Remove the echo commands and their prompts
            lines = task_output.split('\n')
            cleaned_lines = []
            for line in lines:
                # Skip prompt lines and echo commands
                if not line.startswith('erik@') and not line.startswith('echo '):
                    cleaned_lines.append(line)
            task_output = '\n'.join(cleaned_lines).strip()
        else:
            task_output = output

        # Structure the result
        result = {
            "raw_output": task_output,
            "lines": task_output.split('\n') if task_output else [],
            "success": True,
            "has_errors": self._check_for_errors(task_output)
        }

        # Try to extract structured data if present
        json_pattern = r'\{.*?\}'
        json_matches = re.findall(json_pattern, task_output, re.DOTALL)
        if json_matches:
            try:
                result["structured_data"] = json.loads(json_matches[-1])
            except json.JSONDecodeError:
                pass

        return result

    def _handle_task_failure(self, task: AgentTask, error: str):
        """Handle task failure with retry logic"""
        task.retry_count += 1

        if task.retry_count < task.max_retries:
            logger.warning(f"Task {task.id} failed, retrying ({task.retry_count}/{task.max_retries})")

            # Wait before retry with exponential backoff
            retry_delay = min(2 ** task.retry_count, 30)  # Max 30 seconds
            time.sleep(retry_delay)

            # Retry the task
            self._execute_task(task)
        else:
            logger.error(f"Task {task.id} failed after {task.max_retries} retries")
            self.message_bus.publish_result(
                task.id,
                {
                    "agent": self.agent_name,
                    "error": error,
                    "retry_count": task.retry_count
                },
                success=False
            )


class AgentBridgeManager:
    """Manages fixed agent bridges"""

    def __init__(self):
        self.bridges: Dict[str, AgentBridge] = {}
        self.message_bus = get_message_bus()

    def start_all(self):
        """Start bridges for all configured agents"""
        for agent_name in AGENT_SESSIONS.keys():
            try:
                bridge = AgentBridge(agent_name)
                bridge.start()
                self.bridges[agent_name] = bridge
                logger.info(f"Started bridge for {agent_name}")
            except Exception as e:
                logger.error(f"Failed to start bridge for {agent_name}: {e}")

    def stop_all(self):
        """Stop all agent bridges"""
        for agent_name, bridge in self.bridges.items():
            try:
                bridge.stop()
                logger.info(f"Stopped bridge for {agent_name}")
            except Exception as e:
                logger.error(f"Error stopping bridge for {agent_name}: {e}")

        self.bridges.clear()

    def get_bridge(self, agent_name: str) -> Optional[AgentBridge]:
        """Get bridge for specific agent"""
        return self.bridges.get(agent_name)


# Global manager instance
_bridge_manager = None

def get_bridge_manager() -> AgentBridgeManager:
    """Get or create singleton bridge manager"""
    global _bridge_manager
    if _bridge_manager is None:
        _bridge_manager = AgentBridgeManager()
    return _bridge_manager