"""Tax categorization models for financial transactions."""

from sqlalchemy import (
    Column, String, Boolean, Numeric, DateTime, Text, ForeignKey, Index,
    CheckConstraint, Integer, Date, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from decimal import Decimal
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from .base import Base, UUIDMixin, TimestampMixin


class ChartOfAccount(Base, UUIDMixin, TimestampMixin):
    """Chart of accounts for double-entry bookkeeping."""

    __tablename__ = "chart_of_accounts"

    # Basic account information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    account_code = Column(String(20), nullable=False, index=True)
    account_name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False)
    parent_account_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"))
    description = Column(Text)

    # Account properties
    normal_balance = Column(String(10), nullable=False)  # debit or credit
    is_active = Column(Boolean, nullable=False, default=True)
    is_system_account = Column(Boolean, nullable=False, default=False)
    current_balance = Column(Numeric(15, 2), default=Decimal("0.00"))

    # Tax-related fields
    tax_category = Column(String(100))
    tax_line_mapping = Column(String(100))  # Maps to specific tax form lines
    requires_1099 = Column(Boolean, default=False)

    # Additional metadata
    account_metadata = Column(JSONB, default=dict)

    # Relationships
    user = relationship("User", back_populates="chart_of_accounts")
    parent_account = relationship("ChartOfAccount", remote_side=[id])
    child_accounts = relationship("ChartOfAccount", back_populates="parent_account")
    transactions = relationship("Transaction", back_populates="chart_account")
    category_mappings = relationship("CategoryMapping", back_populates="chart_account")
    # journal_entry_lines = relationship("JournalEntryLine", back_populates="chart_account")

    # Constraints
    __table_args__ = (
        Index("idx_chart_of_accounts_code", "account_code"),
        Index("idx_chart_of_accounts_type", "account_type", "is_active"),
        Index("idx_chart_of_accounts_user", "user_id", "is_active"),
        Index("idx_chart_of_accounts_parent", "parent_account_id"),
        UniqueConstraint("user_id", "account_code", name="uq_user_account_code"),
        CheckConstraint(
            "account_type IN ('asset', 'liability', 'equity', 'revenue', 'expense', 'contra_asset', 'contra_liability', 'contra_equity')",
            name="ck_account_type"
        ),
        CheckConstraint(
            "normal_balance IN ('debit', 'credit')",
            name="ck_normal_balance"
        ),
    )

    @property
    def balance_decimal(self) -> Decimal:
        """Return current balance as Decimal."""
        return Decimal(str(self.current_balance)) if self.current_balance else Decimal("0.00")

    @property
    def full_account_name(self) -> str:
        """Return account code and name combined."""
        return f"{self.account_code} - {self.account_name}"

    def is_debit_account(self) -> bool:
        """Check if this is a debit-normal account."""
        return self.normal_balance == "debit"

    def is_credit_account(self) -> bool:
        """Check if this is a credit-normal account."""
        return self.normal_balance == "credit"

    def __repr__(self):
        return f"<ChartOfAccount(code='{self.account_code}', name='{self.account_name}', type='{self.account_type}')>"


