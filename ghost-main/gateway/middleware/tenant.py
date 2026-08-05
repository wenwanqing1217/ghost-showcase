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

import config  # noqa: E402

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
            # Resolve tenant identity with explicit priority order:
            #   1. X-Tenant-ID header  → explicit override (e.g. from upstream proxy)
            #   2. JWT Bearer token    → extract alpha_id claim (primary auth path)
            #   3. alpha_id query param → legacy fallback (internal services only)
            #   4. Nothing found        → 401 Unauthorized
            tenant_id = self._resolve_tenant_id(request)

            if not tenant_id:
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
            request.state.tenant_source = self._tenant_source

            # For ecom routes, also inject X-Tenant-ID for downstream DS backend
            if path.startswith("/v1/ecom"):
                # ASGI scope headers are (bytes, bytes) tuples — mutate directly
                new_headers = []
                found = False
                for k, v in request.scope.get("headers", []):
                    if k.lower() == b"x-tenant-id":
                        new_headers.append((k, tenant_id.encode()))
                        found = True
                    else:
                        new_headers.append((k, v))
                if not found:
                    new_headers.append((b"x-tenant-id", tenant_id.encode()))
                request.scope["headers"] = new_headers

            logger.debug(
                "Tenant resolved: %s (source=%s) for %s %s",
                tenant_id,
                self._tenant_source,
                request.method,
                path,
            )

        return await call_next(request)

    def _resolve_tenant_id(self, request: Request) -> Optional[str]:
        """Resolve tenant identity from request using the priority cascade.

        Priority:
          1. X-Tenant-ID header  — explicit override from upstream proxy
          2. JWT Bearer token    — extract alpha_id claim (primary path)
          3. alpha_id query param — legacy fallback for internal services

        Also sets self._tenant_source to record which source was used.
        Returns None if no identity could be resolved.
        """
        # Source 1: X-Tenant-ID header (explicit override)
        tenant_id = request.headers.get("X-Tenant-ID", "").strip() or None
        if tenant_id:
            self._tenant_source = "header"
            return tenant_id

        # Source 2: JWT Authorization header → extract alpha_id claim
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            tenant_id = self._extract_alpha_id_from_jwt(token)
            if tenant_id:
                self._tenant_source = "jwt"
                return tenant_id

        # Source 3: alpha_id query parameter (legacy, internal services only)
        tenant_id = request.query_params.get("alpha_id", "").strip() or None
        if tenant_id:
            self._tenant_source = "query"
            return tenant_id

        self._tenant_source = "none"
        return None

    def _extract_alpha_id_from_jwt(self, token: str) -> Optional[str]:
        """Extract alpha_id claim from JWT with signature verification.

        Uses the shared AUTH_MASTER_KEY (HKDF-SHA256) from Alpha-ID
        to verify the token signature before extracting the claim.
        Falls back to unverified extraction if AUTH_MASTER_KEY is not configured.
        """
        try:
            import base64
            import hmac
            import hashlib

            # JWT format: header.payload.signature
            parts = token.split(".")
            if len(parts) != 3:
                return None

            header_b64, payload_b64, signature_b64 = parts

            # Verify signature if AUTH_MASTER_KEY is available
            _AUTH_MASTER_KEY = config.AUTH_MASTER_KEY if config else ""
            if _AUTH_MASTER_KEY:
                # HKDF-SHA256 key derivation (same as Alpha-ID)
                _HKDF_SALT = b"\x00" * 32
                _HKDF_INFO = b"alpha-id-jwt-signing-key-v1"
                prk = hmac.new(_HKDF_SALT, _AUTH_MASTER_KEY.encode("utf-8"), hashlib.sha256).digest()
                signing_key = hmac.new(prk, _HKDF_INFO + b"\x01", hashlib.sha256).digest()

                # Compute expected signature
                message = f"{header_b64}.{payload_b64}".encode("utf-8")
                expected_sig = hmac.new(signing_key, message, hashlib.sha256).digest()
                expected_b64 = base64.urlsafe_b64encode(expected_sig).rstrip(b"=").decode("utf-8")

                # Constant-time comparison to prevent timing attacks
                if not hmac.compare_digest(signature_b64, expected_b64):
                    logger.warning("JWT signature verification failed for tenant extraction")
                    return None
            # else: no master key configured — accept token (dev mode)

            # Decode payload
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += b"=" * padding

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
