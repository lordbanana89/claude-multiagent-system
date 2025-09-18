#!/usr/bin/env python3
"""
Enhanced Terminal Interface for Agent Message Management
Provides advanced terminal commands and interactive message handling
"""

import json
import re
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Import from parent shared_state and messaging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_state.models import AgentMessage, MessagePriority
from messaging.notifications import get_notification_system
from messaging.classification import get_message_classifier, MessageType, ResponseRequirement
from messaging.workflow import get_decision_engine, WorkflowAction


class MessageActionHandler:
    """Handles message actions from terminal commands"""

    def __init__(self):
        self.notification_system = get_notification_system()
        self.classifier = get_message_classifier()
        self.decision_engine = get_decision_engine()
        self.response_templates = self._load_response_templates()

    def handle_message_action(self, agent_id: str, message_id: str, action: str, *args) -> str:
        """Handle message action command"""
        try:
            action_lower = action.lower()

            if action_lower == "respond":
                return self._handle_respond(agent_id, message_id, " ".join(args))
            elif action_lower == "acknowledge" or action_lower == "ack":
                return self._handle_acknowledge(agent_id, message_id)
            elif action_lower == "archive":
                return self._handle_archive(agent_id, message_id)
            elif action_lower == "escalate":
                target = args[0] if args else "supervisor"
                reason = " ".join(args[1:]) if len(args) > 1 else "Manual escalation"
                return self._handle_escalate(agent_id, message_id, target, reason)
            elif action_lower == "accept":
                return self._handle_accept_task(agent_id, message_id)
            elif action_lower == "reject":
                reason = " ".join(args) if args else "Unable to complete"
                return self._handle_reject_task(agent_id, message_id, reason)
            elif action_lower == "info":
                return self._handle_get_info(agent_id, message_id)
            elif action_lower == "remind":
                minutes = int(args[0]) if args and args[0].isdigit() else 30
                return self._handle_set_reminder(agent_id, message_id, minutes)
            else:
                return f"❌ Unknown action: {action}. Available: respond, acknowledge, archive, escalate, accept, reject, info, remind"

        except Exception as e:
            return f"❌ Error handling action: {e}"

    def _handle_respond(self, agent_id: str, message_id: str, response: str) -> str:
        """Handle respond action"""
        if not response.strip():
            return f"❌ Response cannot be empty. Usage: message-action {message_id} respond <your message>"

        # This would integrate with the messaging system to send actual response
        print(f"📨 {agent_id}: Responding to {message_id[:8]}: {response}")
        return f"✅ Response sent to message {message_id[:8]}"

    def _handle_acknowledge(self, agent_id: str, message_id: str) -> str:
        """Handle acknowledge action"""
        self.notification_system.acknowledge_notification(agent_id, message_id)
        print(f"✅ {agent_id}: Acknowledged message {message_id[:8]}")
        return f"✅ Message {message_id[:8]} acknowledged"

    def _handle_archive(self, agent_id: str, message_id: str) -> str:
        """Handle archive action"""
        # This would integrate with the messaging system to archive message
        print(f"📁 {agent_id}: Archived message {message_id[:8]}")
        return f"✅ Message {message_id[:8]} archived"

    def _handle_escalate(self, agent_id: str, message_id: str, target: str, reason: str) -> str:
        """Handle escalate action"""
        # This would integrate with the messaging system to escalate message
        print(f"⬆️ {agent_id}: Escalating {message_id[:8]} to {target} - {reason}")
        return f"✅ Message {message_id[:8]} escalated to {target}"

    def _handle_accept_task(self, agent_id: str, message_id: str) -> str:
        """Handle task acceptance"""
        # Generate automatic acceptance response based on agent capabilities
        response = self._generate_task_acceptance_response(agent_id)
        print(f"🎯 {agent_id}: Accepted task {message_id[:8]} - {response}")
        return f"✅ Task {message_id[:8]} accepted. Response: {response}"

    def _handle_reject_task(self, agent_id: str, message_id: str, reason: str) -> str:
        """Handle task rejection"""
        print(f"❌ {agent_id}: Rejected task {message_id[:8]} - {reason}")
        return f"✅ Task {message_id[:8]} rejected. Reason: {reason}"

    def _handle_get_info(self, agent_id: str, message_id: str) -> str:
        """Handle get message info"""
        # This would retrieve message details from the messaging system
        return f"""
📧 Message Info [{message_id[:8]}]:
   From: supervisor
   Subject: Task Assignment
   Priority: HIGH
   Type: TASK_ASSIGNMENT
   Requires Response: Yes
   Timeout: 60 minutes
   Actions: accept, reject, escalate, respond
        """

    def _handle_set_reminder(self, agent_id: str, message_id: str, minutes: int) -> str:
        """Handle set reminder"""
        remind_time = datetime.now().strftime('%H:%M')
        print(f"⏰ {agent_id}: Reminder set for message {message_id[:8]} in {minutes} minutes")
        return f"✅ Reminder set for message {message_id[:8]} in {minutes} minutes"

    def _generate_task_acceptance_response(self, agent_id: str) -> str:
        """Generate task acceptance response based on agent type"""
        responses = {
            "backend-api": "Task accepted. Starting API implementation now. Will provide progress updates every 30 minutes.",
            "frontend-ui": "UI task accepted. Beginning frontend development. Wireframes will be ready shortly.",
            "database": "Database task acknowledged. Starting schema/query work immediately.",
            "testing": "Testing task received. Creating test suite and beginning validation process.",
            "instagram": "Social media task accepted. Preparing content and scheduling posts.",
            "supervisor": "Coordination task accepted. Delegating to appropriate agents now.",
            "master": "Strategic task accepted. Initiating system-wide implementation."
        }

        return responses.get(agent_id, "Task accepted. Beginning work immediately.")

    def _load_response_templates(self) -> Dict[str, List[str]]:
        """Load response templates for quick replies"""
        return {
            "acknowledgment": [
                "Message received and understood.",
                "Acknowledged. Will proceed accordingly.",
                "Received. Taking action now.",
                "Understood. Processing request."
            ],
            "task_acceptance": [
                "Task accepted. Starting work immediately.",
                "Confirmed. Beginning implementation now.",
                "Task received. Work in progress.",
                "Accepted. Will provide updates shortly."
            ],
            "completion": [
                "Task completed successfully.",
                "Work finished as requested.",
                "Implementation complete and tested.",
                "Task done. Ready for review."
            ],
            "need_clarification": [
                "Could you provide more details about this request?",
                "I need additional information to proceed.",
                "Please clarify the requirements.",
                "More context needed to complete this task."
            ],
            "escalation": [
                "This task exceeds my current capabilities. Escalating.",
                "Requires higher-level approval. Forwarding to supervisor.",
                "Outside my scope. Escalating for proper assignment.",
                "Need supervisor guidance on this request."
            ]
        }


