"""Transaction model for financial transactions with double-entry support."""

from sqlalchemy import (
    Column, String, Boolean, Numeric, DateTime, Text, ForeignKey, Index,
    CheckConstraint, Integer, func, event
)
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID, JSONB
from decimal import Decimal
from typing import Optional
from .base import Base, UUIDMixin, TimestampMixin


class Transaction(Base, UUIDMixin, TimestampMixin):
    """Financial transactions with support for double-entry bookkeeping."""
    
    __tablename__ = "transactions"
    
    # Core identifiers
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True)
    plaid_transaction_id = Column(String(255), unique=True, index=True)
    
    # Transaction details
    amount = Column(Numeric(15, 2), nullable=False)  # Always positive for debit/credit clarity
    transaction_type = Column(String(10), nullable=False)  # debit or credit
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    posted_date = Column(DateTime(timezone=True))  # When transaction actually posted
    
    # Description fields
    name = Column(String(500), nullable=False)  # Primary description
    merchant_name = Column(String(255), index=True)
    description = Column(Text)  # Additional details
    
    # Status
    is_pending = Column(Boolean, default=False, nullable=False)
    is_recurring = Column(Boolean, default=False, nullable=False)
    is_transfer = Column(Boolean, default=False, nullable=False)
    is_fee = Column(Boolean, default=False, nullable=False)
    
    # Categorization
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), index=True)
    subcategory = Column(String(100))  # Free-form subcategory
    user_category_override = Column(String(100))  # User manual override
    
    # Business classification
    is_business = Column(Boolean, default=False, nullable=False, index=True)
    is_tax_deductible = Column(Boolean, default=False, nullable=False)
    tax_year = Column(Integer, index=True)  # Year for tax reporting
    
    # Location data
    location_address = Column(String(500))
    location_city = Column(String(100))
    location_region = Column(String(100))  # State/Province
    location_postal_code = Column(String(20))
    location_country = Column(String(3), default="US")
    location_coordinates = Column(JSONB)  # {lat, lon}
    
    # Payment details
    payment_method = Column(String(50))  # online, in_store, atm, etc.
    payment_channel = Column(String(50))  # More specific channel
    account_number_masked = Column(String(20))  # Last 4 digits of payment method
    
    # Double-entry bookkeeping support
    contra_transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    journal_entry_id = Column(UUID(as_uuid=True))  # Group related transactions
    
    # Reconciliation
    is_reconciled = Column(Boolean, default=False, nullable=False)
    reconciled_date = Column(DateTime(timezone=True))
    reconciled_by = Column(String(255))
    
    # Audit and notes
    notes = Column(Text)
    tags = Column(JSONB, default=list)  # User-defined tags
    attachments = Column(JSONB, default=list)  # Receipt/document references
    
    # Processing metadata
    plaid_metadata = Column(JSONB, default=dict)
    processing_status = Column(String(20), default="processed")
    error_details = Column(Text)
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    contra_transaction = relationship("Transaction", remote_side=[id])
    ml_predictions = relationship("MLPrediction", back_populates="transaction", cascade="all, delete-orphan")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_transactions_account_date", "account_id", "date"),
        Index("idx_transactions_merchant", "merchant_name"),
        Index("idx_transactions_amount", "amount"),
        Index("idx_transactions_category_date", "category_id", "date"),
        Index("idx_transactions_business_date", "is_business", "date"),
        Index("idx_transactions_tax_year", "tax_year", "is_tax_deductible"),
        Index("idx_transactions_pending", "is_pending", "date"),
        Index("idx_transactions_reconciled", "is_reconciled"),
        Index("idx_transactions_journal", "journal_entry_id"),
        CheckConstraint(
            "transaction_type IN ('debit', 'credit')",
            name="ck_transaction_type"
        ),
        CheckConstraint(
            "amount > 0",
            name="ck_amount_positive"
        ),
        CheckConstraint(
            "processing_status IN ('processed', 'pending', 'error', 'manual_review')",
            name="ck_processing_status"
        ),
    )
    
    @property
    def amount_decimal(self) -> Decimal:
        """Return amount as Decimal for precise calculations."""
        return Decimal(str(self.amount)) if self.amount else Decimal("0.00")
    
    @property
    def signed_amount(self) -> Decimal:
        """Return amount with proper sign (negative for debits, positive for credits)."""
        amount = self.amount_decimal
        return -amount if self.transaction_type == "debit" else amount
    
    @property
    def is_income(self) -> bool:
        """Check if transaction represents income."""
        return self.transaction_type == "credit" and not self.is_transfer
    
    @property
    def is_expense(self) -> bool:
        """Check if transaction represents an expense."""
        return self.transaction_type == "debit" and not self.is_transfer
    
    def create_contra_entry(self, contra_account_id: UUID, session: Session) -> "Transaction":
        """Create the contra entry for double-entry bookkeeping."""
        contra_type = "credit" if self.transaction_type == "debit" else "debit"
        
        contra_transaction = Transaction(
            account_id=contra_account_id,
            amount=self.amount,
            transaction_type=contra_type,
            date=self.date,
            posted_date=self.posted_date,
            name=f"Transfer: {self.name}",
            merchant_name=self.merchant_name,
            is_transfer=True,
            category_id=self.category_id,
            is_business=self.is_business,
            contra_transaction_id=self.id,
            journal_entry_id=self.journal_entry_id
        )
        
        # Link back to this transaction
        self.contra_transaction_id = contra_transaction.id
        
        session.add(contra_transaction)
        return contra_transaction
    
    def __repr__(self):
        return (f"<Transaction(id={self.id}, account_id={self.account_id}, "
                f"amount={self.signed_amount}, date='{self.date}', name='{self.name}')>")


# Event listener to set tax year automatically
@event.listens_for(Transaction, 'before_insert')
@event.listens_for(Transaction, 'before_update')
def set_tax_year(mapper, connection, target):
    """Automatically set tax year based on transaction date."""
    if target.date and not target.tax_year:
        target.tax_year = target.date.year