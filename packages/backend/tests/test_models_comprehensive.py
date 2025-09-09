"""
Comprehensive tests for database models.
"""

import pytest
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from uuid import uuid4

from src.database.models import (
    User, Account, Transaction, Category, PlaidItem, Institution
)


class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation(self, db_session: Session):
        """Test basic user creation."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password_123",
            full_name="Test User",
            is_active=True,
            is_verified=True
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.is_verified is True
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_string_representation(self, db_session: Session):
        """Test User model string representation."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password_123"
        )
        
        assert str(user) == "testuser"
    
    def test_user_email_uniqueness(self, db_session: Session):
        """Test that user emails must be unique."""
        user1 = User(
            email="test@example.com",
            username="user1",
            hashed_password="hashed1"
        )
        user2 = User(
            email="test@example.com",  # Same email
            username="user2",
            hashed_password="hashed2"
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
    
    def test_user_username_uniqueness(self, db_session: Session):
        """Test that usernames must be unique."""
        user1 = User(
            email="test1@example.com",
            username="testuser",
            hashed_password="hashed1"
        )
        user2 = User(
            email="test2@example.com",
            username="testuser",  # Same username
            hashed_password="hashed2"
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()


class TestInstitutionModel:
    """Test Institution model functionality."""
    
    def test_institution_creation(self, db_session: Session):
        """Test basic institution creation."""
        institution = Institution(
            plaid_institution_id="ins_test_123",
            name="Test Bank",
            logo_url="https://test.com/logo.png",
            primary_color="#1f77b4",
            url="https://testbank.com"
        )
        
        db_session.add(institution)
        db_session.commit()
        db_session.refresh(institution)
        
        assert institution.id is not None
        assert institution.plaid_institution_id == "ins_test_123"
        assert institution.name == "Test Bank"
        assert institution.logo_url == "https://test.com/logo.png"
        assert institution.primary_color == "#1f77b4"
        assert institution.url == "https://testbank.com"
    
    def test_institution_string_representation(self, db_session: Session):
        """Test Institution model string representation."""
        institution = Institution(
            plaid_institution_id="ins_test_123",
            name="Test Bank"
        )
        
        assert str(institution) == "Test Bank"


class TestPlaidItemModel:
    """Test PlaidItem model functionality."""
    
    def test_plaid_item_creation(self, db_session: Session, test_user: User):
        """Test basic Plaid item creation."""
        # Create institution first
        institution = Institution(
            plaid_institution_id="ins_test_123",
            name="Test Bank"
        )
        db_session.add(institution)
        db_session.flush()
        
        plaid_item = PlaidItem(
            user_id=test_user.id,
            institution_id=institution.id,
            plaid_item_id="item_test_123",
            access_token="access-sandbox-test-123",
            last_successful_sync=datetime.utcnow(),
            is_active=True
        )
        
        db_session.add(plaid_item)
        db_session.commit()
        db_session.refresh(plaid_item)
        
        assert plaid_item.id is not None
        assert plaid_item.user_id == test_user.id
        assert plaid_item.institution_id == institution.id
        assert plaid_item.plaid_item_id == "item_test_123"
        assert plaid_item.access_token == "access-sandbox-test-123"
        assert plaid_item.is_active is True
        assert plaid_item.last_successful_sync is not None
    
    def test_plaid_item_relationships(self, db_session: Session, test_user: User):
        """Test PlaidItem model relationships."""
        institution = Institution(
            plaid_institution_id="ins_test_123",
            name="Test Bank"
        )
        db_session.add(institution)
        db_session.flush()
        
        plaid_item = PlaidItem(
            user_id=test_user.id,
            institution_id=institution.id,
            plaid_item_id="item_test_123",
            access_token="access-test-123"
        )
        
        db_session.add(plaid_item)
        db_session.commit()
        db_session.refresh(plaid_item)
        
        # Test relationships
        assert plaid_item.user.id == test_user.id
        assert plaid_item.institution.id == institution.id


class TestAccountModel:
    """Test Account model functionality."""
    
    def test_account_creation(self, db_session: Session, test_user: User):
        """Test basic account creation."""
        institution = Institution(
            plaid_institution_id="ins_test_123",
            name="Test Bank"
        )
        db_session.add(institution)
        db_session.flush()
        
        plaid_item = PlaidItem(
            user_id=test_user.id,
            institution_id=institution.id,
            plaid_item_id="item_test_123",
            access_token="access-test-123"
        )
        db_session.add(plaid_item)
        db_session.flush()
        
        account = Account(
            user_id=test_user.id,
            plaid_item_id=plaid_item.id,
            institution_id=institution.id,
            plaid_account_id="acc_test_123",
            name="Test Checking Account",
            official_name="Test Bank Checking Account",
            type="depository",
            subtype="checking",
            mask="1234",
            current_balance_cents=150000,  # $1,500.00
            available_balance_cents=145000,  # $1,450.00
            iso_currency_code="USD",
            is_active=True,
            is_hidden=False
        )
        
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)
        
        assert account.id is not None
        assert account.user_id == test_user.id
        assert account.plaid_account_id == "acc_test_123"
        assert account.name == "Test Checking Account"
        assert account.current_balance_cents == 150000
        assert account.available_balance_cents == 145000
        assert account.is_active is True
        assert account.is_hidden is False
    
    def test_account_balance_properties(self, db_session: Session, test_user: User):
        """Test account balance property calculations."""
        account = Account(
            user_id=test_user.id,
            plaid_account_id="acc_test_123",
            name="Test Account",
            type="depository",
            subtype="checking",
            current_balance_cents=150050,  # $1,500.50
            available_balance_cents=145075,  # $1,450.75
            limit_cents=200000  # $2,000.00 credit limit
        )
        
        # Test balance calculations
        assert account.current_balance == 1500.50
        assert account.available_balance == 1450.75
        assert account.limit == 2000.00
    
    def test_account_balance_none_handling(self, db_session: Session, test_user: User):
        """Test account balance calculations with None values."""
        account = Account(
            user_id=test_user.id,
            plaid_account_id="acc_test_123",
            name="Test Account",
            type="depository",
            subtype="checking",
            current_balance_cents=None,
            available_balance_cents=None,
            limit_cents=None
        )
        
        assert account.current_balance == 0.0
        assert account.available_balance == 0.0
        assert account.limit == 0.0
    
    def test_account_relationships(self, db_session: Session, test_user: User):
        """Test Account model relationships."""
        institution = Institution(
            plaid_institution_id="ins_test_123",
            name="Test Bank"
        )
        db_session.add(institution)
        db_session.flush()
        
        plaid_item = PlaidItem(
            user_id=test_user.id,
            institution_id=institution.id,
            plaid_item_id="item_test_123",
            access_token="access-test-123"
        )
        db_session.add(plaid_item)
        db_session.flush()
        
        account = Account(
            user_id=test_user.id,
            plaid_item_id=plaid_item.id,
            institution_id=institution.id,
            plaid_account_id="acc_test_123",
            name="Test Account",
            type="depository",
            subtype="checking"
        )
        
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)
        
        # Test relationships
        assert account.user.id == test_user.id
        assert account.plaid_item.id == plaid_item.id
        assert account.institution.id == institution.id


