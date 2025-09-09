"""
Comprehensive tests for middleware modules.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi import Request, Response, HTTPException
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from src.middleware.request_id import RequestIdMiddleware
from src.middleware.cors import setup_cors
from src.middleware.error_handler import ErrorHandlerMiddleware
from src.middleware.logging import LoggingMiddleware
from src.middleware.rate_limit import RateLimitMiddleware
from src.middleware.security_headers import SecurityHeadersMiddleware


class TestRequestIdMiddleware:
    """Test request ID middleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create RequestIdMiddleware instance."""
        app = Mock()
        return RequestIdMiddleware(app)
    
    async def test_request_id_added_to_headers(self, middleware):
        """Test that request ID is added to response headers."""
        # Mock request and response
        request = Mock()
        request.headers = {}
        
        # Mock call_next to return a response
        response = Response(content="test", status_code=200)
        call_next = AsyncMock(return_value=response)
        
        # Call middleware
        result = await middleware.dispatch(request, call_next)
        
        # Verify request ID was added
        assert "x-request-id" in result.headers
        assert len(result.headers["x-request-id"]) > 0
        call_next.assert_called_once_with(request)
    
    async def test_existing_request_id_preserved(self, middleware):
        """Test that existing request ID in headers is preserved."""
        existing_id = "existing-request-id-123"
        
        request = Mock()
        request.headers = {"x-request-id": existing_id}
        
        response = Response(content="test", status_code=200)
        call_next = AsyncMock(return_value=response)
        
        result = await middleware.dispatch(request, call_next)
        
        assert result.headers["x-request-id"] == existing_id
    
    async def test_request_id_format(self, middleware):
        """Test that generated request ID has correct format."""
        request = Mock()
        request.headers = {}
        
        response = Response(content="test", status_code=200)
        call_next = AsyncMock(return_value=response)
        
        result = await middleware.dispatch(request, call_next)
        
        request_id = result.headers["x-request-id"]
        # Should be a UUID format
        assert len(request_id.split('-')) == 5
        assert len(request_id) == 36


class TestCORSSetup:
    """Test CORS setup functionality."""
    
    @patch('src.middleware.cors.CORSMiddleware')
    def test_cors_setup_development(self, mock_cors_middleware):
        """Test CORS setup in development environment."""
        from fastapi import FastAPI
        
        app = FastAPI()
        
        with patch('src.middleware.cors.settings') as mock_settings:
            mock_settings.environment = "development"
            mock_settings.allowed_origins = ["http://localhost:3000"]
            
            setup_cors(app)
            
            # Verify CORS middleware was added
            mock_cors_middleware.assert_called_once()
    
    @patch('src.middleware.cors.CORSMiddleware')
    def test_cors_setup_production(self, mock_cors_middleware):
        """Test CORS setup in production environment."""
        from fastapi import FastAPI
        
        app = FastAPI()
        
        with patch('src.middleware.cors.settings') as mock_settings:
            mock_settings.environment = "production"
            mock_settings.allowed_origins = ["https://app.example.com"]
            
            setup_cors(app)
            
            mock_cors_middleware.assert_called_once()


class TestErrorHandlerMiddleware:
    """Test error handler middleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create ErrorHandlerMiddleware instance."""
        app = Mock()
        return ErrorHandlerMiddleware(app)
    
    async def test_successful_request_passthrough(self, middleware):
        """Test that successful requests pass through unchanged."""
        request = Mock()
        response = Response(content="success", status_code=200)
        call_next = AsyncMock(return_value=response)
        
        result = await middleware.dispatch(request, call_next)
        
        assert result == response
        call_next.assert_called_once_with(request)
    
    async def test_http_exception_handling(self, middleware):
        """Test handling of HTTP exceptions."""
        request = Mock()
        request.url = Mock()
        request.url.path = "/test"
        request.method = "GET"
        
        # Mock call_next to raise HTTPException
        http_exception = HTTPException(status_code=404, detail="Not found")
        call_next = AsyncMock(side_effect=http_exception)
        
        with patch('src.middleware.error_handler.logger'):
            result = await middleware.dispatch(request, call_next)
        
        assert result.status_code == 404
    
    async def test_validation_error_handling(self, middleware):
        """Test handling of validation errors."""
        from pydantic import ValidationError
        
        request = Mock()
        request.url = Mock()
        request.url.path = "/test"
        request.method = "POST"
        
        # Create a validation error
        try:
            from pydantic import BaseModel
            
            class TestModel(BaseModel):
                required_field: str
                
            TestModel()  # This will raise ValidationError
        except ValidationError as e:
            validation_error = e
        
        call_next = AsyncMock(side_effect=validation_error)
        
        with patch('src.middleware.error_handler.logger'):
            result = await middleware.dispatch(request, call_next)
        
        assert result.status_code == 422
    
    async def test_general_exception_handling(self, middleware):
        """Test handling of general exceptions."""
        request = Mock()
        request.url = Mock()
        request.url.path = "/test"
        request.method = "GET"
        
        # Mock call_next to raise general exception
        call_next = AsyncMock(side_effect=Exception("Something went wrong"))
        
        with patch('src.middleware.error_handler.logger'):
            result = await middleware.dispatch(request, call_next)
        
        assert result.status_code == 500


class TestLoggingMiddleware:
    """Test logging middleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create LoggingMiddleware instance."""
        app = Mock()
        return LoggingMiddleware(app)
    
    async def test_request_logging(self, middleware):
        """Test that requests are properly logged."""
        request = Mock()
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/test"
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        response = Response(content="test", status_code=200)
        call_next = AsyncMock(return_value=response)
        
        with patch('src.middleware.logging.access_logger') as mock_logger:
            result = await middleware.dispatch(request, call_next)
        
        assert result == response
        # Verify logging was called
        mock_logger.info.assert_called()
        call_next.assert_called_once_with(request)
    
    async def test_request_timing(self, middleware):
        """Test that request timing is logged."""
        request = Mock()
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/test"
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        response = Response(content="test", status_code=200)
        
        # Mock call_next with a slight delay
        async def mock_call_next(req):
            import asyncio
            await asyncio.sleep(0.01)  # 10ms delay
            return response
        
        call_next = mock_call_next
        
        with patch('src.middleware.logging.access_logger') as mock_logger:
            result = await middleware.dispatch(request, call_next)
        
        # Verify timing information was logged
        assert result == response
        mock_logger.info.assert_called()
        
        # Check if duration was logged
        log_call_args = mock_logger.info.call_args[0][0]
        assert "duration" in log_call_args.lower() or "ms" in log_call_args.lower()


class TestRateLimitMiddleware:
    """Test rate limit middleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create RateLimitMiddleware instance."""
        app = Mock()
        return RateLimitMiddleware(app)
    
    async def test_rate_limit_under_threshold(self, middleware):
        """Test request under rate limit threshold."""
        request = Mock()
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.url = Mock()
        request.url.path = "/test"
        
        response = Response(content="success", status_code=200)
        call_next = AsyncMock(return_value=response)
        
        with patch('src.middleware.rate_limit.get_redis_client') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = b"5"  # Under limit
            mock_redis.incr.return_value = 6
            mock_redis.expire.return_value = True
            mock_get_redis.return_value = mock_redis
            
            result = await middleware.dispatch(request, call_next)
        
        assert result == response
        call_next.assert_called_once_with(request)
    
    async def test_rate_limit_exceeded(self, middleware):
        """Test request exceeding rate limit."""
        request = Mock()
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.url = Mock()
        request.url.path = "/test"
        
        call_next = AsyncMock()
        
        with patch('src.middleware.rate_limit.get_redis_client') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = b"100"  # Over limit
            mock_get_redis.return_value = mock_redis
            
            result = await middleware.dispatch(request, call_next)
        
        assert result.status_code == 429
        call_next.assert_not_called()
    
    async def test_rate_limit_no_redis(self, middleware):
        """Test rate limiting when Redis is unavailable."""
        request = Mock()
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.url = Mock()
        request.url.path = "/test"
        
        response = Response(content="success", status_code=200)
        call_next = AsyncMock(return_value=response)
        
        with patch('src.middleware.rate_limit.get_redis_client') as mock_get_redis:
            mock_get_redis.return_value = None
            
            result = await middleware.dispatch(request, call_next)
        
        # Should allow request when Redis is unavailable
        assert result == response
        call_next.assert_called_once_with(request)


class TestSecurityHeadersMiddleware:
    """Test security headers middleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create SecurityHeadersMiddleware instance."""
        app = Mock()
        return SecurityHeadersMiddleware(app)
    
    async def test_security_headers_added(self, middleware):
        """Test that security headers are added to responses."""
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
    
    async def test_security_header_values(self, middleware):
        """Test that security headers have correct values."""
        request = Mock()
        response = Response(content="test", status_code=200)
        call_next = AsyncMock(return_value=response)
        
        result = await middleware.dispatch(request, call_next)
        
        # Check specific header values
        assert result.headers["x-content-type-options"] == "nosniff"
        assert result.headers["x-frame-options"] == "DENY"
        assert result.headers["x-xss-protection"] == "1; mode=block"
        assert "max-age" in result.headers["strict-transport-security"]
        assert "default-src" in result.headers["content-security-policy"]
    
    async def test_existing_headers_preserved(self, middleware):
        """Test that existing response headers are preserved."""
        request = Mock()
        response = Response(content="test", status_code=200)
        response.headers["custom-header"] = "custom-value"
        call_next = AsyncMock(return_value=response)
        
        result = await middleware.dispatch(request, call_next)
        
        # Custom header should be preserved
        assert result.headers["custom-header"] == "custom-value"
        # Security headers should be added
        assert "x-content-type-options" in result.headers