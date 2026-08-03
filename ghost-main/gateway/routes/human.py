"""Human User Layer — /v1/human/* routes.

All human-facing interfaces, unified permission control.
No fixed role binding, users can be consumer/creator/developer at the same time.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Request

from services.proxy import proxy_get, proxy_post, ok, fail
from middleware.rate_limit import rate_limit_check, client_ip
from services.memory_graph import get_memory_graph
from services.obsidian import search_vault

import config

logger = logging.getLogger("ghost-gateway")

router = APIRouter(prefix="/v1/human", tags=["human"])


# ── Helper: proxy to Alpha-ID with consistent error handling ──

async def _proxy_alphaid_get(path: str, request: Request, headers: dict = None):
    """Proxy GET to Alpha-ID and return unified response."""
    data = await proxy_get(path, config.ALPHAID_URL, headers=headers)
    return ok(data, request)


async def _proxy_alphaid_post(path: str, request: Request, body: dict = None, headers: dict = None):
    """Proxy POST to Alpha-ID and return unified response."""
    data = await proxy_post(path, config.ALPHAID_URL, body=body, headers=headers)
    return ok(data, request)


# ── Identity & Profile ──


@router.get("/identity")
async def get_identity(request: Request, alpha_id: Optional[str] = None):
    """Get current identity → proxy to Alpha-ID API."""
    aid = alpha_id or config.DEFAULT_ALPHA_ID
    data = await proxy_get(
        f"/api/v1/identity/{aid}",
        config.ALPHAID_URL,
        headers={"Authorization": "Bearer placeholder"},
    )
    if "_error" in data:
        data = await proxy_get("/api/v1/identity/stats/overview", config.ALPHAID_URL)
    return ok(data, request)


@router.get("/profile")
async def get_profile(request: Request):
    """Get user profile → proxy to Alpha-ID.

    Forwards the client's Bearer token to Alpha-ID.
    No token → Alpha-ID returns 401 → Gateway returns 502 (correct behavior).
    """
    client_auth = request.headers.get("authorization")
    data = await proxy_get(
        "/api/v1/identity/me",
        config.ALPHAID_URL,
        headers={"Authorization": client_auth} if client_auth else None,
    )
    return ok(data, request)


# ── Brain Status ──


@router.get("/brain/status")
async def get_brain_status(request: Request, alpha_id: Optional[str] = None):
    """Get brain status → proxy to Alpha-ID."""
    aid = alpha_id or config.DEFAULT_ALPHA_ID
    return await _proxy_alphaid_get(f"/api/v1/agent/status?alpha_id={aid}", request)


@router.post("/brain/awake")
async def brain_awake(request: Request):
    """Wake up brain → proxy to Alpha-ID (uses status as ping)."""
    body = await request.json()
    aid = body.get("alpha_id", config.DEFAULT_ALPHA_ID)
    return await _proxy_alphaid_get(f"/api/v1/agent/status?alpha_id={aid}", request)


# ── Chat & Intent ──


@router.post("/chat")
async def chat(request: Request):
    """Chat with Agent → proxy to Alpha-ID /chat, auto-register unknown users.

    流程：
    1. 先尝试用 quick-register 获取 JWT（已注册则直接登录）
    2. 用 JWT 调用 Alpha-ID /api/v1/agent/chat
    """
    ip = client_ip(request)
    if not rate_limit_check(f"chat:{ip}", max_requests=10, window=60):
        return fail("Too many requests, please slow down", 429, request)
    body = await request.json()
    aid = body.get("alpha_id", config.DEFAULT_ALPHA_ID)
    message = body.get("message", "")
    if not message:
        return fail("message required", 400, request)

    # Step 1: 通过 quick-register 获取 JWT（幂等：已注册则直接登录）
    access_token = None
    try:
        qr_body = {"alpha_id": aid} if aid != config.DEFAULT_ALPHA_ID else {}
        qr_data = await proxy_post(
            "/api/v1/identity/quick-register",
            config.ALPHAID_URL,
            body=qr_body,
        )
        if isinstance(qr_data, dict):
            access_token = qr_data.get("access_token")
            # 使用 quick-register 返回的 alpha_id（可能自动生成）
            aid = qr_data.get("alpha_id", aid)
            if not access_token:
                access_token = (qr_data.get("data", {}) or {}).get("access_token")
        logger.info("quick-register ok for %s, token=%s", aid, bool(access_token))
    except Exception as e:
        logger.warning("quick-register failed: %s", e)

    # Step 2: 用 JWT 调用 Alpha-ID /api/v1/agent/chat
    chat_headers = {"Authorization": f"Bearer {access_token}"} if access_token else None
    data = await proxy_post(
        "/api/v1/agent/chat",
        config.ALPHAID_URL,
        body={"alpha_id": aid, "message": message},
        headers=chat_headers,
    )

    return ok(data, request)


@router.post("/intent/parse")
async def parse_intent(request: Request):
    """Intent parsing — gateway-level smart routing."""
    body = await request.json()
    text = body.get("text", "").strip()
    if not text:
        return fail("text required", 400, request)

    text_lower = text.lower()
    is_identity = any(
        kw in text_lower for kw in ["身份", "我是谁", "did", "identity", "画像"]
    )

    if is_identity:
        identity = await proxy_get(
            "/api/v1/identity/stats/overview", config.ALPHAID_URL
        )
        profile = await proxy_get("/api/v1/identity/me", config.ALPHAID_URL)
        return ok(
            {
                "route": "identity",
                "identity": identity,
                "profile_summary": profile.get("profile", {}).get("persona", {}),
            },
            request,
        )
    else:
        data = await proxy_post(
            "/api/v1/agent/chat",
            config.ALPHAID_URL,
            body={"alpha_id": config.DEFAULT_ALPHA_ID, "message": text},
        )
        return ok(
            {
                "route": "chat",
                "reply": data.get("reply", ""),
                "raw": data,
            },
            request,
        )


# ── Memory ──


@router.post("/memory/store")
async def memory_store(request: Request):
    """Store memory → proxy to Alpha-ID /api/v1/dual-chain/save."""
    body = await request.json()
    return await _proxy_alphaid_post("/api/v1/dual-chain/save", request, body=body)


@router.get("/memory/graph")
async def memory_graph(request: Request):
    """Return memory knowledge graph for d3.js visualization. Free, no LLM."""
    graph = get_memory_graph()
    return ok(graph, request)


@router.get("/memory/search")
async def memory_search(keyword: str = "", limit: int = 20, request: Request = None):
    """Search the Obsidian vault for memories matching keyword."""
    try:
        results = search_vault(keyword=keyword, limit=limit)
        return ok({"results": results, "total": len(results)}, request)
    except Exception as e:
        return fail(str(e), 500, request)


@router.get("/memory/search")
async def memory_search_public(keyword: str = "", limit: int = 20, request: Request = None):
    """Public alias: /v1/memory/search → same as /v1/human/memory/search."""
    return await memory_search(keyword=keyword, limit=limit, request=request)


@router.get("/memory/graph")
async def memory_graph_public(request: Request):
    """Public alias: /v1/memory/graph → same as /v1/human/memory/graph."""
    return await memory_graph(request)


@router.get("/dual-chain/stats")
async def dual_chain_stats(request: Request):
    """Proxy dual-chain memory stats to Alpha-ID."""
    data = await proxy_get("/api/v1/dual-chain/stats", config.ALPHAID_URL)
    return ok(data, request)


# ── Workflows ──


@router.get("/workflows")
async def get_workflows(request: Request):
    """Get workflow templates → proxy to Nebula."""
    data = await proxy_get("/api/v1/workflow/templates", config.NEBULA_URL)
    return ok(data, request)


@router.post("/workflows/execute")
async def execute_workflow(request: Request):
    """Execute workflow → proxy to Nebula."""
    body = await request.json()
    data = await proxy_post("/api/v1/workflow/execute", config.NEBULA_URL, body=body)
    return ok(data, request)


# ── Registration ──


@router.post("/register/send-sms")
async def register_send_sms(request: Request):
    """Send SMS verification code → proxy to Alpha-ID (rate limited: 5 req/60s/IP)."""
    ip = client_ip(request)
    if not rate_limit_check(f"sms:{ip}", max_requests=5, window=60):
        return fail("Too many requests, please try again later", 429, request)
    body = await request.json()
    return await _proxy_alphaid_post("/api/v1/register/send-sms", request, body=body)


@router.post("/register/verify-sms")
async def register_verify_sms(request: Request):
    """Verify SMS code → proxy to Alpha-ID."""
    body = await request.json()
    return await _proxy_alphaid_post("/api/v1/register/verify-sms", request, body=body)


@router.post("/register/face-verify")
async def register_face_verify(request: Request):
    """Initiate face verification → proxy to Alpha-ID."""
    body = await request.json()
    return await _proxy_alphaid_post("/api/v1/register/face-verify", request, body=body)


@router.post("/register/face-query")
async def register_face_query(request: Request):
    """Query face verification result → proxy to Alpha-ID."""
    body = await request.json()
    return await _proxy_alphaid_post("/api/v1/register/face-query", request, body=body)


@router.post("/register/generate-did")
async def register_generate_did(request: Request):
    """Generate decentralized identity DID → proxy to Alpha-ID."""
    body = await request.json()
    return await _proxy_alphaid_post("/api/v1/register/generate-did", request, body=body)


@router.post("/register/complete")
async def register_complete(request: Request):
    """Complete registration → proxy to Alpha-ID."""
    body = await request.json()
    return await _proxy_alphaid_post("/api/v1/register/complete", request, body=body)


# ── Dashboard ──


@router.get("/dashboard")
async def dashboard(request: Request):
    """Unified dashboard — single call returns all data needed."""
    import asyncio

    identity, profile = await asyncio.gather(
        proxy_get("/api/v1/identity/stats/overview", config.ALPHAID_URL),
        proxy_get(f"/api/v1/identity/{config.DEFAULT_ALPHA_ID}", config.ALPHAID_URL),
        return_exceptions=True,
    )

    def _to_result(value):
        if isinstance(value, Exception):
            return {"_error": str(value)}
        return value

    identity, profile = (_to_result(v) for v in (identity, profile))

    return ok(
        {
            "identity": {
                "alpha_id": identity.get("founder_alpha_id", config.DEFAULT_ALPHA_ID),
                "total_users": identity.get("total_users", 0),
                "state": "ready",
            },
            "profile": profile,
        },
        request,
    )
