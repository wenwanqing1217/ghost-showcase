"""Agent Ecosystem Layer — /v1/agent/* routes.

All agent-facing interfaces, separate from human traffic.
"""

import logging

from fastapi import APIRouter, Request
from typing import Optional

from services.proxy import proxy_get, proxy_post, ok, fail, forward_csrf_headers
from services.obsidian import get_feeds

import config

logger = logging.getLogger("ghost-gateway")

router = APIRouter(prefix="/v1/agent", tags=["agent"])


# ── A2A Interaction ──


@router.get("/interact/topology")
async def get_network_topology(request: Request):
    """Get Agent network topology → proxy to Alpha-ID stats overview."""
    data = await proxy_get("/api/v1/identity/stats/overview", config.ALPHAID_URL)
    return ok(data, request)


# ── A2A Protocol Proxy ─
# 所有 /v1/agent/a2a/* 路由代理到 Alpha-ID :8000 的 /api/v1/a2a/* 端点


@router.post("/a2a/call")
async def a2a_proxy_call(request: Request):
    """A2A 调用代理 — 转发到 Alpha-ID A2A 端点"""
    body = await request.json()
    headers = forward_csrf_headers(request)
    data = await proxy_post("/api/v1/a2a/call", config.ALPHAID_URL, body=body, headers=headers)
    return ok(data, request)


@router.post("/a2a/register")
async def a2a_proxy_register(request: Request):
    """A2A Agent 注册代理 — 转发到 Alpha-ID"""
    body = await request.json()
    headers = forward_csrf_headers(request)
    data = await proxy_post("/api/v1/a2a/register", config.ALPHAID_URL, body=body, headers=headers)
    return ok(data, request)


@router.get("/a2a/discover")
async def a2a_proxy_discover(request: Request):
    """A2A Agent 发现代理 — 转发到 Alpha-ID"""
    headers = forward_csrf_headers(request)
    data = await proxy_get("/api/v1/a2a/discover", config.ALPHAID_URL, headers=headers)
    return ok(data, request)


@router.get("/a2a/agents")
async def a2a_proxy_agents(request: Request):
    """列出所有 A2A Agent — 转发到 Alpha-ID"""
    headers = forward_csrf_headers(request)
    data = await proxy_get("/api/v1/a2a/agents", config.ALPHAID_URL, headers=headers)
    return ok(data, request)


@router.get("/a2a/graph")
async def a2a_proxy_graph(request: Request):
    """A2A Agent 网络拓扑图 — 转发到 Alpha-ID"""
    headers = forward_csrf_headers(request)
    data = await proxy_get("/api/v1/a2a/graph", config.ALPHAID_URL, headers=headers)
    return ok(data, request)


@router.get("/a2a/skills")
async def a2a_proxy_skills(request: Request):
    """列出可用 A2A 技能 — 转发到 Alpha-ID"""
    headers = forward_csrf_headers(request)
    data = await proxy_get("/api/v1/a2a/skills", config.ALPHAID_URL, headers=headers)
    return ok(data, request)


@router.get("/a2a/audit")
async def a2a_proxy_audit(request: Request):
    """A2A 审计日志查询 — 转发到 Alpha-ID"""
    headers = forward_csrf_headers(request)

    # 转发查询参数
    query_params = request.query_params
    url = f"/api/v1/a2a/audit"
    if query_params:
        url += "?" + str(query_params)

    data = await proxy_get(url, config.ALPHAID_URL, headers=headers)
    return ok(data, request)


@router.get("/a2a/health")
async def a2a_proxy_health(request: Request):
    """A2A 健康检查 — 转发到 Alpha-ID"""
    data = await proxy_get("/api/v1/a2a/health", config.ALPHAID_URL)
    return ok(data, request)


# ── Agent Information Feeds ──


@router.get("/feeds/latest")
async def agent_feeds_latest(
    request: Request,
    industry: Optional[str] = None,
    limit: int = 20,
):
    """Get latest industry-curated info captured by platform ops agent."""
    try:
        feeds = get_feeds(industry=industry, limit=limit)
        return ok({"results": feeds, "total": len(feeds)}, request)
    except Exception as e:
        return fail(str(e), 500, request)


@router.post("/feeds/subscribe")
async def agent_feeds_subscribe(request: Request):
    """Subscribe to industry feed updates."""
    # 订阅持久化尚未实现，返回 501 明确告知客户端
    return fail("订阅功能尚未实现", 501, request)
