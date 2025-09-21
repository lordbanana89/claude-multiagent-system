#!/usr/bin/env python3
"""
MCP v2 Industry Compliance Module
Implements GDPR, HIPAA, SOC 2, and other compliance features
"""

import json
import hashlib
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import secrets
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComplianceLevel(Enum):
    """Compliance frameworks"""
    GDPR = "gdpr"           # General Data Protection Regulation
    HIPAA = "hipaa"         # Health Insurance Portability and Accountability Act
    SOC2 = "soc2"           # Service Organization Control 2
    PCI_DSS = "pci_dss"     # Payment Card Industry Data Security Standard
    ISO_27001 = "iso_27001" # Information Security Management
    CCPA = "ccpa"           # California Consumer Privacy Act

class DataClassification(Enum):
    """Data sensitivity levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PII = "pii"             # Personally Identifiable Information
    PHI = "phi"             # Protected Health Information
    PCI = "pci"             # Payment Card Information

class MCPCompliance:
    def __init__(self, db_path: str = "/tmp/mcp_state.db"):
        self.db_path = db_path
        self.encryption_key = self._generate_encryption_key()
        self.init_compliance_tables()
        self.compliance_policies = self._load_policies()

    def init_compliance_tables(self):
        """Initialize compliance-specific database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Data processing records (GDPR Article 30)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_processing_records (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                data_type TEXT NOT NULL,
                classification TEXT NOT NULL,
                purpose TEXT NOT NULL,
                legal_basis TEXT,
                data_subject_id TEXT,
                retention_period INTEGER,
                encryption_used BOOLEAN,
                third_party_shared BOOLEAN,
                metadata TEXT
            )
        """)

        # Consent management (GDPR)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consent_records (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                purpose TEXT NOT NULL,
                granted_at TEXT NOT NULL,
                expires_at TEXT,
                withdrawn_at TEXT,
                version TEXT,
                ip_address TEXT,
                metadata TEXT
            )
        """)

        # Access logs (HIPAA)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hipaa_access_logs (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                user_id TEXT NOT NULL,
                patient_id TEXT,
                resource_accessed TEXT,
                action TEXT,
                reason TEXT,
                emergency_override BOOLEAN,
                metadata TEXT
            )
        """)

        # Encryption keys audit (PCI-DSS)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS encryption_audit (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                key_id TEXT NOT NULL,
                algorithm TEXT,
                key_length INTEGER,
                purpose TEXT,
                rotation_date TEXT,
                status TEXT,
                metadata TEXT
            )
        """)

        # Data breach records (Multiple regulations)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS breach_records (
                id TEXT PRIMARY KEY,
                detected_at TEXT NOT NULL,
                reported_at TEXT,
                severity TEXT,
                affected_records INTEGER,
                data_types_affected TEXT,
                containment_actions TEXT,
                notification_sent BOOLEAN,
                regulatory_reported BOOLEAN,
                metadata TEXT
            )
        """)

        # Retention policies
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS retention_policies (
                id TEXT PRIMARY KEY,
                data_type TEXT NOT NULL,
                classification TEXT NOT NULL,
                retention_days INTEGER NOT NULL,
                deletion_method TEXT,
                legal_requirement TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Compliance tables initialized")

    def _generate_encryption_key(self) -> bytes:
        """Generate or retrieve encryption key"""
        # In production, use proper key management (KMS, HSM, etc.)
        return b'0123456789abcdef0123456789abcdef'  # 32 bytes for AES-256

    def _load_policies(self) -> Dict:
        """Load compliance policies"""
        return {
            ComplianceLevel.GDPR: {
                "data_minimization": True,
                "purpose_limitation": True,
                "storage_limitation": 365,  # days
                "right_to_erasure": True,
                "data_portability": True,
                "privacy_by_design": True,
                "breach_notification": 72  # hours
            },
            ComplianceLevel.HIPAA: {
                "minimum_necessary": True,
                "access_controls": True,
                "audit_controls": True,
                "integrity_controls": True,
                "transmission_security": True,
                "breach_notification": 60  # days
            },
            ComplianceLevel.SOC2: {
                "security": True,
                "availability": True,
                "processing_integrity": True,
                "confidentiality": True,
                "privacy": True
            },
            ComplianceLevel.PCI_DSS: {
                "encrypt_transmission": True,
                "encrypt_storage": True,
                "access_control": True,
                "regular_testing": True,
                "security_policy": True
            }
        }

    def encrypt_data(self, data: str, classification: DataClassification) -> str:
        """Encrypt sensitive data based on classification"""
        if classification in [DataClassification.PUBLIC, DataClassification.INTERNAL]:
            return data  # No encryption needed

        # Use AES-256-CBC for encryption
        iv = secrets.token_bytes(16)
        cipher = Cipher(
            algorithms.AES(self.encryption_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()

        # Pad the data
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data.encode()) + padder.finalize()

        # Encrypt
        encrypted = encryptor.update(padded_data) + encryptor.finalize()

        # Return base64 encoded (IV + encrypted data)
        return base64.b64encode(iv + encrypted).decode('utf-8')

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt encrypted data"""
        try:
            # Decode from base64
            data = base64.b64decode(encrypted_data)

            # Extract IV and encrypted content
            iv = data[:16]
            encrypted = data[16:]

            # Decrypt
            cipher = Cipher(
                algorithms.AES(self.encryption_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(encrypted) + decryptor.finalize()

            # Unpad
            unpadder = padding.PKCS7(128).unpadder()
            unpadded = unpadder.update(decrypted) + unpadder.finalize()

            return unpadded.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return ""

    def record_consent(self, user_id: str, purpose: str, duration_days: int = 365) -> str:
        """Record user consent (GDPR)"""
        consent_id = f"consent_{secrets.token_hex(16)}"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO consent_records
            (id, user_id, purpose, granted_at, expires_at, version, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            consent_id,
            user_id,
            purpose,
            datetime.utcnow().isoformat(),
            (datetime.utcnow() + timedelta(days=duration_days)).isoformat(),
            "1.0",
            json.dumps({"compliance": "GDPR", "lawful_basis": "consent"})
        ))

        conn.commit()
        conn.close()

        logger.info(f"Consent recorded: {consent_id} for user {user_id}")
        return consent_id

    def withdraw_consent(self, consent_id: str) -> bool:
        """Withdraw consent (GDPR right to withdraw)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE consent_records
            SET withdrawn_at = ?
            WHERE id = ? AND withdrawn_at IS NULL
        """, (datetime.utcnow().isoformat(), consent_id))

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        if affected > 0:
            logger.info(f"Consent withdrawn: {consent_id}")
            return True
        return False

    def check_consent(self, user_id: str, purpose: str) -> bool:
        """Check if valid consent exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM consent_records
            WHERE user_id = ?
            AND purpose = ?
            AND withdrawn_at IS NULL
            AND (expires_at IS NULL OR expires_at > ?)
        """, (user_id, purpose, datetime.utcnow().isoformat()))

        count = cursor.fetchone()[0]
        conn.close()

        return count > 0

    def log_data_processing(self, data_type: str, classification: DataClassification,
                           purpose: str, **kwargs) -> str:
        """Log data processing activity (GDPR Article 30)"""
        record_id = f"dpr_{secrets.token_hex(16)}"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO data_processing_records
            (id, timestamp, data_type, classification, purpose, legal_basis,
             data_subject_id, retention_period, encryption_used, third_party_shared, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record_id,
            datetime.utcnow().isoformat(),
            data_type,
            classification.value,
            purpose,
            kwargs.get('legal_basis', 'legitimate_interest'),
            kwargs.get('data_subject_id'),
            kwargs.get('retention_period', 365),
            kwargs.get('encryption_used', True),
            kwargs.get('third_party_shared', False),
            json.dumps(kwargs.get('metadata', {}))
        ))

        conn.commit()
        conn.close()

        return record_id

    def log_hipaa_access(self, user_id: str, resource: str, action: str, **kwargs) -> str:
        """Log HIPAA-compliant access"""
        access_id = f"hipaa_{secrets.token_hex(16)}"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO hipaa_access_logs
            (id, timestamp, user_id, patient_id, resource_accessed, action,
             reason, emergency_override, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            access_id,
            datetime.utcnow().isoformat(),
            user_id,
            kwargs.get('patient_id'),
            resource,
            action,
            kwargs.get('reason', 'treatment'),
            kwargs.get('emergency_override', False),
            json.dumps(kwargs.get('metadata', {}))
        ))

        conn.commit()
        conn.close()

        return access_id

    def pseudonymize_data(self, data: str, salt: str = "") -> str:
        """Pseudonymize data (GDPR technique)"""
        # Create deterministic but non-reversible pseudonym
        hash_input = f"{data}{salt}{self.encryption_key.hex()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def anonymize_data(self, data: Dict) -> Dict:
        """Anonymize data by removing/masking PII"""
        anonymized = data.copy()

        # Remove direct identifiers
        pii_fields = ['name', 'email', 'phone', 'ssn', 'ip_address',
                     'user_id', 'patient_id', 'credit_card']

        for field in pii_fields:
            if field in anonymized:
                if field == 'email':
                    # Partial masking for emails
                    parts = anonymized[field].split('@')
                    if len(parts) == 2:
                        anonymized[field] = f"{parts[0][:2]}****@{parts[1]}"
                else:
                    anonymized[field] = "REDACTED"

        # Generalize quasi-identifiers
        if 'age' in anonymized:
            age = anonymized['age']
            anonymized['age_group'] = f"{(age // 10) * 10}-{(age // 10) * 10 + 9}"
            del anonymized['age']

        if 'zip_code' in anonymized:
            anonymized['zip_code'] = anonymized['zip_code'][:3] + "**"

        return anonymized

    def export_user_data(self, user_id: str) -> Dict:
        """Export user data (GDPR right to portability)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        exported_data = {
            "user_id": user_id,
            "export_date": datetime.utcnow().isoformat(),
            "data": {}
        }

        # Export consent records
        cursor.execute("""
            SELECT * FROM consent_records WHERE user_id = ?
        """, (user_id,))
        exported_data["data"]["consents"] = cursor.fetchall()

        # Export processing records
        cursor.execute("""
            SELECT * FROM data_processing_records WHERE data_subject_id = ?
        """, (user_id,))
        exported_data["data"]["processing_records"] = cursor.fetchall()

        # Export access logs
        cursor.execute("""
            SELECT * FROM hipaa_access_logs WHERE user_id = ?
        """, (user_id,))
        exported_data["data"]["access_logs"] = cursor.fetchall()

        conn.close()

        # Log the export
        self.log_data_processing(
            "user_data_export",
            DataClassification.PII,
            "data_portability",
            data_subject_id=user_id
        )

        return exported_data

    def delete_user_data(self, user_id: str, reason: str = "user_request") -> bool:
        """Delete user data (GDPR right to erasure)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Delete from various tables
            cursor.execute("DELETE FROM consent_records WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM data_processing_records WHERE data_subject_id = ?", (user_id,))
            cursor.execute("DELETE FROM hipaa_access_logs WHERE user_id = ?", (user_id,))

            # Log the deletion
            cursor.execute("""
                INSERT INTO audit_log (timestamp, event_type, user_id, details)
                VALUES (?, ?, ?, ?)
            """, (
                datetime.utcnow().isoformat(),
                "data_deletion",
                user_id,
                json.dumps({"reason": reason, "compliance": "GDPR"})
            ))

            conn.commit()
            conn.close()

            logger.info(f"User data deleted for {user_id}: {reason}")
            return True

        except Exception as e:
            conn.rollback()
            conn.close()
            logger.error(f"Failed to delete user data: {e}")
            return False

    def record_breach(self, severity: str, affected_records: int,
                     data_types: List[str]) -> str:
        """Record a data breach incident"""
        breach_id = f"breach_{secrets.token_hex(16)}"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO breach_records
            (id, detected_at, severity, affected_records, data_types_affected,
             notification_sent, regulatory_reported, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            breach_id,
            datetime.utcnow().isoformat(),
            severity,
            affected_records,
            json.dumps(data_types),
            False,
            False,
            json.dumps({"status": "investigating"})
        ))

        conn.commit()
        conn.close()

        # Check notification requirements
        self._check_breach_notification_requirements(breach_id, severity)

        return breach_id

    def _check_breach_notification_requirements(self, breach_id: str, severity: str):
        """Check regulatory breach notification requirements"""
        notifications = []

        if severity in ['high', 'critical']:
            # GDPR: 72 hours
            notifications.append({
                "regulation": "GDPR",
                "deadline_hours": 72,
                "authority": "Data Protection Authority"
            })

            # HIPAA: 60 days
            notifications.append({
                "regulation": "HIPAA",
                "deadline_days": 60,
                "authority": "HHS Office for Civil Rights"
            })

        logger.warning(f"Breach {breach_id} requires notifications: {notifications}")
        return notifications

    def generate_compliance_report(self, compliance_level: ComplianceLevel) -> Dict:
        """Generate compliance report for specific framework"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        report = {
            "framework": compliance_level.value,
            "generated_at": datetime.utcnow().isoformat(),
            "status": "compliant",
            "findings": []
        }

        if compliance_level == ComplianceLevel.GDPR:
            # Check consent records
            cursor.execute("""
                SELECT COUNT(*) FROM consent_records
                WHERE withdrawn_at IS NULL AND expires_at > ?
            """, (datetime.utcnow().isoformat(),))
            report["active_consents"] = cursor.fetchone()[0]

            # Check data processing records
            cursor.execute("""
                SELECT COUNT(*) FROM data_processing_records
                WHERE timestamp > ?
            """, ((datetime.utcnow() - timedelta(days=30)).isoformat(),))
            report["processing_activities_30d"] = cursor.fetchone()[0]

            # Check for expired data
            cursor.execute("""
                SELECT COUNT(*) FROM data_processing_records
                WHERE datetime(timestamp, '+' || retention_period || ' days') < ?
            """, (datetime.utcnow().isoformat(),))
            expired_count = cursor.fetchone()[0]

            if expired_count > 0:
                report["status"] = "action_required"
                report["findings"].append({
                    "type": "expired_data",
                    "count": expired_count,
                    "action": "Delete expired data"
                })

        elif compliance_level == ComplianceLevel.HIPAA:
            # Check access logs
            cursor.execute("""
                SELECT COUNT(*) FROM hipaa_access_logs
                WHERE timestamp > ?
            """, ((datetime.utcnow() - timedelta(days=7)).isoformat(),))
            report["access_logs_7d"] = cursor.fetchone()[0]

            # Check for emergency overrides
            cursor.execute("""
                SELECT COUNT(*) FROM hipaa_access_logs
                WHERE emergency_override = 1 AND timestamp > ?
            """, ((datetime.utcnow() - timedelta(days=30)).isoformat(),))
            emergency_count = cursor.fetchone()[0]

            if emergency_count > 0:
                report["findings"].append({
                    "type": "emergency_access",
                    "count": emergency_count,
                    "action": "Review emergency access logs"
                })

        elif compliance_level == ComplianceLevel.SOC2:
            # Check encryption usage
            cursor.execute("""
                SELECT COUNT(*) FROM data_processing_records
                WHERE encryption_used = 0 AND classification IN ('confidential', 'restricted')
            """)
            unencrypted_count = cursor.fetchone()[0]

            if unencrypted_count > 0:
                report["status"] = "non_compliant"
                report["findings"].append({
                    "type": "unencrypted_sensitive_data",
                    "count": unencrypted_count,
                    "action": "Enable encryption for sensitive data"
                })

        conn.close()
        return report

    def get_retention_policy(self, data_type: str, classification: DataClassification) -> int:
        """Get retention period for data type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT retention_days FROM retention_policies
            WHERE data_type = ? AND classification = ?
        """, (data_type, classification.value))

        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]

        # Default retention periods
        defaults = {
            DataClassification.PUBLIC: 0,  # No limit
            DataClassification.INTERNAL: 730,  # 2 years
            DataClassification.CONFIDENTIAL: 365,  # 1 year
            DataClassification.RESTRICTED: 90,  # 3 months
            DataClassification.PII: 365,  # 1 year
            DataClassification.PHI: 2190,  # 6 years (HIPAA)
            DataClassification.PCI: 365  # 1 year (PCI-DSS)
        }

        return defaults.get(classification, 365)

    def validate_compliance(self, data: Dict, required_levels: List[ComplianceLevel]) -> Tuple[bool, List[str]]:
        """Validate data against compliance requirements"""
        violations = []

        for level in required_levels:
            if level == ComplianceLevel.GDPR:
                # Check for consent
                if 'user_id' in data and not self.check_consent(data['user_id'], data.get('purpose', 'processing')):
                    violations.append("GDPR: Missing user consent")

                # Check data minimization
                if len(data) > 20:  # Arbitrary threshold
                    violations.append("GDPR: Potential data minimization violation")

            elif level == ComplianceLevel.HIPAA:
                # Check for minimum necessary
                phi_fields = ['patient_name', 'medical_record', 'diagnosis']
                if any(field in data for field in phi_fields) and 'access_reason' not in data:
                    violations.append("HIPAA: Access reason required for PHI")

            elif level == ComplianceLevel.PCI_DSS:
                # Check for card data
                if 'credit_card' in data and not data.get('encrypted'):
                    violations.append("PCI-DSS: Credit card data must be encrypted")

        return len(violations) == 0, violations


# Test compliance features
if __name__ == "__main__":
    compliance = MCPCompliance()

    # Test GDPR consent
    print("\n=== Testing GDPR Consent ===")
    consent_id = compliance.record_consent("user123", "marketing", 180)
    print(f"Consent recorded: {consent_id}")
    print(f"Consent valid: {compliance.check_consent('user123', 'marketing')}")

    # Test data encryption
    print("\n=== Testing Encryption ===")
    sensitive_data = "SSN: 123-45-6789"
    encrypted = compliance.encrypt_data(sensitive_data, DataClassification.PII)
    print(f"Encrypted: {encrypted[:50]}...")
    decrypted = compliance.decrypt_data(encrypted)
    print(f"Decrypted: {decrypted}")

    # Test anonymization
    print("\n=== Testing Anonymization ===")
    user_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "age": 35,
        "zip_code": "12345"
    }
    anonymized = compliance.anonymize_data(user_data)
    print(f"Anonymized: {anonymized}")

    # Test compliance validation
    print("\n=== Testing Compliance Validation ===")
    test_data = {
        "user_id": "user123",
        "credit_card": "1234-5678-9012-3456",
        "encrypted": False
    }
    is_compliant, violations = compliance.validate_compliance(
        test_data,
        [ComplianceLevel.GDPR, ComplianceLevel.PCI_DSS]
    )
    print(f"Compliant: {is_compliant}")
    print(f"Violations: {violations}")

    # Generate compliance report
    print("\n=== Generating GDPR Report ===")
    report = compliance.generate_compliance_report(ComplianceLevel.GDPR)
    print(json.dumps(report, indent=2))