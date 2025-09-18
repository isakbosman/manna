"""Audit log model for tracking system changes and user actions."""

from sqlalchemy import (
    Column, String, DateTime, Text, ForeignKey, Index, Integer, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from .base import Base, UUIDMixin, TimestampMixin


class AuditLog(Base, UUIDMixin, TimestampMixin):
    """Comprehensive audit trail for all system activities."""
    
    __tablename__ = "audit_logs"
    
    # Actor information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=True)
    
    # Action details
    action = Column(String(100), nullable=False, index=True)  # create, update, delete, login, etc.
    resource_type = Column(String(50), nullable=False, index=True)  # transaction, account, user, etc.
    resource_id = Column(String(100), index=True)  # ID of the affected resource
    
    # Change tracking
    old_values = Column(JSONB)  # Previous values for updates
    new_values = Column(JSONB)  # New values for creates/updates
    changes_summary = Column(Text)  # Human-readable summary of changes
    
    # Context information
    event_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    source = Column(String(50), default="web_app")  # web_app, api, background_job, webhook
    user_agent = Column(String(500))
    ip_address = Column(INET)
    
    # Request details
    request_id = Column(String(100), index=True)  # Trace requests across services
    endpoint = Column(String(200))  # API endpoint or page
    http_method = Column(String(10))
    status_code = Column(Integer)
    
    # Business context
    business_impact = Column(String(20), default="low")  # low, medium, high, critical
    compliance_relevant = Column(Boolean, default=False)  # Important for compliance
    financial_impact = Column(Boolean, default=False)  # Affects financial data
    
    # Additional metadata
    extra_data = Column(JSONB, default=dict)
    tags = Column(JSONB, default=list)  # Searchable tags
    
    # Error information
    error_code = Column(String(50))
    error_message = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    session = relationship("UserSession", back_populates="audit_logs")
    
    # Indexes for performance and querying
    __table_args__ = (
        Index("idx_audit_logs_user_time", "user_id", "event_timestamp"),
        Index("idx_audit_logs_action_resource", "action", "resource_type"),
        Index("idx_audit_logs_resource", "resource_type", "resource_id"),
        Index("idx_audit_logs_source_time", "source", "event_timestamp"),
        Index("idx_audit_logs_request", "request_id"),
        Index("idx_audit_logs_compliance", "compliance_relevant", "event_timestamp"),
        Index("idx_audit_logs_financial", "financial_impact", "event_timestamp"),
        Index("idx_audit_logs_business_impact", "business_impact", "event_timestamp"),
        Index("idx_audit_logs_ip", "ip_address"),
    )
    
    @classmethod
    def create_log(
        cls,
        action: str,
        resource_type: str,
        resource_id: str = None,
        user_id: UUID = None,
        old_values: dict = None,
        new_values: dict = None,
        business_impact: str = "low",
        compliance_relevant: bool = False,
        financial_impact: bool = False,
        source: str = "web_app",
        metadata: dict = None,
        **kwargs
    ) -> "AuditLog":
        """Factory method to create audit log entries."""
        from datetime import datetime
        
        # Generate changes summary if values provided
        changes_summary = None
        if old_values and new_values:
            changes = []
            for key, new_val in new_values.items():
                old_val = old_values.get(key)
                if old_val != new_val:
                    changes.append(f"{key}: {old_val} → {new_val}")
            changes_summary = "; ".join(changes) if changes else "No changes detected"
        
        return cls(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            changes_summary=changes_summary,
            event_timestamp=datetime.utcnow(),
            business_impact=business_impact,
            compliance_relevant=compliance_relevant,
            financial_impact=financial_impact,
            source=source,
            metadata=metadata or {},
            **kwargs
        )
    
    @property
    def is_high_impact(self) -> bool:
        """Check if this is a high-impact event."""
        return self.business_impact in ("high", "critical")
    
    @property
    def is_financial_event(self) -> bool:
        """Check if this event affects financial data."""
        return self.financial_impact or self.resource_type in (
            "transaction", "account", "budget", "report"
        )
    
    @property
    def is_security_event(self) -> bool:
        """Check if this is a security-related event."""
        security_actions = [
            "login", "logout", "failed_login", "password_change", 
            "account_locked", "permissions_changed", "api_key_created"
        ]
        return self.action in security_actions
    
    @property
    def formatted_timestamp(self) -> str:
        """Return formatted timestamp for display."""
        return self.event_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    def __repr__(self):
        return (f"<AuditLog(id={self.id}, action='{self.action}', "
                f"resource='{self.resource_type}', user_id={self.user_id})>")