#!/usr/bin/env python3
"""
Network Operations Routes — /v1/net/*
======================================
Proxies all requests to Net-Agent Server (router management).
JWT-authenticated requests are forwarded with their Authorization header.
Net-Agent handles its own permission checks.
"""

from fastapi import APIRouter, Request

from services.proxy import proxy_get, proxy_post, filter_headers
import config

router = APIRouter(prefix="/v1/net", tags=["net"])


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def net_proxy(request: Request, path: str):
    """Proxy /v1/net/* to Net-Agent server.

    Only safe headers (Authorization, Content-Type, X-Request-ID, etc.) are forwarded.
    Host, Cookie, Content-Length and other gateway-scoped headers are stripped.
    """
    target = f"/v1/net/{path}"
    safe_headers = filter_headers(dict(request.headers))
    if request.method == "GET":
        data = await proxy_get(target, config.NETAGENT_URL, headers=safe_headers)
    else:
        body = await request.json()
        data = await proxy_post(
            target, config.NETAGENT_URL, body=body, headers=safe_headers
        )
    from services.proxy import ok

    return ok(data, request)
