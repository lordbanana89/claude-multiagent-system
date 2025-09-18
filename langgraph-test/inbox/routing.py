"""
Message Routing and Distribution System
Handles intelligent message routing, filtering, and distribution logic
"""

from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import fnmatch
from abc import ABC, abstractmethod

from shared_state.models import AgentMessage, MessageType, MessagePriority, MessageStatus


class RoutingStrategy(Enum):
    """Message routing strategies"""
    DIRECT = "direct"           # Direct one-to-one routing
    BROADCAST = "broadcast"     # Send to all agents
    FILTERED = "filtered"       # Send based on filters
    PRIORITY = "priority"       # Route based on priority
    ROUND_ROBIN = "round_robin" # Distribute evenly
    LOAD_BASED = "load_based"   # Route based on agent load


class FilterType(Enum):
    """Types of routing filters"""
    AGENT_ID = "agent_id"
    CAPABILITIES = "capabilities"
    CONTENT_PATTERN = "content_pattern"
    SUBJECT_PATTERN = "subject_pattern"
    MESSAGE_TYPE = "message_type"
    PRIORITY = "priority"
    SENDER_ID = "sender_id"
    CUSTOM = "custom"


@dataclass
class RoutingRule:
    """Rule for message routing"""
    rule_id: str
    name: str
    strategy: RoutingStrategy
    filter_type: FilterType
    filter_value: Any
    target_agents: Optional[List[str]] = None
    priority: int = 0  # Higher priority rules executed first
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    description: Optional[str] = None

    def matches(self, message: AgentMessage, agent_info: Dict[str, Any] = None) -> bool:
        """Check if message matches this routing rule"""
        if not self.active:
            return False

        if self.filter_type == FilterType.AGENT_ID:
            return message.recipient_id in (self.filter_value if isinstance(self.filter_value, list) else [self.filter_value])

        elif self.filter_type == FilterType.SENDER_ID:
            return message.sender_id in (self.filter_value if isinstance(self.filter_value, list) else [self.filter_value])

        elif self.filter_type == FilterType.MESSAGE_TYPE:
            return message.message_type == self.filter_value

        elif self.filter_type == FilterType.PRIORITY:
            if isinstance(self.filter_value, dict):
                min_priority = self.filter_value.get('min', 1)
                max_priority = self.filter_value.get('max', 4)
                return min_priority <= message.priority.value <= max_priority
            else:
                return message.priority == self.filter_value

        elif self.filter_type == FilterType.CONTENT_PATTERN:
            return bool(re.search(self.filter_value, message.content, re.IGNORECASE))

        elif self.filter_type == FilterType.SUBJECT_PATTERN:
            if message.subject:
                return bool(re.search(self.filter_value, message.subject, re.IGNORECASE))
            return False

        elif self.filter_type == FilterType.CAPABILITIES:
            if agent_info and 'capabilities' in agent_info:
                required_caps = self.filter_value if isinstance(self.filter_value, list) else [self.filter_value]
                agent_caps = agent_info['capabilities']
                return any(cap in agent_caps for cap in required_caps)
            return False

        return False


class RouterFilter(ABC):
    """Abstract base class for routing filters"""

    @abstractmethod
    def apply(self, message: AgentMessage, available_agents: List[str],
              agent_info: Dict[str, Dict[str, Any]]) -> List[str]:
        """Apply filter and return filtered agent list"""
        pass


class CapabilityFilter(RouterFilter):
    """Filter agents by capabilities"""

    def __init__(self, required_capabilities: List[str], match_all: bool = False):
        self.required_capabilities = required_capabilities
        self.match_all = match_all

    def apply(self, message: AgentMessage, available_agents: List[str],
              agent_info: Dict[str, Dict[str, Any]]) -> List[str]:
        filtered = []

        for agent_id in available_agents:
            if agent_id in agent_info:
                agent_caps = agent_info[agent_id].get('capabilities', [])

                if self.match_all:
                    # Agent must have ALL required capabilities
                    if all(cap in agent_caps for cap in self.required_capabilities):
                        filtered.append(agent_id)
                else:
                    # Agent must have ANY required capability
                    if any(cap in agent_caps for cap in self.required_capabilities):
                        filtered.append(agent_id)

        return filtered


