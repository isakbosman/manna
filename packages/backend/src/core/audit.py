"""
Audit logging system for security and compliance tracking.

Records security-relevant events like authentication, authorization,
data access, and administrative actions.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Session

from ..config import settings

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"

    # Authorization events
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_ESCALATION = "permission_escalation"

    # Data access events
    DATA_READ = "data_read"
    DATA_CREATE = "data_create"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"

    # Security events
    ENCRYPTION_KEY_ROTATION = "encryption_key_rotation"
    SECURITY_CONFIGURATION_CHANGE = "security_config_change"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

    # Plaid/Financial events
    PLAID_ITEM_CONNECT = "plaid_item_connect"
    PLAID_ITEM_UPDATE = "plaid_item_update"
    PLAID_ITEM_DISCONNECT = "plaid_item_disconnect"
    PLAID_SYNC_START = "plaid_sync_start"
    PLAID_SYNC_COMPLETE = "plaid_sync_complete"
    PLAID_SYNC_ERROR = "plaid_sync_error"

    # Administrative events
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_ROLE_CHANGE = "user_role_change"

    # System events
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    DATABASE_MIGRATION = "database_migration"
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditContext:
    """Context information for audit events."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None


@dataclass
class AuditEvent:
    """Structured audit event data."""
    event_type: AuditEventType
    severity: AuditSeverity
    message: str
    context: AuditContext
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    success: bool = True
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class AuditLogger:
    """
    Centralized audit logging system.

    Handles structured logging of security and compliance events
    with multiple output destinations.
    """

    def __init__(self):
        self.structured_logger = self._setup_structured_logger()
        self.enabled = settings.audit_logging_enabled

    def _setup_structured_logger(self) -> logging.Logger:
        """Set up structured logging for audit events."""
        audit_logger = logging.getLogger("manna.audit")
        audit_logger.setLevel(logging.INFO)

        # Create structured formatter
        formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(levelname)s - %(message)s'
        )

        # Add console handler for development
        if not audit_logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            audit_logger.addHandler(console_handler)

            # Add file handler for production
            if settings.environment == "production":
                try:
                    file_handler = logging.FileHandler("/var/log/manna/audit.log")
                    file_handler.setFormatter(formatter)
                    audit_logger.addHandler(file_handler)
                except Exception as e:
                    logger.warning(f"Could not set up audit file logging: {e}")

        return audit_logger

    def log_event(
        self,
        event_type: AuditEventType,
        message: str,
        context: Optional[AuditContext] = None,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log an audit event.

        Args:
            event_type: Type of event
            message: Human-readable message
            context: Request/user context
            severity: Event severity
            metadata: Additional structured data
            success: Whether the event was successful
            error_message: Error details if unsuccessful
        """
        if not self.enabled:
            return

        if context is None:
            context = AuditContext()

        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            message=message,
            context=context,
            metadata=metadata or {},
            success=success,
            error_message=error_message
        )

        self._write_audit_log(event)

    def _write_audit_log(self, event: AuditEvent) -> None:
        """Write audit event to configured destinations."""
        try:
            # Create structured log data
            log_data = {
                "event_type": event.event_type.value,
                "severity": event.severity.value,
                "message": event.message,
                "success": event.success,
                "timestamp": event.timestamp.isoformat(),
                "context": asdict(event.context),
                "metadata": event.metadata or {}
            }

            if event.error_message:
                log_data["error_message"] = event.error_message

            # Log as structured JSON
            log_message = json.dumps(log_data, ensure_ascii=False)

            # Choose log level based on severity
            if event.severity == AuditSeverity.CRITICAL:
                self.structured_logger.critical(log_message)
            elif event.severity == AuditSeverity.HIGH:
                self.structured_logger.error(log_message)
            elif event.severity == AuditSeverity.MEDIUM:
                self.structured_logger.warning(log_message)
            else:
                self.structured_logger.info(log_message)

            # TODO: Send to external audit systems (SIEM, etc.)
            # self._send_to_siem(log_data)

        except Exception as e:
            # Audit logging should never break the application
            logger.error(f"Failed to write audit log: {e}")

    def log_authentication_success(
        self,
        user_id: str,
        context: Optional[AuditContext] = None
    ) -> None:
        """Log successful authentication."""
        self.log_event(
            AuditEventType.LOGIN_SUCCESS,
            f"User {user_id} successfully authenticated",
            context,
            AuditSeverity.LOW,
            {"user_id": user_id}
        )

    def log_authentication_failure(
        self,
        username: Optional[str],
        reason: str,
        context: Optional[AuditContext] = None
    ) -> None:
        """Log failed authentication attempt."""
        self.log_event(
            AuditEventType.LOGIN_FAILURE,
            f"Authentication failed for {username or 'unknown'}: {reason}",
            context,
            AuditSeverity.MEDIUM,
            {"username": username, "failure_reason": reason},
            success=False,
            error_message=reason
        )

    def log_access_denied(
        self,
        resource: str,
        action: str,
        context: Optional[AuditContext] = None,
        reason: Optional[str] = None
    ) -> None:
        """Log access denial."""
        message = f"Access denied to {resource} for action {action}"
        if reason:
            message += f": {reason}"

        self.log_event(
            AuditEventType.ACCESS_DENIED,
            message,
            context,
            AuditSeverity.MEDIUM,
            {"resource": resource, "action": action, "reason": reason},
            success=False
        )

    def log_data_access(
        self,
        operation: str,
        resource: str,
        resource_id: Optional[str] = None,
        context: Optional[AuditContext] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log data access events."""
        event_types = {
            "read": AuditEventType.DATA_READ,
            "create": AuditEventType.DATA_CREATE,
            "update": AuditEventType.DATA_UPDATE,
            "delete": AuditEventType.DATA_DELETE,
        }

        event_type = event_types.get(operation.lower(), AuditEventType.DATA_READ)
        severity = AuditSeverity.HIGH if operation.lower() == "delete" else AuditSeverity.LOW

        log_metadata = {"resource": resource, "operation": operation}
        if resource_id:
            log_metadata["resource_id"] = resource_id
        if metadata:
            log_metadata.update(metadata)

        self.log_event(
            event_type,
            f"Data {operation} on {resource}" + (f" ({resource_id})" if resource_id else ""),
            context,
            severity,
            log_metadata
        )

    def log_plaid_event(
        self,
        event_type: AuditEventType,
        plaid_item_id: str,
        message: str,
        context: Optional[AuditContext] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log Plaid-related events."""
        log_metadata = {"plaid_item_id": plaid_item_id}
        if metadata:
            log_metadata.update(metadata)

        severity = AuditSeverity.LOW if success else AuditSeverity.MEDIUM

        self.log_event(
            event_type,
            message,
            context,
            severity,
            log_metadata,
            success,
            error_message
        )

    def log_security_event(
        self,
        event_type: AuditEventType,
        message: str,
        context: Optional[AuditContext] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log security-related events."""
        self.log_event(
            event_type,
            message,
            context,
            AuditSeverity.HIGH,
            metadata
        )


# Global audit logger instance
audit_logger = AuditLogger()


# Convenience functions
def log_audit_event(
    event_type: AuditEventType,
    message: str,
    context: Optional[AuditContext] = None,
    **kwargs
) -> None:
    """Log an audit event using the global logger."""
    audit_logger.log_event(event_type, message, context, **kwargs)


def create_audit_context(
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    **kwargs
) -> AuditContext:
    """Create an audit context from common parameters."""
    return AuditContext(
        user_id=user_id,
        request_id=request_id,
        ip_address=ip_address,
        **kwargs
    )


def log_login_success(user_id: str, **context_kwargs) -> None:
    """Log successful login."""
    context = create_audit_context(user_id=user_id, **context_kwargs)
    audit_logger.log_authentication_success(user_id, context)


def log_login_failure(username: Optional[str], reason: str, **context_kwargs) -> None:
    """Log failed login attempt."""
    context = create_audit_context(**context_kwargs)
    audit_logger.log_authentication_failure(username, reason, context)


def log_access_denied(resource: str, action: str, **context_kwargs) -> None:
    """Log access denial."""
    context = create_audit_context(**context_kwargs)
    audit_logger.log_access_denied(resource, action, context)


def log_data_change(operation: str, resource: str, resource_id: str = None, **context_kwargs) -> None:
    """Log data modification."""
    context = create_audit_context(**context_kwargs)
    audit_logger.log_data_access(operation, resource, resource_id, context)