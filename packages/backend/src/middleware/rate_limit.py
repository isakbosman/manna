"""
Rate limiting middleware using Redis.
"""

from fastapi import Request, HTTPException, status
import time
import logging
from typing import Optional
import hashlib

from ..utils.redis import get_redis_client
from ..config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Rate limiting middleware to prevent abuse.
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        exclude_paths: Optional[list] = None
    ):
        self.app = app
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.exclude_paths = exclude_paths or ["/", "/health", "/docs", "/redoc", "/openapi.json"]

    async def __call__(self, scope, receive, send):
        # Only process HTTP requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        from starlette.requests import Request
        from starlette.responses import Response

        request = Request(scope, receive=receive)

        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            await self.app(scope, receive, send)
            return

        # Skip rate limiting in development
        if settings.environment == "development":
            await self.app(scope, receive, send)
            return

        # Get client identifier (IP address or user ID if authenticated)
        client_id = self._get_client_id(request)

        # Check rate limits
        if not await self._check_rate_limit(client_id):
            response = Response(
                content='{"detail":"Rate limit exceeded. Please try again later."}',
                status_code=429,
                media_type="application/json"
            )
            await response(scope, receive, send)
            return

        # Add custom send to inject headers
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                headers[b"x-ratelimit-limit"] = str(self.requests_per_minute).encode()
                remaining = await self._get_remaining_requests(client_id)
                headers[b"x-ratelimit-remaining"] = str(remaining).encode()
                headers[b"x-ratelimit-reset"] = str(int(time.time()) + 60).encode()

                # Convert headers back to list of tuples
                message["headers"] = [(k, v) for k, v in headers.items()]

            await send(message)

        # Process request with modified send
        await self.app(scope, receive, send_wrapper)
    
    def _get_client_id(self, request: Request) -> str:
        """
        Get unique client identifier.
        """
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"
    
    async def _check_rate_limit(self, client_id: str) -> bool:
        """
        Check if client has exceeded rate limit.
        """
        try:
            redis = await get_redis_client()
            if not redis:
                # If Redis is not available, allow request
                return True
            
            # Create keys for different time windows
            minute_key = f"rate_limit:minute:{client_id}"
            hour_key = f"rate_limit:hour:{client_id}"
            
            # Check minute limit
            minute_count = await redis.incr(minute_key)
            if minute_count == 1:
                await redis.expire(minute_key, 60)
            
            if minute_count > self.requests_per_minute:
                return False
            
            # Check hour limit
            hour_count = await redis.incr(hour_key)
            if hour_count == 1:
                await redis.expire(hour_key, 3600)
            
            if hour_count > self.requests_per_hour:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # On error, allow request
            return True
    
    async def _get_remaining_requests(self, client_id: str) -> int:
        """
        Get remaining requests for the current minute.
        """
        try:
            redis = await get_redis_client()
            if not redis:
                return self.requests_per_minute
            
            minute_key = f"rate_limit:minute:{client_id}"
            count = await redis.get(minute_key)
            
            if count is None:
                return self.requests_per_minute
            
            remaining = self.requests_per_minute - int(count)
            return max(0, remaining)
            
        except Exception as e:
            logger.error(f"Failed to get remaining requests: {e}")
            return self.requests_per_minute