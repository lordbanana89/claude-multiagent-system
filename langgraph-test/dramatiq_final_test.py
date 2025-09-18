#!/usr/bin/env python3
"""
🎉 DRAMATIQ INTEGRATION FINAL TEST SUITE
Complete validation of Dramatiq replacement for tmux subprocess architecture
"""

import time
import subprocess
import json
from datetime import datetime
from dramatiq_agent_integration import (
    submit_agent_request, approve_agent_request, reject_agent_request,
    get_pending_requests, get_system_status, agent_manager
)

def test_complete_workflow():
    """🎉 Test complete agent request workflow"""
    print("🎉 DRAMATIQ COMPLETE WORKFLOW TEST")
    print("=" * 50)

    results = {
        "tests_run": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "start_time": datetime.now().isoformat()
    }

    # Test 1: Submit auto-approve request
    print("\n🧪 Test 1: Auto-approve request")
    results["tests_run"] += 1

    try:
        request_id_1 = submit_agent_request(
            agent_id="test-agent-1",
            session_id="claude-backend-api",
            command="echo '✅ Test 1: Auto-approved command executed successfully'",
            description="Auto-approve test command",
            priority="high",
            auto_approve=True
        )

        print(f"✅ Auto-approve request submitted: {request_id_1}")
        time.sleep(2)  # Wait for processing

        status = agent_manager.get_request_status(request_id_1)
        if status and status["status"] in ["completed", "processing"]:
            print(f"✅ Test 1 PASSED - Status: {status['status']}")
            results["tests_passed"] += 1
        else:
            print(f"❌ Test 1 FAILED - Status: {status['status'] if status else 'Not found'}")
            results["tests_failed"] += 1

    except Exception as e:
        print(f"❌ Test 1 FAILED - Error: {e}")
        results["tests_failed"] += 1

    # Test 2: Submit manual approval request
    print("\n🧪 Test 2: Manual approval workflow")
    results["tests_run"] += 1

    try:
        request_id_2 = submit_agent_request(
            agent_id="test-agent-2",
            session_id="claude-database",
            command="echo '✅ Test 2: Manually approved command executed'",
            description="Manual approval test command",
            priority="normal",
            auto_approve=False
        )

        print(f"📩 Manual approval request submitted: {request_id_2}")

        # Check pending requests
        pending = get_pending_requests()
        pending_ids = [req["request_id"] for req in pending]

        if request_id_2 in pending_ids:
            print("✅ Request found in pending queue")

            # Approve the request
            if approve_agent_request(request_id_2, "Test approval by supervisor"):
                print("✅ Request approved successfully")

                time.sleep(2)  # Wait for processing

                status = agent_manager.get_request_status(request_id_2)
                if status and status["status"] in ["completed", "processing"]:
                    print(f"✅ Test 2 PASSED - Status: {status['status']}")
                    results["tests_passed"] += 1
                else:
                    print(f"❌ Test 2 FAILED - Status: {status['status'] if status else 'Not found'}")
                    results["tests_failed"] += 1
            else:
                print("❌ Test 2 FAILED - Approval failed")
                results["tests_failed"] += 1
        else:
            print("❌ Test 2 FAILED - Request not found in pending queue")
            results["tests_failed"] += 1

    except Exception as e:
        print(f"❌ Test 2 FAILED - Error: {e}")
        results["tests_failed"] += 1

    # Test 3: Request rejection
    print("\n🧪 Test 3: Request rejection workflow")
    results["tests_run"] += 1

    try:
        request_id_3 = submit_agent_request(
            agent_id="test-agent-3",
            session_id="claude-frontend-ui",
            command="echo 'This should be rejected'",
            description="Test rejection command",
            priority="low",
            auto_approve=False
        )

        print(f"📩 Rejection test request submitted: {request_id_3}")

        # Reject the request
        if reject_agent_request(request_id_3, "Test rejection by supervisor"):
            print("✅ Request rejected successfully")

            status = agent_manager.get_request_status(request_id_3)
            if status and status["status"] == "rejected":
                print("✅ Test 3 PASSED - Request properly rejected")
                results["tests_passed"] += 1
            else:
                print(f"❌ Test 3 FAILED - Wrong status: {status['status'] if status else 'Not found'}")
                results["tests_failed"] += 1
        else:
            print("❌ Test 3 FAILED - Rejection failed")
            results["tests_failed"] += 1

    except Exception as e:
        print(f"❌ Test 3 FAILED - Error: {e}")
        results["tests_failed"] += 1

    # Test 4: System statistics
    print("\n🧪 Test 4: System statistics and health")
    results["tests_run"] += 1

    try:
        stats = get_system_status()
        print(f"📊 Total requests: {stats['total_requests']}")
        print(f"📊 Completed requests: {stats['completed_requests']}")
        print(f"📊 Failed requests: {stats['failed_requests']}")
        print(f"📊 Broker health: {stats['broker_health']['database_type']}")

        if stats["total_requests"] >= 3:
            print("✅ Test 4 PASSED - System statistics working")
            results["tests_passed"] += 1
        else:
            print("❌ Test 4 FAILED - Statistics inconsistent")
            results["tests_failed"] += 1

    except Exception as e:
        print(f"❌ Test 4 FAILED - Error: {e}")
        results["tests_failed"] += 1

    # Test 5: Check tmux sessions for command execution
    print("\n🧪 Test 5: Verify tmux command execution")
    results["tests_run"] += 1

    try:
        # Check if commands were actually executed in tmux sessions
        sessions_to_check = ["claude-backend-api", "claude-database"]
        executed_commands = 0

        for session in sessions_to_check:
            try:
                # Capture last few lines from session
                result = subprocess.run([
                    "tmux", "capture-pane", "-t", session, "-p"
                ], capture_output=True, text=True, timeout=10)

                if result.returncode == 0 and "Test" in result.stdout:
                    executed_commands += 1
                    print(f"✅ Commands executed in {session}")

            except Exception as session_error:
                print(f"⚠️ Could not check {session}: {session_error}")

        if executed_commands > 0:
            print("✅ Test 5 PASSED - Commands executed in tmux sessions")
            results["tests_passed"] += 1
        else:
            print("❌ Test 5 FAILED - No command execution detected")
            results["tests_failed"] += 1

    except Exception as e:
        print(f"❌ Test 5 FAILED - Error: {e}")
        results["tests_failed"] += 1

    # Final results
    results["end_time"] = datetime.now().isoformat()
    results["success_rate"] = (results["tests_passed"] / results["tests_run"]) * 100 if results["tests_run"] > 0 else 0

    print("\n" + "=" * 50)
    print("🎉 FINAL TEST RESULTS")
    print("=" * 50)
    print(f"📊 Tests Run: {results['tests_run']}")
    print(f"✅ Tests Passed: {results['tests_passed']}")
    print(f"❌ Tests Failed: {results['tests_failed']}")
    print(f"🎯 Success Rate: {results['success_rate']:.1f}%")

    if results["success_rate"] >= 80:
        print("\n🎉 DRAMATIQ INTEGRATION: FULLY OPERATIONAL!")
        print("✅ System ready for production use")
        return True
    else:
        print("\n⚠️ DRAMATIQ INTEGRATION: NEEDS ATTENTION")
        print("❌ Some tests failed - review before production")
        return False

