"""Security headers middleware for protecting against common web vulnerabilities."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.

    Headers added:
    - Content-Security-Policy: Prevents XSS attacks
    - X-Frame-Options: Prevents clickjacking
    - X-Content-Type-Options: Prevents MIME sniffing
    - Strict-Transport-Security: Enforces HTTPS
    - X-XSS-Protection: Legacy XSS protection
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Controls browser features
    """

    def __init__(
        self,
        app: ASGIApp,
        enable_hsts: bool = True,
        hsts_max_age: int = 31536000,  # 1 year
        csp_directives: str = None
    ):
        """
        Initialize security headers middleware.

        Args:
            app: ASGI application
            enable_hsts: Enable HSTS header (only for HTTPS)
            hsts_max_age: HSTS max-age in seconds
            csp_directives: Custom CSP directives (uses secure defaults if None)
        """
        super().__init__(app)
        self.enable_hsts = enable_hsts
        self.hsts_max_age = hsts_max_age

        # Default CSP: Strict policy for API
        # For production, adjust based on your frontend needs
        self.csp_directives = csp_directives or (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)

        # Content Security Policy - Prevents XSS and injection attacks
        response.headers["Content-Security-Policy"] = self.csp_directives

        # X-Frame-Options - Prevents clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options - Prevents MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection - Legacy XSS protection (for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy - Controls referrer information leakage
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy - Controls browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        # Strict-Transport-Security - Enforces HTTPS (only add if HTTPS)
        # Check if request is HTTPS or behind a proxy (X-Forwarded-Proto)
        if self.enable_hsts:
            is_https = (
                request.url.scheme == "https" or
                request.headers.get("X-Forwarded-Proto") == "https"
            )

            if is_https:
                response.headers["Strict-Transport-Security"] = (
                    f"max-age={self.hsts_max_age}; includeSubDomains; preload"
                )

        # X-Permitted-Cross-Domain-Policies - Restricts Adobe Flash/PDF cross-domain
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # Cache-Control for sensitive endpoints
        if any(path in request.url.path for path in ["/customers", "/conversations", "/metrics"]):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        return response
