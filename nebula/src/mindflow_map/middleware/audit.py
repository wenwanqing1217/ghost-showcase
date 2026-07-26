"""Audit logging middleware and store."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from mindflow_map.models.audit_store import SQLAuditStore
from mindflow_map.models.session import Database
from mindflow_map.schemas.audit import AuditAction, AuditLog, AuditLogFilter

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Records audit logs for incoming HTTP requests using the database.

    Attaches `request.state.audit_logger` so endpoints can emit extra
    domain-specific events beyond the default request log.
    """

    def __init__(self, app, db: Database) -> None:
        super().__init__(app)
        self._db = db

    async def dispatch(self, request: Request, call_next):
        async with self._db.get_session() as session:
            store = SQLAuditStore(session)
            # Reuse the request_id set by CorrelationIdMiddleware (outer layer).
            # Do NOT generate a new UUID — that would break log correlation.
            request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID", str(uuid.uuid4()))
            request.state.request_id = request_id
            request.state.audit_logger = _AuditLogger(request, store)

            response = await call_next(request)

            # Emit request-level audit log to database
            await request.state.audit_logger.log(
                action=AuditAction.ACCESS,
                resource_type="http_request",
                detail={
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                },
            )

            logger.info(
                "Audit: method=%s path=%s status=%s",
                request.method,
                request.url.path,
                response.status_code,
                extra={
                    "request_id": request_id,
                    "tenant_id": getattr(request.state, "tenant_id", None),
                    "user_id": getattr(request.state, "user_id", None),
                },
            )

            return response


class _AuditLogger:
    """Helper attached to request.state for domain audit logging."""

    def __init__(self, request: Request, store: SQLAuditStore) -> None:
        self._request = request
        self._store = store

    async def log(
        self,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        detail: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        log = AuditLog(
            log_id=str(uuid.uuid4()),
            tenant_id=getattr(self._request.state, "tenant_id", None),
            user_id=getattr(self._request.state, "user_id", None),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=self._request.client.host if self._request.client else None,
            user_agent=self._request.headers.get("user-agent"),
            request_id=getattr(self._request.state, "request_id", None),
            detail=detail or {},
            created_at=datetime.now(timezone.utc),
        )
        await self._store.append(log)
        return log
