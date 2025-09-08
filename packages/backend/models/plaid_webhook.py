"""Plaid webhook model for tracking webhook events."""

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, ForeignKey, Index,
    CheckConstraint, Integer
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import Base, UUIDMixin, TimestampMixin


class PlaidWebhook(Base, UUIDMixin, TimestampMixin):
    """Plaid webhook events for real-time updates."""
    
    __tablename__ = "plaid_webhooks"
    
    # Links
    plaid_item_id = Column(UUID(as_uuid=True), ForeignKey("plaid_items.id"), nullable=True, index=True)
    
    # Webhook details
    webhook_type = Column(String(50), nullable=False)  # TRANSACTIONS, AUTH, etc.
    webhook_code = Column(String(50), nullable=False)  # INITIAL_UPDATE, HISTORICAL_UPDATE, etc.
    
    # Plaid identifiers
    plaid_item_id_raw = Column(String(255), index=True)  # Raw Plaid item ID from webhook
    plaid_environment = Column(String(20), default="production")  # sandbox, development, production
    
    # Event data
    event_data = Column(JSONB, nullable=False)  # Full webhook payload
    new_transactions = Column(Integer, default=0)
    modified_transactions = Column(Integer, default=0)
    removed_transactions = Column(Integer, default=0)
    
    # Processing status
    processing_status = Column(String(20), default="pending")  # pending, processing, completed, failed
    processed_at = Column(DateTime(timezone=True))
    processing_duration_ms = Column(Integer)
    
    # Error handling
    error_code = Column(String(50))
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Webhook metadata
    received_at = Column(DateTime(timezone=True), nullable=False)
    user_agent = Column(String(500))
    source_ip = Column(String(45))  # IPv4 or IPv6
    
    # Deduplication
    webhook_hash = Column(String(64), unique=True, index=True)  # SHA-256 of key fields
    is_duplicate = Column(Boolean, default=False)
    original_webhook_id = Column(UUID(as_uuid=True), ForeignKey("plaid_webhooks.id"))
    
    # Relationships
    plaid_item = relationship("PlaidItem", back_populates="webhooks")
    original_webhook = relationship("PlaidWebhook", remote_side=[id])
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_webhooks_item", "plaid_item_id", "received_at"),
        Index("idx_webhooks_type_code", "webhook_type", "webhook_code"),
        Index("idx_webhooks_status", "processing_status", "received_at"),
        Index("idx_webhooks_retry", "retry_count", "processing_status"),
        Index("idx_webhooks_environment", "plaid_environment"),
        Index("idx_webhooks_duplicate", "is_duplicate", "webhook_hash"),
        CheckConstraint(
            "webhook_type IN ('TRANSACTIONS', 'AUTH', 'IDENTITY', 'ASSETS', 'HOLDINGS', 'ITEM', 'INCOME', 'LIABILITIES')",
            name="ck_webhook_type"
        ),
        CheckConstraint(
            "processing_status IN ('pending', 'processing', 'completed', 'failed', 'ignored')",
            name="ck_processing_status"
        ),
        CheckConstraint(
            "plaid_environment IN ('sandbox', 'development', 'production')",
            name="ck_plaid_environment"
        ),
        CheckConstraint(
            "retry_count >= 0 AND retry_count <= max_retries",
            name="ck_retry_count"
        ),
    )
    
    @property
    def can_retry(self) -> bool:
        """Check if webhook can be retried."""
        return (self.processing_status == "failed" and 
                self.retry_count < self.max_retries)
    
    @property
    def is_transaction_update(self) -> bool:
        """Check if webhook is a transaction update."""
        return self.webhook_type == "TRANSACTIONS"
    
    @property
    def has_new_data(self) -> bool:
        """Check if webhook contains new transaction data."""
        return (self.new_transactions > 0 or 
                self.modified_transactions > 0 or 
                self.removed_transactions > 0)
    
    @property
    def total_transaction_changes(self) -> int:
        """Get total number of transaction changes."""
        return (self.new_transactions + 
                self.modified_transactions + 
                self.removed_transactions)
    
    def mark_processing(self) -> None:
        """Mark webhook as currently being processed."""
        self.processing_status = "processing"
        from datetime import datetime
        self.processed_at = datetime.utcnow()
    
    def mark_completed(self, duration_ms: int = None) -> None:
        """Mark webhook as successfully processed."""
        self.processing_status = "completed"
        if duration_ms:
            self.processing_duration_ms = duration_ms
        
        from datetime import datetime
        if not self.processed_at:
            self.processed_at = datetime.utcnow()
    
    def mark_failed(self, error_code: str, error_message: str) -> None:
        """Mark webhook as failed and increment retry count."""
        self.processing_status = "failed"
        self.error_code = error_code
        self.error_message = error_message
        self.retry_count += 1
        
        from datetime import datetime
        if not self.processed_at:
            self.processed_at = datetime.utcnow()
    
    def generate_hash(self) -> str:
        """Generate SHA-256 hash for deduplication."""
        import hashlib
        import json
        
        # Create hash from key identifying fields
        hash_data = {
            "webhook_type": self.webhook_type,
            "webhook_code": self.webhook_code,
            "plaid_item_id": self.plaid_item_id_raw,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "new_transactions": self.new_transactions,
            "modified_transactions": self.modified_transactions,
            "removed_transactions": self.removed_transactions
        }
        
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def __repr__(self):
        return (f"<PlaidWebhook(id={self.id}, type='{self.webhook_type}', "
                f"code='{self.webhook_code}', status='{self.processing_status}')>")