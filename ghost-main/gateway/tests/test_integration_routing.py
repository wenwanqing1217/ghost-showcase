"""
Gateway integration tests — verify full routing chain to all backend services.

Validates:
  - All route prefixes are mounted correctly
  - Gateway proxies to correct backend URLs
  - Response format is consistent
  - Error handling for unreachable backends
"""

import pytest
from tests.conftest import _make_response


@pytest.mark.anyio
async def test_all_route_prefixes_mounted(gateway_client):
    """Gateway has all expected route prefixes registered."""
    # Access the FastAPI app via the ASGITransport
    from app import app

    routes = {route.path for route in app.routes}
    # Check that key routes exist
    assert "/health" in routes
    # Human routes
    assert any("/v1/human" in r for r in routes)
    # Agent routes
    assert any("/v1/agent" in r for r in routes)
    # Internal routes
    assert any("/v1/internal" in r for r in routes)
    # Net routes
    assert any("/v1/net" in r for r in routes)


@pytest.mark.anyio
async def test_human_profile_proxies_to_alphaid(gateway_client, mock_client):
    """GET /v1/human/profile proxies to Alpha-ID /api/v1/identity/me."""
    captured_urls = []

    def mock_get(url, **kwargs):
        captured_urls.append(url)
        return _make_response(200, {"did": "aid:test", "name": "Test User"})

    mock_client.get.side_effect = mock_get
    response = await gateway_client.get("/v1/human/profile")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "/api/v1/identity/me" in captured_urls[0]


