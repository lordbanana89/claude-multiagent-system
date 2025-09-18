#!/usr/bin/env python3
"""
Test script for the new messaging system
"""

from shared_state import (
    SharedStateManager, create_send_message_command,
    create_broadcast_command, create_inbox_command
)


def test_messaging_system():
    """Test the new messaging system functionality"""
    print("🧪 Testing Advanced Messaging System...")

    # Initialize the system
    manager = SharedStateManager()

    # Test agent registration (should already exist from main system)
    agents = list(manager.state.agents.keys())
    print(f"📋 Found {len(agents)} agents: {', '.join(agents)}")

    if len(agents) < 2:
        print("❌ Need at least 2 agents for testing")
        return

    # Test 1: Send direct message
    sender = agents[0]
    recipient = agents[1]

    print(f"\n🔹 Test 1: Sending message from {sender} to {recipient}")
    message_id = manager.send_agent_message(
        sender_id=sender,
        recipient_id=recipient,
        content="Hello! This is a test message from the new messaging system.",
        subject="Test Message",
        priority="HIGH"
    )

    if message_id:
        print(f"✅ Message sent successfully! ID: {message_id[:8]}")
    else:
        print("❌ Failed to send message")

    # Test 2: Send broadcast message
    print(f"\n🔹 Test 2: Broadcasting message from {sender}")
    broadcast_ids = manager.broadcast_agent_message(
        sender_id=sender,
        content="This is a broadcast message to all agents!",
        subject="System Announcement",
        priority="NORMAL"
    )

    if broadcast_ids:
        print(f"✅ Broadcast sent to {len(broadcast_ids)} agents")
    else:
        print("❌ Failed to broadcast message")

    # Test 3: Check inbox
    print(f"\n🔹 Test 3: Checking {recipient}'s inbox")
    inbox = manager.get_agent_inbox(recipient)
    print(f"📬 Inbox has {len(inbox.messages)} total messages, {inbox.unread_count} unread")

    recent_messages = inbox.get_recent_messages(5)
    for msg in recent_messages:
        status = "📩" if msg.status.value == "read" else "📬"
        msg_type = "🔊" if msg.is_broadcast() else "💬"
        print(f"  {status} {msg_type} [{msg.message_id[:8]}] From: {msg.sender_id}")
        print(f"      Subject: {msg.subject or 'No subject'}")
        print(f"      Content: {msg.content[:50]}{'...' if len(msg.content) > 50 else ''}")

    # Test 4: Mark message as read
    if recent_messages:
        test_msg = recent_messages[0]
        print(f"\n🔹 Test 4: Marking message {test_msg.message_id[:8]} as read")
        success = manager.mark_agent_message_read(recipient, test_msg.message_id)
        if success:
            print("✅ Message marked as read")
            # Check updated inbox
            updated_inbox = manager.get_agent_inbox(recipient)
            print(f"📬 Updated inbox: {updated_inbox.unread_count} unread messages")
        else:
            print("❌ Failed to mark message as read")

    # Test 5: Messaging statistics
    print(f"\n🔹 Test 5: System messaging statistics")
    stats = manager.get_messaging_stats()
    print(f"📊 Total agents: {stats['total_agents']}")
    print(f"📊 Total messages: {stats['total_messages']}")
    print(f"📊 Unread messages: {stats['unread_messages']}")
    print(f"📊 Active conversations: {stats['active_conversations']}")

    # Test 6: Terminal commands simulation
    print(f"\n🔹 Test 6: Testing terminal commands")

    # Create command functions
    send_cmd = create_send_message_command(manager.messaging_system, sender)
    broadcast_cmd = create_broadcast_command(manager.messaging_system, sender)
    inbox_cmd = create_inbox_command(manager.messaging_system, recipient)

    # Test send command
    print("Testing send-message command:")
    result = send_cmd(recipient, "This", "is", "a", "terminal", "test")
    print(f"  Result: {result}")

    # Test broadcast command
    print("Testing broadcast command:")
    result = broadcast_cmd("Broadcasting", "from", "terminal!")
    print(f"  Result: {result}")

    # Test inbox command
    print("Testing inbox list command:")
    result = inbox_cmd("list")
    print(f"  Result: {result[:200]}{'...' if len(result) > 200 else ''}")

    print("\n🎉 Messaging system test completed!")


if __name__ == "__main__":
    test_messaging_system()