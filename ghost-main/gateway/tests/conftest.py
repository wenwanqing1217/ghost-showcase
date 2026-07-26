"""
Gateway test fixtures — mock backend services for isolated gateway testing.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock

from app import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Reset rate limit buckets before each test to prevent state leakage."""
    from app import _rate_buckets
    _rate_buckets.clear()
    yield
    _rate_buckets.clear()


@pytest.fixture
async def gateway_client():
    """Create an ASGI transport client for the gateway (no real network)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _make_response(status_code=200, json_data=None, text=None):
    """Build a mock httpx.Response with concrete status_code (int, not Mock)."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data if json_data is not None else {}
    resp.text = text if text is not None else "{}"
    return resp


def _default_get(url, **kwargs):
    """Default mock GET: 200 with simple JSON."""
    return _make_response(200, {"status": "ok", "data": "ok"})


def _default_post(url, **kwargs):
    """Default mock POST: 200 with success envelope."""
    return _make_response(200, {"success": True, "data": {"result": "ok"}})


def _make_mock_client():
    """
    Build a mock httpx.AsyncClient.
    Uses side_effect so callers can override per-test via mock_client.get.side_effect = ...
    """
    mock = MagicMock(name="MockAsyncClient")
    mock.get = AsyncMock(side_effect=_default_get)
    mock.post = AsyncMock(side_effect=_default_post)
    mock.aclose = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def mock_client():
    """
    Replace httpx.AsyncClient with a mock so lifespan startup creates the mock.
    This prevents real HTTP connections from being made.
    """
    mock = _make_mock_client()
    with patch("httpx.AsyncClient", return_value=mock):
        yield mock
