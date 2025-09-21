#!/usr/bin/env python3
"""
Bridge between MCP v2 Server and Distributed Queue System
Enables MCP to submit tasks to the queue and receive results
"""

import asyncio
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from start_queue_system import QueueSystemActivator
from core.distributed_queue import TaskPriority, TaskState

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPQueueBridge:
    """Bridge between MCP v2 and Distributed Queue System"""

    def __init__(self, mcp_server_url="http://localhost:8099", use_redis=False):
        """
        Initialize the bridge

        Args:
            mcp_server_url: URL of the MCP v2 server
            use_redis: Whether to use Redis for queue backend
        """
        self.mcp_server_url = mcp_server_url
        self.queue_system = QueueSystemActivator(use_redis=use_redis)
        self.task_mapping = {}  # Maps MCP request IDs to queue task IDs
        self.reverse_mapping = {}  # Maps queue task IDs to MCP request IDs
        self._running = False

    async def start(self):
        """Start the bridge"""
        logger.info("🌉 Starting MCP-Queue Bridge...")

        # Start queue system
        if not self.queue_system.start():
            logger.error("Failed to start queue system")
            return False

        # Start monitoring loops
        self._running = True
        asyncio.create_task(self._monitor_mcp_requests())
        asyncio.create_task(self._monitor_queue_results())

        logger.info("✅ MCP-Queue Bridge started successfully")
        return True

    async def _monitor_mcp_requests(self):
        """Monitor MCP for new collaboration requests and submit to queue"""
        while self._running:
            try:
                # Check MCP for pending collaboration requests
                response = await self._call_mcp_tool("get_collaborations", {
                    "status": "pending"
                })

                if response and 'result' in response:
                    requests = response['result'].get('requests', [])

                    for req in requests:
                        await self._process_mcp_request(req)

                await asyncio.sleep(2)  # Check every 2 seconds

            except Exception as e:
                logger.error(f"Error monitoring MCP requests: {e}")
                await asyncio.sleep(5)

    async def _process_mcp_request(self, mcp_request: Dict[str, Any]):
        """Process an MCP collaboration request and submit to queue"""
        request_id = mcp_request.get('request_id')

        # Check if already processed
        if request_id in self.task_mapping:
            return

        logger.info(f"📥 Processing MCP request: {request_id}")

        # Extract task details
        from_agent = mcp_request.get('from_agent', 'unknown')
        to_agent = mcp_request.get('to_agent', 'unknown')
        task = mcp_request.get('task', '')
        priority = mcp_request.get('priority', 'normal').upper()
        metadata = mcp_request.get('metadata', {})

        # Submit to queue
        queue_task_id = self.queue_system.submit_task(
            agent=to_agent,
            task_name=f"mcp_task_{request_id[:8]}",
            payload={
                'mcp_request_id': request_id,
                'from_agent': from_agent,
                'task': task,
                'metadata': metadata
            },
            priority=priority
        )

        # Store mapping
        self.task_mapping[request_id] = queue_task_id
        self.reverse_mapping[queue_task_id] = request_id

        # Update MCP status
        await self._update_mcp_status(request_id, 'queued')

        logger.info(f"✅ MCP request {request_id} submitted to queue as {queue_task_id}")

    async def _monitor_queue_results(self):
        """Monitor queue for completed tasks and update MCP"""
        while self._running:
            try:
                # Check queue status
                status = self.queue_system.queue.get_queue_status()

                # Process completed tasks
                for queue_task_id in self.reverse_mapping:
                    task_status = self.queue_system.queue.get_status(queue_task_id)

                    if task_status and task_status['state'] == 'COMPLETED':
                        await self._process_completed_task(queue_task_id, task_status)
                    elif task_status and task_status['state'] == 'FAILED':
                        await self._process_failed_task(queue_task_id, task_status)

                await asyncio.sleep(3)  # Check every 3 seconds

            except Exception as e:
                logger.error(f"Error monitoring queue results: {e}")
                await asyncio.sleep(5)

    async def _process_completed_task(self, queue_task_id: str, task_status: Dict[str, Any]):
        """Process a completed task and update MCP"""
        mcp_request_id = self.reverse_mapping.get(queue_task_id)
        if not mcp_request_id:
            return

        logger.info(f"✅ Task {queue_task_id} completed, updating MCP {mcp_request_id}")

        # Update MCP with result
        result = task_status.get('result', {})
        await self._complete_mcp_request(mcp_request_id, result)

        # Clean up mappings
        del self.reverse_mapping[queue_task_id]
        del self.task_mapping[mcp_request_id]

    async def _process_failed_task(self, queue_task_id: str, task_status: Dict[str, Any]):
        """Process a failed task and update MCP"""
        mcp_request_id = self.reverse_mapping.get(queue_task_id)
        if not mcp_request_id:
            return

        logger.warning(f"❌ Task {queue_task_id} failed, updating MCP {mcp_request_id}")

        # Update MCP with error
        error = task_status.get('error', 'Unknown error')
        await self._fail_mcp_request(mcp_request_id, error)

        # Clean up mappings
        del self.reverse_mapping[queue_task_id]
        del self.task_mapping[mcp_request_id]

    async def _call_mcp_tool(self, tool_name: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Call an MCP tool via JSON-RPC"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": params
                },
                "id": str(uuid.uuid4())
            }

            response = requests.post(
                f"{self.mcp_server_url}/jsonrpc",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=5
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"MCP call failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return None

    async def _update_mcp_status(self, request_id: str, status: str):
        """Update collaboration request status in MCP"""
        # Since MCP doesn't have a direct update_collaboration tool,
        # we'll use the propose_decision tool to record status changes
        await self._call_mcp_tool("propose_decision", {
            "agent": "queue-bridge",
            "decision": f"Task {request_id} status: {status}",
            "confidence": 1.0,
            "alternatives": []
        })

    async def _complete_mcp_request(self, request_id: str, result: Dict[str, Any]):
        """Mark MCP request as completed"""
        await self._call_mcp_tool("propose_decision", {
            "agent": "queue-bridge",
            "decision": f"Task {request_id} completed",
            "confidence": 1.0,
            "alternatives": [],
            "metadata": {
                "request_id": request_id,
                "status": "completed",
                "result": result
            }
        })

    async def _fail_mcp_request(self, request_id: str, error: str):
        """Mark MCP request as failed"""
        await self._call_mcp_tool("propose_decision", {
            "agent": "queue-bridge",
            "decision": f"Task {request_id} failed: {error}",
            "confidence": 0.0,
            "alternatives": ["retry", "reassign"],
            "metadata": {
                "request_id": request_id,
                "status": "failed",
                "error": error
            }
        })

    def submit_task_from_mcp(self, from_agent: str, to_agent: str, task: str,
                            priority: str = "normal") -> str:
        """
        Direct method to submit a task from MCP to queue

        Args:
            from_agent: Agent requesting the task
            to_agent: Agent to execute the task
            task: Task description
            priority: Task priority

        Returns:
            Task ID
        """
        # Generate MCP request ID
        request_id = f"mcp_{uuid.uuid4().hex[:8]}"

        # Submit to queue
        queue_task_id = self.queue_system.submit_task(
            agent=to_agent,
            task_name=f"mcp_direct_{from_agent}",
            payload={
                'mcp_request_id': request_id,
                'from_agent': from_agent,
                'task': task,
                'submitted_at': datetime.now().isoformat()
            },
            priority=priority.upper()
        )

        # Store mapping
        self.task_mapping[request_id] = queue_task_id
        self.reverse_mapping[queue_task_id] = request_id

        logger.info(f"📤 Direct task from {from_agent} to {to_agent}: {queue_task_id}")
        return queue_task_id

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get status of a task (either MCP request ID or queue task ID)"""
        # Check if it's an MCP request ID
        if task_id in self.task_mapping:
            queue_task_id = self.task_mapping[task_id]
            return self.queue_system.queue.get_status(queue_task_id)

        # Check if it's a queue task ID
        return self.queue_system.queue.get_status(task_id)

    async def stop(self):
        """Stop the bridge"""
        logger.info("Stopping MCP-Queue Bridge...")
        self._running = False
        self.queue_system.stop()
        logger.info("MCP-Queue Bridge stopped")


async def test_bridge():
    """Test the MCP-Queue bridge"""
    bridge = MCPQueueBridge(use_redis=False)

    # Start bridge
    if not await bridge.start():
        logger.error("Failed to start bridge")
        return

    logger.info("\n🧪 Testing MCP-Queue Bridge...")

    # Test direct task submission
    task1 = bridge.submit_task_from_mcp(
        from_agent="supervisor",
        to_agent="backend-api",
        task="Implement /api/users endpoint",
        priority="high"
    )

    task2 = bridge.submit_task_from_mcp(
        from_agent="backend-api",
        to_agent="database",
        task="Create users table schema",
        priority="critical"
    )

    task3 = bridge.submit_task_from_mcp(
        from_agent="supervisor",
        to_agent="frontend-ui",
        task="Create login form component",
        priority="normal"
    )

    logger.info(f"✅ Submitted test tasks: {task1}, {task2}, {task3}")

    # Wait for processing
    await asyncio.sleep(5)

    # Check status
    for task_id in [task1, task2, task3]:
        status = bridge.get_task_status(task_id)
        if status:
            logger.info(f"Task {task_id}: {status['state']}")

    # Stop bridge
    await bridge.stop()


def integrate_with_mcp_server():
    """
    Integration function to be called from MCP server
    Returns a configured bridge instance
    """
    bridge = MCPQueueBridge(use_redis=False)

    async def start_bridge():
        await bridge.start()
        return bridge

    return asyncio.run(start_bridge())


if __name__ == "__main__":
    # Run test
    asyncio.run(test_bridge())