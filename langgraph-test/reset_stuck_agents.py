#!/usr/bin/env python3
"""
🔄 Reset Stuck Agents - Emergency Recovery Tool
Manually reset all agents stuck in BUSY state and complete stuck tasks
"""

import sys
import os

# Add shared_state to path
sys.path.append('/Users/erik/Desktop/claude-multiagent-system/langgraph-test')

from shared_state.manager import SharedStateManager
from datetime import datetime

def reset_stuck_system():
    """Reset all stuck agents and complete stuck tasks"""

    print("🔄 Starting Emergency System Reset...")
    print("=" * 50)

    # Initialize SharedStateManager
    manager = SharedStateManager(
        persistence_type="json",
        persistence_file="/Users/erik/Desktop/claude-multiagent-system/langgraph-test/shared_state.json"
    )

    # Check current state
    current_task = manager.state.current_task
    if current_task:
        print(f"📋 Current Task: {current_task.task_id}")
        print(f"   Description: {current_task.description}")
        print(f"   Status: {current_task.status}")
        print(f"   Started: {current_task.started_at}")
        print(f"   Progress: {current_task.progress}%")
        print(f"   Assigned Agents: {current_task.assigned_agents}")

        # Complete the stuck task
        print("\n✅ Completing stuck task...")
        results = {}
        for agent_id in current_task.assigned_agents:
            results[agent_id] = "Task completed via emergency reset - agents were stuck in BUSY state"

        success = manager.complete_task(
            task_id=current_task.task_id,
            results=results
        )

        if success:
            print(f"✅ Task {current_task.task_id} completed successfully")
        else:
            print(f"❌ Failed to complete task {current_task.task_id}")
    else:
        print("📋 No current task found")

    # Reset all agents to IDLE
    print("\n🔄 Resetting all agents to IDLE...")
    agent_count = 0
    for agent_id, agent in manager.state.agents.items():
        if agent.status == "busy":
            print(f"   Resetting {agent_id}: {agent.status} → idle")
            manager.update_agent_status(agent_id, "idle")
            manager.state.agents[agent_id].current_task = None
            manager.state.agents[agent_id].error_message = None
            manager.state.agents[agent_id].last_activity = datetime.now().isoformat()
            agent_count += 1
        else:
            print(f"   {agent_id}: {agent.status} (no change needed)")

    # Set system status to idle
    manager.state.system_status = "idle"
    manager.state.last_updated = datetime.now().isoformat()

    # Save state
    try:
        manager.persistence_manager.save(manager.state)
        print(f"\n💾 State saved successfully")
        print(f"✅ Reset complete! {agent_count} agents reset to IDLE")
        print(f"🎯 System is now ready for new tasks")

        # Show final state
        print("\n📊 Final System Status:")
        print(f"   System Status: {manager.state.system_status}")
        print(f"   Current Task: {manager.state.current_task}")
        print(f"   Active Agents: {len([a for a in manager.state.agents.values() if a.status == 'idle'])}")

    except Exception as e:
        print(f"❌ Error saving state: {e}")
        return False

    return True

if __name__ == "__main__":
    print("🚨 Emergency Agent Reset Tool")
    print("This will reset all stuck agents to IDLE state")

    try:
        success = reset_stuck_system()
        if success:
            print("\n🎉 Emergency reset completed successfully!")
            print("💡 Agents are now ready to accept new tasks")
        else:
            print("\n❌ Emergency reset failed")
            sys.exit(1)

    except Exception as e:
        print(f"💥 Critical error during reset: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)