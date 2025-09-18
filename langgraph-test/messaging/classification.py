#!/usr/bin/env python3
"""
Intelligent message classification system
Automatically categorizes messages and determines appropriate workflows
"""

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Import from parent shared_state
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_state.models import AgentMessage, MessagePriority, MessageType as BaseMessageType


# Create compatibility alias for external imports
MessageType = BaseMessageType

class ClassificationMessageType(Enum):
    """Extended message types for classification"""
    TASK_ASSIGNMENT = "task_assignment"
    QUESTION = "question"
    INFORMATION = "information"
    URGENT_ALERT = "urgent_alert"
    SYSTEM_UPDATE = "system_update"
    REQUEST_APPROVAL = "request_approval"
    CONFIRMATION = "confirmation"
    ESCALATION = "escalation"
    GENERAL = "general"


class ResponseRequirement(Enum):
    """Response requirement levels"""
    NONE = "none"              # No response needed
    OPTIONAL = "optional"      # Response helpful but not required
    REQUIRED = "required"      # Response required
    IMMEDIATE = "immediate"    # Immediate response required
    ACKNOWLEDGMENT = "acknowledgment"  # Simple acknowledgment sufficient


class UrgencyLevel(Enum):
    """Message urgency levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


@dataclass
class MessageCategory:
    """Classification result for a message"""
    message_type: ClassificationMessageType
    urgency_level: UrgencyLevel
    response_requirement: ResponseRequirement
    confidence: float  # 0.0 to 1.0
    timeout_minutes: Optional[int] = None  # Response timeout
    auto_archive: bool = False
    escalation_path: List[str] = None
    suggested_actions: List[str] = None
    keywords_matched: List[str] = None

    def __post_init__(self):
        if self.escalation_path is None:
            self.escalation_path = []
        if self.suggested_actions is None:
            self.suggested_actions = []
        if self.keywords_matched is None:
            self.keywords_matched = []


@dataclass
class ClassificationPattern:
    """Pattern definition for message classification"""
    name: str
    keywords: List[str]
    message_type: ClassificationMessageType
    urgency_level: UrgencyLevel
    response_requirement: ResponseRequirement
    priority_boost: Optional[MessagePriority] = None
    timeout_minutes: Optional[int] = None
    auto_archive: bool = False
    escalation_roles: List[str] = None
    confidence_weight: float = 1.0

    def __post_init__(self):
        if self.escalation_roles is None:
            self.escalation_roles = []


class MessageClassifier:
    """Intelligent message classification system"""

    def __init__(self, patterns_file: str = "classification_patterns.json"):
        self.patterns: List[ClassificationPattern] = []
        self.patterns_file = patterns_file
        self.classification_history: List[Dict] = []
        self.learning_enabled = True

        # Initialize with default patterns
        self._load_default_patterns()

        # Load custom patterns if available
        self._load_patterns()

    def _load_default_patterns(self):
        """Load default classification patterns"""
        default_patterns = [
            # Task Assignment Patterns
            ClassificationPattern(
                name="deploy_task",
                keywords=["deploy", "deployment", "release", "publish", "launch"],
                message_type=ClassificationMessageType.TASK_ASSIGNMENT,
                urgency_level=UrgencyLevel.HIGH,
                response_requirement=ResponseRequirement.REQUIRED,
                timeout_minutes=30,
                escalation_roles=["supervisor", "master"]
            ),
            ClassificationPattern(
                name="fix_task",
                keywords=["fix", "bug", "error", "issue", "problem", "broken"],
                message_type=ClassificationMessageType.TASK_ASSIGNMENT,
                urgency_level=UrgencyLevel.HIGH,
                response_requirement=ResponseRequirement.REQUIRED,
                timeout_minutes=60,
                escalation_roles=["supervisor"]
            ),
            ClassificationPattern(
                name="implement_task",
                keywords=["implement", "create", "build", "develop", "add"],
                message_type=ClassificationMessageType.TASK_ASSIGNMENT,
                urgency_level=UrgencyLevel.NORMAL,
                response_requirement=ResponseRequirement.REQUIRED,
                timeout_minutes=120
            ),

            # Urgent Alert Patterns
            ClassificationPattern(
                name="critical_emergency",
                keywords=["emergency", "critical", "urgent", "immediately", "asap", "now"],
                message_type=ClassificationMessageType.URGENT_ALERT,
                urgency_level=UrgencyLevel.CRITICAL,
                response_requirement=ResponseRequirement.IMMEDIATE,
                priority_boost=MessagePriority.URGENT,
                timeout_minutes=5,
                escalation_roles=["master", "supervisor"]
            ),
            ClassificationPattern(
                name="system_down",
                keywords=["down", "offline", "crashed", "failure", "outage"],
                message_type=ClassificationMessageType.URGENT_ALERT,
                urgency_level=UrgencyLevel.CRITICAL,
                response_requirement=ResponseRequirement.IMMEDIATE,
                timeout_minutes=10,
                escalation_roles=["master", "supervisor"]
            ),
            ClassificationPattern(
                name="security_alert",
                keywords=["security", "breach", "vulnerability", "attack", "threat"],
                message_type=ClassificationMessageType.URGENT_ALERT,
                urgency_level=UrgencyLevel.CRITICAL,
                response_requirement=ResponseRequirement.IMMEDIATE,
                timeout_minutes=5,
                escalation_roles=["master"]
            ),

            # Question Patterns
            ClassificationPattern(
                name="how_question",
                keywords=["how", "what", "where", "when", "why", "which", "?"],
                message_type=ClassificationMessageType.QUESTION,
                urgency_level=UrgencyLevel.NORMAL,
                response_requirement=ResponseRequirement.REQUIRED,
                timeout_minutes=60
            ),
            ClassificationPattern(
                name="help_request",
                keywords=["help", "assist", "support", "guidance", "advice"],
                message_type=ClassificationMessageType.QUESTION,
                urgency_level=UrgencyLevel.NORMAL,
                response_requirement=ResponseRequirement.REQUIRED,
                timeout_minutes=30
            ),

            # Information Patterns
            ClassificationPattern(
                name="status_update",
                keywords=["status", "update", "progress", "completed", "finished"],
                message_type=ClassificationMessageType.INFORMATION,
                urgency_level=UrgencyLevel.LOW,
                response_requirement=ResponseRequirement.ACKNOWLEDGMENT,
                auto_archive=True,
                timeout_minutes=240
            ),
            ClassificationPattern(
                name="report",
                keywords=["report", "summary", "metrics", "analytics", "results"],
                message_type=ClassificationMessageType.INFORMATION,
                urgency_level=UrgencyLevel.LOW,
                response_requirement=ResponseRequirement.OPTIONAL,
                auto_archive=True
            ),

            # System Update Patterns
            ClassificationPattern(
                name="system_update",
                keywords=["update", "upgrade", "version", "release", "patch"],
                message_type=ClassificationMessageType.SYSTEM_UPDATE,
                urgency_level=UrgencyLevel.NORMAL,
                response_requirement=ResponseRequirement.ACKNOWLEDGMENT,
                timeout_minutes=120
            ),

            # Approval Request Patterns
            ClassificationPattern(
                name="approval_request",
                keywords=["approve", "approval", "permission", "authorize", "confirm"],
                message_type=ClassificationMessageType.REQUEST_APPROVAL,
                urgency_level=UrgencyLevel.HIGH,
                response_requirement=ResponseRequirement.REQUIRED,
                timeout_minutes=30,
                escalation_roles=["supervisor", "master"]
            ),

            # Confirmation Patterns
            ClassificationPattern(
                name="confirmation",
                keywords=["confirm", "confirmed", "acknowledged", "received", "understood"],
                message_type=ClassificationMessageType.CONFIRMATION,
                urgency_level=UrgencyLevel.LOW,
                response_requirement=ResponseRequirement.NONE,
                auto_archive=True
            )
        ]

        self.patterns = default_patterns

    def classify_message(self, message: AgentMessage) -> MessageCategory:
        """Classify a message and return category information"""

        # Prepare text for analysis
        text_to_analyze = f"{message.subject or ''} {message.content}".lower()

        # Find matching patterns
        pattern_matches = []

        for pattern in self.patterns:
            keywords_found = []
            confidence_score = 0.0

            # Check for keyword matches
            for keyword in pattern.keywords:
                if keyword.lower() in text_to_analyze:
                    keywords_found.append(keyword)
                    confidence_score += pattern.confidence_weight

            if keywords_found:
                # Calculate confidence based on keywords found and pattern weight
                confidence = min(1.0, (len(keywords_found) / len(pattern.keywords)) * pattern.confidence_weight)

                pattern_matches.append({
                    'pattern': pattern,
                    'confidence': confidence,
                    'keywords_found': keywords_found
                })

        # Sort by confidence
        pattern_matches.sort(key=lambda x: x['confidence'], reverse=True)

        if pattern_matches:
            # Use best match
            best_match = pattern_matches[0]
            pattern = best_match['pattern']

            # Determine escalation path based on message priority and pattern
            escalation_path = self._determine_escalation_path(message, pattern)

            # Generate suggested actions
            suggested_actions = self._generate_suggested_actions(message, pattern)

            # Apply priority boost if specified
            urgency = pattern.urgency_level
            if pattern.priority_boost and message.priority == MessagePriority.NORMAL:
                urgency = UrgencyLevel.URGENT

            category = MessageCategory(
                message_type=pattern.message_type,
                urgency_level=urgency,
                response_requirement=pattern.response_requirement,
                confidence=best_match['confidence'],
                timeout_minutes=pattern.timeout_minutes,
                auto_archive=pattern.auto_archive,
                escalation_path=escalation_path,
                suggested_actions=suggested_actions,
                keywords_matched=best_match['keywords_found']
            )
        else:
            # Default classification for unmatched messages
            category = MessageCategory(
                message_type=ClassificationMessageType.GENERAL,
                urgency_level=UrgencyLevel.NORMAL,
                response_requirement=ResponseRequirement.OPTIONAL,
                confidence=0.1,
                timeout_minutes=240,
                suggested_actions=["Review manually", "Respond if needed"]
            )

        # Record classification for learning
        self._record_classification(message, category)

        return category

    def _determine_escalation_path(self, message: AgentMessage, pattern: ClassificationPattern) -> List[str]:
        """Determine escalation path based on message and pattern"""
        escalation_path = []

        # Add pattern-specific escalation roles
        escalation_path.extend(pattern.escalation_roles)

        # Add priority-based escalation
        if message.priority == MessagePriority.URGENT and "master" not in escalation_path:
            escalation_path.insert(0, "master")

        if message.priority in [MessagePriority.HIGH, MessagePriority.URGENT] and "supervisor" not in escalation_path:
            escalation_path.append("supervisor")

        return escalation_path

    def _generate_suggested_actions(self, message: AgentMessage, pattern: ClassificationPattern) -> List[str]:
        """Generate suggested actions based on message type"""
        actions = []

        if pattern.message_type == ClassificationMessageType.TASK_ASSIGNMENT:
            actions.extend([
                "Accept task",
                "Estimate completion time",
                "Request clarification if needed",
                "Start work immediately"
            ])

        elif pattern.message_type == ClassificationMessageType.URGENT_ALERT:
            actions.extend([
                "Acknowledge immediately",
                "Assess situation",
                "Take corrective action",
                "Report status updates"
            ])

        elif pattern.message_type == ClassificationMessageType.QUESTION:
            actions.extend([
                "Provide detailed answer",
                "Ask clarifying questions",
                "Share relevant resources"
            ])

        elif pattern.message_type == ClassificationMessageType.INFORMATION:
            actions.extend([
                "Acknowledge receipt",
                "Archive message",
                "Take note for future reference"
            ])

        elif pattern.message_type == ClassificationMessageType.REQUEST_APPROVAL:
            actions.extend([
                "Review request details",
                "Approve or reject with reason",
                "Escalate if outside authority"
            ])

        else:
            actions.extend([
                "Review message content",
                "Respond appropriately",
                "Archive when complete"
            ])

        return actions

    def _record_classification(self, message: AgentMessage, category: MessageCategory):
        """Record classification for learning and analytics"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'message_id': message.message_id,
            'sender_id': message.sender_id,
            'recipient_id': message.recipient_id,
            'message_type': category.message_type.value,
            'urgency_level': category.urgency_level.value,
            'response_requirement': category.response_requirement.value,
            'confidence': category.confidence,
            'keywords_matched': category.keywords_matched
        }

        self.classification_history.append(record)

        # Keep only last 1000 records
        if len(self.classification_history) > 1000:
            self.classification_history = self.classification_history[-1000:]

    def add_custom_pattern(self, pattern: ClassificationPattern):
        """Add custom classification pattern"""
        self.patterns.append(pattern)
        self._save_patterns()

    def get_classification_stats(self) -> Dict[str, Any]:
        """Get classification statistics"""
        if not self.classification_history:
            return {}

        total = len(self.classification_history)

        # Message type distribution
        type_counts = {}
        urgency_counts = {}
        confidence_sum = 0

        for record in self.classification_history:
            msg_type = record['message_type']
            urgency = record['urgency_level']

            type_counts[msg_type] = type_counts.get(msg_type, 0) + 1
            urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1
            confidence_sum += record['confidence']

        return {
            'total_classifications': total,
            'average_confidence': confidence_sum / total,
            'message_type_distribution': type_counts,
            'urgency_distribution': urgency_counts,
            'patterns_count': len(self.patterns)
        }

    def _load_patterns(self):
        """Load custom patterns from file"""
        try:
            patterns_path = Path(self.patterns_file)
            if patterns_path.exists():
                with open(patterns_path, 'r') as f:
                    data = json.load(f)

                custom_patterns = []
                for pattern_data in data.get('patterns', []):
                    pattern = ClassificationPattern(**pattern_data)
                    custom_patterns.append(pattern)

                self.patterns.extend(custom_patterns)
                print(f"📋 Loaded {len(custom_patterns)} custom classification patterns")
        except Exception as e:
            print(f"❌ Error loading custom patterns: {e}")

    def _save_patterns(self):
        """Save patterns to file"""
        try:
            # Only save custom patterns (not default ones)
            custom_patterns = self.patterns[len(self._get_default_pattern_count()):]

            data = {
                'patterns': [asdict(pattern) for pattern in custom_patterns],
                'updated': datetime.now().isoformat()
            }

            with open(self.patterns_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving patterns: {e}")

    def _get_default_pattern_count(self) -> int:
        """Get count of default patterns"""
        # This should match the number of default patterns loaded
        return 12

    def retrain_pattern(self, pattern_name: str, correct_classification: MessageCategory):
        """Retrain a specific pattern based on feedback"""
        # Find and update pattern
        for pattern in self.patterns:
            if pattern.name == pattern_name:
                # Update pattern confidence weight based on feedback
                if correct_classification.confidence > 0.7:
                    pattern.confidence_weight = min(2.0, pattern.confidence_weight * 1.1)
                else:
                    pattern.confidence_weight = max(0.1, pattern.confidence_weight * 0.9)
                break

        self._save_patterns()


# Global classifier instance
_classifier = None


def get_message_classifier() -> MessageClassifier:
    """Get global classifier instance"""
    global _classifier
    if _classifier is None:
        _classifier = MessageClassifier()
    return _classifier


def classify_agent_message(message: AgentMessage) -> MessageCategory:
    """Convenience function to classify a message"""
    return get_message_classifier().classify_message(message)


if __name__ == "__main__":
    # Test the classification system
    from shared_state.models import MessageType as OriginalMessageType

    classifier = MessageClassifier()

    # Test messages
    test_messages = [
        AgentMessage(
            sender_id="supervisor",
            recipient_id="backend-api",
            content="Deploy the new authentication module immediately! This is critical.",
            subject="URGENT: Emergency Deployment",
            priority=MessagePriority.URGENT,
            message_type=BaseMessageType.DIRECT
        ),
        AgentMessage(
            sender_id="frontend-ui",
            recipient_id="backend-api",
            content="How do I integrate the new API endpoint for user profiles?",
            subject="API Integration Question",
            priority=MessagePriority.NORMAL,
            message_type=BaseMessageType.DIRECT
        ),
        AgentMessage(
            sender_id="database",
            recipient_id="supervisor",
            content="Migration completed successfully. All tables updated.",
            subject="Migration Status",
            priority=MessagePriority.LOW,
            message_type=BaseMessageType.DIRECT
        )
    ]

    for message in test_messages:
        category = classifier.classify_message(message)
        print(f"\n📧 Message: {message.subject}")
        print(f"🏷️  Type: {category.message_type.value}")
        print(f"🚨 Urgency: {category.urgency_level.value}")
        print(f"📋 Response: {category.response_requirement.value}")
        print(f"🎯 Confidence: {category.confidence:.2f}")
        print(f"⏰ Timeout: {category.timeout_minutes} minutes")
        print(f"🔧 Actions: {', '.join(category.suggested_actions[:2])}")

    # Print stats
    stats = classifier.get_classification_stats()
    print(f"\n📊 Classification Stats:")
    print(f"Total: {stats['total_classifications']}")
    print(f"Avg Confidence: {stats['average_confidence']:.2f}")