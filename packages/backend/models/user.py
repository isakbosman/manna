"""User model for authentication and profile management."""

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from .base import Base, UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    """User accounts with authentication and profile data."""
    
    __tablename__ = "users"
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime(timezone=True))
    
    # Profile
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    timezone = Column(String(50), default="UTC")
    
    # Business profile
    business_name = Column(String(255))
    business_type = Column(String(100))  # sole_prop, llc, corp, etc.
    tax_id = Column(String(20))  # EIN or SSN (encrypted)
    business_address = Column(JSONB)
    
    # Preferences
    preferences = Column(JSONB, default=dict)
    notification_settings = Column(JSONB, default=dict)
    
    # Security
    last_login = Column(DateTime(timezone=True))
    failed_login_attempts = Column(String(10), default="0")
    account_locked_until = Column(DateTime(timezone=True))
    password_reset_token = Column(String(255))
    password_reset_expires = Column(DateTime(timezone=True))
    
    # Relationships
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    plaid_items = relationship("PlaidItem", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    user_sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

    # Tax categorization relationships
    chart_of_accounts = relationship("ChartOfAccount", back_populates="user", cascade="all, delete-orphan")
    category_mappings = relationship("CategoryMapping", back_populates="user", cascade="all, delete-orphan")
    business_expense_tracking = relationship("BusinessExpenseTracking", back_populates="user", cascade="all, delete-orphan")
    categorization_audits = relationship("CategorizationAudit", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_users_email_active", "email", "is_active"),
        Index("idx_users_last_login", "last_login"),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"