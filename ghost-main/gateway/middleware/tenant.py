"""Tenant Isolation Middleware — Ghost Gateway
=============================================
Extracts tenant identity from JWT (AlphaID DID) and enforces
tenant-scoped access across all Gateway routes.

Design:
  - Every authenticated request carries an Alpha-ID (DID) as tenant_id
  - The tenant_id is injected into request.state for downstream use
  - Routes that require tenant isolation can check request.state.tenant_id
  - Public routes (health, docs) bypass tenant enforcement

Integration with AlphaID:
  - AlphaID issues JWTs with 'alpha_id' and 'did' claims
  - Gateway validates the JWT and extracts the tenant identifier
  - DS backend receives X-Tenant-ID header for Prisma query scoping
"""

import logging
import os
from typing import Optional

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("ghost-gateway")

# Routes that do NOT require tenant authentication
_PUBLIC_PATHS = {
    "/health",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api",
    "/",
    "/workbench",
}

# Routes that require tenant authentication
_TENANT_REQUIRED_PATHS = {
    "/v1/ecom",
    "/v1/human",
    "/v1/agent",
    "/v1/flow",
}


class TenantMiddleware(BaseHTTPMiddleware):
    """Extract and validate tenant identity from request headers/JWT."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip public paths
        if path in _PUBLIC_PATHS or path.startswith("/static"):
            return await call_next(request)

        # Determine if this path requires tenant auth
        requires_tenant = any(
            path.startswith(p) for p in _TENANT_REQUIRED_PATHS
        )

        if requires_tenant:
            # Try multiple sources for tenant identity (priority order):
            # 1. X-Tenant-ID header (set by upstream proxy or internal service)
            # 2. Authorization: Bearer <JWT> → extract alpha_id claim
            # 3. alpha_id query parameter (legacy, for backward compat)

            tenant_id: Optional[str] = None
            tenant_source: str = "none"

            # Source 1: X-Tenant-ID header
            tenant_id = request.headers.get("X-Tenant-ID", "").strip() or None
            if tenant_id:
                tenant_source = "header"

            # Source 2: JWT Authorization header
            if not tenant_id:
                auth_header = request.headers.get("authorization", "")
                if auth_header.startswith("Bearer "):
                    token = auth_header[7:]
                    tenant_id = self._extract_alpha_id_from_jwt(token)
                    if tenant_id:
                        tenant_source = "jwt"

            # Source 3: Query parameter (legacy, only for internal services)
            if not tenant_id:
                tenant_id = request.query_params.get("alpha_id", "").strip() or None
                if tenant_id:
                    tenant_source = "query"

            if not tenant_id:
                # No tenant identity found — reject
                logger.warning(
                    "Tenant auth required but no identity found: %s %s",
                    request.method,
                    path,
                )
                return JSONResponse(
                    status_code=401,
                    content={
                        "success": False,
                        "error": "missing_tenant_identity",
                        "message": "Tenant identity required. Provide X-Tenant-ID header or Bearer JWT.",
                    },
                )

            # Inject tenant_id into request state
            request.state.tenant_id = tenant_id
            request.state.tenant_source = tenant_source

            # For ecom routes, also inject X-Tenant-ID for downstream DS backend
            if path.startswith("/v1/ecom"):
                request.headers.__dict__["_headers"]["x-tenant-id"] = tenant_id

            logger.debug(
                "Tenant resolved: %s (source=%s) for %s %s",
                tenant_id,
                tenant_source,
                request.method,
                path,
            )

        return await call_next(request)

    def _extract_alpha_id_from_jwt(self, token: str) -> Optional[str]:
        """Extract alpha_id claim from JWT without full verification.

        The Gateway trusts Alpha-ID's JWT issuance. Full verification
        should happen at Alpha-ID level. Here we just extract the claim.

        For production, consider using python-jose[cryptography] for
        proper JWT decoding and signature verification.
        """
        try:
            # JWT format: header.payload.signature
            import base64

            payload_b64 = token.split(".")[1]
            # Add padding if needed
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding

            payload_json = base64.urlsafe_b64decode(payload_b64)
            import json

            payload = json.loads(payload_json)

            # Extract alpha_id claim
            alpha_id = payload.get("alpha_id") or payload.get("sub") or payload.get("did")
            return str(alpha_id).strip() if alpha_id else None

        except Exception as e:
            logger.debug("JWT parse failed: %s", e)
            return None


# Import here to avoid circular dependency
from fastapi.responses import JSONResponse  # noqa: E402
