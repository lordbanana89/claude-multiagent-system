"""
Tests for central configuration system
Verify that all paths and settings are properly configured
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings


class TestConfiguration:
    """Test suite for configuration settings"""

    def test_project_root_exists(self):
        """Test that project root is correctly detected"""
        assert settings.PROJECT_ROOT.exists()
        assert settings.PROJECT_ROOT.is_dir()
        assert (settings.PROJECT_ROOT / "config").exists()

    def test_directory_paths_valid(self):
        """Test that all configured directories are valid paths"""
        dirs_to_check = [
            settings.CORE_DIR,
            settings.LANGGRAPH_DIR,
            settings.INTERFACES_DIR,
            settings.SCRIPTS_DIR,
            settings.TESTS_DIR,
        ]

        for dir_path in dirs_to_check:
            assert isinstance(dir_path, Path)
            # Check that parent exists (directory might not be created yet)
            assert dir_path.parent.exists()

    def test_tmux_binary_detection(self):
        """Test TMUX binary detection"""
        assert settings.TMUX_BIN is not None
        assert isinstance(settings.TMUX_BIN, str)
        # Should be either a full path or command name
        assert "/" in settings.TMUX_BIN or settings.TMUX_BIN == "tmux"

    def test_tmux_delay_setting(self):
        """Test that TMUX delay is properly set"""
        assert settings.TMUX_COMMAND_DELAY > 0
        assert settings.TMUX_COMMAND_DELAY >= 0.1  # Minimum safe delay

    def test_agent_sessions_mapping(self):
        """Test agent session configuration"""
        assert isinstance(settings.AGENT_SESSIONS, dict)
        assert len(settings.AGENT_SESSIONS) > 0

        # Check required agents
        required_agents = ["supervisor", "backend-api", "database", "frontend-ui"]
        for agent in required_agents:
            assert agent in settings.AGENT_SESSIONS
            assert settings.AGENT_SESSIONS[agent].startswith("claude-")

    def test_agent_ports_mapping(self):
        """Test agent port configuration"""
        assert isinstance(settings.AGENT_PORTS, dict)

        # Check port ranges
        for agent, port in settings.AGENT_PORTS.items():
            assert isinstance(port, int)
            assert 8000 <= port <= 9000  # Reasonable port range

    def test_dynamic_port_range(self):
        """Test dynamic port configuration"""
        assert settings.DYNAMIC_PORT_START < settings.DYNAMIC_PORT_END
        assert settings.DYNAMIC_PORT_START >= 8000
        assert settings.DYNAMIC_PORT_END <= 9999

    def test_redis_configuration(self):
        """Test Redis configuration"""
        assert isinstance(settings.REDIS_HOST, str)
        assert isinstance(settings.REDIS_PORT, int)
        assert isinstance(settings.REDIS_DB, int)
        assert settings.REDIS_URL.startswith("redis://")

    def test_queue_configuration(self):
        """Test queue settings"""
        assert settings.QUEUE_MAX_RETRIES > 0
        assert settings.QUEUE_RETRY_DELAY > 0
        assert settings.QUEUE_MESSAGE_TTL > 0

        # Check queue names
        assert settings.QUEUE_DEFAULT == "default"
        assert settings.QUEUE_PRIORITY == "priority"
        assert settings.QUEUE_DLQ == "dead_letter"

    def test_feature_flags(self):
        """Test feature flag configuration"""
        assert isinstance(settings.FEATURES, dict)

        # Check that all feature flags are booleans
        for feature, enabled in settings.FEATURES.items():
            assert isinstance(enabled, bool)

    def test_system_limits(self):
        """Test system limit configurations"""
        assert settings.MAX_CONCURRENT_TASKS > 0
        assert settings.MAX_TASK_QUEUE_SIZE > 0
        assert settings.TASK_TIMEOUT_DEFAULT > 0
        assert settings.MAX_MESSAGE_SIZE > 0
        assert settings.MAX_MESSAGES_PER_INBOX > 0
        assert settings.MAX_AGENTS > 0

    def test_utility_functions(self):
        """Test utility functions in settings"""
        # Test get_agent_session
        session = settings.get_agent_session("supervisor")
        assert session == "claude-supervisor"

        # Test unknown agent
        session = settings.get_agent_session("unknown")
        assert session == "claude-unknown"

        # Test get_agent_port
        port = settings.get_agent_port("backend-api")
        assert isinstance(port, int)
        assert port == settings.AGENT_PORTS["backend-api"]

    def test_ensure_directories(self):
        """Test directory creation function"""
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            settings.ensure_directories()
            # Should have been called for each required directory
            assert mock_mkdir.called

    def test_config_validation(self):
        """Test configuration validation"""
        issues = settings.validate_config()
        assert isinstance(issues, list)

        # In a properly configured system, there should be no critical issues
        # But we might have warnings about Redis, etc.
        for issue in issues:
            assert isinstance(issue, str)

    def test_config_export(self):
        """Test CONFIG dictionary export"""
        assert isinstance(settings.CONFIG, dict)
        assert "PROJECT_ROOT" in settings.CONFIG
        assert "TMUX_BIN" in settings.CONFIG
        assert "AGENT_SESSIONS" in settings.CONFIG
        assert "FEATURES" in settings.CONFIG

    def test_paths_relative_to_project(self):
        """Test that all paths are relative to project root"""
        # Check that configured paths are under project root
        assert settings.STATE_DIR.is_relative_to(settings.PROJECT_ROOT)
        assert settings.SHARED_STATE_FILE.is_relative_to(settings.PROJECT_ROOT)

    def test_auth_configuration(self):
        """Test authentication settings"""
        assert settings.AUTH_DB_PATH.parent == settings.AUTH_DIR
        assert isinstance(settings.AUTH_SECRET_KEY, str)
        assert len(settings.AUTH_SECRET_KEY) > 0

    @patch.dict('os.environ', {'DEBUG': 'true'})
    def test_debug_mode(self):
        """Test debug mode detection"""
        # Reload module to pick up environment change
        import importlib
        importlib.reload(settings)
        assert settings.DEBUG is True

    @patch.dict('os.environ', {'TEST_MODE': 'true'})
    def test_test_mode(self):
        """Test test mode detection"""
        import importlib
        importlib.reload(settings)
        assert settings.TEST_MODE is True
        assert settings.MOCK_CLAUDE is True


class TestConfigurationIntegration:
    """Integration tests for configuration"""

    def test_actual_directories_exist(self):
        """Test that expected directories actually exist"""
        expected_dirs = [
            settings.PROJECT_ROOT,
            settings.CORE_DIR,
            settings.CONFIG_DIR,
        ]

        for dir_path in expected_dirs:
            assert dir_path.exists(), f"Directory {dir_path} does not exist"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"

    def test_shared_state_file_location(self):
        """Test shared state file configuration"""
        # File might not exist yet, but parent should
        assert settings.SHARED_STATE_FILE.parent.exists()
        assert settings.SHARED_STATE_FILE.suffix == ".json"

    def test_log_directory_creation(self):
        """Test that log directory is created on import"""
        assert settings.LOG_DIR.exists()
        assert settings.LOG_DIR.is_dir()

    @pytest.mark.skipif(
        not Path("/opt/homebrew/bin/tmux").exists() and not Path("/usr/bin/tmux").exists(),
        reason="TMUX not installed"
    )
    def test_tmux_binary_exists(self):
        """Test that configured TMUX binary actually exists"""
        tmux_path = Path(settings.TMUX_BIN)
        assert tmux_path.exists() or settings.TMUX_BIN == "tmux"


if __name__ == "__main__":
    print("🧪 Running Configuration Tests...")

    test = TestConfiguration()

    test.test_project_root_exists()
    print("✅ Project root test passed")

    test.test_directory_paths_valid()
    print("✅ Directory paths test passed")

    test.test_tmux_binary_detection()
    print("✅ TMUX binary detection test passed")

    test.test_agent_sessions_mapping()
    print("✅ Agent sessions test passed")

    test.test_feature_flags()
    print("✅ Feature flags test passed")

    test.test_utility_functions()
    print("✅ Utility functions test passed")

    print("\n✅ All configuration tests passed!")