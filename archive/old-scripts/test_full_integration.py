#!/usr/bin/env python3
"""
Full Integration Test for MCP v2 Multi-Agent System
Tests: Queue System + Inbox Bridge + Orchestrator + MCP Server
"""

import asyncio
import json
import logging
import requests
import time
from datetime import datetime
import uuid

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FullIntegrationTest:
    """Complete integration test for all components"""

    def __init__(self):
        self.mcp_url = "http://localhost:8099"
        self.inbox_url = "http://localhost:8098"
        self.test_results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }

    async def run_all_tests(self):
        """Run complete integration test suite"""
        logger.info("=" * 80)
        logger.info("🧪 STARTING FULL INTEGRATION TEST")
        logger.info("=" * 80)

        # Test 1: MCP Server Health
        await self.test_mcp_health()

        # Test 2: Queue System
        await self.test_queue_system()

        # Test 3: Inbox API
        await self.test_inbox_api()

        # Test 4: MCP Tools
        await self.test_mcp_tools()

        # Test 5: End-to-End Flow
        await self.test_end_to_end_flow()

        # Print results
        self.print_test_results()

    async def test_mcp_health(self):
        """Test MCP server health"""
        test_name = "MCP Server Health"
        logger.info(f"\n📋 Test 1: {test_name}")

        try:
            response = requests.get(f"{self.mcp_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.test_results['passed'].append(test_name)
                    logger.info(f"  ✅ MCP Server is healthy")
                    logger.info(f"     Version: {data.get('version', 'unknown')}")
                    logger.info(f"     Tools: {data.get('tools_count', 0)}")
                else:
                    self.test_results['failed'].append(f"{test_name}: Unhealthy status")
                    logger.error(f"  ❌ MCP Server unhealthy: {data}")
            else:
                self.test_results['failed'].append(f"{test_name}: HTTP {response.status_code}")
                logger.error(f"  ❌ MCP Server returned {response.status_code}")
        except Exception as e:
            self.test_results['failed'].append(f"{test_name}: {str(e)}")
            logger.error(f"  ❌ Failed to connect to MCP: {e}")

    async def test_queue_system(self):
        """Test queue system functionality"""
        test_name = "Queue System"
        logger.info(f"\n📋 Test 2: {test_name}")

        try:
            # Import and test queue
            from start_queue_system import QueueSystemActivator

            activator = QueueSystemActivator(use_redis=False)
            if activator.start():
                # Submit test task
                task_id = activator.submit_task(
                    agent='testing',
                    task_name='integration_test',
                    payload={'test': True},
                    priority='HIGH'
                )

                if task_id:
                    self.test_results['passed'].append(test_name)
                    logger.info(f"  ✅ Queue system working, task ID: {task_id}")
                else:
                    self.test_results['failed'].append(f"{test_name}: Task submission failed")
                    logger.error(f"  ❌ Failed to submit task to queue")

                activator.stop()
            else:
                self.test_results['failed'].append(f"{test_name}: Failed to start")
                logger.error(f"  ❌ Queue system failed to start")

        except Exception as e:
            self.test_results['failed'].append(f"{test_name}: {str(e)}")
            logger.error(f"  ❌ Queue system error: {e}")

    async def test_inbox_api(self):
        """Test Inbox API functionality"""
        test_name = "Inbox API"
        logger.info(f"\n📋 Test 3: {test_name}")

        try:
            # Test GET messages
            response = requests.get(f"{self.inbox_url}/api/inbox/messages", timeout=5)
            if response.status_code == 200:
                data = response.json()
                message_count = data.get('total', 0)
                logger.info(f"  ✅ Inbox API working, {message_count} messages")

                # Test POST message
                test_message = {
                    'from': 'Integration Test',
                    'to': 'System',
                    'subject': 'Test Message',
                    'content': 'This is an integration test message',
                    'priority': 'normal',
                    'type': 'notification'
                }

                post_response = requests.post(
                    f"{self.inbox_url}/api/inbox/messages",
                    json=test_message,
                    headers={'Content-Type': 'application/json'}
                )

                if post_response.status_code == 200:
                    self.test_results['passed'].append(test_name)
                    logger.info(f"  ✅ Successfully added test message")
                else:
                    self.test_results['warnings'].append(f"{test_name}: POST failed")
                    logger.warning(f"  ⚠️ Failed to POST message: {post_response.status_code}")
            else:
                self.test_results['failed'].append(f"{test_name}: API not accessible")
                logger.error(f"  ❌ Inbox API returned {response.status_code}")

        except Exception as e:
            self.test_results['failed'].append(f"{test_name}: {str(e)}")
            logger.error(f"  ❌ Inbox API error: {e}")

    async def test_mcp_tools(self):
        """Test MCP v2 tools"""
        test_name = "MCP Tools"
        logger.info(f"\n📋 Test 4: {test_name}")

        tools_tested = 0
        tools_passed = 0

        # Test heartbeat
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "heartbeat",
                    "arguments": {"agent": "test-agent"}
                },
                "id": 1
            }

            response = requests.post(
                f"{self.mcp_url}/jsonrpc",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            tools_tested += 1
            if response.status_code == 200 and 'result' in response.json():
                tools_passed += 1
                logger.info(f"  ✅ Tool 'heartbeat' working")
            else:
                logger.error(f"  ❌ Tool 'heartbeat' failed")

        except Exception as e:
            logger.error(f"  ❌ Error testing heartbeat: {e}")

        # Test update_status
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "update_status",
                    "arguments": {
                        "agent": "test-agent",
                        "status": "testing"
                    }
                },
                "id": 2
            }

            response = requests.post(
                f"{self.mcp_url}/jsonrpc",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            tools_tested += 1
            if response.status_code == 200 and 'result' in response.json():
                tools_passed += 1
                logger.info(f"  ✅ Tool 'update_status' working")
            else:
                logger.error(f"  ❌ Tool 'update_status' failed")

        except Exception as e:
            logger.error(f"  ❌ Error testing update_status: {e}")

        # Evaluate results
        if tools_passed == tools_tested:
            self.test_results['passed'].append(test_name)
            logger.info(f"  ✅ All {tools_tested} tools tested successfully")
        elif tools_passed > 0:
            self.test_results['warnings'].append(f"{test_name}: {tools_passed}/{tools_tested} passed")
            logger.warning(f"  ⚠️ {tools_passed}/{tools_tested} tools working")
        else:
            self.test_results['failed'].append(f"{test_name}: All tools failed")
            logger.error(f"  ❌ All tools failed")

    async def test_end_to_end_flow(self):
        """Test complete end-to-end flow"""
        test_name = "End-to-End Flow"
        logger.info(f"\n📋 Test 5: {test_name}")

        try:
            # Step 1: Create MCP collaboration request
            logger.info("  Step 1: Creating MCP collaboration request...")
            request_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "request_collaboration",
                    "arguments": {
                        "from_agent": "integration-test",
                        "to_agent": "backend-api",
                        "task": "Integration test task",
                        "priority": "normal"
                    }
                },
                "id": "e2e-1"
            }

            response = requests.post(
                f"{self.mcp_url}/jsonrpc",
                json=request_payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    request_id = result['result'].get('request_id')
                    logger.info(f"    ✅ Created request: {request_id}")

                    # Step 2: Convert to Inbox message
                    logger.info("  Step 2: Converting to Inbox message...")
                    inbox_payload = {
                        "task_id": request_id,
                        "from_agent": "integration-test",
                        "to_agent": "backend-api",
                        "task": "Integration test task",
                        "priority": "normal"
                    }

                    inbox_response = requests.post(
                        f"{self.inbox_url}/api/mcp/task-to-inbox",
                        json=inbox_payload,
                        headers={"Content-Type": "application/json"}
                    )

                    if inbox_response.status_code == 200:
                        inbox_data = inbox_response.json()
                        message_id = inbox_data.get('message_id')
                        logger.info(f"    ✅ Created inbox message: {message_id}")

                        # Step 3: Check message exists
                        logger.info("  Step 3: Verifying message in inbox...")
                        messages_response = requests.get(
                            f"{self.inbox_url}/api/inbox/messages"
                        )

                        if messages_response.status_code == 200:
                            messages = messages_response.json().get('messages', [])
                            found = any(m['id'] == message_id for m in messages)

                            if found:
                                self.test_results['passed'].append(test_name)
                                logger.info(f"    ✅ Complete flow successful!")
                            else:
                                self.test_results['warnings'].append(f"{test_name}: Message not found")
                                logger.warning(f"    ⚠️ Message not found in inbox")
                        else:
                            self.test_results['warnings'].append(f"{test_name}: Could not verify")
                            logger.warning(f"    ⚠️ Could not verify message")
                    else:
                        self.test_results['failed'].append(f"{test_name}: Inbox conversion failed")
                        logger.error(f"    ❌ Failed to convert to inbox message")
                else:
                    self.test_results['failed'].append(f"{test_name}: No request ID")
                    logger.error(f"    ❌ No request ID returned")
            else:
                self.test_results['failed'].append(f"{test_name}: MCP request failed")
                logger.error(f"    ❌ MCP request failed")

        except Exception as e:
            self.test_results['failed'].append(f"{test_name}: {str(e)}")
            logger.error(f"  ❌ End-to-end flow error: {e}")

    def print_test_results(self):
        """Print test results summary"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 80)

        total_tests = len(self.test_results['passed']) + len(self.test_results['failed']) + len(self.test_results['warnings'])

        logger.info(f"\n✅ PASSED: {len(self.test_results['passed'])}/{total_tests}")
        for test in self.test_results['passed']:
            logger.info(f"  • {test}")

        if self.test_results['warnings']:
            logger.info(f"\n⚠️ WARNINGS: {len(self.test_results['warnings'])}/{total_tests}")
            for warning in self.test_results['warnings']:
                logger.info(f"  • {warning}")

        if self.test_results['failed']:
            logger.info(f"\n❌ FAILED: {len(self.test_results['failed'])}/{total_tests}")
            for failure in self.test_results['failed']:
                logger.info(f"  • {failure}")

        # Overall status
        logger.info("\n" + "=" * 80)
        if not self.test_results['failed']:
            if not self.test_results['warnings']:
                logger.info("🎉 ALL TESTS PASSED! System is fully integrated.")
            else:
                logger.info("✅ TESTS PASSED WITH WARNINGS. System is functional.")
        else:
            logger.info("❌ SOME TESTS FAILED. Please check the failures above.")

        # Integration percentage
        passed_percentage = (len(self.test_results['passed']) / total_tests * 100) if total_tests > 0 else 0
        logger.info(f"\n📈 Integration Level: {passed_percentage:.1f}%")

        if passed_percentage >= 80:
            logger.info("    → System is ready for production testing")
        elif passed_percentage >= 60:
            logger.info("    → System is partially functional")
        else:
            logger.info("    → System needs more work")


async def main():
    """Main test runner"""
    tester = FullIntegrationTest()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())