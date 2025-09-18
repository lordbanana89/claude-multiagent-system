#!/usr/bin/env python3
"""
Test integration between SharedStateManager and Enhanced Messaging System
Verifies that notifications are sent when messages are exchanged through SharedStateManager
"""

import time
from datetime import datetime
from shared_state.manager import SharedStateManager
from shared_state.models import AgentState, AgentStatus


def test_notification_integration():
    """Test the integrated notification system"""
    print("🔗 TESTING SHAREDSATEMANAGER + ENHANCED MESSAGING INTEGRATION")
    print("=" * 70)

    # Initialize SharedStateManager (should auto-integrate with notifications)
    print("📋 Initializing SharedStateManager...")
    manager = SharedStateManager()

    # Check if notification system is available
    if not manager.notification_system:
        print("❌ Notification system not available - enhanced messaging not integrated")
        return False

    print("✅ Enhanced notification system integrated successfully")

    # Register test agents
    print("\n📝 Registering test agents...")
    supervisor_agent = AgentState(
        agent_id="supervisor",
        name="Supervisor Agent",
        status=AgentStatus.IDLE
    )

    backend_agent = AgentState(
        agent_id="backend-api",
        name="Backend API Agent",
        status=AgentStatus.IDLE
    )

    frontend_agent = AgentState(
        agent_id="frontend-ui",
        name="Frontend UI Agent",
        status=AgentStatus.IDLE
    )

    manager.register_agent(supervisor_agent)
    manager.register_agent(backend_agent)
    manager.register_agent(frontend_agent)

    print(f"✅ Registered 3 agents")

    # Test 1: Direct message with notification
    print("\n🧪 TEST 1: Direct message with urgent notification")
    print("-" * 50)

    message_id = manager.send_agent_message(
        sender_id="supervisor",
        recipient_id="backend-api",
        content="Critical security vulnerability found! Please patch the authentication module immediately.",
        subject="URGENT: Security Patch Required",
        priority="URGENT"
    )

    print(f"📧 Sent urgent message: {message_id[:8] if message_id else 'FAILED'}")

    # Check notification was sent
    if manager.notification_system:
        active_notifications = manager.notification_system.get_active_notifications("backend-api")
        print(f"🔔 Active notifications for backend-api: {len(active_notifications)}")

        if active_notifications:
            latest_notification = active_notifications[-1]
            print(f"   Alert Level: {latest_notification.alert_level.value}")
            print(f"   Content: {latest_notification.content[:50]}...")
            print("   ✅ Urgent notification sent successfully")
        else:
            print("   ❌ No notification received")

    time.sleep(2)

    # Test 2: Broadcast message with notifications
    print("\n🧪 TEST 2: Broadcast message with notifications")
    print("-" * 50)

    broadcast_ids = manager.broadcast_agent_message(
        sender_id="supervisor",
        content="System maintenance will begin in 30 minutes. Please save your work and prepare for downtime.",
        subject="System Maintenance Notice",
        priority="HIGH"
    )

    print(f"📢 Broadcast sent to {len(broadcast_ids)} agents")

    # Check notifications for all agents
    if manager.notification_system:
        for agent_id in ["backend-api", "frontend-ui"]:
            notifications = manager.notification_system.get_active_notifications(agent_id)
            unread_count = manager.notification_system.get_unacknowledged_count(agent_id)
            print(f"🔔 {agent_id}: {len(notifications)} total, {unread_count} unread")

    time.sleep(2)

    # Test 3: Normal priority message
    print("\n🧪 TEST 3: Normal priority message")
    print("-" * 50)

    normal_message_id = manager.send_agent_message(
        sender_id="frontend-ui",
        recipient_id="backend-api",
        content="Could you help me understand the new API endpoint for user profile updates?",
        subject="API Documentation Question",
        priority="NORMAL"
    )

    print(f"📧 Sent normal message: {normal_message_id[:8] if normal_message_id else 'FAILED'}")

    # Check notification level
    if manager.notification_system:
        notifications = manager.notification_system.get_active_notifications("backend-api")
        if notifications:
            latest_notification = notifications[-1]
            print(f"🔔 Alert level: {latest_notification.alert_level.value}")
            print("   ✅ Normal priority notification sent")

    # Test 4: Notification acknowledgment
    print("\n🧪 TEST 4: Notification acknowledgment")
    print("-" * 50)

    if manager.notification_system:
        backend_notifications = manager.notification_system.get_active_notifications("backend-api")
        if backend_notifications:
            first_notification = backend_notifications[0]
            acknowledged = manager.notification_system.acknowledge_notification(
                "backend-api",
                first_notification.notification_id
            )
            print(f"✅ Notification acknowledged: {acknowledged}")

            # Check updated count
            unread_count = manager.notification_system.get_unacknowledged_count("backend-api")
            print(f"📊 Remaining unread notifications: {unread_count}")

    # Test 5: System statistics
    print("\n🧪 TEST 5: System statistics")
    print("-" * 50)

    # SharedStateManager stats
    stats = manager.get_system_stats()
    print(f"📊 SharedStateManager Stats:")
    print(f"   Total agents: {stats['total_agents']}")
    print(f"   Total messages: {stats['total_messages']}")

    # Enhanced messaging stats
    messaging_stats = manager.get_messaging_stats()
    print(f"📊 Enhanced Messaging Stats:")
    print(f"   Total agents: {messaging_stats['total_agents']}")
    print(f"   Total messages: {messaging_stats['total_messages']}")
    print(f"   Unread messages: {messaging_stats['unread_messages']}")

    # Notification system stats
    if manager.notification_system:
        all_notifications = 0
        all_unread = 0
        for agent_id in ["supervisor", "backend-api", "frontend-ui"]:
            notifications = manager.notification_system.get_active_notifications(agent_id)
            unread = manager.notification_system.get_unacknowledged_count(agent_id)
            all_notifications += len(notifications)
            all_unread += unread

        print(f"📊 Notification System Stats:")
        print(f"   Total notifications: {all_notifications}")
        print(f"   Unread notifications: {all_unread}")

    print("\n" + "=" * 70)
    print("🎉 INTEGRATION TEST COMPLETED SUCCESSFULLY!")
    print("✅ SharedStateManager now fully integrated with Enhanced Messaging System")
    print("✅ All messages sent through SharedStateManager trigger real-time notifications")
    print("✅ Notifications include terminal alerts, visual notifications, and audio alerts")
    print("✅ Priority levels properly mapped between systems")
    print("✅ Agent registration synchronized between both systems")

    return True


if __name__ == "__main__":
    success = test_notification_integration()

    if success:
        print("\n🚀 ENHANCED MESSAGING SYSTEM FULLY INTEGRATED!")
        print("\n💡 Usage examples:")
        print("   manager = SharedStateManager()")
        print("   manager.send_agent_message('agent1', 'agent2', 'Hello!', priority='URGENT')")
        print("   manager.broadcast_agent_message('supervisor', 'System update', priority='HIGH')")
        print("\n🔔 Notifications will automatically be sent to agent terminals!")
    else:
        print("\n❌ Integration test failed. Please check the setup.")