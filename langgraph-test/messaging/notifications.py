#!/usr/bin/env python3
"""
Real-time notification system for agent messaging
Provides immediate alerts and notifications when agents receive messages
"""

import json
import os
import subprocess
import threading
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path

# Import from parent shared_state
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_state.models import AgentMessage, MessagePriority, MessageType


class NotificationType(Enum):
    """Types of notifications"""
    VISUAL = "visual"
    AUDIO = "audio"
    TERMINAL = "terminal"
    WEB = "web"


class AlertLevel(Enum):
    """Alert levels for notifications"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


@dataclass
class NotificationConfig:
    """Configuration for agent notifications"""
    agent_id: str
    enable_visual: bool = True
    enable_audio: bool = True
    enable_terminal: bool = True
    enable_web: bool = True
    audio_on_urgent: bool = True
    terminal_flash: bool = True
    web_popup: bool = True
    quiet_hours_start: Optional[str] = None  # "22:00"
    quiet_hours_end: Optional[str] = None    # "08:00"


@dataclass
class AgentNotification:
    """Individual notification instance"""
    notification_id: str
    agent_id: str
    message_id: str
    notification_type: NotificationType
    alert_level: AlertLevel
    content: str
    subject: Optional[str] = None
    timestamp: datetime = None
    acknowledged: bool = False
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class AgentNotificationSystem:
    """Real-time notification system for agents"""

    def __init__(self, config_file: str = "notification_config.json"):
        self.configs: Dict[str, NotificationConfig] = {}
        self.active_notifications: Dict[str, List[AgentNotification]] = {}
        self.notification_queue: Dict[str, List[AgentNotification]] = {}
        self.observers: List[Callable] = []
        self.config_file = config_file
        self.running = True

        # Thread for processing notifications
        self.notification_thread = threading.Thread(
            target=self._process_notification_queue,
            daemon=True
        )
        self.notification_thread.start()

        # Load existing configurations
        self._load_configs()

    def register_agent(self, agent_id: str, config: Optional[NotificationConfig] = None):
        """Register an agent for notifications"""
        if config is None:
            config = NotificationConfig(agent_id=agent_id)

        self.configs[agent_id] = config
        self.active_notifications[agent_id] = []
        self.notification_queue[agent_id] = []

        self._save_configs()
        print(f"🔔 Notification system registered for agent: {agent_id}")

    def send_notification(self, agent_id: str, message: AgentMessage) -> str:
        """Send notification for new message"""
        if agent_id not in self.configs:
            self.register_agent(agent_id)

        config = self.configs[agent_id]

        # Check quiet hours
        if self._is_quiet_hours(config):
            print(f"🔇 Quiet hours active for {agent_id}, notification queued")
            return self._queue_notification(agent_id, message)

        # Determine alert level based on message priority
        alert_level = self._get_alert_level(message.priority)

        # Create notification
        notification = AgentNotification(
            notification_id=f"notif_{int(time.time() * 1000)}_{agent_id}",
            agent_id=agent_id,
            message_id=message.message_id,
            notification_type=NotificationType.TERMINAL,  # Primary notification
            alert_level=alert_level,
            content=message.content[:100] + "..." if len(message.content) > 100 else message.content,
            subject=message.subject,
            metadata={
                'sender_id': message.sender_id,
                'priority': message.priority.value,
                'message_type': message.message_type.value
            }
        )

        # Add to active notifications
        self.active_notifications[agent_id].append(notification)

        # Send immediate notifications based on config
        self._send_immediate_notifications(notification, config)

        # Notify observers
        for observer in self.observers:
            try:
                observer('notification_sent', notification)
            except Exception as e:
                print(f"Observer error: {e}")

        return notification.notification_id

    def _send_immediate_notifications(self, notification: AgentNotification, config: NotificationConfig):
        """Send immediate notifications based on configuration"""

        # Terminal notification
        if config.enable_terminal:
            self._send_terminal_notification(notification)

        # Audio notification for urgent messages
        if (config.enable_audio and config.audio_on_urgent and
            notification.alert_level in [AlertLevel.URGENT, AlertLevel.CRITICAL]):
            self._send_audio_notification(notification)

        # Visual notification
        if config.enable_visual:
            self._send_visual_notification(notification)

    def _send_terminal_notification(self, notification: AgentNotification):
        """Send notification to agent's terminal"""
        try:
            session_id = f"claude-{notification.agent_id}"

            # Priority indicator
            priority_icons = {
                AlertLevel.LOW: "📝",
                AlertLevel.NORMAL: "📬",
                AlertLevel.HIGH: "⚠️",
                AlertLevel.URGENT: "🚨",
                AlertLevel.CRITICAL: "🔥"
            }

            icon = priority_icons.get(notification.alert_level, "📬")

            # Format notification message
            notif_msg = (
                f"\n{icon} NEW MESSAGE [{notification.message_id[:8]}]\n"
                f"From: {notification.metadata.get('sender_id', 'Unknown')}\n"
                f"Priority: {notification.alert_level.value.upper()}\n"
                f"Subject: {notification.subject or 'No subject'}\n"
                f"Content: {notification.content}\n"
                f"🎯 Actions: inbox list | message-action {notification.message_id[:8]} [action]\n"
                f"⏰ Time: {notification.timestamp.strftime('%H:%M:%S')}\n"
            )

            # Clear any existing input first
            subprocess.run([
                "/opt/homebrew/bin/tmux", "send-keys", "-t", session_id,
                "C-c"
            ])

            # Send the command first
            simple_msg = f"🔔 NEW MSG [{notification.message_id[:8]}] from {notification.metadata.get('sender_id', 'Unknown')}: {notification.subject or 'No subject'}"
            subprocess.run([
                "/opt/homebrew/bin/tmux", "send-keys", "-t", session_id,
                f"echo '{simple_msg}'"
            ])

            # Wait a moment for the command to be received, then send Enter
            import time
            time.sleep(0.1)  # Short delay to let command be processed
            subprocess.run([
                "/opt/homebrew/bin/tmux", "send-keys", "-t", session_id,
                "Enter"
            ])
            print(f"🔔 Terminal notification sent to {session_id}")

        except Exception as e:
            print(f"❌ Failed to send terminal notification: {e}")

    def _send_audio_notification(self, notification: AgentNotification):
        """Send audio alert for urgent notifications"""
        try:
            # Use system bell or play sound
            if notification.alert_level == AlertLevel.CRITICAL:
                # Multiple beeps for critical
                for _ in range(3):
                    subprocess.run(["afplay", "/System/Library/Sounds/Sosumi.aiff"],
                                 capture_output=True)
                    time.sleep(0.2)
            elif notification.alert_level == AlertLevel.URGENT:
                # Single urgent sound
                subprocess.run(["afplay", "/System/Library/Sounds/Ping.aiff"],
                             capture_output=True)

            print(f"🔊 Audio notification sent for {notification.alert_level.value}")

        except Exception as e:
            print(f"❌ Failed to send audio notification: {e}")

    def _send_visual_notification(self, notification: AgentNotification):
        """Send visual notification (system notification)"""
        try:
            # macOS notification
            title = f"Message from {notification.metadata.get('sender_id', 'Agent')}"
            subtitle = notification.subject or "New message"
            message = notification.content[:100]

            cmd = [
                "osascript", "-e",
                f'display notification "{message}" with title "{title}" subtitle "{subtitle}"'
            ]

            subprocess.run(cmd, capture_output=True)
            print(f"💻 Visual notification sent for {notification.agent_id}")

        except Exception as e:
            print(f"❌ Failed to send visual notification: {e}")

    def acknowledge_notification(self, agent_id: str, notification_id: str) -> bool:
        """Mark notification as acknowledged"""
        if agent_id in self.active_notifications:
            for notification in self.active_notifications[agent_id]:
                if notification.notification_id == notification_id:
                    notification.acknowledged = True
                    print(f"✅ Notification {notification_id[:8]} acknowledged")
                    return True
        return False

    def get_active_notifications(self, agent_id: str) -> List[AgentNotification]:
        """Get active notifications for agent"""
        return self.active_notifications.get(agent_id, [])

    def get_unacknowledged_count(self, agent_id: str) -> int:
        """Get count of unacknowledged notifications"""
        if agent_id not in self.active_notifications:
            return 0

        return len([n for n in self.active_notifications[agent_id]
                   if not n.acknowledged])

    def clear_old_notifications(self, agent_id: str, hours: int = 24):
        """Clear notifications older than specified hours"""
        if agent_id not in self.active_notifications:
            return

        cutoff_time = datetime.now() - timedelta(hours=hours)

        self.active_notifications[agent_id] = [
            n for n in self.active_notifications[agent_id]
            if n.timestamp > cutoff_time
        ]

    def update_agent_config(self, agent_id: str, config: NotificationConfig):
        """Update notification configuration for agent"""
        self.configs[agent_id] = config
        self._save_configs()
        print(f"🔧 Updated notification config for {agent_id}")

    def _get_alert_level(self, priority: MessagePriority) -> AlertLevel:
        """Convert message priority to alert level"""
        mapping = {
            MessagePriority.LOW: AlertLevel.LOW,
            MessagePriority.NORMAL: AlertLevel.NORMAL,
            MessagePriority.HIGH: AlertLevel.HIGH,
            MessagePriority.URGENT: AlertLevel.URGENT
        }
        return mapping.get(priority, AlertLevel.NORMAL)

    def _is_quiet_hours(self, config: NotificationConfig) -> bool:
        """Check if current time is in quiet hours"""
        if not config.quiet_hours_start or not config.quiet_hours_end:
            return False

        now = datetime.now().time()
        start = datetime.strptime(config.quiet_hours_start, "%H:%M").time()
        end = datetime.strptime(config.quiet_hours_end, "%H:%M").time()

        if start <= end:
            return start <= now <= end
        else:  # Spans midnight
            return now >= start or now <= end

    def _queue_notification(self, agent_id: str, message: AgentMessage) -> str:
        """Queue notification for later delivery"""
        notification = AgentNotification(
            notification_id=f"queued_{int(time.time() * 1000)}_{agent_id}",
            agent_id=agent_id,
            message_id=message.message_id,
            notification_type=NotificationType.TERMINAL,
            alert_level=self._get_alert_level(message.priority),
            content=message.content[:100],
            subject=message.subject
        )

        self.notification_queue[agent_id].append(notification)
        return notification.notification_id

    def _process_notification_queue(self):
        """Background thread to process queued notifications"""
        while self.running:
            try:
                for agent_id, queue in self.notification_queue.items():
                    if queue and agent_id in self.configs:
                        config = self.configs[agent_id]

                        # Check if quiet hours ended
                        if not self._is_quiet_hours(config):
                            # Send queued notifications
                            while queue:
                                notification = queue.pop(0)
                                self._send_immediate_notifications(notification, config)
                                self.active_notifications[agent_id].append(notification)

                time.sleep(30)  # Check every 30 seconds

            except Exception as e:
                print(f"Notification queue processing error: {e}")
                time.sleep(60)

    def _load_configs(self):
        """Load notification configurations from file"""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    data = json.load(f)

                for agent_id, config_data in data.items():
                    self.configs[agent_id] = NotificationConfig(**config_data)

                print(f"📋 Loaded notification configs for {len(self.configs)} agents")
        except Exception as e:
            print(f"❌ Error loading notification configs: {e}")

    def _save_configs(self):
        """Save notification configurations to file"""
        try:
            data = {}
            for agent_id, config in self.configs.items():
                data[agent_id] = asdict(config)

            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"❌ Error saving notification configs: {e}")

    def add_observer(self, observer: Callable):
        """Add observer for notification events"""
        self.observers.append(observer)

    def remove_observer(self, observer: Callable):
        """Remove observer"""
        if observer in self.observers:
            self.observers.remove(observer)

    def shutdown(self):
        """Shutdown notification system"""
        self.running = False
        if self.notification_thread.is_alive():
            self.notification_thread.join(timeout=5)
        print("🔕 Notification system shutdown")


# Global notification system instance
_notification_system = None


def get_notification_system() -> AgentNotificationSystem:
    """Get global notification system instance"""
    global _notification_system
    if _notification_system is None:
        _notification_system = AgentNotificationSystem()
    return _notification_system


def send_agent_notification(agent_id: str, message: AgentMessage) -> str:
    """Convenience function to send notification"""
    return get_notification_system().send_notification(agent_id, message)


if __name__ == "__main__":
    # Test the notification system
    from shared_state.models import MessageType, MessagePriority

    # Create test system
    notif_system = AgentNotificationSystem()

    # Register test agent
    notif_system.register_agent("backend-api")

    # Create test message
    test_message = AgentMessage(
        sender_id="supervisor",
        recipient_id="backend-api",
        content="This is a test urgent message for the notification system!",
        subject="Test Notification",
        priority=MessagePriority.URGENT,
        message_type=MessageType.DIRECT
    )

    # Send notification
    notif_id = notif_system.send_notification("backend-api", test_message)
    print(f"✅ Test notification sent: {notif_id}")

    # Check active notifications
    active = notif_system.get_active_notifications("backend-api")
    print(f"📬 Active notifications: {len(active)}")

    time.sleep(2)
    notif_system.shutdown()