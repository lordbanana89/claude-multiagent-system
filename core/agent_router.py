"""
Advanced Agent Message Routing and Coordination
"""

import json
import time
import uuid
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
import logging
from collections import defaultdict
import threading

from core.message_bus import get_message_bus
from core.persistence import get_persistence_manager

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of inter-agent messages"""
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    QUERY = "query"
    NOTIFICATION = "notification"
    COORDINATION = "coordination"
    DELEGATION = "delegation"
    ESCALATION = "escalation"


class Priority(Enum):
    """Message priority levels"""
    CRITICAL = 5
    HIGH = 4
    NORMAL = 3
    LOW = 2
    BACKGROUND = 1


@dataclass
class AgentMessage:
    """Inter-agent message"""
    id: str
    type: MessageType
    source: str
    target: str
    content: Dict[str, Any]
    priority: Priority
    timestamp: float
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    ttl: int = 300  # Time to live in seconds
    requires_ack: bool = False
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'type': self.type.value,
            'source': self.source,
            'target': self.target,
            'content': self.content,
            'priority': self.priority.value,
            'timestamp': self.timestamp,
            'correlation_id': self.correlation_id,
            'reply_to': self.reply_to,
            'ttl': self.ttl,
            'requires_ack': self.requires_ack,
            'metadata': self.metadata or {}
        }


class AgentCapability:
    """Defines what an agent can do"""
    def __init__(self, name: str, description: str,
                 input_schema: Dict = None, output_schema: Dict = None):
        self.name = name
        self.description = description
        self.input_schema = input_schema or {}
        self.output_schema = output_schema or {}
        self.performance_metrics = {
            'success_rate': 1.0,
            'avg_response_time': 0.0,
            'total_executions': 0
        }


class AgentProfile:
    """Agent profile with capabilities and routing info"""
    def __init__(self, agent_id: str, role: str):
        self.agent_id = agent_id
        self.role = role
        self.capabilities: Dict[str, AgentCapability] = {}
        self.dependencies: Set[str] = set()
        self.status = "unknown"
        self.last_heartbeat = 0
        self.message_queue: List[AgentMessage] = []
        self.routing_rules: Dict[str, Any] = {}
        self.load_score = 0.0
        self.success_rate = 1.0


class AgentRouter:
    """
    Advanced routing and coordination between agents
    """

    def __init__(self):
        self.message_bus = get_message_bus()
        self.persistence = get_persistence_manager()
        self.agents: Dict[str, AgentProfile] = {}
        self.routing_table: Dict[str, List[str]] = defaultdict(list)
        self.message_buffer: Dict[str, List[AgentMessage]] = defaultdict(list)
        self.pending_acks: Dict[str, AgentMessage] = {}
        self.conversation_history: Dict[str, List[AgentMessage]] = defaultdict(list)
        self._lock = threading.Lock()
        self._ack_timeout_thread = None
        self._running = False

        self._initialize_agent_profiles()
        logger.info("AgentRouter initialized")

    def _initialize_agent_profiles(self):
        """Initialize known agent profiles"""
        # Supervisor
        supervisor = AgentProfile("supervisor", "orchestrator")
        supervisor.capabilities["delegate_task"] = AgentCapability(
            "delegate_task",
            "Delegate tasks to other agents",
            {"task": "string", "agent": "string"},
            {"task_id": "string", "status": "string"}
        )
        supervisor.capabilities["coordinate_workflow"] = AgentCapability(
            "coordinate_workflow",
            "Coordinate multi-agent workflows",
            {"workflow": "object"},
            {"execution_id": "string"}
        )
        self.agents["supervisor"] = supervisor

        # Backend API
        backend = AgentProfile("backend-api", "executor")
        backend.capabilities["process_request"] = AgentCapability(
            "process_request",
            "Process API requests",
            {"method": "string", "endpoint": "string", "data": "object"},
            {"response": "object", "status_code": "integer"}
        )
        backend.capabilities["data_validation"] = AgentCapability(
            "data_validation",
            "Validate data structures",
            {"data": "object", "schema": "object"},
            {"valid": "boolean", "errors": "array"}
        )
        self.agents["backend-api"] = backend

        # Database
        database = AgentProfile("database", "storage")
        database.capabilities["query"] = AgentCapability(
            "query",
            "Execute database queries",
            {"query": "string", "params": "object"},
            {"result": "array", "affected_rows": "integer"}
        )
        database.capabilities["schema_migration"] = AgentCapability(
            "schema_migration",
            "Manage database schema",
            {"migration": "object"},
            {"success": "boolean", "version": "string"}
        )
        self.agents["database"] = database

        # Frontend UI
        frontend = AgentProfile("frontend-ui", "interface")
        frontend.capabilities["render_component"] = AgentCapability(
            "render_component",
            "Render UI components",
            {"component": "string", "props": "object"},
            {"html": "string", "css": "string"}
        )
        self.agents["frontend-ui"] = frontend

        # Testing
        testing = AgentProfile("testing", "validator")
        testing.capabilities["run_tests"] = AgentCapability(
            "run_tests",
            "Execute test suites",
            {"suite": "string", "filter": "string"},
            {"passed": "integer", "failed": "integer", "report": "object"}
        )
        testing.capabilities["performance_test"] = AgentCapability(
            "performance_test",
            "Run performance tests",
            {"target": "string", "load": "integer"},
            {"metrics": "object"}
        )
        self.agents["testing"] = testing

        # Build routing table based on capabilities
        self._build_routing_table()

    def _build_routing_table(self):
        """Build routing table from agent capabilities"""
        for agent_id, profile in self.agents.items():
            for capability_name in profile.capabilities:
                self.routing_table[capability_name].append(agent_id)

        logger.info(f"Built routing table with {len(self.routing_table)} capabilities")

    def start(self):
        """Start the router"""
        self._running = True

        # Start ACK timeout monitor
        self._ack_timeout_thread = threading.Thread(target=self._monitor_acks)
        self._ack_timeout_thread.daemon = True
        self._ack_timeout_thread.start()

        # Subscribe to agent messages
        self.message_bus.subscribe("bus:agent:*", self._handle_agent_message)

        logger.info("AgentRouter started")

    def stop(self):
        """Stop the router"""
        self._running = False
        if self._ack_timeout_thread:
            self._ack_timeout_thread.join(timeout=2)
        logger.info("AgentRouter stopped")

    def send_message(self, message: AgentMessage) -> str:
        """Send message to target agent"""
        with self._lock:
            # Validate target
            if message.target not in self.agents and message.target != "broadcast":
                raise ValueError(f"Unknown target agent: {message.target}")

            # Add to conversation history
            if message.correlation_id:
                self.conversation_history[message.correlation_id].append(message)

            # Route based on type
            if message.type == MessageType.BROADCAST:
                self._broadcast_message(message)
            elif message.type == MessageType.QUERY:
                return self._route_query(message)
            else:
                self._route_direct_message(message)

            # Track if ACK required
            if message.requires_ack:
                self.pending_acks[message.id] = message

            # Persist important messages
            if message.priority.value >= Priority.HIGH.value:
                self._persist_message(message)

            return message.id

    def _route_direct_message(self, message: AgentMessage):
        """Route direct message to specific agent"""
        target_profile = self.agents.get(message.target)

        if not target_profile:
            logger.error(f"Target agent {message.target} not found")
            return

        # Check agent status
        if target_profile.status != "ready":
            # Buffer message if agent not ready
            self.message_buffer[message.target].append(message)
            logger.info(f"Buffered message for {message.target} (status: {target_profile.status})")
            return

        # Check load and potentially redirect
        if target_profile.load_score > 0.8:
            alternative = self._find_alternative_agent(message)
            if alternative:
                logger.info(f"Redirecting message from {message.target} to {alternative} due to load")
                message.target = alternative
                target_profile = self.agents[alternative]

        # Send via message bus
        self.message_bus.publish_task(
            agent=message.target,
            task={
                'type': 'agent_message',
                'message': message.to_dict()
            },
            priority=self._map_priority(message.priority)
        )

        # Update metrics
        target_profile.load_score += 0.1

    def _broadcast_message(self, message: AgentMessage):
        """Broadcast message to all agents"""
        for agent_id in self.agents:
            if agent_id != message.source:
                broadcast_copy = AgentMessage(
                    id=f"{message.id}_{agent_id}",
                    type=message.type,
                    source=message.source,
                    target=agent_id,
                    content=message.content,
                    priority=message.priority,
                    timestamp=message.timestamp,
                    correlation_id=message.correlation_id,
                    metadata=message.metadata
                )
                self._route_direct_message(broadcast_copy)

    def _route_query(self, message: AgentMessage) -> Optional[str]:
        """Route query to best available agent"""
        capability_needed = message.content.get('capability')

        if not capability_needed:
            logger.error("Query missing required capability field")
            return None

        # Find agents with capability
        capable_agents = self.routing_table.get(capability_needed, [])

        if not capable_agents:
            logger.error(f"No agents found with capability: {capability_needed}")
            return None

        # Select best agent based on load and success rate
        best_agent = self._select_best_agent(capable_agents)

        if best_agent:
            message.target = best_agent
            self._route_direct_message(message)
            return best_agent

        return None

    def _select_best_agent(self, agent_ids: List[str]) -> Optional[str]:
        """Select best agent based on metrics"""
        best_score = -1
        best_agent = None

        for agent_id in agent_ids:
            profile = self.agents.get(agent_id)
            if not profile or profile.status != "ready":
                continue

            # Calculate score (higher is better)
            score = (profile.success_rate * 0.7) + ((1 - profile.load_score) * 0.3)

            if score > best_score:
                best_score = score
                best_agent = agent_id

        return best_agent

    def _find_alternative_agent(self, message: AgentMessage) -> Optional[str]:
        """Find alternative agent for load balancing"""
        # Check if message requires specific capability
        required_capability = message.metadata.get('required_capability') if message.metadata else None

        if required_capability:
            alternatives = [a for a in self.routing_table.get(required_capability, [])
                          if a != message.target]
            if alternatives:
                return self._select_best_agent(alternatives)

        return None

    def _handle_agent_message(self, message: Dict):
        """Handle incoming agent message"""
        if message.get('type') == 'agent_response':
            self._process_response(message)
        elif message.get('type') == 'agent_ack':
            self._process_ack(message)
        elif message.get('type') == 'agent_status':
            self._update_agent_status(message)

    def _process_response(self, response: Dict):
        """Process agent response"""
        correlation_id = response.get('correlation_id')

        if correlation_id:
            # Find original message
            original = None
            for msg in self.conversation_history.get(correlation_id, []):
                if msg.id == response.get('reply_to'):
                    original = msg
                    break

            if original and original.source in self.agents:
                # Route response back to requester
                response_msg = AgentMessage(
                    id=str(uuid.uuid4()),
                    type=MessageType.RESPONSE,
                    source=response.get('source'),
                    target=original.source,
                    content=response.get('content', {}),
                    priority=Priority.NORMAL,
                    timestamp=time.time(),
                    correlation_id=correlation_id,
                    reply_to=original.id
                )
                self._route_direct_message(response_msg)

    def _process_ack(self, ack: Dict):
        """Process acknowledgment"""
        msg_id = ack.get('message_id')

        with self._lock:
            if msg_id in self.pending_acks:
                del self.pending_acks[msg_id]
                logger.debug(f"Received ACK for message {msg_id}")

    def _update_agent_status(self, status_msg: Dict):
        """Update agent status"""
        agent_id = status_msg.get('agent_id')

        if agent_id in self.agents:
            profile = self.agents[agent_id]
            profile.status = status_msg.get('status', 'unknown')
            profile.last_heartbeat = time.time()
            profile.load_score = status_msg.get('load_score', profile.load_score)

            # Process buffered messages if agent is ready
            if profile.status == "ready" and agent_id in self.message_buffer:
                buffered = self.message_buffer[agent_id]
                self.message_buffer[agent_id] = []

                for msg in buffered:
                    if time.time() - msg.timestamp < msg.ttl:
                        self._route_direct_message(msg)

    def _monitor_acks(self):
        """Monitor for ACK timeouts"""
        while self._running:
            with self._lock:
                expired = []
                for msg_id, message in self.pending_acks.items():
                    if time.time() - message.timestamp > 30:  # 30 second timeout
                        expired.append(msg_id)
                        logger.warning(f"ACK timeout for message {msg_id} to {message.target}")

                        # Mark agent as potentially unhealthy
                        if message.target in self.agents:
                            self.agents[message.target].success_rate *= 0.95

                for msg_id in expired:
                    del self.pending_acks[msg_id]

            time.sleep(5)

    def _persist_message(self, message: AgentMessage):
        """Persist important messages"""
        self.persistence.log_event(
            event_type="agent_message",
            source=message.source,
            data=message.to_dict()
        )

    def _map_priority(self, priority: Priority):
        """Map router priority to message bus priority"""
        from core.message_bus import MessagePriority
        mapping = {
            Priority.CRITICAL: MessagePriority.CRITICAL,
            Priority.HIGH: MessagePriority.HIGH,
            Priority.NORMAL: MessagePriority.NORMAL,
            Priority.LOW: MessagePriority.NORMAL,
            Priority.BACKGROUND: MessagePriority.NORMAL
        }
        return mapping.get(priority, MessagePriority.NORMAL)

    def get_agent_capabilities(self, agent_id: str) -> Dict[str, AgentCapability]:
        """Get capabilities of an agent"""
        profile = self.agents.get(agent_id)
        return profile.capabilities if profile else {}

    def discover_capability(self, capability_name: str) -> List[str]:
        """Discover which agents have a capability"""
        return self.routing_table.get(capability_name, [])

    def get_conversation(self, correlation_id: str) -> List[AgentMessage]:
        """Get conversation history"""
        return self.conversation_history.get(correlation_id, [])

    def get_agent_metrics(self, agent_id: str) -> Dict:
        """Get agent performance metrics"""
        profile = self.agents.get(agent_id)
        if not profile:
            return {}

        return {
            'agent_id': agent_id,
            'status': profile.status,
            'load_score': profile.load_score,
            'success_rate': profile.success_rate,
            'last_heartbeat': profile.last_heartbeat,
            'capabilities': list(profile.capabilities.keys()),
            'buffered_messages': len(self.message_buffer.get(agent_id, []))
        }

    def delegate_task(self, task: Dict, from_agent: str) -> str:
        """Delegate task to appropriate agent"""
        # Determine required capability
        task_type = task.get('type', 'generic')

        # Map task type to capability
        capability_map = {
            'api_request': 'process_request',
            'database_query': 'query',
            'ui_render': 'render_component',
            'test_execution': 'run_tests',
            'coordination': 'coordinate_workflow'
        }

        required_capability = capability_map.get(task_type)

        if not required_capability:
            logger.error(f"Unknown task type: {task_type}")
            return None

        # Create delegation message
        message = AgentMessage(
            id=str(uuid.uuid4()),
            type=MessageType.DELEGATION,
            source=from_agent,
            target="",  # Will be determined by routing
            content=task,
            priority=Priority.HIGH if task.get('urgent') else Priority.NORMAL,
            timestamp=time.time(),
            requires_ack=True,
            metadata={'required_capability': required_capability}
        )

        # Route to best agent
        target = self._route_query(message)

        if target:
            logger.info(f"Delegated task from {from_agent} to {target}")
            return message.id

        return None


# Singleton instance
_agent_router = None

def get_agent_router() -> AgentRouter:
    """Get or create agent router instance"""
    global _agent_router
    if _agent_router is None:
        _agent_router = AgentRouter()
    return _agent_router