@pytest.mark.anyio
async def test_human_chat_proxies_to_alphaid(gateway_client, mock_client):
    """POST /v1/human/chat proxies to Alpha-ID /api/v1/agent/chat."""
    captured = []

    def mock_post(url, **kwargs):
        captured.append((url, kwargs.get("json")))
        return _make_response(200, {"reply": "Hello!"})

    mock_client.post.side_effect = mock_post
    response = await gateway_client.post("/v1/human/chat", json={"message": "hi"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "/api/v1/agent/chat" in captured[0][0]


@pytest.mark.anyio
async def test_agent_topology_proxies_to_alphaid(gateway_client, mock_client):
    """GET /v1/agent/interact/topology proxies to Alpha-ID stats endpoint."""
    captured_urls = []

    def mock_get(url, **kwargs):
        captured_urls.append(url)
        return _make_response(200, {"nodes": 10, "edges": 20})

    mock_client.get.side_effect = mock_get
    response = await gateway_client.get("/v1/agent/interact/topology")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "/api/v1/identity/stats/overview" in captured_urls[0]


@pytest.mark.anyio
async def test_internal_doubao_proxies_to_alphaid(gateway_client, mock_client):
    """POST /v1/internal/doubao/capture proxies to Alpha-ID dual-chain save."""
    captured = []

    def mock_post(url, **kwargs):
        captured.append((url, kwargs.get("json")))
        return _make_response(200, {"saved": True})

    mock_client.post.side_effect = mock_post
    response = await gateway_client.post(
        "/v1/internal/doubao/capture",
        json={
            "session_id": "test-session-001",
            "messages": [
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "你好！有什么可以帮你的？"},
            ],
        },
        headers={"X-Forwarded-For": "127.0.0.1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "/api/v1/dual-chain/save" in captured[0][0]


@pytest.mark.anyio
async def test_net_routes_proxied_to_netagent(gateway_client, mock_client):
    """GET /v1/net/* proxies to Net-Agent server."""
    captured_urls = []

    def mock_get(url, **kwargs):
        captured_urls.append(url)
        return _make_response(200, {"status": "ok"})

    mock_client.get.side_effect = mock_get
    response = await gateway_client.get("/v1/net/status")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "18180" in captured_urls[0]


@pytest.mark.anyio
async def test_gateway_returns_error_on_backend_failure(gateway_client, mock_client):
    """Gateway returns error envelope when backend is unreachable."""

    def mock_get(url, **kwargs):
        raise ConnectionError("Connection refused")

    mock_client.get.side_effect = mock_get
    response = await gateway_client.get("/v1/human/profile")
    # Should not crash, should return error
    assert response.status_code in [200, 502, 503]
    data = response.json()
    assert "success" in data


@pytest.mark.anyio
async def test_correlation_id_propagated(gateway_client, mock_client):
    """X-Request-ID is present in all responses."""
    response = await gateway_client.get("/v1/human/profile")
    assert "x-request-id" in response.headers


@pytest.mark.anyio
async def test_request_id_respected(gateway_client, mock_client):
    """Gateway respects client-provided X-Request-ID."""
    custom_id = "integration-test-456"
    response = await gateway_client.get(
        "/v1/human/profile", headers={"X-Request-ID": custom_id}
    )
    assert response.headers["x-request-id"] == custom_id


# ── Flow Workflow Proxy Tests ──


@pytest.mark.anyio
async def test_flow_routes_mounted(gateway_client):
    """Flow routes are registered under /v1/agent/flow/*."""
    from app import app

    routes = {route.path for route in app.routes}
    # Verify key Flow routes exist
    assert "/v1/agent/flow/health" in routes
    assert "/v1/agent/flow/templates" in routes
    assert "/v1/agent/flow/templates/{template_id}" in routes
    assert "/v1/agent/flow/execute" in routes
    assert "/v1/agent/flow/executions" in routes
    assert "/v1/agent/flow/aid/sessions" in routes
    assert "/v1/agent/flow/map/search" in routes
    assert "/v1/agent/flow/computer-use/status" in routes


@pytest.mark.anyio
async def test_flow_health_proxies_to_flow_service(gateway_client, mock_client):
    """GET /v1/agent/flow/health proxies to Flow /health."""
    captured_urls = []

    def mock_get(url, **kwargs):
        captured_urls.append(url)
        return _make_response(200, {"success": True, "data": {"status": "ok"}})

    mock_client.get.side_effect = mock_get
    response = await gateway_client.get("/v1/agent/flow/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "3036" in captured_urls[0]


@pytest.mark.anyio
async def test_flow_templates_proxied(gateway_client, mock_client):
    """GET /v1/agent/flow/templates proxies to Flow /templates."""
    captured_urls = []

    def mock_get(url, **kwargs):
        captured_urls.append(url)
        return _make_response(200, {"success": True, "data": {"templates": []}})

    mock_client.get.side_effect = mock_get
    response = await gateway_client.get("/v1/agent/flow/templates")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "/templates" in captured_urls[0]
    assert "3036" in captured_urls[0]


@pytest.mark.anyio
async def test_flow_execute_proxies_post(gateway_client, mock_client):
    """POST /v1/agent/flow/execute proxies to Flow /execute with body."""
    captured = []

    def mock_post(url, **kwargs):
        captured.append((url, kwargs.get("json")))
        return _make_response(
            200, {"success": True, "data": {"execution_id": "exec-001"}}
        )

    mock_client.post.side_effect = mock_post
    response = await gateway_client.post(
        "/v1/agent/flow/execute",
        json={"message": "search for AI news"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "/execute" in captured[0][0]
    assert "3036" in captured[0][0]
    assert captured[0][1]["message"] == "search for AI news"


@pytest.mark.anyio
async def test_flow_aid_session_proxied(gateway_client, mock_client):
    """POST /v1/agent/flow/aid/sessions proxies to Flow /sessions."""
    captured = []

    def mock_post(url, **kwargs):
        captured.append((url, kwargs.get("json")))
        return _make_response(
            200, {"success": True, "data": {"session_id": "sess-001"}}
        )

    mock_client.post.side_effect = mock_post
    response = await gateway_client.post(
        "/v1/agent/flow/aid/sessions",
        json={"context": "test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "/sessions" in captured[0][0]


@pytest.mark.anyio
async def test_flow_error_envelope_wrapped(gateway_client, mock_client):
    """Flow {success:false} envelope is converted to Gateway error envelope."""

    def mock_get(url, **kwargs):
        return _make_response(200, {"success": False, "error": "template not found"})

    mock_client.get.side_effect = mock_get
    response = await gateway_client.get("/v1/agent/flow/templates/nonexistent")
    assert response.status_code == 502
    data = response.json()
    assert data["success"] is False
    assert "template not found" in data["error"]
