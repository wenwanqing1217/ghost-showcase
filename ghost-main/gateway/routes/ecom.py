"""E-Commerce Routes — /v1/ecom/*
=================================
Proxies e-commerce API requests to the DS (Next.js) backend.

All requests here require tenant authentication (enforced by TenantMiddleware).
The tenant_id is forwarded as X-Tenant-ID header for backend query scoping.

Architecture:
  DS Frontend → Gateway (:18080/v1/ecom/*) → DS API (:3000/api/*)
                    ↑
              Auth, Rate Limit, Audit, Tenant Injection

Routes:
  GET    /v1/ecom/products       → DS /api/products
  GET    /v1/ecom/products/{id}  → DS /api/products/{id}
  POST   /v1/ecom/sync           → DS /api/sync
  GET    /v1/ecom/orders         → DS /api/orders
  POST   /v1/ecom/orders/{id}/fulfill → DS /api/orders/{id}/fulfill
  GET    /v1/ecom/stats          → DS /api/stats
  GET    /v1/ecom/health         → DS /api/health
"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from services.proxy import proxy_get, proxy_post, ok, fail
from middleware.rate_limit import rate_limit_check, client_ip
import config

logger = logging.getLogger("ghost-gateway")

# DS backend URL — uses config.DS_URL which defaults to ghost-ds:3000 (Docker service name)
DS_URL = config.DS_URL

router = APIRouter(prefix="/v1/ecom", tags=["ecom"])


# ── Helper: proxy to DS backend with tenant header ──


async def _proxy_ds(
    method: str,
    path: str,
    request: Request,
    body: dict = None,
    timeout: float = None,
) -> dict:
    """Proxy request to DS backend, forwarding tenant_id and auth headers."""
    tenant_id = getattr(request.state, "tenant_id", None)

    # Build headers to forward
    headers = {
        "X-Tenant-ID": tenant_id or "anonymous",
        "X-Request-ID": getattr(request.state, "request_id", ""),
    }

    # Forward Authorization if present (for internal DS API auth)
    auth_header = request.headers.get("authorization")
    if auth_header:
        headers["Authorization"] = auth_header

    url = f"{DS_URL}{path}"
    from services.proxy import _proxy_request

    return await _proxy_request(method, url, "", body=body, headers=headers, timeout=timeout)


# ── Products ──


@router.get("/products")
async def list_products(request: Request):
    """List products with pagination, search, and status filter.

    Query params: ?page=1&limit=20&status=active&search=xxx
    """
    ip = client_ip(request)
    if not rate_limit_check(f"ecom:products:{ip}", max_requests=30, window=60):
        return fail("Too many requests, please slow down", 429, request)

    # Forward query params to DS
    query_string = str(request.url.query)
    path = f"/api/products{('?' + query_string) if query_string else ''}"

    data = await _proxy_ds("GET", path, request)
    return ok(data, request)


@router.get("/products/{product_id}")
async def get_product(product_id: str, request: Request):
    """Get single product details."""
    data = await _proxy_ds("GET", f"/api/products/{product_id}", request)
    if isinstance(data, dict) and "_error" in data:
        return fail(data["_error"], 404, request)
    return ok(data, request)


@router.post("/sync")
async def trigger_sync(request: Request):
    """Trigger data sync from external platform (Shoplazza, etc.).

    Body: { entity: 'products'|'orders'|'all', shopId?: string }
    """
    body = await request.json()
    entity = body.get("entity", "all")
    ip = client_ip(request)

    # Rate limit sync operations (heavier than reads)
    if not rate_limit_check(f"ecom:sync:{ip}", max_requests=5, window=120):
        return fail("Sync rate limit exceeded, please wait 2 minutes", 429, request)

    data = await _proxy_ds("POST", "/api/sync", request, body=body, timeout=120)
    return ok(data, request)


# ── Orders ──


@router.get("/orders")
async def list_orders(request: Request):
    """List orders with pagination, status filter, and search.

    Query params: ?page=1&limit=20&status=paid&search=xxx
    """
    ip = client_ip(request)
    if not rate_limit_check(f"ecom:orders:{ip}", max_requests=30, window=60):
        return fail("Too many requests, please slow down", 429, request)

    query_string = str(request.url.query)
    path = f"/api/orders{('?' + query_string) if query_string else ''}"

    data = await _proxy_ds("GET", path, request)
    return ok(data, request)


@router.post("/orders/{order_id}/fulfill")
async def fulfill_order(order_id: str, request: Request):
    """Mark order as shipped with tracking info.

    Body: { trackingNumber?: string, trackingCompany?: string }
    """
    ip = client_ip(request)
    if not rate_limit_check(f"ecom:fulfill:{ip}", max_requests=10, window=60):
        return fail("Too many requests, please slow down", 429, request)

    body = await request.json()
    data = await _proxy_ds(
        "POST", f"/api/orders/{order_id}/fulfill", request, body=body
    )
    return ok(data, request)


# ── Stats ──


@router.get("/stats")
async def get_stats(request: Request):
    """Get e-commerce dashboard stats (revenue, orders, products)."""
    data = await _proxy_ds("GET", "/api/stats", request)
    return ok(data, request)


# ── Shop Config ──


@router.get("/shop")
async def get_shop_config(request: Request):
    """Get current shop connection configuration."""
    data = await _proxy_ds("GET", "/api/shop", request)
    return ok(data, request)


@router.post("/shop/connect")
async def connect_shop(request: Request):
    """Connect a new shop (Shoplazta, etc.).

    Body: { domain, accessToken, platform?, storeMode? }
    """
    body = await request.json()
    data = await _proxy_ds("POST", "/api/shop/connect", request, body=body)
    return ok(data, request)


@router.patch("/shop/mode")
async def update_shop_mode(request: Request):
    """Update shop store mode (marketplace/independent/both).

    Body: { storeMode: 'marketplace' | 'independent' | 'both' }
    """
    body = await request.json()
    data = await _proxy_ds("PATCH", "/api/shop/mode", request, body=body)
    return ok(data, request)


@router.delete("/shop/disconnect")
async def disconnect_shop(request: Request):
    """Disconnect current shop."""
    data = await _proxy_ds("DELETE", "/api/shop/disconnect", request)
    return ok(data, request)


# ── Health ──


@router.get("/health")
async def ecom_health(request: Request):
    """E-commerce service health — checks DS backend connectivity."""
    from services.proxy import _proxy_request

    headers = {
        "X-Tenant-ID": getattr(request.state, "tenant_id", "anonymous"),
        "X-Request-ID": getattr(request.state, "request_id", ""),
    }

    ds_health = await _proxy_request("GET", f"{DS_URL}/api/health", "", headers=headers)

    return ok(
        {
            "ecom": "ok" if isinstance(ds_health, dict) and not ds_health.get("_error") else "error",
            "ds_backend": ds_health if isinstance(ds_health, dict) else {"_error": str(ds_health)},
        },
        request,
    )


# ── AI Copywriting ──


@router.post("/ai/copy")
async def ai_copy(request: Request):
    """Generate AI-enhanced product copy.

    Body: { title, tone?: 'professional'|'casual'|'luxury'|'fun', lang?: 'zh'|'en' }
    """
    body = await request.json()
    data = await _proxy_ds("POST", "/api/ai/copy", request, body=body, timeout=60)
    return ok(data, request)


@router.get("/ai/status")
async def ai_status(request: Request):
    """Check AI service availability and current mode (demo/api)."""
    data = await _proxy_ds("GET", "/api/ai/status", request)
    return ok(data, request)
