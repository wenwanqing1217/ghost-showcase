from __future__ import annotations

import logging
import time
from typing import Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from mindflow_map.core.metrics import get_metrics

logger = logging.getLogger(__name__)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """请求指标采集中间件。"""

    def __init__(self, app) -> None:
        super().__init__(app)
        self._metrics = get_metrics()
        self._active_requests: Dict[str, int] = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        method = request.method
        route = self._normalize_route(path)

        labels = {"method": method, "route": route, "status": "error"}

        self._metrics.increment("requests_total", labels=labels)
        self._metrics.gauge("active_requests", self._active_requests.get(route, 0) + 1, labels=labels)
        self._active_requests[route] = self._active_requests.get(route, 0) + 1

        start = time.perf_counter()
        try:
            response = await call_next(request)
            labels["status"] = str(response.status_code)
            return response
        except Exception:
            labels["status"] = "500"
            raise
        finally:
            duration = time.perf_counter() - start
            labels["status"] = labels.get("status", "error")
            self._metrics.observe("request_duration_seconds", duration, labels=labels)
            self._metrics.gauge(
                "active_requests",
                max(0, self._active_requests.get(route, 1) - 1),
                labels=labels,
            )
            self._active_requests[route] = max(0, self._active_requests.get(route, 1) - 1)

    @staticmethod
    def _normalize_route(path: str) -> str:
        """将路径中的 UUID/数字替换为参数名，避免指标爆炸。"""
        import re
        path = re.sub(r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "/{uuid}", path)
        path = re.sub(r"/\d+", "/{id}", path)
        return path
