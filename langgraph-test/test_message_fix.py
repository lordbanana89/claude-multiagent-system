#!/usr/bin/env python3
"""
Test del fix per l'invio di messaggi ai terminali degli agenti
"""

from shared_state.manager import SharedStateManager
from shared_state.models import AgentState, AgentStatus

def test_message_sending():
    print("🔧 TESTING MESSAGE SENDING FIX")
    print("=" * 50)

    # Initialize manager
    manager = SharedStateManager()

    if not manager.notification_system:
        print("❌ Notification system not available")
        return

    print("✅ Sending test message to backend-api...")

    # Send test message
    message_id = manager.send_agent_message(
        sender_id="supervisor",
        recipient_id="backend-api",
        content="Test message - verifica che questo messaggio appaia correttamente nel terminale!",
        subject="TEST: Message Fix Verification",
        priority="HIGH"
    )

    print(f"📧 Message sent: {message_id[:8] if message_id else 'FAILED'}")
    print("💡 Check the claude-backend-api terminal to verify the message appears correctly")
    print("💡 The message should be displayed immediately after being sent")

if __name__ == "__main__":
    test_message_sending()