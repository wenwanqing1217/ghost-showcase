"""Internal Operations Layer — /v1/internal/* routes.

Platform internal use only, not exposed to public.
"""

import os
import logging
import asyncio
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from services.proxy import proxy_get, proxy_post, ok, fail, has_error
from services.eventbus_client import get_gateway_eventbus
from middleware.rate_limit import client_ip
from services.obsidian import (
    check_vault_status,
    write_conversation_async,
    trigger_organization,
)
import config

logger = logging.getLogger("ghost-gateway")

router = APIRouter(prefix="/v1/internal", tags=["internal"])


# ── Monitoring Dashboard ──


@router.get("/monitoring")
async def monitoring_dashboard(request: Request):
    """Internal: Serve the Ghost Platform monitoring dashboard."""
    html_path = os.path.join(os.path.dirname(__file__), "..", "monitoring.html")
    if os.path.exists(html_path):
        html = open(html_path, "r", encoding="utf-8").read()
        return HTMLResponse(content=html)
    return HTMLResponse(content="<h1>Monitoring dashboard not found</h1>", status_code=404)


@router.get("/monitoring/metrics")
async def monitoring_metrics(request: Request):
    """Internal: Aggregate metrics from all backend services.
    
    Calls each service's /metrics endpoint and returns combined health + metrics.
    This replaces the need for a separate Prometheus server.
    """
    import time
    
    # Use the shared httpx client from proxy module
    from services.proxy import _proxy_request
    
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
        try:
            start = time.perf_counter()
            # Use the shared client (connection pool)
            data = await _proxy_request("GET", url, "")
            duration = time.perf_counter() - start
            
            if isinstance(data, dict) and data.get("_error"):
                return name, {
                    "status": 0,
                    "ok": False,
                    "error": data["_error"],
                    "duration_ms": round(duration * 1000, 1),
                }
            
            # Convert to text for display
            if isinstance(data, dict):
                text = "\n".join(f"{k} {v}" for k, v in data.items())
            else:
                text = str(data)
            
            return name, {
                "status": 200,
                "ok": True,
                "duration_ms": round(duration * 1000, 1),
                "size_bytes": len(text),
                "metrics": text[:5000],
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
    import time
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
            start = time.perf_counter()
            data = await _proxy_request("GET", f"{base_url}/health", "")
            duration = time.perf_counter() - start
            
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


# ── Doubao Capture ──


@router.get("/doubao")
async def doubao_page(request: Request):
    """Internal: Serve the Doubao workspace page."""
    html_path = os.path.join(os.path.dirname(__file__), "..", "doubao_page.html")
    if os.path.exists(html_path):
        html = open(html_path, "r", encoding="utf-8").read()
        return HTMLResponse(content=html)
    return HTMLResponse(content="<h1>Doubao page not found</h1>", status_code=404)


@router.post("/doubao/capture")
async def doubao_capture(request: Request):
    """Internal: Accept Doubao conversation data from local LogReader only."""
    ip = client_ip(request)
    if ip not in ("127.0.0.1", "::1", "localhost"):
        logger.warning("Rejected doubao capture from non-local IP: %s", ip)
        return fail("Only local requests allowed", 403, request)
    body = await request.json()
    session_id = body.get("session_id", "")
    messages = body.get("messages", [])

    # Refine: dedup, filter noise, auto-tag
    if messages:
        from doubao_reader.knowledge_refiner import refine_conversation  # lazy import (not available in Docker)

        messages = refine_conversation(body.get("metadata", {}), messages)

    if not session_id or not messages:
        return fail("session_id and messages required", 400, request)
    for m in messages:
        if not all(k in m for k in ("role", "content")):
            return fail("Each message must have role and content", 400, request)

    bot_id = body.get("bot_id", "")
    summary = messages[0].get("content", "")[:100]
    last = messages[-1].get("content", "")[:200] if len(messages) > 1 else ""

    memory_payload = {
        "alpha_id": os.getenv("DEFAULT_ALPHA_ID", "Alpha-001"),
        "content": "[Doubao] " + summary + (" ... " + last if last else ""),
        "category": "doubao_chat",
        "sensitivity": 10,
        "source": "doubao",
        "tags": ["doubao", "chat"] + ([bot_id] if bot_id else []),
        "metadata": {
            "session_id": session_id,
            "bot_id": bot_id,
            "captured_at": body.get("captured_at", 0),
            "message_count": len(messages),
            "messages": messages,
        },
    }

    # 获取 JWT Token（自动注册/登录默认 Alpha-ID）
    _alpha_id = os.getenv("DEFAULT_ALPHA_ID", "Alpha-001")
    _access_token = None
    try:
        # 尝试登录默认 Alpha-ID
        login_data = await proxy_post(
            "/api/v1/identity/login",
            config.ALPHAID_URL,
            body={"alpha_id": _alpha_id, "device_fingerprint": f"gateway_{_alpha_id}"},
        )
        if isinstance(login_data, dict):
            _access_token = login_data.get("access_token") or (login_data.get("data", {}) or {}).get("access_token")
        # 登录失败 → 尝试注册后再登录
        if not _access_token:
            reg_data = await proxy_post(
                "/api/v1/identity/register",
                config.ALPHAID_URL,
                body={"alpha_id": _alpha_id, "device_fingerprint": f"gateway_{_alpha_id}"},
            )
            registered_aid = _alpha_id
            if isinstance(reg_data, dict):
                registered_aid = reg_data.get("alpha_id", _alpha_id) or _alpha_id
            login_data2 = await proxy_post(
                "/api/v1/identity/login",
                config.ALPHAID_URL,
                body={"alpha_id": registered_aid, "device_fingerprint": f"gateway_{_alpha_id}"},
            )
            if isinstance(login_data2, dict):
                _access_token = login_data2.get("access_token") or (login_data2.get("data", {}) or {}).get("access_token")
        if _access_token:
            logger.info("Gateway→Alpha-ID auth ok (alpha_id=%s)", _alpha_id)
    except Exception as auth_err:
        logger.warning("Gateway→Alpha-ID auth failed: %s", auth_err)

    # 调用 dual-chain/save（带 JWT Token + CSRF 头）
    from urllib.parse import urlparse

    _parsed = urlparse(config.ALPHAID_URL)
    _alphaid_origin = f"{_parsed.scheme}://{_parsed.netloc}"
    _headers = {
        "X-Requested-With": "XMLHttpRequest",  # Alpha-ID CSRF 防护要求
        "Origin": _alphaid_origin,              # Alpha-ID 允许的来源
    }
    if _access_token:
        _headers["Authorization"] = f"Bearer {_access_token}"
    data = await proxy_post(
        "/api/v1/dual-chain/save", config.ALPHAID_URL, body=memory_payload, headers=_headers
    )

    # Also write to Obsidian vault
    write_conversation_async(
        metadata=memory_payload.get("metadata", {}),
        messages=messages,
        session_id=session_id,
        bot_id=bot_id,
    )

    if has_error(data):
        logger.error("Failed to store doubao memory: %s", data.get("_error"))
        return ok(
            {
                "status": "stored_with_warning",
                "session_id": session_id,
                "error": data.get("_error"),
            },
            request,
        )

    # Trigger Obsidian organization in background
    trigger_organization()

    logger.info(
        "Doubao conversation %s captured: %d messages", session_id, len(messages)
    )
    return ok(
        {
            "status": "stored",
            "session_id": session_id,
            "message_count": len(messages),
        },
        request,
    )


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
                EventType.SOCIAL_MESSAGE.value if hasattr(EventType, "value") else "social.message",
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
    from fastapi.responses import PlainTextResponse
    data = await proxy_get("/api/v1/observability/metrics", config.ALPHAID_URL)
    if isinstance(data, dict) and data.get("_error"):
        return fail(f"Alpha-ID metrics error: {data.get('_error')}", 502, request)
    return PlainTextResponse(content=str(data), media_type="text/plain")
