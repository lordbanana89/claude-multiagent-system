#!/usr/bin/env python3
"""
Integration test for delay logic fix
Tests the actual behavior in a more realistic scenario
"""

import sys
import os
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from messaging.interface import EnhancedTerminalInterface
from shared_state.models import AgentMessage, MessagePriority


def test_real_notification_timing():
    """Test notification timing with real delay implementation"""
    print("🧪 Integration Test: Real notification timing")
    print("=" * 50)

    interface = EnhancedTerminalInterface()

    # Create test message
    test_message = AgentMessage(
        message_id="integration_test_001",
        sender_id="supervisor",
        recipient_id="backend-api",
        content="Integration test for delay fix - this message tests the timing between tmux commands",
        subject="Integration Test: Delay Fix",
        priority=MessagePriority.HIGH
    )

    print(f"📤 Sending test notification at {datetime.now().strftime('%H:%M:%S.%f')}")

    start_time = time.time()

    # Send notification (this will use the real delay logic)
    interface.send_terminal_notification("backend-api", test_message)

    end_time = time.time()
    duration = end_time - start_time

    print(f"📥 Notification sent in {duration:.3f} seconds")

    # The notification should take at least 0.1 seconds due to the delay
    if duration >= 0.1:
        print("✅ Delay timing working correctly - took appropriate time")
        return True
    else:
        print("❌ Delay timing issue - completed too quickly")
        return False


def test_multiple_rapid_notifications():
    """Test multiple rapid notifications to ensure delay works consistently"""
    print("\n🧪 Integration Test: Multiple rapid notifications")
    print("=" * 50)

    interface = EnhancedTerminalInterface()

    times = []
    for i in range(3):
        test_message = AgentMessage(
            message_id=f"rapid_test_{i:03d}",
            sender_id="test-sender",
            recipient_id="backend-api",
            content=f"Rapid test message #{i+1}",
            subject=f"Rapid Test #{i+1}",
            priority=MessagePriority.NORMAL
        )

        start = time.time()
        interface.send_terminal_notification("backend-api", test_message)
        end = time.time()

        duration = end - start
        times.append(duration)
        print(f"📤 Message {i+1} sent in {duration:.3f} seconds")

    avg_time = sum(times) / len(times)
    print(f"📊 Average time: {avg_time:.3f} seconds")

    # All notifications should take reasonable time (accounting for delay)
    if all(t >= 0.09 for t in times):  # Slight tolerance for timing variations
        print("✅ All notifications took appropriate time with delay")
        return True
    else:
        print("❌ Some notifications were too fast")
        return False


def test_delay_fix_summary():
    """Print summary of what the delay fix addresses"""
    print("\n📋 Delay Fix Summary")
    print("=" * 50)

    print("🎯 Problem addressed:")
    print("   • Race condition between tmux send-keys commands")
    print("   • Command and Enter being sent too quickly")
    print("   • Terminal not having time to process the echo command")

    print("\n🔧 Solution implemented:")
    print("   • Added time.sleep(0.1) between command and Enter")
    print("   • Allows terminal time to process the command")
    print("   • Prevents lost or malformed notifications")

    print("\n📍 Location of fix:")
    print("   • File: messaging/interface.py")
    print("   • Method: send_terminal_notification")
    print("   • Line: ~468 (time.sleep(0.1))")

    print("\n✅ Benefits:")
    print("   • Reliable message delivery to agent terminals")
    print("   • Consistent notification formatting")
    print("   • Better agent communication experience")


def main():
    """Run all integration tests"""
    print("🚀 Integration Tests for Delay Logic Fix")
    print("=" * 60)

    results = []

    # Test 1: Real notification timing
    results.append(test_real_notification_timing())

    # Test 2: Multiple rapid notifications
    results.append(test_multiple_rapid_notifications())

    # Summary
    test_delay_fix_summary()

    # Final result
    print("\n🏁 Integration Test Results")
    print("=" * 60)

    if all(results):
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ Delay logic fix is working correctly")
        return True
    else:
        print("❌ Some integration tests failed")
        print("🔧 Delay logic fix needs attention")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)