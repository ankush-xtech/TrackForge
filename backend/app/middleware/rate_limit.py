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
    Uses SEPARATE buckets for auth vs general requests so they don't interfere.
    - Default: 200 requests per minute per IP
    - Auth endpoints: 30 requests per minute per IP (brute force protection)
    """

    # Rate limit configuration (requests per 60 seconds)
    DEFAULT_LIMIT = 200
    AUTH_LIMIT = 30
    WINDOW_SIZE = 60  # seconds

    # Auth endpoints that need stricter rate limiting (login/register only)
    AUTH_PATHS = {
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
    }

    def __init__(self, app):
        super().__init__(app)
        # Separate stores for auth and general requests
        self.auth_requests: dict[str, list[float]] = {}
        self.general_requests: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit and process request."""
        client_ip = self._get_client_ip(request)
        is_auth_endpoint = request.url.path in self.AUTH_PATHS

        # Use the correct bucket and limit
        if is_auth_endpoint:
            store = self.auth_requests
            limit = self.AUTH_LIMIT
        else:
            store = self.general_requests
            limit = self.DEFAULT_LIMIT

        # Check rate limit
        if not self._is_within_limit(store, client_ip, limit):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please try again later."},
            )

        # Cleanup old entries periodically
        total = len(self.auth_requests) + len(self.general_requests)
        if total > 0 and total % 100 == 0:
            self._cleanup_expired_entries(self.auth_requests)
            self._cleanup_expired_entries(self.general_requests)

        # Process request
        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP from request.
        Respects X-Forwarded-For and X-Real-IP headers for proxied requests.
        """
        if forwarded := request.headers.get("x-forwarded-for"):
            return forwarded.split(",")[0].strip()
        if real_ip := request.headers.get("x-real-ip"):
            return real_ip.strip()
        return request.client.host if request.client else "unknown"

    @staticmethod
    def _is_within_limit(
        store: dict[str, list[float]], client_ip: str, limit: int
    ) -> bool:
        """
        Check if the client is within the rate limit for a given bucket.
        Returns True if request is allowed, False if rate limit exceeded.
        """
        now = time.time()

        if client_ip not in store:
            store[client_ip] = []

        request_times = store[client_ip]
        window_start = now - RateLimitMiddleware.WINDOW_SIZE

        # Remove old requests outside the window
        request_times[:] = [ts for ts in request_times if ts > window_start]

        if len(request_times) >= limit:
            return False

        request_times.append(now)
        return True

    @staticmethod
    def _cleanup_expired_entries(store: dict[str, list[float]]) -> None:
        """
        Clean up rate limit entries for IPs with no recent requests.
        """
        now = time.time()
        window_start = now - RateLimitMiddleware.WINDOW_SIZE

        ips_to_remove = [
            ip
            for ip, times in store.items()
            if not any(ts > window_start for ts in times)
        ]

        for ip in ips_to_remove:
            del store[ip]
