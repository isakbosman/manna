"""
SQLAlchemy database models for Manna Financial Platform.
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, Text, JSON, Numeric, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy import TypeDecorator, String
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import uuid
from datetime import datetime
import re

from .base import Base


class UUID(TypeDecorator):
    """Platform-independent UUID type.
    
    Uses PostgreSQL's native UUID type when possible,
    otherwise uses String(36) for other databases like SQLite.
    """
    impl = String
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQLUUID())
        else:
            return dialect.type_descriptor(String(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value
        return str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value
        return uuid.UUID(value)


class TimestampMixin:
    """Mixin for adding created_at and updated_at timestamps."""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class User(Base, TimestampMixin):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    plaid_items = relationship("PlaidItem", back_populates="user", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    
    @validates("email")
    def validate_email(self, key, email):
        """Validate email format."""
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email address")
        return email.lower()
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Institution(Base, TimestampMixin):
    """Financial institution model."""
    __tablename__ = "institutions"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    plaid_institution_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500))
    logo_url = Column(Text)  # Base64 encoded logo or URL
    primary_color = Column(String(7))  # Hex color code
    
    # Relationships
    plaid_items = relationship("PlaidItem", back_populates="institution")
    accounts = relationship("Account", back_populates="institution")
    
    def __repr__(self):
        return f"<Institution(id={self.id}, name={self.name})>"


class PlaidItem(Base, TimestampMixin):
    """Plaid Item representing a user's connection to a financial institution."""
    __tablename__ = "plaid_items"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    institution_id = Column(UUID(), ForeignKey("institutions.id"), nullable=True)
    plaid_item_id = Column(String(255), unique=True, nullable=False, index=True)
    access_token = Column(Text, nullable=False)  # Should be encrypted in production
    cursor = Column(String(255))  # For transaction updates
    consent_expiration_time = Column(DateTime(timezone=True))
    last_successful_sync = Column(DateTime(timezone=True))
    last_failed_sync = Column(DateTime(timezone=True))
    error = Column(Text)  # JSON error details
    webhook_url = Column(String(500))
    available_products = Column(Text)  # JSON array of available products
    billed_products = Column(Text)  # JSON array of billed products
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="plaid_items")
    institution = relationship("Institution", back_populates="plaid_items")
    accounts = relationship("Account", back_populates="plaid_item", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PlaidItem(id={self.id}, user_id={self.user_id})>"


class Account(Base, TimestampMixin):
    """Financial account model."""
    __tablename__ = "accounts"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    plaid_item_id = Column(UUID(), ForeignKey("plaid_items.id"), nullable=False)
    institution_id = Column(UUID(), ForeignKey("institutions.id"), nullable=True)
    plaid_account_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Account information
    name = Column(String(255), nullable=False)
    official_name = Column(String(255))
    type = Column(String(50), nullable=False)  # depository, credit, loan, investment
    subtype = Column(String(50))  # checking, savings, credit card, etc.
    mask = Column(String(10))  # Last 4 digits of account number
    
    # Balances (stored as cents to avoid floating point issues)
    current_balance_cents = Column(Integer)
    available_balance_cents = Column(Integer)
    limit_cents = Column(Integer)  # For credit accounts
    iso_currency_code = Column(String(3), default="USD")
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_hidden = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    plaid_item = relationship("PlaidItem", back_populates="accounts")
    institution = relationship("Institution", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_account_user_active", "user_id", "is_active"),
        Index("idx_account_type", "type", "subtype"),
    )
    
    @property
    def current_balance(self):
        """Get current balance in dollars."""
        return self.current_balance_cents / 100 if self.current_balance_cents else 0
    
    @property
    def available_balance(self):
        """Get available balance in dollars."""
        return self.available_balance_cents / 100 if self.available_balance_cents else 0
    
    def __repr__(self):
        return f"<Account(id={self.id}, name={self.name}, type={self.type})>"


class Transaction(Base, TimestampMixin):
    """Financial transaction model."""
    __tablename__ = "transactions"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(), ForeignKey("accounts.id"), nullable=False)
    plaid_transaction_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Transaction details
    amount_cents = Column(Integer, nullable=False)  # Stored as cents
    iso_currency_code = Column(String(3), default="USD")
    date = Column(Date, nullable=False, index=True)
    datetime = Column(DateTime(timezone=True))
    authorized_date = Column(Date)
    authorized_datetime = Column(DateTime(timezone=True))
    
    # Description and merchant info
    name = Column(String(500), nullable=False)
    merchant_name = Column(String(255), index=True)
    original_description = Column(Text)
    
    # Categorization
    category = Column(JSON)  # Plaid categories as JSON array
    category_id = Column(String(50), index=True)
    primary_category = Column(String(100), index=True)
    detailed_category = Column(String(100))
    confidence_level = Column(Float)  # ML confidence score
    user_category = Column(String(100))  # User-defined override
    
    # Transaction type and status
    pending = Column(Boolean, default=False, nullable=False)
    pending_transaction_id = Column(String(255))
    payment_channel = Column(String(50))  # online, in store, other
    transaction_type = Column(String(50))  # place, special, digital, unresolved
    transaction_code = Column(String(50))
    
    # Location data
    location = Column(JSON)  # Store location info as JSON
    
    # Additional metadata
    account_owner = Column(String(255))
    logo_url = Column(Text)
    website = Column(String(500))
    payment_meta = Column(JSON)
    
    # Accounting fields
    is_reconciled = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)
    tags = Column(JSON)  # Array of tags
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    ml_predictions = relationship("MLPrediction", back_populates="transaction", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_transaction_date_account", "date", "account_id"),
        Index("idx_transaction_pending", "pending"),
        Index("idx_transaction_category", "primary_category", "detailed_category"),
        Index("idx_transaction_merchant", "merchant_name"),
        Index("idx_transaction_reconciled", "is_reconciled"),
    )
    
    @property
    def amount(self):
        """Get amount in dollars."""
        return self.amount_cents / 100 if self.amount_cents else 0
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, name={self.name}, amount={self.amount})>"


