"""
Pytest Configuration and Fixtures
"""

import os
import sys
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.main import app
from src.database import Base, get_db
from src.database.models import User, Account, Transaction, PlaidItem, Institution, Category
from src.utils.security import create_access_token, hash_password
from src.config import settings

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator:
    """Create a test client with overridden database dependency"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    """Create a test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user: User) -> dict:
    """Create authentication headers with a valid token"""
    access_token = create_access_token(
        data={"sub": test_user.email, "user_id": str(test_user.id)}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def test_account(db_session: Session, test_user: User) -> Account:
    """Create a test account"""
    account = Account(
        user_id=test_user.id,
        plaid_account_id="test_account_123",
        name="Test Checking",
        official_name="Test Checking Account",
        type="depository",
        subtype="checking",
        mask="1234",
        current_balance=1000.00,
        available_balance=900.00,
        currency="USD",
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture(scope="function")
def test_category(db_session: Session, test_user: User) -> Category:
    """Create a test category"""
    category = Category(
        user_id=test_user.id,
        name="Groceries",
        type="expense",
        color="#4CAF50",
        icon="shopping_cart",
        description="Grocery shopping expenses",
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture(scope="function")
def test_transactions(db_session: Session, test_account: Account, test_category: Category) -> list[Transaction]:
    """Create test transactions"""
    transactions = []
    for i in range(10):
        transaction = Transaction(
            account_id=test_account.id,
            plaid_transaction_id=f"test_txn_{i}",
            amount=100.00 + (i * 10),
            date=datetime.now().date() - timedelta(days=i),
            name=f"Test Transaction {i}",
            merchant_name=f"Test Merchant {i}",
            category_id=test_category.id if i % 2 == 0 else None,
            pending=False,
        )
        db_session.add(transaction)
        transactions.append(transaction)
    
    db_session.commit()
    for txn in transactions:
        db_session.refresh(txn)
    
    return transactions


@pytest.fixture(scope="function")
def mock_plaid_client():
    """Mock Plaid client for testing"""
    with patch('src.services.plaid.plaid_client') as mock_client:
        # Mock link token creation
        mock_client.link_token_create.return_value = {
            'link_token': 'test-link-token-123',
            'expiration': '2024-12-31T23:59:59Z',
        }
        
        # Mock public token exchange
        mock_client.item_public_token_exchange.return_value = {
            'access_token': 'test-access-token-123',
            'item_id': 'test-item-123',
        }
        
        # Mock accounts get
        mock_client.accounts_get.return_value = {
            'accounts': [
                {
                    'account_id': 'test-account-123',
                    'name': 'Test Checking',
                    'official_name': 'Test Checking Account',
                    'type': 'depository',
                    'subtype': 'checking',
                    'mask': '1234',
                    'balances': {
                        'current': 1000.00,
                        'available': 900.00,
                        'iso_currency_code': 'USD',
                    },
                },
            ],
        }
        
        # Mock transactions sync
        mock_client.transactions_sync.return_value = {
            'added': [
                {
                    'transaction_id': 'test-txn-123',
                    'account_id': 'test-account-123',
                    'amount': 50.00,
                    'date': '2024-01-01',
                    'name': 'Test Transaction',
                    'merchant_name': 'Test Merchant',
                    'category': ['Food and Drink', 'Restaurants'],
                    'pending': False,
                },
            ],
            'modified': [],
            'removed': [],
            'has_more': False,
        }
        
        yield mock_client


@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis client for testing"""
    with patch('src.utils.redis.redis_client') as mock_redis:
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = True
        mock_redis.exists.return_value = False
        mock_redis.expire.return_value = True
        mock_redis.ttl.return_value = 3600
        
        yield mock_redis


@pytest.fixture(scope="function")
def sample_account(test_user: User, db_session: Session) -> Account:
    """Create a sample account for testing."""
    # Create institution
    institution = Institution(
        plaid_institution_id="ins_test_123",
        name="Test Bank",
        logo_url="https://test.com/logo.png",
        primary_color="#1f77b4"
    )
    db_session.add(institution)
    db_session.flush()
    
    # Create Plaid item
    plaid_item = PlaidItem(
        user_id=test_user.id,
        institution_id=institution.id,
        plaid_item_id="item_test_123",
        access_token="access-sandbox-test-123",
        last_successful_sync=datetime.utcnow()
    )
    db_session.add(plaid_item)
    db_session.flush()
    
    # Create account
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
    
    return account


@pytest.fixture(scope="function")
def mock_plaid_service():
    """Mock Plaid service for testing."""
    with patch('src.services.plaid_service.plaid_service') as mock_service:
        # Mock default responses
        mock_service.create_link_token.return_value = {
            "link_token": "link-sandbox-test-123",
            "expiration": datetime.utcnow() + timedelta(minutes=30),
            "request_id": "req-test-123"
        }
        
        mock_service.exchange_public_token.return_value = "access-sandbox-test-123"
        
        mock_service.get_item.return_value = {
            "item_id": "item-test-123",
            "institution_id": "ins_test_123",
            "webhook": "https://example.com/webhook",
            "available_products": ["transactions"],
            "billed_products": ["transactions"]
        }
        
        mock_service.get_institution.return_value = {
            "institution_id": "ins_test_123",
            "name": "Test Bank",
            "url": "https://testbank.com",
            "primary_color": "#1f77b4",
            "logo": "https://testbank.com/logo.png"
        }
        
        mock_service.get_accounts.return_value = [
            {
                "account_id": "acc_test_123",
                "name": "Test Checking",
                "official_name": "Test Checking Account",
                "type": "depository",
                "subtype": "checking",
                "mask": "1234",
                "current_balance": 1500.00,
                "available_balance": 1450.00,
                "limit": None,
                "iso_currency_code": "USD"
            }
        ]
        
        mock_service.handle_webhook.return_value = {"action": "fetch_transactions"}
        
        yield mock_service


@pytest.fixture(scope="function")
def mock_redis_client():
    """Mock Redis client for testing."""
    with patch('src.utils.redis.get_redis_client') as mock_get_redis:
        mock_redis = MagicMock()
        mock_redis.exists.return_value = False
        mock_redis.setex.return_value = True
        mock_redis.delete.return_value = True
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        
        mock_get_redis.return_value = mock_redis
        yield mock_redis


@pytest.fixture(scope="function")
def mock_ml_service():
    """Mock ML service for testing"""
    with patch('src.services.ml.MLService') as MockMLService:
        mock_service = Mock()
        
        # Mock categorization
        mock_service.categorize_transaction.return_value = {
            'category_id': 'cat_123',
            'category_name': 'Groceries',
            'confidence': 0.95,
        }
        
        # Mock batch prediction
        mock_service.predict_categories.return_value = [
            {
                'transaction_id': 'txn_1',
                'category_id': 'cat_123',
                'confidence': 0.92,
            },
            {
                'transaction_id': 'txn_2',
                'category_id': 'cat_456',
                'confidence': 0.88,
            },
        ]
        
        # Mock anomaly detection
        mock_service.detect_anomalies.return_value = {
            'anomalies': [],
            'confidence_scores': [0.95, 0.92, 0.88],
        }
        
        MockMLService.return_value = mock_service
        yield mock_service


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Performance testing fixtures
@pytest.fixture
def performance_timer():
    """Timer for performance tests"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.perf_counter()
        
        def stop(self):
            self.end_time = time.perf_counter()
        
        @property
        def elapsed_ms(self):
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time) * 1000
            return None
    
    return Timer()


# Security testing fixtures
@pytest.fixture
def security_headers():
    """Security headers for testing"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
    }


@pytest.fixture
def large_dataset(db_session: Session, test_account: Account):
    """Create a large dataset for performance testing"""
    transactions = []
    batch_size = 100
    
    for batch in range(10):  # 1000 transactions total
        batch_transactions = []
        for i in range(batch_size):
            txn_id = batch * batch_size + i
            transaction = Transaction(
                account_id=test_account.id,
                plaid_transaction_id=f"perf_txn_{txn_id}",
                amount=100.00 + (txn_id % 100),
                date=datetime.now().date() - timedelta(days=txn_id % 365),
                name=f"Performance Test Transaction {txn_id}",
                merchant_name=f"Merchant {txn_id % 50}",
                pending=False,
            )
            batch_transactions.append(transaction)
        
        db_session.bulk_save_objects(batch_transactions)
        transactions.extend(batch_transactions)
    
    db_session.commit()
    return transactions