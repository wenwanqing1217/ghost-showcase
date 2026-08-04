"""Standardized Supply Data Schemas
=====================================
Pydantic schemas for supply source API requests/responses.

Used by:
  - Supply adapters (for validation)
  - Gateway routes (for request/response serialization)
  - DS backend (for database storage)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


# ── Request Schemas ──


class ProductFetchRequest(BaseModel):
    """Request to fetch products from a supply source."""
    adapter: str = Field(..., description="Adapter name (e.g., '1688', 'cj_dropshipping')")
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(50, ge=1, le=200, description="Items per page")
    category: str = Field("", description="Category filter")
    keyword: str = Field("", description="Search keyword")
    source_ids: List[str] = Field(default_factory=list, description="Specific product IDs to fetch")


class ProductSyncRequest(BaseModel):
    """Request to sync products to a sales channel."""
    products: List[str] = Field(..., description="Source product IDs to sync")
    target: str = Field(..., description="Target channel: 'marketplace' | 'independent' | 'both'")
    shop_id: Optional[str] = Field(None, description="Target shop ID (for independent stores)")
    pricing_strategy: str = Field("auto", description="Pricing: 'auto' | 'manual' | 'markup'")
    markup_percent: float = Field(0.0, ge=0, description="Markup percentage if strategy is 'markup'")


class InventoryCheckRequest(BaseModel):
    """Request to check inventory across sources."""
    adapter: str = Field(..., description="Adapter name")
    source_ids: List[str] = Field(..., min_items=1, description="Product IDs to check")


class FulfillOrderRequest(BaseModel):
    """Request to fulfill an order via supply source."""
    adapter: str = Field(..., description="Adapter name for fulfillment")
    source_order_id: str = Field(..., description="Source order ID")
    items: List[Dict[str, Any]] = Field(..., description="Order items to fulfill")
    tracking_number: Optional[str] = Field(None, description="Tracking number (if known)")
    shipping_method: str = Field("standard", description="Shipping method")


# ── Response Schemas ──


class ProductResponse(BaseModel):
    """Standardized product response."""
    source_id: str
    source_name: str
    sku: str = ""
    title: str
    description: str = ""
    category: str = ""
    price: float = 0.0
    currency: str = "USD"
    compare_price: float = 0.0
    cost_price: float = 0.0
    inventory: int = 0
    images: List[str] = Field(default_factory=list)
    shipping_weight: float = 0.0
    origin_country: str = ""
    estimated_delivery_days: int = 7
    source_url: str = ""
    supplier_name: str = ""
    supplier_rating: float = 0.0
    fetched_at: str


class ProductSyncResult(BaseModel):
    """Result of syncing a product to a sales channel."""
    source_id: str
    target: str
    success: bool
    channel_product_id: Optional[str] = None
    price: float = 0.0
    error: Optional[str] = None


class InventoryCheckResponse(BaseModel):
    """Inventory check result."""
    adapter: str
    inventory: Dict[str, int]  # {source_id: count}
    stale: List[str] = []      # Source IDs not found (may be delisted)
    checked_at: str


class FulfillOrderResponse(BaseModel):
    """Order fulfillment result."""
    success: bool
    source_order_id: str
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    estimated_delivery: Optional[str] = None
    error: Optional[str] = None


class SupplyHealthResponse(BaseModel):
    """Supply source health check response."""
    adapter: str
    healthy: bool
    error: Optional[str] = None
    checked_at: str


class AdapterListResponse(BaseModel):
    """List of available supply adapters."""
    adapters: List[Dict[str, Any]]
    total: int
