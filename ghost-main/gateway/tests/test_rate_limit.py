"""
Gateway rate limiting and proxy endpoint tests.
Validates:
  - Rate limit enforcement on SMS and chat endpoints
  - Proxy endpoints forward correctly
  - Request validation (missing fields → 400)
  - Response correlation ID propagation
"""

import pytest

from tests.conftest import _make_response


@pytest.mark.anyio
async def test_chat_rate_limit_blocks_after_10(gateway_client, mock_client):
    """Chat endpoint blocks after 10 requests per IP within 60s window."""
    mock_client.post.side_effect = lambda url, **kwargs: _make_response(
        200, {"reply": "hello"}
    )

    # First 10 requests should pass (not 429)
    for i in range(10):
        response = await gateway_client.post(
            "/v1/human/chat", json={"message": f"msg {i}"}
        )
        assert response.status_code != 429, (
            f"Request {i + 1} should not be rate limited"
        )

    # 11th request should be rate limited
    response = await gateway_client.post("/v1/human/chat", json={"message": "overflow"})
    assert response.status_code == 429
    data = response.json()
    assert data["success"] is False
    assert "Too many requests" in data["error"]


@pytest.mark.anyio
async def test_chat_missing_message_returns_400(gateway_client):
    """Chat endpoint rejects empty message with 400."""
    response = await gateway_client.post("/v1/human/chat", json={})
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "message required" in data["error"]


@pytest.mark.anyio
async def test_intent_parse_missing_text_returns_400(gateway_client):
    """Intent parse rejects empty text with 400."""
    response = await gateway_client.post("/v1/human/intent/parse", json={})
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "text required" in data["error"]


@pytest.mark.anyio
async def test_identity_proxy(gateway_client, mock_client):
    """Identity endpoint proxies to Alpha-ID and returns data."""
    mock_client.get.side_effect = lambda url, **kwargs: _make_response(
        200, {"alpha_id": "Alpha-1", "did": "did:aid:test"}
    )
    response = await gateway_client.get("/v1/human/identity")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["alpha_id"] == "Alpha-1"


@pytest.mark.anyio
async def test_dashboard_returns_aggregated_data(gateway_client, mock_client):
    """Dashboard aggregates data from all backends."""

    def mock_get(url, **kwargs):
        if "/identity" in url:
            return _make_response(200, {"alpha_id": "Alpha-1"})
        elif "/brain/status" in url:
            return _make_response(200, {"state": "awake"})
        elif "/network/topology" in url:
            return _make_response(200, {"my_did": "did:aid:test"})
        elif "/api/profile" in url:
            return _make_response(200, {"profile": {"persona": {}}})
        return _make_response(200, {})

    mock_client.get.side_effect = mock_get
    response = await gateway_client.get("/v1/human/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "identity" in data["data"]
    assert "profile" in data["data"]


@pytest.mark.anyio
async def test_register_sms_rate_limit(gateway_client, mock_client):
    """SMS endpoint rate limits to 5 requests per IP."""
    mock_client.post.side_effect = lambda url, **kwargs: _make_response(
        200, {"success": True, "data": {"code": "123456"}}
    )
    # First 5 requests pass
    for i in range(5):
        response = await gateway_client.post(
            "/v1/human/register/send-sms", json={"phone": f"1380000000{i}"}
        )
        assert response.status_code != 429, f"SMS {i + 1} should not be rate limited"

    # 6th request blocked
    response = await gateway_client.post(
        "/v1/human/register/send-sms", json={"phone": "13800000099"}
    )
    assert response.status_code == 429


@pytest.mark.anyio
async def test_response_includes_request_id(gateway_client, mock_client):
    """All responses include X-Request-ID header."""
    response = await gateway_client.get("/v1/human/identity")
    assert "x-request-id" in response.headers
