#!/usr/bin/env python3
"""
Ghost Gateway — Unified API Gateway
=====================================
Single entry point for all Ghost services, four-layer routing:
  - /v1/human/*   → Human user interfaces (consumer/creator/developer roles share, unified permission control)
  - /v1/agent/*   → Agent ecosystem interfaces (feeds for industry info, A2A interaction)
  - /v1/internal/*→ Internal operations (Doubao capture, Obsidian, orchestrator, health)
  - /v1/net/*     → Network operations (router management, Net-Agent proxy)

Design principles:
  - Zero-trust defaults (explicit allowlists, no wildcard CORS in prod)
  - Observable (structured logs, correlation IDs, timing)
  - Resilient (timeouts, circuit-aware health, graceful degradation)
  - Role-agnostic design: users can be consumer/creator/developer at the same time, no fixed role binding
"""

import os
import sys
import logging
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure parent directory (ghost-main/) is on path for doubao_reader imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv

load_dotenv()

import config  # noqa: E402
import services.proxy as _proxy  # noqa: E402
from services.proxy import ok  # noqa: E402
from services.metrics import record_request, set_backend_health, get_metrics_response  # noqa: E402
from middleware.correlation import correlation_id_middleware  # noqa: E402
from routes.human import router as human_router  # noqa: E402
from routes.agent import router as agent_router  # noqa: E402
from routes.internal import router as internal_router  # noqa: E402
from routes.net import router as net_router  # noqa: E402
from routes.flow import router as flow_router  # noqa: E402
from routes.ecom import router as ecom_router  # noqa: E402
from routes.notify import router as notify_router  # noqa: E402
from routes.obsidian_bridge import router as obsidian_bridge_router  # noqa: E402
from routes.tools import router as tools_router  # noqa: E402
from middleware.tenant import TenantMiddleware  # noqa: E402

# ============================================================
# Structured Logger
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("ghost-gateway")


# ============================================================
# HTTP client (connection pool) — managed in lifespan
# ============================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — create client on startup, cleanup on shutdown."""
    _proxy.client = httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    )
    logger.info(
        "Gateway started — Alpha-ID=%s Nebula=%s Flow=%s Net-Agent=%s DS=%s",
        config.ALPHAID_URL,
        config.NEBULA_URL,
        config.FLOW_URL,
        config.NETAGENT_URL,
        os.getenv("DS_URL", config.DS_URL),
    )

    # 启动豆包桌面日志扫描器（默认启用，设置 ENABLE_DOUBAO_SCANNER=0 可禁用）
    if os.environ.get("ENABLE_DOUBAO_SCANNER", "1") != "0":
        ensure_scanner()

    yield
    await _proxy.client.aclose()
    logger.info("Gateway shutdown complete")


# ============================================================
# FastAPI Application
# ============================================================
tags_metadata = [
    {
        "name": "human",
        "description": "Human user interfaces — identity, chat, memory, registration, dashboard. Proxied to Alpha-ID.",
    },
    {
        "name": "agent",
        "description": "Agent ecosystem — A2A interaction topology, industry feeds.",
    },
    {
        "name": "flow",
        "description": "Workflow engine — templates, execution, AID sessions, map/POI, computer-use. Proxied to Flow :3036.",
    },
    {
        "name": "ecom",
        "description": "E-commerce operations — products, orders, sync, fulfillment, AI copywriting. Proxied to DS :3001.",
    },
    {
        "name": "internal",
        "description": "Internal operations — Doubao capture, Obsidian, orchestrator.",
    },
    {
        "name": "net",
        "description": "Network operations — router management, Net-Agent proxy.",
    },
    {
        "name": "tools",
        "description": "Code generation and optimization — ToolA (generator) and ToolB (optimizer).",
    },
]