class EnhancedTerminalInterface:
    """Enhanced terminal interface for message management"""

    def __init__(self):
        self.action_handler = MessageActionHandler()
        self.command_history: List[str] = []

    def create_inbox_command(self, agent_id: str) -> callable:
        """Create inbox management command function"""
        def inbox_command(*args) -> str:
            if not args:
                return self._show_inbox_help()

            command = args[0].lower()

            if command == "list":
                return self._list_messages(agent_id, "all")
            elif command == "unread":
                return self._list_messages(agent_id, "unread")
            elif command == "urgent":
                return self._list_messages(agent_id, "urgent")
            elif command == "tasks":
                return self._list_messages(agent_id, "tasks")
            elif command == "manage":
                return self._interactive_inbox_manager(agent_id)
            elif command == "stats":
                return self._show_inbox_stats(agent_id)
            elif command == "clear":
                return self._clear_notifications(agent_id)
            else:
                return self._show_inbox_help()

        return inbox_command

    def create_message_action_command(self, agent_id: str) -> callable:
        """Create message action command function"""
        def message_action_command(*args) -> str:
            if len(args) < 2:
                return "❌ Usage: message-action <message_id> <action> [args...]"

            message_id = args[0]
            action = args[1]
            action_args = args[2:] if len(args) > 2 else []

            return self.action_handler.handle_message_action(agent_id, message_id, action, *action_args)

        return message_action_command

    def create_quick_reply_command(self, agent_id: str) -> callable:
        """Create quick reply command function"""
        def quick_reply_command(*args) -> str:
            if len(args) < 2:
                return "❌ Usage: quick-reply <message_id> <response>"

            message_id = args[0]
            response = " ".join(args[1:])

            return self.action_handler.handle_message_action(agent_id, message_id, "respond", response)

        return quick_reply_command

    def create_auto_respond_command(self, agent_id: str) -> callable:
        """Create auto-respond configuration command"""
        def auto_respond_command(*args) -> str:
            if len(args) < 2:
                return """❌ Usage: auto-respond <pattern> <response>
Examples:
  auto-respond "status" "Current status: All systems operational"
  auto-respond "ping" "Pong! Agent is active and responding"
                """

            pattern = args[0]
            response = " ".join(args[1:])

            # This would configure auto-response patterns
            print(f"🤖 {agent_id}: Auto-response configured - '{pattern}' → '{response}'")
            return f"✅ Auto-response configured for pattern: {pattern}"

        return auto_respond_command

    def _list_messages(self, agent_id: str, filter_type: str) -> str:
        """List messages based on filter type"""
        # This would integrate with the messaging system to get actual messages
        messages = self._get_mock_messages(agent_id, filter_type)

        if not messages:
            return f"📭 No {filter_type} messages found."

        output = [f"📬 {filter_type.upper()} MESSAGES for {agent_id}:"]
        output.append("-" * 60)

        for i, msg in enumerate(messages, 1):
            status_icon = self._get_status_icon(msg)
            priority_icon = self._get_priority_icon(msg)
            time_str = msg.get('timestamp', 'Unknown')

            output.append(f"{i}. {status_icon} {priority_icon} [{msg['id'][:8]}] From: {msg['sender']}")
            output.append(f"   Subject: {msg['subject']}")
            output.append(f"   Content: {msg['content'][:50]}{'...' if len(msg['content']) > 50 else ''}")
            output.append(f"   Time: {time_str} | Actions: {', '.join(msg['actions'])}")
            output.append("")

        output.append(f"💡 Use: message-action <id> <action> to interact with messages")
        return "\n".join(output)

    def _interactive_inbox_manager(self, agent_id: str) -> str:
        """Start interactive inbox management"""
        return f"""
🎛️  INTERACTIVE INBOX MANAGER - {agent_id}
===============================================

📬 Available Commands:
  list [filter]     - List messages (all/unread/urgent/tasks)
  action <id> <cmd> - Take action on message
  respond <id>      - Quick respond to message
  clear             - Clear read notifications
  stats             - Show inbox statistics
  help              - Show this help

🎯 Quick Actions:
  a <id>    - Acknowledge message
  r <id>    - Respond to message
  e <id>    - Escalate message
  arch <id> - Archive message

Type 'exit' to return to normal terminal.
        """

    def _show_inbox_stats(self, agent_id: str) -> str:
        """Show inbox statistics"""
        # This would get actual stats from the messaging system
        return f"""
📊 INBOX STATISTICS - {agent_id}
================================

📬 Message Counts:
   Total Messages: 15
   Unread: 3
   Urgent: 1
   Tasks Pending: 2
   Archived: 9

⏰ Response Times:
   Average Response: 12 minutes
   Fastest Response: 2 minutes
   Overdue Messages: 0

🎯 Message Types:
   Task Assignments: 8
   Questions: 4
   Information: 2
   Urgent Alerts: 1

🔄 Recent Activity:
   Messages Today: 5
   Messages This Week: 15
   Auto-Responses: 3
        """

    def _clear_notifications(self, agent_id: str) -> str:
        """Clear read notifications"""
        # This would clear notifications in the notification system
        print(f"🧹 {agent_id}: Clearing read notifications")
        return "✅ Read notifications cleared"

    def _show_inbox_help(self) -> str:
        """Show inbox command help"""
        return """
📬 INBOX COMMANDS:
==================

inbox list      - Show all messages
inbox unread    - Show unread messages only
inbox urgent    - Show urgent messages only
inbox tasks     - Show task assignments only
inbox manage    - Start interactive manager
inbox stats     - Show statistics
inbox clear     - Clear read notifications

💡 TIP: Use 'message-action <id> <action>' to interact with specific messages
        """

    def _get_mock_messages(self, agent_id: str, filter_type: str) -> List[Dict]:
        """Get mock messages for demonstration"""
        all_messages = [
            {
                'id': 'msg_abc123',
                'sender': 'supervisor',
                'subject': 'Deploy Authentication Module',
                'content': 'Please deploy the new authentication module to production immediately.',
                'priority': 'HIGH',
                'type': 'TASK_ASSIGNMENT',
                'status': 'unread',
                'timestamp': '14:30',
                'actions': ['accept', 'reject', 'escalate']
            },
            {
                'id': 'msg_def456',
                'sender': 'frontend-ui',
                'subject': 'API Integration Question',
                'content': 'How do I integrate the new user profile API endpoint?',
                'priority': 'NORMAL',
                'type': 'QUESTION',
                'status': 'unread',
                'timestamp': '14:15',
                'actions': ['respond', 'escalate']
            },
            {
                'id': 'msg_ghi789',
                'sender': 'database',
                'subject': 'Migration Complete',
                'content': 'Database migration completed successfully. All tables updated.',
                'priority': 'LOW',
                'type': 'INFORMATION',
                'status': 'read',
                'timestamp': '13:45',
                'actions': ['acknowledge', 'archive']
            }
        ]

        if filter_type == "unread":
            return [msg for msg in all_messages if msg['status'] == 'unread']
        elif filter_type == "urgent":
            return [msg for msg in all_messages if msg['priority'] in ['HIGH', 'URGENT']]
        elif filter_type == "tasks":
            return [msg for msg in all_messages if msg['type'] == 'TASK_ASSIGNMENT']
        else:
            return all_messages

    def _get_status_icon(self, message: Dict) -> str:
        """Get status icon for message"""
        if message['status'] == 'unread':
            return "📬"
        else:
            return "📧"

    def _get_priority_icon(self, message: Dict) -> str:
        """Get priority icon for message"""
        priority_icons = {
            'LOW': "📝",
            'NORMAL': "📋",
            'HIGH': "⚠️",
            'URGENT': "🚨",
            'CRITICAL': "🔥"
        }
        return priority_icons.get(message['priority'], "📋")

    def send_terminal_notification(self, agent_id: str, message: AgentMessage):
        """Send formatted notification to agent's terminal"""
        try:
            session_id = f"claude-{agent_id}"

            # Classify message for better formatting
            category = self.action_handler.classifier.classify_message(message)

            # Format notification with enhanced info
            priority_icon = {
                'LOW': "📝",
                'NORMAL': "📬",
                'HIGH': "⚠️",
                'URGENT': "🚨"
            }.get(message.priority.value, "📬")

            type_icon = {
                'TASK_ASSIGNMENT': "🎯",
                'QUESTION': "❓",
                'INFORMATION': "📄",
                'URGENT_ALERT': "🚨",
                'CONFIRMATION': "✅"
            }.get(category.message_type.value, "📬")

            notif_msg = f"""
{priority_icon} NEW MESSAGE {type_icon} [{message.message_id[:8]}]
From: {message.sender_id} | Priority: {message.priority.value}
Subject: {message.subject or 'No subject'}
Content: {message.content[:80]}{'...' if len(message.content) > 80 else ''}

🎯 Quick Actions:
   message-action {message.message_id[:8]} accept    # Accept task
   message-action {message.message_id[:8]} respond   # Respond to message
   message-action {message.message_id[:8]} escalate  # Escalate to supervisor
   quick-reply {message.message_id[:8]} <response>   # Quick response

📋 More: message-action {message.message_id[:8]} info
⏰ Time: {datetime.now().strftime('%H:%M:%S')}
"""

            # Send to tmux session - first send command
            subprocess.run([
                "/opt/homebrew/bin/tmux", "send-keys", "-t", session_id,
                f"echo '{notif_msg}'"
            ], capture_output=True, text=True)

            # Wait for command to be processed, then send Enter
            import time
            time.sleep(0.1)  # Short delay to let command be processed
            subprocess.run([
                "/opt/homebrew/bin/tmux", "send-keys", "-t", session_id,
                "Enter"
            ], capture_output=True, text=True)
            print(f"🔔 Enhanced notification sent to {session_id}")

        except Exception as e:
            print(f"❌ Failed to send terminal notification: {e}")


