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
    """Reads or generates an X-Request-ID, propagates it inward and back in the response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Set on request.state for downstream access
        request.state.request_id = request_id

        # Set in ContextVar with token for proper async-safe reset
        token: Optional[contextvars.Token] = None
        if _request_id_var is not None:
            token = _request_id_var.set(request_id)

        try:
            response = await call_next(request)
            # Echo the request ID back to the client for log correlation
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            if _request_id_var is not None and token is not None:
                _request_id_var.reset(token)
