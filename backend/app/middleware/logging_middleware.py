"""
Request logging middleware for FastAPI.
Logs HTTP requests with method, path, status code, and duration.
"""

import logging
import time
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all HTTP requests.
    Includes request method, path, response status code, and duration in milliseconds.
    Skips health check endpoints to reduce noise.
    """

    # Endpoints to skip logging
    SKIP_PATHS = {
        "/health",
        "/healthz",
        "/readiness",
        "/liveness",
        "/metrics",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and log it."""
        # Skip logging for health check endpoints
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        # Record start time
        start_time = time.perf_counter()

        # Process request
        response = await call_next(request)

        # Calculate duration in milliseconds
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log the request
        self._log_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        return response

    @staticmethod
    def _log_request(method: str, path: str, status_code: int, duration_ms: float) -> None:
        """Format and log the request."""
        log_message = f"{method} {path} | {status_code} | {duration_ms:.1f}ms"
        logger.info(log_message)