# Global interface instance
_terminal_interface = None


def get_terminal_interface() -> EnhancedTerminalInterface:
    """Get global terminal interface instance"""
    global _terminal_interface
    if _terminal_interface is None:
        _terminal_interface = EnhancedTerminalInterface()
    return _terminal_interface


# Command creation functions for easy integration
def create_enhanced_inbox_command(agent_id: str) -> callable:
    """Create enhanced inbox command for agent"""
    return get_terminal_interface().create_inbox_command(agent_id)


def create_message_action_command(agent_id: str) -> callable:
    """Create message action command for agent"""
    return get_terminal_interface().create_message_action_command(agent_id)


def create_quick_reply_command(agent_id: str) -> callable:
    """Create quick reply command for agent"""
    return get_terminal_interface().create_quick_reply_command(agent_id)


def create_auto_respond_command(agent_id: str) -> callable:
    """Create auto-respond command for agent"""
    return get_terminal_interface().create_auto_respond_command(agent_id)


if __name__ == "__main__":
    # Test the enhanced interface
    interface = EnhancedTerminalInterface()

    # Test inbox command
    inbox_cmd = interface.create_inbox_command("backend-api")
    print("Testing inbox list:")
    print(inbox_cmd("list"))

    print("\n" + "="*60 + "\n")

    # Test message action command
    action_cmd = interface.create_message_action_command("backend-api")
    print("Testing message action:")
    print(action_cmd("msg_abc123", "accept"))

    print("\n" + "="*60 + "\n")

    # Test quick reply command
    reply_cmd = interface.create_quick_reply_command("backend-api")
    print("Testing quick reply:")
    print(reply_cmd("msg_def456", "The API endpoint is /api/v1/users/profile"))

    print("\n" + "="*60 + "\n")

    # Test stats
    print("Testing inbox stats:")
    print(inbox_cmd("stats"))