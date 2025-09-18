"""
Health Checks for Claude Multi-Agent System
Provides comprehensive health monitoring for all components
"""

import time
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import sys
from enum import Enum
from dataclasses import dataclass, asdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status of a component"""
    name: str
    status: HealthStatus
    message: str = ""
    details: Dict[str, Any] = None
    last_check: float = None

    def __post_init__(self):
        if self.last_check is None:
            self.last_check = time.time()
        if self.details is None:
            self.details = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "last_check": self.last_check,
            "last_check_human": time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.localtime(self.last_check)
            )
        }


class HealthChecker:
    """
    Comprehensive health checker for the system
    """

    def __init__(self):
        """Initialize health checker"""
        self.components: Dict[str, ComponentHealth] = {}
        self.start_time = time.time()
        self.check_interval = 30  # seconds
        self.last_full_check = 0

    def check_redis_health(self) -> ComponentHealth:
        """Check Redis health"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=2)

            # Ping Redis
            start = time.time()
            r.ping()
            latency = (time.time() - start) * 1000  # ms

            # Get info
            info = r.info()

            health = ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="Redis is operational",
                details={
                    "version": info.get("redis_version", "unknown"),
                    "uptime_seconds": info.get("uptime_in_seconds", 0),
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "unknown"),
                    "latency_ms": round(latency, 2)
                }
            )

            # Check for issues
            if latency > 100:
                health.status = HealthStatus.DEGRADED
                health.message = f"High latency: {latency:.2f}ms"
            elif info.get("connected_clients", 0) > 100:
                health.status = HealthStatus.DEGRADED
                health.message = "High number of connections"

        except Exception as e:
            health = ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis connection failed: {str(e)}"
            )

        self.components["redis"] = health
        return health

    def check_agents_health(self) -> ComponentHealth:
        """Check TMUX agents health"""
        try:
            from core.tmux_client import TMUXClient
            from config.settings import AGENT_SESSIONS

            total_agents = len(AGENT_SESSIONS)
            active_agents = 0
            agent_status = {}

            for agent_id, session_name in AGENT_SESSIONS.items():
                if TMUXClient.session_exists(session_name):
                    active_agents += 1
                    agent_status[agent_id] = "active"
                else:
                    agent_status[agent_id] = "inactive"

            # Determine overall health
            if active_agents == total_agents:
                status = HealthStatus.HEALTHY
                message = f"All {total_agents} agents are active"
            elif active_agents > total_agents * 0.5:
                status = HealthStatus.DEGRADED
                message = f"{active_agents}/{total_agents} agents active"
            elif active_agents > 0:
                status = HealthStatus.UNHEALTHY
                message = f"Only {active_agents}/{total_agents} agents active"
            else:
                status = HealthStatus.UNHEALTHY
                message = "No agents are active"

            health = ComponentHealth(
                name="agents",
                status=status,
                message=message,
                details={
                    "total": total_agents,
                    "active": active_agents,
                    "inactive": total_agents - active_agents,
                    "agents": agent_status
                }
            )

        except Exception as e:
            health = ComponentHealth(
                name="agents",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check agents: {str(e)}"
            )

        self.components["agents"] = health
        return health

    def check_queue_health(self) -> ComponentHealth:
        """Check Dramatiq queue health"""
        try:
            from task_queue.broker import check_broker_health
            from task_queue.actors import check_actors_health

            broker_health = check_broker_health()
            actors_health = check_actors_health()

            # Determine status
            if broker_health["status"] == "healthy" and actors_health["status"] == "healthy":
                status = HealthStatus.HEALTHY
                message = "Queue system operational"
            elif broker_health["status"] == "degraded" or actors_health["status"] == "degraded":
                status = HealthStatus.DEGRADED
                message = "Queue system degraded"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Queue system unhealthy"

            health = ComponentHealth(
                name="queue",
                status=status,
                message=message,
                details={
                    "broker": broker_health,
                    "actors": {
                        "registered": len(actors_health.get("actors", {})),
                        "status": actors_health["status"]
                    }
                }
            )

        except Exception as e:
            health = ComponentHealth(
                name="queue",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check queue: {str(e)}"
            )

        self.components["queue"] = health
        return health

    def check_shared_state_health(self) -> ComponentHealth:
        """Check shared state system health"""
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / "langgraph-test"))
            from shared_state.manager import SharedStateManager

            manager = SharedStateManager()

            # Check if state file exists and is readable
            state_file = Path(manager.state_file) if hasattr(manager, 'state_file') else None

            if state_file and state_file.exists():
                file_size = state_file.stat().st_size
                modified = time.time() - state_file.stat().st_mtime

                status = HealthStatus.HEALTHY
                message = "Shared state accessible"

                # Check for issues
                if file_size > 10 * 1024 * 1024:  # 10MB
                    status = HealthStatus.DEGRADED
                    message = "State file is large"
                elif modified > 3600:  # 1 hour
                    status = HealthStatus.DEGRADED
                    message = "State file not recently updated"

                details = {
                    "file_size_bytes": file_size,
                    "file_size_human": self._format_bytes(file_size),
                    "last_modified_seconds": modified,
                    "path": str(state_file)
                }
            else:
                status = HealthStatus.DEGRADED
                message = "State file not found"
                details = {"error": "State file does not exist"}

            health = ComponentHealth(
                name="shared_state",
                status=status,
                message=message,
                details=details
            )

        except Exception as e:
            health = ComponentHealth(
                name="shared_state",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check shared state: {str(e)}"
            )

        self.components["shared_state"] = health
        return health

    def check_overmind_health(self) -> ComponentHealth:
        """Check Overmind process manager health"""
        try:
            from core.overmind_client import OvermindClient

            client = OvermindClient()
            processes = client.get_processes()

            if processes:
                running = sum(1 for p in processes.values() if p.get("status") == "running")
                total = len(processes)

                if running == total:
                    status = HealthStatus.HEALTHY
                    message = f"All {total} processes running"
                elif running > 0:
                    status = HealthStatus.DEGRADED
                    message = f"{running}/{total} processes running"
                else:
                    status = HealthStatus.UNHEALTHY
                    message = "No processes running"

                details = {
                    "total_processes": total,
                    "running": running,
                    "processes": processes
                }
            else:
                status = HealthStatus.UNHEALTHY
                message = "Overmind not running"
                details = {"error": "Could not get process list"}

            health = ComponentHealth(
                name="overmind",
                status=status,
                message=message,
                details=details
            )

        except Exception as e:
            health = ComponentHealth(
                name="overmind",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check Overmind: {str(e)}"
            )

        self.components["overmind"] = health
        return health

    def check_system_health(self) -> Dict[str, Any]:
        """
        Perform comprehensive system health check

        Returns:
            Dictionary with overall health status and component details
        """
        # Check all components
        checks = [
            self.check_redis_health(),
            self.check_agents_health(),
            self.check_queue_health(),
            self.check_shared_state_health(),
            self.check_overmind_health(),
        ]

        # Determine overall status
        statuses = [check.status for check in checks]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall_status = HealthStatus.HEALTHY
            overall_message = "All systems operational"
        elif HealthStatus.UNHEALTHY in statuses:
            overall_status = HealthStatus.UNHEALTHY
            unhealthy = [c.name for c in checks if c.status == HealthStatus.UNHEALTHY]
            overall_message = f"Components unhealthy: {', '.join(unhealthy)}"
        elif HealthStatus.DEGRADED in statuses:
            overall_status = HealthStatus.DEGRADED
            degraded = [c.name for c in checks if c.status == HealthStatus.DEGRADED]
            overall_message = f"Components degraded: {', '.join(degraded)}"
        else:
            overall_status = HealthStatus.UNKNOWN
            overall_message = "Unable to determine system health"

        # Build response
        self.last_full_check = time.time()
        uptime = time.time() - self.start_time

        return {
            "status": overall_status.value,
            "message": overall_message,
            "timestamp": self.last_full_check,
            "uptime_seconds": uptime,
            "uptime_human": self._format_duration(uptime),
            "components": {
                name: component.to_dict()
                for name, component in self.components.items()
            },
            "summary": {
                "healthy": sum(1 for c in checks if c.status == HealthStatus.HEALTHY),
                "degraded": sum(1 for c in checks if c.status == HealthStatus.DEGRADED),
                "unhealthy": sum(1 for c in checks if c.status == HealthStatus.UNHEALTHY),
                "unknown": sum(1 for c in checks if c.status == HealthStatus.UNKNOWN),
                "total": len(checks)
            }
        }

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in human-readable format"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    @staticmethod
    def _format_bytes(bytes: int) -> str:
        """Format bytes in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} TB"


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global checker instance
_checker = None


def get_checker() -> HealthChecker:
    """Get or create global health checker"""
    global _checker
    if _checker is None:
        _checker = HealthChecker()
    return _checker


def check_system_health() -> Dict[str, Any]:
    """Quick function to check system health"""
    checker = get_checker()
    return checker.check_system_health()


def check_redis_health() -> ComponentHealth:
    """Quick function to check Redis health"""
    checker = get_checker()
    return checker.check_redis_health()


def check_agents_health() -> ComponentHealth:
    """Quick function to check agents health"""
    checker = get_checker()
    return checker.check_agents_health()


def check_queue_health() -> ComponentHealth:
    """Quick function to check queue health"""
    checker = get_checker()
    return checker.check_queue_health()


def get_health_endpoint() -> Tuple[int, Dict[str, Any]]:
    """
    Get health status for HTTP endpoint

    Returns:
        Tuple of (HTTP status code, health data)
    """
    health = check_system_health()

    # Map health status to HTTP codes
    status_codes = {
        "healthy": 200,
        "degraded": 200,  # Still return 200 for degraded
        "unhealthy": 503,
        "unknown": 503
    }

    http_code = status_codes.get(health["status"], 503)
    return http_code, health


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("🧪 Testing Health Check Module...")

    # Create checker
    checker = HealthChecker()

    # Run comprehensive check
    health = check_system_health()

    # Pretty print results
    print("\n" + "=" * 60)
    print(f"SYSTEM HEALTH: {health['status'].upper()}")
    print("=" * 60)
    print(f"Message: {health['message']}")
    print(f"Uptime: {health['uptime_human']}")
    print(f"\nComponent Summary:")
    for status, count in health['summary'].items():
        if count > 0:
            print(f"  {status}: {count}")

    print(f"\nComponent Details:")
    for name, component in health['components'].items():
        status_icon = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌",
            "unknown": "❓"
        }.get(component['status'], "❓")

        print(f"\n  {status_icon} {name.upper()}")
        print(f"     Status: {component['status']}")
        print(f"     Message: {component['message']}")

        if component.get('details'):
            for key, value in component['details'].items():
                if not isinstance(value, dict):
                    print(f"     {key}: {value}")

    # Test endpoint
    code, data = get_health_endpoint()
    print(f"\n🌐 HTTP Endpoint: {code} {['OK' if code == 200 else 'SERVICE UNAVAILABLE'][0]}")

    print("\n✅ Health check module ready!")