"""Performance monitoring middleware."""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track request performance metrics.

    Tracks:
    - Request duration
    - Response status codes
    - Endpoint performance
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.request_count = 0
        self.total_duration = 0.0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track performance metrics."""
        start_time = time.time()

        # Add request ID for tracing
        request_id = request.headers.get("X-Request-ID", f"req_{int(start_time * 1000)}")

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time
            duration_ms = duration * 1000

            # Track metrics
            self.request_count += 1
            self.total_duration += duration

            # Add performance headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            # Log slow requests (> 1 second)
            if duration > 1.0:
                logger.warning(
                    f"Slow request detected",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": duration_ms,
                        "status_code": response.status_code
                    }
                )

            # Log request metrics
            logger.info(
                f"{request.method} {request.url.path} - {response.status_code} - {duration_ms:.2f}ms",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "status_code": response.status_code
                }
            )

            return response

        except Exception as e:
            duration = time.time() - start_time
            duration_ms = duration * 1000

            # Log error with performance data
            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "error": str(e)
                },
                exc_info=True
            )

            raise

    def get_stats(self) -> dict:
        """Get performance statistics."""
        avg_duration = (
            self.total_duration / self.request_count
            if self.request_count > 0
            else 0
        )

        return {
            "total_requests": self.request_count,
            "total_duration_seconds": round(self.total_duration, 2),
            "average_duration_ms": round(avg_duration * 1000, 2)
        }
