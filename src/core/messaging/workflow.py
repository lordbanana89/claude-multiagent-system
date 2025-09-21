#!/usr/bin/env python3
"""
Agent Decision Engine and Workflow Management
Handles automated decision-making for message processing and agent workflows
"""

import json
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Tuple
from pathlib import Path

# Import from parent shared_state and messaging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_state.models import AgentMessage, MessagePriority
from messaging.classification import MessageClassifier, MessageCategory, ClassificationMessageType, ResponseRequirement, UrgencyLevel


class WorkflowAction(Enum):
    """Available workflow actions"""
    ACKNOWLEDGE = "acknowledge"
    RESPOND = "respond"
    ESCALATE = "escalate"
    ARCHIVE = "archive"
    DEFER = "defer"
    AUTO_REPLY = "auto_reply"
    REQUEST_CLARIFICATION = "request_clarification"
    MARK_COMPLETE = "mark_complete"
    IGNORE = "ignore"


class AgentCapability(Enum):
    """Agent capability types"""
    API_DEVELOPMENT = "api_development"
    DATABASE_MANAGEMENT = "database_management"
    FRONTEND_DEVELOPMENT = "frontend_development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    SECURITY = "security"
    COORDINATION = "coordination"
    SOCIAL_MEDIA = "social_media"


@dataclass
class WorkflowRule:
    """Defines workflow automation rule"""
    name: str
    conditions: Dict[str, Any]  # Conditions to match
    actions: List[WorkflowAction]  # Actions to take
    auto_response_template: Optional[str] = None
    escalation_delay_minutes: int = 60
    priority: int = 1  # Higher priority rules checked first
    enabled: bool = True


@dataclass
class AgentConfig:
    """Configuration for agent behavior"""
    agent_id: str
    capabilities: List[AgentCapability]
    auto_acknowledge: bool = True
    auto_respond_info: bool = True
    auto_escalate_urgent: bool = True
    working_hours_start: str = "00:00"
    working_hours_end: str = "23:59"
    max_concurrent_tasks: int = 3
    response_delay_seconds: int = 5  # Delay before auto-response
    custom_rules: List[WorkflowRule] = None

    def __post_init__(self):
        if self.custom_rules is None:
            self.custom_rules = []


@dataclass
class WorkflowDecision:
    """Result of workflow decision-making"""
    message_id: str
    agent_id: str
    category: MessageCategory
    recommended_actions: List[WorkflowAction]
    auto_response: Optional[str] = None
    escalation_target: Optional[str] = None
    defer_until: Optional[datetime] = None
    confidence: float = 0.0
    reasoning: str = ""


