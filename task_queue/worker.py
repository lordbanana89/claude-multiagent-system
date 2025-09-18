#!/usr/bin/env python3
"""
Dramatiq Worker - Processes messages from the Redis queue
Run with: python -m dramatiq task_queue.worker
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import broker and actors to register them
from task_queue.broker import broker
from task_queue.actors import (
    process_agent_command,
    broadcast_message,
    execute_task,
    notify_agent,
    handle_failed_task
)

# Log startup
logger = logging.getLogger(__name__)
logger.info("=" * 60)
logger.info("🎬 Dramatiq Worker Starting")
logger.info(f"Broker: {type(broker).__name__}")
logger.info("Registered actors:")
logger.info("  - process_agent_command")
logger.info("  - broadcast_message")
logger.info("  - execute_task")
logger.info("  - notify_agent")
logger.info("  - handle_failed_task")
logger.info("=" * 60)
logger.info("Worker ready! Waiting for messages...")

# The worker will be started by Dramatiq when running:
# python -m dramatiq task_queue.worker