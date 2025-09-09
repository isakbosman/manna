"""
Comprehensive tests for utility modules.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from uuid import uuid4
import json

from src.utils.json_encoder import DateTimeEncoder, jsonable_encoder_custom
from src.utils.security import (
    create_access_token, 
    decode_token, 
    hash_password, 
    verify_password,
    generate_password_reset_token,
    validate_password_strength
)


class TestJSONEncoder:
    """Test custom JSON encoder utilities."""
    
    def test_datetime_encoder_datetime(self):
        """Test encoding datetime objects."""
        encoder = DateTimeEncoder()
        dt = datetime(2024, 1, 1, 12, 0, 0)
        
        result = encoder.default(dt)
        assert result == "2024-01-01T12:00:00"
    
    def test_datetime_encoder_date(self):
        """Test encoding date objects."""
        from datetime import date
        encoder = DateTimeEncoder()
        d = date(2024, 1, 1)
        
        result = encoder.default(d)
        assert result == "2024-01-01"
    
    def test_datetime_encoder_uuid(self):
        """Test encoding UUID objects."""
        encoder = DateTimeEncoder()
        uuid_obj = uuid4()
        
        result = encoder.default(uuid_obj)
        assert result == str(uuid_obj)
    
    def test_datetime_encoder_fallback(self):
        """Test encoder fallback for unsupported types."""
        encoder = DateTimeEncoder()
        
        with pytest.raises(TypeError):
            encoder.default(object())
    
    def test_jsonable_encoder_custom_datetime(self):
        """Test custom jsonable encoder with datetime."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = jsonable_encoder_custom(dt)
        assert result == "2024-01-01T12:00:00"
    
    def test_jsonable_encoder_custom_dict(self):
        """Test custom jsonable encoder with dict containing datetime."""
        data = {
            "timestamp": datetime(2024, 1, 1, 12, 0, 0),
            "name": "test",
            "id": uuid4()
        }
        
        result = jsonable_encoder_custom(data)
        
        assert result["timestamp"] == "2024-01-01T12:00:00"
        assert result["name"] == "test"
        assert isinstance(result["id"], str)
    
    def test_jsonable_encoder_custom_list(self):
        """Test custom jsonable encoder with list containing datetime."""
        data = [
            datetime(2024, 1, 1, 12, 0, 0),
            "test",
            uuid4()
        ]
        
        result = jsonable_encoder_custom(data)
        
        assert result[0] == "2024-01-01T12:00:00"
        assert result[1] == "test"
        assert isinstance(result[2], str)