class TestCategoryModel:
    """Test Category model functionality."""
    
    def test_category_creation(self, db_session: Session, test_user: User):
        """Test basic category creation."""
        category = Category(
            user_id=test_user.id,
            name="Groceries",
            type="expense",
            color="#4CAF50",
            icon="shopping_cart",
            description="Food and grocery expenses"
        )
        
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        
        assert category.id is not None
        assert category.user_id == test_user.id
        assert category.name == "Groceries"
        assert category.type == "expense"
        assert category.color == "#4CAF50"
        assert category.icon == "shopping_cart"
        assert category.description == "Food and grocery expenses"
    
    def test_category_string_representation(self, db_session: Session, test_user: User):
        """Test Category model string representation."""
        category = Category(
            user_id=test_user.id,
            name="Groceries",
            type="expense",
            color="#4CAF50",
            icon="shopping_cart"
        )
        
        assert str(category) == "Groceries"
    
    def test_category_user_relationship(self, db_session: Session, test_user: User):
        """Test Category-User relationship."""
        category = Category(
            user_id=test_user.id,
            name="Groceries",
            type="expense",
            color="#4CAF50",
            icon="shopping_cart"
        )
        
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        
        assert category.user.id == test_user.id


class TestTransactionModel:
    """Test Transaction model functionality."""
    
    def test_transaction_creation(self, db_session: Session, test_account: Account, test_category: Category):
        """Test basic transaction creation."""
        transaction = Transaction(
            account_id=test_account.id,
            plaid_transaction_id="txn_test_123",
            amount_cents=-2550,  # -$25.50
            date=date.today(),
            name="Test Transaction",
            merchant_name="Test Merchant",
            category_id=test_category.id,
            pending=False,
            notes="Test notes"
        )
        
        db_session.add(transaction)
        db_session.commit()
        db_session.refresh(transaction)
        
        assert transaction.id is not None
        assert transaction.account_id == test_account.id
        assert transaction.plaid_transaction_id == "txn_test_123"
        assert transaction.amount_cents == -2550
        assert transaction.date == date.today()
        assert transaction.name == "Test Transaction"
        assert transaction.merchant_name == "Test Merchant"
        assert transaction.category_id == test_category.id
        assert transaction.pending is False
        assert transaction.notes == "Test notes"
    
    def test_transaction_amount_property(self, db_session: Session, test_account: Account):
        """Test transaction amount property calculation."""
        transaction = Transaction(
            account_id=test_account.id,
            plaid_transaction_id="txn_test_123",
            amount_cents=-2550,  # -$25.50
            date=date.today(),
            name="Test Transaction",
            pending=False
        )
        
        assert transaction.amount == -25.50
    
    def test_transaction_amount_none_handling(self, db_session: Session, test_account: Account):
        """Test transaction amount calculation with None."""
        transaction = Transaction(
            account_id=test_account.id,
            plaid_transaction_id="txn_test_123",
            amount_cents=None,
            date=date.today(),
            name="Test Transaction",
            pending=False
        )
        
        assert transaction.amount == 0.0
    
    def test_transaction_relationships(self, db_session: Session, test_account: Account, test_category: Category):
        """Test Transaction model relationships."""
        transaction = Transaction(
            account_id=test_account.id,
            plaid_transaction_id="txn_test_123",
            amount_cents=-1000,
            date=date.today(),
            name="Test Transaction",
            category_id=test_category.id,
            pending=False
        )
        
        db_session.add(transaction)
        db_session.commit()
        db_session.refresh(transaction)
        
        # Test relationships
        assert transaction.account.id == test_account.id
        assert transaction.category.id == test_category.id


# Additional model tests can be added here for UserSession, APIKey, AuditLog
# when these models are implemented in the future