class LoadBalanceFilter(RouterFilter):
    """Filter agents based on current load"""

    def __init__(self, max_load_threshold: float = 0.8):
        self.max_load_threshold = max_load_threshold

    def apply(self, message: AgentMessage, available_agents: List[str],
              agent_info: Dict[str, Dict[str, Any]]) -> List[str]:
        filtered = []

        for agent_id in available_agents:
            if agent_id in agent_info:
                current_load = agent_info[agent_id].get('current_load', 0.0)
                if current_load <= self.max_load_threshold:
                    filtered.append(agent_id)

        return filtered


class MessageRouter:
    """Advanced message routing system"""

    def __init__(self):
        self.routing_rules: List[RoutingRule] = []
        self.filters: Dict[str, RouterFilter] = {}
        self.agent_loads: Dict[str, int] = {}  # Track message load per agent
        self.round_robin_state: Dict[str, int] = {}  # Round robin state per message type
        self.route_history: List[Dict[str, Any]] = []

    def add_routing_rule(self, rule: RoutingRule):
        """Add a new routing rule"""
        self.routing_rules.append(rule)
        # Sort by priority (highest first)
        self.routing_rules.sort(key=lambda r: r.priority, reverse=True)

    def remove_routing_rule(self, rule_id: str) -> bool:
        """Remove a routing rule"""
        original_count = len(self.routing_rules)
        self.routing_rules = [r for r in self.routing_rules if r.rule_id != rule_id]
        return len(self.routing_rules) < original_count

    def add_filter(self, name: str, filter_instance: RouterFilter):
        """Add a custom filter"""
        self.filters[name] = filter_instance

    def route_message(self, message: AgentMessage, available_agents: List[str],
                     agent_info: Dict[str, Dict[str, Any]] = None) -> List[str]:
        """Route message to appropriate agents"""
        if agent_info is None:
            agent_info = {}

        # If message has specific recipient, route directly
        if message.recipient_id and message.message_type == MessageType.DIRECT:
            if message.recipient_id in available_agents:
                self._record_route(message, [message.recipient_id], "direct_routing")
                return [message.recipient_id]
            else:
                self._record_route(message, [], "recipient_not_available")
                return []

        # Apply routing rules
        target_agents = self._apply_routing_rules(message, available_agents, agent_info)

        if target_agents:
            self._record_route(message, target_agents, "rule_based_routing")
            return target_agents

        # Fallback to default routing strategy
        fallback_agents = self._apply_default_routing(message, available_agents, agent_info)
        self._record_route(message, fallback_agents, "default_routing")

        return fallback_agents

    def _apply_routing_rules(self, message: AgentMessage, available_agents: List[str],
                           agent_info: Dict[str, Dict[str, Any]]) -> List[str]:
        """Apply routing rules to determine target agents"""
        for rule in self.routing_rules:
            if not rule.matches(message, agent_info):
                continue

            if rule.strategy == RoutingStrategy.DIRECT:
                if rule.target_agents:
                    return [agent for agent in rule.target_agents if agent in available_agents]

            elif rule.strategy == RoutingStrategy.BROADCAST:
                return available_agents.copy()

            elif rule.strategy == RoutingStrategy.FILTERED:
                return self._apply_filters(message, available_agents, agent_info)

            elif rule.strategy == RoutingStrategy.PRIORITY:
                return self._route_by_priority(message, available_agents, agent_info)

            elif rule.strategy == RoutingStrategy.ROUND_ROBIN:
                return self._route_round_robin(message, available_agents)

            elif rule.strategy == RoutingStrategy.LOAD_BASED:
                return self._route_by_load(message, available_agents, agent_info)

        return []

    def _apply_default_routing(self, message: AgentMessage, available_agents: List[str],
                             agent_info: Dict[str, Dict[str, Any]]) -> List[str]:
        """Apply default routing when no rules match"""
        if message.message_type == MessageType.BROADCAST:
            return available_agents.copy()

        elif message.message_type == MessageType.SYSTEM:
            # System messages go to all agents
            return available_agents.copy()

        elif message.message_type == MessageType.TASK_UPDATE:
            # Task updates go to involved agents (could be enhanced with task tracking)
            return available_agents.copy()

        else:
            # For direct messages without specific recipient, use round robin
            return self._route_round_robin(message, available_agents)

    def _apply_filters(self, message: AgentMessage, available_agents: List[str],
                      agent_info: Dict[str, Dict[str, Any]]) -> List[str]:
        """Apply all registered filters"""
        filtered_agents = available_agents.copy()

        for filter_name, filter_instance in self.filters.items():
            filtered_agents = filter_instance.apply(message, filtered_agents, agent_info)

        return filtered_agents

    def _route_by_priority(self, message: AgentMessage, available_agents: List[str],
                          agent_info: Dict[str, Dict[str, Any]]) -> List[str]:
        """Route based on agent priority/availability"""
        # Sort agents by their current load (ascending)
        agent_loads = [(agent, self.agent_loads.get(agent, 0)) for agent in available_agents]
        agent_loads.sort(key=lambda x: x[1])

        # For urgent messages, send to multiple agents
        if message.priority == MessagePriority.URGENT:
            return [agent for agent, _ in agent_loads[:3]]  # Top 3 least loaded

        # For high priority, send to best available agent
        elif message.priority == MessagePriority.HIGH:
            return [agent_loads[0][0]] if agent_loads else []

        # For normal/low priority, use round robin
        else:
            return self._route_round_robin(message, available_agents)

    def _route_round_robin(self, message: AgentMessage, available_agents: List[str]) -> List[str]:
        """Round robin routing"""
        if not available_agents:
            return []

        message_type_key = message.message_type.value
        current_index = self.round_robin_state.get(message_type_key, 0)

        selected_agent = available_agents[current_index % len(available_agents)]

        # Update round robin state
        self.round_robin_state[message_type_key] = (current_index + 1) % len(available_agents)

        return [selected_agent]

    def _route_by_load(self, message: AgentMessage, available_agents: List[str],
                      agent_info: Dict[str, Dict[str, Any]]) -> List[str]:
        """Route to least loaded agent"""
        if not available_agents:
            return []

        # Find agent with minimum load
        min_load = float('inf')
        best_agent = None

        for agent_id in available_agents:
            load = self.agent_loads.get(agent_id, 0)
            if agent_id in agent_info:
                # Factor in additional load metrics from agent info
                current_load = agent_info[agent_id].get('current_load', 0)
                total_load = load + current_load
            else:
                total_load = load

            if total_load < min_load:
                min_load = total_load
                best_agent = agent_id

        return [best_agent] if best_agent else []

    def update_agent_load(self, agent_id: str, delta: int = 1):
        """Update agent load tracking"""
        self.agent_loads[agent_id] = self.agent_loads.get(agent_id, 0) + delta

    def _record_route(self, message: AgentMessage, target_agents: List[str], strategy: str):
        """Record routing decision for analytics"""
        route_record = {
            'message_id': message.message_id,
            'sender_id': message.sender_id,
            'target_agents': target_agents,
            'strategy': strategy,
            'message_type': message.message_type.value,
            'priority': message.priority.value,
            'timestamp': datetime.now()
        }

        self.route_history.append(route_record)

        # Keep only last 1000 route records
        if len(self.route_history) > 1000:
            self.route_history = self.route_history[-1000:]

    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        total_routes = len(self.route_history)

        if total_routes == 0:
            return {'total_routes': 0}

        # Strategy distribution
        strategy_counts = {}
        for record in self.route_history:
            strategy = record['strategy']
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        # Agent load distribution
        load_stats = {
            'agent_loads': self.agent_loads.copy(),
            'total_load': sum(self.agent_loads.values())
        }

        return {
            'total_routes': total_routes,
            'strategy_distribution': strategy_counts,
            'load_statistics': load_stats,
            'active_rules': len([r for r in self.routing_rules if r.active]),
            'round_robin_state': self.round_robin_state.copy()
        }

    def export_rules(self) -> List[Dict[str, Any]]:
        """Export routing rules configuration"""
        return [
            {
                'rule_id': rule.rule_id,
                'name': rule.name,
                'strategy': rule.strategy.value,
                'filter_type': rule.filter_type.value,
                'filter_value': rule.filter_value,
                'target_agents': rule.target_agents,
                'priority': rule.priority,
                'active': rule.active,
                'description': rule.description
            }
            for rule in self.routing_rules
        ]

    def import_rules(self, rules_data: List[Dict[str, Any]]):
        """Import routing rules configuration"""
        for rule_data in rules_data:
            rule = RoutingRule(
                rule_id=rule_data['rule_id'],
                name=rule_data['name'],
                strategy=RoutingStrategy(rule_data['strategy']),
                filter_type=FilterType(rule_data['filter_type']),
                filter_value=rule_data['filter_value'],
                target_agents=rule_data.get('target_agents'),
                priority=rule_data.get('priority', 0),
                active=rule_data.get('active', True),
                description=rule_data.get('description')
            )
            self.add_routing_rule(rule)