class TestSecurityUtils:
    """Test security utility functions."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$")  # bcrypt hash format
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    @patch('src.utils.security.datetime')
    def test_create_access_token(self, mock_datetime):
        """Test JWT access token creation."""
        # Mock datetime for consistent testing
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        
        data = {"sub": "test@example.com", "user_id": "123"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT tokens have 3 parts separated by dots
        assert len(token.split('.')) == 3
    
    @patch('src.utils.security.datetime')
    def test_create_access_token_with_expires_delta(self, mock_datetime):
        """Test JWT token creation with custom expiration."""
        from datetime import timedelta
        
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(hours=2)
        
        token = create_access_token(data, expires_delta=expires_delta)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_token_valid(self):
        """Test token decoding with valid token."""
        data = {"sub": "test@example.com", "user_id": "123"}
        token = create_access_token(data)
        
        payload = decode_token(token)
        
        assert payload is not None
        assert payload.get("sub") == "test@example.com"
        assert payload.get("user_id") == "123"
    
    def test_decode_token_invalid(self):
        """Test token decoding with invalid token."""
        from jose import JWTError
        invalid_token = "invalid.token.here"
        
        with pytest.raises(JWTError):
            decode_token(invalid_token)
    
    def test_decode_token_expired(self):
        """Test token decoding with expired token."""
        from datetime import timedelta
        from jose import JWTError
        
        # Create token with very short expiration
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(seconds=-1)  # Already expired
        
        token = create_access_token(data, expires_delta=expires_delta)
        
        with pytest.raises(JWTError):
            decode_token(token)
    
    def test_generate_password_reset_token(self):
        """Test password reset token generation."""
        # Test default length
        token = generate_password_reset_token()
        assert len(token) == 32
        assert isinstance(token, str)
        
        # Test that multiple calls generate different tokens
        token1 = generate_password_reset_token()
        token2 = generate_password_reset_token()
        assert token1 != token2
    
    def test_validate_password_strength_valid(self):
        """Test password strength validation with valid password."""
        valid_password = "StrongPass123!"
        
        is_valid, message = validate_password_strength(valid_password)
        
        assert is_valid is True
        assert message == ""
    
    def test_validate_password_strength_too_short(self):
        """Test password strength validation with short password."""
        short_password = "Sh1!"
        
        is_valid, message = validate_password_strength(short_password)
        
        assert is_valid is False
        assert "must be at least" in message
    
    def test_validate_password_strength_missing_uppercase(self):
        """Test password strength validation missing uppercase."""
        password = "lowercase123!"
        
        is_valid, message = validate_password_strength(password)
        
        assert is_valid is False
        assert "uppercase" in message
    
    def test_validate_password_strength_missing_special(self):
        """Test password strength validation missing special character."""
        password = "Password123"
        
        is_valid, message = validate_password_strength(password)
        
        assert is_valid is False
        assert "special character" in message


class TestRedisUtils:
    """Test Redis utility functions."""
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        return MagicMock()
    
    @patch('src.utils.redis.redis.from_url')
    async def test_get_redis_client_success(self, mock_from_url):
        """Test successful Redis client creation."""
        from src.utils.redis import get_redis_client
        
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        
        client = await get_redis_client()
        
        assert client == mock_client
    
    @patch('src.utils.redis.redis.from_url')
    async def test_get_redis_client_connection_error(self, mock_from_url):
        """Test Redis client creation with connection error."""
        from src.utils.redis import get_redis_client
        
        mock_from_url.side_effect = Exception("Connection failed")
        
        client = await get_redis_client()
        
        assert client is None
    
    @patch('src.utils.redis.get_redis_client')
    async def test_check_redis_connection_success(self, mock_get_client):
        """Test successful Redis connection check."""
        from src.utils.redis import check_redis_connection
        
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_get_client.return_value = mock_client
        
        result = await check_redis_connection()
        
        assert result is True
        mock_client.ping.assert_called_once()
    
    @patch('src.utils.redis.get_redis_client')
    async def test_check_redis_connection_no_client(self, mock_get_client):
        """Test Redis connection check with no client."""
        from src.utils.redis import check_redis_connection
        
        mock_get_client.return_value = None
        
        result = await check_redis_connection()
        
        assert result is False
    
    @patch('src.utils.redis.get_redis_client')
    async def test_check_redis_connection_ping_fails(self, mock_get_client):
        """Test Redis connection check when ping fails."""
        from src.utils.redis import check_redis_connection
        
        mock_client = MagicMock()
        mock_client.ping.side_effect = Exception("Ping failed")
        mock_get_client.return_value = mock_client
        
        result = await check_redis_connection()
        
        assert result is False
    
    @patch('src.utils.redis.get_redis_client')
    async def test_cache_set_success(self, mock_get_client):
        """Test successful cache set operation."""
        from src.utils.redis import cache_set
        
        mock_client = MagicMock()
        mock_client.setex.return_value = True
        mock_get_client.return_value = mock_client
        
        result = await cache_set("test_key", "test_value", 300)
        
        assert result is True
        mock_client.setex.assert_called_once_with("test_key", 300, "test_value")
    
    @patch('src.utils.redis.get_redis_client')
    async def test_cache_set_no_client(self, mock_get_client):
        """Test cache set with no Redis client."""
        from src.utils.redis import cache_set
        
        mock_get_client.return_value = None
        
        result = await cache_set("test_key", "test_value", 300)
        
        assert result is False
    
    @patch('src.utils.redis.get_redis_client')
    async def test_cache_get_success(self, mock_get_client):
        """Test successful cache get operation."""
        from src.utils.redis import cache_get
        
        mock_client = MagicMock()
        mock_client.get.return_value = b"test_value"
        mock_get_client.return_value = mock_client
        
        result = await cache_get("test_key")
        
        assert result == "test_value"
        mock_client.get.assert_called_once_with("test_key")
    
    @patch('src.utils.redis.get_redis_client')
    async def test_cache_get_not_found(self, mock_get_client):
        """Test cache get when key not found."""
        from src.utils.redis import cache_get
        
        mock_client = MagicMock()
        mock_client.get.return_value = None
        mock_get_client.return_value = mock_client
        
        result = await cache_get("test_key")
        
        assert result is None
    
    @patch('src.utils.redis.get_redis_client')
    async def test_cache_delete_success(self, mock_get_client):
        """Test successful cache delete operation."""
        from src.utils.redis import cache_delete
        
        mock_client = MagicMock()
        mock_client.delete.return_value = 1
        mock_get_client.return_value = mock_client
        
        result = await cache_delete("test_key")
        
        assert result is True
        mock_client.delete.assert_called_once_with("test_key")
    
    @patch('src.utils.redis.get_redis_client')
    async def test_cache_delete_not_found(self, mock_get_client):
        """Test cache delete when key not found."""
        from src.utils.redis import cache_delete
        
        mock_client = MagicMock()
        mock_client.delete.return_value = 0
        mock_get_client.return_value = mock_client
        
        result = await cache_delete("test_key")
        
        assert result is False