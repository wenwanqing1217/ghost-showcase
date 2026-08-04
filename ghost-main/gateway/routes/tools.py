"""Tools Routes — /v1/tools/*
==========================
Proxies ToolA/ToolB requests to the code generator and optimizer services.

Architecture:
  DS Frontend → Gateway (:18080/v1/tools/*) → ToolA :8081 / ToolB :8082

Routes:
  POST /v1/tools/generate  → ToolA /v1/generate (code generator)
  POST /v1/tools/optimize  → ToolB /v1/optimize (code optimizer)
  GET  /v1/tools/health    → ToolA + ToolB combined health
"""

import logging
from typing import Optional

from fastapi import APIRouter, Request, HTTPException

from services.proxy import proxy_get, proxy_post, proxy_delete, ok, fail
import config

logger = logging.getLogger("ghost-gateway")

TOOL_A_URL = getattr(config, "TOOL_A_URL", "http://tool-a:8081")
TOOL_B_URL = getattr(config, "TOOL_B_URL", "http://tool-b:8082")

router = APIRouter(prefix="/v1/tools", tags=["tools"])


# ── Helper: proxy to ToolA/ToolB ──


async def _proxy_tool(
    method: str,
    tool_url: str,
    path: str,
    request: Request,
    body: dict = None,
    timeout: float = None,
) -> dict:
    """Proxy request to ToolA or ToolB, forwarding auth headers."""
    headers = {"X-Request-ID": getattr(request.state, "request_id", "")}

    # Forward Authorization if present
    auth_header = request.headers.get("authorization")
    if auth_header:
        headers["Authorization"] = auth_header

    # Forward CSRF-relevant headers
    from services.proxy import forward_csrf_headers
    headers.update(forward_csrf_headers(request))

    url = f"{tool_url}{path}"
    from services.proxy import _proxy_request

    return await _proxy_request(method, url, "", body=body, headers=headers, timeout=timeout)


# ── ToolA: Code Generator ──


@router.post("/generate")
async def generate_code(request: Request):
    """Generate code from a requirement description using ToolA.

    Body: { requirement: string, task_id: string, language?: string }
    Proxied to ToolA /v1/generate.
    """
    body = await request.json()

    ip = request.client.host if request.client else "unknown"
    from middleware.rate_limit import rate_limit_check
    if not rate_limit_check(f"tools:generate:{ip}", max_requests=10, window=60):
        return fail("Rate limit exceeded, please wait 1 minute", 429, request)

    data = await _proxy_tool("POST", TOOL_A_URL, "/v1/generate", request, body=body, timeout=120)
    return ok(data, request)


# ── ToolB: Code Optimizer ──


@router.post("/optimize")
async def optimize_code(request: Request):
    """Optimize existing code using ToolB.

    Body: { requirement: string, task_id: string, tool_a_result: dict }
    Proxied to ToolB /v1/optimize.
    """
    body = await request.json()

    ip = request.client.host if request.client else "unknown"
    from middleware.rate_limit import rate_limit_check
    if not rate_limit_check(f"tools:optimize:{ip}", max_requests=10, window=60):
        return fail("Rate limit exceeded, please wait 1 minute", 429, request)

    data = await _proxy_tool("POST", TOOL_B_URL, "/v1/optimize", request, body=body, timeout=120)
    return ok(data, request)


# ── Combined Health ──


@router.get("/health")
async def tools_health(request: Request):
    """Check health of ToolA and ToolB services."""
    from services.proxy import proxy_get

    tool_a_health = await proxy_get("/health", TOOL_A_URL)
    tool_b_health = await proxy_get("/health", TOOL_B_URL)

    a_ok = isinstance(tool_a_health, dict) and tool_a_health.get("status") == "ok"
    b_ok = isinstance(tool_b_health, dict) and tool_b_health.get("status") == "ok"

    return ok(
        {
            "tool-a": tool_a_health if a_ok else {"status": "error", "detail": tool_a_health},
            "tool-b": tool_b_health if b_ok else {"status": "error", "detail": tool_b_health},
            "overall": "ok" if (a_ok and b_ok) else "degraded",
        },
        request,
    )
