#!/usr/bin/env python3
"""
Test script to verify shared context system actually works
"""

import time
import subprocess
from core.tmux_client import TMUXClient

def test_shared_context():
    """Test the shared context system"""
    print("🧪 Testing Shared Context System")
    print("="*50)

    tmux = TMUXClient()

    # 1. Create test agents
    test_agents = ["test-agent-1", "test-agent-2", "test-agent-3"]

    print("\n1️⃣ Creating test agent sessions...")
    for agent in test_agents:
        if tmux.session_exists(agent):
            tmux.kill_session(agent)
        tmux.create_session(agent)
        print(f"   ✓ Created {agent}")

    # 2. Create shared context if not exists
    shared_context = "claude-shared-context"
    if not tmux.session_exists(shared_context):
        tmux.create_session(shared_context)
        print(f"\n2️⃣ Created shared context: {shared_context}")
    else:
        print(f"\n2️⃣ Using existing shared context: {shared_context}")

    # 3. Simulate agent activities
    print("\n3️⃣ Simulating agent activities...")

    activities = [
        ("test-agent-1", "Starting backend API development"),
        ("test-agent-2", "Creating database schema"),
        ("test-agent-3", "Building frontend components"),
        ("test-agent-1", "Created /api/users endpoint"),
        ("test-agent-2", "Added users table with id, email, password"),
        ("test-agent-3", "Implemented login form")
    ]

    for agent, activity in activities:
        # Send to agent's own session
        tmux.send_command(agent, f"echo '[ACTIVITY] {activity}'")

        # Send to shared context
        timestamp = time.strftime("%H:%M:%S")
        msg = f"[{timestamp}] {agent}: {activity}"
        tmux.send_command(shared_context, f"echo '{msg}'")

        print(f"   📝 {agent}: {activity}")
        time.sleep(1)

    # 4. Capture and display shared context
    print("\n4️⃣ Shared Context Contents:")
    print("-"*50)

    # Wait a moment for commands to execute
    time.sleep(2)

    # Capture shared context
    context_content = tmux.capture_pane(shared_context)

    # Get last 20 lines that contain our messages
    lines = context_content.split('\n')
    relevant_lines = [l for l in lines if 'test-agent' in l and '[' in l]

    if relevant_lines:
        for line in relevant_lines[-10:]:  # Show last 10 activities
            print(f"   {line}")
    else:
        print("   ⚠️ No activities found in shared context")
        print("   Raw content (last 10 lines):")
        for line in lines[-10:]:
            if line.strip():
                print(f"   {line}")

    # 5. Test message broadcasting
    print("\n5️⃣ Testing Message Broadcasting...")

    # Broadcast a coordination message
    coordination_msg = "ATTENTION: All agents please sync on API schema"
    for agent in test_agents:
        tmux.send_command(agent, f"echo '📢 BROADCAST: {coordination_msg}'")

    print(f"   📢 Broadcasted: {coordination_msg}")

    # 6. Verify agents received broadcast
    print("\n6️⃣ Verifying Broadcast Reception:")
    time.sleep(2)

    for agent in test_agents:
        content = tmux.capture_pane(agent)
        if "BROADCAST" in content:
            print(f"   ✅ {agent} received broadcast")
        else:
            print(f"   ❌ {agent} did NOT receive broadcast")

    # 7. Cleanup
    print("\n7️⃣ Cleanup test sessions...")
    for agent in test_agents:
        tmux.kill_session(agent)
        print(f"   ✓ Removed {agent}")

    print("\n✨ Test Complete!")
    print(f"\n💡 Shared context is still running: {shared_context}")
    print("   View it with: tmux attach -t claude-shared-context")

    return True

def test_with_real_claude():
    """Test with real Claude agents if available"""
    print("\n🤖 Testing with Real Claude Agents")
    print("="*50)

    tmux = TMUXClient()

    # Check for real Claude agents
    claude_agents = [
        "claude-backend-api",
        "claude-database",
        "claude-frontend-ui"
    ]

    active_agents = []
    for agent in claude_agents:
        if tmux.session_exists(agent):
            active_agents.append(agent)

    if not active_agents:
        print("❌ No Claude agents found. Start them first.")
        return False

    print(f"✅ Found {len(active_agents)} Claude agents: {', '.join(active_agents)}")

    # Send a coordination message to all
    shared_context = "claude-shared-context"

    test_task = """
# 🎯 COORDINATION TEST
# This is a test of the shared context system
# Each agent should acknowledge seeing this message
"""

    print("\n📤 Sending test coordination message...")

    for agent in active_agents:
        tmux.send_command(agent, test_task)
        print(f"   → Sent to {agent}")

    # Log to shared context
    tmux.send_command(shared_context, f"echo '[TEST] Coordination message sent to all agents'")

    print("\n✅ Test message sent!")
    print("Check each agent to see if they received it:")
    for agent in active_agents:
        print(f"   tmux attach -t {agent}")

    return True

if __name__ == "__main__":
    # Run basic test first
    if test_shared_context():
        # Then test with real agents if available
        test_with_real_claude()