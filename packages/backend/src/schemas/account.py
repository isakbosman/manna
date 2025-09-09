"""Pydantic schemas for account management."""

from pydantic import BaseModel, Field, ConfigDict, computed_field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class AccountBase(BaseModel):
    """Base schema for account information."""
    name: str = Field(..., description="Account display name")
    official_name: Optional[str] = Field(None, description="Official account name from institution")
    type: str = Field(..., description="Account type (depository, credit, loan, investment)")
    subtype: Optional[str] = Field(None, description="Account subtype (checking, savings, credit card, etc.)")
    mask: Optional[str] = Field(None, description="Last 4 digits of account number")
    iso_currency_code: str = Field(default="USD", description="Currency code")
    is_active: bool = Field(default=True, description="Whether account is active")
    is_hidden: bool = Field(default=False, description="Whether account is hidden from user")
    
    model_config = ConfigDict(from_attributes=True)


class AccountCreate(AccountBase):
    """Schema for creating a new account."""
    plaid_account_id: str = Field(..., description="Plaid account identifier")
    plaid_item_id: UUID = Field(..., description="Associated Plaid item ID")
    institution_id: UUID = Field(..., description="Institution ID")
    current_balance_cents: Optional[int] = Field(None, description="Current balance in cents")
    available_balance_cents: Optional[int] = Field(None, description="Available balance in cents")
    limit_cents: Optional[int] = Field(None, description="Credit limit in cents")


class AccountUpdate(BaseModel):
    """Schema for updating account information."""
    name: Optional[str] = Field(None, description="Account display name")
    is_hidden: Optional[bool] = Field(None, description="Whether account is hidden")
    is_active: Optional[bool] = Field(None, description="Whether account is active")
    
    model_config = ConfigDict(from_attributes=True)


class Account(AccountBase):
    """Full account schema with computed fields."""
    id: UUID = Field(..., description="Account unique identifier")
    user_id: UUID = Field(..., description="User ID who owns this account")
    plaid_account_id: str = Field(..., description="Plaid account identifier")
    plaid_item_id: UUID = Field(..., description="Associated Plaid item ID")
    institution_id: UUID = Field(..., description="Institution ID")
    current_balance_cents: Optional[int] = Field(None, description="Current balance in cents")
    available_balance_cents: Optional[int] = Field(None, description="Available balance in cents")
    limit_cents: Optional[int] = Field(None, description="Credit limit in cents")
    created_at: datetime = Field(..., description="When account was created")
    updated_at: datetime = Field(..., description="When account was last updated")
    
    @computed_field
    @property
    def current_balance(self) -> float:
        """Current balance in dollars."""
        return self.current_balance_cents / 100 if self.current_balance_cents else 0.0
    
    @computed_field
    @property
    def available_balance(self) -> float:
        """Available balance in dollars."""
        return self.available_balance_cents / 100 if self.available_balance_cents else 0.0
    
    @computed_field
    @property
    def limit(self) -> float:
        """Credit limit in dollars."""
        return self.limit_cents / 100 if self.limit_cents else 0.0
    
    model_config = ConfigDict(from_attributes=True)


class AccountWithInstitution(Account):
    """Account schema with institution details."""
    institution_name: Optional[str] = Field(None, description="Institution name")
    institution_logo: Optional[str] = Field(None, description="Institution logo URL")
    institution_color: Optional[str] = Field(None, description="Institution primary color")
    
    model_config = ConfigDict(from_attributes=True)


class AccountList(BaseModel):
    """Paginated list of accounts."""
    accounts: List[AccountWithInstitution] = Field(..., description="List of accounts")
    total: int = Field(..., description="Total number of accounts")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of accounts per page")
    
    model_config = ConfigDict(from_attributes=True)


class AccountBalance(BaseModel):
    """Account balance information."""
    account_id: UUID = Field(..., description="Account ID")
    current_balance: float = Field(..., description="Current balance in dollars")
    available_balance: Optional[float] = Field(None, description="Available balance in dollars")
    limit: Optional[float] = Field(None, description="Credit limit in dollars")
    currency: str = Field(default="USD", description="Currency code")
    as_of: datetime = Field(..., description="When balance was last updated")
    
    model_config = ConfigDict(from_attributes=True)


class AccountSyncStatus(BaseModel):
    """Account synchronization status."""
    account_id: UUID = Field(..., description="Account ID")
    status: str = Field(..., description="Sync status (success, in_progress, error)")
    last_synced: Optional[datetime] = Field(None, description="Last successful sync")
    error_message: Optional[str] = Field(None, description="Error message if sync failed")
    transaction_count: int = Field(default=0, description="Number of transactions synced")
    
    model_config = ConfigDict(from_attributes=True)