class TaxCategory(Base, UUIDMixin, TimestampMixin):
    """IRS tax categories for business expense classification."""

    __tablename__ = "tax_categories"

    # Basic category information
    category_code = Column(String(20), nullable=False, unique=True, index=True)
    category_name = Column(String(255), nullable=False)
    tax_form = Column(String(50), nullable=False)  # Schedule C, Schedule E, etc.
    tax_line = Column(String(100))  # Specific line on tax form
    description = Column(Text)

    # Deduction properties
    deduction_type = Column(String(50))  # ordinary, capital, itemized, etc.
    percentage_limit = Column(Numeric(5, 2))  # e.g., 50% for meals
    dollar_limit = Column(Numeric(15, 2))  # Annual dollar limits
    carryover_allowed = Column(Boolean, default=False)
    documentation_required = Column(Boolean, default=False)

    # Classification
    is_business_expense = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    # Effective dates
    effective_date = Column(Date, nullable=False)
    expiration_date = Column(Date)

    # IRS references and automation
    irs_reference = Column(String(100))  # IRS publication or code reference
    keywords = Column(JSONB, default=list)  # Keywords for auto-categorization
    exclusions = Column(JSONB, default=list)  # Keywords that exclude this category
    special_rules = Column(JSONB, default=dict)  # Special calculation rules

    # Relationships
    transactions = relationship("Transaction", back_populates="tax_category")
    category_mappings = relationship("CategoryMapping", back_populates="tax_category")

    # Constraints
    __table_args__ = (
        Index("idx_tax_categories_code", "category_code"),
        Index("idx_tax_categories_form", "tax_form", "is_active"),
        Index("idx_tax_categories_business", "is_business_expense", "is_active"),
        Index("idx_tax_categories_effective", "effective_date", "expiration_date"),
        CheckConstraint(
            "deduction_type IN ('ordinary', 'capital', 'itemized', 'above_line', 'business')",
            name="ck_deduction_type"
        ),
        CheckConstraint(
            "tax_form IN ('Schedule C', 'Schedule E', 'Form 8829', 'Form 4562', 'Schedule A')",
            name="ck_tax_form"
        ),
    )

    def is_currently_effective(self) -> bool:
        """Check if category is currently effective."""
        today = date.today()
        if not self.is_active:
            return False
        if self.effective_date > today:
            return False
        if self.expiration_date and self.expiration_date < today:
            return False
        return True

    def calculate_deductible_amount(self, amount: Decimal, **kwargs) -> Decimal:
        """Calculate deductible amount based on category rules."""
        deductible = amount

        # Apply percentage limits
        if self.percentage_limit:
            limit_factor = self.percentage_limit / Decimal("100")
            deductible = min(deductible, amount * limit_factor)

        # Apply dollar limits (annual)
        if self.dollar_limit:
            # This would need to be calculated based on year-to-date totals
            # For now, just return the calculated amount
            pass

        return deductible

    def __repr__(self):
        return f"<TaxCategory(code='{self.category_code}', name='{self.category_name}', form='{self.tax_form}')>"


class BusinessExpenseTracking(Base, UUIDMixin, TimestampMixin):
    """Detailed tracking for business expense substantiation."""

    __tablename__ = "business_expense_tracking"

    # Core references
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Business purpose and percentage
    business_purpose = Column(Text)
    business_percentage = Column(Numeric(5, 2), default=Decimal("100.00"))

    # Receipt tracking
    receipt_required = Column(Boolean, default=False)
    receipt_attached = Column(Boolean, default=False)
    receipt_url = Column(String(500))

    # Mileage tracking (for vehicle expenses)
    mileage_start_location = Column(String(255))
    mileage_end_location = Column(String(255))
    miles_driven = Column(Numeric(8, 2))
    vehicle_info = Column(JSONB, default=dict)

    # Depreciation tracking
    depreciation_method = Column(String(50))  # straight_line, accelerated, etc.
    depreciation_years = Column(Integer)
    section_179_eligible = Column(Boolean, default=False)

    # Audit trail
    substantiation_notes = Column(Text)
    audit_trail = Column(JSONB, default=list)

    # Relationships
    transaction = relationship("Transaction", back_populates="business_expense_tracking")
    user = relationship("User", back_populates="business_expense_tracking")

    # Constraints
    __table_args__ = (
        Index("idx_business_expense_transaction", "transaction_id"),
        Index("idx_business_expense_user", "user_id"),
        Index("idx_business_expense_receipt", "receipt_required", "receipt_attached"),
        CheckConstraint(
            "business_percentage >= 0 AND business_percentage <= 100",
            name="ck_business_percentage"
        ),
        CheckConstraint(
            "miles_driven >= 0",
            name="ck_miles_positive"
        ),
        CheckConstraint(
            "depreciation_years > 0",
            name="ck_depreciation_years_positive"
        ),
    )

    @property
    def business_percentage_decimal(self) -> Decimal:
        """Return business percentage as decimal."""
        return Decimal(str(self.business_percentage)) if self.business_percentage else Decimal("100.00")

    def calculate_business_amount(self, total_amount: Decimal) -> Decimal:
        """Calculate the business portion of the expense."""
        percentage = self.business_percentage_decimal / Decimal("100")
        return total_amount * percentage

    def is_substantiation_complete(self) -> bool:
        """Check if substantiation requirements are met."""
        if self.receipt_required and not self.receipt_attached:
            return False
        if not self.business_purpose:
            return False
        return True

    def __repr__(self):
        return f"<BusinessExpenseTracking(transaction_id={self.transaction_id}, business_percentage={self.business_percentage})>"


