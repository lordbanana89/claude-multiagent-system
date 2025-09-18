"""
Central configuration for Claude Multi-Agent System
All paths, settings, and constants in one place
"""

import os
import shutil
from pathlib import Path

# ============================================================================
# PATH CONFIGURATION
# ============================================================================

# Project root directory (parent of config/)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Core directories
CONFIG_DIR = PROJECT_ROOT / "config"
CORE_DIR = PROJECT_ROOT / "core"
LANGGRAPH_DIR = PROJECT_ROOT / "langgraph-test"
INTERFACES_DIR = PROJECT_ROOT / "interfaces"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
INSTRUCTIONS_DIR = PROJECT_ROOT / "instructions"
SESSIONS_DIR = PROJECT_ROOT / "sessions"
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs"

# State and data directories
STATE_DIR = LANGGRAPH_DIR
SHARED_STATE_FILE = STATE_DIR / "shared_state.json"
PERSISTENCE_DIR = STATE_DIR / "persistence"
INBOX_DIR = LANGGRAPH_DIR / "inbox"

# Auth and security
AUTH_DIR = PROJECT_ROOT / ".auth"
AUTH_DB_PATH = AUTH_DIR / "auth.db"
AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "change-this-in-production")

# Logs
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ============================================================================
# TMUX CONFIGURATION
# ============================================================================

# TMUX binary path - try to auto-detect
TMUX_BIN = shutil.which("tmux")
if not TMUX_BIN:
    # Fallback to common locations
    if Path("/opt/homebrew/bin/tmux").exists():
        TMUX_BIN = "/opt/homebrew/bin/tmux"
    elif Path("/usr/local/bin/tmux").exists():
        TMUX_BIN = "/usr/local/bin/tmux"
    else:
        TMUX_BIN = "tmux"  # Hope it's in PATH

# TMUX command delay (CRITICAL - DO NOT REDUCE)
TMUX_COMMAND_DELAY = 0.1  # seconds

# ============================================================================
# AGENT CONFIGURATION
# ============================================================================

# Agent session mapping
AGENT_SESSIONS = {
    "supervisor": "claude-supervisor",
    "master": "claude-master",
    "backend-api": "claude-backend-api",
    "database": "claude-database",
    "frontend-ui": "claude-frontend-ui",
    "instagram": "claude-instagram",
    "testing": "claude-testing",
    "queue-manager": "claude-queue-manager",
    "deployment": "claude-deployment"
}

# Agent ports for web interfaces
AGENT_PORTS = {
    "supervisor": 8088,
    "master": 8089,
    "backend-api": 8090,
    "database": 8091,
    "frontend-ui": 8092,
    "instagram": 8093,
    "testing": 8094,
    "queue-manager": 8095,
    "deployment": 8096
}

# Dynamic agent port range
DYNAMIC_PORT_START = 8100
DYNAMIC_PORT_END = 8200

# Agent instruction files
AGENT_INSTRUCTIONS = {
    agent_id: INSTRUCTIONS_DIR / f"{agent_id.replace('-', '_')}.md"
    for agent_id in AGENT_SESSIONS.keys()
}

# ============================================================================
# QUEUE CONFIGURATION (Dramatiq)
# ============================================================================

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_URL = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

# Queue names
QUEUE_DEFAULT = "default"
QUEUE_PRIORITY = "priority"
QUEUE_DELAYED = "delayed"
QUEUE_DLQ = "dead_letter"

# Queue settings
QUEUE_MAX_RETRIES = 3
QUEUE_RETRY_DELAY = 60  # seconds
QUEUE_MESSAGE_TTL = 86400  # 24 hours

# ============================================================================
# WEB INTERFACE CONFIGURATION
# ============================================================================

# Streamlit settings
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", 8501))
STREAMLIT_HOST = os.getenv("STREAMLIT_HOST", "localhost")
STREAMLIT_THEME = "dark"

# LangGraph Studio settings
LANGGRAPH_API_URL = os.getenv("LANGGRAPH_API_URL", "http://localhost:8123")
LANGGRAPH_API_KEY = os.getenv("LANGGRAPH_API_KEY", "")

