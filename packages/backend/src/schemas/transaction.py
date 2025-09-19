"""
Transaction schemas for API request/response validation.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict, computed_field
from typing import Optional, List, Dict, Any, Literal
from datetime import date as date_type, datetime
from uuid import UUID


class TransactionBase(BaseModel):
    """Base transaction schema."""
    name: str = Field(..., description="Transaction description")
    merchant_name: Optional[str] = Field(None, description="Merchant name")
    amount: float = Field(..., description="Transaction amount")
    date: date_type = Field(..., description="Transaction date")
    pending: bool = Field(False, description="Whether transaction is pending")
    
    model_config = ConfigDict(from_attributes=True)


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction."""
    account_id: UUID = Field(..., description="Account ID")
    category: Optional[str] = Field(None, description="Transaction category")
    notes: Optional[str] = Field(None, description="Transaction notes")
    tags: Optional[List[str]] = Field(default_factory=list, description="Transaction tags")


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""
    name: Optional[str] = None
    merchant_name: Optional[str] = None
    amount: Optional[float] = None
    user_category: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    is_reconciled: Optional[bool] = None
    
    model_config = ConfigDict(from_attributes=True)


class Transaction(TransactionBase):
    """Complete transaction schema for responses."""
    id: UUID
    account_id: UUID
    plaid_transaction_id: str
    iso_currency_code: str = "USD"
    original_description: Optional[str] = None
    
    # Categorization
    plaid_category: Optional[List[str]] = Field(None, alias="plaid_categories")
    primary_category: Optional[str] = None
    detailed_category: Optional[str] = None
    user_category: Optional[str] = None
    confidence_level: Optional[float] = None

    # Add category field that frontend expects (use detailed_category or user_category)
    @computed_field
    @property
    def category(self) -> Optional[str]:
        """Return category for frontend compatibility."""
        return self.user_category or self.detailed_category or None

    # Add description alias for name (frontend expects 'description')
    @computed_field
    @property
    def description(self) -> str:
        """Return description for frontend compatibility."""
        return self.name

    # Status
    is_reconciled: bool = False
    pending_transaction_id: Optional[str] = None
    
    # Metadata
    payment_channel: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    @property
    def display_category(self) -> str:
        """Get the display category (user override or ML category)."""
        return self.user_category or self.primary_category or "Uncategorized"
    
    model_config = ConfigDict(from_attributes=True)


class TransactionList(BaseModel):
    """List of transactions."""
    transactions: List[Transaction]
    total: int
    
    model_config = ConfigDict(from_attributes=True)


class TransactionFilter(BaseModel):
    """Transaction filter criteria."""
    start_date: Optional[date_type] = None
    end_date: Optional[date_type] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    category: Optional[str] = None
    account_id: Optional[UUID] = None
    account_type: Optional[str] = None
    pending: Optional[bool] = None
    reconciled: Optional[bool] = None
    search: Optional[str] = None


class TransactionExport(BaseModel):
    """Transaction export request."""
    format: Literal["csv", "excel", "json"] = Field("csv", description="Export format")
    start_date: Optional[date_type] = None
    end_date: Optional[date_type] = None
    account_ids: Optional[List[UUID]] = None
    include_summary: bool = Field(True, description="Include summary sheet (Excel only)")


class BulkTransactionUpdate(BaseModel):
    """Bulk transaction update request."""
    transaction_ids: List[UUID] = Field(..., description="Transaction IDs to update")
    operation: Literal[
        "categorize", "reconcile", "unreconcile", 
        "add_tag", "remove_tag", "delete"
    ] = Field(..., description="Bulk operation type")
    category: Optional[str] = Field(None, description="Category for categorize operation")
    tag: Optional[str] = Field(None, description="Tag for add/remove tag operations")
    
    @field_validator("category")
    @classmethod
    def validate_category(cls, v, info):
        if info.data.get("operation") == "categorize" and not v:
            raise ValueError("Category is required for categorize operation")
        return v
    
    @field_validator("tag")
    @classmethod
    def validate_tag(cls, v, info):
        operation = info.data.get("operation")
        if operation in ["add_tag", "remove_tag"] and not v:
            raise ValueError(f"Tag is required for {operation} operation")
        return v


class TransactionCategorization(BaseModel):
    """Transaction categorization request/response."""
    transaction_id: UUID
    suggested_category: str
    confidence: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    alternative_categories: Optional[List[Dict[str, float]]] = None
    rules_applied: Optional[List[str]] = None


class CategorySummary(BaseModel):
    """Category summary for statistics."""
    category: str
    transaction_count: int
    total_amount: float
    percentage: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)


class TransactionStats(BaseModel):
    """Transaction statistics."""
    total_transactions: int
    total_income: float
    total_expenses: float
    net_amount: float
    categories: List[CategorySummary]
    monthly_trend: Optional[List[Dict[str, Any]]] = None

    # Add computed fields for frontend compatibility
    @computed_field
    @property
    def net_income(self) -> float:
        """Return net_income for frontend compatibility."""
        return self.net_amount

    @computed_field
    @property
    def transaction_count(self) -> int:
        """Return transaction_count for frontend compatibility."""
        return self.total_transactions

    @computed_field
    @property
    def avg_transaction_amount(self) -> float:
        """Calculate average transaction amount."""
        if self.total_transactions > 0:
            return (self.total_income + self.total_expenses) / self.total_transactions
        return 0

    model_config = ConfigDict(from_attributes=True)


class TransactionImportResult(BaseModel):
    """Result of transaction import."""
    success: bool
    imported_count: int
    failed_count: int
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None