"""Database schema and connection management for financial data."""

from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from cryptography.fernet import Fernet

Base = declarative_base()

class Account(Base):
    __tablename__ = 'accounts'
    
    id = Column(String, primary_key=True)
    plaid_account_id = Column(String, unique=True)
    institution_name = Column(String)
    account_name = Column(String)
    account_type = Column(String)  # checking, savings, credit, investment
    account_subtype = Column(String)
    is_business = Column(Boolean, default=False)
    current_balance = Column(Float)
    available_balance = Column(Float)
    credit_limit = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    transactions = relationship("Transaction", back_populates="account")

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(String, primary_key=True)
    plaid_transaction_id = Column(String, unique=True)
    account_id = Column(String, ForeignKey('accounts.id'))
    amount = Column(Float)
    date = Column(DateTime)
    merchant_name = Column(String)
    name = Column(String)
    pending = Column(Boolean, default=False)
    
    # Categorization
    category = Column(String)
    subcategory = Column(String)
    ml_category = Column(String)
    ml_confidence = Column(Float)
    user_category = Column(String)  # User override
    is_business = Column(Boolean, default=False)
    is_tax_deductible = Column(Boolean, default=False)
    
    # Metadata
    notes = Column(Text)
    tags = Column(String)  # JSON array as string
    location_city = Column(String)
    location_state = Column(String)
    payment_method = Column(String)
    
    # Reconciliation
    is_reconciled = Column(Boolean, default=False)
    is_transfer = Column(Boolean, default=False)
    transfer_pair_id = Column(String, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    account = relationship("Account", back_populates="transactions")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_date', 'date'),
        Index('idx_category', 'category'),
        Index('idx_merchant', 'merchant_name'),
        Index('idx_account_date', 'account_id', 'date'),
    )

class MLModel(Base):
    __tablename__ = 'ml_models'
    
    id = Column(Integer, primary_key=True)
    model_version = Column(String)
    model_type = Column(String)  # xgboost, random_forest, etc
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    training_date = Column(DateTime, default=datetime.utcnow)
    training_samples = Column(Integer)
    feature_importance = Column(Text)  # JSON
    model_path = Column(String)
    is_active = Column(Boolean, default=False)
    
class CategoryRule(Base):
    __tablename__ = 'category_rules'
    
    id = Column(Integer, primary_key=True)
    rule_type = Column(String)  # merchant, keyword, amount_range
    pattern = Column(String)
    category = Column(String)
    subcategory = Column(String)
    is_business = Column(Boolean)
    is_tax_deductible = Column(Boolean)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class ReconciliationLog(Base):
    __tablename__ = 'reconciliation_logs'
    
    id = Column(Integer, primary_key=True)
    reconciliation_date = Column(DateTime)
    account_id = Column(String, ForeignKey('accounts.id'))
    starting_balance = Column(Float)
    ending_balance = Column(Float)
    transaction_count = Column(Integer)
    discrepancy_amount = Column(Float)
    is_resolved = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class TaxEstimate(Base):
    __tablename__ = 'tax_estimates'
    
    id = Column(Integer, primary_key=True)
    tax_year = Column(Integer)
    quarter = Column(Integer)
    business_income = Column(Float)
    business_expenses = Column(Float)
    estimated_quarterly_tax = Column(Float)
    federal_amount = Column(Float)
    state_amount = Column(Float)
    effective_rate = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

def get_database_url():
    """Get encrypted database URL."""
    db_path = os.getenv('DATABASE_PATH', 'data/financial.db')
    return f'sqlite:///{db_path}'

def init_database():
    """Initialize database with tables."""
    engine = create_engine(get_database_url())
    Base.metadata.create_all(engine)
    return engine

def get_session():
    """Get database session."""
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    return Session()