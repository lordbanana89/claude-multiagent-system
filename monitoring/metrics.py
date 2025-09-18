"""
Prometheus Metrics for Claude Multi-Agent System
Provides comprehensive metrics collection and export
"""

import time
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        Summary,
        Info,
        generate_latest,
        REGISTRY,
        CollectorRegistry,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Create dummy classes for compatibility
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def labels(self, **kwargs): return self

    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def time(self): return self
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def labels(self, **kwargs): return self

    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
        def labels(self, **kwargs): return self

    def generate_latest(*args, **kwargs):
        return b"# Prometheus client not installed\n"

logger = logging.getLogger(__name__)

# ============================================================================
# METRICS DEFINITIONS
# ============================================================================

# Agent Command Metrics
agent_command_counter = Counter(
    'agent_commands_total',
    'Total number of commands sent to agents',
    ['agent_id', 'status', 'command_type']
)

agent_command_latency = Histogram(
    'agent_command_duration_seconds',
    'Time taken to execute agent commands',
    ['agent_id', 'command_type'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0)
)

# Agent Status Metrics
active_agents_gauge = Gauge(
    'active_agents_total',
    'Number of currently active agents',
    ['agent_type']
)

agent_health_gauge = Gauge(
    'agent_health_status',
    'Health status of each agent (1=healthy, 0=unhealthy)',
    ['agent_id']
)

# Queue Metrics
queue_depth_gauge = Gauge(
    'queue_depth_total',
    'Current depth of message queues',
    ['queue_name', 'priority']
)

queue_processing_rate = Histogram(
    'queue_processing_duration_seconds',
    'Time to process queue messages',
    ['queue_name', 'message_type'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0)
)

queue_errors_counter = Counter(
    'queue_errors_total',
    'Total queue processing errors',
    ['queue_name', 'error_type']
)

# Task Metrics
task_completion_counter = Counter(
    'task_completions_total',
    'Total number of completed tasks',
    ['task_type', 'status', 'agent_id']
)

task_duration_histogram = Histogram(
    'task_duration_seconds',
    'Time taken to complete tasks',
    ['task_type', 'agent_id'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600)
)

# System Metrics
system_errors_counter = Counter(
    'system_errors_total',
    'Total system errors',
    ['component', 'error_type', 'severity']
)

system_uptime_gauge = Gauge(
    'system_uptime_seconds',
    'System uptime in seconds'
)

memory_usage_gauge = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes',
    ['component']
)

# Performance Metrics
api_request_counter = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code']
)

