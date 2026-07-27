"""
CSRF 防护中间件 — 纵深防御

基于 Origin/Referer 头验证，阻止跨站伪造的状态变更请求。
与 JWT Bearer Token 认证互补：Token 防未授权访问，CSRF 防跨站请求伪造。

防护策略：
  1. 安全方法（GET/HEAD/OPTIONS）直接放行
  2. 状态变更方法（POST/PUT/DELETE/PATCH）要求：
     a. Origin 头匹配允许的来源列表，或
     b. Referer 头匹配允许的来源列表
     c. 同时要求 X-Requested-With 头
  3. 无 Origin/Referer 头的请求直接拒绝
  4. Webhook 回调路径（外部平台推送）豁免
"""

import logging
from typing import Optional, Set

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from mindflow_map.config import settings

logger = logging.getLogger(__name__)

# 安全方法 — 不要求 CSRF 检查
_SAFE_METHODS: Set[str] = {"GET", "HEAD", "OPTIONS"}

# 自定义头 — 浏览器跨域 fetch 无法设置
_CSRF_CUSTOM_HEADER = "X-Requested-With"
_CSRF_CUSTOM_HEADER_VALUE = "XMLHttpRequest"


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF 防护中间件 — 验证 Origin/Referer + 自定义头"""

    def __init__(
        self,
        app: ASGIApp,
        allowed_origins: Set[str],
        exempt_paths: Optional[Set[str]] = None,
        enforce_custom_header: bool = True,
    ) -> None:
        super().__init__(app)
        self._allowed_origins = allowed_origins
        self._exempt_paths = exempt_paths or set()
        self._enforce_custom_header = enforce_custom_header

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 测试模式跳过 CSRF
        if settings.csrf_disabled:
            return await call_next(request)

        # 安全方法直接放行
        if request.method in _SAFE_METHODS:
            return await call_next(request)

        path = request.url.path

        # 豁免路径（如 webhook 回调、OAuth 回调等外部入口）
        if path in self._exempt_paths:
            return await call_next(request)

        # 自定义头检查
        if self._enforce_custom_header:
            requested_with = request.headers.get(_CSRF_CUSTOM_HEADER, "")
            if requested_with != _CSRF_CUSTOM_HEADER_VALUE:
                logger.warning(
                    "CSRF check failed: missing %s header (path=%s, method=%s)",
                    _CSRF_CUSTOM_HEADER,
                    path,
                    request.method,
                )
                return Response(
                    content='{"detail":"CSRF validation failed: missing X-Requested-With header"}',
                    status_code=403,
                    media_type="application/json",
                    headers={"X-CSRF-Error": "missing-custom-header"},
                )

        # Origin 头检查
        origin = request.headers.get("Origin")
        if origin:
            if origin not in self._allowed_origins:
                logger.warning(
                    "CSRF check failed: Origin not allowed (origin=%s, path=%s)",
                    origin,
                    path,
                )
                return Response(
                    content='{"detail":"CSRF validation failed: origin not allowed"}',
                    status_code=403,
                    media_type="application/json",
                    headers={"X-CSRF-Error": "origin-not-allowed"},
                )
            return await call_next(request)

        # Referer 头回退
        referer = request.headers.get("Referer")
        if referer:
            from urllib.parse import urlparse

            parsed = urlparse(referer)
            referer_origin = f"{parsed.scheme}://{parsed.netloc}"
            if referer_origin not in self._allowed_origins:
                logger.warning(
                    "CSRF check failed: Referer not allowed (referer=%s, path=%s)",
                    referer,
                    path,
                )
                return Response(
                    content='{"detail":"CSRF validation failed: referer not allowed"}',
                    status_code=403,
                    media_type="application/json",
                    headers={"X-CSRF-Error": "referer-not-allowed"},
                )
            return await call_next(request)

        # 无 Origin/Referer — 拒绝
        logger.warning(
            "CSRF check failed: no Origin or Referer (path=%s, method=%s, client=%s)",
            path,
            request.method,
            request.client,
        )
        return Response(
            content='{"detail":"CSRF validation failed: missing Origin/Referer"}',
            status_code=403,
            media_type="application/json",
            headers={"X-CSRF-Error": "missing-origin-referer"},
        )
