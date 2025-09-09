"""
Critical tests to achieve 80% coverage - focusing on high-impact, low-effort areas.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from uuid import uuid4

from src.database.models import User, Account, Transaction, Category, PlaidItem, Institution
from src.dependencies.auth import get_current_user, get_current_verified_user, verify_api_key
from src.utils.security import hash_password, verify_password
from src.middleware.security_headers import SecurityHeadersMiddleware
from src.middleware.rate_limit import RateLimitMiddleware


class TestAuthDependencies:
    """Test authentication dependencies - high impact for coverage."""
    
    @patch('src.dependencies.auth.decode_token')
    async def test_get_current_user_valid_token(self, mock_decode):
        """Test getting current user with valid token."""
        from fastapi import HTTPException
        
        # Mock valid token decode
        mock_decode.return_value = {
            "sub": "test@example.com", 
            "user_id": "123",
            "type": "access"
        }
        
        # Mock database session and query
        db_mock = Mock()
        user_mock = Mock()
        user_mock.id = "123"
        user_mock.email = "test@example.com"
        user_mock.is_active = True
        
        db_mock.query.return_value.filter.return_value.first.return_value = user_mock
        
        result = await get_current_user("valid_token", db_mock)
        assert result == user_mock
    
    @patch('src.dependencies.auth.decode_token')
    async def test_get_current_user_invalid_token(self, mock_decode):
        """Test getting current user with invalid token."""
        from fastapi import HTTPException
        from jose import JWTError
        
        # Mock invalid token decode
        mock_decode.side_effect = JWTError("Invalid token")
        
        db_mock = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user("invalid_token", db_mock)
        
        assert exc_info.value.status_code == 401
    
    @patch('src.dependencies.auth.get_current_user')
    async def test_get_current_verified_user_verified(self, mock_get_user):
        """Test getting verified user when user is verified."""
        # Mock verified user
        user_mock = Mock()
        user_mock.is_verified = True
        mock_get_user.return_value = user_mock
        
        result = await get_current_verified_user("token", Mock())
        assert result == user_mock
    
    @patch('src.dependencies.auth.get_current_user')
    async def test_get_current_verified_user_not_verified(self, mock_get_user):
        """Test getting verified user when user is not verified."""
        from fastapi import HTTPException
        
        # Mock unverified user
        user_mock = Mock()
        user_mock.is_verified = False
        mock_get_user.return_value = user_mock
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_verified_user("token", Mock())
        
        assert exc_info.value.status_code == 403
    
    async def test_verify_api_key_valid(self):
        """Test API key verification with valid key."""
        # Mock database session and query
        db_mock = Mock()
        api_key_mock = Mock()
        api_key_mock.is_active = True
        api_key_mock.expires_at = datetime.utcnow() + timedelta(days=1)
        api_key_mock.permissions = ["read", "write"]
        
        db_mock.query.return_value.filter.return_value.first.return_value = api_key_mock
        
        # Mock hash verification
        with patch('src.dependencies.auth.verify_password', return_value=True):
            result = await verify_api_key("valid_key", db_mock)
            assert result == api_key_mock
    
    async def test_verify_api_key_invalid(self):
        """Test API key verification with invalid key."""
        from fastapi import HTTPException
        
        # Mock database session - no key found
        db_mock = Mock()
        db_mock.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key("invalid_key", db_mock)
        
        assert exc_info.value.status_code == 401


class TestSecurityHeadersMiddleware:
    """Test security headers middleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create SecurityHeadersMiddleware instance."""
        app = Mock()
        return SecurityHeadersMiddleware(app)
    
    async def test_security_headers_added(self, middleware):
        """Test that security headers are added to responses."""
        from fastapi import Response
        
        request = Mock()
        response = Response(content="test", status_code=200)
        call_next = AsyncMock(return_value=response)
        
        result = await middleware.dispatch(request, call_next)
        
        # Check that security headers are present
        expected_headers = [
            "x-content-type-options",
            "x-frame-options", 
            "x-xss-protection",
            "strict-transport-security",
            "content-security-policy"
        ]
        
        for header in expected_headers:
            assert header in result.headers
        
        call_next.assert_called_once_with(request)


class TestRateLimitMiddleware:
    """Test rate limit middleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create RateLimitMiddleware instance."""
        app = Mock()
        return RateLimitMiddleware(app)
    
    async def test_rate_limit_no_redis(self, middleware):
        """Test rate limiting when Redis is unavailable."""
        from fastapi import Response
        
        request = Mock()
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.url = Mock()
        request.url.path = "/test"
        
        response = Response(content="success", status_code=200)
        call_next = AsyncMock(return_value=response)
        
        with patch('src.middleware.rate_limit.get_redis_client', return_value=None):
            result = await middleware.dispatch(request, call_next)
        
        # Should allow request when Redis is unavailable
        assert result == response
        call_next.assert_called_once_with(request)
    
    async def test_rate_limit_under_threshold(self, middleware):
        """Test request under rate limit threshold."""
        from fastapi import Response
        
        request = Mock()
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.url = Mock()
        request.url.path = "/test"
        
        response = Response(content="success", status_code=200)
        call_next = AsyncMock(return_value=response)
        
        with patch('src.middleware.rate_limit.get_redis_client') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = "5"  # Under default limit
            mock_redis.incr.return_value = 6
            mock_redis.expire.return_value = True
            mock_get_redis.return_value = mock_redis
            
            result = await middleware.dispatch(request, call_next)
        
        assert result == response
        call_next.assert_called_once_with(request)


class TestDatabaseModels:
    """Test database model properties and methods."""
    
    def test_user_model_properties(self, db_session: Session):
        """Test User model computed properties."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password_123",
            full_name="Test User",
            is_active=True,
            is_verified=True
        )
        
        # Test string representation uses username or email
        assert "testuser" in repr(user) or "test@example.com" in repr(user)
    
    def test_account_balance_calculations(self, db_session: Session, test_user: User):
        """Test Account balance property calculations."""
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
    
    def test_transaction_amount_calculation(self, db_session: Session, test_account: Account):
        """Test Transaction amount property calculation."""
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


