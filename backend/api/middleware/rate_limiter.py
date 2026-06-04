"""Rate limiting middleware."""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """In-memory rate limiter using sliding window with async safety."""

    def __init__(self, requests_per_window: int = 100, window_seconds: int = 60, cleanup_interval: int = 300):
        """
        Initialize rate limiter.

        Args:
            requests_per_window: Max requests per window
            window_seconds: Window size in seconds
            cleanup_interval: Seconds between stale entry cleanups
        """
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self._requests: dict[str, list[datetime]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._last_cleanup = datetime.utcnow()
        self._cleanup_interval = cleanup_interval

    def _stale_entry(self, item: tuple) -> bool:
        """Check if a rate limiter entry is stale (no requests in 2 windows)."""
        key, timestamps = item
        if not timestamps:
            return True
        cutoff = datetime.utcnow() - timedelta(seconds=self.window_seconds * 2)
        return all(t < cutoff for t in timestamps)

    async def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed for given key (thread-safe).

        Args:
            key: Rate limit key (e.g., IP address)

        Returns:
            True if allowed
        """
        async with self._lock:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=self.window_seconds)

            # Periodically purge stale entries to prevent unbounded memory growth
            if (now - self._last_cleanup).total_seconds() > self._cleanup_interval:
                stale_keys = [k for k, v in self._requests.items() if not v or all(t < window_start for t in v)]
                for stale_key in stale_keys:
                    del self._requests[stale_key]
                self._last_cleanup = now

            # Remove old requests for this key
            self._requests[key] = [
                req_time for req_time in self._requests[key]
                if req_time > window_start
            ]

            # Check if under limit
            if len(self._requests[key]) < self.requests_per_window:
                self._requests[key].append(now)
                return True

            return False

    async def get_remaining(self, key: str) -> int:
        """Get remaining requests for key (thread-safe)."""
        async with self._lock:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=self.window_seconds)

            current_requests = [
                req_time for req_time in self._requests[key]
                if req_time > window_start
            ]

            return max(0, self.requests_per_window - len(current_requests))


# Global rate limiter instance (10 submissions per minute per IP)
rate_limiter = RateLimiter(requests_per_window=10, window_seconds=60)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/"]:
            return await call_next(request)

        # Check rate limit (async-safe)
        if not await rate_limiter.is_allowed(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": 60
                },
                headers={
                    "X-RateLimit-Limit": str(rate_limiter.requests_per_window),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "60"
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = await rate_limiter.get_remaining(client_ip)
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.requests_per_window)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
