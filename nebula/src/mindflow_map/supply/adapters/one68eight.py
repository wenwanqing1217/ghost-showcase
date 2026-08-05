"""1688 Adapter — Mock Implementation
========================================
1688 批发平台货源适配器。

当前为 Mock 实现，用于：
  1. 验证适配器接口设计
  2. 前端联调
  3. 测试铺货流程

接入真实 API 时需要：
  1. 申请 1688 开放平台 API Key
  2. 实现 OAuth 2.0 授权流程
  3. 对接商品搜索、详情、库存查询接口
  4. 处理图片上传和类目映射

API 文档：https://open.1688.com/
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


# 1688 模拟类目
MOCK_CATEGORIES = [
    "电子数码 > 手机配件 > 手机壳",
    "电子数码 > 手机配件 > 数据线",
    "服装 > 女装 > 连衣裙",
    "服装 > 男装 > T恤",
    "家居 > 厨具 > 保温杯",
    "家居 > 收纳 > 收纳箱",
    "美妆 > 护肤 > 面膜",
    "玩具 > 益智玩具 > 积木",
]

# 1688 模拟商品
MOCK_PRODUCTS = [
    {
        "source_id": "1688-001",
        "sku": "1688-SJ-001",
        "title": "2024新款iPhone 15 Pro Max 透明磁吸手机壳",
        "description": "采用进口TPU材质，防摔防刮，支持MagSafe磁吸充电。",
        "category": "电子数码 > 手机配件 > 手机壳",
        "price": 8.50,
        "compare_price": 25.00,
        "cost_price": 5.80,
        "inventory": 5000,
        "images": ["https://mock.1688.com/img/phone-case-1.jpg"],
        "origin_country": "中国",
        "estimated_delivery_days": 5,
        "supplier_name": "深圳XX科技有限公司",
        "supplier_rating": 4.8,
    },
    {
        "source_id": "1688-002",
        "sku": "1688-SJ-002",
        "title": "PD 100W快充数据线 Type-C to USB-C 2m",
        "description": "100W大功率快充，2米加长线身，编织网材质耐用。",
        "category": "电子数码 > 手机配件 > 数据线",
        "price": 3.20,
        "compare_price": 12.00,
        "cost_price": 1.80,
        "inventory": 10000,
        "images": ["https://mock.1688.com/img/cable-1.jpg"],
        "origin_country": "中国",
        "estimated_delivery_days": 5,
        "supplier_name": "东莞XX电子厂",
        "supplier_rating": 4.6,
    },
    {
        "source_id": "1688-003",
        "sku": "1688-NZ-001",
        "title": "2024夏季新款法式碎花连衣裙女",
        "description": "韩版宽松版型，碎花印花，适合日常穿搭。",
        "category": "服装 > 女装 > 连衣裙",
        "price": 35.00,
        "compare_price": 89.00,
        "cost_price": 22.00,
        "inventory": 800,
        "images": ["https://mock.1688.com/img/dress-1.jpg"],
        "origin_country": "中国",
        "estimated_delivery_days": 7,
        "supplier_name": "杭州XX服饰有限公司",
        "supplier_rating": 4.7,
    },
    {
        "source_id": "1688-004",
        "sku": "1688-JJ-001",
        "title": "316不锈钢保温杯 500ml 便携保温杯",
        "description": "316不锈钢内胆，12小时保温，食品级材质。",
        "category": "家居 > 厨具 > 保温杯",
        "price": 12.00,
        "compare_price": 35.00,
        "cost_price": 7.50,
        "inventory": 3000,
        "images": ["https://mock.1688.com/img/thermos-1.jpg"],
        "origin_country": "中国",
        "estimated_delivery_days": 5,
        "supplier_name": "永康XX杯业",
        "supplier_rating": 4.9,
    },
    {
        "source_id": "1688-005",
        "sku": "1688-MZ-001",
        "title": "玻尿酸补水面膜 30片装",
        "description": "三重玻尿酸配方，深层补水保湿，温和不刺激。",
        "category": "美妆 > 护肤 > 面膜",
        "price": 18.00,
        "compare_price": 58.00,
        "cost_price": 9.00,
        "inventory": 2000,
        "images": ["https://mock.1688.com/img/mask-1.jpg"],
        "origin_country": "中国",
        "estimated_delivery_days": 7,
        "supplier_name": "广州XX化妆品有限公司",
        "supplier_rating": 4.5,
    },
]


@supply_adapter(name="1688", display_name="1688 批发平台")
class Adapter1688(SupplyAdapter):
    """1688 批发平台货源适配器（Mock 实现）。

    产品标准化流程：
      1. 调用 1688 API 搜索/拉取商品
      2. 将 1688 字段映射到 StandardizedProduct 统一schema
      3. 返回标准化结果供下游（铺货引擎、集市、独立站）消费
    """

    name = "1688"
    display_name = "1688 批发平台"
    version = "1.0.0"
    supported_operations = ["fetch_products", "fetch_product_detail", "check_inventory"]
    auth_type = "api_key"
    rate_limit_rpm = 120
    rate_limit_rps = 5

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._api_key = self.config.get("api_key", "")
        self._api_secret = self.config.get("api_secret", "")
        self._authenticated = bool(self._api_key)

    async def authenticate(self) -> bool:
        """Mock authentication check."""
        if not self._api_key:
            logger.warning("1688 adapter: missing API key")
            return False
        # Real implementation: call 1688 auth endpoint
        self._authenticated = True
        logger.info("1688 adapter: authenticated (mock)")
        return True

    async def fetch_products(
        self,
        page: int = 1,
        page_size: int = 50,
        category: str = "",
        keyword: str = "",
    ) -> SupplyFetchResult:
        """Fetch products from 1688 (mock implementation)."""
        start = time.time()
        self._record_request()

        if not self._authenticated:
            result = SupplyFetchResult(success=False, error="Not authenticated")
            self._log_fetch("fetch_products", result)
            return result

        # Filter mock data
        filtered = MOCK_PRODUCTS
        if category:
            filtered = [p for p in filtered if category in p["category"]]
        if keyword:
            filtered = [p for p in filtered if keyword.lower() in p["title"].lower()]

        # Pagination
        total = len(filtered)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_items = filtered[start_idx:end_idx]

        # Normalize to StandardizedProduct
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
        """Fetch single product detail by source ID."""
        self._record_request()
        for p in MOCK_PRODUCTS:
            if p["source_id"] == source_id:
                return self._normalize(p)
        return None

    async def check_inventory(self, source_ids: List[str]) -> Dict[str, int]:
        """Check inventory for given products."""
        self._record_request()
        inventory = {}
        for p in MOCK_PRODUCTS:
            if p["source_id"] in source_ids:
                inventory[p["source_id"]] = p["inventory"]
        return inventory

    def _normalize(self, raw: Dict[str, Any]) -> StandardizedProduct:
        """Convert 1688-specific data to StandardizedProduct."""
        return StandardizedProduct(
            source_id=raw["source_id"],
            source_name=self.name,
            sku=raw.get("sku", ""),
            title=raw["title"],
            description=raw.get("description", ""),
            category=raw.get("category", ""),
            price=raw.get("price", 0.0),
            currency="CNY",
            compare_price=raw.get("compare_price", 0.0),
            cost_price=raw.get("cost_price", 0.0),
            inventory=raw.get("inventory", 0),
            images=raw.get("images", []),
            origin_country=raw.get("origin_country", "CN"),
            estimated_delivery_days=raw.get("estimated_delivery_days", 7),
            supplier_name=raw.get("supplier_name", ""),
            supplier_rating=raw.get("supplier_rating", 0.0),
            source_url=raw.get("source_url", f"https://detail.1688.com/offer/{raw['source_id']}"),
            raw_data=raw,
        )


# Fix: import time at top level
