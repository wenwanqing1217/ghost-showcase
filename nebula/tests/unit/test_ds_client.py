"""DS 客户端单元测试"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
import httpx

from mindflow_map.api.ds_client import DSClient, DSClientError, get_ds_client, close_ds_client


@pytest.fixture
def ds_client():
    """创建测试用 DS 客户端"""
    client = DSClient(
        base_url="http://ds-test:3004",
        api_key="test-key-123",
        timeout=5.0,
    )
    yield client
    # 异步 fixtures 需要手动关闭，但 sync yield 方式下我们通过 mock _client 避免实际连接


def _mock_ds_client(client: DSClient, mock_response) -> MagicMock:
    """将 client._client 替换为 mock，返回 mock 以便断言"""
    mock = MagicMock()
    mock.is_closed = False
    mock.request = AsyncMock(return_value=mock_response)
    client._client = mock
    return mock


class TestDSClientInit:
    """测试 DS 客户端初始化"""

    def test_init_with_defaults(self):
        client = DSClient(base_url="http://example.com", api_key="key")
        assert client.base_url == "http://example.com"
        assert client.api_key == "key"
        assert client.timeout == 10.0

    def test_init_strips_trailing_slash(self):
        client = DSClient(base_url="http://example.com/", api_key="k")
        assert client.base_url == "http://example.com"

    def test_init_default_timeout(self):
        client = DSClient(base_url="http://x.com", api_key="k")
        assert client.timeout == 10.0


class TestDSClientRequests:
    """测试 DS 客户端 HTTP 请求"""

    @pytest.mark.asyncio
    async def test_get_metrics_success(self):
        client = DSClient(base_url="http://ds:3004", api_key="test-key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"total": 100, "active": 50}
        mock_response.raise_for_status = MagicMock()

        mock = _mock_ds_client(client, mock_response)
        result = await client.get_metrics()

        assert result == {"total": 100, "active": 50}
        mock.request.assert_called_once_with(
            "GET", "/api/dashboard/metrics", params=None, json=None
        )

    @pytest.mark.asyncio
    async def test_get_products_with_limit(self):
        client = DSClient(base_url="http://ds:3004", api_key="key")
        mock_response = MagicMock()
        mock_response.json.return_value = {"products": []}
        mock_response.raise_for_status = MagicMock()

        mock = _mock_ds_client(client, mock_response)
        result = await client.get_products(limit=25)

        assert result == {"products": []}
        mock.request.assert_called_once_with(
            "GET", "/api/shopify/products", params={"limit": 25}, json=None
        )

    @pytest.mark.asyncio
    async def test_service_key_header(self):
        """验证 API Key 通过 X-Service-Key 头发送"""
        client = DSClient(base_url="http://ds:3004", api_key="my-secret-key")

        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.request = AsyncMock(return_value=mock_response)
            mock_instance.is_closed = False
            mock_cls.return_value = mock_instance
            # 触发 client property
            _ = client.client

        mock_cls.assert_called_once()
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["headers"]["X-Service-Key"] == "my-secret-key"

    @pytest.mark.asyncio
    async def test_http_error_raises_ds_client_error(self):
        client = DSClient(base_url="http://ds:3004", api_key="key")
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Service Unavailable", request=MagicMock(), response=mock_response
        )

        _mock_ds_client(client, mock_response)
        with pytest.raises(DSClientError) as exc_info:
            await client.get_metrics()

        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_connection_error(self):
        client = DSClient(base_url="http://ds:3004", api_key="key")

        mock = MagicMock()
        mock.is_closed = False
        mock.request = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        client._client = mock

        with pytest.raises(DSClientError) as exc_info:
            await client.get_metrics()

        assert "unreachable" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_event(self):
        client = DSClient(base_url="http://ds:3004", api_key="key")
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status = MagicMock()

        mock = _mock_ds_client(client, mock_response)
        result = await client.send_event("approval.completed", {"id": "123"})

        assert result == {"success": True}
        mock.request.assert_called_once_with(
            "POST",
            "/api/webhooks/mindflow-map",
            params=None,
            json={"event": "approval.completed", "payload": {"id": "123"}},
        )


class TestDSClientError:
    """测试 DSClientError 异常"""

    def test_error_with_status(self):
        err = DSClientError("Not found", status_code=404)
        assert str(err) == "Not found"
        assert err.status_code == 404

    def test_error_without_status(self):
        err = DSClientError("Connection failed")
        assert err.status_code is None


class TestGetDSClient:
    """测试全局单例"""

    def test_returns_same_instance(self):
        # 重置全局状态
        import mindflow_map.api.ds_client as mod
        mod._ds_client = None

        with patch("mindflow_map.api.ds_client.DSClient") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance
            client1 = get_ds_client()
            client2 = get_ds_client()
            # 第二次不应创建新实例
            assert mock_cls.call_count == 1