class Category(Base, TimestampMixin):
    """Custom transaction categories for ML training and user preferences."""
    __tablename__ = "categories"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=True)  # Null for system categories
    name = Column(String(100), nullable=False)
    parent_category = Column(String(100))
    description = Column(Text)
    color = Column(String(7))  # Hex color code
    icon = Column(String(50))  # Icon name or emoji
    is_system = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    rules = Column(JSON)  # Matching rules for auto-categorization
    
    # Unique constraint on name per user
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_category"),
    )

    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name})>"


class MLPrediction(Base, TimestampMixin):
    """Model for storing ML categorization predictions."""
    __tablename__ = "ml_predictions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(UUID, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    confidence = Column(Float, nullable=False)
    model_version = Column(String, nullable=True)
    prediction_data = Column(JSON, nullable=True)  # Store additional prediction metadata
    user_feedback = Column(Boolean, nullable=True)  # True if correct, False if incorrect, None if no feedback

    # Relationships
    transaction = relationship("Transaction", back_populates="ml_predictions")
    category = relationship("Category")

    def __repr__(self):
        return f"<MLPrediction(id={self.id}, transaction_id={self.transaction_id}, confidence={self.confidence})>"


class CategorizationRule(Base, TimestampMixin):
    """Model for storing categorization rules."""
    __tablename__ = "categorization_rules"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(UUID, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    rule_type = Column(String, nullable=False)  # keyword, regex, amount, compound
    pattern = Column(String, nullable=False)
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    conditions = Column(JSON, nullable=True)  # Store complex rule conditions
    statistics = Column(JSON, nullable=True)  # Track rule performance

    # Relationships
    user = relationship("User")
    category = relationship("Category")

    def __repr__(self):
        return f"<CategorizationRule(id={self.id}, name={self.name}, rule_type={self.rule_type})>"