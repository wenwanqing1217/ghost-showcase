"""DS (Dashboard Shopify)  HTTP 客户端

提供对 DS 服务的类型化 API 调用，内置重试、超时和错误处理。
通过 settings.ds_api_url + settings.ds_api_key 认证。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from mindflow_map.config import settings

logger = logging.getLogger(__name__)


class DSClientError(Exception):
    """DS 服务调用异常"""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class DSClient:
    """DS Dashboard HTTP 客户端（异步，带连接池）"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 10.0,
    ):
        self.base_url = (base_url or settings.ds_api_url).rstrip("/")
        self.api_key = api_key or settings.ds_api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {"Accept": "application/json"}
            if self.api_key:
                headers["X-Service-Key"] = self.api_key
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """发送 HTTP 请求并处理响应"""
        try:
            response = await self.client.request(
                method,
                path,
                params=params,
                json=json,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "DS API error: %s %s → %d",
                method, path, exc.response.status_code,
            )
            raise DSClientError(
                f"DS API {method} {path} failed: {exc.response.status_code}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            logger.error("DS API request failed: %s %s — %s", method, path, exc)
            raise DSClientError(f"DS API {method} {path} unreachable: {exc}") from exc

    # ── Dashboard ──

    async def get_metrics(self) -> Dict[str, Any]:
        """获取 Dashboard 指标"""
        return await self._request("GET", "/api/dashboard/metrics")

    async def get_alerts(self) -> Dict[str, Any]:
        """获取告警列表"""
        return await self._request("GET", "/api/dashboard/alerts")

    # ── Shopify ──

    async def get_products(self, limit: int = 50) -> Dict[str, Any]:
        """获取 Shopify 产品列表"""
        return await self._request("GET", "/api/shopify/products", params={"limit": limit})

    async def get_orders(self, limit: int = 50) -> Dict[str, Any]:
        """获取 Shopify 订单列表"""
        return await self._request("GET", "/api/shopify/orders", params={"limit": limit})

    # ── Health ──

    async def health_check(self) -> Dict[str, Any]:
        """检查 DS 服务健康状态"""
        return await self._request("GET", "/api/health")

    # ── Webhook 回调 ──

    async def send_event(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """向 DS 发送事件通知"""
        return await self._request(
            "POST",
            "/api/webhooks/mindflow-map",
            json={"event": event_type, "payload": payload},
        )


# 全局单例
_ds_client: Optional[DSClient] = None


def get_ds_client() -> DSClient:
    """获取全局 DS 客户端实例"""
    global _ds_client
    if _ds_client is None:
        _ds_client = DSClient()
    return _ds_client


async def close_ds_client():
    """关闭全局 DS 客户端"""
    global _ds_client
    if _ds_client is not None:
        await _ds_client.close()
        _ds_client = None
