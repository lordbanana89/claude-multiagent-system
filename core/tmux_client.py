"""
TMUX Client Helper - Centralized TMUX interaction with mandatory delays
CRITICAL: The delay between send-keys commands is MANDATORY to prevent race conditions
"""

import subprocess
import time
import logging
from typing import Optional, List, Dict, Tuple
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import TMUX_BIN, TMUX_COMMAND_DELAY, AGENT_SESSIONS, DEBUG

# Configure logging
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger(__name__)


class TMUXClient:
    """
    Centralized TMUX client with mandatory delay enforcement

    CRITICAL: Never bypass the delay in send_command() - it prevents 30-40% command loss
    """

    @staticmethod
    def send_command(session: str, command: str, delay: float = None) -> bool:
        """
        Send command to TMUX session with MANDATORY delay

        Args:
            session: TMUX session name
            command: Command to send
            delay: Optional custom delay (defaults to TMUX_COMMAND_DELAY)

        Returns:
            True if successful, False otherwise

        WARNING: DO NOT REMOVE OR REDUCE THE DELAY - IT IS CRITICAL FOR RELIABILITY
        """
        if delay is None:
            delay = TMUX_COMMAND_DELAY

        try:
            # Log the command being sent
            logger.debug(f"Sending to {session}: {command[:100]}...")

            # Step 1: Send the command text
            result = subprocess.run(
                [TMUX_BIN, "send-keys", "-t", session, command],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                logger.error(f"Failed to send command: {result.stderr}")
                return False

            # Step 2: MANDATORY DELAY - DO NOT REMOVE
            # This prevents race conditions where Enter is sent before command is processed
            time.sleep(delay)

            # Step 3: Send Enter key
            result = subprocess.run(
                [TMUX_BIN, "send-keys", "-t", session, "Enter"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                logger.error(f"Failed to send Enter: {result.stderr}")
                return False

            logger.debug(f"Command sent successfully to {session}")
            return True

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout sending command to {session}")
            return False
        except Exception as e:
            logger.error(f"Error sending command to {session}: {e}")
            return False

    @staticmethod
    def send_keys(session: str, keys: str) -> bool:
        """
        Send raw keys without Enter (for special key sequences)

        Args:
            session: TMUX session name
            keys: Keys to send (e.g., "C-c" for Ctrl+C)

        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                [TMUX_BIN, "send-keys", "-t", session, keys],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error sending keys to {session}: {e}")
            return False

    @staticmethod
    def send_command_raw(session: str, keys: str) -> bool:
        """
        Alias for send_keys() for backward compatibility

        Args:
            session: TMUX session name
            keys: Keys to send (e.g., "C-c" for Ctrl+C)

        Returns:
            True if successful, False otherwise
        """
        return TMUXClient.send_keys(session, keys)

    @staticmethod
    def capture_pane(session: str, lines: Optional[int] = None) -> Optional[str]:
        """
        Capture output from TMUX pane

        Args:
            session: TMUX session name
            lines: Optional number of recent lines to capture (default: all)

        Returns:
            Captured text or None if failed
        """
        try:
            cmd = [TMUX_BIN, "capture-pane", "-t", session, "-p"]
            if lines:
                cmd.extend(["-S", f"-{lines}"])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return result.stdout
            else:
                logger.error(f"Failed to capture pane: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout capturing pane from {session}")
            return None
        except Exception as e:
            logger.error(f"Error capturing pane from {session}: {e}")
            return None

    @staticmethod
    def session_exists(session: str) -> bool:
        """
        Check if TMUX session exists

        Args:
            session: TMUX session name

        Returns:
            True if session exists, False otherwise
        """
        try:
            result = subprocess.run(
                [TMUX_BIN, "has-session", "-t", session],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def create_session(session: str, command: Optional[str] = None,
                      detached: bool = True) -> bool:
        """
        Create new TMUX session

        Args:
            session: Session name to create
            command: Optional command to run in session
            detached: Whether to create in detached mode

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = [TMUX_BIN, "new-session"]

            if detached:
                cmd.append("-d")

            cmd.extend(["-s", session])

            if command:
                cmd.append(command)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                logger.info(f"Created session: {session}")
                return True
            else:
                logger.error(f"Failed to create session: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error creating session {session}: {e}")
            return False

    @staticmethod
    def kill_session(session: str) -> bool:
        """
        Kill TMUX session

        Args:
            session: Session name to kill

        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                [TMUX_BIN, "kill-session", "-t", session],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.info(f"Killed session: {session}")
                return True
            else:
                # Session might not exist, which is okay
                logger.debug(f"Could not kill session {session}: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error killing session {session}: {e}")
            return False

    @staticmethod
    def list_sessions() -> List[str]:
        """
        List all TMUX sessions

        Returns:
            List of session names
        """
        try:
            result = subprocess.run(
                [TMUX_BIN, "list-sessions", "-F", "#{session_name}"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return [s.strip() for s in result.stdout.splitlines() if s.strip()]
            else:
                return []

        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []

    @staticmethod
    def get_session_info(session: str) -> Optional[Dict]:
        """
        Get detailed information about a session

        Args:
            session: Session name

        Returns:
            Dictionary with session info or None if not found
        """
        try:
            # Check if session exists
            if not TMUXClient.session_exists(session):
                return None

            # Get session details
            result = subprocess.run(
                [TMUX_BIN, "list-sessions", "-t", session,
                 "-F", "#{session_name}:#{session_created}:#{session_attached}"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                parts = result.stdout.strip().split(':')
                if len(parts) >= 3:
                    return {
                        "name": parts[0],
                        "created": parts[1],
                        "attached": parts[2] == "1"
                    }

            return None

        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return None

    @staticmethod
    def send_to_agent(agent_id: str, command: str) -> bool:
        """
        Send command to specific agent by ID

        Args:
            agent_id: Agent identifier
            command: Command to send

        Returns:
            True if successful, False otherwise
        """
        session = AGENT_SESSIONS.get(agent_id)
        if not session:
            logger.error(f"Unknown agent ID: {agent_id}")
            return False

        return TMUXClient.send_command(session, command)

    @staticmethod
    def capture_agent_output(agent_id: str, lines: Optional[int] = None) -> Optional[str]:
        """
        Capture output from specific agent

        Args:
            agent_id: Agent identifier
            lines: Optional number of recent lines

        Returns:
            Captured text or None if failed
        """
        session = AGENT_SESSIONS.get(agent_id)
        if not session:
            logger.error(f"Unknown agent ID: {agent_id}")
            return None

        return TMUXClient.capture_pane(session, lines)

    @staticmethod
    def broadcast_to_agents(command: str, exclude: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Broadcast command to all agents

        Args:
            command: Command to broadcast
            exclude: Optional list of agent IDs to exclude

        Returns:
            Dictionary mapping agent_id to success status
        """
        results = {}
        exclude = exclude or []

        for agent_id, session in AGENT_SESSIONS.items():
            if agent_id in exclude:
                continue

            results[agent_id] = TMUXClient.send_command(session, command)

        return results

    @staticmethod
    def restart_session(session: str, command: Optional[str] = None) -> bool:
        """
        Restart a TMUX session (kill and recreate)

        Args:
            session: Session name
            command: Optional command to run in new session

        Returns:
            True if successful, False otherwise
        """
        # Kill existing session
        TMUXClient.kill_session(session)

        # Small delay to ensure cleanup
        time.sleep(0.5)

        # Create new session
        return TMUXClient.create_session(session, command)

    @staticmethod
    def health_check() -> Dict[str, bool]:
        """
        Check health of all agent sessions

        Returns:
            Dictionary mapping agent_id to health status
        """
        health = {}

        for agent_id, session in AGENT_SESSIONS.items():
            health[agent_id] = TMUXClient.session_exists(session)

        return health


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def send_to_supervisor(command: str) -> bool:
    """Send command to supervisor agent"""
    return TMUXClient.send_to_agent("supervisor", command)

def send_to_all_agents(command: str, exclude_supervisor: bool = True) -> Dict[str, bool]:
    """Send command to all agents"""
    exclude = ["supervisor"] if exclude_supervisor else []
    return TMUXClient.broadcast_to_agents(command, exclude)

def get_all_agent_outputs(lines: int = 10) -> Dict[str, str]:
    """Get recent output from all agents"""
    outputs = {}
    for agent_id in AGENT_SESSIONS.keys():
        output = TMUXClient.capture_agent_output(agent_id, lines)
        if output:
            outputs[agent_id] = output
    return outputs

def restart_all_agents(command: str = "claude") -> Dict[str, bool]:
    """Restart all agent sessions"""
    results = {}
    for agent_id, session in AGENT_SESSIONS.items():
        results[agent_id] = TMUXClient.restart_session(session, command)
    return results


# ============================================================================
# TESTING & VALIDATION
# ============================================================================

if __name__ == "__main__":
    print("🧪 Testing TMUX Client...")
    print(f"📍 TMUX Binary: {TMUX_BIN}")
    print(f"⏱️  Command Delay: {TMUX_COMMAND_DELAY}s")
    print(f"🤖 Configured Agents: {len(AGENT_SESSIONS)}")

    # Test listing sessions
    sessions = TMUXClient.list_sessions()
    print(f"\n📋 Active Sessions: {sessions}")

    # Test health check
    health = TMUXClient.health_check()
    print(f"\n💚 Agent Health:")
    for agent_id, is_healthy in health.items():
        status = "✅" if is_healthy else "❌"
        print(f"  {status} {agent_id}")

    # Test creating a test session
    test_session = "tmux-client-test"
    if TMUXClient.create_session(test_session, "echo 'Test session created'"):
        print(f"\n✅ Created test session: {test_session}")

        # Test sending command
        if TMUXClient.send_command(test_session, "echo 'Hello from TMUX client!'"):
            print("✅ Command sent successfully")

            # Wait for command to execute
            time.sleep(0.5)

            # Capture output
            output = TMUXClient.capture_pane(test_session, lines=5)
            if output:
                print(f"📤 Captured output:\n{output}")

        # Clean up
        if TMUXClient.kill_session(test_session):
            print(f"✅ Cleaned up test session")

    print("\n✅ TMUX Client testing complete!")