class TestConfigurationCoverage:
    """Test configuration and settings coverage."""
    
    def test_settings_validation(self):
        """Test settings validation methods."""
        from src.config import Settings
        
        # Test environment validation
        settings = Settings()
        
        # Test valid environment
        valid_env = settings.validate_environment("development")
        assert valid_env == "development"
        
        # Test invalid environment should raise ValueError
        with pytest.raises(ValueError):
            settings.validate_environment("invalid")
    
    def test_plaid_environment_validation(self):
        """Test Plaid environment validation.""" 
        from src.config import Settings
        
        settings = Settings()
        
        # Test valid Plaid environment
        valid_env = settings.validate_plaid_environment("sandbox")
        assert valid_env == "sandbox"
        
        # Test invalid Plaid environment
        with pytest.raises(ValueError):
            settings.validate_plaid_environment("invalid")


class TestSchemaValidation:
    """Test Pydantic schema validation and properties."""
    
    def test_account_schema_properties(self):
        """Test Account schema computed properties."""
        from src.schemas.account import Account
        
        account_data = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "plaid_account_id": "acc_123",
            "plaid_item_id": str(uuid4()),
            "institution_id": str(uuid4()),
            "name": "Test Account",
            "type": "depository",
            "subtype": "checking",
            "current_balance_cents": 150050,
            "available_balance_cents": 145075,
            "limit_cents": 200000,
            "iso_currency_code": "USD",
            "is_active": True,
            "is_hidden": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        account = Account(**account_data)
        
        # Test computed properties
        assert account.current_balance == 1500.50
        assert account.available_balance == 1450.75
        assert account.limit == 2000.00
    
    def test_transaction_schema_properties(self):
        """Test Transaction schema computed properties."""
        from src.schemas.transaction import Transaction
        
        transaction_data = {
            "id": str(uuid4()),
            "account_id": str(uuid4()),
            "plaid_transaction_id": "txn_123",
            "amount_cents": -2550,
            "date": date.today(),
            "name": "Test Transaction",
            "pending": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        transaction = Transaction(**transaction_data)
        
        # Test computed property
        assert transaction.amount == -25.50
    
    def test_category_schema_validation(self):
        """Test Category schema validation."""
        from src.schemas.category import Category
        
        category_data = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "name": "Groceries",
            "type": "expense",
            "color": "#4CAF50",
            "icon": "shopping_cart",
            "description": "Food expenses",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        category = Category(**category_data)
        
        assert category.name == "Groceries"
        assert category.type == "expense"
        assert category.color == "#4CAF50"


class TestUtilityFunctions:
    """Test utility functions for coverage."""
    
    def test_security_password_functions(self):
        """Test password hashing and verification."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    def test_json_encoder_edge_cases(self):
        """Test JSON encoder edge cases."""
        from src.utils.json_encoder import DateTimeEncoder, jsonable_encoder_custom
        from datetime import date
        
        encoder = DateTimeEncoder()
        
        # Test date encoding
        test_date = date(2024, 1, 1)
        result = encoder.default(test_date)
        assert result == "2024-01-01"
        
        # Test UUID encoding  
        test_uuid = uuid4()
        result = encoder.default(test_uuid)
        assert result == str(test_uuid)
        
        # Test nested data structures
        complex_data = {
            "timestamp": datetime(2024, 1, 1, 12, 0, 0),
            "nested": {
                "date": date(2024, 1, 1),
                "id": uuid4()
            },
            "list": [datetime(2024, 1, 2), "string", 123]
        }
        
        result = jsonable_encoder_custom(complex_data)
        assert isinstance(result["timestamp"], str)
        assert isinstance(result["nested"]["date"], str)
        assert isinstance(result["nested"]["id"], str)
        assert isinstance(result["list"][0], str)


class TestDatabaseConnection:
    """Test database connection utilities."""
    
    @patch('src.database.base.create_engine')
    def test_database_connection_success(self, mock_create_engine):
        """Test successful database connection."""
        from src.database.base import check_db_connection
        
        # Mock successful connection
        mock_engine = Mock()
        mock_connection = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.return_value = Mock()
        mock_create_engine.return_value = mock_engine
        
        result = check_db_connection()
        assert result is True
    
    @patch('src.database.base.create_engine')
    def test_database_connection_failure(self, mock_create_engine):
        """Test database connection failure."""
        from src.database.base import check_db_connection
        
        # Mock connection failure
        mock_create_engine.side_effect = Exception("Connection failed")
        
        result = check_db_connection()
        assert result is False