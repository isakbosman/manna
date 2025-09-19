"""
Bookkeeping schemas for API request/response validation.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import date as date_type, datetime
from decimal import Decimal
from uuid import UUID


class JournalEntryLineCreate(BaseModel):
    """Schema for creating a journal entry line."""
    chart_account_id: Optional[UUID] = None
    debit_amount: Optional[Decimal] = Field(None, ge=0)
    credit_amount: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None
    transaction_id: Optional[UUID] = None
    tax_category_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class JournalEntryCreate(BaseModel):
    """Schema for creating a journal entry."""
    entry_date: Optional[date_type] = None
    description: str
    reference: Optional[str] = None
    journal_type: Optional[str] = None
    source_type: Optional[str] = None
    lines: List[JournalEntryLineCreate]

    model_config = ConfigDict(from_attributes=True)


class JournalEntryUpdate(BaseModel):
    """Schema for updating a journal entry."""
    description: Optional[str] = None
    reference: Optional[str] = None
    journal_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class JournalEntryResponse(BaseModel):
    """Response schema for journal entry."""
    id: UUID
    entry_number: str
    entry_date: date_type
    description: str
    total_debits: Decimal
    total_credits: Decimal
    is_posted: bool
    lines_count: int

    model_config = ConfigDict(from_attributes=True)


class AccountingPeriodResponse(BaseModel):
    """Response schema for accounting period."""
    id: UUID
    period_name: str
    period_type: str
    start_date: date_type
    end_date: date_type
    is_closed: bool
    closing_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ReconciliationStart(BaseModel):
    """Schema for starting reconciliation."""
    account_id: UUID
    reconciliation_date: Optional[date_type] = None
    statement_balance: Decimal

    model_config = ConfigDict(from_attributes=True)


class ReconciliationItemCreate(BaseModel):
    """Schema for creating reconciliation items."""
    transaction_id: Optional[UUID] = None
    statement_date: date_type
    statement_description: str
    statement_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class ReconciliationResponse(BaseModel):
    """Response schema for reconciliation."""
    id: UUID
    account_id: UUID
    account_name: str
    reconciliation_date: date_type
    statement_balance: Decimal
    book_balance: Decimal
    discrepancy_amount: Decimal
    status: str
    matched_count: int
    unmatched_count: int

    model_config = ConfigDict(from_attributes=True)


class BookkeepingHealthResponse(BaseModel):
    """Response schema for bookkeeping health."""
    status: Literal["current", "warning", "behind", "error"]
    current_period: Optional[str] = None
    unposted_entries: int
    unreconciled_accounts: int
    accuracy_score: float
    last_reconciliation_date: Optional[date_type] = None

    model_config = ConfigDict(from_attributes=True)


class PendingTaskResponse(BaseModel):
    """Schema for a pending task."""
    type: str
    title: str
    description: str
    priority: Literal["high", "medium", "low"]
    count: Optional[int] = None
    account_id: Optional[str] = None
    period_date: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PendingTasksResponse(BaseModel):
    """Response schema for pending tasks."""
    total_count: int
    tasks: List[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)


class BookkeepingRuleCreate(BaseModel):
    """Schema for creating a bookkeeping rule."""
    rule_name: str
    rule_type: str
    trigger_conditions: Dict[str, Any]
    journal_template: Optional[Dict[str, Any]] = None
    is_active: bool = True
    priority: int = 100

    model_config = ConfigDict(from_attributes=True)


class BookkeepingRuleResponse(BaseModel):
    """Response schema for bookkeeping rule."""
    id: UUID
    rule_name: str
    rule_type: str
    is_active: bool
    priority: int
    execution_count: int
    last_executed: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TransactionPatternResponse(BaseModel):
    """Response schema for transaction pattern."""
    id: UUID
    pattern_type: str
    confidence_score: float
    last_occurrence: Optional[date_type] = None
    next_expected: Optional[date_type] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)