"""
Dramatiq Broker Configuration with Redis Backend
Production-ready message broker setup
"""

import os
import logging
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import (
    AgeLimit,
    Callbacks,
    Pipelines,
    Prometheus,
    Retries,
    ShutdownNotifications,
    TimeLimit
)
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import (
    REDIS_URL,
    QUEUE_MAX_RETRIES,
    QUEUE_RETRY_DELAY,
    QUEUE_MESSAGE_TTL,
    DEBUG
)

# Configure logging
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger(__name__)


def setup_broker(redis_url: str = None,
                 namespace: str = "dramatiq",
                 middleware_options: dict = None) -> RedisBroker:
    """
    Setup and configure the Dramatiq broker with Redis backend

    Args:
        redis_url: Redis connection URL (defaults to config.REDIS_URL)
        namespace: Redis key namespace for Dramatiq
        middleware_options: Additional middleware configuration

    Returns:
        Configured RedisBroker instance
    """
    url = redis_url or REDIS_URL

    # Create Redis broker
    redis_broker = RedisBroker(
        url=url,
        namespace=namespace,
    )

    # Configure middleware
    middleware_config = middleware_options or {}

    # Remove default middleware we want to reconfigure
    redis_broker.middleware = [
        m for m in redis_broker.middleware
        if not isinstance(m, (AgeLimit, TimeLimit, ShutdownNotifications, Retries))
    ]

    # Add middleware with our configuration
    redis_broker.add_middleware(
        AgeLimit(max_age=middleware_config.get("max_age", QUEUE_MESSAGE_TTL * 1000))
    )

    redis_broker.add_middleware(
        TimeLimit(time_limit=middleware_config.get("time_limit", 600000))  # 10 minutes
    )

    redis_broker.add_middleware(
        Retries(
            max_retries=middleware_config.get("max_retries", QUEUE_MAX_RETRIES),
            min_backoff=middleware_config.get("min_backoff", QUEUE_RETRY_DELAY * 1000),
            max_backoff=middleware_config.get("max_backoff", QUEUE_RETRY_DELAY * 10 * 1000)
            # Note: retries_exceeded parameter not supported in current version
        )
    )

    redis_broker.add_middleware(ShutdownNotifications(notify_shutdown=True))
    redis_broker.add_middleware(Callbacks())
    redis_broker.add_middleware(Pipelines())

    # Add Prometheus metrics if enabled
    if middleware_config.get("prometheus", False):
        redis_broker.add_middleware(
            Prometheus(http_port=middleware_config.get("prometheus_port", 9191))
        )

    # Set as global broker
    dramatiq.set_broker(redis_broker)

    logger.info(f"✅ Dramatiq broker configured with Redis at {url}")

    return redis_broker


# Create default broker instance
try:
    broker = setup_broker()
except Exception as e:
    logger.error(f"⚠️  Failed to setup Redis broker: {e}")
    logger.warning("Falling back to stub broker for testing")
    from dramatiq.brokers.stub import StubBroker
    broker = StubBroker()
    dramatiq.set_broker(broker)


# Dead Letter Queue handler
@dramatiq.actor(queue_name="dead_letter_queue", max_retries=0)
def handle_failed_message(message_data: dict):
    """
    Process messages that failed after all retries

    Args:
        message_data: Failed message information
    """
    logger.error(f"📥 Dead Letter Queue received: {message_data}")

    # Here you could:
    # - Log to external service
    # - Send alerts
    # - Store in database for manual review
    # - Attempt different processing strategy

    # For now, just log
    import json
    from datetime import datetime

    dlq_log_path = Path("logs/dlq.jsonl")
    dlq_log_path.parent.mkdir(exist_ok=True)

    with open(dlq_log_path, "a") as f:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message_data,
        }
        f.write(json.dumps(log_entry) + "\n")


# Health check
def check_broker_health() -> dict:
    """
    Check health of the broker and Redis connection

    Returns:
        Health status dictionary
    """
    health = {
        "status": "unknown",
        "broker_type": type(broker).__name__,
        "redis_url": REDIS_URL,
        "errors": []
    }

    try:
        # Try to get Redis info
        if hasattr(broker, 'client'):
            info = broker.client.info()
            health["redis_version"] = info.get("redis_version", "unknown")
            health["used_memory_human"] = info.get("used_memory_human", "unknown")
            health["connected_clients"] = info.get("connected_clients", 0)
            health["status"] = "healthy"
        else:
            health["status"] = "degraded"
            health["errors"].append("Not a Redis broker")

    except Exception as e:
        health["status"] = "unhealthy"
        health["errors"].append(str(e))

    return health


if __name__ == "__main__":
    # Test broker setup
    print("🧪 Testing Dramatiq broker setup...")

    health = check_broker_health()
    print(f"\n📊 Broker Health:")
    for key, value in health.items():
        if key != "errors":
            print(f"  {key}: {value}")

    if health["errors"]:
        print(f"  ⚠️  Errors: {health['errors']}")

    if health["status"] == "healthy":
        print("\n✅ Broker is healthy and ready!")
    else:
        print(f"\n⚠️  Broker status: {health['status']}")