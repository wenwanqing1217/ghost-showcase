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
    from middleware.rate_limit import _rate_buckets

    _rate_buckets.clear()
    yield
    _rate_buckets.clear()


@pytest.fixture
async def gateway_client(mock_client):
    """
    Create an ASGI transport client for the gateway (no real network).
    Depends on mock_client so the patch is active when lifespan runs,
    ensuring the module-level ``client`` is the mock (not a real httpx.AsyncClient).
    """
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
    Supports `async with client as c:` pattern via __aenter__/__aexit__.

    The ``request`` method dispatches to get/post based on HTTP method, so tests
    can keep setting ``mock_client.get.side_effect`` / ``mock_client.post.side_effect``
    while the proxy uses the unified ``client.request(method, url, ...)`` interface.
    """
    mock = MagicMock(name="MockAsyncClient")
    mock.get = AsyncMock(side_effect=_default_get)
    mock.post = AsyncMock(side_effect=_default_post)
    mock.aclose = AsyncMock(return_value=None)
    # Support `async with httpx.AsyncClient(...) as client:` pattern
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=False)

    # Dispatch client.request() to the appropriate get/post mock
    async def _dispatch_request(method, url, **kwargs):
        if method.upper() == "GET":
            return await mock.get(url, **kwargs)
        elif method.upper() == "POST":
            return await mock.post(url, **kwargs)
        return _make_response(200, {"status": "ok"})

    mock.request = AsyncMock(side_effect=_dispatch_request)
    return mock


@pytest.fixture
def mock_client():
    """
    Replace the module-level ``client`` with a mock so proxy functions use it directly.
    Patching httpx.AsyncClient does NOT work because ASGITransport runs the lifespan
    in an inner context where the class-level patch is not visible.

    Patches services.proxy.client — the single source of truth used by both
    the routes (via proxy_get) and the /health endpoint (via _proxy.client).
    """
    import services.proxy as _proxy_module

    mock = _make_mock_client()
    with patch.object(_proxy_module, "client", mock):
        yield mock
