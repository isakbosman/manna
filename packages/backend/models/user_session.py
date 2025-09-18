"""User session model for tracking active user sessions."""

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, ForeignKey, Index,
    CheckConstraint, Integer
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from .base import Base, UUIDMixin, TimestampMixin


class UserSession(Base, UUIDMixin, TimestampMixin):
    """Active user sessions for authentication and tracking."""
    
    __tablename__ = "user_sessions"
    
    # User association
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Session details
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True)
    
    # Session metadata
    device_info = Column(JSONB, default=dict)  # Device fingerprint, type, etc.
    user_agent = Column(String(500))
    ip_address = Column(INET, index=True)
    location_info = Column(JSONB)  # City, country, etc. from IP
    
    # Session timing
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    last_activity = Column(DateTime(timezone=True), nullable=False, index=True)
    login_time = Column(DateTime(timezone=True), nullable=False)
    
    # Session status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    logout_time = Column(DateTime(timezone=True))
    logout_reason = Column(String(50))  # user_logout, timeout, security, admin
    
    # Security flags
    is_suspicious = Column(Boolean, default=False)
    risk_score = Column(Integer, default=0)  # 0-100 risk assessment
    requires_mfa = Column(Boolean, default=False)
    mfa_verified = Column(Boolean, default=False)
    
    # Session type and source
    session_type = Column(String(20), default="web")  # web, mobile, api, background
    login_method = Column(String(50))  # password, oauth, sso, api_key
    
    # Additional metadata
    extra_data = Column(JSONB, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="user_sessions")
    audit_logs = relationship("AuditLog", back_populates="session")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_sessions_user_active", "user_id", "is_active"),
        Index("idx_sessions_expires", "expires_at", "is_active"),
        Index("idx_sessions_activity", "last_activity", "is_active"),
        Index("idx_sessions_ip", "ip_address"),
        Index("idx_sessions_suspicious", "is_suspicious", "risk_score"),
        Index("idx_sessions_type", "session_type", "login_method"),
        Index("idx_sessions_mfa", "requires_mfa", "mfa_verified"),
        CheckConstraint(
            "logout_reason IN ('user_logout', 'timeout', 'security', 'admin', 'expired')",
            name="ck_logout_reason"
        ),
        CheckConstraint(
            "session_type IN ('web', 'mobile', 'api', 'background')",
            name="ck_session_type"
        ),
        CheckConstraint(
            "risk_score >= 0 AND risk_score <= 100",
            name="ck_risk_score_range"
        ),
        CheckConstraint(
            "expires_at > created_at",
            name="ck_valid_expiry"
        ),
    )
    
    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        from datetime import datetime
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if session is currently valid."""
        return self.is_active and not self.is_expired
    
    @property
    def is_recent_activity(self) -> bool:
        """Check if there was recent activity (within last 5 minutes)."""
        from datetime import datetime, timedelta
        return (datetime.utcnow() - self.last_activity) < timedelta(minutes=5)
    
    @property
    def session_duration(self) -> int:
        """Get session duration in minutes."""
        end_time = self.logout_time or datetime.utcnow()
        return int((end_time - self.login_time).total_seconds() / 60)
    
    @property
    def time_until_expiry(self) -> int:
        """Get minutes until session expires."""
        from datetime import datetime
        if self.is_expired:
            return 0
        return int((self.expires_at - datetime.utcnow()).total_seconds() / 60)
    
    @property
    def is_high_risk(self) -> bool:
        """Check if session is high risk."""
        return self.risk_score >= 70 or self.is_suspicious
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        from datetime import datetime
        self.last_activity = datetime.utcnow()
    
    def extend_session(self, minutes: int = 60) -> None:
        """Extend session expiry time."""
        from datetime import datetime, timedelta
        self.expires_at = datetime.utcnow() + timedelta(minutes=minutes)
        self.update_activity()
    
    def terminate_session(self, reason: str = "user_logout") -> None:
        """Terminate the session."""
        from datetime import datetime
        self.is_active = False
        self.logout_time = datetime.utcnow()
        self.logout_reason = reason
    
    def flag_suspicious(self, risk_increase: int = 20) -> None:
        """Flag session as suspicious and increase risk score."""
        self.is_suspicious = True
        self.risk_score = min(100, self.risk_score + risk_increase)
    
    def generate_tokens(self) -> tuple[str, str]:
        """Generate new session and refresh tokens."""
        import secrets
        
        self.session_token = secrets.token_urlsafe(32)
        self.refresh_token = secrets.token_urlsafe(32)
        
        return self.session_token, self.refresh_token
    
    def __repr__(self):
        return (f"<UserSession(id={self.id}, user_id={self.user_id}, "
                f"active={self.is_active}, expires={self.expires_at})>")