app = FastAPI(
    title="Ghost Gateway",
    description="Ghost Unified API Gateway — Identity + Workflow + Registration",
    version="2.0.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS: explicit allowlist via AID_ALLOWED_ORIGINS env var (comma-separated)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


# Correlation ID + access log + metrics
@app.middleware("http")
async def _correlation_wrapper(request: Request, call_next):
    start = time.time()
    response = await correlation_id_middleware(request, call_next)
    duration = time.time() - start
    record_request(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
        duration=duration,
    )
    return response


# Tenant isolation middleware — extracts tenant_id from JWT/header
app.add_middleware(TenantMiddleware)


# ============================================================
# Route Mounting
# ============================================================
app.include_router(human_router)
app.include_router(agent_router)
app.include_router(internal_router)
app.include_router(net_router)
app.include_router(flow_router)
app.include_router(ecom_router)
app.include_router(notify_router)
app.include_router(obsidian_bridge_router)
app.include_router(tools_router)

# Ghost Workbench (extracted from inline _GHOST_PAGE)
# 静态文件服务：/workbench → ghost-main/gateway/static/
app.mount("/workbench", StaticFiles(directory="static", html=True), name="workbench")


# ============================================================
# Legacy Route Aliases（兼容旧版前端 /v1/register/* 路径）
# ============================================================
# ghost.js 使用 /v1/register/* 而非 /v1/human/register/*
# 添加通配转发路由，将 /v1/register/{action} 代理到 /v1/human/register/{action}

# TERM: Gateway — 统一 API 网关（端口 :18080），四层路由 /v1/human /v1/agent /v1/internal /v1/net


@app.post("/v1/register/{action}")
async def proxy_legacy_register(action: str, request: Request):
    """代理旧版 /v1/register/{action} → /v1/human/register/{action}"""
    from starlette.responses import JSONResponse
    body = await request.body()
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                f"http://{config.GATEWAY_HOST or '0.0.0.0'}:{config.GATEWAY_PORT}/v1/human/register/{action}",
                content=body,
                headers={"Content-Type": request.headers.get("content-type", "application/json")},
            )
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
        except Exception as e:
            return JSONResponse(content={"success": False, "error": str(e)}, status_code=502)


@app.get("/v1/doubao")
async def proxy_doubao(request: Request):
    """前端 iframe 使用 /v1/doubao，实际页面在 /v1/internal/doubao"""
    from starlette.responses import RedirectResponse
    return RedirectResponse(url="/v1/internal/doubao", status_code=307)


# ── Legacy Chat Alias ──
# feishu_webhook.py 和 demo UI 使用 /v1/chat，实际处理在 /v1/human/chat
@app.post("/v1/chat")
async def proxy_legacy_chat(request: Request):
    """代理旧版 /v1/chat → /v1/human/chat（内部代理用 127.0.0.1，避免 0.0.0.0 不可路由）

    关键：内部代理必须携带租户身份（X-Tenant-ID / Authorization / alpha_id），
    否则 /v1/human/chat 的 TenantMiddleware 会拒绝请求。
    """
    from starlette.responses import JSONResponse
    body = await request.json()
    # 内部代理必须用 loopback 地址，0.0.0.0 仅作 bind 地址，不可作为目标
    internal_url = f"http://127.0.0.1:{config.GATEWAY_PORT}/v1/human/chat"

    # 转发租户身份到内部代理，确保 /v1/human/chat 的 TenantMiddleware 放行
    proxy_headers = {"Content-Type": "application/json"}
    tenant_header = request.headers.get("X-Tenant-ID", "").strip()
    if tenant_header:
        proxy_headers["X-Tenant-ID"] = tenant_header
    auth_header = request.headers.get("authorization", "").strip()
    if auth_header:
        proxy_headers["Authorization"] = auth_header
    # 如果请求体包含 alpha_id，也作为 tenant 身份转发
    alpha_id_from_body = body.get("alpha_id", "").strip()
    if alpha_id_from_body and not tenant_header:
        proxy_headers["X-Tenant-ID"] = alpha_id_from_body

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                internal_url,
                json=body,
                headers=proxy_headers,
            )
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
        except Exception as e:
            return JSONResponse(content={"success": False, "error": str(e)}, status_code=502)


