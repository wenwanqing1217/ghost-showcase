"""Supply Source API Routes — /api/v1/supply/*
================================================
REST API for supply source management and product fetching.

All requests go through Nebula's SupplyRegistry which dispatches
to the appropriate adapter (1688, CJ Dropshipping, etc.).

Routes:
  GET  /api/v1/supply/adapters           — List all registered adapters
  GET  /api/v1/supply/health             — Health check all adapters
  POST /api/v1/supply/products/fetch     — Fetch products from a supply source
  GET  /api/v1/supply/products/{id}      — Get single product detail
  POST /api/v1/supply/inventory/check    — Check inventory across sources
  POST /api/v1/supply/sync               — Sync products to sales channel
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from mindflow_map.supply.base import (
    get_supply_registry,
    StandardizedProduct,
    SupplyFetchResult,
)
from mindflow_map.supply.schemas import (
    ProductFetchRequest,
    ProductSyncRequest,
    InventoryCheckRequest,
    ProductResponse,
    ProductSyncResult,
    InventoryCheckResponse,
    SupplyHealthResponse,
    AdapterListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/supply", tags=["supply"])


# ── Helper: convert StandardizedProduct to Pydantic response ──

def _product_to_response(p: StandardizedProduct) -> ProductResponse:
    return ProductResponse(
        source_id=p.source_id,
        source_name=p.source_name,
        sku=p.sku,
        title=p.title,
        description=p.description,
        category=p.category,
        price=p.price,
        currency=p.currency,
        compare_price=p.compare_price,
        cost_price=p.cost_price,
        inventory=p.inventory,
        images=p.images,
        shipping_weight=p.shipping_weight,
        origin_country=p.origin_country,
        estimated_delivery_days=p.estimated_delivery_days,
        source_url=p.source_url,
        supplier_name=p.supplier_name,
        supplier_rating=p.supplier_rating,
        fetched_at=p.fetched_at,
    )


# ── Adapter Management ──


@router.get("/adapters", response_model=AdapterListResponse)
async def list_adapters():
    """List all registered supply source adapters."""
    registry = get_supply_registry()
    adapters = registry.list_adapters()
    return AdapterListResponse(adapters=adapters, total=len(adapters))


@router.get("/health", response_model=List[SupplyHealthResponse])
async def health_check_all():
    """Health check all registered supply adapters."""
    registry = get_supply_registry()
    results = []

    for adapter_name in registry._adapters:
        instance = registry.create_instance(adapter_name)
        if instance is None:
            results.append(SupplyHealthResponse(
                adapter=adapter_name,
                healthy=False,
                error="Failed to create instance",
                checked_at="",
            ))
            continue

        try:
            health = await instance.health_check()
            results.append(SupplyHealthResponse(
                adapter=adapter_name,
                healthy=health.get("healthy", False),
                error=health.get("error"),
                checked_at=health.get("checked_at", ""),
            ))
        except Exception as e:
            results.append(SupplyHealthResponse(
                adapter=adapter_name,
                healthy=False,
                error=str(e),
                checked_at="",
            ))

    return results


# ── Product Fetching ──


@router.post("/products/fetch", response_model=List[ProductResponse])
async def fetch_products(request: ProductFetchRequest):
    """Fetch products from a supply source.

    Request body:
        adapter: "1688" | "cj_dropshipping" | ...
        page: 1
        page_size: 50
        category: ""
        keyword: ""

    Returns:
        List of standardized products
    """
    registry = get_supply_registry()
    adapter_cls = registry.get(request.adapter)

    if adapter_cls is None:
        raise HTTPException(
            status_code=404,
            detail=f"Supply adapter '{request.adapter}' not found. Available: {list(registry._adapters.keys())}",
        )

    instance = registry.create_instance(request.adapter)
    if instance is None:
        raise HTTPException(status_code=500, detail=f"Failed to create adapter instance for '{request.adapter}'")

    try:
        result: SupplyFetchResult = await instance.fetch_products(
            page=request.page,
            page_size=request.page_size,
            category=request.category,
            keyword=request.keyword,
        )

        if not result.success:
            raise HTTPException(status_code=502, detail=result.error or "Fetch failed")

        return [_product_to_response(p) for p in result.products]

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Fetch products error [%s]: %s", request.adapter, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{source_id}", response_model=ProductResponse)
async def get_product_detail(source_id: str, adapter: str = Query(..., description="Adapter name")):
    """Get single product detail by source ID.

    Query: ?adapter=1688
    Path: /products/1688-001
    """
    registry = get_supply_registry()
    adapter_cls = registry.get(adapter)

    if adapter_cls is None:
        raise HTTPException(status_code=404, detail=f"Adapter '{adapter}' not found")

    instance = registry.create_instance(adapter)
    if instance is None:
        raise HTTPException(status_code=500, detail=f"Failed to create adapter instance")

    try:
        product = await instance.fetch_product_detail(source_id)
        if product is None:
            raise HTTPException(status_code=404, detail=f"Product '{source_id}' not found")
        return _product_to_response(product)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Product detail error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Inventory Check ──


@router.post("/inventory/check", response_model=InventoryCheckResponse)
async def check_inventory(request: InventoryCheckRequest):
    """Check inventory for multiple products across a supply source."""
    registry = get_supply_registry()
    adapter_cls = registry.get(request.adapter)

    if adapter_cls is None:
        raise HTTPException(status_code=404, detail=f"Adapter '{request.adapter}' not found")

    instance = registry.create_instance(request.adapter)
    if instance is None:
        raise HTTPException(status_code=500, detail="Failed to create adapter instance")

    try:
        inventory = await instance.check_inventory(request.source_ids)

        # Identify stale (not found) items
        found_ids = set(inventory.keys())
        stale = [sid for sid in request.source_ids if sid not in found_ids]

        return InventoryCheckResponse(
            adapter=request.adapter,
            inventory=inventory,
            stale=stale,
            checked_at=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        logger.error("Inventory check error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Product Sync to Sales Channel ──


@router.post("/sync", response_model=List[ProductSyncResult])
async def sync_products(request: ProductSyncRequest):
    """Sync products from supply source to sales channel.

    Request body:
        products: ["1688-001", "1688-002"]
        target: "marketplace" | "independent" | "both"
        shop_id: "shop-abc" (optional, for independent stores)
        pricing_strategy: "auto" | "manual" | "markup"
        markup_percent: 30.0

    Returns:
        List of sync results per product
    """
    results: List[ProductSyncResult] = []

    for source_id in request.products:
        try:
            # TODO: Lookup product from supply source
            # TODO: Apply pricing strategy
            # TODO: Create/update product in target channel

            results.append(ProductSyncResult(
                source_id=source_id,
                target=request.target,
                success=True,
                channel_product_id=f"channel-{source_id}",
                price=0.0,  # TODO: calculate based on pricing strategy
            ))
        except Exception as e:
            results.append(ProductSyncResult(
                source_id=source_id,
                target=request.target,
                success=False,
                error=str(e),
            ))

    return results
