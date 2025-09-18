"""
Tests for TMUX Client Helper
Verify that the delay is properly enforced
"""

import pytest
import time
from unittest.mock import patch, MagicMock, call
import subprocess
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tmux_client import TMUXClient


class TestTMUXClient:
    """Test suite for TMUXClient"""

    def test_send_command_enforces_delay(self):
        """Test that send_command enforces mandatory delay between commands"""
        with patch('subprocess.run') as mock_run:
            with patch('time.sleep') as mock_sleep:
                mock_run.return_value.returncode = 0

                # Send command
                result = TMUXClient.send_command("test-session", "echo test")

                # Verify success
                assert result is True

                # Verify delay was called
                mock_sleep.assert_called_once_with(0.1)

                # Verify two subprocess calls (command + Enter)
                assert mock_run.call_count == 2

                # Verify correct command sequence
                calls = mock_run.call_args_list
                assert "send-keys" in calls[0][0][0]
                assert "test-session" in calls[0][0][0]
                assert "echo test" in calls[0][0][0]

                assert "send-keys" in calls[1][0][0]
                assert "test-session" in calls[1][0][0]
                assert "Enter" in calls[1][0][0]

    def test_send_command_custom_delay(self):
        """Test that custom delay can be specified"""
        with patch('subprocess.run') as mock_run:
            with patch('time.sleep') as mock_sleep:
                mock_run.return_value.returncode = 0

                # Send command with custom delay
                TMUXClient.send_command("test-session", "echo test", delay=0.5)

                # Verify custom delay was used
                mock_sleep.assert_called_once_with(0.5)

    def test_send_command_handles_failure(self):
        """Test that send_command handles subprocess failures"""
        with patch('subprocess.run') as mock_run:
            # Simulate failure
            mock_run.side_effect = subprocess.CalledProcessError(1, "tmux")

            result = TMUXClient.send_command("test-session", "echo test")

            # Should return False on failure
            assert result is False

    def test_capture_pane(self):
        """Test capturing pane output"""
        with patch('subprocess.run') as mock_run:
            # Mock successful output capture
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Test output\nLine 2"
            mock_run.return_value = mock_result

            output = TMUXClient.capture_pane("test-session")

            assert output == "Test output\nLine 2"
            mock_run.assert_called_once()

    def test_capture_pane_with_lines(self):
        """Test capturing specific number of lines"""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Line 1\nLine 2\nLine 3"
            mock_run.return_value = mock_result

            TMUXClient.capture_pane("test-session", lines=5)

            # Verify -S flag was added for line limit
            call_args = mock_run.call_args[0][0]
            assert "-S" in call_args
            assert "-5" in call_args

    def test_session_exists(self):
        """Test checking if session exists"""
        with patch('subprocess.run') as mock_run:
            # Test existing session
            mock_run.return_value.returncode = 0
            assert TMUXClient.session_exists("existing") is True

            # Test non-existing session
            mock_run.return_value.returncode = 1
            assert TMUXClient.session_exists("non-existing") is False

    def test_create_session(self):
        """Test creating new session"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0

            # Create detached session
            result = TMUXClient.create_session("new-session", "claude", detached=True)

            assert result is True
            call_args = mock_run.call_args[0][0]
            assert "new-session" in call_args
            assert "-d" in call_args
            assert "-s" in call_args
            assert "new-session" in call_args
            assert "claude" in call_args

    def test_kill_session(self):
        """Test killing session"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0

            result = TMUXClient.kill_session("old-session")

            assert result is True
            call_args = mock_run.call_args[0][0]
            assert "kill-session" in call_args
            assert "old-session" in call_args

    def test_list_sessions(self):
        """Test listing sessions"""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "session1\nsession2\nsession3\n"
            mock_run.return_value = mock_result

            sessions = TMUXClient.list_sessions()

            assert sessions == ["session1", "session2", "session3"]

    def test_send_to_agent(self):
        """Test sending command to agent by ID"""
        with patch.object(TMUXClient, 'send_command') as mock_send:
            mock_send.return_value = True

            result = TMUXClient.send_to_agent("supervisor", "test command")

            assert result is True
            mock_send.assert_called_once_with("claude-supervisor", "test command")

    def test_send_to_unknown_agent(self):
        """Test sending to unknown agent fails gracefully"""
        result = TMUXClient.send_to_agent("unknown-agent", "test command")
        assert result is False

    def test_broadcast_to_agents(self):
        """Test broadcasting to multiple agents"""
        with patch.object(TMUXClient, 'send_command') as mock_send:
            mock_send.return_value = True

            results = TMUXClient.broadcast_to_agents("broadcast message", exclude=["supervisor"])

            # Should have sent to all agents except supervisor
            assert "supervisor" not in results
            assert len(results) > 0
            assert all(results.values())  # All should be True

    def test_restart_session(self):
        """Test restarting session"""
        with patch.object(TMUXClient, 'kill_session') as mock_kill:
            with patch.object(TMUXClient, 'create_session') as mock_create:
                with patch('time.sleep'):  # Mock the delay
                    mock_kill.return_value = True
                    mock_create.return_value = True

                    result = TMUXClient.restart_session("test-session", "claude")

                    assert result is True
                    mock_kill.assert_called_once_with("test-session")
                    mock_create.assert_called_once_with("test-session", "claude")

    def test_health_check(self):
        """Test health check for all agents"""
        with patch.object(TMUXClient, 'session_exists') as mock_exists:
            # Simulate some healthy and some unhealthy
            mock_exists.side_effect = [True, False, True, True, False, True, True, False, True]

            health = TMUXClient.health_check()

            assert "supervisor" in health
            assert isinstance(health["supervisor"], bool)
            assert len(health) > 0


class TestTMUXClientIntegration:
    """Integration tests (require actual TMUX)"""

    @pytest.mark.skipif(
        not Path("/opt/homebrew/bin/tmux").exists() and not Path("/usr/bin/tmux").exists(),
        reason="TMUX not installed"
    )
    def test_real_command_delay(self):
        """Test actual delay timing with real TMUX"""
        test_session = "pytest-tmux-test"

        # Clean up any existing test session
        TMUXClient.kill_session(test_session)

        try:
            # Create test session
            assert TMUXClient.create_session(test_session, "bash")

            # Measure actual command timing
            start_time = time.time()
            result = TMUXClient.send_command(test_session, "echo 'delay test'")
            elapsed = time.time() - start_time

            assert result is True
            # Should take at least 0.1 seconds due to mandatory delay
            assert elapsed >= 0.1

            # Verify command was executed
            time.sleep(0.2)  # Wait for command to process
            output = TMUXClient.capture_pane(test_session)
            assert output is not None
            assert "delay test" in output

        finally:
            # Clean up
            TMUXClient.kill_session(test_session)


if __name__ == "__main__":
    # Run basic tests
    print("🧪 Running TMUX Client Tests...")

    test = TestTMUXClient()

    # Test delay enforcement
    test.test_send_command_enforces_delay()
    print("✅ Delay enforcement test passed")

    test.test_send_command_custom_delay()
    print("✅ Custom delay test passed")

    test.test_send_command_handles_failure()
    print("✅ Failure handling test passed")

    test.test_session_exists()
    print("✅ Session exists test passed")

    test.test_list_sessions()
    print("✅ List sessions test passed")

    print("\n✅ All tests passed!")