# ============================================================
# API Documentation Landing Page
# ============================================================
@app.get("/api", tags=["docs"])
async def api_docs(request: Request):
    """API documentation landing page — overview of all endpoints."""
    return ok(
        {
            "name": "Ghost Gateway API",
            "version": "2.0.0",
            "description": "Unified API Gateway for Ghost Web4.0 infrastructure",
            "documentation": {
                "swagger_ui": "/docs",
                "redoc": "/redoc",
                "openapi_schema": "/openapi.json",
            },
            "endpoints": {
                "health": {
                    "path": "/health",
                    "description": "Public health check — aggregates all backend statuses",
                },
                "human": {
                    "prefix": "/v1/human/*",
                    "description": "Human user interfaces — identity, chat, memory, registration, dashboard",
                    "backend": "Alpha-ID :8000",
                    "key_routes": [
                        "GET  /v1/human/identity",
                        "GET  /v1/human/profile",
                        "POST /v1/human/chat",
                        "GET  /v1/human/brain/status",
                        "POST /v1/human/brain/awake",
                        "POST /v1/human/intent/parse",
                        "POST /v1/human/memory/store",
                        "GET  /v1/human/memory/graph",
                        "GET  /v1/human/memory/search",
                        "GET  /v1/human/workflows",
                        "POST /v1/human/workflows/execute",
                        "POST /v1/human/register/send-sms",
                        "POST /v1/human/register/verify-sms",
                        "POST /v1/human/register/face-verify",
                        "POST /v1/human/register/generate-did",
                        "POST /v1/human/register/complete",
                        "GET  /v1/human/dashboard",
                    ],
                },
                "agent": {
                    "prefix": "/v1/agent/*",
                    "description": "Agent ecosystem — A2A interaction, industry feeds",
                    "backend": "Alpha-ID :8000",
                    "key_routes": [
                        "GET  /v1/agent/interact/topology",
                        "GET  /v1/agent/feeds/latest",
                        "POST /v1/agent/feeds/subscribe",
                    ],
                },
                "flow": {
                    "prefix": "/v1/agent/flow/*",
                    "description": "Workflow engine — templates, execution, AID sessions, map, computer-use",
                    "backend": "Flow :3036",
                    "key_routes": [
                        "GET  /v1/agent/flow/health",
                        "GET  /v1/agent/flow/templates",
                        "GET  /v1/agent/flow/templates/{id}",
                        "POST /v1/agent/flow/execute",
                        "GET  /v1/agent/flow/executions",
                        "GET  /v1/agent/flow/executions/{id}",
                        "GET  /v1/agent/flow/aid/capabilities",
                        "POST /v1/agent/flow/aid/sessions",
                        "GET  /v1/agent/flow/aid/sessions/{id}",
                        "POST /v1/agent/flow/aid/sessions/{id}/messages",
                        "DELETE /v1/agent/flow/aid/sessions/{id}",
                        "GET  /v1/agent/flow/map/search",
                        "GET  /v1/agent/flow/map/pois",
                        "POST /v1/agent/flow/map/routes",
                        "GET  /v1/agent/flow/map/routes",
                        "GET  /v1/agent/flow/map/routes/{id}",
                        "DELETE /v1/agent/flow/map/routes/{id}",
                        "GET  /v1/agent/flow/computer-use/status",
                        "POST /v1/agent/flow/computer-use/tasks",
                        "GET  /v1/agent/flow/computer-use/tasks",
                        "GET  /v1/agent/flow/computer-use/tasks/{id}",
                        "POST /v1/agent/flow/computer-use/screenshot",
                    ],
                },
                "ecom": {
                    "prefix": "/v1/ecom/*",
                    "description": "E-commerce operations — products, orders, sync, fulfillment, AI copy. Proxied to DS :3001.",
                    "backend": "Ghost DS :3001",
                    "key_routes": [
                        "GET  /v1/ecom/products",
                        "GET  /v1/ecom/products/{id}",
                        "POST /v1/ecom/sync",
                        "GET  /v1/ecom/orders",
                        "POST /v1/ecom/orders/{id}/fulfill",
                        "GET  /v1/ecom/stats",
                        "POST /v1/ecom/ai/copy",
                        "GET  /v1/ecom/ai/status",
                        "GET  /v1/ecom/shop",
                        "POST /v1/ecom/shop/connect",
                        "DELETE /v1/ecom/shop/disconnect",
                    ],
                },
                "internal": {
                    "prefix": "/v1/internal/*",
                    "description": "Internal operations — Doubao capture, Obsidian, orchestrator",
                    "backend": "Various",
                    "key_routes": [
                        "POST /v1/internal/doubao/capture",
                        "POST /v1/internal/orchestrator/task/submit",
                        "GET  /v1/internal/orchestrator/tasks",
                        "GET  /v1/internal/orchestrator/task/{id}",
                        "GET  /v1/internal/obsidian/status",
                    ],
                },
                "net": {
                    "prefix": "/v1/net/*",
                    "description": "Network operations — router management, Net-Agent proxy",
                    "backend": "Net-Agent :18180",
                    "key_routes": [
                        "GET  /v1/net/vendors",
                        "POST /v1/net/config/save",
                        "GET  /v1/net/config",
                        "POST /v1/net/action/{action}",
                        "GET  /v1/net/tasks/pending",
                        "POST /v1/net/tasks/{id}/complete",
                        "POST /v1/net/metrics/upload",
                        "GET  /v1/net/logs/history",
                        "GET  /v1/net/logs/audit",
                    ],
                },
            },
            "response_format": {
                "success": {"success": True, "data": {}, "ts": 1234567890},
                "error": {"success": False, "error": "message", "ts": 1234567890},
            },
            "headers": {
                "X-Request-ID": "Optional client-provided request ID (UUID). Gateway echoes it back.",
                "X-Correlation-ID": "Auto-generated if not provided. Present in all responses.",
            },
        },
        request,
    )


