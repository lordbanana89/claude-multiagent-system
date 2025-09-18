#!/usr/bin/env python3
"""
Debug script to understand why tasks don't complete
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.tmux_client import TMUXClient
import logging

logging.basicConfig(level=logging.DEBUG)

def test_simple_command():
    """Test the simplest possible command execution"""
    print("\n=== TESTING SIMPLE COMMAND EXECUTION ===\n")

    tmux = TMUXClient()
    session = "test-session"

    # Clean start
    if tmux.session_exists(session):
        tmux.kill_session(session)
    tmux.create_session(session)
    print(f"✓ Created session: {session}")

    # Test 1: Direct echo
    print("\nTest 1: Simple echo")
    tmux.send_command(session, "echo 'TEST OUTPUT'")
    time.sleep(1)
    output = tmux.capture_pane(session)
    print(f"Output captured ({len(output)} chars):")
    print("-" * 40)
    print(output[-200:] if len(output) > 200 else output)
    print("-" * 40)

    if "TEST OUTPUT" in output:
        print("✅ Command executed successfully!")
    else:
        print("❌ Command not found in output")

    # Test 2: With markers
    print("\nTest 2: With task markers")
    tmux.send_command(session, "echo '# TASK_START:123'")
    time.sleep(0.5)
    tmux.send_command(session, "echo 'TASK CONTENT'")
    time.sleep(0.5)
    tmux.send_command(session, "echo '# TASK_END:123'")
    time.sleep(1)

    output = tmux.capture_pane(session)
    print(f"Output captured ({len(output)} chars):")
    print("-" * 40)
    print(output[-300:] if len(output) > 300 else output)
    print("-" * 40)

    if "TASK_START:123" in output and "TASK_END:123" in output:
        print("✅ Markers found in output!")
    else:
        print("❌ Markers not found")
        if "TASK_START:123" in output:
            print("  - START found")
        if "TASK_END:123" in output:
            print("  - END found")

    # Test 3: Multi-line command
    print("\nTest 3: Multi-line command")
    command = """echo '# TASK_START:456'
echo 'Line 1'
echo 'Line 2'
echo '# TASK_END:456'"""

    for line in command.split('\n'):
        tmux.send_command(session, line)
        time.sleep(0.2)

    time.sleep(1)
    output = tmux.capture_pane(session)

    print(f"Output captured ({len(output)} chars)")

    # Check what we actually got
    lines = output.split('\n')
    relevant_lines = [l for l in lines if 'TASK' in l or 'Line' in l]
    print("Relevant lines found:")
    for line in relevant_lines:
        print(f"  {line}")

    # Cleanup
    tmux.kill_session(session)
    print("\n✓ Session cleaned up")

def test_completion_detection():
    """Test how we detect task completion"""
    print("\n=== TESTING COMPLETION DETECTION ===\n")

    from agents.agent_bridge import AgentTask, AgentBridge

    # Create test task
    task = AgentTask(
        id="test-task-999",
        agent="backend-api",
        command="echo 'Test completion'",
        params={},
        timeout=5
    )

    # Mock output scenarios
    scenarios = [
        ("With END marker", "some output\n# TASK_END:test-task-999\nmore output"),
        ("Without END marker", "some output\nTest completion\nmore output"),
        ("With Done", "some output\nDone.\nmore output"),
        ("With Completed", "some output\nCompleted.\nmore output"),
        ("With error", "some output\nError: something failed\nmore output"),
    ]

    for name, test_output in scenarios:
        print(f"\nScenario: {name}")
        print(f"Output: {test_output[:50]}...")

        # Check completion patterns
        task_end = f"# TASK_END:{task.id}" in test_output
        done = "Done." in test_output
        completed = "Completed." in test_output
        error = "Error:" in test_output

        print(f"  Task END marker: {task_end}")
        print(f"  Done found: {done}")
        print(f"  Completed found: {completed}")
        print(f"  Error found: {error}")

        if task_end or done or completed:
            print("  → Would be detected as COMPLETE ✅")
        elif error:
            print("  → Would be detected as ERROR ⚠️")
        else:
            print("  → Would NOT be detected ❌")

def test_with_agent_bridge():
    """Test with real agent bridge"""
    print("\n=== TESTING WITH AGENT BRIDGE ===\n")

    from core.message_bus import get_message_bus
    from agents.agent_bridge import AgentBridge, AgentTask
    from core.tmux_client import TMUXClient

    # Setup
    tmux = TMUXClient()
    session = "claude-backend-api"

    if tmux.session_exists(session):
        tmux.kill_session(session)
    tmux.create_session(session)
    print(f"✓ Created session: {session}")

    # Start message bus
    bus = get_message_bus()
    if not bus.running:
        bus.start()
    print("✓ Message bus started")

    # Create bridge but don't start it (we'll call methods directly)
    bridge = AgentBridge("backend-api")
    print("✓ Agent bridge created")

    # Create simple task
    task = AgentTask(
        id="direct-test-001",
        agent="backend-api",
        command="echo 'Direct test execution'",
        params={},
        timeout=5
    )

    print(f"\nExecuting task: {task.id}")
    print(f"Command: {task.command}")

    # Prepare command (add markers)
    prepared = bridge._prepare_command(task.command, task.params)
    print(f"\nPrepared command:")
    print("-" * 40)
    print(prepared)
    print("-" * 40)

    # Send to TMUX
    tmux.send_command(session, prepared)
    time.sleep(2)

    # Check output
    output = tmux.capture_pane(session)
    print(f"\nTMUX output ({len(output)} chars):")
    print("-" * 40)
    print(output[-500:] if len(output) > 500 else output)
    print("-" * 40)

    # Parse output
    result = bridge._parse_output(output)
    print(f"\nParsed result:")
    print(f"  Success: {result.get('success', False)}")
    print(f"  Lines: {len(result.get('lines', []))}")
    if result.get('raw_output'):
        print(f"  Raw output: {result['raw_output'][:100]}...")

    # Check for completion
    if f"# TASK_END:{task.id}" in output:
        print("\n✅ Task END marker found!")
    else:
        print("\n❌ Task END marker NOT found")
        print("This is why tasks timeout!")

    # Cleanup
    bus.stop()
    tmux.kill_session(session)
    print("\n✓ Cleanup complete")

def main():
    print("=" * 60)
    print("DEBUGGING TASK EXECUTION")
    print("=" * 60)

    test_simple_command()
    test_completion_detection()
    test_with_agent_bridge()

    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()