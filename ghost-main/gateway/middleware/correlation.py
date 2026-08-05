"""Correlation ID + Access Log middleware."""

import logging
import time
import uuid

from fastapi import Request

logger = logging.getLogger("ghost-gateway")


async def correlation_id_middleware(request: Request, call_next):
    """Inject correlation ID for distributed tracing and log all requests."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:12])
    request.state.request_id = request_id
    start = time.time()

    response = await call_next(request)

    duration_ms = round((time.time() - start) * 1000, 1)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "%s %s %s %.1fms [%s]",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request_id,
    )
    return response
