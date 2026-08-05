"""CJ Dropshipping Adapter — Mock Implementation
================================================
CJ Dropshipping (cjdropshipping.com) 跨境一件代发货源适配器。

当前为 Mock 实现，用于验证适配器接口设计。
接入真实 API 时需要：
  1. 申请 CJ Dropshipping API Key
  2. 对接商品搜索、导入、订单同步接口
  3. 处理自动履约和物流跟踪

API 文档：https://cjdropshipping.com/api-docs/
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from mindflow_map.supply.base import (
    StandardizedProduct,
    SupplyAdapter,
    SupplyFetchResult,
    supply_adapter,
)

logger = logging.getLogger(__name__)

# CJ Dropshipping 模拟商品（跨境类目）
MOCK_PRODUCTS = [
    {
        "source_id": "cj-001",
        "sku": "CJ-COS-001",
        "title": "Custom Logo Face Mask 3-Ply Disposable Masks (50pcs)",
        "description": "Custom logo printed disposable face masks. CE/FDA certified. MOQ 500pcs.",
        "category": "Health & Beauty > Face Masks",
        "price": 2.50,
        "compare_price": 8.99,
        "cost_price": 1.20,
        "inventory": 50000,
        "images": ["https://mock.cj.com/img/mask-1.jpg"],
        "origin_country": "CN",
        "estimated_delivery_days": 12,
        "supplier_name": "CJ Verified Supplier #A1234",
        "supplier_rating": 4.8,
    },
    {
        "source_id": "cj-002",
        "sku": "CJ-HOM-001",
        "title": "LED Strip Lights RGB 10M IP65 Waterproof with Remote",
        "description": "10M LED strip, RGB color changing, IP65 waterproof, includes 24-key remote control.",
        "category": "Home & Garden > Lighting",
        "price": 6.80,
        "compare_price": 24.99,
        "cost_price": 3.50,
        "inventory": 8000,
        "images": ["https://mock.cj.com/img/led-1.jpg"],
        "origin_country": "CN",
        "estimated_delivery_days": 15,
        "supplier_name": "CJ Verified Supplier #B5678",
        "supplier_rating": 4.6,
    },
    {
        "source_id": "cj-003",
        "sku": "CJ-SPO-001",
        "title": "Yoga Mat Non-Slip 6mm Thick with Carrying Strap",
        "description": "Premium TPE yoga mat, 6mm thick, non-slip surface, eco-friendly material.",
        "category": "Sports & Outdoors > Yoga",
        "price": 9.90,
        "compare_price": 29.99,
        "cost_price": 5.20,
        "inventory": 3000,
        "images": ["https://mock.cj.com/img/yoga-1.jpg"],
        "origin_country": "CN",
        "estimated_delivery_days": 18,
        "supplier_name": "CJ Verified Supplier #C9012",
        "supplier_rating": 4.7,
    },
    {
        "source_id": "cj-004",
        "sku": "CJ-ELE-001",
        "title": "Wireless Earbuds Bluetooth 5.3 with Charging Case",
        "description": "TWS wireless earbuds, Bluetooth 5.3, 30H playtime, IPX5 waterproof, touch control.",
        "category": "Electronics > Audio",
        "price": 4.50,
        "compare_price": 19.99,
        "cost_price": 2.10,
        "inventory": 15000,
        "images": ["https://mock.cj.com/img/earbuds-1.jpg"],
        "origin_country": "CN",
        "estimated_delivery_days": 15,
        "supplier_name": "CJ Verified Supplier #D3456",
        "supplier_rating": 4.9,
    },
    {
        "source_id": "cj-005",
        "sku": "CJ-PET-001",
        "title": "Cat Litter Box Self-Cleaning Automatic with Enclosed Design",
        "description": "Automatic self-cleaning cat litter box, enclosed design, odor control, easy assembly.",
        "category": "Pet Supplies > Cat Litter Boxes",
        "price": 35.00,
        "compare_price": 99.99,
        "cost_price": 22.00,
        "inventory": 500,
        "images": ["https://mock.cj.com/img/litter-1.jpg"],
        "origin_country": "CN",
        "estimated_delivery_days": 20,
        "supplier_name": "CJ Verified Supplier #E7890",
        "supplier_rating": 4.5,
    },
]


@supply_adapter(name="cj_dropshipping", display_name="CJ Dropshipping")
class AdapterCJDropshipping(SupplyAdapter):
    """CJ Dropshipping 跨境一件代发货源适配器（Mock 实现）。"""

    name = "cj_dropshipping"
    display_name = "CJ Dropshipping"
    version = "1.0.0"
    supported_operations = ["fetch_products", "fetch_product_detail", "check_inventory"]
    auth_type = "api_key"
    rate_limit_rpm = 60
    rate_limit_rps = 5

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._api_key = self.config.get("api_key", "")
        self._authenticated = bool(self._api_key)

    async def authenticate(self) -> bool:
        if not self._api_key:
            logger.warning("CJ adapter: missing API key")
            return False
        self._authenticated = True
        logger.info("CJ adapter: authenticated (mock)")
        return True

    async def fetch_products(
        self,
        page: int = 1,
        page_size: int = 50,
        category: str = "",
        keyword: str = "",
    ) -> SupplyFetchResult:
        start = time.time()
        self._record_request()

        if not self._authenticated:
            return SupplyFetchResult(success=False, error="Not authenticated")

        filtered = MOCK_PRODUCTS
        if category:
            filtered = [p for p in filtered if category.lower() in p["category"].lower()]
        if keyword:
            filtered = [p for p in filtered if keyword.lower() in p["title"].lower()]

        total = len(filtered)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_items = filtered[start_idx:end_idx]

        products = [self._normalize(p) for p in page_items]
        duration = (time.time() - start) * 1000

        result = SupplyFetchResult(
            success=True,
            products=products,
            total_count=total,
            page=page,
            has_more=end_idx < total,
            duration_ms=duration,
        )
        self._log_fetch("fetch_products", result)
        return result

    async def fetch_product_detail(self, source_id: str) -> Optional[StandardizedProduct]:
        self._record_request()
        for p in MOCK_PRODUCTS:
            if p["source_id"] == source_id:
                return self._normalize(p)
        return None

    async def check_inventory(self, source_ids: List[str]) -> Dict[str, int]:
        self._record_request()
        return {p["source_id"]: p["inventory"] for p in MOCK_PRODUCTS if p["source_id"] in source_ids}

    def _normalize(self, raw: Dict[str, Any]) -> StandardizedProduct:
        return StandardizedProduct(
            source_id=raw["source_id"],
            source_name=self.name,
            sku=raw.get("sku", ""),
            title=raw["title"],
            description=raw.get("description", ""),
            category=raw.get("category", ""),
            price=raw["price"],
            currency="USD",
            compare_price=raw.get("compare_price", 0.0),
            cost_price=raw.get("cost_price", 0.0),
            inventory=raw.get("inventory", 0),
            images=raw.get("images", []),
            origin_country=raw.get("origin_country", "CN"),
            estimated_delivery_days=raw.get("estimated_delivery_days", 15),
            supplier_name=raw.get("supplier_name", ""),
            supplier_rating=raw.get("supplier_rating", 0.0),
            source_url=raw.get("source_url", f"https://cjdropshipping.com/product/{raw['source_id']}"),
            raw_data=raw,
        )
