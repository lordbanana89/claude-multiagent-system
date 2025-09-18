"""
Inbox Integration Bridge
Integrates inbox storage with existing shared_state system
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import threading

from shared_state.models import SharedState, InterAgentMessage
from shared_state.messaging import MessagingSystem, AgentMessage as SharedAgentMessage
from .storage import InboxStorage, InboxManager
from .routing import MessageRouter
from shared_state.models import MessageType, MessagePriority, MessageStatus


class InboxSharedStateAdapter:
    """Adapter to bridge inbox system with shared_state"""

    def __init__(self, shared_state_manager, inbox_manager: InboxManager):
        self.shared_state_manager = shared_state_manager
        self.inbox_manager = inbox_manager
        self.lock = threading.RLock()

        # Register as observer to shared_state messaging
        self.shared_state_manager.register_observer(self._handle_shared_state_event)

    def _handle_shared_state_event(self, event_type: str, data: Any):
        """Handle shared state events and sync to inbox"""
        if event_type in ["advanced_message_sent", "broadcast_sent"]:
            # Message already handled by shared_state's advanced messaging
            # No need to duplicate
            pass

    def send_message_via_inbox(self, sender_id: str, recipient_id: str, content: str,
                              subject: Optional[str] = None, priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """Send message through inbox system and sync to shared_state"""
        with self.lock:
            # Send through inbox system
            message = self.inbox_manager.send_message(
                sender_id=sender_id,
                recipient_id=recipient_id,
                content=content,
                subject=subject,
                priority=priority
            )

            # Sync to shared_state legacy format
            legacy_message = InterAgentMessage(
                message_id=message.message_id,
                from_agent=sender_id,
                to_agent=recipient_id,
                message=content,
                timestamp=message.timestamp,
                read=False
            )

            # Add to shared_state messages list
            self.shared_state_manager.state.messages.append(legacy_message)
            self.shared_state_manager.save_state()

            return message.message_id

    def get_unified_inbox(self, agent_id: str) -> Dict[str, Any]:
        """Get unified inbox combining both systems"""
        with self.lock:
            # Get from inbox system
            inbox_data = self.inbox_manager.get_inbox(agent_id)

            # Get from shared_state system
            shared_inbox = self.shared_state_manager.get_agent_inbox(agent_id)

            # Combine and deduplicate
            all_messages = []

            # Add inbox messages
            for msg in inbox_data['messages']:
                all_messages.append({
                    'source': 'inbox',
                    'message_id': msg.message_id,
                    'sender_id': msg.sender_id,
                    'content': msg.content,
                    'subject': msg.subject,
                    'timestamp': msg.timestamp,
                    'status': msg.status.value,
                    'priority': msg.priority.value
                })

            # Add shared_state messages (avoid duplicates)
            existing_ids = {msg['message_id'] for msg in all_messages}
            for msg in shared_inbox.messages:
                if msg.message_id not in existing_ids:
                    all_messages.append({
                        'source': 'shared_state',
                        'message_id': msg.message_id,
                        'sender_id': msg.sender_id,
                        'content': msg.content,
                        'subject': msg.subject,
                        'timestamp': msg.timestamp,
                        'status': msg.status.value,
                        'priority': msg.priority.value
                    })

            # Sort by timestamp
            all_messages.sort(key=lambda x: x['timestamp'], reverse=True)

            return {
                'agent_id': agent_id,
                'messages': all_messages,
                'total_count': len(all_messages),
                'inbox_count': len(inbox_data['messages']),
                'shared_state_count': len(shared_inbox.messages),
                'unread_count': inbox_data['unread_count'] + shared_inbox.unread_count
            }

    def sync_to_inbox(self, force: bool = False) -> bool:
        """Sync shared_state messages to inbox storage"""
        with self.lock:
            try:
                synced_count = 0

                # Get all messages from shared_state
                for legacy_msg in self.shared_state_manager.state.messages:
                    # Check if already exists in inbox
                    existing = self.inbox_manager.storage.get_message_by_id(legacy_msg.message_id)

                    if existing is None or force:
                        # Convert to inbox format
                        inbox_message = SharedAgentMessage(
                            message_id=legacy_msg.message_id,
                            sender_id=legacy_msg.from_agent,
                            recipient_id=legacy_msg.to_agent,
                            content=legacy_msg.message,
                            timestamp=legacy_msg.timestamp,
                            status=MessageStatus.READ if legacy_msg.read else MessageStatus.SENT
                        )

                        # Store in inbox
                        if self.inbox_manager.storage.store_message(inbox_message):
                            synced_count += 1

                print(f"✅ Synced {synced_count} messages to inbox storage")
                return True

            except Exception as e:
                print(f"❌ Error syncing to inbox: {e}")
                return False

    def sync_from_inbox(self, force: bool = False) -> bool:
        """Sync inbox messages to shared_state"""
        with self.lock:
            try:
                synced_count = 0

                # Get all agents
                for agent_id in self.shared_state_manager.state.agents.keys():
                    inbox_data = self.inbox_manager.get_inbox(agent_id)

                    for inbox_msg in inbox_data['messages']:
                        # Check if already exists in shared_state
                        existing = any(
                            msg.message_id == inbox_msg.message_id
                            for msg in self.shared_state_manager.state.messages
                        )

                        if not existing or force:
                            # Convert to shared_state format
                            legacy_message = InterAgentMessage(
                                message_id=inbox_msg.message_id,
                                from_agent=inbox_msg.sender_id,
                                to_agent=inbox_msg.recipient_id,
                                message=inbox_msg.content,
                                timestamp=inbox_msg.timestamp,
                                read=(inbox_msg.status == MessageStatus.READ)
                            )

                            self.shared_state_manager.state.messages.append(legacy_message)
                            synced_count += 1

                # Save shared_state
                self.shared_state_manager.save_state()
                print(f"✅ Synced {synced_count} messages from inbox to shared_state")
                return True

            except Exception as e:
                print(f"❌ Error syncing from inbox: {e}")
                return False

    def perform_full_sync(self) -> Dict[str, Any]:
        """Perform bidirectional sync between systems"""
        with self.lock:
            results = {
                'to_inbox': False,
                'from_inbox': False,
                'errors': []
            }

            try:
                # Sync to inbox
                results['to_inbox'] = self.sync_to_inbox()

                # Sync from inbox
                results['from_inbox'] = self.sync_from_inbox()

                return results

            except Exception as e:
                results['errors'].append(str(e))
                return results


class InboxStorageFix:
    """Fixes and optimizations for inbox storage integration"""

    @staticmethod
    def create_integrated_manager(shared_state_manager) -> tuple:
        """Create fully integrated inbox system"""
        try:
            # Initialize inbox components
            inbox_storage = InboxStorage("shared_inbox.db")
            inbox_manager = InboxManager(inbox_storage)
            message_router = MessageRouter()

            # Create adapter
            adapter = InboxSharedStateAdapter(shared_state_manager, inbox_manager)

            # Perform initial sync
            sync_results = adapter.perform_full_sync()
            print(f"🔄 Initial sync completed: {sync_results}")

            return inbox_manager, adapter, message_router

        except Exception as e:
            print(f"❌ Error creating integrated manager: {e}")
            raise

    @staticmethod
    def test_storage_connectivity() -> Dict[str, Any]:
        """Test storage layer connectivity and functionality"""
        results = {
            'sqlite_connection': False,
            'table_creation': False,
            'message_storage': False,
            'message_retrieval': False,
            'errors': []
        }

        try:
            # Test SQLite connection with actual file (not in-memory)
            storage = InboxStorage("integration_test.db")
            results['sqlite_connection'] = True
            results['table_creation'] = True  # Tables are created in __init__

            # Test message storage
            test_message = SharedAgentMessage(
                sender_id="test_sender",
                recipient_id="test_recipient",
                content="Test message for connectivity"
            )

            if storage.store_message(test_message):
                results['message_storage'] = True

                # Test message retrieval
                messages = storage.get_messages_for_agent("test_recipient")
                if len(messages) > 0 and messages[0].content == "Test message for connectivity":
                    results['message_retrieval'] = True

        except Exception as e:
            results['errors'].append(f"Storage test error: {str(e)}")

        return results

    @staticmethod
    def diagnose_integration_issues(shared_state_manager) -> Dict[str, Any]:
        """Diagnose integration issues between systems"""
        diagnosis = {
            'shared_state_accessible': False,
            'shared_state_agents_count': 0,
            'shared_state_messages_count': 0,
            'inbox_storage_working': False,
            'integration_possible': False,
            'recommendations': [],
            'errors': []
        }

        try:
            # Check shared_state accessibility
            if hasattr(shared_state_manager, 'state'):
                diagnosis['shared_state_accessible'] = True
                diagnosis['shared_state_agents_count'] = len(shared_state_manager.state.agents)
                diagnosis['shared_state_messages_count'] = len(shared_state_manager.state.messages)

            # Test inbox storage
            storage_test = InboxStorageFix.test_storage_connectivity()
            diagnosis['inbox_storage_working'] = all([
                storage_test['sqlite_connection'],
                storage_test['message_storage'],
                storage_test['message_retrieval']
            ])

            # Check integration possibility
            diagnosis['integration_possible'] = (
                diagnosis['shared_state_accessible'] and
                diagnosis['inbox_storage_working']
            )

            # Generate recommendations
            if not diagnosis['shared_state_accessible']:
                diagnosis['recommendations'].append("Fix shared_state manager initialization")

            if not diagnosis['inbox_storage_working']:
                diagnosis['recommendations'].append("Debug inbox storage SQLite connectivity")

            if diagnosis['integration_possible']:
                diagnosis['recommendations'].append("Proceed with inbox integration using adapter pattern")
            else:
                diagnosis['recommendations'].append("Fix underlying issues before integration")

        except Exception as e:
            diagnosis['errors'].append(f"Diagnosis error: {str(e)}")

        return diagnosis


def fix_inbox_integration(shared_state_manager):
    """Main function to fix inbox integration issues"""
    print("🔧 Starting inbox integration fix...")

    # Step 1: Diagnose issues
    diagnosis = InboxStorageFix.diagnose_integration_issues(shared_state_manager)
    print(f"📊 Diagnosis results: {diagnosis}")

    if not diagnosis['integration_possible']:
        print("❌ Integration not possible due to underlying issues")
        return None, diagnosis

    # Step 2: Create integrated system
    try:
        inbox_manager, adapter, router = InboxStorageFix.create_integrated_manager(shared_state_manager)
        print("✅ Integrated inbox system created successfully")

        # Step 3: Test functionality
        test_message_id = adapter.send_message_via_inbox(
            sender_id="system",
            recipient_id="test",
            content="Integration test message",
            subject="Test"
        )

        if test_message_id:
            print(f"✅ Test message sent successfully: {test_message_id}")
        else:
            print("❌ Test message failed")

        return {
            'inbox_manager': inbox_manager,
            'adapter': adapter,
            'router': router,
            'status': 'success'
        }, diagnosis

    except Exception as e:
        print(f"❌ Integration fix failed: {e}")
        return None, diagnosis