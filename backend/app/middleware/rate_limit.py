"""
Rate limiting middleware for FastAPI.
Simple in-memory rate limiter using dictionary-based tracking.
Different rate limits for auth endpoints vs general endpoints.
"""

import time
from typing import Callable

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory rate limiting middleware.
    - Default: 100 requests per minute per IP
    - Auth endpoints: 20 requests per minute per IP (brute force protection)
    """

    # Rate limit configuration (requests per 60 seconds)
    DEFAULT_LIMIT = 100
    AUTH_LIMIT = 20
    WINDOW_SIZE = 60  # seconds

    # Auth endpoints that need stricter rate limiting
    AUTH_PATHS = {
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
    }

    def __init__(self, app):
        super().__init__(app)
        # In-memory store: {ip_address: [(timestamp, count), ...]}
        self.requests = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit and process request."""
        client_ip = self._get_client_ip(request)
        is_auth_endpoint = request.url.path in self.AUTH_PATHS

        # Determine rate limit
        limit = self.AUTH_LIMIT if is_auth_endpoint else self.DEFAULT_LIMIT

        # Check rate limit
        if not self._is_within_limit(client_ip, limit):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please try again later."},
            )

        # Cleanup old entries periodically (every 100 requests)
        if len(self.requests) % 100 == 0:
            self._cleanup_expired_entries()

        # Process request
        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP from request.
        Respects X-Forwarded-For and X-Real-IP headers for proxied requests.
        """
        if forwarded := request.headers.get("x-forwarded-for"):
            # X-Forwarded-For can contain multiple IPs; use the first one
            return forwarded.split(",")[0].strip()
        if real_ip := request.headers.get("x-real-ip"):
            return real_ip.strip()
        return request.client.host if request.client else "unknown"

    def _is_within_limit(self, client_ip: str, limit: int) -> bool:
        """
        Check if the client is within the rate limit.
        Returns True if request is allowed, False if rate limit exceeded.
        """
        now = time.time()

        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Get requests within the current window
        request_times = self.requests[client_ip]
        window_start = now - self.WINDOW_SIZE

        # Remove old requests outside the window
        request_times[:] = [ts for ts in request_times if ts > window_start]

        # Check if within limit
        if len(request_times) >= limit:
            return False

        # Add current request
        request_times.append(now)
        return True

    def _cleanup_expired_entries(self) -> None:
        """
        Clean up rate limit entries for IPs with no recent requests.
        Called periodically to prevent unbounded memory growth.
        """
        now = time.time()
        window_start = now - self.WINDOW_SIZE

        # Remove IPs with no requests in the current window
        ips_to_remove = [
            ip
            for ip, times in self.requests.items()
            if not any(ts > window_start for ts in times)
        ]

        for ip in ips_to_remove:
            del self.requests[ip]
