"""
Security headers middleware for enhanced protection.

Adds comprehensive security headers to all responses including
CSP, HSTS, XSS protection, and other security controls.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Dict, Optional
import logging

from ..config import settings
from ..core.audit import log_audit_event, AuditEventType, create_audit_context

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Enhanced security headers middleware.

    Adds comprehensive security headers based on environment
    and configuration settings.
    """

    def __init__(self, app, enable_hsts: bool = True, custom_csp: Optional[str] = None):
        super().__init__(app)
        self.enable_hsts = enable_hsts and settings.environment == "production"
        self.custom_csp = custom_csp
        self.enabled = settings.security_headers_enabled

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        if not self.enabled:
            return response

        # Get security headers based on environment
        security_headers = self._get_security_headers(request)

        # Add headers to response
        for header, value in security_headers.items():
            if value:  # Only add headers with values
                response.headers[header] = value

        # Remove sensitive server information
        response.headers.pop("server", None)
        response.headers.pop("x-powered-by", None)

        # Log security header application in development
        if settings.environment == "development":
            logger.debug(f"Applied {len(security_headers)} security headers")

        return response

    def _get_security_headers(self, request: Request) -> Dict[str, str]:
        """Get security headers based on environment and configuration."""
        headers = {
            # Prevent MIME sniffing
            "X-Content-Type-Options": "nosniff",

            # XSS Protection (deprecated but still useful for older browsers)
            "X-XSS-Protection": "1; mode=block",

            # Frame options - prevent clickjacking
            "X-Frame-Options": "DENY",

            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",

            # Permissions Policy (successor to Feature-Policy)
            "Permissions-Policy": (
                "geolocation=(), "
                "camera=(), "
                "microphone=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "accelerometer=()"
            ),

            # Content Security Policy
            "Content-Security-Policy": self._get_csp_header(),
        }

        # Add HSTS in production with HTTPS
        if self.enable_hsts and self._is_https(request):
            headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Add HTTPS redirect header if needed
        if settings.require_https and not self._is_https(request):
            # Log security violation
            context = create_audit_context(
                ip_address=self._get_client_ip(request),
                endpoint=str(request.url),
                method=request.method
            )
            log_audit_event(
                AuditEventType.SUSPICIOUS_ACTIVITY,
                f"HTTP request to HTTPS-required endpoint: {request.url}",
                context
            )

        return headers

    def _get_csp_header(self) -> str:
        """Generate Content Security Policy header."""
        if self.custom_csp:
            return self.custom_csp

        # Production CSP is more restrictive
        if settings.environment == "production":
            return (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https:; "
                "font-src 'self'; "
                "object-src 'none'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "upgrade-insecure-requests"
            )
        else:
            # Development CSP is more permissive
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https: http:; "
                "connect-src 'self' ws: wss: http: https:; "
                "font-src 'self' data:; "
                "object-src 'none'; "
                "frame-ancestors 'self'"
            )

    def _is_https(self, request: Request) -> bool:
        """Check if request is over HTTPS."""
        # Check scheme
        if request.url.scheme == "https":
            return True

        # Check for forwarded proto header (for reverse proxies)
        forwarded_proto = request.headers.get("x-forwarded-proto")
        if forwarded_proto == "https":
            return True

        return False

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address, considering proxies."""
        # Check X-Forwarded-For header first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP (original client)
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct connection IP
        return request.client.host if request.client else "unknown"
