"""Shopify 电商运营自动化 — 复用单一 httpx 客户端"""

import re
from typing import Any, Dict, Optional

import httpx

from mindflow_map.config import settings

# 严格的 Shopify 域名格式校验
_SHOPIFY_DOMAIN_RE = re.compile(r"^[a-z0-9-]+\.myshopify\.com$")


class ShopifyClient:
    """Shopify Admin API 客户端 — 复用实例级别 httpx.AsyncClient"""

    def __init__(self):
        self.shop_domain = settings.shopify_shop_domain
        self.access_token = settings.shopify_access_token

        if self.shop_domain and not _SHOPIFY_DOMAIN_RE.match(self.shop_domain):
            raise ValueError(
                f"无效的 Shopify 域名: {self.shop_domain}。"
                "必须以 .myshopify.com 结尾，且仅包含小写字母、数字和连字符。"
            )

        self.base_url = f"https://{self.shop_domain}/admin/api/2024-01" if self.shop_domain else ""
        # 复用连接池，避免每请求创建新 client
        self._client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.base_url or not self.access_token:
            return {"ok": False, "error": "Shopify 未配置"}
        url = f"{self.base_url}{path}"
        headers = {"X-Shopify-Access-Token": self.access_token, "Content-Type": "application/json"}
        response = await self._client.request(method, url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    async def list_products(self, limit: int = 10) -> Dict[str, Any]:
        return await self._request("GET", f"/products.json?limit={limit}")

    async def create_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "/products.json", {"product": product})
