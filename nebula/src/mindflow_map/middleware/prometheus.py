from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from mindflow_map.core.metrics import (
    record_http_request,
    increment_active_requests,
    decrement_active_requests,
)

logger = logging.getLogger(__name__)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """请求指标采集中间件 — 基于 prometheus_client。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        method = request.method
        route = _normalize_route(path)

        increment_active_requests(method, route)

        start = time.perf_counter()
        response = None
        try:
            response = await call_next(request)
            return response
        except Exception:
            duration = time.perf_counter() - start
            record_http_request(method, route, 500, duration)
            raise
        finally:
            if response is not None:
                duration = time.perf_counter() - start
                record_http_request(method, route, response.status_code, duration)
                decrement_active_requests(method, route)


def _normalize_route(path: str) -> str:
    """将路径中的 UUID/数字替换为参数名，避免指标爆炸。"""
    import re
    path = re.sub(r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "/{uuid}", path)
    path = re.sub(r"/\d+", "/{id}", path)
    return path
