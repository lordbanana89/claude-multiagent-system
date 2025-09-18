"""
Input Validation and Error Handling for Inbox System
Comprehensive validation, sanitization, and error handling utilities
"""

from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import re
import html
import json
from dataclasses import dataclass
from enum import Enum

from shared_state.models import MessageType, MessagePriority, MessageStatus


class ValidationError(Exception):
    """Custom validation exception"""
    def __init__(self, message: str, field: str = None, code: str = None):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'error': self.message,
            'field': self.field,
            'code': self.code
        }


class ValidationSeverity(Enum):
    """Validation error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of validation with details"""
    valid: bool
    errors: List[ValidationError] = None
    warnings: List[str] = None
    sanitized_data: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

    def add_error(self, message: str, field: str = None, code: str = None):
        """Add validation error"""
        self.errors.append(ValidationError(message, field, code))
        self.valid = False

    def add_warning(self, message: str):
        """Add validation warning"""
        self.warnings.append(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'valid': self.valid,
            'errors': [error.to_dict() for error in self.errors],
            'warnings': self.warnings,
            'sanitized_data': self.sanitized_data
        }


class MessageValidator:
    """Validates message content and structure"""

    # Configuration constants
    MAX_CONTENT_LENGTH = 10000
    MAX_SUBJECT_LENGTH = 200
    MAX_AGENT_ID_LENGTH = 100
    MIN_CONTENT_LENGTH = 1

    # Regex patterns
    AGENT_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    # Blocked content patterns (basic security)
    BLOCKED_PATTERNS = [
        re.compile(r'<script.*?</script>', re.IGNORECASE | re.DOTALL),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'on\w+\s*=', re.IGNORECASE),  # Event handlers
        re.compile(r'data:.*base64', re.IGNORECASE),  # Data URLs
    ]

    @classmethod
    def validate_message_content(cls, data: Dict[str, Any]) -> ValidationResult:
        """Validate message content data"""
        result = ValidationResult(valid=True)
        sanitized = {}

        # Validate recipient_id
        if 'recipient_id' in data:
            recipient_id = data['recipient_id']
            if recipient_id is not None:
                if not isinstance(recipient_id, str):
                    result.add_error("recipient_id must be string", "recipient_id", "INVALID_TYPE")
                elif len(recipient_id) > cls.MAX_AGENT_ID_LENGTH:
                    result.add_error(f"recipient_id too long (max {cls.MAX_AGENT_ID_LENGTH})", "recipient_id", "TOO_LONG")
                elif not cls.AGENT_ID_PATTERN.match(recipient_id):
                    result.add_error("recipient_id contains invalid characters", "recipient_id", "INVALID_FORMAT")
                else:
                    sanitized['recipient_id'] = recipient_id.strip()

        # Validate sender_id
        if 'sender_id' in data:
            sender_id = data['sender_id']
            if not isinstance(sender_id, str):
                result.add_error("sender_id must be string", "sender_id", "INVALID_TYPE")
            elif len(sender_id) > cls.MAX_AGENT_ID_LENGTH:
                result.add_error(f"sender_id too long (max {cls.MAX_AGENT_ID_LENGTH})", "sender_id", "TOO_LONG")
            elif not cls.AGENT_ID_PATTERN.match(sender_id):
                result.add_error("sender_id contains invalid characters", "sender_id", "INVALID_FORMAT")
            else:
                sanitized['sender_id'] = sender_id.strip()

        # Validate content
        if 'content' not in data:
            result.add_error("content is required", "content", "REQUIRED")
        else:
            content = data['content']
            if not isinstance(content, str):
                result.add_error("content must be string", "content", "INVALID_TYPE")
            elif len(content.strip()) < cls.MIN_CONTENT_LENGTH:
                result.add_error("content cannot be empty", "content", "TOO_SHORT")
            elif len(content) > cls.MAX_CONTENT_LENGTH:
                result.add_error(f"content too long (max {cls.MAX_CONTENT_LENGTH})", "content", "TOO_LONG")
            else:
                # Security check for malicious content
                security_result = cls._check_content_security(content)
                if not security_result[0]:
                    result.add_error(f"content contains potentially malicious code: {security_result[1]}", "content", "SECURITY_VIOLATION")
                else:
                    sanitized['content'] = cls._sanitize_content(content)

        # Validate subject
        if 'subject' in data and data['subject'] is not None:
            subject = data['subject']
            if not isinstance(subject, str):
                result.add_error("subject must be string", "subject", "INVALID_TYPE")
            elif len(subject) > cls.MAX_SUBJECT_LENGTH:
                result.add_error(f"subject too long (max {cls.MAX_SUBJECT_LENGTH})", "subject", "TOO_LONG")
            else:
                sanitized['subject'] = cls._sanitize_content(subject)

        # Validate message_type
        if 'message_type' in data:
            try:
                message_type = MessageType(data['message_type'])
                sanitized['message_type'] = message_type.value
            except (ValueError, TypeError):
                result.add_error("invalid message_type", "message_type", "INVALID_VALUE")

        # Validate priority
        if 'priority' in data:
            try:
                if isinstance(data['priority'], int):
                    priority = MessagePriority(data['priority'])
                    sanitized['priority'] = priority.value
                else:
                    priority = MessagePriority(data['priority'])
                    sanitized['priority'] = priority.value
            except (ValueError, TypeError):
                result.add_error("invalid priority (must be 1-4)", "priority", "INVALID_VALUE")

        # Validate metadata
        if 'metadata' in data:
            if not isinstance(data['metadata'], dict):
                result.add_error("metadata must be object", "metadata", "INVALID_TYPE")
            else:
                try:
                    # Ensure metadata is JSON serializable
                    json.dumps(data['metadata'])
                    sanitized['metadata'] = data['metadata']
                except (TypeError, ValueError):
                    result.add_error("metadata must be JSON serializable", "metadata", "INVALID_FORMAT")

        result.sanitized_data = sanitized
        return result

    @classmethod
    def validate_broadcast_data(cls, data: Dict[str, Any]) -> ValidationResult:
        """Validate broadcast message data"""
        result = cls.validate_message_content(data)

        # Additional validation for broadcast
        if 'recipients' in data:
            recipients = data['recipients']
            if not isinstance(recipients, list):
                result.add_error("recipients must be array", "recipients", "INVALID_TYPE")
            elif len(recipients) == 0:
                result.add_warning("broadcasting to no recipients")
            else:
                valid_recipients = []
                for i, recipient in enumerate(recipients):
                    if not isinstance(recipient, str):
                        result.add_error(f"recipient[{i}] must be string", f"recipients[{i}]", "INVALID_TYPE")
                    elif len(recipient) > cls.MAX_AGENT_ID_LENGTH:
                        result.add_error(f"recipient[{i}] too long", f"recipients[{i}]", "TOO_LONG")
                    elif not cls.AGENT_ID_PATTERN.match(recipient):
                        result.add_error(f"recipient[{i}] invalid format", f"recipients[{i}]", "INVALID_FORMAT")
                    else:
                        valid_recipients.append(recipient.strip())

                if result.sanitized_data:
                    result.sanitized_data['recipients'] = valid_recipients

        return result

    @classmethod
    def validate_search_query(cls, query: str) -> ValidationResult:
        """Validate search query"""
        result = ValidationResult(valid=True)

        if not isinstance(query, str):
            result.add_error("query must be string", "query", "INVALID_TYPE")
        elif len(query.strip()) == 0:
            result.add_error("query cannot be empty", "query", "TOO_SHORT")
        elif len(query) > 1000:
            result.add_error("query too long (max 1000)", "query", "TOO_LONG")
        else:
            # Basic SQL injection protection
            dangerous_patterns = ['--', ';', 'union', 'select', 'insert', 'update', 'delete', 'drop']
            query_lower = query.lower()
            for pattern in dangerous_patterns:
                if pattern in query_lower:
                    result.add_warning(f"query contains potentially dangerous pattern: {pattern}")

            result.sanitized_data = {'query': query.strip()}

        return result

    @classmethod
    def validate_pagination(cls, limit: Any, offset: Any) -> ValidationResult:
        """Validate pagination parameters"""
        result = ValidationResult(valid=True)
        sanitized = {}

        # Validate limit
        if limit is not None:
            try:
                limit_int = int(limit)
                if limit_int < 1:
                    result.add_error("limit must be positive", "limit", "INVALID_VALUE")
                elif limit_int > 1000:
                    result.add_warning("limit capped at 1000")
                    sanitized['limit'] = 1000
                else:
                    sanitized['limit'] = limit_int
            except (ValueError, TypeError):
                result.add_error("limit must be integer", "limit", "INVALID_TYPE")

        # Validate offset
        if offset is not None:
            try:
                offset_int = int(offset)
                if offset_int < 0:
                    result.add_error("offset must be non-negative", "offset", "INVALID_VALUE")
                else:
                    sanitized['offset'] = offset_int
            except (ValueError, TypeError):
                result.add_error("offset must be integer", "offset", "INVALID_TYPE")

        result.sanitized_data = sanitized
        return result

    @classmethod
    def _check_content_security(cls, content: str) -> Tuple[bool, Optional[str]]:
        """Check content for security violations"""
        for pattern in cls.BLOCKED_PATTERNS:
            match = pattern.search(content)
            if match:
                return False, match.group(0)[:50] + "..." if len(match.group(0)) > 50 else match.group(0)
        return True, None

    @classmethod
    def _sanitize_content(cls, content: str) -> str:
        """Sanitize content by escaping HTML and trimming whitespace"""
        # HTML escape to prevent XSS
        sanitized = html.escape(content)
        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized)
        # Trim
        sanitized = sanitized.strip()
        return sanitized


