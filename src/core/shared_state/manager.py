"""
SharedStateManager - Gestore centrale dello stato condiviso
"""

import threading
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime
import uuid

from .models import (
    SharedState, AgentState, TaskInfo, InterAgentMessage,
    AgentStatus, TaskPriority
)
from .persistence import PersistenceManager
from .messaging import MessagingSystem


class SharedStateManager:
    """Manager centrale per stato condiviso multi-agente"""

    def __init__(self,
                 persistence_type: str = "json",
                 persistence_file: str = "shared_state.json"):

        # Initialize state and persistence
        self.persistence_manager = PersistenceManager(
            persistence_type=persistence_type,
            file_path=persistence_file
        )

        # Load existing state or create new
        self.state = self.persistence_manager.load()
        if self.state is None:
            self.state = SharedState()

        # Thread safety
        self.lock = threading.RLock()

        # Observer pattern per notifiche real-time
        self.observers: List[Callable] = []

        # Initialize advanced messaging system
        self.messaging_system = MessagingSystem()

        # Initialize notification system from enhanced messaging
        try:
            from messaging.notifications import get_notification_system
            self.notification_system = get_notification_system()
            print("🔔 Enhanced notification system integrated")
        except ImportError:
            self.notification_system = None
            print("⚠️ Enhanced notification system not available")

        # Register all existing agents with messaging system
        for agent_id in self.state.agents.keys():
            self.messaging_system.register_agent(agent_id)
            # Also register with notification system if available
            if self.notification_system:
                self.notification_system.register_agent(agent_id)

        # Load messaging data from persistence if available
        if hasattr(self.state, 'messaging_data'):
            try:
                self.messaging_system.from_dict(self.state.messaging_data)
            except Exception as e:
                print(f"Warning: Could not load messaging data: {e}")

        print(f"SharedStateManager initialized with {len(self.state.agents)} agents")

    # Observer Pattern
    def register_observer(self, callback: Callable[[str, Any], None]):
        """Registra callback per notifiche cambiamenti stato"""
        with self.lock:
            self.observers.append(callback)

    def unregister_observer(self, callback: Callable):
        """Rimuovi callback observer"""
        with self.lock:
            if callback in self.observers:
                self.observers.remove(callback)

    def notify_observers(self, event_type: str, data: Any):
        """Notifica tutti gli observers di un cambiamento"""
        for observer in self.observers:
            try:
                observer(event_type, data)
            except Exception as e:
                print(f"Observer notification error: {e}")

    # Persistence Operations
    def save_state(self) -> bool:
        """Salva stato corrente su persistenza"""
        try:
            self.state.last_updated = datetime.now()

            # Include messaging data in state
            if hasattr(self, 'messaging_system'):
                self.state.messaging_data = self.messaging_system.to_dict()

            success = self.persistence_manager.save(self.state)
            if success:
                self.notify_observers("state_saved", {"timestamp": self.state.last_updated})
            return success
        except Exception as e:
            print(f"Error saving state: {e}")
            return False

    # Agent Management
    def register_agent(self, agent_state: AgentState) -> bool:
        """Registra nuovo agente nel sistema"""
        with self.lock:
            try:
                self.state.agents[agent_state.agent_id] = agent_state
                # Register with messaging system
                self.messaging_system.register_agent(agent_state.agent_id)
                # Register with notification system if available
                if self.notification_system:
                    self.notification_system.register_agent(agent_state.agent_id)
                self.save_state()
                self.notify_observers("agent_registered", agent_state)
                return True
            except Exception as e:
                print(f"Error registering agent {agent_state.agent_id}: {e}")
                return False

    def update_agent_status(self, agent_id: str, status: AgentStatus,
                          current_task: str = None, error_message: str = None) -> bool:
        """Aggiorna status di un agente"""
        with self.lock:
            if agent_id not in self.state.agents:
                return False

            try:
                agent = self.state.agents[agent_id]
                old_status = agent.status

                agent.status = status
                agent.last_activity = datetime.now()

                if current_task is not None:
                    agent.current_task = current_task

                if error_message is not None:
                    agent.error_message = error_message

                self.save_state()
                self.notify_observers("agent_status_changed", {
                    "agent_id": agent_id,
                    "old_status": old_status.value,
                    "new_status": status.value,
                    "current_task": current_task
                })
                return True

            except Exception as e:
                print(f"Error updating agent {agent_id} status: {e}")
                return False

    def get_agent(self, agent_id: str) -> Optional[AgentState]:
        """Ottieni stato di un agente"""
        with self.lock:
            return self.state.agents.get(agent_id)

    def get_all_agents(self) -> Dict[str, AgentState]:
        """Ottieni tutti gli agenti"""
        with self.lock:
            return self.state.agents.copy()

    def get_available_agents(self) -> List[AgentState]:
        """Ottieni agenti disponibili per nuovi task"""
        with self.lock:
            return [
                agent for agent in self.state.agents.values()
                if agent.status == AgentStatus.IDLE
            ]

    # Task Management
    def create_task(self, description: str,
                   priority: TaskPriority = TaskPriority.MEDIUM,
                   task_id: str = None) -> TaskInfo:
        """Crea nuovo task"""
        if task_id is None:
            task_id = f"task_{uuid.uuid4().hex[:8]}"

        return TaskInfo(
            task_id=task_id,
            description=description,
            priority=priority,
            created_at=datetime.now()
        )

    def add_task(self, task: TaskInfo) -> bool:
        """Aggiunge task alla coda"""
        with self.lock:
            try:
                # Aggiungi alla coda ordinando per priorità
                self.state.task_queue.append(task)
                self.state.task_queue.sort(key=lambda t: t.priority.value, reverse=True)

                self.save_state()
                self.notify_observers("task_added", task)
                return True

            except Exception as e:
                print(f"Error adding task {task.task_id}: {e}")
                return False

    def assign_task(self, task_id: str, agent_ids: List[str]) -> bool:
        """Assegna task agli agenti specificati"""
        with self.lock:
            # Trova task nella coda
            task = None
            for i, t in enumerate(self.state.task_queue):
                if t.task_id == task_id:
                    task = self.state.task_queue.pop(i)
                    break

            if task is None:
                return False

            try:
                # Assegna task
                task.assigned_agents = agent_ids
                task.status = "in_progress"
                task.started_at = datetime.now()
                self.state.current_task = task

                # Aggiorna status degli agenti
                for agent_id in agent_ids:
                    if agent_id in self.state.agents:
                        self.state.agents[agent_id].status = AgentStatus.BUSY
                        self.state.agents[agent_id].current_task = task_id

                # Aggiorna status sistema
                self.state.system_status = "busy"

                self.save_state()
                self.notify_observers("task_assigned", {
                    "task": task,
                    "agents": agent_ids
                })
                return True

            except Exception as e:
                print(f"Error assigning task {task_id}: {e}")
                # Rimetti task in coda se errore
                self.state.task_queue.append(task)
                return False

    def complete_task(self, task_id: str, results: Dict[str, Any] = None,
                     error_message: str = None) -> bool:
        """Completa un task"""
        with self.lock:
            try:
                task = self.state.current_task
                if not task or task.task_id != task_id:
                    # Cerca nei task history
                    task = self.state.get_task_by_id(task_id)
                    if not task:
                        return False

                # Aggiorna task
                task.completed_at = datetime.now()
                task.progress = 100.0

                if error_message:
                    task.status = "failed"
                    task.error_message = error_message
                else:
                    task.status = "completed"
                    if results:
                        task.results.update(results)

                # Sposta in history
                self.state.task_history.append(task)
                if self.state.current_task and self.state.current_task.task_id == task_id:
                    self.state.current_task = None

                # Libera agenti
                for agent_id in task.assigned_agents:
                    if agent_id in self.state.agents:
                        self.state.agents[agent_id].status = AgentStatus.IDLE
                        self.state.agents[agent_id].current_task = None

                # Aggiorna status sistema
                if not self.state.task_queue and not self.state.current_task:
                    self.state.system_status = "idle"

                # Mantieni solo ultimi 50 task in history
                if len(self.state.task_history) > 50:
                    self.state.task_history = self.state.task_history[-50:]

                self.save_state()
                self.notify_observers("task_completed", {
                    "task": task,
                    "success": error_message is None
                })
                return True

            except Exception as e:
                print(f"Error completing task {task_id}: {e}")
                return False

    def get_current_task(self) -> Optional[TaskInfo]:
        """Ottieni task corrente"""
        with self.lock:
            return self.state.current_task

    def get_task_queue(self) -> List[TaskInfo]:
        """Ottieni coda task"""
        with self.lock:
            return self.state.task_queue.copy()

    def get_task_history(self, limit: int = 10) -> List[TaskInfo]:
        """Ottieni cronologia task"""
        with self.lock:
            return self.state.task_history[-limit:] if limit > 0 else self.state.task_history

    # Advanced Inter-Agent Communication System
    def send_agent_message(self, sender_id: str, recipient_id: str, content: str,
                          subject: Optional[str] = None, priority: str = "NORMAL") -> Optional[str]:
        """Send advanced message between agents"""
        with self.lock:
            try:
                from .messaging import MessagePriority
                priority_enum = MessagePriority.NORMAL
                if priority.upper() == "HIGH":
                    priority_enum = MessagePriority.HIGH
                elif priority.upper() == "URGENT":
                    priority_enum = MessagePriority.URGENT
                elif priority.upper() == "LOW":
                    priority_enum = MessagePriority.LOW

                message = self.messaging_system.send_message(
                    sender_id=sender_id,
                    recipient_id=recipient_id,
                    content=content,
                    subject=subject,
                    priority=priority_enum
                )

                # Send notification through enhanced system if available
                if self.notification_system:
                    try:
                        self.notification_system.send_notification(recipient_id, message)
                    except Exception as e:
                        print(f"Warning: Could not send notification: {e}")

                # Update persistence
                self.save_state()
                self.notify_observers("advanced_message_sent", {
                    "sender": sender_id,
                    "recipient": recipient_id,
                    "message_id": message.message_id
                })

                return message.message_id

            except Exception as e:
                print(f"Error sending advanced message: {e}")
                return None

    def broadcast_agent_message(self, sender_id: str, content: str,
                               subject: Optional[str] = None, priority: str = "NORMAL",
                               exclude_agents: Optional[List[str]] = None) -> List[str]:
        """Send broadcast message to all agents"""
        with self.lock:
            try:
                from .messaging import MessagePriority
                priority_enum = MessagePriority.NORMAL
                if priority.upper() == "HIGH":
                    priority_enum = MessagePriority.HIGH
                elif priority.upper() == "URGENT":
                    priority_enum = MessagePriority.URGENT
                elif priority.upper() == "LOW":
                    priority_enum = MessagePriority.LOW

                messages = self.messaging_system.broadcast_message(
                    sender_id=sender_id,
                    content=content,
                    subject=subject,
                    priority=priority_enum,
                    exclude_agents=exclude_agents
                )

                # Send notifications through enhanced system if available
                if self.notification_system:
                    for message in messages:
                        try:
                            self.notification_system.send_notification(message.recipient_id, message)
                        except Exception as e:
                            print(f"Warning: Could not send notification to {message.recipient_id}: {e}")

                # Update persistence
                self.save_state()
                self.notify_observers("broadcast_sent", {
                    "sender": sender_id,
                    "message_count": len(messages)
                })

                return [msg.message_id for msg in messages]

            except Exception as e:
                print(f"Error broadcasting message: {e}")
                return []

    def get_agent_inbox(self, agent_id: str):
        """Get agent's inbox with advanced messaging features"""
        with self.lock:
            return self.messaging_system.get_inbox(agent_id)

    def mark_agent_message_read(self, agent_id: str, message_id: str) -> bool:
        """Mark message as read in advanced system"""
        with self.lock:
            result = self.messaging_system.mark_message_read(agent_id, message_id)
            if result:
                self.save_state()
                self.notify_observers("message_read", {
                    "agent_id": agent_id,
                    "message_id": message_id
                })
            return result

    def get_conversation(self, agent1_id: str, agent2_id: str):
        """Get conversation between two agents"""
        with self.lock:
            return self.messaging_system.get_conversation(agent1_id, agent2_id)

    def get_messaging_stats(self) -> Dict[str, Any]:
        """Get messaging system statistics"""
        with self.lock:
            return self.messaging_system.get_system_stats()

    # Legacy messaging methods (kept for backward compatibility)
    def send_message(self, from_agent: str, to_agent: str,
                    message: str, data: Dict[str, Any] = None) -> bool:
        """Legacy message method - redirects to advanced system"""
        message_id = self.send_agent_message(from_agent, to_agent, message)
        return message_id is not None

    def get_messages_for_agent(self, agent_id: str, unread_only: bool = False):
        """Legacy method - get messages for agent"""
        inbox = self.get_agent_inbox(agent_id)
        if unread_only:
            return inbox.get_unread_messages()
        return inbox.get_recent_messages()

    def mark_message_read(self, message_id: str) -> bool:
        """Legacy method - mark message as read"""
        # Try to find which agent this message belongs to
        for agent_id in self.state.agents.keys():
            inbox = self.get_agent_inbox(agent_id)
            for msg in inbox.messages:
                if msg.message_id == message_id or msg.message_id.startswith(message_id):
                    return self.mark_agent_message_read(agent_id, msg.message_id)
        return False

    # Shared Variables
    def set_shared_var(self, key: str, value: Any) -> bool:
        """Imposta variabile condivisa"""
        with self.lock:
            try:
                old_value = self.state.shared_variables.get(key)
                self.state.shared_variables[key] = value
                self.save_state()
                self.notify_observers("shared_var_updated", {
                    "key": key,
                    "old_value": old_value,
                    "new_value": value
                })
                return True
            except Exception as e:
                print(f"Error setting shared variable {key}: {e}")
                return False

    def get_shared_var(self, key: str, default: Any = None) -> Any:
        """Ottieni variabile condivisa"""
        with self.lock:
            return self.state.shared_variables.get(key, default)

    def delete_shared_var(self, key: str) -> bool:
        """Elimina variabile condivisa"""
        with self.lock:
            if key in self.state.shared_variables:
                old_value = self.state.shared_variables.pop(key)
                self.save_state()
                self.notify_observers("shared_var_deleted", {
                    "key": key,
                    "old_value": old_value
                })
                return True
            return False

    # System Status and Stats
    def get_system_stats(self) -> Dict[str, Any]:
        """Ottieni statistiche sistema"""
        with self.lock:
            active_agents = len([
                a for a in self.state.agents.values()
                if a.status != AgentStatus.IDLE
            ])

            completed_tasks = len([
                t for t in self.state.task_history
                if t.status == "completed"
            ])

            failed_tasks = len([
                t for t in self.state.task_history
                if t.status == "failed"
            ])

            return {
                "total_agents": len(self.state.agents),
                "active_agents": active_agents,
                "tasks_in_queue": len(self.state.task_queue),
                "current_task": self.state.current_task.task_id if self.state.current_task else None,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "total_messages": len(self.state.messages),
                "shared_variables": len(self.state.shared_variables),
                "system_status": self.state.system_status,
                "last_updated": self.state.last_updated
            }

    def get_state_snapshot(self) -> SharedState:
        """Ottieni snapshot completo dello stato"""
        with self.lock:
            return self.state