# Web session settings
WEB_SESSION_TIMEOUT = 3600  # 1 hour
WEB_MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

# ============================================================================
# MONITORING & METRICS
# ============================================================================

# Prometheus metrics
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"
METRICS_PORT = int(os.getenv("METRICS_PORT", 9090))
METRICS_PATH = "/metrics"

# Health check settings
HEALTH_CHECK_INTERVAL = 30  # seconds
HEALTH_CHECK_TIMEOUT = 5  # seconds

# ============================================================================
# DEVELOPMENT SETTINGS
# ============================================================================

# Debug mode
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Test mode
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

# Mock Claude responses in test mode
MOCK_CLAUDE = TEST_MODE or os.getenv("MOCK_CLAUDE", "false").lower() == "true"

# ============================================================================
# SYSTEM LIMITS
# ============================================================================

# Task limits
MAX_CONCURRENT_TASKS = 10
MAX_TASK_QUEUE_SIZE = 100
TASK_TIMEOUT_DEFAULT = 300  # 5 minutes

# Message limits
MAX_MESSAGE_SIZE = 10000  # characters
MAX_MESSAGES_PER_INBOX = 1000
MESSAGE_CLEANUP_AGE = 30  # days

# Agent limits
MAX_AGENTS = 20
MAX_DYNAMIC_AGENTS = 10

# ============================================================================
# FEATURE FLAGS
# ============================================================================

FEATURES = {
    "DRAMATIQ_ENABLED": os.getenv("FEATURE_DRAMATIQ", "false").lower() == "true",
    "OVERMIND_ENABLED": os.getenv("FEATURE_OVERMIND", "false").lower() == "true",
    "METRICS_ENABLED": METRICS_ENABLED,
    "AUTH_ENABLED": os.getenv("FEATURE_AUTH", "true").lower() == "true",
    "INBOX_ENABLED": os.getenv("FEATURE_INBOX", "true").lower() == "true",
    "DYNAMIC_AGENTS": os.getenv("FEATURE_DYNAMIC_AGENTS", "true").lower() == "true",
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_agent_session(agent_id: str) -> str:
    """Get tmux session name for agent ID"""
    return AGENT_SESSIONS.get(agent_id, f"claude-{agent_id}")

def get_agent_port(agent_id: str) -> int:
    """Get web port for agent ID"""
    return AGENT_PORTS.get(agent_id, DYNAMIC_PORT_START)

def ensure_directories():
    """Ensure all required directories exist"""
    dirs = [
        AUTH_DIR,
        LOG_DIR,
        PERSISTENCE_DIR,
        SESSIONS_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# ============================================================================
# ENVIRONMENT VALIDATION
# ============================================================================

def validate_config():
    """Validate configuration and environment"""
    issues = []

    # Check TMUX
    if not TMUX_BIN or not Path(TMUX_BIN).exists():
        issues.append(f"TMUX not found at {TMUX_BIN}")

    # Check Redis if Dramatiq enabled
    if FEATURES["DRAMATIQ_ENABLED"]:
        try:
            import redis
            r = redis.Redis.from_url(REDIS_URL)
            r.ping()
        except Exception as e:
            issues.append(f"Redis not accessible: {e}")

    # Check directories
    if not PROJECT_ROOT.exists():
        issues.append(f"Project root not found: {PROJECT_ROOT}")

    return issues

# ============================================================================
# EXPORT CONFIGURATION AS DICT (for compatibility)
# ============================================================================

CONFIG = {
    "PROJECT_ROOT": str(PROJECT_ROOT),
    "TMUX_BIN": TMUX_BIN,
    "SHARED_STATE_FILE": str(SHARED_STATE_FILE),
    "AUTH_DB_PATH": str(AUTH_DB_PATH),
    "REDIS_URL": REDIS_URL,
    "AGENT_SESSIONS": AGENT_SESSIONS,
    "AGENT_PORTS": AGENT_PORTS,
    "FEATURES": FEATURES,
}

# Ensure directories on import
ensure_directories()

# Print config issues if in debug mode
if DEBUG:
    issues = validate_config()
    if issues:
        print("⚠️ Configuration issues detected:")
        for issue in issues:
            print(f"  - {issue}")