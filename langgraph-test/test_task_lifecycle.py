#!/usr/bin/env python3
"""
🧪 Test Task Lifecycle - Complete System Test
Tests the complete task lifecycle from creation to completion
"""

import sys
import os
import time
import subprocess
from datetime import datetime, timedelta

# Add shared_state to path
sys.path.append('/Users/erik/Desktop/claude-multiagent-system/langgraph-test')

from shared_state.manager import SharedStateManager
from shared_state.models import TaskPriority
from task_completion_monitor import TaskCompletionMonitor

def test_complete_lifecycle():
    """Test complete task lifecycle"""

    print("🧪 Starting Complete Task Lifecycle Test")
    print("=" * 60)

    # 1. Initialize system
    print("1️⃣ Initializing SharedStateManager...")
    manager = SharedStateManager(
        persistence_type="json",
        persistence_file="/Users/erik/Desktop/claude-multiagent-system/langgraph-test/shared_state.json"
    )

    # 2. Check initial state
    print("2️⃣ Checking initial state...")
    initial_state = manager.get_system_stats()
    print(f"   System Status: {initial_state['system_status']}")
    print(f"   Active Agents: {initial_state['active_agents']}")
    print(f"   Total Agents: {initial_state['total_agents']}")

    if initial_state['system_status'] != 'idle':
        print("❌ System not idle - running emergency reset first...")
        subprocess.run([
            "python3",
            "/Users/erik/Desktop/claude-multiagent-system/langgraph-test/reset_stuck_agents.py"
        ])
        time.sleep(2)

    # 3. Create test task
    print("3️⃣ Creating test task...")
    task = manager.create_task(
        description="Test task lifecycle - respond with 'task complete' when done",
        priority=TaskPriority.HIGH
    )
    manager.add_task(task)
    print(f"   Task ID: {task.task_id}")
    print(f"   Description: {task.description}")

    # 4. Assign to one agent for testing
    print("4️⃣ Assigning task to backend-api agent...")
    success = manager.assign_task(task.task_id, ["backend-api"])
    if success:
        print("   ✅ Task assigned successfully")
    else:
        print("   ❌ Failed to assign task")
        return False

    # 5. Start completion monitor
    print("5️⃣ Starting task completion monitor...")
    monitor = TaskCompletionMonitor()
    monitor.start_monitoring()
    print("   🤖 Monitor started - watching for completion signals")

    # 6. Send task to agent terminal
    print("6️⃣ Sending task to agent terminal...")
    try:
        # Send task to tmux session
        subprocess.run([
            "tmux", "send-keys", "-t", "claude-backend-api",
            f"Task: {task.description}"
        ], check=True)

        # Wait for command to be processed, then send Enter
        time.sleep(0.1)  # Short delay to let command be processed
        subprocess.run([
            "tmux", "send-keys", "-t", "claude-backend-api",
            "Enter"
        ], check=True)
        print("   ✅ Task sent to terminal")

        # Send reminder about completion
        time.sleep(1)
        subprocess.run([
            "tmux", "send-keys", "-t", "claude-backend-api",
            "Please respond with 'task complete' when you're done"
        ], check=True)

        # Wait for command to be processed, then send Enter
        time.sleep(0.1)  # Short delay to let command be processed
        subprocess.run([
            "tmux", "send-keys", "-t", "claude-backend-api",
            "Enter"
        ], check=True)

    except Exception as e:
        print(f"   ❌ Error sending to terminal: {e}")

    # 7. Monitor task progress with intervention detection
    print("7️⃣ Monitoring task progress...")
    print("   Waiting for completion with intervention detection...")

    start_time = datetime.now()
    completed = False
    timeout_minutes = 5
    last_intervention_check = datetime.now()
    intervention_detected = False

    def check_for_intervention_requests():
        """Check terminal output for intervention signals"""
        try:
            # Capture terminal output to look for intervention signals
            capture_result = subprocess.run([
                "tmux", "capture-pane", "-t", "claude-backend-api", "-p"
            ], capture_output=True, text=True)

            if capture_result.returncode == 0:
                terminal_output = capture_result.stdout.lower()
                # Look for common intervention request patterns
                intervention_signals = [
                    "need help", "assistance required", "intervention needed",
                    "require clarification", "need more information", "please help",
                    "can you help", "need guidance", "stuck", "blocking issue",
                    "waiting for", "need approval", "manual intervention"
                ]
                return any(signal in terminal_output for signal in intervention_signals)
        except Exception as e:
            print(f"   ⚠️ Could not check intervention: {e}")
        return False

    def extend_timeout_for_intervention():
        """Extend timeout when intervention is detected"""
        print("   🔔 INTERVENTION DETECTED - Extending timeout by 5 minutes...")
        return datetime.now() + timedelta(minutes=5)

    # Initial timeout
    timeout_deadline = start_time + timedelta(minutes=timeout_minutes)

    while datetime.now() < timeout_deadline:
        # Reload state
        manager.state = manager.persistence_manager.load()
        current_task = manager.state.current_task

        if not current_task:
            print("   ✅ Task completed and moved to history!")
            completed = True
            break

        if current_task.task_id != task.task_id:
            print("   ✅ Task completed (different current task)!")
            completed = True
            break

        # Check if task has results
        if current_task.results and "backend-api" in current_task.results:
            result_content = current_task.results["backend-api"]
            print(f"   ✅ Agent completed: {result_content}")
            # Check if result indicates task completion
            completion_indicators = ["task complete", "completed", "done", "finished"]
            if any(indicator in result_content.lower() for indicator in completion_indicators):
                completed = True
                break

        # Check for intervention requests every 30 seconds
        if (datetime.now() - last_intervention_check).total_seconds() >= 30:
            if check_for_intervention_requests():
                if not intervention_detected:
                    intervention_detected = True
                    timeout_deadline = extend_timeout_for_intervention()
                else:
                    # Already detected, extend again if still requesting intervention
                    timeout_deadline = extend_timeout_for_intervention()
            last_intervention_check = datetime.now()

        elapsed = datetime.now() - start_time
        remaining = timeout_deadline - datetime.now()
        print(f"   ⏳ Still waiting... Progress: {current_task.progress}% | Elapsed: {elapsed.total_seconds():.0f}s | Remaining: {remaining.total_seconds():.0f}s")

        if intervention_detected:
            print(f"   🤖 Intervention mode active - monitoring for completion...")

        time.sleep(10)

    # 8. Check final results
    print("8️⃣ Checking final results...")
    final_state = manager.get_system_stats()
    task_history = manager.get_task_history(10)

    if completed:
        print("   🎉 LIFECYCLE TEST PASSED!")
        print(f"   Final system status: {final_state['system_status']}")

        # Find our test task in history
        test_task_in_history = None
        for hist_task in task_history:
            if hist_task.task_id == task.task_id:
                test_task_in_history = hist_task
                break

        if test_task_in_history:
            print(f"   Task status: {test_task_in_history.status}")
            print(f"   Task progress: {test_task_in_history.progress}%")
            print(f"   Results: {test_task_in_history.results}")
        else:
            print("   ⚠️ Task not found in history")

    else:
        print("   ❌ LIFECYCLE TEST FAILED - Task did not complete in time")
        print(f"   Final system status: {final_state['system_status']}")

        # Show current task status
        current_task = manager.state.current_task
        if current_task:
            print(f"   Current task: {current_task.task_id}")
            print(f"   Status: {current_task.status}")
            print(f"   Progress: {current_task.progress}%")

    # 9. Stop monitor
    print("9️⃣ Stopping monitor...")
    monitor.stop_monitoring()

    print("\n📊 Test Summary:")
    print(f"   Status: {'PASSED' if completed else 'FAILED'}")
    print(f"   Duration: {datetime.now() - start_time}")
    print(f"   System Status: {final_state['system_status']}")
    print(f"   Completed Tasks: {final_state['completed_tasks']}")

    return completed

if __name__ == "__main__":
    print("🧪 Claude Multi-Agent System - Task Lifecycle Test")
    print("This test will verify the complete task lifecycle")
    print()

    try:
        success = test_complete_lifecycle()
        if success:
            print("\n🎉 ALL TESTS PASSED! System is working correctly.")
            sys.exit(0)
        else:
            print("\n❌ TESTS FAILED! Check system configuration.")
            sys.exit(1)

    except Exception as e:
        print(f"💥 Critical test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)