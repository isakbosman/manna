"""
Bookkeeping models for double-entry accounting system.
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, Date, DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
import uuid

from .base import Base


class AccountingPeriod(Base):
    """Represents an accounting period (month, quarter, year) for financial closing."""
    __tablename__ = "accounting_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    period_name = Column(String(100), nullable=False)  # e.g., "2024-Q1", "January 2024"
    period_type = Column(String(20), nullable=False)  # month, quarter, year
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_closed = Column(Boolean, default=False)
    closing_date = Column(DateTime(timezone=True), nullable=True)
    closing_journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="accounting_periods")
    journal_entries = relationship("JournalEntry", back_populates="period", foreign_keys="[JournalEntry.period_id]")


class BookkeepingRule(Base):
    """Automation rules for bookkeeping entries."""
    __tablename__ = "bookkeeping_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rule_name = Column(String(255), nullable=False)
    rule_type = Column(String(50), nullable=False)  # categorization, journal_entry, accrual
    trigger_conditions = Column(JSONB, nullable=False)  # Transaction matching criteria
    journal_template = Column(JSONB, nullable=True)  # Template for journal entries
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)
    last_executed = Column(DateTime(timezone=True), nullable=True)
    execution_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="bookkeeping_rules")
    journal_entries = relationship("JournalEntry", back_populates="automation_rule")


class JournalEntry(Base):
    """Represents a journal entry in double-entry bookkeeping."""
    __tablename__ = "journal_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    entry_number = Column(String(50), unique=True, nullable=False)  # Sequential numbering
    entry_date = Column(Date, nullable=False)
    description = Column(Text, nullable=False)
    reference = Column(String(100), nullable=True)  # Invoice number, check number, etc.
    journal_type = Column(String(20), nullable=True)  # general, sales, purchase, cash_receipts, cash_disbursements
    total_debits = Column(Numeric(15, 2), nullable=False)
    total_credits = Column(Numeric(15, 2), nullable=False)
    is_balanced = Column(Boolean, default=True)
    is_posted = Column(Boolean, default=False)
    posting_date = Column(DateTime(timezone=True), nullable=True)
    period_id = Column(UUID(as_uuid=True), ForeignKey("accounting_periods.id"), nullable=True)
    source_type = Column(String(50), nullable=True)  # plaid_sync, manual, recurring, adjustment
    automation_rule_id = Column(UUID(as_uuid=True), ForeignKey("bookkeeping_rules.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="journal_entries")
    period = relationship("AccountingPeriod", back_populates="journal_entries", foreign_keys=[period_id])
    automation_rule = relationship("BookkeepingRule", back_populates="journal_entries")
    lines = relationship("JournalEntryLine", back_populates="journal_entry", cascade="all, delete-orphan")

    def validate_balance(self):
        """Ensure debits equal credits."""
        total_debits = sum(line.debit_amount or Decimal(0) for line in self.lines)
        total_credits = sum(line.credit_amount or Decimal(0) for line in self.lines)
        return total_debits == total_credits


class JournalEntryLine(Base):
    """Individual debit/credit lines in a journal entry."""
    __tablename__ = "journal_entry_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False)
    chart_account_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=True)
    debit_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    credit_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    description = Column(Text, nullable=True)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True)
    line_number = Column(Integer, nullable=False)
    tax_category_id = Column(UUID(as_uuid=True), ForeignKey("tax_categories.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    journal_entry = relationship("JournalEntry", back_populates="lines")
    # ChartOfAccount relationship will be added when models are properly integrated
    # chart_account = relationship("ChartOfAccount", back_populates="journal_entry_lines")
    transaction = relationship("Transaction", back_populates="journal_entry_lines")
    tax_category = relationship("TaxCategory", back_populates="journal_entry_lines")


class ReconciliationRecord(Base):
    """Bank reconciliation tracking."""
    __tablename__ = "reconciliation_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    reconciliation_date = Column(Date, nullable=False)
    statement_balance = Column(Numeric(15, 2), nullable=True)
    book_balance = Column(Numeric(15, 2), nullable=True)
    adjusted_balance = Column(Numeric(15, 2), nullable=True)
    status = Column(String(20), nullable=False)  # pending, reconciled, discrepancy
    reconciled_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    discrepancy_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    account = relationship("Account", back_populates="reconciliation_records")
    reconciled_by_user = relationship("User", back_populates="reconciliations_performed")
    items = relationship("ReconciliationItem", back_populates="reconciliation", cascade="all, delete-orphan")


class ReconciliationItem(Base):
    """Individual items in a reconciliation (for matching transactions)."""
    __tablename__ = "reconciliation_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reconciliation_id = Column(UUID(as_uuid=True), ForeignKey("reconciliation_records.id", ondelete="CASCADE"), nullable=False)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True)
    statement_date = Column(Date, nullable=False)
    statement_description = Column(String(255), nullable=True)
    statement_amount = Column(Numeric(15, 2), nullable=False)
    is_matched = Column(Boolean, default=False)
    match_confidence = Column(Numeric(5, 4), nullable=True)  # 0.0000 to 1.0000
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    reconciliation = relationship("ReconciliationRecord", back_populates="items")
    transaction = relationship("Transaction", back_populates="reconciliation_items")


class TransactionPattern(Base):
    """Patterns identified in transactions for ML and automation."""
    __tablename__ = "transaction_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pattern_type = Column(String(50), nullable=False)  # recurring, seasonal, anomaly
    pattern_data = Column(JSONB, nullable=False)  # Pattern details (merchant, amount range, frequency, etc.)
    confidence_score = Column(Numeric(5, 4), nullable=False)  # 0.0000 to 1.0000
    last_occurrence = Column(Date, nullable=True)
    next_expected = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="transaction_patterns")