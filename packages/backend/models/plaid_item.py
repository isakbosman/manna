"""Plaid Item model for tracking Plaid connections."""

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, ForeignKey, Index,
    CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import Base, UUIDMixin, TimestampMixin


class PlaidItem(Base, UUIDMixin, TimestampMixin):
    """Plaid Item represents a user's connection to a financial institution."""
    
    __tablename__ = "plaid_items"
    
    # Ownership and institution
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    institution_id = Column(UUID(as_uuid=True), ForeignKey("institutions.id"), nullable=False, index=True)
    
    # Plaid identifiers
    plaid_item_id = Column(String(255), unique=True, nullable=False, index=True)
    plaid_access_token = Column(String(255), nullable=False)  # Encrypted in production
    
    # Connection status
    status = Column(String(20), default="active", nullable=False)  # active, error, expired, revoked
    error_code = Column(String(50))
    error_message = Column(Text)
    
    # Available products
    available_products = Column(JSONB, default=list)  # ['transactions', 'auth', 'identity', 'assets']
    billed_products = Column(JSONB, default=list)  # What we're being billed for
    
    # Connection metadata
    webhook_url = Column(String(500))
    consent_expiration_time = Column(DateTime(timezone=True))
    
    # Sync tracking
    last_successful_sync = Column(DateTime(timezone=True))
    last_sync_attempt = Column(DateTime(timezone=True))
    sync_cursor = Column(String(255))  # For incremental updates
    
    # Transaction sync settings
    max_days_back = Column(Integer, default=730)  # 2 years default
    sync_frequency_hours = Column(Integer, default=6)  # Sync every 6 hours
    
    # Status flags
    is_active = Column(Boolean, default=True, nullable=False)
    requires_reauth = Column(Boolean, default=False)
    has_mfa = Column(Boolean, default=False)
    
    # Metadata
    update_type = Column(String(20))  # background, user_present
    metadata = Column(JSONB, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="plaid_items")
    institution = relationship("Institution", back_populates="plaid_items")
    accounts = relationship("Account", back_populates="plaid_item", cascade="all, delete-orphan")
    webhooks = relationship("PlaidWebhook", back_populates="plaid_item", cascade="all, delete-orphan")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_plaid_items_user", "user_id", "is_active"),
        Index("idx_plaid_items_status", "status", "last_sync_attempt"),
        Index("idx_plaid_items_institution", "institution_id"),
        Index("idx_plaid_items_reauth", "requires_reauth", "is_active"),
        CheckConstraint(
            "status IN ('active', 'error', 'expired', 'revoked', 'pending')",
            name="ck_plaid_item_status"
        ),
        CheckConstraint(
            "max_days_back > 0 AND max_days_back <= 730",
            name="ck_max_days_back"
        ),
        CheckConstraint(
            "sync_frequency_hours >= 1 AND sync_frequency_hours <= 168",
            name="ck_sync_frequency"
        ),
    )
    
    @property
    def is_healthy(self) -> bool:
        """Check if item is in a healthy state."""
        return self.status == "active" and not self.requires_reauth and self.is_active
    
    @property
    def needs_attention(self) -> bool:
        """Check if item needs user attention."""
        return self.status in ("error", "expired") or self.requires_reauth
    
    @property
    def has_transactions_product(self) -> bool:
        """Check if item has transactions product enabled."""
        return "transactions" in (self.available_products or [])
    
    @property
    def days_since_last_sync(self) -> int:
        """Calculate days since last successful sync."""
        if not self.last_successful_sync:
            return 999  # Large number to indicate never synced
        
        from datetime import datetime
        delta = datetime.utcnow() - self.last_successful_sync
        return delta.days
    
    def mark_error(self, error_code: str, error_message: str) -> None:
        """Mark item as having an error."""
        self.status = "error"
        self.error_code = error_code
        self.error_message = error_message
        
        # Set reauth flag for certain errors
        reauth_errors = [
            "ITEM_LOGIN_REQUIRED",
            "ACCESS_NOT_GRANTED",
            "INSUFFICIENT_CREDENTIALS",
            "INVALID_CREDENTIALS",
            "ITEM_LOCKED"
        ]
        if error_code in reauth_errors:
            self.requires_reauth = True
    
    def mark_healthy(self) -> None:
        """Mark item as healthy and clear error state."""
        self.status = "active"
        self.error_code = None
        self.error_message = None
        self.requires_reauth = False
        
        from datetime import datetime
        self.last_successful_sync = datetime.utcnow()
    
    def __repr__(self):
        return (f"<PlaidItem(id={self.id}, plaid_item_id='{self.plaid_item_id}', "
                f"status='{self.status}', user_id={self.user_id})>")