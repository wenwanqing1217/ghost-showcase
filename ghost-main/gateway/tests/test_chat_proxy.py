"""
Tests for /v1/chat legacy alias.

Validates:
  - /v1/chat proxies to /v1/human/chat internally
  - Tenant identity headers are forwarded to the internal call
  - alpha_id from body is forwarded as X-Tenant-ID if no header present
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app import app


def _make_response(status_code=200, json_data=None, text=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data if json_data is not None else {}
    resp.text = text if text is not None else "{}"
    return resp


def _make_mock_client(chat_response=None):
    """Build a mock httpx.AsyncClient with configurable chat response."""
    mock = MagicMock(name="MockAsyncClient")
    mock.get = AsyncMock(return_value=_make_response(200, {"status": "ok"}))
    mock.post = AsyncMock(return_value=chat_response or _make_response(200, {"success": True, "data": {"reply": "ok"}}))
    mock.aclose = AsyncMock(return_value=None)
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=False)

    async def _dispatch_request(method, url, **kwargs):
        if method.upper() == "GET":
            return await mock.get(url, **kwargs)
        elif method.upper() == "POST":
            return await mock.post(url, **kwargs)
        return _make_response(200, {"status": "ok"})

    mock.request = AsyncMock(side_effect=_dispatch_request)
    return mock


@pytest.mark.anyio
async def test_v1_chat_proxies_to_human_chat():
    """POST /v1/chat should proxy to /v1/human/chat internally."""
    chat_response = _make_response(200, {"success": True, "data": {"reply": "pong"}})
    mock = _make_mock_client(chat_response)

    with patch("httpx.AsyncClient", return_value=mock):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post(
                "/v1/chat",
                json={"alpha_id": "Alpha-001", "message": "ping"},
                headers={"X-Tenant-ID": "Alpha-001"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # The real Alpha-ID may return a longer reply; just verify it succeeded
    assert "data" in data

    # Verify internal call was made to /v1/human/chat
    mock.post.assert_called_once()
    call_url = mock.post.call_args[0][0]
    assert "/v1/human/chat" in call_url


@pytest.mark.anyio
async def test_v1_chat_forwards_tenant_header():
    """POST /v1/chat should forward X-Tenant-ID to internal call."""
    chat_response = _make_response(200, {"success": True, "data": {"reply": "ok"}})
    mock = _make_mock_client(chat_response)

    with patch("httpx.AsyncClient", return_value=mock):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            await ac.post(
                "/v1/chat",
                json={"alpha_id": "Alpha-001", "message": "test"},
                headers={"X-Tenant-ID": "Alpha-001"},
            )

    # Check that the forwarded headers include X-Tenant-ID
    call_kwargs = mock.post.call_args[1]
    forwarded_headers = call_kwargs.get("headers", {})
    assert forwarded_headers.get("X-Tenant-ID") == "Alpha-001"


@pytest.mark.anyio
async def test_v1_chat_forwards_alpha_id_as_tenant():
    """POST /v1/chat should use alpha_id from body as X-Tenant-ID if no header."""
    chat_response = _make_response(200, {"success": True, "data": {"reply": "ok"}})
    mock = _make_mock_client(chat_response)

    with patch("httpx.AsyncClient", return_value=mock):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            await ac.post(
                "/v1/chat",
                json={"alpha_id": "Alpha-001", "message": "test"},
                # No X-Tenant-ID header
            )

    call_kwargs = mock.post.call_args[1]
    forwarded_headers = call_kwargs.get("headers", {})
    # alpha_id from body should be forwarded as X-Tenant-ID
    assert forwarded_headers.get("X-Tenant-ID") == "Alpha-001"


@pytest.mark.anyio
async def test_v1_chat_propagates_internal_error():
    """POST /v1/chat should return 502 if internal proxy fails."""
    mock = MagicMock(name="MockAsyncClient")
    mock.post = AsyncMock(side_effect=ConnectionError("connection refused"))
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post(
                "/v1/chat",
                json={"alpha_id": "Alpha-001", "message": "test"},
            )

    assert response.status_code == 502
    data = response.json()
    assert data["success"] is False
