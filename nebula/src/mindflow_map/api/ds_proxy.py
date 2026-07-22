"""DS Dashboard 代理路由

将 DS 服务的能力暴露为 mindflow-map 的 /api/v1/ds/* 端点，
使前端和外部调用方可以通过 mindflow-map 统一访问 DS 数据。

所有端点复用 mindflow-map 的 Bearer Token 认证。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from mindflow_map.api.ds_client import DSClient, DSClientError, get_ds_client
from mindflow_map.middleware.auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user_id)])


# ── Dashboard 代理 ──


@router.get("/metrics")
async def get_ds_metrics() -> Dict[str, Any]:
    """获取 DS Dashboard 指标"""
    client = get_ds_client()
    try:
        return await client.get_metrics()
    except DSClientError as exc:
        raise HTTPException(
            status_code=exc.status_code or 502,
            detail=f"DS metrics unavailable: {exc}",
        ) from exc


@router.get("/alerts")
async def get_ds_alerts() -> Dict[str, Any]:
    """获取 DS 告警列表"""
    client = get_ds_client()
    try:
        return await client.get_alerts()
    except DSClientError as exc:
        raise HTTPException(
            status_code=exc.status_code or 502,
            detail=f"DS alerts unavailable: {exc}",
        ) from exc


# ── Shopify 代理 ──


@router.get("/products")
async def get_ds_products(
    limit: int = Query(default=50, ge=1, le=200),
) -> Dict[str, Any]:
    """获取 DS Shopify 产品列表"""
    client = get_ds_client()
    try:
        return await client.get_products(limit=limit)
    except DSClientError as exc:
        raise HTTPException(
            status_code=exc.status_code or 502,
            detail=f"DS products unavailable: {exc}",
        ) from exc


@router.get("/orders")
async def get_ds_orders(
    limit: int = Query(default=50, ge=1, le=200),
) -> Dict[str, Any]:
    """获取 DS Shopify 订单列表"""
    client = get_ds_client()
    try:
        return await client.get_orders(limit=limit)
    except DSClientError as exc:
        raise HTTPException(
            status_code=exc.status_code or 502,
            detail=f"DS orders unavailable: {exc}",
        ) from exc


# ── Health 代理 ──


@router.get("/health")
async def ds_health() -> Dict[str, Any]:
    """检查 DS 服务健康状态（透传）"""
    client = get_ds_client()
    try:
        result = await client.health_check()
        return {"service": "ds", "reachable": True, "details": result}
    except DSClientError:
        return {"service": "ds", "reachable": False, "details": None}
