"""
Tests for OrchestratorEngine tool retry and status endpoints.
"""

import pytest
from unittest.mock import patch, MagicMock
from main import app, _call_tool_with_retry, TOOL_A, TOOL_B, TOOL_A_TIMEOUT, TOOL_B_TIMEOUT, TOOL_MAX_RETRIES


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_tools_status_when_not_configured():
    """GET /v1/tools/status returns not_configured when tools are unset."""
    with patch("main.TOOL_A", ""), patch("main.TOOL_B", ""):
        from httpx import AsyncClient, ASGITransport
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/v1/tools/status")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["tools"]["tool_a"]["configured"] is False
    assert data["tools"]["tool_b"]["configured"] is False


@pytest.mark.anyio
async def test_health_endpoint():
    """GET /health returns ok with task count."""
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "tasks" in data
    assert "port" in data


class TestCallToolWithRetry:
    """Unit tests for _call_tool_with_retry."""

    def test_success_on_first_attempt(self):
        """Returns data dict when tool responds 200 on first try."""
        import httpx
        client = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"result": "ok"}
        client.post.return_value = resp

        result = _call_tool_with_retry(
            client=client,
            url="http://tool:8081/v1/generate",
            payload={"req": "test"},
            timeout=30.0,
            max_retries=2,
            tool_name="ToolA",
        )
        assert "data" in result
        assert result["data"]["result"] == "ok"
        assert result["attempt"] == 1
        client.post.assert_called_once()

    def test_retry_on_500(self):
        """Retries on 500, succeeds on second attempt."""
        client = MagicMock()
        err_resp = MagicMock()
        err_resp.status_code = 500
        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"result": "ok"}
        client.post.side_effect = [err_resp, ok_resp]

        result = _call_tool_with_retry(
            client=client,
            url="http://tool:8081/v1/generate",
            payload={"req": "test"},
            timeout=30.0,
            max_retries=2,
            tool_name="ToolA",
        )
        assert "data" in result
        assert result["attempt"] == 2
        assert client.post.call_count == 2

    def test_no_retry_on_400(self):
        """Does not retry on 4xx client error."""
        client = MagicMock()
        err_resp = MagicMock()
        err_resp.status_code = 400
        err_resp.text = "bad request"
        client.post.return_value = err_resp

        result = _call_tool_with_retry(
            client=client,
            url="http://tool:8081/v1/generate",
            payload={"req": "test"},
            timeout=30.0,
            max_retries=2,
            tool_name="ToolA",
        )
        assert "error" in result
        assert result["status_code"] == 400
        client.post.assert_called_once()

    def test_timeout_retries(self):
        """Retries on httpx.TimeoutException."""
        import httpx
        client = MagicMock()
        client.post.side_effect = httpx.TimeoutException("timeout")

        result = _call_tool_with_retry(
            client=client,
            url="http://tool:8081/v1/generate",
            payload={"req": "test"},
            timeout=5.0,
            max_retries=2,
            tool_name="ToolA",
        )
        assert "error" in result
        assert "timeout" in result["error"]
        assert client.post.call_count == 2

    def test_exhausts_retries(self):
        """Returns last error after exhausting retries."""
        import httpx
        client = MagicMock()
        client.post.side_effect = httpx.ConnectError("unreachable")

        result = _call_tool_with_retry(
            client=client,
            url="http://tool:8081/v1/generate",
            payload={"req": "test"},
            timeout=5.0,
            max_retries=2,
            tool_name="ToolA",
        )
        assert "error" in result
        assert result["attempts"] == 2
        assert client.post.call_count == 2
