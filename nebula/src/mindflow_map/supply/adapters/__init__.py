"""Supply Source Adapters — Nebula
=====================================
Concrete implementations of supply source adapters.

Adapters:
  - mock_1688       : 1688 批发平台（Mock 实现，待接入真实 API）
  - mock_cj          : CJ Dropshipping（Mock 实现，待接入真实 API）
  - shoplazza        : Shoplazza 店铺（已有 DS 集成，此处统一适配器接口）

Each adapter normalizes source data into StandardizedProduct schema.
"""

from mindflow_map.supply.base import (
    SupplyAdapter,
    SupplyRegistry,
    StandardizedProduct,
    StandardizedOrder,
    SupplyFetchResult,
    supply_adapter,
    get_supply_registry,
)

__all__ = [
    "SupplyAdapter",
    "StandardizedProduct",
    "StandardizedOrder",
    "SupplyFetchResult",
    "SupplyRegistry",
    "supply_adapter",
    "get_supply_registry",
]