class CategoryMapping(Base, UUIDMixin, TimestampMixin):
    """Mapping between transaction categories, chart of accounts, and tax categories."""

    __tablename__ = "category_mappings"

    # Core references
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    source_category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    chart_account_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=False)
    tax_category_id = Column(UUID(as_uuid=True), ForeignKey("tax_categories.id"), nullable=False)

    # Mapping properties
    confidence_score = Column(Numeric(5, 4), default=Decimal("1.0000"))
    is_user_defined = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    # Effective dates
    effective_date = Column(Date, nullable=False)
    expiration_date = Column(Date)

    # Default business expense settings
    business_percentage_default = Column(Numeric(5, 2), default=Decimal("100.00"))
    always_require_receipt = Column(Boolean, default=False)
    auto_substantiation_rules = Column(JSONB, default=dict)

    # Notes
    mapping_notes = Column(Text)

    # Relationships
    user = relationship("User", back_populates="category_mappings")
    source_category = relationship("Category", back_populates="category_mappings")
    chart_account = relationship("ChartOfAccount", back_populates="category_mappings")
    tax_category = relationship("TaxCategory", back_populates="category_mappings")

    # Constraints
    __table_args__ = (
        Index("idx_category_mappings_source", "source_category_id", "is_active"),
        Index("idx_category_mappings_user", "user_id", "is_active"),
        Index("idx_category_mappings_tax", "tax_category_id"),
        Index("idx_category_mappings_effective", "effective_date", "expiration_date"),
        UniqueConstraint("user_id", "source_category_id", "effective_date", name="uq_user_category_mapping"),
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="ck_confidence_score"
        ),
        CheckConstraint(
            "business_percentage_default >= 0 AND business_percentage_default <= 100",
            name="ck_default_business_percentage"
        ),
    )

    def is_currently_active(self) -> bool:
        """Check if mapping is currently active."""
        today = date.today()
        if not self.is_active:
            return False
        if self.effective_date > today:
            return False
        if self.expiration_date and self.expiration_date < today:
            return False
        return True

    @property
    def confidence_decimal(self) -> Decimal:
        """Return confidence score as decimal."""
        return Decimal(str(self.confidence_score)) if self.confidence_score else Decimal("1.0000")

    def __repr__(self):
        return f"<CategoryMapping(source_category_id={self.source_category_id}, tax_category={self.tax_category.category_code if self.tax_category else None})>"


class CategorizationAudit(Base, UUIDMixin):
    """Audit trail for all categorization changes."""

    __tablename__ = "categorization_audit"

    # Only created_at timestamp (immutable audit records)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Core references
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Action details
    action_type = Column(String(50), nullable=False)

    # Before/after states
    old_category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    new_category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    old_tax_category_id = Column(UUID(as_uuid=True), ForeignKey("tax_categories.id"))
    new_tax_category_id = Column(UUID(as_uuid=True), ForeignKey("tax_categories.id"))
    old_chart_account_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"))
    new_chart_account_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"))

    # Additional context
    reason = Column(String(255))
    confidence_before = Column(Numeric(5, 4))
    confidence_after = Column(Numeric(5, 4))
    automated = Column(Boolean, default=False)
    ml_model_version = Column(String(50))
    processing_time_ms = Column(Integer)
    audit_metadata = Column(JSONB, default=dict)

    # Relationships
    transaction = relationship("Transaction", back_populates="categorization_audits")
    user = relationship("User", back_populates="categorization_audits")
    old_category = relationship("Category", foreign_keys=[old_category_id])
    new_category = relationship("Category", foreign_keys=[new_category_id])
    old_tax_category = relationship("TaxCategory", foreign_keys=[old_tax_category_id])
    new_tax_category = relationship("TaxCategory", foreign_keys=[new_tax_category_id])
    old_chart_account = relationship("ChartOfAccount", foreign_keys=[old_chart_account_id])
    new_chart_account = relationship("ChartOfAccount", foreign_keys=[new_chart_account_id])

    # Constraints
    __table_args__ = (
        Index("idx_categorization_audit_transaction", "transaction_id"),
        Index("idx_categorization_audit_user", "user_id", "created_at"),
        Index("idx_categorization_audit_action", "action_type", "created_at"),
        Index("idx_categorization_audit_automated", "automated", "created_at"),
        CheckConstraint(
            "action_type IN ('categorize', 'recategorize', 'tax_categorize', 'chart_assign', 'bulk_update')",
            name="ck_action_type"
        ),
    )

    def __repr__(self):
        return f"<CategorizationAudit(transaction_id={self.transaction_id}, action='{self.action_type}', created_at='{self.created_at}')>"