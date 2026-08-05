"""Standardized error response format for all HTTP exceptions."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def _build_error_response(
    status_code: int,
    error_type: str,
    message: str,
    detail: Any = None,
    request_id: str | None = None,
    timestamp: str | None = None,
) -> Dict[str, Any]:
    """Build a standardized error response payload."""
    return {
        "error": error_type,
        "message": message,
        "detail": detail,
        "request_id": request_id,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
    }


def register_error_handlers(app: FastAPI) -> None:
    """Register exception handlers on the FastAPI app."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        logger.warning("Validation error: %s | %s", exc.errors(), request_id)

        return JSONResponse(
            status_code=422,
            content=_build_error_response(
                status_code=422,
                error_type="validation_error",
                message="Request validation failed.",
                detail=exc.errors(),
                request_id=request_id,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

        # Map status code to error type
        error_type_map = {
            400: "bad_request",
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            405: "method_not_allowed",
            409: "conflict",
            422: "validation_error",
            429: "rate_limit_exceeded",
            500: "internal_server_error",
            502: "bad_gateway",
            503: "service_unavailable",
        }
        error_type = error_type_map.get(exc.status_code, "http_error")

        # Extract detail from exc
        detail = exc.detail if isinstance(exc.detail, (str, dict, list)) else str(exc.detail)

        logger.warning(
            "HTTP %d: %s | %s | %s",
            exc.status_code,
            error_type,
            str(detail),
            request_id,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=_build_error_response(
                status_code=exc.status_code,
                error_type=error_type,
                message=str(detail) if detail else error_type,
                detail=detail if isinstance(detail, (dict, list)) else None,
                request_id=request_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
            ),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        logger.error("Unhandled exception: %s", exc, exc_info=True)

        return JSONResponse(
            status_code=500,
            content=_build_error_response(
                status_code=500,
                error_type="internal_server_error",
                message="An unexpected error occurred.",
                detail=str(exc) if app.debug else None,
                request_id=request_id,
            ),
        )
