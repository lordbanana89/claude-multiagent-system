#!/usr/bin/env python3
"""
Adapter to integrate existing Orchestrators with MCP v2
Enables orchestrators to receive tasks from MCP and delegate via tmux
"""

import asyncio
import json
import logging
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import requests
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.claude_orchestrator import ClaudeNativeOrchestrator
from mcp_server_v2_full import MCPServerV2Full

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPOrchestratorAdapter:
    """Adapter to bridge MCP v2 with existing orchestrators"""

    def __init__(self, mcp_server_url="http://localhost:8099"):
        """Initialize the adapter"""
        self.mcp_server_url = mcp_server_url
        self.orchestrator = ClaudeNativeOrchestrator()
        self.active_tasks = {}  # Track active delegations
        self._running = False

    async def start(self):
        """Start the adapter"""
        logger.info("🚀 Starting MCP-Orchestrator Adapter...")

        # Orchestrator is already initialized in __init__

        # Start monitoring loops
        self._running = True
        asyncio.create_task(self._monitor_mcp_tasks())
        asyncio.create_task(self._monitor_agent_responses())

        logger.info("✅ MCP-Orchestrator Adapter started")
        return True

    async def _monitor_mcp_tasks(self):
        """Monitor MCP for tasks that need orchestration"""
        while self._running:
            try:
                # Check for collaboration requests targeting supervisor
                response = await self._call_mcp_tool("find_component_owner", {
                    "component": "orchestration"
                })

                if response and 'result' in response:
                    owner = response['result'].get('owner')
                    if owner == 'supervisor':
                        # Get pending collaborations for supervisor
                        await self._process_pending_collaborations()

                await asyncio.sleep(3)

            except Exception as e:
                logger.error(f"Error monitoring MCP tasks: {e}")
                await asyncio.sleep(5)

    async def _process_pending_collaborations(self):
        """Process pending collaboration requests"""
        # This would normally query MCP for pending requests
        # For now, we'll simulate by checking a specific pattern

        # In a real implementation, you'd query MCP's database
        # or have a specific endpoint for pending tasks
        pass

    async def delegate_task(self, task: Dict[str, Any]) -> str:
        """
        Delegate a task using the orchestrator

        Args:
            task: Task details including target agent, description, priority

        Returns:
            Task ID
        """
        task_id = task.get('id', str(uuid.uuid4()))
        from_agent = task.get('from_agent', 'mcp-system')
        to_agent = task.get('to_agent', 'supervisor')
        description = task.get('task', '')
        priority = task.get('priority', 'normal')

        logger.info(f"📋 Delegating task {task_id} to {to_agent}")

        # Register in MCP
        mcp_request = await self._register_mcp_collaboration(
            from_agent, to_agent, description, priority
        )

        if mcp_request:
            request_id = mcp_request.get('request_id')
            self.active_tasks[request_id] = {
                'task_id': task_id,
                'to_agent': to_agent,
                'description': description,
                'status': 'delegated',
                'delegated_at': datetime.now().isoformat()
            }

            # Delegate via orchestrator
            success = self.orchestrator.send_task_to_claude(
                session_name=to_agent,
                task=f"[{request_id}] {description}",
                context=f"Priority: {priority}"
            )

            if success:
                logger.info(f"✅ Task {request_id} delegated to {to_agent}")

                # Update MCP status
                await self._update_mcp_status(to_agent, 'busy', f"Working on {request_id}")
            else:
                logger.error(f"❌ Failed to delegate task {request_id}")
                self.active_tasks[request_id]['status'] = 'failed'

            return request_id

        return None

    async def _monitor_agent_responses(self):
        """Monitor agent terminals for responses"""
        while self._running:
            try:
                for request_id, task_info in list(self.active_tasks.items()):
                    if task_info['status'] == 'delegated':
                        agent = task_info['to_agent']

                        # Capture agent output
                        output = self._capture_agent_output(agent)

                        # Check for completion patterns
                        if self._is_task_completed(output, request_id):
                            await self._process_completion(request_id, output)
                        elif self._is_task_failed(output, request_id):
                            await self._process_failure(request_id, output)

                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Error monitoring agent responses: {e}")
                await asyncio.sleep(5)

    def _capture_agent_output(self, agent: str) -> str:
        """Capture output from agent's tmux session"""
        try:
            result = subprocess.run(
                ['tmux', 'capture-pane', '-t', f'claude-{agent}', '-p'],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.stdout
        except Exception as e:
            logger.error(f"Error capturing output from {agent}: {e}")
            return ""

    def _is_task_completed(self, output: str, request_id: str) -> bool:
        """Check if task is completed in output"""
        completion_patterns = [
            f"COMPLETED: {request_id}",
            f"Task {request_id} completed",
            f"✅ {request_id}",
            f"Done: {request_id}"
        ]
        return any(pattern in output for pattern in completion_patterns)

    def _is_task_failed(self, output: str, request_id: str) -> bool:
        """Check if task failed in output"""
        failure_patterns = [
            f"FAILED: {request_id}",
            f"ERROR: {request_id}",
            f"❌ {request_id}",
            f"Cannot complete {request_id}"
        ]
        return any(pattern in output for pattern in failure_patterns)

    async def _process_completion(self, request_id: str, output: str):
        """Process task completion"""
        task_info = self.active_tasks.get(request_id)
        if not task_info:
            return

        logger.info(f"✅ Task {request_id} completed by {task_info['to_agent']}")

        # Update task status
        task_info['status'] = 'completed'
        task_info['completed_at'] = datetime.now().isoformat()
        task_info['result'] = self._extract_result(output, request_id)

        # Update MCP
        await self._complete_mcp_collaboration(request_id, task_info['result'])

        # Update agent status
        await self._update_mcp_status(task_info['to_agent'], 'idle', '')

        # Remove from active tasks
        del self.active_tasks[request_id]

    async def _process_failure(self, request_id: str, output: str):
        """Process task failure"""
        task_info = self.active_tasks.get(request_id)
        if not task_info:
            return

        logger.error(f"❌ Task {request_id} failed for {task_info['to_agent']}")

        # Update task status
        task_info['status'] = 'failed'
        task_info['failed_at'] = datetime.now().isoformat()
        task_info['error'] = self._extract_error(output, request_id)

        # Update MCP
        await self._fail_mcp_collaboration(request_id, task_info['error'])

        # Update agent status
        await self._update_mcp_status(task_info['to_agent'], 'error', task_info['error'])

        # Remove from active tasks
        del self.active_tasks[request_id]

    def _extract_result(self, output: str, request_id: str) -> str:
        """Extract result from output"""
        # Look for result after completion marker
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if request_id in line and 'COMPLETED' in line:
                # Return next few lines as result
                return '\n'.join(lines[i+1:min(i+5, len(lines))])
        return "Task completed successfully"

    def _extract_error(self, output: str, request_id: str) -> str:
        """Extract error from output"""
        # Look for error after failure marker
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if request_id in line and ('FAILED' in line or 'ERROR' in line):
                # Return next few lines as error
                return '\n'.join(lines[i+1:min(i+5, len(lines))])
        return "Task failed with unknown error"

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

        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")

        return None

    async def _register_mcp_collaboration(self, from_agent: str, to_agent: str,
                                         task: str, priority: str) -> Optional[Dict]:
        """Register collaboration request in MCP"""
        response = await self._call_mcp_tool("request_collaboration", {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "task": task,
            "priority": priority
        })

        if response and 'result' in response:
            return response['result']
        return None

    async def _update_mcp_status(self, agent: str, status: str, activity: str):
        """Update agent status in MCP"""
        await self._call_mcp_tool("update_status", {
            "agent": agent,
            "status": status,
            "current_task": activity
        })

    async def _complete_mcp_collaboration(self, request_id: str, result: str):
        """Mark collaboration as completed in MCP"""
        await self._call_mcp_tool("propose_decision", {
            "agent": "orchestrator",
            "decision": f"Task {request_id} completed",
            "confidence": 1.0,
            "alternatives": [],
            "metadata": {
                "request_id": request_id,
                "status": "completed",
                "result": result
            }
        })

    async def _fail_mcp_collaboration(self, request_id: str, error: str):
        """Mark collaboration as failed in MCP"""
        await self._call_mcp_tool("propose_decision", {
            "agent": "orchestrator",
            "decision": f"Task {request_id} failed",
            "confidence": 0.0,
            "alternatives": ["retry", "reassign"],
            "metadata": {
                "request_id": request_id,
                "status": "failed",
                "error": error
            }
        })

    async def stop(self):
        """Stop the adapter"""
        logger.info("Stopping MCP-Orchestrator Adapter...")
        self._running = False
        logger.info("MCP-Orchestrator Adapter stopped")


async def test_orchestration():
    """Test the orchestration adapter"""
    adapter = MCPOrchestratorAdapter()

    # Start adapter
    if not await adapter.start():
        logger.error("Failed to start adapter")
        return

    logger.info("\n🧪 Testing MCP-Orchestrator Integration...")

    # Test task delegation
    test_tasks = [
        {
            'from_agent': 'mcp-test',
            'to_agent': 'backend-api',
            'task': 'Create REST endpoint for user authentication',
            'priority': 'high'
        },
        {
            'from_agent': 'mcp-test',
            'to_agent': 'database',
            'task': 'Design schema for user sessions table',
            'priority': 'critical'
        },
        {
            'from_agent': 'mcp-test',
            'to_agent': 'frontend-ui',
            'task': 'Implement login form with validation',
            'priority': 'normal'
        }
    ]

    task_ids = []
    for task in test_tasks:
        task_id = await adapter.delegate_task(task)
        if task_id:
            task_ids.append(task_id)
            logger.info(f"✅ Delegated task: {task_id}")
        else:
            logger.error(f"❌ Failed to delegate task to {task['to_agent']}")

    # Wait for processing
    logger.info("\n⏳ Waiting for agents to process tasks...")
    await asyncio.sleep(10)

    # Check status
    logger.info("\n📊 Current active tasks:")
    for task_id, info in adapter.active_tasks.items():
        logger.info(f"  {task_id}: {info['status']} - {info['to_agent']}")

    # Stop adapter
    await adapter.stop()


if __name__ == "__main__":
    asyncio.run(test_orchestration())