api_latency_histogram = Histogram(
    'api_request_duration_seconds',
    'API request latency',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

# ============================================================================
# METRICS COLLECTOR CLASS
# ============================================================================

class MetricsCollector:
    """
    Centralized metrics collection and management
    """

    def __init__(self, registry=None):
        """Initialize metrics collector"""
        self.registry = registry or REGISTRY if PROMETHEUS_AVAILABLE else None
        self.start_time = time.time()
        self._last_update = time.time()
        self._metrics_cache = {}

        # Update system uptime periodically
        if PROMETHEUS_AVAILABLE:
            system_uptime_gauge.set(0)

    def record_agent_command(
        self,
        agent_id: str,
        command_type: str,
        status: str = "success",
        duration: Optional[float] = None
    ):
        """Record an agent command execution"""
        try:
            agent_command_counter.labels(
                agent_id=agent_id,
                status=status,
                command_type=command_type
            ).inc()

            if duration is not None:
                agent_command_latency.labels(
                    agent_id=agent_id,
                    command_type=command_type
                ).observe(duration)

            logger.debug(f"Recorded command for {agent_id}: {status} ({duration:.2f}s)")
        except Exception as e:
            logger.error(f"Failed to record agent command metric: {e}")

    def record_task_completion(
        self,
        task_type: str,
        agent_id: str,
        status: str = "completed",
        duration: Optional[float] = None
    ):
        """Record task completion"""
        try:
            task_completion_counter.labels(
                task_type=task_type,
                status=status,
                agent_id=agent_id
            ).inc()

            if duration is not None:
                task_duration_histogram.labels(
                    task_type=task_type,
                    agent_id=agent_id
                ).observe(duration)

            logger.debug(f"Recorded task {task_type} for {agent_id}: {status}")
        except Exception as e:
            logger.error(f"Failed to record task completion metric: {e}")

    def record_error(
        self,
        component: str,
        error_type: str,
        severity: str = "error"
    ):
        """Record system error"""
        try:
            system_errors_counter.labels(
                component=component,
                error_type=error_type,
                severity=severity
            ).inc()

            logger.debug(f"Recorded {severity} error in {component}: {error_type}")
        except Exception as e:
            logger.error(f"Failed to record error metric: {e}")

    def update_queue_depth(self, queue_name: str, depth: int, priority: str = "normal"):
        """Update queue depth metric"""
        try:
            queue_depth_gauge.labels(
                queue_name=queue_name,
                priority=priority
            ).set(depth)
        except Exception as e:
            logger.error(f"Failed to update queue depth metric: {e}")

    def update_active_agents(self, agent_counts: Dict[str, int]):
        """Update active agent counts"""
        try:
            for agent_type, count in agent_counts.items():
                active_agents_gauge.labels(agent_type=agent_type).set(count)
        except Exception as e:
            logger.error(f"Failed to update active agents metric: {e}")

    def update_system_uptime(self):
        """Update system uptime metric"""
        try:
            uptime = time.time() - self.start_time
            system_uptime_gauge.set(uptime)
            return uptime
        except Exception as e:
            logger.error(f"Failed to update uptime metric: {e}")
            return 0

    def get_metrics(self) -> bytes:
        """Get current metrics in Prometheus format"""
        try:
            # Update uptime before generating metrics
            self.update_system_uptime()

            if PROMETHEUS_AVAILABLE:
                return generate_latest(self.registry)
            else:
                return b"# Prometheus client not available\n"
        except Exception as e:
            logger.error(f"Failed to generate metrics: {e}")
            return b"# Error generating metrics\n"

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary as dictionary"""
        uptime = self.update_system_uptime()

        summary = {
            "uptime_seconds": uptime,
            "uptime_human": self._format_duration(uptime),
            "prometheus_available": PROMETHEUS_AVAILABLE,
            "last_update": self._last_update,
            "metrics_types": [
                "agent_commands",
                "task_completions",
                "queue_depth",
                "system_errors",
                "api_requests"
            ]
        }

        self._last_update = time.time()
        return summary

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in human-readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global collector instance
_collector = None


def get_collector() -> MetricsCollector:
    """Get or create global metrics collector"""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


def record_agent_command(
    agent_id: str,
    command_type: str = "generic",
    status: str = "success",
    duration: Optional[float] = None
):
    """Quick function to record agent command"""
    collector = get_collector()
    collector.record_agent_command(agent_id, command_type, status, duration)


def record_task_completion(
    task_type: str,
    agent_id: str,
    status: str = "completed",
    duration: Optional[float] = None
):
    """Quick function to record task completion"""
    collector = get_collector()
    collector.record_task_completion(task_type, agent_id, status, duration)


def record_error(component: str, error_type: str, severity: str = "error"):
    """Quick function to record error"""
    collector = get_collector()
    collector.record_error(component, error_type, severity)


def get_metrics_endpoint() -> bytes:
    """Get metrics for Prometheus endpoint"""
    collector = get_collector()
    return collector.get_metrics()


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("🧪 Testing Metrics Module...")

    # Create collector
    collector = MetricsCollector()

    # Record some test metrics
    record_agent_command("supervisor", "echo", "success", 0.5)
    record_agent_command("backend-api", "deploy", "failure", 10.2)

    record_task_completion("deployment", "supervisor", "completed", 45.3)
    record_task_completion("test", "testing", "failed", 2.1)

    record_error("queue", "timeout", "warning")
    record_error("agent", "connection_lost", "error")

    # Update gauges
    collector.update_active_agents({"supervisor": 1, "backend": 2, "frontend": 1})
    collector.update_queue_depth("default", 42)
    collector.update_queue_depth("priority", 5, "high")

    # Get summary
    summary = collector.get_metrics_summary()
    print("\n📊 Metrics Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Get Prometheus format
    metrics_output = get_metrics_endpoint()
    print(f"\n📈 Prometheus Output ({len(metrics_output)} bytes)")

    if PROMETHEUS_AVAILABLE:
        print("\n✅ Prometheus client available - full metrics enabled")
    else:
        print("\n⚠️ Prometheus client not installed - install with: pip install prometheus-client")

    print("\n✅ Metrics module ready!")