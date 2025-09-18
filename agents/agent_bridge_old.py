"""
Agent Bridge - Connects TMUX agents with Dramatiq queue and Message Bus
Enables real task execution in TMUX sessions from queue messages
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
    Bridge between TMUX sessions and Dramatiq queue
    - Receives tasks from queue
    - Executes commands in TMUX
    - Captures output
    - Publishes results
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

        # Output capture
        self.output_buffer = []
        self.capture_thread = None

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
        """Execute task in TMUX session"""
        self.current_task = task
        start_time = time.time()

        # Update status to running
        self.message_bus.update_agent_status(
            self.agent_name,
            "busy",
            {"task_id": task.id, "command": task.command[:100]}
        )

        try:
            # Prepare command with parameters
            command = self._prepare_command(task.command, task.params)

            # Clear output buffer
            self.output_buffer = []

            # Start output capture in background
            self.capture_thread = threading.Thread(
                target=self._capture_output_loop,
                args=(task.id,)
            )
            self.capture_thread.start()

            # Send command to TMUX
            logger.info(f"Executing in TMUX: {command[:200]}")

            # Send multi-line commands properly
            for line in command.split('\n'):
                if line.strip():  # Skip empty lines
                    self.tmux_client.send_command(self.session_name, line)
                    time.sleep(0.1)  # Small delay between lines

            # Wait for completion or timeout
            success, output = self._wait_for_completion(task.timeout)

            # Process result
            if success:
                result = self._parse_output(output)
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
                logger.info(f"Task {task.id} completed successfully")
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

    def _prepare_command(self, command_template: str, params: Dict[str, Any]) -> str:
        """Prepare command by substituting parameters"""
        command = command_template

        # Replace placeholders with parameters
        for key, value in params.items():
            placeholder = f"{{{key}}}"
            if placeholder in command:
                command = command.replace(placeholder, str(value))

        # Add task tracking marker if we have a current task
        if self.current_task:
            command = f"echo '### TASK_START:{self.current_task.id}'\n{command}\necho '### TASK_END:{self.current_task.id}'"
        else:
            # Fallback for testing
            command = f"echo '### TASK_START'\n{command}\necho '### TASK_END'"

        return command

    def _capture_output_loop(self, task_id: str):
        """Continuously capture output from TMUX session"""
        last_output = ""
        while self.current_task and self.current_task.id == task_id:
            try:
                # Capture current pane content
                output = self.tmux_client.capture_pane(self.session_name)

                # Check for new content
                if output != last_output:
                    new_lines = self._get_new_lines(last_output, output)
                    if new_lines:
                        self.output_buffer.extend(new_lines)

                        # Stream output to message bus
                        self.message_bus.broadcast_event(
                            "agent_output",
                            {
                                "agent": self.agent_name,
                                "task_id": task_id,
                                "output": new_lines
                            }
                        )

                    last_output = output

                time.sleep(0.5)  # Check every 500ms

            except Exception as e:
                logger.error(f"Error capturing output: {e}")
                break

    def _get_new_lines(self, old_output: str, new_output: str) -> List[str]:
        """Extract new lines from output"""
        old_lines = old_output.split('\n')
        new_lines = new_output.split('\n')

        # Find new content
        if len(new_lines) > len(old_lines):
            return new_lines[len(old_lines):]

        # Check if last line changed (partial output)
        if old_lines and new_lines and old_lines[-1] != new_lines[-1]:
            return [new_lines[-1]]

        return []

    def _wait_for_completion(self, timeout: int) -> tuple[bool, str]:
        """Wait for task completion or timeout"""
        start_time = time.time()
        task_id = self.current_task.id

        while time.time() - start_time < timeout:
            # Get current output
            output = '\n'.join(self.output_buffer)

            # Check for completion markers
            if f"### TASK_END:{task_id}" in output:
                return True, output

            # Check for error patterns
            error_patterns = [
                r"Error:",
                r"Exception:",
                r"Failed:",
                r"FATAL:",
                r"Traceback \(most recent call last\):"
            ]

            for pattern in error_patterns:
                if re.search(pattern, output, re.IGNORECASE):
                    logger.warning(f"Error pattern detected in output: {pattern}")
                    # Continue anyway as some errors might be recoverable

            # Check for common completion patterns
            completion_patterns = [
                r"Done\.",
                r"Completed\.",
                r"Finished\.",
                r"Success\.",
                f"TASK_END:{task_id}"
            ]

            for pattern in completion_patterns:
                if re.search(pattern, output, re.IGNORECASE | re.MULTILINE):
                    return True, output

            time.sleep(1)

        # Timeout
        logger.warning(f"Task {task_id} timed out after {timeout} seconds")
        return False, '\n'.join(self.output_buffer)

    def _parse_output(self, output: str) -> Dict[str, Any]:
        """Parse and structure the output"""
        # Get task_id safely
        task_id = self.current_task.id if self.current_task else "unknown"

        # Extract task output between markers
        pattern = f"### TASK_START:{task_id}(.*?)### TASK_END:{task_id}"
        match = re.search(pattern, output, re.DOTALL)

        # Also try generic markers as fallback
        if not match and task_id == "unknown":
            pattern = r"### TASK_START(.*?)### TASK_END"
            match = re.search(pattern, output, re.DOTALL)

        if match:
            task_output = match.group(1).strip()
        else:
            task_output = output

        # Try to extract structured data if present
        result = {
            "raw_output": task_output,
            "lines": task_output.split('\n'),
            "success": True
        }

        # Look for JSON output
        json_pattern = r'\{.*?\}'
        json_matches = re.findall(json_pattern, task_output, re.DOTALL)
        if json_matches:
            try:
                # Try to parse the last JSON object
                result["structured_data"] = json.loads(json_matches[-1])
            except json.JSONDecodeError:
                pass

        return result

    def _handle_task_failure(self, task: AgentTask, error: str):
        """Handle task failure with retry logic"""
        task.retry_count += 1

        if task.retry_count < task.max_retries:
            logger.warning(f"Task {task.id} failed, retrying ({task.retry_count}/{task.max_retries})")

            # Schedule retry with exponential backoff
            retry_delay = 2 ** task.retry_count
            threading.Timer(retry_delay, lambda: self._execute_task(task)).start()
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
    """Manages all agent bridges"""

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

    def restart_bridge(self, agent_name: str):
        """Restart bridge for specific agent"""
        if agent_name in self.bridges:
            self.bridges[agent_name].stop()

        bridge = AgentBridge(agent_name)
        bridge.start()
        self.bridges[agent_name] = bridge
        logger.info(f"Restarted bridge for {agent_name}")


# Global manager instance
_bridge_manager = None

def get_bridge_manager() -> AgentBridgeManager:
    """Get or create singleton bridge manager"""
    global _bridge_manager
    if _bridge_manager is None:
        _bridge_manager = AgentBridgeManager()
    return _bridge_manager