class ErrorHandler:
    """Centralized error handling for inbox operations"""

    @staticmethod
    def handle_storage_error(error: Exception) -> Dict[str, Any]:
        """Handle storage-related errors"""
        error_type = type(error).__name__

        if "UNIQUE constraint failed" in str(error):
            return {
                'error': 'Message already exists',
                'code': 'DUPLICATE_MESSAGE',
                'type': 'storage_error'
            }
        elif "database is locked" in str(error):
            return {
                'error': 'Database temporarily unavailable',
                'code': 'DATABASE_LOCKED',
                'type': 'storage_error'
            }
        elif "no such table" in str(error):
            return {
                'error': 'Database not properly initialized',
                'code': 'DATABASE_NOT_INITIALIZED',
                'type': 'storage_error'
            }
        else:
            return {
                'error': 'Storage operation failed',
                'code': 'STORAGE_ERROR',
                'type': 'storage_error',
                'details': str(error)
            }

    @staticmethod
    def handle_routing_error(error: Exception) -> Dict[str, Any]:
        """Handle routing-related errors"""
        return {
            'error': 'Message routing failed',
            'code': 'ROUTING_ERROR',
            'type': 'routing_error',
            'details': str(error)
        }

    @staticmethod
    def handle_auth_error(error: Exception) -> Dict[str, Any]:
        """Handle authentication-related errors"""
        error_message = str(error).lower()

        if "token" in error_message and "expired" in error_message:
            return {
                'error': 'Authentication token expired',
                'code': 'TOKEN_EXPIRED',
                'type': 'auth_error'
            }
        elif "invalid" in error_message and "token" in error_message:
            return {
                'error': 'Invalid authentication token',
                'code': 'INVALID_TOKEN',
                'type': 'auth_error'
            }
        elif "permission" in error_message:
            return {
                'error': 'Insufficient permissions',
                'code': 'PERMISSION_DENIED',
                'type': 'auth_error'
            }
        else:
            return {
                'error': 'Authentication failed',
                'code': 'AUTH_ERROR',
                'type': 'auth_error',
                'details': str(error)
            }

    @staticmethod
    def handle_validation_error(validation_result: ValidationResult) -> Dict[str, Any]:
        """Handle validation errors"""
        return {
            'error': 'Validation failed',
            'code': 'VALIDATION_ERROR',
            'type': 'validation_error',
            'validation_errors': [error.to_dict() for error in validation_result.errors],
            'warnings': validation_result.warnings
        }

    @staticmethod
    def handle_generic_error(error: Exception, operation: str = "operation") -> Dict[str, Any]:
        """Handle generic errors"""
        return {
            'error': f'{operation.capitalize()} failed',
            'code': 'INTERNAL_ERROR',
            'type': 'internal_error',
            'details': str(error)
        }


# Rate limiting utilities
class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self):
        self.requests = {}  # agent_id -> list of timestamps

    def is_allowed(self, agent_id: str, max_requests: int = 100, window_seconds: int = 3600) -> bool:
        """Check if request is allowed under rate limit"""
        now = datetime.now()
        window_start = now.timestamp() - window_seconds

        # Clean old requests
        if agent_id in self.requests:
            self.requests[agent_id] = [
                timestamp for timestamp in self.requests[agent_id]
                if timestamp > window_start
            ]
        else:
            self.requests[agent_id] = []

        # Check limit
        if len(self.requests[agent_id]) >= max_requests:
            return False

        # Add current request
        self.requests[agent_id].append(now.timestamp())
        return True

    def get_remaining_requests(self, agent_id: str, max_requests: int = 100, window_seconds: int = 3600) -> int:
        """Get remaining requests for agent"""
        now = datetime.now()
        window_start = now.timestamp() - window_seconds

        if agent_id in self.requests:
            recent_requests = [
                timestamp for timestamp in self.requests[agent_id]
                if timestamp > window_start
            ]
            return max(0, max_requests - len(recent_requests))

        return max_requests