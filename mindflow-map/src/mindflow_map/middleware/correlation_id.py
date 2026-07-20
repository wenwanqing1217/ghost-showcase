"""Correlation ID middleware for async-safe request tracking."""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

try:
    import contextvars
    _request_id_var = contextvars.ContextVar("request_id", default="")
except ImportError:  # pragma: no cover
    _request_id_var = None  # type: ignore[assignment]


def get_request_id() -> str:
    """Return the current request ID from context vars."""
    if _request_id_var is None:
        return ""
    return _request_id_var.get("")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Reads or generates an X-Request-ID and propagates it."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        if _request_id_var is not None:
            _request_id_var.set(request_id)

        request.state.request_id = request_id

        try:
            response = await call_next(request)
            return response
        finally:
            if _request_id_var is not None:
                _request_id_var.set("")
