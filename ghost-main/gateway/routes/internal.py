"""Internal Operations Layer — /v1/internal/* routes.

Platform internal use only, not exposed to public.
"""

import asyncio
import logging
import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

import config
from services.eventbus_client import get_gateway_eventbus
from services.obsidian import (
    check_vault_status,
)
from services.proxy import fail, has_error, ok, proxy_get, proxy_post

logger = logging.getLogger("ghost-gateway")

router = APIRouter(prefix="/v1/internal", tags=["internal"])


# ── Monitoring Dashboard ──


@router.get("/monitoring")
async def monitoring_dashboard(request: Request):
    """Internal: Serve the Ghost Platform monitoring dashboard."""
    html_path = os.path.join(os.path.dirname(__file__), "..", "monitoring.html")
    if os.path.exists(html_path):
        html = open(html_path, encoding="utf-8").read()
        return HTMLResponse(content=html)
    return HTMLResponse(content="<h1>Monitoring dashboard not found</h1>", status_code=404)


@router.get("/monitoring/metrics")
async def monitoring_metrics(request: Request):
    """Internal: Aggregate metrics from all backend services.

    Calls each service's /metrics endpoint and returns combined health + metrics.
    This replaces the need for a separate Prometheus server.
    """
    import time

    import httpx

    services = {
        "gateway": f"http://localhost:{config.GATEWAY_PORT}/metrics",
        "alphaid": f"{config.ALPHAID_URL}/metrics",
        "nebula": f"{config.NEBULA_URL}/metrics",
        "flow": f"{config.FLOW_URL}/metrics",
        "orchestrator": f"{config.ORCHESTRATOR_URL}/metrics",
        "netagent": f"{config.NETAGENT_URL}/metrics",
        "ghost-ds": f"{config.DS_URL}/api/metrics",
    }

    results = {}
    health = {}

    async def _fetch(name: str, url: str) -> tuple[str, dict]:
        # /metrics 返回 Prometheus 纯文本，不能用 JSON 解析器（_proxy_request），
        # 必须直接 httpx 抓取文本。
        try:
            start = time.perf_counter()
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
            duration = time.perf_counter() - start

            if resp.status_code != 200:
                return name, {
                    "status": resp.status_code,
                    "ok": False,
                    "error": f"HTTP {resp.status_code}",
                    "duration_ms": round(duration * 1000, 1),
                }
            return name, {
                "status": 200,
                "ok": True,
                "duration_ms": round(duration * 1000, 1),
                "size_bytes": len(resp.text),
                "metrics": resp.text[:5000],
            }
        except Exception as e:
            return name, {
                "status": 0,
                "ok": False,
                "error": str(e),
                "duration_ms": 0,
            }

    # Fetch all concurrently
    tasks = [_fetch(name, url) for name, url in services.items()]
    completed = await asyncio.gather(*tasks, return_exceptions=True)

    for result in completed:
        if isinstance(result, Exception):
            continue
        name, data = result
        results[name] = data
        health[name] = "ok" if data.get("ok") else "error"

    overall = "ok" if all(v == "ok" for v in health.values()) else "degraded"

    return ok({
        "overall": overall,
        "services": health,
        "details": results,
        "timestamp": time.time(),
    }, request)


@router.get("/monitoring/health")
async def monitoring_health(request: Request):
    """Internal: Quick health summary for monitoring dashboards."""

    from services.proxy import _proxy_request

    services = {
        "alphaid": config.ALPHAID_URL,
        "nebula": config.NEBULA_URL,
        "orchestrator": config.ORCHESTRATOR_URL,
        "netagent": config.NETAGENT_URL,
        "flow": config.FLOW_URL,
        "ghost-ds": config.DS_URL,
    }

    health = {}

    async def _check(name: str, base_url: str) -> None:
        try:
            data = await _proxy_request("GET", f"{base_url}/health", "")

            if isinstance(data, dict) and data.get("_error"):
                health[name] = "error"
            else:
                health[name] = "ok"
        except Exception:
            health[name] = "error"

    tasks = [_check(name, url) for name, url in services.items()]
    await asyncio.gather(*tasks)

    # Obsidian vault check
    vault_status = check_vault_status()
    health["obsidian"] = "ok" if vault_status.get("exists") else "not_found"

    overall = "ok" if all(v == "ok" for v in health.values()) else "degraded"

    return ok({"overall": overall, "services": health}, request)


# ── WeChat Webhook ──


