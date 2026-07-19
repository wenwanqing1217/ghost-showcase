"""Shopify 电商运营自动化"""

from typing import Dict, Any, Optional
import httpx

from mindflow_map.config import settings


class ShopifyClient:
    """Shopify Admin API 客户端"""
    
    def __init__(self):
        self.shop_domain = settings.shopify_shop_domain
        self.access_token = settings.shopify_access_token
        self.base_url = f"https://{self.shop_domain}/admin/api/2024-01" if self.shop_domain else ""
    
    async def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.base_url or not self.access_token:
            return {"ok": False, "error": "Shopify 未配置"}
        url = f"{self.base_url}{path}"
        headers = {"X-Shopify-Access-Token": self.access_token, "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def list_products(self, limit: int = 10) -> Dict[str, Any]:
        return await self._request("GET", f"/products.json?limit={limit}")
    
    async def create_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "/products.json", {"product": product})
