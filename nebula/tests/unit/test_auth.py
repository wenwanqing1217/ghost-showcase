"""RBAC and multi-tenancy tests."""

from __future__ import annotations

from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from mindflow_map.core.auth import get_auth_provider
from mindflow_map.middleware.auth import (
    AuthMiddleware,
    get_tenant_context,
    require_permission,
)
from mindflow_map.models.session import Database
from mindflow_map.schemas.auth import (
    PermissionType,
    RoleType,
    Tenant,
    TenantContext,
    User,
)

# ---------------------------------------------------------------------------
# AuthProvider unit tests
# ---------------------------------------------------------------------------


class TestAuthProvider:
    """Tests for the in-memory auth provider."""

    def setup_method(self):
        # Reset global provider for each test
        import mindflow_map.core.auth as auth_module
        auth_module._auth_provider = None

    def test_create_and_get_tenant(self):
        provider = get_auth_provider()
        tenant = provider.create_tenant(Tenant(tenant_id="t1", name="Test Tenant"))
        assert provider.get_tenant("t1") == tenant
        assert len(provider.list_tenants()) == 1

    def test_create_user_sets_role(self):
        provider = get_auth_provider()
        provider.create_tenant(Tenant(tenant_id="t1", name="Tenant"))
        user = provider.create_user(
            User(user_id="u1", tenant_id="t1", email="u1@test.com", name="User One", role=RoleType.ADMIN)
        )
        assert user.role == RoleType.ADMIN
        assert provider.get_role("u1", "t1") == RoleType.ADMIN

    def test_issue_and_validate_token(self):
        provider = get_auth_provider()
        provider.create_tenant(Tenant(tenant_id="t1", name="Tenant"))
        provider.create_user(User(user_id="u1", tenant_id="t1", email="u1@test.com", name="User One"))
        token_value = provider.issue_token(user_id="u1", tenant_id="t1", role=RoleType.MEMBER)
        payload = provider.validate_token(token_value)
        assert payload is not None
        assert payload.user_id == "u1"
        assert payload.tenant_id == "t1"

    def test_validate_invalid_token_returns_none(self):
        provider = get_auth_provider()
        assert provider.validate_token("nonexistent") is None

    def test_revoke_token(self):
        provider = get_auth_provider()
        provider.create_tenant(Tenant(tenant_id="t1", name="Tenant"))
        provider.create_user(User(user_id="u1", tenant_id="t1", email="u1@test.com", name="User One"))
        token_value = provider.issue_token(user_id="u1", tenant_id="t1", role=RoleType.MEMBER)
        provider.revoke_token(token_value)
        assert provider.validate_token(token_value) is None

    def test_role_based_permissions(self):
        provider = get_auth_provider()
        assert PermissionType.WORKFLOW_WRITE in provider.get_permissions(RoleType.ADMIN)
        assert PermissionType.WORKFLOW_WRITE not in provider.get_permissions(RoleType.VIEWER)

    def test_has_permission_checks_role(self):
        provider = get_auth_provider()
        provider.create_tenant(Tenant(tenant_id="t1", name="Tenant"))
        provider.create_user(
            User(user_id="u1", tenant_id="t1", email="u1@test.com", name="User One", role=RoleType.VIEWER)
        )
        assert not provider.has_permission("u1", "t1", PermissionType.WORKFLOW_WRITE)
        assert provider.has_permission("u1", "t1", PermissionType.WORKFLOW_READ)

    def test_get_tenant_context(self):
        provider = get_auth_provider()
        provider.create_tenant(Tenant(tenant_id="t1", name="Tenant"))
        provider.create_user(
            User(user_id="u1", tenant_id="t1", email="u1@test.com", name="User One", role=RoleType.MEMBER)
        )
        ctx = provider.get_tenant_context("u1", "t1")
        assert ctx.tenant_id == "t1"
        assert ctx.user_id == "u1"
        assert ctx.role == RoleType.MEMBER


# ---------------------------------------------------------------------------
# Middleware / integration tests
# ---------------------------------------------------------------------------