@router.post("/webhook/wechat")
async def wechat_webhook(request: Request):
    """Proxy WeChat webhook to Nebula /api/v1/wechat.

    WeChat sends XML messages to this endpoint. We forward to Nebula
    which handles signature verification, message parsing, and reply.

    Also emits SOCIAL_MESSAGE event to EventBus for cross-service consumption.
    """
    body = await request.body()

    # Parse WeChat XML to extract message content for EventBus
    event_emitted = False
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(body.decode("utf-8"))
        msg_type = root.find("MsgType")
        content = root.find("Content")
        from_user = root.find("FromUserName")

        if msg_type is not None and msg_type.text == "text" and content is not None:
            bus = get_gateway_eventbus()
            event = bus.emit(
                "social.message",
                {
                    "platform": "wechat",
                    "action_type": "MESSAGE_RECEIVED",
                    "intent": "wechat.message",
                    "payload": {
                        "content": content.text,
                        "from_user": from_user.text if from_user is not None else "",
                        "msg_type": msg_type.text,
                    },
                    "source_alpha_id": "",
                },
                source="gateway_wechat_webhook",
            )
            event_emitted = event is not None
            if event_emitted:
                logger.info("[WeChat] Emitted SOCIAL_MESSAGE event (id=%s)", event.event_id)
    except Exception as e:
        logger.warning("[WeChat] EventBus emit failed (non-critical): %s", e)

    # Forward to Nebula WeChat endpoint
    data = await proxy_post(
        "/api/v1/wechat",
        config.NEBULA_URL,
        body=body,
        is_json=False,
    )
    if has_error(data):
        return fail(f"WeChat proxy error: {data.get('_error', 'unknown')}", 502, request)
    return ok(data, request)


@router.get("/webhook/wechat")
async def wechat_verify(request: Request):
    """WeChat signature verification — proxy to Nebula."""
    # Forward query params for signature verification
    query_params = str(request.query_params)
    data = await proxy_get(
        f"/api/v1/wechat?{query_params}",
        config.NEBULA_URL,
    )
    if has_error(data):
        return fail(f"WeChat verify error: {data.get('_error', 'unknown')}", 502, request)
    return ok(data, request)


# ── Orchestrator ──


@router.post("/orchestrator/task/submit")
async def orch_submit(request: Request):
    """Internal: Submit task to orchestrator."""
    body = await request.json()
    data = await proxy_post("/v1/task/submit", config.ORCHESTRATOR_URL, body=body)
    return ok(data, request)


@router.get("/orchestrator/tasks")
async def orch_tasks(request: Request):
    """Internal: Get all orchestrator tasks."""
    data = await proxy_get("/v1/tasks", config.ORCHESTRATOR_URL)
    return ok(data, request)


@router.get("/orchestrator/task/{task_id}")
async def orch_task(task_id: str, request: Request):
    """Internal: Get task status by ID."""
    data = await proxy_get(f"/v1/task/{task_id}", config.ORCHESTRATOR_URL)
    return ok(data, request)


# ── Internal Status Checks ──


@router.get("/obsidian/status")
async def obsidian_status(request: Request):
    """Internal: Check Obsidian vault status."""
    return ok(check_vault_status(), request)


# ── Observability (盘活 Alpha-ID 死代码：2 条路由) ──


@router.get("/observability/ready")
async def alphaid_ready(request: Request):
    """Alpha-ID readiness check → proxy to Alpha-ID."""
    data = await proxy_get("/api/v1/observability/ready", config.ALPHAID_URL)
    return ok(data, request)


@router.get("/observability/metrics")
async def alphaid_metrics(request: Request):
    """Alpha-ID Prometheus metrics → proxy to Alpha-ID."""
    data = await proxy_get("/api/v1/observability/metrics", config.ALPHAID_URL)
    if isinstance(data, dict) and data.get("_error"):
        return fail(f"Alpha-ID metrics error: {data.get('_error')}", 502, request)
    return PlainTextResponse(content=str(data), media_type="text/plain")


# ── Event Emit (DS / 前端事件入口) ──


@router.post("/events/emit")
async def emit_event(request: Request):
    """DS / 前端事件入口 — 接收事件并写入 Redis Streams.

    简化 EventBus 架构：DS 不再直接连接 Redis，
    而是通过 Gateway 统一写入 EventBus stream。
    """
    bus = get_gateway_eventbus()
    body = await request.json()
    event_type = body.get("type", "unknown")
    data = body.get("data", {})
    source = body.get("source", "ds")

    event = bus.emit(event_type, data, source=source)
    if event is None:
        return fail("EventBus unavailable — Redis not connected", 503, request)
    return ok({"event_id": event.event_id, "type": event_type}, request)
