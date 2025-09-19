"""
SQLAlchemy database models for Manna Financial Platform.
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, Text, JSON, Numeric, Index, UniqueConstraint
)
from decimal import Decimal
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
    logo_url = Column('logo', Text)  # Base64 encoded logo or URL
    primary_color = Column(String(7))  # Hex color code
    country_codes = Column('country_codes', JSON, default=list)
    products = Column('products', JSON, default=list)
    routing_numbers = Column('routing_numbers', JSON, default=list)
    is_active = Column('is_active', Boolean, default=True, nullable=False)
    oauth_required = Column('oauth_required', Boolean, default=False)
    institution_metadata = Column('metadata', JSON, default=dict)

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

    # Sync tracking
    cursor = Column(String(255))  # For transaction sync updates
    last_successful_sync = Column(DateTime(timezone=True))
    last_sync_attempt = Column(DateTime(timezone=True))

    # Status and error tracking
    status = Column(String(20), default="active", nullable=False)  # active, error, expired, revoked
    error_code = Column(String(50))
    error_message = Column(Text)
    requires_reauth = Column(Boolean, default=False)

    # Plaid metadata
    consent_expiration_time = Column(DateTime(timezone=True))
    webhook_url = Column(String(500))
    available_products = Column(Text)  # JSON array of available products
    billed_products = Column(Text)  # JSON array of billed products
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User", back_populates="plaid_items")
    institution = relationship("Institution", back_populates="plaid_items")
    accounts = relationship("Account", back_populates="plaid_item", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_plaid_items_user_active", "user_id", "is_active"),
        Index("idx_plaid_items_status", "status", "last_sync_attempt"),
        Index("idx_plaid_items_reauth", "requires_reauth", "is_active"),
    )

    @property
    def is_healthy(self) -> bool:
        """Check if item is in a healthy state."""
        return self.status == "active" and not self.requires_reauth and self.is_active

    @property
    def needs_attention(self) -> bool:
        """Check if item needs user attention."""
        return self.status in ("error", "expired") or self.requires_reauth

    def mark_error(self, error_code: str, error_message: str) -> None:
        """Mark item as having an error."""
        self.status = "error"
        self.error_code = error_code
        self.error_message = error_message[:1000] if error_message else None

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
        self.last_successful_sync = datetime.utcnow()

    def __repr__(self):
        return f"<PlaidItem(id={self.id}, status={self.status}, user_id={self.user_id})>"


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
    account_type = Column('account_type', String(50), nullable=False)  # depository, credit, loan, investment
    account_subtype = Column('account_subtype', String(50))  # checking, savings, credit card, etc.

    # Maintain backwards compatibility with property aliases
    @property
    def type(self):
        return self.account_type

    @type.setter
    def type(self, value):
        self.account_type = value

    @property
    def subtype(self):
        return self.account_subtype

    @subtype.setter
    def subtype(self, value):
        self.account_subtype = value

    @property
    def mask(self):
        return self.account_number_masked

    @mask.setter
    def mask(self, value):
        self.account_number_masked = value
    
    # Balances (using Numeric for precise decimal values)
    current_balance = Column('current_balance', Numeric(15, 2))
    available_balance = Column('available_balance', Numeric(15, 2))
    credit_limit = Column('credit_limit', Numeric(15, 2))  # For credit accounts
    minimum_balance = Column('minimum_balance', Numeric(15, 2))

    # Maintain backwards compatibility with cents properties
    @property
    def current_balance_cents(self):
        return int(self.current_balance * 100) if self.current_balance else 0

    @property
    def available_balance_cents(self):
        return int(self.available_balance * 100) if self.available_balance else 0

    @property
    def limit_cents(self):
        return int(self.credit_limit * 100) if self.credit_limit else None

    # Currency
    iso_currency_code = Column('iso_currency_code', String(3), default="USD")

    # Status
    is_business = Column('is_business', Boolean, default=False, nullable=False)
    is_active = Column('is_active', Boolean, default=True, nullable=False)
    is_manual = Column('is_manual', Boolean, default=False, nullable=False)

    # Sync status
    last_sync = Column('last_sync', DateTime(timezone=True))
    sync_status = Column('sync_status', String(20))
    error_code = Column('error_code', String(50))
    error_message = Column('error_message', Text)

    # Additional fields
    account_number_masked = Column('account_number_masked', String(20))
    routing_number = Column('routing_number', String(20))
    account_metadata = Column('metadata', JSON)

    # Compatibility property for is_hidden
    @property
    def is_hidden(self):
        return not self.is_active  # Treat inactive accounts as hidden

    @is_hidden.setter
    def is_hidden(self, value):
        if value:
            self.is_active = False
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    plaid_item = relationship("PlaidItem", back_populates="accounts")
    institution = relationship("Institution", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_account_user_active", "user_id", "is_active"),
        Index("idx_account_type", "account_type", "account_subtype"),
    )

    def __repr__(self):
        return f"<Account(id={self.id}, name={self.name}, type={self.type})>"


class Transaction(Base, TimestampMixin):
    """Financial transaction model."""
    __tablename__ = "transactions"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(), ForeignKey("accounts.id"), nullable=False)
    plaid_transaction_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Transaction details
    amount = Column('amount', Numeric(15, 2), nullable=False)
    iso_currency_code = Column(String(3), default="USD")
    date = Column(Date, nullable=False, index=True)
    datetime = Column(DateTime(timezone=True))
    authorized_date = Column(Date)
    authorized_datetime = Column(DateTime(timezone=True))

    # Backwards compatibility for amount_cents
    @property
    def amount_cents(self):
        return int(self.amount * 100) if self.amount else 0

    @amount_cents.setter
    def amount_cents(self, value):
        self.amount = Decimal(value) / 100 if value else 0
    
    # Description and merchant info
    name = Column(String(500), nullable=False)
    merchant_name = Column(String(255), index=True)
    original_description = Column(Text)
    
    # Categorization
    plaid_category = Column('plaid_category', JSON)  # Plaid categories as JSON array
    plaid_category_id = Column('plaid_category_id', String(50))
    category_id = Column('category_id', UUID(), ForeignKey("categories.id"))  # Reference to categories table
    subcategory = Column('subcategory', String(100))
    user_category_override = Column('user_category_override', String(100))  # User-defined override
    tax_category_id = Column('tax_category_id', UUID(), ForeignKey("tax_categories.id"))

    # Maintain backwards compatibility
    @property
    def primary_category(self):
        """Get primary category name from related category."""
        if self.category:
            return self.category.name
        return None

    @property
    def detailed_category(self):
        return self.subcategory

    @property
    def user_category(self):
        return self.user_category_override
    
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
    category = relationship("Category", backref="transactions")
    tax_category = relationship("TaxCategory", backref="transactions")
    ml_predictions = relationship("MLPrediction", back_populates="transaction", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_transaction_date_account", "date", "account_id"),
        Index("idx_transaction_pending", "pending"),
        Index("idx_transaction_category", "category_id", "subcategory"),
        Index("idx_transaction_merchant", "merchant_name"),
        Index("idx_transaction_reconciled", "is_reconciled"),
    )

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


class TaxCategory(Base, TimestampMixin):
    """Tax categories for IRS reporting."""
    __tablename__ = "tax_categories"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    category_code = Column(String(20), nullable=False, unique=True)
    category_name = Column(String(255), nullable=False)
    tax_form = Column(String(50), nullable=False)
    tax_line = Column(String(100))
    description = Column(Text)
    deduction_type = Column(String(50))
    percentage_limit = Column(Numeric(5, 2))
    is_business_expense = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    effective_date = Column(Date, nullable=False)

    def __repr__(self):
        return f"<TaxCategory(id={self.id}, code={self.category_code}, name={self.category_name})>"


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