"""Financial institution model for bank/credit union data."""

from sqlalchemy import Column, String, Boolean, Text, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from .base import Base, UUIDMixin, TimestampMixin


class Institution(Base, UUIDMixin, TimestampMixin):
    """Financial institutions (banks, credit unions, etc.)."""
    
    __tablename__ = "institutions"
    
    # Plaid institution data
    plaid_institution_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # Institution details
    country_codes = Column(JSONB, default=list)  # ['US', 'CA']
    products = Column(JSONB, default=list)  # ['transactions', 'auth', 'identity']
    routing_numbers = Column(JSONB, default=list)
    
    # Branding
    logo = Column(String(500))  # URL to logo
    primary_color = Column(String(7))  # Hex color
    url = Column(String(500))  # Institution website
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    oauth_required = Column(Boolean, default=False)
    
    # Metadata
    metadata = Column(JSONB, default=dict)
    
    # Relationships
    accounts = relationship("Account", back_populates="institution")
    plaid_items = relationship("PlaidItem", back_populates="institution")
    
    # Indexes
    __table_args__ = (
        Index("idx_institutions_name", "name"),
        Index("idx_institutions_active", "is_active"),
    )
    
    def __repr__(self):
        return f"<Institution(id={self.id}, name='{self.name}')>"