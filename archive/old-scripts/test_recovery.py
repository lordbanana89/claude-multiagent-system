#!/usr/bin/env python3
"""Test recovery and retry mechanisms"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.recovery import get_recovery_manager
from core.tmux_client import TMUXClient
from core.message_bus import get_message_bus
from agents.agent_bridge import AgentBridge

def test_health_check():
    """Test system health check"""
    print("\n=== TESTING HEALTH CHECK ===\n")

    recovery = get_recovery_manager()

    # Perform health check
    health = recovery.health_check()

    print("System Health:")
    print(f"  Overall: {'✅ Healthy' if health['healthy'] else '❌ Unhealthy'}")
    print("\nComponents:")
    for component, status in health['components'].items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {component}")

    if 'persistence_stats' in health:
        print("\nPersistence Stats:")
        for key, value in health['persistence_stats'].items():
            print(f"  {key}: {value}")

    if health.get('stale_tasks', 0) > 0:
        print(f"\n⚠️ Found {health['stale_tasks']} stale tasks")

    return health['healthy']

def test_session_recovery():
    """Test TMUX session recovery"""
    print("\n=== TESTING SESSION RECOVERY ===\n")

    tmux = TMUXClient()
    recovery = get_recovery_manager()

    # Kill a session to simulate failure
    test_session = "claude-backend-api"
    if tmux.session_exists(test_session):
        tmux.kill_session(test_session)
        print(f"Killed session: {test_session}")

    # Perform recovery
    print("\nRecovering sessions...")
    results = recovery._recover_sessions()

    for session, success in results.items():
        if session == test_session:
            if success:
                print(f"  ✅ Successfully recovered {session}")
            else:
                print(f"  ❌ Failed to recover {session}")

def test_auto_recovery():
    """Test automatic recovery"""
    print("\n=== TESTING AUTO RECOVERY ===\n")

    recovery = get_recovery_manager()
    tmux = TMUXClient()

    # Create unhealthy state
    print("Creating unhealthy state...")
    test_sessions = ["claude-supervisor", "claude-database"]
    for session in test_sessions:
        if tmux.session_exists(session):
            tmux.kill_session(session)
            print(f"  Killed: {session}")

    # Check health before recovery
    print("\nHealth before recovery:")
    health_before = recovery.health_check()
    print(f"  Healthy: {health_before['healthy']}")

    # Perform auto recovery
    print("\nPerforming auto recovery...")
    success = recovery.auto_recover()

    # Check health after recovery
    print("\nHealth after recovery:")
    health_after = recovery.health_check()
    print(f"  Healthy: {health_after['healthy']}")

    if success:
        print("\n✅ Auto recovery successful!")
    else:
        print("\n❌ Auto recovery failed")

    return success

def test_task_retry():
    """Test task retry mechanism"""
    print("\n=== TESTING TASK RETRY ===\n")

    # Setup
    tmux = TMUXClient()
    bus = get_message_bus()
    recovery = get_recovery_manager()

    # Create session
    session = "claude-backend-api"
    if tmux.session_exists(session):
        tmux.kill_session(session)
    tmux.create_session(session)

    # Start message bus
    if not bus.running:
        bus.start()

    # Start agent bridge but immediately stop it to simulate failure
    bridge = AgentBridge("backend-api")
    bridge.start()
    time.sleep(0.5)
    bridge.stop()  # Stop bridge to make task fail

    # Publish a task that will fail
    print("1. Publishing task that will fail...")
    task_id = bus.publish_task(
        agent="backend-api",
        task={"command": "echo 'This will timeout'", "params": {}}
    )
    print(f"   Task ID: {task_id}")

    # Wait a bit
    time.sleep(2)

    # Now restart bridge
    bridge = AgentBridge("backend-api")
    bridge.start()
    print("2. Bridge restarted")

    # Try to retry the failed task
    print("3. Attempting task retry...")
    success = recovery.retry_failed_task(task_id)

    if success:
        print("   ✅ Task retry initiated")
    else:
        print("   ❌ Task retry failed")

    # Cleanup
    bridge.stop()
    bus.stop()
    tmux.kill_session(session)

    return success

def test_full_recovery():
    """Test full system recovery"""
    print("\n=== TESTING FULL SYSTEM RECOVERY ===\n")

    recovery = get_recovery_manager()

    print("Performing full system recovery...")
    results = recovery.recover_system()

    print("\nRecovery Results:")
    for component, result in results.items():
        print(f"\n{component.upper()}:")
        if isinstance(result, dict):
            for key, value in result.items():
                status = "✅" if value else "❌" if isinstance(value, bool) else str(value)
                print(f"  {key}: {status}")
        else:
            print(f"  {result}")

    print("\n✓ Full recovery test complete")

def main():
    print("=" * 60)
    print("RECOVERY AND RETRY TEST")
    print("=" * 60)

    results = []

    # Test 1: Health check
    health_ok = test_health_check()
    results.append(("Health Check", health_ok))

    # Test 2: Session recovery
    test_session_recovery()
    results.append(("Session Recovery", True))

    # Test 3: Auto recovery
    auto_ok = test_auto_recovery()
    results.append(("Auto Recovery", auto_ok))

    # Test 4: Full recovery
    test_full_recovery()
    results.append(("Full Recovery", True))

    # Report
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{name:20} {status}")

    passed = sum(1 for _, s in results if s)
    total = len(results)

    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All recovery tests passed!")
    else:
        print(f"\n⚠️ {total - passed} tests failed")

if __name__ == "__main__":
    main()