#!/usr/bin/env python3
"""
Integration test script for Claude Multi-Agent System
Tests the complete flow from API to agents to results
"""

import asyncio
import json
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.message_bus import get_message_bus
from core.workflow_engine import get_workflow_engine
from agents.agent_bridge import get_bridge_manager
from core.tmux_client import TMUXClient
from config.settings import AGENT_SESSIONS
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegrationTest:
    """Test complete system integration"""

    def __init__(self):
        self.message_bus = get_message_bus()
        self.workflow_engine = get_workflow_engine()
        self.bridge_manager = get_bridge_manager()
        self.tmux_client = TMUXClient()
        self.test_results = []

    def setup(self):
        """Setup test environment"""
        logger.info("Setting up integration test environment...")

        # Start message bus
        if not self.message_bus.running:
            self.message_bus.start()
            logger.info("✓ Message bus started")

        # Create TMUX sessions for agents
        for agent_name, session_name in AGENT_SESSIONS.items():
            if not self.tmux_client.session_exists(session_name):
                self.tmux_client.create_session(session_name)
                logger.info(f"✓ Created TMUX session: {session_name}")

                # Send initial command to mark session as ready
                self.tmux_client.send_command(
                    session_name,
                    f"echo 'Agent {agent_name} ready for tasks'"
                )

        # Start agent bridges
        self.bridge_manager.start_all()
        logger.info(f"✓ Started {len(self.bridge_manager.bridges)} agent bridges")

        time.sleep(2)  # Allow everything to initialize
        logger.info("Setup complete!")

    def test_simple_task(self):
        """Test simple task execution"""
        logger.info("\n=== Testing Simple Task Execution ===")

        # Submit task
        task_id = self.message_bus.publish_task(
            agent="backend-api",
            task={
                "command": "echo 'Hello from backend agent'",
                "params": {},
                "timeout": 10
            }
        )
        logger.info(f"Submitted task: {task_id}")

        # Wait for result
        start_time = time.time()
        timeout = 15

        while time.time() - start_time < timeout:
            status = self.message_bus.get_task_status(task_id)
            if status and status['status'] in ['completed', 'failed']:
                if status['status'] == 'completed':
                    logger.info(f"✓ Task completed successfully")
                    self.test_results.append(("simple_task", True, None))
                else:
                    logger.error(f"✗ Task failed: {status}")
                    self.test_results.append(("simple_task", False, status))
                return status['status'] == 'completed'
            time.sleep(1)

        logger.error("✗ Task timed out")
        self.test_results.append(("simple_task", False, "Timeout"))
        return False

    def test_multi_agent_coordination(self):
        """Test coordination between multiple agents"""
        logger.info("\n=== Testing Multi-Agent Coordination ===")

        tasks = []

        # Submit tasks to different agents
        for agent in ["backend-api", "database", "frontend-ui"]:
            task_id = self.message_bus.publish_task(
                agent=agent,
                task={
                    "command": f"echo 'Processing in {agent}'",
                    "params": {"test": True},
                    "timeout": 10
                }
            )
            tasks.append((agent, task_id))
            logger.info(f"Submitted task to {agent}: {task_id}")

        # Wait for all tasks
        timeout = 20
        start_time = time.time()
        completed = []

        while time.time() - start_time < timeout and len(completed) < len(tasks):
            for agent, task_id in tasks:
                if task_id not in completed:
                    status = self.message_bus.get_task_status(task_id)
                    if status and status['status'] == 'completed':
                        completed.append(task_id)
                        logger.info(f"✓ {agent} task completed")
            time.sleep(1)

        success = len(completed) == len(tasks)
        if success:
            logger.info("✓ All agents completed tasks successfully")
            self.test_results.append(("multi_agent", True, None))
        else:
            logger.error(f"✗ Only {len(completed)}/{len(tasks)} tasks completed")
            self.test_results.append(("multi_agent", False, f"{len(completed)}/{len(tasks)}"))

        return success

    def test_workflow_execution(self):
        """Test workflow engine execution"""
        logger.info("\n=== Testing Workflow Execution ===")

        # Define simple workflow
        workflow_def = {
            "name": "Test Workflow",
            "description": "Integration test workflow",
            "steps": [
                {
                    "id": "step1",
                    "name": "First Step",
                    "agent": "supervisor",
                    "action": "echo 'Starting workflow'",
                    "params": {}
                },
                {
                    "id": "step2",
                    "name": "Parallel Step A",
                    "agent": "backend-api",
                    "action": "echo 'Backend processing'",
                    "params": {},
                    "depends_on": ["step1"]
                },
                {
                    "id": "step3",
                    "name": "Parallel Step B",
                    "agent": "database",
                    "action": "echo 'Database processing'",
                    "params": {},
                    "depends_on": ["step1"]
                },
                {
                    "id": "step4",
                    "name": "Final Step",
                    "agent": "supervisor",
                    "action": "echo 'Workflow complete'",
                    "params": {},
                    "depends_on": ["step2", "step3"]
                }
            ]
        }

        try:
            # Define and execute workflow
            workflow_id = self.workflow_engine.define_workflow(workflow_def)
            logger.info(f"Defined workflow: {workflow_id}")

            execution_id = self.workflow_engine.execute(workflow_id, {})
            logger.info(f"Started execution: {execution_id}")

            # Monitor execution
            timeout = 30
            start_time = time.time()

            while time.time() - start_time < timeout:
                status = self.workflow_engine.get_execution_status(execution_id)
                if status:
                    # Log step progress
                    for step_id, step_status in status['steps'].items():
                        if step_status['status'] == 'completed':
                            logger.info(f"  ✓ {step_status['name']} completed")

                    if status['status'] in ['completed', 'failed']:
                        if status['status'] == 'completed':
                            logger.info("✓ Workflow completed successfully")
                            self.test_results.append(("workflow", True, None))
                        else:
                            logger.error(f"✗ Workflow failed: {status.get('error')}")
                            self.test_results.append(("workflow", False, status.get('error')))
                        return status['status'] == 'completed'

                time.sleep(2)

            logger.error("✗ Workflow execution timed out")
            self.test_results.append(("workflow", False, "Timeout"))
            return False

        except Exception as e:
            logger.error(f"✗ Workflow test failed: {e}")
            self.test_results.append(("workflow", False, str(e)))
            return False

    def test_error_handling(self):
        """Test error handling and recovery"""
        logger.info("\n=== Testing Error Handling ===")

        # Submit task that will fail
        task_id = self.message_bus.publish_task(
            agent="backend-api",
            task={
                "command": "false",  # Command that returns error
                "params": {},
                "timeout": 5
            }
        )
        logger.info(f"Submitted failing task: {task_id}")

        # Wait for failure
        start_time = time.time()
        timeout = 10

        while time.time() - start_time < timeout:
            status = self.message_bus.get_task_status(task_id)
            if status and status['status'] == 'failed':
                logger.info("✓ Error correctly detected and handled")
                self.test_results.append(("error_handling", True, None))
                return True
            time.sleep(1)

        logger.error("✗ Error handling test failed")
        self.test_results.append(("error_handling", False, "No error detected"))
        return False

    def test_agent_status_updates(self):
        """Test agent status tracking"""
        logger.info("\n=== Testing Agent Status Updates ===")

        success = True
        for agent_name in ["supervisor", "backend-api", "database"]:
            status = self.message_bus.get_agent_status(agent_name)
            if status:
                logger.info(f"✓ {agent_name}: {status.get('status', 'unknown')}")
            else:
                logger.error(f"✗ No status for {agent_name}")
                success = False

        if success:
            logger.info("✓ All agent statuses tracked correctly")
            self.test_results.append(("agent_status", True, None))
        else:
            logger.error("✗ Some agent statuses missing")
            self.test_results.append(("agent_status", False, "Missing statuses"))

        return success

    def cleanup(self):
        """Cleanup test environment"""
        logger.info("\nCleaning up...")

        # Stop bridges
        self.bridge_manager.stop_all()

        # Stop message bus
        self.message_bus.stop()

        logger.info("Cleanup complete")

    def run_all_tests(self):
        """Run all integration tests"""
        logger.info("=" * 60)
        logger.info("Starting Claude Multi-Agent System Integration Tests")
        logger.info("=" * 60)

        try:
            # Setup
            self.setup()

            # Run tests
            tests = [
                self.test_simple_task,
                self.test_multi_agent_coordination,
                self.test_workflow_execution,
                self.test_error_handling,
                self.test_agent_status_updates
            ]

            for test in tests:
                try:
                    test()
                    time.sleep(2)  # Brief pause between tests
                except Exception as e:
                    logger.error(f"Test failed with exception: {e}")
                    self.test_results.append((test.__name__, False, str(e)))

        finally:
            # Cleanup
            self.cleanup()

            # Report results
            self.report_results()

    def report_results(self):
        """Report test results"""
        logger.info("\n" + "=" * 60)
        logger.info("Integration Test Results")
        logger.info("=" * 60)

        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)

        for test_name, success, error in self.test_results:
            status = "✓ PASSED" if success else "✗ FAILED"
            logger.info(f"{test_name:20} {status}")
            if error:
                logger.info(f"  Error: {error}")

        logger.info("-" * 60)
        logger.info(f"Total: {passed}/{total} tests passed")

        if passed == total:
            logger.info("\n🎉 All integration tests passed!")
        else:
            logger.warning(f"\n⚠️  {total - passed} tests failed")

        return passed == total


async def test_api_integration():
    """Test API Gateway integration"""
    import httpx

    logger.info("\n=== Testing API Gateway Integration ===")

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        try:
            # Test health endpoint
            response = await client.get("/health")
            if response.status_code == 200:
                logger.info("✓ API Gateway is healthy")
            else:
                logger.error(f"✗ API Gateway health check failed: {response.status_code}")

            # Test agent listing
            response = await client.get("/agents")
            if response.status_code == 200:
                agents = response.json()["agents"]
                logger.info(f"✓ Found {len(agents)} agents via API")
            else:
                logger.error(f"✗ Failed to list agents: {response.status_code}")

        except Exception as e:
            logger.error(f"✗ API Gateway test failed: {e}")


def main():
    """Main entry point"""
    # Run integration tests
    tester = IntegrationTest()
    success = tester.run_all_tests()

    # Test API if available
    try:
        asyncio.run(test_api_integration())
    except Exception as e:
        logger.warning(f"API Gateway test skipped: {e}")

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()