"""Simple in-memory auth provider (replace with DB in production)."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from mindflow_map.schemas.auth import PermissionType, RoleType, Tenant, TenantContext, TokenPayload, User


class AuthProvider:
    """Minimal auth provider for RBAC and multi-tenancy."""

    def __init__(self) -> None:
        self._tenants: dict[str, Tenant] = {}
        self._users: dict[str, User] = {}
        self._roles: dict[str, dict[str, RoleType]] = {}  # user_id -> role mapping per tenant
        self._tokens: dict[str, TokenPayload] = {}
        self._permissions: dict[str, List[PermissionType]] = {}  # role -> permissions

    # ------------------------------------------------------------------
    # Tenant management
    # ------------------------------------------------------------------

    def create_tenant(self, tenant: Tenant) -> Tenant:
        self._tenants[tenant.tenant_id] = tenant
        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self._tenants.get(tenant_id)

    def list_tenants(self) -> List[Tenant]:
        return list(self._tenants.values())

    # ------------------------------------------------------------------
    # User management
    # ------------------------------------------------------------------

    def create_user(self, user: User) -> User:
        self._users[user.user_id] = user
        self._roles.setdefault(user.user_id, {})[user.tenant_id] = user.role
        return user

    def get_user(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def list_users_by_tenant(self, tenant_id: str) -> List[User]:
        return [u for u in self._users.values() if u.tenant_id == tenant_id]

    def set_role(self, user_id: str, tenant_id: str, role: RoleType) -> None:
        self._roles.setdefault(user_id, {})[tenant_id] = role
        if user_id in self._users:
            self._users[user_id].role = role

    def get_role(self, user_id: str, tenant_id: str) -> RoleType:
        return self._roles.get(user_id, {}).get(tenant_id, RoleType.MEMBER)

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def issue_token(
        self,
        user_id: str,
        tenant_id: str,
        role: RoleType,
        ttl_seconds: int = 3600,
        scope: Optional[List[PermissionType]] = None,
    ) -> str:
        token_value = secrets.token_urlsafe(32)
        payload = TokenPayload(
            user_id=user_id,
            tenant_id=tenant_id,
            role=role,
            exp=datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
            scope=scope or [],
        )
        self._tokens[token_value] = payload
        return token_value

    def validate_token(self, token_value: str) -> Optional[TokenPayload]:
        payload = self._tokens.get(token_value)
        if not payload:
            return None
        if payload.exp and payload.exp < datetime.now(timezone.utc):
            del self._tokens[token_value]
            return None
        return payload

    def revoke_token(self, token_value: str) -> None:
        self._tokens.pop(token_value, None)

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------

    def get_permissions(self, role: RoleType) -> List[PermissionType]:
        return self._permissions.get(role, [])

    def set_permissions(self, role: RoleType, permissions: List[PermissionType]) -> None:
        self._permissions[role] = permissions

    def has_permission(self, user_id: str, tenant_id: str, permission: PermissionType) -> bool:
        role = self.get_role(user_id, tenant_id)
        return permission in self.get_permissions(role)

    def get_tenant_context(self, user_id: str, tenant_id: str) -> TenantContext:
        role = self.get_role(user_id, tenant_id)
        permissions = self.get_permissions(role)
        return TenantContext(
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
            permissions=permissions,
        )


# Global singleton (replace with DI in production)
_auth_provider: Optional[AuthProvider] = None


def get_auth_provider() -> AuthProvider:
    global _auth_provider
    if _auth_provider is None:
        _auth_provider = AuthProvider()
        _bootstrap_defaults(_auth_provider)
    return _auth_provider


def _bootstrap_defaults(provider: AuthProvider) -> None:
    # Default permissions per role
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
