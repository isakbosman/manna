"""Pydantic schemas for Plaid API integration."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class PlaidLinkToken(BaseModel):
    """Response schema for Plaid Link token creation."""
    link_token: str = Field(..., description="Plaid Link token for frontend")
    expiration: datetime = Field(..., description="When the token expires")
    request_id: Optional[str] = Field(None, description="Plaid request ID")
    
    model_config = ConfigDict(from_attributes=True)


class PlaidPublicTokenExchange(BaseModel):
    """Request schema for exchanging public token."""
    public_token: str = Field(..., description="Public token from Plaid Link")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata from Link")
    
    model_config = ConfigDict(from_attributes=True)


class PlaidInstitution(BaseModel):
    """Schema for Plaid institution information."""
    institution_id: str = Field(..., description="Plaid institution ID")
    name: str = Field(..., description="Institution name")
    url: Optional[str] = Field(None, description="Institution website")
    logo: Optional[str] = Field(None, description="Institution logo URL")
    primary_color: Optional[str] = Field(None, description="Institution primary color")
    
    model_config = ConfigDict(from_attributes=True)


class PlaidError(BaseModel):
    """Schema for Plaid error responses."""
    error_type: str = Field(..., description="Type of error")
    error_code: str = Field(..., description="Specific error code")
    error_message: str = Field(..., description="Human readable error message")
    display_message: Optional[str] = Field(None, description="User-friendly message")
    request_id: Optional[str] = Field(None, description="Plaid request ID")
    
    model_config = ConfigDict(from_attributes=True)


class PlaidWebhook(BaseModel):
    """Schema for Plaid webhook payloads."""
    webhook_type: str = Field(..., description="Type of webhook")
    webhook_code: str = Field(..., description="Specific webhook code")
    item_id: str = Field(..., description="Plaid item ID")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details if any")
    
    model_config = ConfigDict(from_attributes=True)


class PlaidItemStatus(BaseModel):
    """Schema for Plaid item status information."""
    item_id: str = Field(..., description="Internal item ID")
    plaid_item_id: str = Field(..., description="Plaid item ID")
    institution: Optional[PlaidInstitution] = Field(None, description="Institution info")
    is_active: bool = Field(..., description="Whether item is active")
    error: Optional[str] = Field(None, description="Current error state")
    account_count: int = Field(..., description="Number of linked accounts")
    last_synced: Optional[datetime] = Field(None, description="Last successful sync")
    created_at: datetime = Field(..., description="When item was created")
    
    model_config = ConfigDict(from_attributes=True)
