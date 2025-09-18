"""
Monitoring Package - Prometheus metrics and health checks for Claude Multi-Agent System
"""

from .metrics import (
    MetricsCollector,
    agent_command_counter,
    agent_command_latency,
    active_agents_gauge,
    queue_depth_gauge,
    system_errors_counter,
    task_completion_counter,
    get_metrics_endpoint,
    record_agent_command,
    record_task_completion,
    record_error,
)

from .health import (
    HealthChecker,
    check_system_health,
    check_redis_health,
    check_agents_health,
    check_queue_health,
    get_health_endpoint,
)

__version__ = "1.0.0"

__all__ = [
    # Metrics
    "MetricsCollector",
    "agent_command_counter",
    "agent_command_latency",
    "active_agents_gauge",
    "queue_depth_gauge",
    "system_errors_counter",
    "task_completion_counter",
    "get_metrics_endpoint",
    "record_agent_command",
    "record_task_completion",
    "record_error",
    # Health
    "HealthChecker",
    "check_system_health",
    "check_redis_health",
    "check_agents_health",
    "check_queue_health",
    "get_health_endpoint",
]