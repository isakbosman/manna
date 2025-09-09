"""
Security headers middleware for enhanced protection
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Security headers
        security_headers = {
            # Prevent MIME sniffing
            "X-Content-Type-Options": "nosniff",
            
            # XSS Protection
            "X-XSS-Protection": "1; mode=block",
            
            # Frame options
            "X-Frame-Options": "DENY",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Content Security Policy (adjust as needed)
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "font-src 'self' data:; "
                "object-src 'none'; "
                "frame-ancestors 'none';"
            ),
            
            # HSTS (only in production with HTTPS)
            # "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
        }
        
        # Add headers to response
        for header, value in security_headers.items():
            response.headers[header] = value
            
        # Remove server information
        response.headers.pop("server", None)
        
        logger.debug("Security headers added to response")
        return response
