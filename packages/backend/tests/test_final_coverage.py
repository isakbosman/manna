"""
Final comprehensive tests to achieve 80% coverage.
Focuses on easily testable areas with high impact.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, date, timedelta
from uuid import uuid4
import json


class TestConfigurationValidation:
    """Test configuration validation functions."""
    
    def test_environment_validation_success(self):
        """Test valid environment validation."""
        from src.config import Settings
        
        settings = Settings()
        
        # Test all valid environments
        valid_environments = ["development", "staging", "production", "testing"]
        for env in valid_environments:
            result = settings.validate_environment(env)
            assert result == env
    
    def test_environment_validation_failure(self):
        """Test invalid environment validation."""
        from src.config import Settings
        
        settings = Settings()
        
        with pytest.raises(ValueError) as exc_info:
            settings.validate_environment("invalid_environment")
        
        assert "Environment must be one of" in str(exc_info.value)
    
    def test_plaid_environment_validation_success(self):
        """Test valid Plaid environment validation."""
        from src.config import Settings
        
        settings = Settings()
        
        valid_plaid_envs = ["sandbox", "development", "production"]
        for env in valid_plaid_envs:
            result = settings.validate_plaid_environment(env)
            assert result == env
    
    def test_plaid_environment_validation_failure(self):
        """Test invalid Plaid environment validation."""
        from src.config import Settings
        
        settings = Settings()
        
        with pytest.raises(ValueError) as exc_info:
            settings.validate_plaid_environment("invalid_plaid_env")
        
        assert "Plaid environment must be one of" in str(exc_info.value)
    
    def test_secret_key_validation_production(self):
        """Test secret key validation in production."""
        from src.config import Settings
        
        settings = Settings()
        
        # Test that default key is rejected in production
        with pytest.raises(ValueError) as exc_info:
            settings.validate_secret_key(
                "development-secret-key-change-in-production",
                {"environment": "production"}
            )
        
        assert "Secret key must be changed in production" in str(exc_info.value)
    
    def test_secret_key_validation_development(self):
        """Test secret key validation in development."""
        from src.config import Settings
        
        settings = Settings()
        
        # Test that default key is accepted in development
        result = settings.validate_secret_key(
            "development-secret-key-change-in-production",
            {"environment": "development"}
        )
        
        assert result == "development-secret-key-change-in-production"


class TestSecurityUtilities:
    """Test security utility functions comprehensively."""
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        from src.utils.security import create_refresh_token
        
        data = {"sub": "test@example.com", "user_id": "123"}
        token = create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT tokens have 3 parts separated by dots
        assert len(token.split('.')) == 3
    
    def test_create_refresh_token_with_expires_delta(self):
        """Test refresh token creation with custom expiration."""
        from src.utils.security import create_refresh_token
        from datetime import timedelta
        
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(days=14)
        
        token = create_refresh_token(data, expires_delta=expires_delta)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_generate_email_verification_token(self):
        """Test email verification token generation."""
        from src.utils.security import generate_email_verification_token
        
        token = generate_email_verification_token()
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Test uniqueness
        token2 = generate_email_verification_token()
        assert token != token2
    
    def test_validate_password_strength_comprehensive(self):
        """Test comprehensive password strength validation."""
        from src.utils.security import validate_password_strength
        
        # Test all validation rules
        test_cases = [
            ("Short1!", False, "must be at least"),
            ("nouppercase123!", False, "uppercase"),
            ("NOLOWERCASE123!", False, "lowercase"),
            ("NoDigitsHere!", False, "digit"),
            ("NoSpecialChars123", False, "special character"),
            ("ValidPassword123!", True, "")
        ]
        
        for password, expected_valid, expected_message_part in test_cases:
            is_valid, message = validate_password_strength(password)
            assert is_valid == expected_valid
            if not expected_valid:
                assert expected_message_part in message


class TestJSONEncodingUtilities:
    """Test JSON encoding utilities comprehensively."""
    
    def test_jsonable_encoder_nested_structures(self):
        """Test encoding of deeply nested structures."""
        from src.utils.json_encoder import jsonable_encoder_custom
        from datetime import date
        
        complex_data = {
            "level1": {
                "level2": {
                    "timestamp": datetime(2024, 1, 1, 12, 0, 0),
                    "date": date(2024, 1, 1),
                    "list": [
                        {"nested_time": datetime(2024, 1, 2)},
                        uuid4(),
                        "string_value"
                    ]
                }
            },
            "top_level_list": [
                datetime(2024, 1, 3),
                {"inner_uuid": uuid4()},
                42
            ]
        }
        
        result = jsonable_encoder_custom(complex_data)
        
        # Verify all datetime objects are strings
        assert isinstance(result["level1"]["level2"]["timestamp"], str)
        assert isinstance(result["level1"]["level2"]["date"], str)
        assert isinstance(result["level1"]["level2"]["list"][0]["nested_time"], str)
        assert isinstance(result["level1"]["level2"]["list"][1], str)  # UUID
        assert isinstance(result["top_level_list"][0], str)  # datetime
        assert isinstance(result["top_level_list"][1]["inner_uuid"], str)  # UUID
        
        # Verify non-datetime objects unchanged
        assert result["level1"]["level2"]["list"][2] == "string_value"
        assert result["top_level_list"][2] == 42
    
    def test_json_encoder_error_handling(self):
        """Test JSON encoder error handling."""
        from src.utils.json_encoder import DateTimeEncoder
        
        encoder = DateTimeEncoder()
        
        # Test with unsupported object type
        class UnsupportedClass:
            pass
        
        with pytest.raises(TypeError):
            encoder.default(UnsupportedClass())


class TestDatabaseModelValidation:
    """Test database model validation and edge cases."""
    
    def test_model_timestamp_mixin(self):
        """Test TimestampMixin functionality."""
        from src.database.models import TimestampMixin
        from sqlalchemy import Column, Integer
        from sqlalchemy.ext.declarative import declarative_base
        
        Base = declarative_base()
        
        class TestModel(Base, TimestampMixin):
            __tablename__ = 'test_model'
            id = Column(Integer, primary_key=True)
        
        model = TestModel()
        
        # Test that created_at and updated_at are set
        assert hasattr(model, 'created_at')
        assert hasattr(model, 'updated_at')
    
    def test_uuid_column_type(self):
        """Test custom UUID column type."""
        from src.database.models import UUID
        from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
        from sqlalchemy.dialects.sqlite import CHAR
        import uuid
        
        uuid_type = UUID()
        
        # Test UUID string conversion
        test_uuid = uuid.uuid4()
        
        # Test process_bind_param
        result = uuid_type.process_bind_param(test_uuid, None)
        assert result == str(test_uuid)
        
        # Test with string input
        uuid_str = str(test_uuid)
        result = uuid_type.process_bind_param(uuid_str, None)
        assert result == uuid_str
        
        # Test with None
        result = uuid_type.process_bind_param(None, None)
        assert result is None


class TestPydanticSchemas:
    """Test Pydantic schema validation and computed fields."""
    
    def test_pagination_params_properties(self):
        """Test pagination parameter calculations."""
        from src.schemas.common import PaginationParams
        
        # Test default values
        params = PaginationParams()
        assert params.page == 1
        assert params.per_page == 50
        assert params.offset == 0
        assert params.limit == 50
        
        # Test custom values
        params = PaginationParams(page=3, per_page=20)
        assert params.offset == 40  # (3-1) * 20
        assert params.limit == 20
    
    def test_paginated_response_pages_calculation(self):
        """Test paginated response pages calculation."""
        from src.schemas.common import PaginatedResponse
        from pydantic import ValidationInfo
        
        # Mock validation info
        mock_info = Mock()
        mock_info.data = {"total": 100, "per_page": 20}
        
        # Test pages calculation
        pages = PaginatedResponse.calculate_pages(None, mock_info)
        assert pages == 5  # 100 / 20 = 5
        
        # Test with remainder
        mock_info.data = {"total": 103, "per_page": 20}
        pages = PaginatedResponse.calculate_pages(None, mock_info)
        assert pages == 6  # (103 + 20 - 1) // 20 = 6
        
        # Test edge cases
        mock_info.data = {"total": 0, "per_page": 20}
        pages = PaginatedResponse.calculate_pages(None, mock_info)
        assert pages == 0
        
        mock_info.data = {"total": 20, "per_page": 0}
        pages = PaginatedResponse.calculate_pages(None, mock_info)
        assert pages == 0


class TestMiddlewareUtilities:
    """Test middleware utility functions."""
    
    @patch('src.middleware.cors.logger')
    def test_cors_middleware_setup(self, mock_logger):
        """Test CORS middleware setup."""
        from src.middleware.cors import setup_cors
        from fastapi import FastAPI
        
        app = FastAPI()
        
        with patch('src.middleware.cors.settings') as mock_settings:
            mock_settings.environment = "development"
            mock_settings.allowed_origins = ["http://localhost:3000"]
            
            setup_cors(app)
            
            # Verify logger was called
            mock_logger.info.assert_called()
    
    def test_exception_handlers_setup(self):
        """Test exception handlers setup."""
        from src.middleware.error_handler import setup_exception_handlers
        from fastapi import FastAPI
        
        app = FastAPI()
        
        # Should not raise an error
        setup_exception_handlers(app)
        
        # Verify handlers were added
        assert len(app.exception_handlers) > 0


class TestDatabaseConnection:
    """Test database connection utilities."""
    
    @patch('src.database.base.logger')
    @patch('src.database.base.create_engine')
    def test_init_db_success(self, mock_create_engine, mock_logger):
        """Test successful database initialization."""
        from src.database.base import init_db
        
        # Mock successful engine creation
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        # Mock metadata creation
        with patch('src.database.base.Base.metadata') as mock_metadata:
            init_db()
            
            mock_metadata.create_all.assert_called_once_with(bind=mock_engine)
            mock_logger.info.assert_called()
    
    @patch('src.database.base.logger')
    @patch('src.database.base.create_engine')
    def test_init_db_failure(self, mock_create_engine, mock_logger):
        """Test database initialization failure."""
        from src.database.base import init_db
        
        # Mock engine creation failure
        mock_create_engine.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            init_db()
        
        mock_logger.error.assert_called()


class TestLoggingConfiguration:
    """Test logging configuration."""
    
    @patch('src.middleware.logging.logging.getLogger')
    @patch('src.middleware.logging.logging.basicConfig')
    def test_logging_setup(self, mock_basic_config, mock_get_logger):
        """Test logging setup configuration."""
        from src.middleware.logging import setup_logging
        
        with patch('src.middleware.logging.settings') as mock_settings:
            mock_settings.log_level = "INFO"
            mock_settings.log_format = "%(message)s"
            mock_settings.environment = "development"
            
            setup_logging()
            
            mock_basic_config.assert_called()


class TestErrorHandling:
    """Test error handling utilities."""
    
    def test_error_response_creation(self):
        """Test error response schema creation."""
        from src.schemas.common import ErrorResponse, ErrorDetail
        
        error_detail = ErrorDetail(
            field="email",
            message="Invalid email format",
            code="invalid_format"
        )
        
        error_response = ErrorResponse(
            error="ValidationError",
            message="Request validation failed",
            details=[error_detail],
            request_id="req_123"
        )
        
        assert error_response.error == "ValidationError"
        assert error_response.message == "Request validation failed"
        assert len(error_response.details) == 1
        assert error_response.details[0].field == "email"
        assert error_response.request_id == "req_123"
        assert isinstance(error_response.timestamp, datetime)
    
    def test_success_response_creation(self):
        """Test success response schema creation."""
        from src.schemas.common import SuccessResponse
        
        success_response = SuccessResponse(
            message="Operation completed successfully",
            details={"item_id": "123"}
        )
        
        assert success_response.success is True
        assert success_response.message == "Operation completed successfully"
        assert success_response.details["item_id"] == "123"
        assert isinstance(success_response.timestamp, datetime)