class TestAuthMiddleware:
    """Tests for auth middleware with isolated FastAPI apps."""

    def test_headers_set_tenant_context(self):
        from unittest.mock import patch

        db = Database("sqlite+aiosqlite:///:memory:")
        app = FastAPI()
        app.add_middleware(AuthMiddleware, db=db)

        @app.get("/check")
        def check(request: Request):
            ctx = get_tenant_context(request)
            return {"tenant_id": ctx.tenant_id, "user_id": ctx.user_id}

        # 模拟可信客户端（localhost），因为 TestClient 的 ASGI transport 不设置真实 IP
        with patch("mindflow_map.middleware.auth._is_trusted_client", return_value=True):
            client = TestClient(app)
            resp = client.get("/check", headers={"X-Tenant-ID": "t1", "X-User-ID": "u1"})
            assert resp.status_code == 200
            assert resp.json()["tenant_id"] == "t1"

    def test_missing_headers_returns_401_for_protected_route(self):
        db = Database("sqlite+aiosqlite:///:memory:")
        app = FastAPI()
        app.add_middleware(AuthMiddleware, db=db)

        @app.get("/protected")
        def protected(request: Request):
            get_tenant_context(request)
            return {"ok": True}

        client = TestClient(app)
        resp = client.get("/protected")
        assert resp.status_code == 401

    def test_bearer_token_sets_context(self):
        import asyncio

        async def setup():
            db = Database("sqlite+aiosqlite:///:memory:")
            async with db.get_session() as session:
                from mindflow_map.models.auth_store import SQLAuthProvider
                provider = SQLAuthProvider(session)
                await provider.create_tenant(Tenant(tenant_id="t1", name="Tenant"))
                await provider.create_user(User(user_id="u1", tenant_id="t1", email="u1@test.com", name="User One"))
                token_value = await provider.issue_token(user_id="u1", tenant_id="t1", role=RoleType.ADMIN)
                return db, token_value

        db, token_value = asyncio.run(setup())

        app = FastAPI()
        app.add_middleware(AuthMiddleware, db=db)

        @app.get("/token-protected")
        def token_protected(request: Request):
            ctx = get_tenant_context(request)
            return {"user_id": ctx.user_id, "role": ctx.role}

        client = TestClient(app)
        resp = client.get("/token-protected", headers={"Authorization": f"Bearer {token_value}"})
        assert resp.status_code == 200
        assert resp.json()["user_id"] == "u1"


# ---------------------------------------------------------------------------
# Permission / role dependency tests
# ---------------------------------------------------------------------------


class TestPermissionDependencies:
    def test_require_permission_grants_access(self):
        import asyncio

        async def setup():
            db = Database("sqlite+aiosqlite:///:memory:")
            async with db.get_session() as session:
                from mindflow_map.models.auth_store import SQLAuthProvider
                provider = SQLAuthProvider(session)
                await provider.create_tenant(Tenant(tenant_id="t1", name="Tenant"))
                await provider.create_user(
                    User(user_id="u1", tenant_id="t1", email="u1@test.com", name="User One", role=RoleType.ADMIN)
                )
                token = await provider.issue_token(user_id="u1", tenant_id="t1", role=RoleType.ADMIN)
                return db, token

        db, token = asyncio.run(setup())

        app = FastAPI()
        app.add_middleware(AuthMiddleware, db=db)

        @app.get("/perm-test")
        def perm_endpoint(ctx: TenantContext = Depends(require_permission(PermissionType.WORKFLOW_WRITE))):
            return {"granted": True}

        client = TestClient(app)
        resp = client.get("/perm-test", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_require_permission_denies_access(self):
        import asyncio

        async def setup():
            db = Database("sqlite+aiosqlite:///:memory:")
            async with db.get_session() as session:
                from mindflow_map.models.auth_store import SQLAuthProvider
                provider = SQLAuthProvider(session)
                await provider.create_tenant(Tenant(tenant_id="t1", name="Tenant"))
                await provider.create_user(
                    User(user_id="u1", tenant_id="t1", email="u1@test.com", name="User One", role=RoleType.VIEWER)
                )
                token = await provider.issue_token(user_id="u1", tenant_id="t1", role=RoleType.VIEWER)
                return db, token

        db, token = asyncio.run(setup())

        app = FastAPI()
        app.add_middleware(AuthMiddleware, db=db)

        @app.get("/perm-test")
        def perm_endpoint(ctx: TenantContext = Depends(require_permission(PermissionType.WORKFLOW_WRITE))):
            return {"granted": True}

        client = TestClient(app)
        resp = client.get("/perm-test", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
