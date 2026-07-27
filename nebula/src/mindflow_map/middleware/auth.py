"""Auth middleware and dependencies for FastAPI."""

from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import Depends, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from mindflow_map.models.auth_store import SQLAuthProvider
from mindflow_map.models.session import Database
from mindflow_map.schemas.auth import PermissionType, RoleType, TenantContext

logger = logging.getLogger(__name__)

# 安全：仅当显式设置时才允许 header 认证（开发环境）
_ALLOW_HEADER_AUTH = os.getenv("NEBULA_ALLOW_HEADER_AUTH", "false").lower() in ("1", "true", "yes")


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Extracts tenant/user context from request headers and attaches it to
    `request.state`. Supports both bearer-token and header-based auth.
    """

    def __init__(self, app, db: Database) -> None:
        super().__init__(app)
        self._db = db

    async def dispatch(self, request: Request, call_next):
        async with self._db.get_session() as session:
            provider = SQLAuthProvider(session)
            # Bootstrap default permissions once per session if needed
            if not provider.get_permissions(RoleType.OWNER):
                _bootstrap_defaults(provider)

            tenant_id = request.headers.get("X-Tenant-ID")
            user_id = request.headers.get("X-User-ID")
            auth_header = request.headers.get("Authorization", "")
            token_payload = None

            if auth_header.startswith("Bearer "):
                token_value = auth_header[7:]
                token_payload = await provider.validate_token(token_value)

            if token_payload:
                tenant_id = token_payload.tenant_id
                user_id = token_payload.user_id
                role = token_payload.role
                permissions = token_payload.scope or provider.get_permissions(role)
            elif _ALLOW_HEADER_AUTH and tenant_id and user_id:
                # ⚠️ 仅开发环境：允许 header 认证（需显式设置 NEBULA_ALLOW_HEADER_AUTH=true）
                logger.warning(
                    "Header-based auth used for tenant=%s user=%s (dev mode)",
                    tenant_id, user_id,
                )
                role = await provider.get_role(user_id, tenant_id)
                permissions = provider.get_permissions(role)
            else:
                tenant_id = None
                user_id = None
                role = None
                permissions = []

            request.state.tenant_id = tenant_id
            request.state.user_id = user_id
            request.state.user_role = role
            request.state.user_permissions = permissions
            request.state.auth_provider = provider

            logger.info(
                "Auth: tenant=%s user=%s role=%s",
                tenant_id,
                user_id,
                role,
                extra={
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "action": "authenticate",
                },
            )

            return await call_next(request)


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def get_tenant_context(request: Request) -> TenantContext:
    """
    FastAPI dependency that returns the current tenant context.

    Raises 401 if no tenant/user is present.
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    user_id = getattr(request.state, "user_id", None)
    role = getattr(request.state, "user_role", None)
    permissions = getattr(request.state, "user_permissions", [])

    if not tenant_id or not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    return TenantContext(
        tenant_id=tenant_id,
        user_id=user_id,
        role=role,
        permissions=permissions,
    )


def get_current_user_id(request: Request) -> Optional[str]:
    """FastAPI dependency that returns the current user ID, or None."""
    return getattr(request.state, "user_id", None)


def get_current_tenant_id(request: Request) -> Optional[str]:
    """FastAPI dependency that returns the current tenant ID, or None."""
    return getattr(request.state, "tenant_id", None)


def require_permission(permission: PermissionType):
    """
    Factory that returns a FastAPI dependency requiring a specific permission.
    Usage: `current_user: TenantContext = Depends(require_permission(PermissionType.WORKFLOW_WRITE))`
    """

    def _check(request: Request) -> TenantContext:
        ctx = get_tenant_context(request)
        if permission not in ctx.permissions:
            raise HTTPException(status_code=403, detail=f"Missing permission: {permission}")
        return ctx

    return _check


def require_role(required_role: str):
    """
    Factory that returns a FastAPI dependency requiring a minimum role level.
    Role hierarchy: owner > admin > member > viewer
    """

    def _check(request: Request) -> TenantContext:
        ctx = get_tenant_context(request)
        role_hierarchy = {"owner": 4, "admin": 3, "member": 2, "viewer": 1}
        user_level = role_hierarchy.get(str(ctx.role), 0)
        required_level = role_hierarchy.get(required_role.lower(), 0)
        if user_level < required_level:
            raise HTTPException(status_code=403, detail=f"Requires role: {required_role}")
        return ctx

    return _check


# ---------------------------------------------------------------------------
# Bootstrap defaults (shared with in-memory provider)
# ---------------------------------------------------------------------------


def _bootstrap_defaults(provider: SQLAuthProvider) -> None:
    provider.set_permissions(RoleType.OWNER, list(PermissionType))
    provider.set_permissions(RoleType.ADMIN, [
        PermissionType.WORKFLOW_READ,
        PermissionType.WORKFLOW_WRITE,
        PermissionType.WORKFLOW_EXECUTE,
        PermissionType.APPROVAL_READ,
        PermissionType.APPROVAL_DECIDE,
        PermissionType.INTEGRATION_READ,
        PermissionType.INTEGRATION_WRITE,
    ])
    provider.set_permissions(RoleType.MEMBER, [
        PermissionType.WORKFLOW_READ,
        PermissionType.WORKFLOW_EXECUTE,
        PermissionType.APPROVAL_READ,
    ])
    provider.set_permissions(RoleType.VIEWER, [
        PermissionType.WORKFLOW_READ,
        PermissionType.APPROVAL_READ,
        PermissionType.INTEGRATION_READ,
    ])