class AgentDecisionEngine:
    """Core decision engine for agent workflow automation"""

    def __init__(self, config_file: str = "workflow_config.json"):
        self.configs: Dict[str, AgentConfig] = {}
        self.classifier = MessageClassifier()
        self.config_file = config_file
        self.decision_history: List[WorkflowDecision] = []
        self.pending_escalations: Dict[str, datetime] = {}
        self.active_workflows: Dict[str, Dict] = {}  # message_id -> workflow state

        # Background processing
        self.processing_enabled = True
        self.workflow_thread = threading.Thread(target=self._process_workflows, daemon=True)
        self.workflow_thread.start()

        # Load configurations
        self._load_default_configs()
        self._load_configs()

    def _load_default_configs(self):
        """Load default agent configurations"""
        default_configs = {
            "backend-api": AgentConfig(
                agent_id="backend-api",
                capabilities=[
                    AgentCapability.API_DEVELOPMENT,
                    AgentCapability.DATABASE_MANAGEMENT,
                    AgentCapability.SECURITY
                ],
                auto_acknowledge=True,
                auto_respond_info=True,
                max_concurrent_tasks=5
            ),
            "frontend-ui": AgentConfig(
                agent_id="frontend-ui",
                capabilities=[
                    AgentCapability.FRONTEND_DEVELOPMENT,
                    AgentCapability.TESTING
                ],
                auto_acknowledge=True,
                auto_respond_info=True,
                max_concurrent_tasks=3
            ),
            "database": AgentConfig(
                agent_id="database",
                capabilities=[
                    AgentCapability.DATABASE_MANAGEMENT,
                    AgentCapability.MONITORING
                ],
                auto_acknowledge=True,
                auto_respond_info=True,
                max_concurrent_tasks=4
            ),
            "testing": AgentConfig(
                agent_id="testing",
                capabilities=[
                    AgentCapability.TESTING,
                    AgentCapability.MONITORING
                ],
                auto_acknowledge=True,
                auto_respond_info=True,
                max_concurrent_tasks=6
            ),
            "instagram": AgentConfig(
                agent_id="instagram",
                capabilities=[
                    AgentCapability.SOCIAL_MEDIA
                ],
                auto_acknowledge=True,
                auto_respond_info=True,
                max_concurrent_tasks=2
            ),
            "supervisor": AgentConfig(
                agent_id="supervisor",
                capabilities=[
                    AgentCapability.COORDINATION,
                    AgentCapability.MONITORING
                ],
                auto_acknowledge=True,
                auto_respond_info=False,  # Supervisor handles manually
                auto_escalate_urgent=False,
                max_concurrent_tasks=10
            ),
            "master": AgentConfig(
                agent_id="master",
                capabilities=[
                    AgentCapability.COORDINATION,
                    AgentCapability.SECURITY,
                    AgentCapability.MONITORING
                ],
                auto_acknowledge=True,
                auto_respond_info=False,  # Master handles manually
                auto_escalate_urgent=False,
                max_concurrent_tasks=20
            )
        }

        self.configs = default_configs

    def process_message(self, message: AgentMessage) -> WorkflowDecision:
        """Process incoming message and make workflow decision"""

        # Classify the message
        category = self.classifier.classify_message(message)

        # Get agent configuration
        agent_config = self.configs.get(
            message.recipient_id,
            AgentConfig(agent_id=message.recipient_id, capabilities=[])
        )

        # Make workflow decision
        decision = self._make_workflow_decision(message, category, agent_config)

        # Record decision
        self.decision_history.append(decision)

        # Execute immediate actions
        self._execute_immediate_actions(decision)

        # Schedule deferred actions
        if decision.defer_until:
            self._schedule_deferred_action(decision)

        return decision

    def _make_workflow_decision(self, message: AgentMessage, category: MessageCategory, config: AgentConfig) -> WorkflowDecision:
        """Make intelligent workflow decision based on message and agent config"""

        actions = []
        auto_response = None
        escalation_target = None
        defer_until = None
        confidence = category.confidence
        reasoning_parts = []

        # Check custom rules first
        for rule in config.custom_rules:
            if rule.enabled and self._matches_rule_conditions(message, category, rule):
                actions.extend(rule.actions)
                if rule.auto_response_template:
                    auto_response = self._generate_response_from_template(message, rule.auto_response_template)
                reasoning_parts.append(f"Matched custom rule: {rule.name}")
                break

        # If no custom rules matched, apply default logic
        if not actions:
            actions, auto_response, escalation_target, defer_until, reasoning = self._apply_default_workflow_logic(
                message, category, config
            )
            reasoning_parts.extend(reasoning)

        # Apply working hours logic
        if not self._is_working_hours(config):
            if category.urgency_level != UrgencyLevel.CRITICAL:
                # Defer non-critical messages outside working hours
                defer_until = self._calculate_next_working_hour(config)
                actions = [WorkflowAction.DEFER]
                reasoning_parts.append("Outside working hours - deferred")

        decision = WorkflowDecision(
            message_id=message.message_id,
            agent_id=message.recipient_id,
            category=category,
            recommended_actions=actions,
            auto_response=auto_response,
            escalation_target=escalation_target,
            defer_until=defer_until,
            confidence=confidence,
            reasoning=" | ".join(reasoning_parts)
        )

        return decision

    def _apply_default_workflow_logic(self, message: AgentMessage, category: MessageCategory, config: AgentConfig) -> Tuple[List[WorkflowAction], Optional[str], Optional[str], Optional[datetime], List[str]]:
        """Apply default workflow logic based on message type and agent config"""

        actions = []
        auto_response = None
        escalation_target = None
        defer_until = None
        reasoning = []

        # Handle by message type
        if category.message_type == ClassificationMessageType.URGENT_ALERT:
            actions.append(WorkflowAction.ACKNOWLEDGE)
            reasoning.append("Urgent alert - immediate acknowledgment")

            if config.auto_escalate_urgent and "master" in category.escalation_path:
                escalation_target = "master"
                actions.append(WorkflowAction.ESCALATE)
                reasoning.append("Auto-escalating urgent alert to master")

        elif category.message_type == ClassificationMessageType.TASK_ASSIGNMENT:
            # Check if agent has relevant capabilities
            if self._has_relevant_capabilities(message, config):
                actions.append(WorkflowAction.ACKNOWLEDGE)
                auto_response = self._generate_task_acceptance_response(message, config)
                reasoning.append("Task matches agent capabilities - accepting")
            else:
                actions.append(WorkflowAction.ESCALATE)
                escalation_target = "supervisor"
                auto_response = f"This task appears to be outside my capabilities. Escalating to supervisor for proper assignment."
                reasoning.append("Task outside capabilities - escalating")

        elif category.message_type == ClassificationMessageType.QUESTION:
            if category.response_requirement == ResponseRequirement.IMMEDIATE:
                actions.append(WorkflowAction.RESPOND)
                reasoning.append("Immediate response required for question")
            else:
                actions.append(WorkflowAction.ACKNOWLEDGE)
                reasoning.append("Question acknowledged - will respond shortly")

        elif category.message_type == ClassificationMessageType.INFORMATION:
            if config.auto_acknowledge:
                actions.append(WorkflowAction.ACKNOWLEDGE)
                reasoning.append("Information auto-acknowledged")

            if category.auto_archive:
                actions.append(WorkflowAction.ARCHIVE)
                reasoning.append("Information marked for auto-archive")

        elif category.message_type == ClassificationMessageType.CONFIRMATION:
            actions.append(WorkflowAction.ARCHIVE)
            reasoning.append("Confirmation message - archived")

        elif category.message_type == ClassificationMessageType.REQUEST_APPROVAL:
            if message.recipient_id in ["supervisor", "master"]:
                # Approval requests need manual handling
                actions.append(WorkflowAction.ACKNOWLEDGE)
                reasoning.append("Approval request - manual review required")
            else:
                actions.append(WorkflowAction.ESCALATE)
                escalation_target = "supervisor"
                reasoning.append("Approval request escalated to supervisor")

        else:  # GENERAL or unknown
            if config.auto_acknowledge:
                actions.append(WorkflowAction.ACKNOWLEDGE)
                reasoning.append("General message auto-acknowledged")

        return actions, auto_response, escalation_target, defer_until, reasoning

    def _has_relevant_capabilities(self, message: AgentMessage, config: AgentConfig) -> bool:
        """Check if agent has capabilities relevant to the message"""
        content_lower = f"{message.subject or ''} {message.content}".lower()

        capability_keywords = {
            AgentCapability.API_DEVELOPMENT: ["api", "endpoint", "backend", "server", "rest"],
            AgentCapability.DATABASE_MANAGEMENT: ["database", "sql", "migration", "query", "db"],
            AgentCapability.FRONTEND_DEVELOPMENT: ["frontend", "ui", "react", "component", "interface"],
            AgentCapability.TESTING: ["test", "testing", "qa", "validation", "bug"],
            AgentCapability.DEPLOYMENT: ["deploy", "deployment", "release", "production"],
            AgentCapability.SECURITY: ["security", "auth", "authentication", "vulnerability"],
            AgentCapability.SOCIAL_MEDIA: ["instagram", "social", "post", "media", "content"],
            AgentCapability.MONITORING: ["monitor", "metrics", "performance", "health"],
            AgentCapability.COORDINATION: ["coordinate", "manage", "oversee", "delegate"]
        }

        for capability in config.capabilities:
            keywords = capability_keywords.get(capability, [])
            if any(keyword in content_lower for keyword in keywords):
                return True

        return False

    def _generate_task_acceptance_response(self, message: AgentMessage, config: AgentConfig) -> str:
        """Generate automatic task acceptance response"""
        responses = [
            f"Task received and accepted. I'll begin work on this immediately.",
            f"Acknowledged. This falls within my capabilities - starting work now.",
            f"Task accepted. Will provide progress updates as work progresses.",
            f"Received and understood. Beginning implementation now."
        ]

        # Select response based on agent type
        agent_id = config.agent_id
        if "backend" in agent_id:
            return f"Backend task received. Starting API/server implementation now. ETA will be provided shortly."
        elif "frontend" in agent_id:
            return f"UI task accepted. Will begin frontend development and provide wireframes soon."
        elif "database" in agent_id:
            return f"Database task acknowledged. Starting schema/query work immediately."
        elif "testing" in agent_id:
            return f"Testing task received. Will create test suite and begin validation."
        else:
            return responses[0]

    def _generate_response_from_template(self, message: AgentMessage, template: str) -> str:
        """Generate response from template with variable substitution"""
        variables = {
            'sender': message.sender_id,
            'subject': message.subject or 'No subject',
            'timestamp': datetime.now().strftime('%H:%M'),
            'agent_id': message.recipient_id
        }

        response = template
        for key, value in variables.items():
            response = response.replace(f'{{{key}}}', str(value))

        return response

    def _matches_rule_conditions(self, message: AgentMessage, category: MessageCategory, rule: WorkflowRule) -> bool:
        """Check if message matches rule conditions"""
        conditions = rule.conditions

        # Check message type
        if 'message_type' in conditions:
            if category.message_type.value != conditions['message_type']:
                return False

        # Check urgency level
        if 'urgency_level' in conditions:
            if category.urgency_level.value != conditions['urgency_level']:
                return False

        # Check sender
        if 'sender_id' in conditions:
            if message.sender_id not in conditions['sender_id']:
                return False

        # Check keywords
        if 'keywords' in conditions:
            content = f"{message.subject or ''} {message.content}".lower()
            if not any(keyword.lower() in content for keyword in conditions['keywords']):
                return False

        return True

    def _execute_immediate_actions(self, decision: WorkflowDecision):
        """Execute actions that should happen immediately"""
        for action in decision.recommended_actions:
            if action == WorkflowAction.ACKNOWLEDGE:
                self._send_acknowledgment(decision)
            elif action == WorkflowAction.AUTO_REPLY and decision.auto_response:
                self._send_auto_response(decision)
            elif action == WorkflowAction.ESCALATE and decision.escalation_target:
                self._escalate_message(decision)

    def _send_acknowledgment(self, decision: WorkflowDecision):
        """Send acknowledgment message"""
        print(f"📨 {decision.agent_id}: Acknowledging message {decision.message_id[:8]}")
        # This would integrate with the messaging system to send actual acknowledgment

    def _send_auto_response(self, decision: WorkflowDecision):
        """Send automatic response"""
        print(f"🤖 {decision.agent_id}: Auto-responding to {decision.message_id[:8]}: {decision.auto_response}")
        # This would integrate with the messaging system to send actual response

    def _escalate_message(self, decision: WorkflowDecision):
        """Escalate message to appropriate agent"""
        print(f"⬆️ {decision.agent_id}: Escalating {decision.message_id[:8]} to {decision.escalation_target}")
        # This would integrate with the messaging system to send escalation

    def _schedule_deferred_action(self, decision: WorkflowDecision):
        """Schedule action to be executed later"""
        if decision.defer_until:
            self.active_workflows[decision.message_id] = {
                'decision': decision,
                'scheduled_time': decision.defer_until,
                'status': 'deferred'
            }

    def _process_workflows(self):
        """Background thread to process scheduled workflows"""
        while self.processing_enabled:
            try:
                current_time = datetime.now()

                # Process deferred workflows
                completed_workflows = []
                for message_id, workflow in self.active_workflows.items():
                    if workflow['status'] == 'deferred' and current_time >= workflow['scheduled_time']:
                        decision = workflow['decision']
                        self._execute_immediate_actions(decision)
                        completed_workflows.append(message_id)

                # Clean up completed workflows
                for message_id in completed_workflows:
                    del self.active_workflows[message_id]

                time.sleep(30)  # Check every 30 seconds

            except Exception as e:
                print(f"Workflow processing error: {e}")
                time.sleep(60)

    def _is_working_hours(self, config: AgentConfig) -> bool:
        """Check if current time is within agent's working hours"""
        now = datetime.now().time()
        start = datetime.strptime(config.working_hours_start, "%H:%M").time()
        end = datetime.strptime(config.working_hours_end, "%H:%M").time()

        if start <= end:
            return start <= now <= end
        else:  # Spans midnight
            return now >= start or now <= end

    def _calculate_next_working_hour(self, config: AgentConfig) -> datetime:
        """Calculate next working hour for deferred actions"""
        now = datetime.now()
        start_time = datetime.strptime(config.working_hours_start, "%H:%M").time()

        # Calculate next working day start
        next_working = now.replace(
            hour=start_time.hour,
            minute=start_time.minute,
            second=0,
            microsecond=0
        )

        if next_working <= now:
            next_working += timedelta(days=1)

        return next_working

    def add_agent_config(self, config: AgentConfig):
        """Add or update agent configuration"""
        self.configs[config.agent_id] = config
        self._save_configs()

    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow statistics"""
        if not self.decision_history:
            return {}

        total = len(self.decision_history)
        action_counts = {}
        confidence_sum = 0

        for decision in self.decision_history:
            for action in decision.recommended_actions:
                action_counts[action.value] = action_counts.get(action.value, 0) + 1
            confidence_sum += decision.confidence

        return {
            'total_decisions': total,
            'average_confidence': confidence_sum / total,
            'action_distribution': action_counts,
            'active_workflows': len(self.active_workflows),
            'agents_configured': len(self.configs)
        }

    def _load_configs(self):
        """Load configurations from file"""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    data = json.load(f)

                for agent_id, config_data in data.get('agents', {}).items():
                    # Convert capability strings back to enums
                    if 'capabilities' in config_data:
                        config_data['capabilities'] = [
                            AgentCapability(cap) for cap in config_data['capabilities']
                        ]

                    self.configs[agent_id] = AgentConfig(**config_data)

                print(f"📋 Loaded workflow configs for {len(self.configs)} agents")
        except Exception as e:
            print(f"❌ Error loading workflow configs: {e}")

    def _save_configs(self):
        """Save configurations to file"""
        try:
            data = {
                'agents': {},
                'updated': datetime.now().isoformat()
            }

            for agent_id, config in self.configs.items():
                config_dict = asdict(config)
                # Convert enums to strings for JSON serialization
                config_dict['capabilities'] = [cap.value for cap in config.capabilities]
                data['agents'][agent_id] = config_dict

            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"❌ Error saving workflow configs: {e}")

    def shutdown(self):
        """Shutdown the decision engine"""
        self.processing_enabled = False
        if self.workflow_thread.is_alive():
            self.workflow_thread.join(timeout=5)


# Global decision engine instance
_decision_engine = None


def get_decision_engine() -> AgentDecisionEngine:
    """Get global decision engine instance"""
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = AgentDecisionEngine()
    return _decision_engine


def process_agent_message(message: AgentMessage) -> WorkflowDecision:
    """Convenience function to process a message"""
    return get_decision_engine().process_message(message)


if __name__ == "__main__":
    # Test the decision engine
    from shared_state.models import MessageType as OriginalMessageType

    engine = AgentDecisionEngine()

    # Test message
    test_message = AgentMessage(
        sender_id="supervisor",
        recipient_id="backend-api",
        content="Please implement the new user authentication API endpoints. This includes login, logout, and password reset functionality.",
        subject="Task: Authentication API Implementation",
        priority=MessagePriority.HIGH,
        message_type=OriginalMessageType.DIRECT
    )

    decision = engine.process_message(test_message)

    print(f"📧 Message: {test_message.subject}")
    print(f"🤖 Agent: {decision.agent_id}")
    print(f"🏷️  Category: {decision.category.message_type.value}")
    print(f"🎯 Actions: {[action.value for action in decision.recommended_actions]}")
    print(f"💬 Auto Response: {decision.auto_response}")
    print(f"🔧 Reasoning: {decision.reasoning}")
    print(f"🎯 Confidence: {decision.confidence:.2f}")

    # Print stats
    stats = engine.get_workflow_stats()
    print(f"\n📊 Workflow Stats:")
    print(f"Total Decisions: {stats['total_decisions']}")
    print(f"Average Confidence: {stats['average_confidence']:.2f}")
    print(f"Agents Configured: {stats['agents_configured']}")

    engine.shutdown()