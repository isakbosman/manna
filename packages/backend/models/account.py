"""Account model for linked financial accounts."""

from sqlalchemy import (
    Column, String, Boolean, Numeric, DateTime, Text, ForeignKey, Index,
    CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from decimal import Decimal
from .base import Base, UUIDMixin, TimestampMixin


class Account(Base, UUIDMixin, TimestampMixin):
    """Financial accounts linked via Plaid or manual entry."""
    
    __tablename__ = "accounts"
    
    # Ownership
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    institution_id = Column(UUID(as_uuid=True), ForeignKey("institutions.id"), nullable=True)
    plaid_item_id = Column(UUID(as_uuid=True), ForeignKey("plaid_items.id"), nullable=True)
    
    # Plaid identifiers
    plaid_account_id = Column(String(255), unique=True, index=True)
    plaid_persistent_id = Column(String(255), unique=True)
    
    # Account details
    name = Column(String(255), nullable=False)
    official_name = Column(String(255))
    account_type = Column(String(50), nullable=False)  # checking, savings, credit, investment, loan
    account_subtype = Column(String(50))  # detailed subtype from Plaid
    
    # Account classification
    is_business = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_manual = Column(Boolean, default=False, nullable=False)  # Manually entered account
    
    # Balance information (using Decimal for precision)
    current_balance = Column(Numeric(15, 2))
    available_balance = Column(Numeric(15, 2))
    credit_limit = Column(Numeric(15, 2))
    minimum_balance = Column(Numeric(15, 2))
    
    # Account numbers (encrypted)
    account_number_masked = Column(String(20))  # Last 4 digits
    routing_number = Column(String(20))
    
    # Status tracking
    last_sync = Column(DateTime(timezone=True))
    sync_status = Column(String(20), default="active")  # active, error, disconnected
    error_code = Column(String(50))
    error_message = Column(Text)
    
    # Metadata
    extra_data = Column(JSONB, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    institution = relationship("Institution", back_populates="accounts")
    plaid_item = relationship("PlaidItem", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        Index("idx_accounts_user_type", "user_id", "account_type"),
        Index("idx_accounts_sync_status", "sync_status", "last_sync"),
        Index("idx_accounts_business", "is_business", "is_active"),
        CheckConstraint(
            "account_type IN ('checking', 'savings', 'credit', 'investment', 'loan', 'other')",
            name="ck_account_type"
        ),
        CheckConstraint(
            "sync_status IN ('active', 'error', 'disconnected', 'pending')",
            name="ck_sync_status"
        ),
        UniqueConstraint("user_id", "name", name="uq_user_account_name"),
    )
    
    @property
    def balance_decimal(self) -> Decimal:
        """Return current balance as Decimal for precise calculations."""
        return Decimal(str(self.current_balance)) if self.current_balance else Decimal("0.00")
    
    @property
    def is_credit_account(self) -> bool:
        """Check if account is a credit account (balance decreases with spending)."""
        return self.account_type in ("credit", "loan")
    
    def __repr__(self):
        return f"<Account(id={self.id}, name='{self.name}', type='{self.account_type}')>"