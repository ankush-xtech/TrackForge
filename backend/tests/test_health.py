"""
Basic health check tests to verify the API starts correctly.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test that the root endpoint returns app info."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["app"] == "WebWork Clone"
        assert "version" in data


@pytest.mark.asyncio
async def test_docs_available():
    """Test that Swagger docs are available in development."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/docs")
        assert response.status_code == 200
