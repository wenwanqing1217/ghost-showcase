"""
Gateway health check tests.
Validates:
  - 200 when all backends healthy
  - 503 when any backend is down
  - Correct backend status reporting
  - Correlation ID propagation
"""

import pytest

import config as _config


@pytest.mark.anyio
async def test_health_all_backends_healthy(gateway_client, mock_client):
    """Health returns 200 when all backends respond 200."""
    response = await gateway_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["gateway"] == "ok"
    assert data["data"]["alphaid"] == "ok"
    assert data["data"]["netagent"] == "ok"


@pytest.mark.anyio
async def test_health_alphaid_down_reports_error(gateway_client, mock_client):
    """Health reports alphaid error when unreachable (overall: degraded)."""

    async def mock_get(url, **kwargs):
        if str(_config.ALPHAID_URL) in url:
            raise ConnectionError("Connection refused")
        from tests.conftest import _make_response

        return _make_response(200, {"status": "ok"})

    mock_client.get.side_effect = mock_get
    response = await gateway_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["alphaid"] == "error"
    assert data["data"]["overall"] == "degraded"


@pytest.mark.anyio
async def test_health_netagent_down_reports_error(gateway_client, mock_client):
    """Health reports netagent error when unreachable."""

    async def mock_get(url, **kwargs):
        if str(_config.NETAGENT_URL) in url:
            raise ConnectionError("Connection refused")
        from tests.conftest import _make_response

        return _make_response(200, {"status": "ok"})

    mock_client.get.side_effect = mock_get
    response = await gateway_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["netagent"] == "error"
    assert data["data"]["overall"] == "degraded"


@pytest.mark.anyio
async def test_health_all_down_reports_errors(gateway_client, mock_client):
    """Health reports all backends error when all unreachable."""

    async def mock_get(url, **kwargs):
        raise ConnectionError("Connection refused")

    mock_client.get.side_effect = mock_get
    response = await gateway_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["alphaid"] == "error"
    assert data["data"]["netagent"] == "error"
    assert data["data"]["overall"] == "degraded"


@pytest.mark.anyio
async def test_health_includes_nebula_and_orchestrator(gateway_client, mock_client):
    """Health check covers nebula and orchestrator backends."""
    response = await gateway_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "nebula" in data["data"]
    assert "orchestrator" in data["data"]


@pytest.mark.anyio
async def test_health_includes_request_id(gateway_client, mock_client):
    """Health response includes X-Request-ID header."""
    response = await gateway_client.get("/health")
    assert "x-request-id" in response.headers


@pytest.mark.anyio
async def test_health_uses_provided_request_id(gateway_client, mock_client):
    """Gateway respects client-provided X-Request-ID."""
    custom_id = "test-req-123"
    response = await gateway_client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.headers["x-request-id"] == custom_id
