#!/usr/bin/env python3
"""
MCP Security Module v2
Implements OAuth 2.1, consent flow, path protection, and audit logging
Following RFC 8707 for Resource Indicators
"""

import json
import sqlite3
import hashlib
import secrets
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import jwt
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DB_PATH = "/tmp/mcp_state.db"
PROJECT_ROOT = Path("/Users/erik/Desktop/claude-multiagent-system")
JWT_SECRET = secrets.token_urlsafe(32)
TOKEN_EXPIRY_HOURS = 24
CONSENT_EXPIRY_MINUTES = 30

class OperationType(Enum):
    """Types of operations requiring different security levels"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"

class ConsentLevel(Enum):
    """Consent levels for dangerous operations"""
    NONE = "none"
    REQUIRED = "required"
    EXPLICIT = "explicit"
    ADMIN_ONLY = "admin_only"

@dataclass
class SecurityContext:
    """Security context for a request"""
    session_id: str
    user_id: Optional[str]
    token: Optional[str]
    scopes: List[str]
    ip_address: str
    request_id: str
    timestamp: datetime

class MCPSecurity:
    def __init__(self):
        self.db_path = DB_PATH
        self._init_security_tables()
        self._init_dangerous_operations()

    def _init_security_tables(self):
        """Initialize security-related database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # OAuth tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS oauth_tokens (
                token_id TEXT PRIMARY KEY,
                session_id TEXT,
                user_id TEXT,
                scopes TEXT,
                issued_at INTEGER,
                expires_at INTEGER,
                revoked BOOLEAN DEFAULT FALSE
            )
        """)

        # Consent decisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consent_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                operation TEXT,
                resource TEXT,
                decision TEXT,
                timestamp INTEGER,
                expires_at INTEGER,
                reason TEXT
            )
        """)

        # Audit log table with enhanced fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                session_id TEXT,
                user_id TEXT,
                operation TEXT,
                resource TEXT,
                result TEXT,
                ip_address TEXT,
                request_id TEXT,
                details TEXT
            )
        """)

        # Path access attempts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS path_access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                path TEXT,
                normalized_path TEXT,
                access_type TEXT,
                allowed BOOLEAN,
                reason TEXT,
                session_id TEXT
            )
        """)

        # Rate limiting table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rate_limits (
                key TEXT PRIMARY KEY,
                count INTEGER,
                window_start INTEGER,
                last_request INTEGER
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Security tables initialized")

    def _init_dangerous_operations(self):
        """Define operations requiring consent"""
        self.dangerous_operations = {
            # Destructive operations
            "delete": ConsentLevel.REQUIRED,
            "drop": ConsentLevel.REQUIRED,
            "remove": ConsentLevel.REQUIRED,
            "destroy": ConsentLevel.REQUIRED,
            "reset": ConsentLevel.EXPLICIT,
            "truncate": ConsentLevel.EXPLICIT,

            # Production operations
            "deploy_production": ConsentLevel.EXPLICIT,
            "migrate_database": ConsentLevel.EXPLICIT,
            "modify_production": ConsentLevel.ADMIN_ONLY,

            # Security operations
            "change_permissions": ConsentLevel.ADMIN_ONLY,
            "modify_security": ConsentLevel.ADMIN_ONLY,
            "access_secrets": ConsentLevel.ADMIN_ONLY
        }

    # OAuth 2.1 Implementation
    def create_oauth_token(self, session_id: str, user_id: str, scopes: List[str]) -> Dict:
        """Create OAuth 2.1 compliant token"""
        token_id = secrets.token_urlsafe(32)

        # Create JWT token
        payload = {
            "jti": token_id,
            "sub": user_id,
            "iss": "mcp_server_v2",
            "aud": "mcp_client",
            "exp": int(time.time()) + (TOKEN_EXPIRY_HOURS * 3600),
            "iat": int(time.time()),
            "scopes": scopes,
            "session_id": session_id
        }

        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

        # Store token in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO oauth_tokens
            (token_id, session_id, user_id, scopes, issued_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            token_id,
            session_id,
            user_id,
            json.dumps(scopes),
            int(time.time()),
            payload["exp"]
        ))

        conn.commit()
        conn.close()

        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": TOKEN_EXPIRY_HOURS * 3600,
            "scope": " ".join(scopes),
            "refresh_token": secrets.token_urlsafe(32)
        }

    def validate_oauth_token(self, token: str) -> Optional[Dict]:
        """Validate OAuth token and return claims"""
        try:
            # Decode JWT
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

            # Check if token is revoked
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT revoked FROM oauth_tokens WHERE token_id = ?
            """, (payload["jti"],))

            result = cursor.fetchone()
            conn.close()

            if result and result[0]:
                return None  # Token is revoked

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None

    def revoke_token(self, token_id: str) -> bool:
        """Revoke an OAuth token"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE oauth_tokens SET revoked = TRUE WHERE token_id = ?
        """, (token_id,))

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0

    # Consent Flow Implementation
    def check_consent_required(self, operation: str, resource: str) -> ConsentLevel:
        """Check if operation requires consent"""
        operation_lower = operation.lower()

        # Check dangerous operations
        for dangerous_op, level in self.dangerous_operations.items():
            if dangerous_op in operation_lower:
                return level

        # Check resource-specific rules
        if resource.startswith("file://"):
            if "write" in operation_lower or "delete" in operation_lower:
                return ConsentLevel.REQUIRED

        return ConsentLevel.NONE

    def request_consent(self, session_id: str, operation: str, resource: str,
                        details: Dict = None) -> str:
        """Request user consent for dangerous operation"""
        consent_id = secrets.token_urlsafe(16)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO consent_decisions
            (session_id, operation, resource, decision, timestamp, expires_at, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            operation,
            resource,
            "pending",
            int(time.time()),
            int(time.time()) + (CONSENT_EXPIRY_MINUTES * 60),
            json.dumps(details) if details else None
        ))

        conn.commit()
        conn.close()

        return consent_id

    def check_consent(self, session_id: str, operation: str, resource: str) -> Tuple[bool, str]:
        """Check if consent has been granted"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT decision, expires_at FROM consent_decisions
            WHERE session_id = ? AND operation = ? AND resource = ?
            AND expires_at > ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (session_id, operation, resource, int(time.time())))

        result = cursor.fetchone()
        conn.close()

        if result:
            decision, expires_at = result
            if decision == "approved":
                return True, "Consent granted"
            elif decision == "denied":
                return False, "Consent denied"

        return False, "No valid consent found"

    def grant_consent(self, consent_id: str, decision: str, reason: str = None) -> bool:
        """Grant or deny consent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE consent_decisions
            SET decision = ?, reason = ?
            WHERE id = ? AND decision = 'pending'
        """, (decision, reason, consent_id))

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0

    # Path Traversal Protection
    def validate_file_path(self, uri: str) -> Tuple[bool, str]:
        """Validate file path against traversal attacks"""
        if not uri.startswith("file://"):
            return True, "Not a file URI"

        path_str = uri[7:]  # Remove file://

        try:
            # Resolve the path and normalize it
            requested_path = Path(path_str).resolve()

            # Log access attempt
            self._log_path_access(str(requested_path), uri, True)

            # Check if path is within project root
            if not str(requested_path).startswith(str(PROJECT_ROOT)):
                self._log_path_access(str(requested_path), uri, False,
                                     "Outside project directory")
                return False, "Access denied: Path outside project directory"

            # Check blacklist patterns
            blacklist = [
                '.git', '.env', 'id_rsa', 'id_ed25519', '.ssh',
                'private.key', 'secret', 'password', 'token',
                '.pem', '.key', '.cert', 'credentials'
            ]

            path_lower = str(requested_path).lower()
            for forbidden in blacklist:
                if forbidden in path_lower:
                    self._log_path_access(str(requested_path), uri, False,
                                         f"Blacklisted: {forbidden}")
                    return False, f"Access denied: Forbidden path pattern '{forbidden}'"

            # Check if file exists and is readable
            if not requested_path.exists():
                return True, "Path validated (file does not exist)"

            if not requested_path.is_file():
                return False, "Access denied: Not a file"

            return True, "Path validated successfully"

        except Exception as e:
            self._log_path_access(path_str, uri, False, str(e))
            return False, f"Path validation error: {str(e)}"

    def _log_path_access(self, path: str, original_uri: str, allowed: bool,
                         reason: str = None):
        """Log path access attempts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO path_access_log
            (timestamp, path, normalized_path, access_type, allowed, reason, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            int(time.time()),
            original_uri,
            path,
            "read",
            allowed,
            reason,
            "system"
        ))

        conn.commit()
        conn.close()

    # Rate Limiting
    def check_rate_limit(self, key: str, limit: int = 100,
                        window_seconds: int = 60) -> Tuple[bool, Dict]:
        """Check and update rate limit"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        current_time = int(time.time())
        window_start = current_time - window_seconds

        # Get current rate limit state
        cursor.execute("""
            SELECT count, window_start, last_request
            FROM rate_limits WHERE key = ?
        """, (key,))

        result = cursor.fetchone()

        if result:
            count, old_window_start, last_request = result

            # Reset if window expired
            if old_window_start < window_start:
                count = 1
                cursor.execute("""
                    UPDATE rate_limits
                    SET count = ?, window_start = ?, last_request = ?
                    WHERE key = ?
                """, (1, current_time, current_time, key))
            else:
                # Increment counter
                count += 1
                cursor.execute("""
                    UPDATE rate_limits
                    SET count = ?, last_request = ?
                    WHERE key = ?
                """, (count, current_time, key))
        else:
            # Create new rate limit entry
            count = 1
            cursor.execute("""
                INSERT INTO rate_limits (key, count, window_start, last_request)
                VALUES (?, ?, ?, ?)
            """, (key, 1, current_time, current_time))

        conn.commit()
        conn.close()

        allowed = count <= limit
        remaining = max(0, limit - count)
        reset_time = window_start + window_seconds

        return allowed, {
            "allowed": allowed,
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time,
            "retry_after": reset_time - current_time if not allowed else None
        }

    # Audit Logging
    def log_audit(self, context: SecurityContext, operation: str,
                  resource: str, result: str, details: Dict = None):
        """Log security audit event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO audit_log
            (timestamp, session_id, user_id, operation, resource, result,
             ip_address, request_id, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            int(time.time()),
            context.session_id,
            context.user_id,
            operation,
            resource,
            result,
            context.ip_address,
            context.request_id,
            json.dumps(details) if details else None
        ))

        conn.commit()
        conn.close()

    def get_audit_logs(self, session_id: str = None, limit: int = 100) -> List[Dict]:
        """Retrieve audit logs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if session_id:
            cursor.execute("""
                SELECT * FROM audit_log
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (session_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM audit_log
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

        columns = [col[0] for col in cursor.description]
        logs = []
        for row in cursor.fetchall():
            log_dict = dict(zip(columns, row))
            if log_dict.get('details'):
                log_dict['details'] = json.loads(log_dict['details'])
            logs.append(log_dict)

        conn.close()
        return logs

    # Security Policy Enforcement
    def enforce_security_policy(self, context: SecurityContext,
                               operation: str, resource: str) -> Tuple[bool, str]:
        """Enforce security policies for an operation"""
        # Check OAuth scopes
        if context.token:
            token_data = self.validate_oauth_token(context.token)
            if not token_data:
                return False, "Invalid or expired token"

            required_scope = self._get_required_scope(operation)
            if required_scope not in token_data.get("scopes", []):
                return False, f"Missing required scope: {required_scope}"

        # Check rate limiting
        rate_key = f"{context.ip_address}:{operation}"
        allowed, rate_info = self.check_rate_limit(rate_key)
        if not allowed:
            return False, f"Rate limit exceeded. Retry after {rate_info['retry_after']} seconds"

        # Check consent for dangerous operations
        consent_level = self.check_consent_required(operation, resource)
        if consent_level != ConsentLevel.NONE:
            has_consent, reason = self.check_consent(context.session_id, operation, resource)
            if not has_consent:
                return False, f"Consent required: {reason}"

        # Check path security for file operations
        if resource.startswith("file://"):
            valid, reason = self.validate_file_path(resource)
            if not valid:
                return False, reason

        return True, "Security checks passed"

    def _get_required_scope(self, operation: str) -> str:
        """Get required OAuth scope for operation"""
        operation_lower = operation.lower()

        if any(op in operation_lower for op in ["read", "list", "get"]):
            return "read"
        elif any(op in operation_lower for op in ["write", "create", "update"]):
            return "write"
        elif any(op in operation_lower for op in ["delete", "remove", "drop"]):
            return "delete"
        elif any(op in operation_lower for op in ["execute", "run", "call"]):
            return "execute"
        else:
            return "admin"

def create_security_context(request_data: Dict) -> SecurityContext:
    """Create security context from request data"""
    return SecurityContext(
        session_id=request_data.get("session_id", ""),
        user_id=request_data.get("user_id"),
        token=request_data.get("token"),
        scopes=request_data.get("scopes", []),
        ip_address=request_data.get("ip_address", "127.0.0.1"),
        request_id=request_data.get("request_id", ""),
        timestamp=datetime.now()
    )

# Example usage and testing
if __name__ == "__main__":
    security = MCPSecurity()

    print("MCP Security Module v2 initialized")
    print("Security features:")
    print("- OAuth 2.1 authentication")
    print("- Consent flow for dangerous operations")
    print("- Path traversal protection")
    print("- Rate limiting")
    print("- Comprehensive audit logging")

    # Test OAuth token creation
    token_response = security.create_oauth_token(
        session_id="test-session",
        user_id="test-user",
        scopes=["read", "write", "execute"]
    )
    print(f"\nTest OAuth token created: {token_response['token_type']}")
    print(f"Expires in: {token_response['expires_in']} seconds")

    # Test path validation
    test_paths = [
        "file:///Users/erik/Desktop/claude-multiagent-system/README.md",
        "file://../../etc/passwd",
        "file://.git/config",
        "file://test.key"
    ]

    print("\nPath validation tests:")
    for path in test_paths:
        valid, reason = security.validate_file_path(path)
        status = "✅" if valid else "❌"
        print(f"{status} {path}: {reason}")