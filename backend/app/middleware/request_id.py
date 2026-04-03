"""
Request ID middleware for FastAPI.
Generates a unique UUID for each request and adds it to response headers.
"""

import uuid
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates and attaches a unique request ID to each request.
    The request ID is added to the response headers as X-Request-ID.
    Useful for request tracing and debugging.
    """

    HEADER_NAME = "X-Request-ID"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Generate request ID and add it to the response."""
        # Generate or retrieve request ID
        request_id = request.headers.get(self.HEADER_NAME) or str(uuid.uuid4())

        # Store in request state for use in handlers
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers[self.HEADER_NAME] = request_id

        return response