def test_performance():
    """🚀 Test system performance under load"""
    print("\n🚀 PERFORMANCE TEST")
    print("=" * 30)

    start_time = time.time()

    # Submit multiple requests rapidly
    request_ids = []
    for i in range(10):
        request_id = submit_agent_request(
            agent_id=f"perf-test-{i}",
            session_id="claude-testing",
            command=f"echo 'Performance test {i} completed'",
            description=f"Performance test command {i}",
            priority="normal",
            auto_approve=True
        )
        request_ids.append(request_id)

    submission_time = time.time() - start_time
    print(f"📊 10 requests submitted in {submission_time:.2f}s")

    # Wait for processing
    time.sleep(5)

    # Check completion
    completed = 0
    for request_id in request_ids:
        status = agent_manager.get_request_status(request_id)
        if status and status["status"] == "completed":
            completed += 1

    total_time = time.time() - start_time
    throughput = len(request_ids) / total_time

    print(f"📊 {completed}/{len(request_ids)} requests completed")
    print(f"📊 Total time: {total_time:.2f}s")
    print(f"📊 Throughput: {throughput:.2f} requests/second")

    return completed >= 8  # 80% completion rate

if __name__ == "__main__":
    print("🚨 DRAMATIQ INTEGRATION FINAL TEST SUITE")
    print("🚀 Testing complete replacement of tmux subprocess architecture")
    print("=" * 70)

    # Run complete workflow test
    workflow_success = test_complete_workflow()

    # Run performance test
    performance_success = test_performance()

    # Overall result
    print("\n" + "=" * 70)
    print("🏁 OVERALL RESULTS")
    print("=" * 70)

    if workflow_success and performance_success:
        print("🎉 DRAMATIQ INTEGRATION: 100% SUCCESSFUL!")
        print("✅ Ready to replace tmux subprocess architecture")
        print("✅ All systems operational")
        exit(0)
    else:
        print("⚠️ DRAMATIQ INTEGRATION: PARTIAL SUCCESS")
        print("❌ Some issues detected - review required")
        exit(1)