# ============================================================
# Ghost Web UI (served at root)
# ============================================================
# TERM: Ghost Workbench — 豆包记忆桥操作面板
# Extracted from inline _GHOST_PAGE to static/ghost_workbench.html


@app.get("/", include_in_schema=False)
def ghost_home():
    """Ghost 工作台主页 — 豆包记忆桥操作面板."""
    from fastapi.responses import FileResponse
    return FileResponse(str(Path(__file__).parent / "static" / "ghost_workbench.html"))


# ============================================================
# Prometheus Metrics
# ============================================================
@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus metrics endpoint — scrape target for monitoring."""
    resp = get_metrics_response()
    if resp is None:
        return JSONResponse(
            {"error": "prometheus_client not installed"},
            status_code=503,
        )
    return resp


# ============================================================
# Health Check (public)
# ============================================================
@app.get("/health")
async def health(request: Request):
    """Public health check — aggregates status of all backend services."""
    import asyncio

    # Check all backends concurrently
    async def _check(url: str) -> bool:
        try:
            r = await _proxy.client.get(f"{url}/health", timeout=5.0)
            return r.status_code < 500
        except Exception:
            return False

    alphaid_ok, nebula_ok, orchestrator_ok, netagent_ok, flow_ok, ds_ok = await asyncio.gather(
        _check(config.ALPHAID_URL),
        _check(config.NEBULA_URL),
        _check(config.ORCHESTRATOR_URL),
        _check(config.NETAGENT_URL),
        _check(config.FLOW_URL),
        _check(f"{config.DS_URL}/api/health"),
    )

    # Obsidian vault check (local filesystem) — 使用服务层的路径，避免硬编码不一致
    from services.obsidian import get_vault_path

    vault_path = get_vault_path()
    obsidian_ok = os.path.isdir(vault_path) and len(os.listdir(vault_path)) > 0

    # Update Prometheus backend health gauges
    set_backend_health("alphaid", alphaid_ok)
    set_backend_health("nebula", nebula_ok)
    set_backend_health("orchestrator", orchestrator_ok)
    set_backend_health("obsidian", obsidian_ok)
    set_backend_health("netagent", netagent_ok)
    set_backend_health("flow", flow_ok)
    set_backend_health("ghost-ds", ds_ok)

    all_ok = all([alphaid_ok, nebula_ok, netagent_ok, flow_ok, ds_ok])

    return ok(
        {
            "gateway": "ok",
            "overall": "ok" if all_ok else "degraded",
            "alphaid": "ok" if alphaid_ok else "error",
            "nebula": "ok" if nebula_ok else "error",
            "orchestrator": "ok" if orchestrator_ok else "error",
            "obsidian": "ok" if obsidian_ok else "not_found",
            "netagent": "ok" if netagent_ok else "error",
            "flow": "ok" if flow_ok else "error",
            "ghost-ds": "ok" if ds_ok else "error",
        },
        request,
    )


# ============================================================
# Periodic scanner for Doubao desktop app LevelDB
# ============================================================
# 扫描器在 lifespan 中启动（而非模块级别），避免 import 时产生副作用。
# 可通过设置环境变量 ENABLE_DOUBAO_SCANNER=0 禁用。
_scanner_started = False
_scanner_thread = None


def _run_scanner_loop():
    """后台扫描循环：读取豆包 LevelDB → 通过 ASGI transport 直接调用内部 API。"""
    from doubao_reader.log_reader import LogReader
    from doubao_reader.obsidian_organizer import run_organization, batch_link_related

    # 使用 ASGI transport 直接调用 FastAPI 应用，避免 HTTP loopback
    import httpx

    transport = httpx.ASGITransport(app=app)
    client = httpx.Client(transport=transport, base_url="http://testserver")

    reader = LogReader()
    time.sleep(10)  # Wait for server to start
    while True:
        try:
            convs = reader.read_all()
            logger.info("Doubao scanner: found %d conversations", len(convs))
            for conv in convs[:5]:  # Limit to 5 per scan
                payload = conv.to_dict()
                try:
                    r = client.post(
                        "/v1/internal/doubao/capture", json=payload, timeout=5
                    )
                    logger.debug("Scanned: %s", r.status_code)
                except Exception as e:
                    logger.debug("Scan send error: %s", e)
        except Exception as e:
            logger.error("Doubao scanner error: %s", e)
        # Run Obsidian organization
        try:
            run_organization()
            batch_link_related()
        except Exception as org_err:
            logger.error("Organization error: %s", org_err)

        time.sleep(120)  # Scan every 2 minutes


def ensure_scanner():
    """Start the Doubao desktop log scanner background thread (idempotent)."""
    global _scanner_started, _scanner_thread
    if _scanner_started:
        return
    _scanner_started = True

    _scanner_thread = threading.Thread(target=_run_scanner_loop, daemon=True)
    _scanner_thread.start()
    logger.info("Doubao desktop log scanner started")


# ============================================================
# Startup
# ============================================================
if __name__ == "__main__":
    import uvicorn

    print(f"""
╔══════════════════════════════════════════════════╗
║           Ghost Gateway v2.0.0                   ║
║   Unified API Gateway                            ║
╠══════════════════════════════════════════════════╣
║   Port:     {config.GATEWAY_PORT}                                ║
║   Alpha-ID: {config.ALPHAID_URL}    ║
║   Nebula:   {config.NEBULA_URL}       ║
║   Flow:     {config.FLOW_URL}       ║
║   NetAgent: {config.NETAGENT_URL}      ║
╚══════════════════════════════════════════════════╝
    """)
    uvicorn.run("gateway.app:app", host="0.0.0.0", port=config.GATEWAY_PORT)
